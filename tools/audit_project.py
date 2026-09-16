#!/usr/bin/env python3
"""
Volyera - project consistency audit.

Where `generate_enchantments.py` *produces* the data, this script *reads what is
actually on disk* and cross-checks it. That separation is deliberate: it catches
hand-edits to the JSON, a lang key that was renamed but not translated, a tag
that points at an enchantment which no longer exists, and - the subtlest one -
an exclusive-set conflict that is only declared in one direction.

Volyera supports several Minecraft versions and their enchantment formats are
not compatible, so every data check runs once per version against that version's
own resource tree, and there is an extra check that each tree actually uses its
own version's spelling. That last one matters because the failure mode is
silent: a jar built with the wrong tree loads nothing and logs no error.

Run it any time; CI runs it on every push.

    python3 tools/audit_project.py
"""

import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMMON_SRC = os.path.join(ROOT, 'common', 'src')
SHARED = os.path.join(COMMON_SRC, 'main', 'resources')
fail = []


def version_res(version):
    return os.path.join(COMMON_SRC, 'mc' + version.replace('.', ''), 'resources')


def vparts(version):
    return tuple(int(p) for p in version.split('.'))


def load_json_tree(root):
    docs = {}
    for p in sorted(glob.glob(root + '/**/*.json', recursive=True)):
        try:
            docs[p] = json.load(open(p, encoding='utf-8'))
        except Exception as e:
            fail.append('JSON parse error %s: %s' % (p, e))
    return docs


def props_from(path):
    out = {}
    for line in open(path, encoding='utf-8'):
        line = line.strip()
        if '=' in line and not line.startswith('#'):
            k, v = line.split('=', 1)
            out[k.strip()] = v.strip()
    return out


props = props_from(os.path.join(ROOT, 'gradle.properties'))
VERSIONS = [v.strip() for v in props.get('supported_minecraft_versions', '').split(',') if v.strip()]
if not VERSIONS:
    fail.append('gradle.properties sets no supported_minecraft_versions')

# The version list and the resource trees on disk must agree, or a build would
# silently pick up a stale tree.
expected_trees = {'mc' + v.replace('.', '') for v in VERSIONS}
actual_trees = {os.path.basename(d) for d in glob.glob(os.path.join(COMMON_SRC, 'mc*'))
                if os.path.isdir(d)}
if actual_trees != expected_trees:
    fail.append('resource trees %s do not match supported_minecraft_versions %s '
                '(expected %s)' % (sorted(actual_trees), VERSIONS, sorted(expected_trees)))

shared_docs = load_json_tree(SHARED)
print('supported Minecraft versions: %s' % ', '.join(VERSIONS))
print('shared json files (tags, lang): %d' % len(shared_docs))

# Condition types that are unambiguously conditions: `minecraft:all_of` is both
# an effect and a condition, so it cannot be used to tell the two spellings
# apart and is excluded from the negative check below.
UNAMBIGUOUS_CONDITIONS = {
    'minecraft:damage_source_properties', 'minecraft:random_chance',
    'minecraft:entity_properties', 'minecraft:weather_check',
    'minecraft:any_of', 'minecraft:inverted', 'minecraft:match_tool',
    'minecraft:location_check', 'minecraft:enchantment_active_check',
}

rosters = {}

