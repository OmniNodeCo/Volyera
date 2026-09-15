#!/usr/bin/env python3
"""
Volyera - project consistency audit.

Where `generate_enchantments.py` *produces* the data, this script *reads what is
actually on disk* and cross-checks it. That separation is deliberate: it catches
hand-edits to the JSON, a lang key that was renamed but not translated, a tag
that points at an enchantment which no longer exists, and - the subtlest one -
an exclusive-set conflict that is only declared in one direction.

Run it any time; CI runs it on every push.

    python3 tools/audit_project.py
"""

import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = os.path.join(ROOT, 'common', 'src', 'main', 'resources')
fail = []

# 1. every JSON parses
docs = {}
for p in sorted(glob.glob(R + '/**/*.json', recursive=True)):
    try:
        docs[p] = json.load(open(p, encoding='utf-8'))
    except Exception as e:
        fail.append('JSON parse error %s: %s' % (p, e))
print('parsed %d json files' % len(docs))

ench = {os.path.basename(p)[:-5] for p in docs if '/data/volyera/enchantment/' in p}
print('enchantment files: %d' % len(ench))

# 2. lang coverage for every description translate key (+ .desc for Enchantment Descriptions)
lang = docs.get(R + '/assets/volyera/lang/en_us.json', {})
for p, d in docs.items():
    if '/data/volyera/enchantment/' not in p:
        continue
    k = d['description']['translate']
    if k not in lang:
        fail.append('%s: lang key missing %s' % (p, k))
    desc = k + '.desc'
    if desc not in lang:
        fail.append('%s: desc key missing %s' % (p, desc))
print('lang keys: %d' % len(lang))
unused = set(lang) - {d['description']['translate'] for d in docs.values()
                      if isinstance(d, dict) and 'description' in d}
unused -= {k for k in lang if k.endswith('.desc')}
if unused:
    fail.append('lang keys with no enchantment: %s' % sorted(unused))

# 3. tag references from enchantment documents
refs = set()
for p, d in docs.items():
    if '/data/volyera/enchantment/' not in p:
        continue
    for f in ('supported_items', 'primary_items', 'exclusive_set'):
        v = d.get(f)
        if isinstance(v, str) and v.startswith('#'):
            refs.add((p, v))
for p, ref in sorted(refs):
    ns, path = ref[1:].split(':', 1)
    if ns == 'volyera':
        if not os.path.exists('%s/data/volyera/tags/enchantment/%s.json' % (R, path)):
            fail.append('%s: tag file missing for %s' % (p, ref))
    elif not (path.startswith('enchantable/') or path.startswith('exclusive_set/')):
        fail.append('%s: unexpected vanilla tag %s' % (p, ref))
print('tag refs checked: %d' % len(refs))

# 4. tag value entries must resolve
for p, d in docs.items():
    if '/tags/enchantment/' not in p:
        continue
    for v in d.get('values', []):
        if v.startswith('#'):
            ns, path = v[1:].split(':', 1)
            if ns == 'volyera' and not os.path.exists(
                    '%s/data/volyera/tags/enchantment/%s.json' % (R, path)):
                fail.append('%s: nested tag %s has no file' % (p, v))
        elif v.startswith('volyera:') and v.split(':', 1)[1] not in ench:
            fail.append('%s: unknown volyera enchantment %s' % (p, v))

# 5. vanilla tag merges must be additive
for p, d in docs.items():
    if '/data/minecraft/tags/' in p and d.get('replace'):
        fail.append('%s: must not set replace:true' % p)

# 6. treasure/curse bookkeeping consistency
def ids(tagfile):
    p = '%s/data/minecraft/tags/enchantment/%s.json' % (R, tagfile)
    if not os.path.exists(p):
        return set()
    return {v.split(':', 1)[1] for v in docs[p]['values'] if v.startswith('volyera:')}

treasure, curses, non_treasure = ids('treasure'), ids('curse'), ids('non_treasure')
if treasure & non_treasure:
    fail.append('enchantments in both treasure and non_treasure: %s' % sorted(treasure & non_treasure))
if treasure | non_treasure != ench:
    fail.append('treasure+non_treasure != roster. missing=%s extra=%s' % (
        sorted(ench - (treasure | non_treasure)), sorted((treasure | non_treasure) - ench)))
if not curses <= treasure:
    fail.append('curses must also be treasure: %s' % sorted(curses - treasure))
if not curses <= ids('on_random_loot'):
    fail.append('curses should be findable in loot')

# 7. exclusive-set symmetry: if we add X to a vanilla exclusive_set tag, X's own
#    exclusive_set should list the vanilla members of that set too.
vanilla_excl = {}
for p, d in docs.items():
    m = re.search(r'data/minecraft/tags/enchantment/exclusive_set/(\w+)\.json$', p)
    if m:
        vanilla_excl[m.group(1)] = {v.split(':', 1)[1] for v in d['values'] if v.startswith('volyera:')}
for name, group in vanilla_excl.items():
    for e in group:
        doc = docs['%s/data/volyera/enchantment/%s.json' % (R, e)]
        own = doc.get('exclusive_set', '')
        if own == '#minecraft:exclusive_set/%s' % name:
            continue
        if not own.startswith('#volyera:'):
            fail.append('%s added to vanilla exclusive_set/%s but its own exclusive_set is %r'
                        % (e, name, own))
        else:
            members = docs['%s/data/volyera/tags/enchantment/%s.json'
                           % (R, own[1:].split(':', 1)[1])]['values']
            if not any(m.startswith('minecraft:') for m in members):
                fail.append('%s lists no vanilla enchantments in %s, so the conflict is one-way'
                            % (e, own))

# 8. placeholder coverage
props = {}
for line in open(os.path.join(ROOT, 'gradle.properties')):
    line = line.strip()
    if '=' in line and not line.startswith('#'):
        k, v = line.split('=', 1)
        props[k.strip()] = v.strip()
toml = open(os.path.join(ROOT, 'neoforge/src/main/templates/META-INF/neoforge.mods.toml')).read()
# Match ANY dollar-brace, not just well-formed ones. Gradle expands this file with
# Groovy's SimpleTemplateEngine, so a literal ${...} - even inside a TOML comment -
# is parsed as an expression and fails the build with an opaque template error.
# A \w+ pattern would quietly skip exactly the malformed cases that break.
need = set(re.findall(r'\$\{([^}]*)\}', toml))
missing = need - set(props)
if missing:
    fail.append('neoforge.mods.toml has dollar-brace text that is not a gradle.properties '
                'key (Groovy will try to evaluate it): %s' % sorted(missing))
print('toml placeholders: %s' % sorted(need))
fj = open(os.path.join(ROOT, 'fabric/src/main/resources/fabric.mod.json')).read()
print('fabric.mod.json placeholders: %s' % sorted(set(re.findall(r'\$\{(\w+)\}', fj))))

# 9. Java entrypoint class names referenced by metadata must exist
for meta, want in ((os.path.join(ROOT, 'fabric/src/main/resources/fabric.mod.json'),
                    'fabric/src/main/java/net/volyera/fabric/VolyeraFabric.java'),):
    d = json.load(open(meta))
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
