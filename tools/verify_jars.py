#!/usr/bin/env python3
"""
Volyera - packaged jar verification.

A green `gradlew build` only proves the jars were produced. This checks that
they were produced *correctly*, which is where a two-loader data-driven mod
actually goes wrong:

  * shared resources silently missing from one loader's jar;
  * the NeoForge metadata template expanding to nothing, or leaving an
    unexpanded placeholder behind;
  * fabric.mod.json shipping with a literal `${version}`;
  * loader-specific classes leaking into the other loader's jar;
  * classes compiled for the wrong JVM (26.2 needs Java 25 / class file 69).

It reads the finished jars, so it also verifies the enchantment JSON survived
packaging intact and still parses.

    python3 tools/verify_jars.py [jar ...]

With no arguments it looks under fabric/build/libs and neoforge/build/libs.
Pass --markdown to also print a summary suitable for a CI comment.
Exits non-zero if any check fails.
"""

from __future__ import annotations

import argparse
import glob
import io
import json
import os
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, 'common', 'src', 'main', 'resources')

JAVA_25_CLASS_MAJOR = 69

failures: list[str] = []
notes: list[str] = []


def check(ok: bool, message: str) -> bool:
    if ok:
        notes.append('ok   ' + message)
    else:
        failures.append(message)
        notes.append('FAIL ' + message)
    return ok


def expected_resources() -> dict[str, set[str]]:
    """Every shared resource path that must appear in both jars."""
    groups: dict[str, set[str]] = {'enchantments': set(), 'tags': set(),
                                   'lang': set(), 'other': set()}
    for dirpath, _, files in os.walk(RES):
        for name in files:
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, RES).replace(os.sep, '/')
            # Order matters: `data/volyera/tags/enchantment/*.json` also contains
            # the substring `/enchantment/`, so the definition prefix has to be
            # matched first or tag files get treated as enchantment definitions.
            if rel.startswith('data/volyera/enchantment/'):
                groups['enchantments'].add(rel)
            elif '/tags/' in rel:
                groups['tags'].add(rel)
            elif rel.startswith('assets/'):
                groups['lang'].add(rel)
            else:
                groups.setdefault('other', set()).add(rel)
    return groups


def class_major_version(data: bytes) -> int | None:
    if len(data) < 8 or data[:4] != b'\xca\xfe\xba\xbe':
        return None
    return int.from_bytes(data[6:8], 'big')