for version in VERSIONS:
    root = version_res(version)
    modern = vparts(version) >= (26, 3)
    cond_key = 'type' if modern else 'condition'
    tag_prefix = '#' if modern else ''
    where = 'mc%s' % version.replace('.', '')

    docs = dict(shared_docs)
    docs.update(load_json_tree(root))

    ench_paths = [p for p in docs if '/data/volyera/enchantment/' in p]
    ench = {os.path.basename(p)[:-5] for p in ench_paths}
    rosters[version] = ench
    if not ench:
        fail.append('%s: no enchantment definitions found under %s' % (where, root))

    # -- version spelling ----------------------------------------------------
    # 26.3 renamed the condition discriminator and prefixed damage-source tag
    # references. Check the files on disk match the version they live under.
    for p in sorted(ench_paths):
        raw = open(p, encoding='utf-8').read()
        name = os.path.basename(p)
        if modern and '"condition"' in raw:
            fail.append('%s/%s: uses the 26.2 "condition" key; 26.3 needs "type"'
                        % (where, name))
        if not modern:
            for kind in sorted(UNAMBIGUOUS_CONDITIONS):
                if '"type": "%s"' % kind in raw:
                    fail.append('%s/%s: uses the 26.3 "type" spelling for %s'
                                % (where, name, kind))
        d = docs[p]

        def walk(node, path=''):
            if isinstance(node, dict):
                if node.get(cond_key) == 'minecraft:damage_source_properties':
                    for tag in node.get('predicate', {}).get('tags', []):
                        tid = tag.get('id', '')
                        if not tid.startswith(tag_prefix + 'minecraft:'):
                            fail.append('%s/%s%s: damage-source tag id %r must %sbe '
                                        '"#"-prefixed' % (where, name, path, tid,
                                                          '' if modern else 'not '))
                for k, v in node.items():
                    walk(v, '%s.%s' % (path, k))
            elif isinstance(node, list):
                for i, v in enumerate(node):
                    walk(v, '%s[%d]' % (path, i))

        walk(d)

    # -- lang coverage -------------------------------------------------------
    lang = docs.get(SHARED + '/assets/volyera/lang/en_us.json', {})
    for p in ench_paths:
        d = docs[p]
        k = d['description']['translate']
        if k not in lang:
            fail.append('%s: lang key missing %s' % (p, k))
        if k + '.desc' not in lang:
            fail.append('%s: desc key missing %s.desc' % (p, k))
    unused = set(lang) - {d['description']['translate'] for d in docs.values()
                          if isinstance(d, dict) and 'description' in d}
    unused -= {k for k in lang if k.endswith('.desc')}
    if unused:
        fail.append('%s: lang keys with no enchantment: %s' % (where, sorted(unused)))

    # -- tag references from enchantment documents ---------------------------
    refs = set()
    for p in ench_paths:
        d = docs[p]
        for f in ('supported_items', 'primary_items', 'exclusive_set'):
            v = d.get(f)
            if isinstance(v, str) and v.startswith('#'):
                refs.add((p, v))
    for p, ref in sorted(refs):
        ns, path = ref[1:].split(':', 1)
        if ns == 'volyera':
            if not os.path.exists('%s/data/volyera/tags/enchantment/%s.json' % (SHARED, path)):
                fail.append('%s: tag file missing for %s' % (p, ref))
        elif not (path.startswith('enchantable/') or path.startswith('exclusive_set/')):
            fail.append('%s: unexpected vanilla tag %s' % (p, ref))

    # -- tag value entries must resolve --------------------------------------
    for p, d in docs.items():
        if '/tags/enchantment/' not in p:
            continue
        for v in d.get('values', []):
            if v.startswith('#'):
                ns, path = v[1:].split(':', 1)
                if ns == 'volyera' and not os.path.exists(
                        '%s/data/volyera/tags/enchantment/%s.json' % (SHARED, path)):
                    fail.append('%s: nested tag %s has no file' % (p, v))
            elif v.startswith('volyera:') and v.split(':', 1)[1] not in ench:
                fail.append('%s: unknown volyera enchantment %s' % (p, v))

    # -- vanilla tag merges must be additive ---------------------------------
    for p, d in docs.items():
        if '/data/minecraft/tags/' in p and d.get('replace'):
            fail.append('%s: must not set replace:true' % p)

    # -- treasure/curse bookkeeping ------------------------------------------
    def ids(tagfile):
        p = '%s/data/minecraft/tags/enchantment/%s.json' % (SHARED, tagfile)
        if p not in docs:
            return set()
        return {v.split(':', 1)[1] for v in docs[p]['values'] if v.startswith('volyera:')}

    treasure, curses, non_treasure = ids('treasure'), ids('curse'), ids('non_treasure')
    if treasure & non_treasure:
        fail.append('%s: in both treasure and non_treasure: %s'
                    % (where, sorted(treasure & non_treasure)))
    if treasure | non_treasure != ench:
        fail.append('%s: treasure+non_treasure != roster. missing=%s extra=%s' % (
            where, sorted(ench - (treasure | non_treasure)),
            sorted((treasure | non_treasure) - ench)))
    if not curses <= treasure:
        fail.append('%s: curses must also be treasure: %s' % (where, sorted(curses - treasure)))
    if not curses <= ids('on_random_loot'):
        fail.append('%s: curses should be findable in loot' % where)

    # -- exclusive-set symmetry ----------------------------------------------
    vanilla_excl = {}
    for p, d in docs.items():
        m = re.search(r'data/minecraft/tags/enchantment/exclusive_set/(\w+)\.json$', p)
        if m:
            vanilla_excl[m.group(1)] = {v.split(':', 1)[1] for v in d['values']
                                        if v.startswith('volyera:')}
    for name, group in vanilla_excl.items():
        for e in group:
            ep = '%s/data/volyera/enchantment/%s.json' % (root, e)
            if ep not in docs:
                fail.append('%s: vanilla exclusive_set/%s lists %s but it has no definition'
                            % (where, name, e))
                continue
            own = docs[ep].get('exclusive_set', '')
            if own == '#minecraft:exclusive_set/%s' % name:
                continue
            if not own.startswith('#volyera:'):
                fail.append('%s: %s added to vanilla exclusive_set/%s but its own '
                            'exclusive_set is %r' % (where, e, name, own))
            else:
                tp = '%s/data/volyera/tags/enchantment/%s.json' % (SHARED, own[1:].split(':', 1)[1])
                members = docs[tp]['values'] if tp in docs else []
                if not any(m.startswith('minecraft:') for m in members):
                    fail.append('%s: %s lists no vanilla enchantments in %s, so the '
                                'conflict is one-way' % (where, e, own))

    print('  %s: %d enchantments, condition key %r, damage-source tags %sprefixed'
          % (where, len(ench), cond_key, '#' if tag_prefix else 'un'))

