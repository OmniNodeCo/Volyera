#!/usr/bin/env python3
"""
Volyera - packaged jar verification.

A green `gradlew build` only proves the jars were produced. This checks that
they were produced *correctly*, which is where a two-loader, two-Minecraft-version
data-driven mod actually goes wrong:

  * shared resources silently missing from one loader's jar;
  * a jar packaging the *other* Minecraft version's enchantment data, which
    builds fine, loads nothing, and logs no error - the single worst failure
    available here, and the reason the version-spelling check exists;
  * the NeoForge metadata template expanding to nothing, or leaving an
    unexpanded placeholder behind;
  * fabric.mod.json shipping with a literal `${version}`, or declaring the wrong
    Minecraft dependency for the data it actually contains;
  * loader-specific classes leaking into the other loader's jar;
  * classes compiled for the wrong JVM (26.2 and 26.3 both need Java 25, which
    is class file major version 69).

The Minecraft version is read from the artifact name (`volyera-fabric-26.3-...`),
which the build derives from -Pminecraft_version, so a mismatch between the name
and the packaged data is caught rather than trusted.

    python3 tools/verify_jars.py [jar ...]

With no arguments it looks under fabric/build/libs and neoforge/build/libs.
Pass --markdown to also print a summary suitable for a CI comment.
Exits non-zero if any check fails.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMMON_SRC = os.path.join(ROOT, 'common', 'src')
SHARED = os.path.join(COMMON_SRC, 'main', 'resources')

JAVA_25_CLASS_MAJOR = 69

# Condition types that are unambiguously conditions. `minecraft:all_of` is both
# an effect and a condition in 26.2, so it cannot distinguish the two spellings
# and is deliberately absent.
UNAMBIGUOUS_CONDITIONS = {
    'minecraft:damage_source_properties', 'minecraft:random_chance',
    'minecraft:entity_properties', 'minecraft:weather_check',
    'minecraft:any_of', 'minecraft:inverted', 'minecraft:match_tool',
    'minecraft:location_check', 'minecraft:enchantment_active_check',
}

failures: list[str] = []
notes: list[str] = []


def check(ok: bool, message: str) -> bool:
    if ok:
        notes.append('ok   ' + message)
    else:
        failures.append(message)
        notes.append('FAIL ' + message)
    return ok


def vparts(version: str) -> tuple[int, ...]:
    return tuple(int(p) for p in version.split('.'))


def version_res(version: str) -> str:
    return os.path.join(COMMON_SRC, 'mc' + version.replace('.', ''), 'resources')


def supported_versions() -> list[str]:
    for line in open(os.path.join(ROOT, 'gradle.properties'), encoding='utf-8'):
        line = line.strip()
        if line.startswith('supported_minecraft_versions='):
            return [v.strip() for v in line.split('=', 1)[1].split(',') if v.strip()]
    return []


def mod_version() -> str:
    for line in open(os.path.join(ROOT, 'gradle.properties'), encoding='utf-8'):
        line = line.strip()
        if line.startswith('mod_version='):
            return line.split('=', 1)[1].strip()
    return ''


def expected_resources(version: str) -> dict[str, set[str]]:
    """Resource paths that must appear in a jar built for this Minecraft version.

    Tags and translations parse identically on every supported version and come
    from the shared tree; only the enchantment definitions are per version.
    """
    groups: dict[str, set[str]] = {'enchantments': set(), 'tags': set(),
                                   'lang': set(), 'other': set()}

    def add(root: str, only_enchantments: bool) -> None:
        if not os.path.isdir(root):
            return
        for dirpath, _, files in os.walk(root):
            for name in files:
                full = os.path.join(dirpath, name)
                rel = os.path.relpath(full, root).replace(os.sep, '/')
                # Order matters: `data/volyera/tags/enchantment/*.json` also
                # contains the substring `/enchantment/`, so the definition
                # prefix has to be matched first or tag files get treated as
                # enchantment definitions and fail the completeness check.
                if rel.startswith('data/volyera/enchantment/'):
                    groups['enchantments'].add(rel)
                elif only_enchantments:
                    continue
                elif '/tags/' in rel:
                    groups['tags'].add(rel)
                elif rel.startswith('assets/'):
                    groups['lang'].add(rel)
                else:
                    groups['other'].add(rel)

    add(version_res(version), only_enchantments=True)
    add(SHARED, only_enchantments=False)
    return groups


def class_major_version(data: bytes) -> int | None:
    if len(data) < 8 or data[:4] != b'\xca\xfe\xba\xbe':
        return None
    return int.from_bytes(data[6:8], 'big')


def damage_source_tag_ids(node, out: list[str]) -> None:
    """Collect the `id` of every tag inside a damage_source_properties condition."""
    if isinstance(node, dict):
        for key in ('type', 'condition'):
            if node.get(key) == 'minecraft:damage_source_properties':
                for tag in node.get('predicate', {}).get('tags', []):
                    if isinstance(tag, dict) and 'id' in tag:
                        out.append(tag['id'])
        for value in node.values():
            damage_source_tag_ids(value, out)
    elif isinstance(node, list):
        for value in node:
            damage_source_tag_ids(value, out)


def check_version_spelling(name: str, jar: zipfile.ZipFile,
                           enchantments: set[str], version: str) -> None:
    """The packaged data must be in the format THIS Minecraft version parses."""
    modern = vparts(version) >= (26, 3)
    tag_prefix = '#' if modern else ''
    wrong_key: list[str] = []
    wrong_prefix: list[str] = []

    for rel in sorted(enchantments):
        raw = jar.read(rel).decode('utf-8')
        if modern:
            if '"condition"' in raw:
                wrong_key.append(rel)
                continue
        else:
            if any('"%s": "%s"' % ('type', kind) in raw
                   for kind in UNAMBIGUOUS_CONDITIONS):
                wrong_key.append(rel)
                continue
        ids: list[str] = []
        damage_source_tag_ids(json.loads(raw), ids)
        if any(not i.startswith(tag_prefix + 'minecraft:') for i in ids):
            wrong_prefix.append(rel)

    want = '"type" and "#"-prefixed damage-source tags' if modern \
        else '"condition" and unprefixed damage-source tags'
    check(not wrong_key,
          '%s: all %d enchantment definitions use the %s spelling (%s)%s'
          % (name, len(enchantments), version, want,
             '' if not wrong_key else ' - wrong key in %s' % wrong_key[:4]))
    check(not wrong_prefix,
          '%s: damage-source tag references are %sprefixed as %s requires%s'
          % (name, tag_prefix or 'un', version,
             '' if not wrong_prefix else ' - %s' % wrong_prefix[:4]))


def verify_jar(path: str, loader: str, version: str) -> None:
    name = os.path.basename(path)
    groups = expected_resources(version)
    if not check(os.path.exists(path), '%s: jar exists' % name):
        return

    with zipfile.ZipFile(path) as jar:
        entries = set(jar.namelist())

        # -- shared content -------------------------------------------------
        for group in ('enchantments', 'tags', 'lang', 'other'):
            wanted = groups.get(group) or set()
            missing = wanted - entries
            detail = '' if not missing else ' (missing %s)' % (sorted(missing)[:6],)
            check(not missing, '%s: all %d %s present%s'
                  % (name, len(wanted), group, detail))

        # Enchantment definitions from the *other* version must not be in there.
        # Both trees define the same 20 paths, so a jar can only ever carry one;
        # the spelling check below is what tells us which.

        # Every enchantment definition must still parse after packaging.
        broken = []
        for rel in sorted(groups['enchantments']):
            if rel not in entries:
                continue
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

        check_version_spelling(name, jar, groups['enchantments'] & entries, version)

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
                    check(meta.get('version') == mod_version(),
                          '%s: fabric.mod.json version expanded to %r'
                          % (name, meta.get('version')))
                    eps = meta.get('entrypoints', {}).get('main', [])
                    check(eps == ['net.volyera.fabric.VolyeraFabric'],
                          '%s: entrypoint is %s' % (name, eps))
                    # Fabric Loader has no pack-repository code;
                    # fabric-resource-loader-v1 is what makes the game read this
                    # jar's data/volyera/enchantment at all.
                    deps = meta.get('depends', {})
                    check('fabric-resource-loader-v1' in deps,
                          '%s: depends on fabric-resource-loader-v1 so its data is '
                          'loaded (%s)' % (name, sorted(deps)))
                    # The declared Minecraft dependency must match the data that
                    # was actually packaged, or the loader will happily install
                    # 26.2 data into a 26.3 game.
                    check(deps.get('minecraft') == '~%s' % version,
                          '%s: declares minecraft %r, matching the packaged data '
                          '(expected %r)' % (name, deps.get('minecraft'),
                                             '~%s' % version))
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
                check('version = "%s"' % mod_version() in raw,
                      '%s: neoforge.mods.toml version expanded' % name)
                check('modLoader = "javafml"' in raw,
                      '%s: neoforge.mods.toml declares the mod loader' % name)
                check('[%s]' % version in raw,
                      '%s: neoforge.mods.toml pins Minecraft %s' % (name, version))
            check('net/volyera/neoforge/VolyeraNeoForge.class' in entries,
                  '%s: contains the NeoForge entrypoint class' % name)
            leaked = [e for e in entries if e == 'fabric.mod.json'
                      or e.startswith('net/volyera/fabric/')]
            check(not leaked, '%s: no Fabric files leaked in%s'
                  % (name, '' if not leaked else ' (%s)' % leaked[:4]))


ARTIFACT_RE = re.compile(r'^volyera-(fabric|neoforge)-(\d+\.\d+)-(.+)\.jar$')


def classify(path: str) -> tuple[str, str] | None:
    """(loader, minecraft version) from the artifact name."""
    m = ARTIFACT_RE.match(os.path.basename(path))
    if not m:
        return None
    return m.group(1), m.group(2)


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

    versions = supported_versions()
    print('supported Minecraft versions: %s' % ', '.join(versions))
    for version in versions:
        groups = expected_resources(version)
        print('  %s expects %d enchantments, %d tag files, %d assets'
              % (version, len(groups['enchantments']), len(groups['tags']),
                 len(groups['lang'])))

    seen: set[tuple[str, str]] = set()
    for path in jars:
        info = classify(path)
        if info is None:
            check(False, '%s: name does not match volyera-<loader>-<mcversion>-<modversion>.jar, '
                  'so the target Minecraft version cannot be determined'
                  % os.path.basename(path))
            continue
        loader, version = info
        if version not in versions:
            check(False, '%s: built for Minecraft %s, which is not in '
                  'supported_minecraft_versions (%s)'
                  % (os.path.basename(path), version, ', '.join(versions)))
            continue
        seen.add((loader, version))
        print('\n--- %s (%s, Minecraft %s) ---'
              % (os.path.relpath(path, ROOT), loader, version))
        verify_jar(path, loader, version)

    # Every supported version must have produced a Fabric jar; a build stage
    # that quietly failed would otherwise leave a hole nothing else notices.
    for version in versions:
        check(('fabric', version) in seen,
              'a Fabric jar for Minecraft %s was expected but not verified' % version)

    # NeoForge has no stable release for every supported version, so a missing
    # NeoForge jar is only a problem for versions that have one.
    neo_versions = []
    for line in open(os.path.join(ROOT, 'gradle.properties'), encoding='utf-8'):
        m = re.match(r'^neo_version_(\d+)_(\d+)=', line.strip())
        if m:
            neo_versions.append('%s.%s' % m.groups())
    for version in versions:
        if version in neo_versions:
            check(('neoforge', version) in seen,
                  'a NeoForge jar for Minecraft %s was expected but not verified' % version)
        else:
            notes.append('note Minecraft %s is Fabric-only: NeoForge has no stable '
                         'release for it yet' % version)

    print()
    for line in notes:
        print('  ' + line)

    if args.markdown:
        print('\n<!-- markdown -->')
        print('### Packaged jar verification\n')
        for path in jars:
            # An unexpanded shell glob arrives here as a literal path when a
            # build produced nothing; report that instead of crashing.
            size = os.path.getsize(path) // 1024 if os.path.exists(path) else -1
            print('- `%s` (%s)' % (os.path.basename(path),
                                   'missing' if size < 0 else '%d KB' % size))
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