def verify_jar(path: str, loader: str, groups: dict[str, set[str]]) -> None:
    name = os.path.basename(path)
    if not check(os.path.exists(path), '%s: jar exists' % name):
        return

    with zipfile.ZipFile(path) as jar:
        entries = set(jar.namelist())

        # -- shared content -------------------------------------------------
        for group, wanted in groups.items():
            missing = wanted - entries
            detail = '' if not missing else ' (missing %s)' % (sorted(missing)[:6],)
            check(not missing, '%s: all %d %s present%s'
                  % (name, len(wanted), group, detail))

        # Every enchantment definition must still parse after packaging.
        broken = []
        for rel in sorted(groups['enchantments']):
            try:
                doc = json.loads(jar.read(rel).decode('utf-8'))
                for field in ('description', 'effects', 'max_level', 'min_cost',
                              'max_cost', 'slots', 'supported_items', 'weight',
                              'anvil_cost'):
                    if field not in doc:
                        broken.append('%s (no %s)' % (rel, field))
                        break
            except Exception as exc:  # noqa: BLE001 - report and keep going
                broken.append('%s (%s)' % (rel, exc))
        check(not broken, '%s: packaged enchantment JSON parses and is complete%s'
              % (name, '' if not broken else ': ' + '; '.join(broken[:4])))

        # -- shared classes -------------------------------------------------
        for cls in ('net/volyera/Volyera.class', 'net/volyera/VolyeraEnchantments.class'):
            check(cls in entries, '%s: contains %s' % (name, cls))

        # -- JVM target -----------------------------------------------------
        bad_jvm = []
        for cls in (e for e in entries if e.endswith('.class')):
            major = class_major_version(jar.read(cls))
            if major is not None and major > JAVA_25_CLASS_MAJOR:
                bad_jvm.append('%s=%d' % (cls, major))
        check(not bad_jvm, '%s: no class targets a JVM newer than Java 25%s'
              % (name, '' if not bad_jvm else ' (%s)' % ', '.join(bad_jvm[:4])))
        sample = next((e for e in sorted(entries) if e.endswith('.class')), None)
        if sample:
            notes.append('     %s compiled to class file major version %s'
                         % (sample, class_major_version(jar.read(sample))))

        # -- loader metadata ------------------------------------------------
        if loader == 'fabric':
            check('fabric.mod.json' in entries, '%s: contains fabric.mod.json' % name)
            if 'fabric.mod.json' in entries:
                raw = jar.read('fabric.mod.json').decode('utf-8')
                check('${' not in raw,
                      '%s: fabric.mod.json has no unexpanded placeholder' % name)
                try:
                    meta = json.loads(raw)
                    check(meta.get('id') == 'volyera',
                          '%s: fabric.mod.json id is volyera' % name)
                    check(meta.get('version') == '1.0.0',
                          '%s: fabric.mod.json version expanded to %r'
                          % (name, meta.get('version')))
                    eps = meta.get('entrypoints', {}).get('main', [])
                    check(eps == ['net.volyera.fabric.VolyeraFabric'],
                          '%s: entrypoint is %s' % (name, eps))
                    # The opposite of what this used to assert. Fabric Loader has
                    # no pack-repository code; fabric-resource-loader-v1 is what
                    # makes the game read this jar's data/volyera/enchantment.
                    deps = meta.get('depends', {})
                    check('fabric-resource-loader-v1' in deps,
                          '%s: depends on fabric-resource-loader-v1 so its data is loaded (%s)'
                          % (name, sorted(deps)))
                except Exception as exc:  # noqa: BLE001
                    check(False, '%s: fabric.mod.json parses (%s)' % (name, exc))
            check('net/volyera/fabric/VolyeraFabric.class' in entries,
                  '%s: contains the Fabric entrypoint class' % name)
            leaked = [e for e in entries if 'neoforge' in e.lower()]
            check(not leaked, '%s: no NeoForge files leaked in%s'
                  % (name, '' if not leaked else ' (%s)' % leaked[:4]))
        else:
            toml_path = 'META-INF/neoforge.mods.toml'
            check(toml_path in entries, '%s: contains %s' % (name, toml_path))
            if toml_path in entries:
                raw = jar.read(toml_path).decode('utf-8')
                check('${' not in raw,
                      '%s: neoforge.mods.toml has no unexpanded placeholder' % name)
                check('modId = "volyera"' in raw,
                      '%s: neoforge.mods.toml declares modId volyera' % name)
                check('version = "1.0.0"' in raw,
                      '%s: neoforge.mods.toml version expanded' % name)
                check('modLoader = "javafml"' in raw,
                      '%s: neoforge.mods.toml declares the mod loader' % name)
                check('[26.2]' in raw,
                      '%s: neoforge.mods.toml pins Minecraft 26.2' % name)
            check('net/volyera/neoforge/VolyeraNeoForge.class' in entries,
                  '%s: contains the NeoForge entrypoint class' % name)
            leaked = [e for e in entries if e == 'fabric.mod.json'
                      or e.startswith('net/volyera/fabric/')]
            check(not leaked, '%s: no Fabric files leaked in%s'
                  % (name, '' if not leaked else ' (%s)' % leaked[:4]))


def find_jars() -> list[str]:
    jars: list[str] = []
    for pattern in ('fabric/build/libs/*.jar', 'neoforge/build/libs/*.jar'):
        for path in sorted(glob.glob(os.path.join(ROOT, pattern))):
            # Skip the -sources jar; it has no metadata or resources to verify.
            if not path.endswith('-sources.jar'):
                jars.append(path)
    return jars


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument('jars', nargs='*', help='jar files to verify')
    parser.add_argument('--markdown', action='store_true',
                        help='also print a Markdown summary for CI comments')
    args = parser.parse_args()

    jars = args.jars or find_jars()
    if not jars:
        print('no jars found under fabric/build/libs or neoforge/build/libs',
              file=sys.stderr)
        return 1

    groups = expected_resources()
    print('shared resources expected in every jar: %d enchantments, %d tag files, '
          '%d assets' % (len(groups['enchantments']), len(groups['tags']),
                         len(groups['lang'])))

    for path in jars:
        loader = 'fabric' if os.sep + 'fabric' + os.sep in path else 'neoforge'
        print('\n--- %s (%s) ---' % (os.path.relpath(path, ROOT), loader))
        verify_jar(path, loader, groups)

    print()
    for line in notes:
        print('  ' + line)

    if args.markdown:
        print('\n<!-- markdown -->')
        print('### Packaged jar verification\n')
        for path in jars:
            print('- `%s` (%d KB)' % (os.path.basename(path),
                                      os.path.getsize(path) // 1024))
        print('\n```')
        for line in notes:
            print(line)
        print('```')

    print()
    if failures:
        print('JAR VERIFICATION FAILED (%d):' % len(failures), file=sys.stderr)
        for f in failures:
            print('  - ' + f, file=sys.stderr)
        return 1
    print('JAR VERIFICATION: OK (%d jars, %d checks)' % (len(jars), len(notes)))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