# Every version must ship the same roster; a version that silently lost an
# enchantment would otherwise pass all of the above.
if len({frozenset(r) for r in rosters.values()}) > 1:
    fail.append('rosters differ between versions: %s'
                % {v: len(r) for v, r in rosters.items()})

# ---------------------------------------------------------------------------
# Placeholder coverage. Gradle expands the loader metadata with Groovy's
# SimpleTemplateEngine, which parses ANY ${...} as an expression - even inside a
# TOML or JSON comment - and fails the build with an opaque template error. So
# every ${...} in those files must be a key the build script actually supplies.
# Checking against the build scripts rather than gradle.properties is what makes
# this correct now that some values are derived per Minecraft version.
# ---------------------------------------------------------------------------
def supplied_keys(path, pattern):
    text = open(path, encoding='utf-8').read()
    m = re.search(pattern, text, re.S)
    if not m:
        fail.append('%s: could not find the expansion map' % os.path.basename(path))
        return set()
    return set(re.findall(r"['\"]?(\w+)['\"]?\s*:", m.group(1)))


toml_path = os.path.join(ROOT, 'neoforge/src/main/templates/META-INF/neoforge.mods.toml')
if os.path.exists(toml_path):
    toml = open(toml_path, encoding='utf-8').read()
    need = set(re.findall(r'\$\{([^}]*)\}', toml))
    have = supplied_keys(os.path.join(ROOT, 'neoforge/build.gradle'),
                         r'var replaceProperties = \[(.*?)\n    \]')
    missing = need - have
    if missing:
        fail.append('neoforge.mods.toml has dollar-brace text that generateModMetadata does '
                    'not supply (Groovy will try to evaluate it): %s' % sorted(missing))
    print('toml placeholders: %s' % sorted(need))

fj_path = os.path.join(ROOT, 'fabric/src/main/resources/fabric.mod.json')
fj = open(fj_path, encoding='utf-8').read()
need = set(re.findall(r'\$\{([^}]*)\}', fj))
have = supplied_keys(os.path.join(ROOT, 'fabric/build.gradle'), r'expand ((?:.|\n)*?)\n    \}')
missing = need - have
if missing:
    fail.append('fabric.mod.json has dollar-brace text that processResources does not '
                'supply: %s' % sorted(missing))
print('fabric.mod.json placeholders: %s' % sorted(need))

# The resource tree directory is mc<version with no separator>, and build.gradle
# must derive it the same way the generator and this script do. Getting it wrong
# (mc26_2 instead of mc262) fails only when Gradle runs, so check it here where
# it is free.
bg = open(os.path.join(ROOT, 'build.gradle'), encoding='utf-8').read()
if "def mcDir = 'mc' + mcVersion.replace('.', '')" not in bg:
    fail.append('build.gradle does not derive mcDir as "mc" + the version without '
                'separators, which is how the generator names the resource trees')
if 'common/src/mc${mcKey}' in bg:
    fail.append('build.gradle builds the resource tree path from mcKey (underscores); '
                'the trees on disk have no separator')
if 'common/src/${mcDir}/resources' not in bg:
    fail.append('build.gradle does not resolve the version resource tree via mcDir')

# Per-version coordinates the build scripts require must exist.
for version in VERSIONS:
    key = version.replace('.', '_')
    if 'fabric_api_version_%s' % key not in props:
        fail.append('gradle.properties has no fabric_api_version_%s' % key)
if 'neo_version_%s' % props.get('minecraft_version', '').replace('.', '_') not in props:
    print('note: no stable NeoForge for the default minecraft_version; :neoforge is excluded')

# Entrypoint classes referenced by metadata must exist.
d = json.loads(re.sub(r'\$\{[^}]*\}', 'PLACEHOLDER', fj))
for ep in d.get('entrypoints', {}).get('main', []):
    path = os.path.join(ROOT, 'fabric/src/main/java', ep.replace('.', '/') + '.java')
    if not os.path.exists(path):
        fail.append('fabric entrypoint %s has no source at %s' % (ep, path))

print()
if fail:
    print('PROBLEMS:')
    for f in fail:
        print('  - ' + f)
    sys.exit(1)
print('CROSS-FILE CONSISTENCY: OK')
