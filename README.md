# Volyera

[![Build](https://github.com/OmniNodeCo/Volyera/actions/workflows/build.yml/badge.svg)](https://github.com/OmniNodeCo/Volyera/actions/workflows/build.yml)

**A Minecraft 26.2 mod adding 20 armour enchantments — for Fabric *and* NeoForge from one codebase.**

Volyera adds elemental wards, mobility boons, utility enchantments and two curses to every
armour slot. It targets Minecraft **26.2 "Chaos Cubed"** (Java 25, data pack format 107.1) and
builds one jar per loader from a single shared source tree.

---

## Contents

| Enchantment | Applies to | Max | What it does |
|---|---|---|---|
| **Warding** | any armour | IV | Reduces most incoming damage (0.75 EPF/level) *and* adds armour toughness. Protection family. |
| **Emberheart** | any armour | III | Strong fire protection, burns you for 20 % less time per level, and sets melee attackers alight at a durability cost. Protection family. |
| **Bulwark** | any armour | III | +1 armour toughness and +10 % knockback resistance per level. |
| **Colossus** | any armour | II | +1 heart, +2 armour and +15 % knockback resistance per level. Rare. |
| **Glacial Ward** | any armour | III | Immune to freezing damage, extra protection in powder snow, chance to inflict Slowness on attackers. |
| **Stormwarden** | any armour | II | Immune to lightning, heavy protection from it, and +10 % speed per level while a thunderstorm is active. |
| **Rejuvenation** | any armour | III | Grants a short burst of Regeneration every 5 seconds. |
| **Thornmail** | any armour | III | Chance to wound melee attackers for thorns damage, costing durability like vanilla Thorns. |
| **Prosperity** | any armour | III | +1 luck per level for better block and mob drops. |
| **Gilded Aegis** | any armour | I | *Treasure.* Toughness, knockback resistance, a bonus heart and luck in one enchantment. |
| **Tidewarden** | helmet | III | Immune to drowning, +1 breath and +20 % swim speed per level. |
| **Keeneye** | helmet | III | +0.5 block and entity interaction range per level. |
| **Shadowstride** | leggings | III | +12 % sneaking speed and +40 % movement efficiency per level (ignores soul-sand-style slowdown). |
| **Momentum** | leggings | III | +10 % speed per level once you are already moving quickly. |
| **Featherstep** | boots | III | +3 safe fall distance, −20 % fall damage and fall protection per level. |
| **Springstep** | boots | III | Uses the **bounciness** attribute added in 26.2 (and still present in 26.3), plus step height and jump strength. |
| **Abysswalker** | boots | III | Full swim speed and normal mining speed while submerged. |
| **Vanguard** | chestplate | II | +2 armour per level and a chance to inflict Weakness on melee attackers. |
| **Curse of Anchoring** | any equippable | I | *Treasure curse.* Slows you, increases gravity, reduces step height — and cannot be taken off. |
| **Curse of Frailty** | any equippable | I | *Treasure curse.* Reduces armour toughness and quietly drains durability over time. |

Costs, weights and anvil costs follow vanilla's own curves, so the enchantments slot into a normal
survival world rather than trivialising it.

### Obtaining them

The mod merges into vanilla's enchantment tags, so behaviour matches vanilla expectations:

* the 17 non-treasure enchantments appear in the **enchanting table**, in **villager trades** and in
  **random loot** (all three vanilla tags resolve through `#minecraft:non_treasure`);
* **Gilded Aegis** and the two curses are **treasure**: never on the enchanting table, but findable in
  loot chests. Treasure enchantments also inherit vanilla's doubled trade price;
* both curses are in `#minecraft:curse`, so they render red and cannot be removed by a grindstone.

### Conflicts

Exclusivity is declared in **both** directions so it holds regardless of which side of the
comparison the game evaluates:

* `Warding` and `Emberheart` join vanilla's `#minecraft:exclusive_set/armor` and additionally list
  each other plus the four vanilla protection enchantments in
  `#volyera:exclusive_set/protection_family` — you pick one protection line, exactly as in vanilla.
* `Bulwark` ⟷ `Colossus` (`fortress`), `Featherstep` ⟷ `Springstep` (`descent`),
  `Thornmail` ⟷ `Vanguard` ⟷ vanilla Thorns (`retaliation`).
* `Abysswalker` joins `#minecraft:exclusive_set/boots`, so it competes with Frost Walker and
  Depth Strider.

---

## Building

Requires a **Java 25** JDK. Gradle will auto-provision one via the foojay toolchain resolver if
yours is older, and the wrapper downloads Gradle 9.5.1 for you.

```bash
./gradlew build                                     # 26.2, both loaders (the default)
./gradlew :fabric:build -Pminecraft_version=26.3    # the 26.3 Fabric jar
```

Jars land in `fabric/build/libs/` and `neoforge/build/libs/`. The target game version is part of
the file name, so the three artifacts can sit side by side:

```
volyera-fabric-26.2-1.0.0.jar
volyera-fabric-26.3-1.0.0.jar
volyera-neoforge-26.2-1.0.0.jar
```

Install the jar matching **both** your loader and your Minecraft version. A 26.2 jar on a 26.3
server loads nothing and logs nothing — see the note below.

| Loader | Minecraft | Minimum version |
|---|---|---|
| Fabric Loader | 26.2, 26.3 | 0.19.5 |
| Fabric API | 26.2 | 0.160.0+26.2 |
| Fabric API | 26.3 | 0.160.6+26.3 |
| NeoForge | 26.2 | 26.2.0.87 |
| NeoForge | 26.3 | *not shipped — no stable release yet* |

**Fabric API is required on Fabric; nothing extra is required on NeoForge.** Volyera's behaviour is
entirely data-driven, but data-driven is not the same as self-loading: it is Fabric API's
`fabric-resource-loader-v1` module that registers a mod's `data/` folder with the game's pack
repository. Fabric Loader itself contains no pack-repository code. NeoForge treats every mod jar as
a resource pack natively, so it needs no equivalent.

This was learned the hard way and is now enforced by CI: with no resource loader, the jar still
contained all 20 enchantment files, the server still booted cleanly with zero errors, `/datapack
list` still showed only `vanilla`, and the enchantment registry was simply empty. A live-server
probe that summons an item wearing `volyera:warding` next to a `minecraft:protection` control is
what caught it — see the boot job in `.github/workflows/build.yml`.

Development runs:

```bash
./gradlew :fabric:runClient
./gradlew :neoforge:runClient
```

---

## Architecture

```
Volyera/
├── common/          loader-agnostic sources + ALL content (not a Gradle project)
│   └── src/
│       ├── main/
│       │   ├── java/net/volyera/
│       │   │   ├── Volyera.java              shared constants, logger, id() helper
│       │   │   └── VolyeraEnchantments.java  generated ResourceKey<Enchantment> constants
│       │   └── resources/                    shared by every game version
│       │       ├── assets/volyera/lang/en_us.json
│       │       ├── data/volyera/tags/enchantment/*.json      grouping + exclusive sets
│       │       └── data/minecraft/tags/enchantment/*.json    merges into vanilla tags
│       ├── mc262/resources/data/volyera/enchantment/*.json   20 enchantments, 26.2 format
│       └── mc263/resources/data/volyera/enchantment/*.json   20 enchantments, 26.3 format
├── fabric/          Loom module + ModInitializer entrypoint + fabric.mod.json
├── neoforge/        ModDevGradle module + @Mod entrypoint + neoforge.mods.toml template
└── tools/generate_enchantments.py   the authoring source for everything in common/
```

### Two versions, one source of truth

26.3 is a **breaking data-format release** for enchantments. Diffing the vanilla data between the
two versions shows 20 enchantment definitions changed and no components added or removed — every
difference comes from exactly two renames:

| | 26.2 | 26.3 |
|---|---|---|
| condition discriminator | `{"condition": "minecraft:random_chance"}` | `{"type": "minecraft:random_chance"}` |
| damage-source tag reference | `{"id": "minecraft:is_fire"}` | `{"id": "#minecraft:is_fire"}` |

Neither version's codec accepts the other's spelling, so one jar cannot serve both. Volyera's tags
and translations are byte-identical across the two versions (verified file by file), so only the 20
definitions are duplicated — into `common/src/mc262/` and `common/src/mc263/`, both written by the
generator. There is still no place to hand-edit one version and forget the other.

`-Pminecraft_version` selects the whole target at once: the resource tree, the Fabric API release,
the artifact name and the loader metadata's version dependency. The root `build.gradle` resolves it
once into `rootProject.ext.mc`, so no module can disagree with another. When a target has no
`neo_version_<target>` in `gradle.properties`, `settings.gradle` drops `:neoforge` from the build
entirely — which is what makes `-Pminecraft_version=26.3` work, since Gradle configures every
included project and a module that cannot configure itself would break a build that never asked
for it. Adding `neo_version_26_3` when NeoForge cuts a stable release brings the module back with
no other change.

> **Why this is enforced rather than trusted.** A jar built with the wrong version's data compiles,
> packages and boots without a single error — it just registers nothing. `tools/verify_jars.py`
> reads the Minecraft version out of the artifact *name* and asserts the packaged JSON uses that
> version's spelling, so the two can never silently disagree.

### Why there is almost no Java

Since 1.21, enchantments are **data-driven**: an enchantment is a JSON document whose behaviour is
assembled from vanilla *enchantment effect components* (`damage_protection`, `attributes`,
`post_attack`, `tick`, `location_changed`, `damage_immunity`, …). 26.2 changed none of this.

That matters twice over for a two-loader mod:

1. **The content needs no loader code at all.** Both loaders load a mod jar's `data/` folder as a
   built-in datapack, so the *same 20 JSON files* ship in both jars and behave identically.
2. **Minecraft 26.2 is unobfuscated.** There are no mappings to declare, and both loaders compile
   against Mojang's own names. That is what allows `common/` to be shared *verbatim* — each module
   simply adds it as a source directory. There is no abstraction layer, no service loader and no
   per-loader API shim, because none is needed.

The Java that remains is deliberately minimal: a mod id, a logger, an `Identifier` helper, and
generated `ResourceKey<Enchantment>` constants so other mods can reference a Volyera enchantment
without repeating a string literal. Adding behaviour that vanilla components cannot express would
be the point at which you introduce a real common/loader split — see *Extending* below.

### The generator is the source of truth

`tools/generate_enchantments.py` emits the enchantment JSON, both tag trees, the lang file **and**
`VolyeraEnchantments.java` from one roster, so the Java constants can never drift from the data.

It also validates before writing. Every effect component, effect type, level-based value provider,
condition, attribute, operation, slot, damage-type tag, mob effect and item tag used by the roster
is checked against a vocabulary extracted from **real Minecraft 26.2 generated data** — so a typo
fails here rather than silently breaking the datapack at game load.

```bash
python3 tools/generate_enchantments.py           # regenerate everything
python3 tools/generate_enchantments.py --check   # validate + fail on drift (runs in CI)
python3 tools/audit_project.py                   # cross-check what is on disk (runs in CI)
```

`audit_project.py` is deliberately separate: it reads the committed files instead of the in-memory
roster, so it also catches hand-edits. It verifies that every enchantment has both a name and a
`.desc` translation, that every tag entry points at an enchantment that exists, that the
treasure/non-treasure split exactly covers the roster, that curses are treasure and findable in
loot, and — the subtlest check — that every exclusive-set conflict is declared in *both* directions.

To change a number, edit the roster in the generator and re-run it. Do not hand-edit the JSON or
`VolyeraEnchantments.java`.

---

## Extending Volyera

**A new data-only enchantment** — add it to `build_enchantments()` in the generator, give it a
`DISPLAY_NAMES` and `DESCRIPTIONS` entry plus a `JAVA_DOC` line, and re-run. Decide whether it goes
in `TREASURE`/`CURSES`. The helpers (`protection`, `attribute`, `post_attack`, `mob_effect`, …)
only emit shapes vanilla 26.2 actually uses.

**Behaviour vanilla components cannot express** (lifesteal, cheat-death, area effects) needs Java,
and that is where the loader split finally earns its keep:

* put the shared logic in `common/`, written against plain Minecraft classes;
* register it per loader — `Registry.register(Registries.ENCHANTMENT_EFFECT_COMPONENT_TYPE, …)` on
  Fabric, `DeferredRegister` bound to the mod event bus on NeoForge;
* reference the new component type from the enchantment JSON like any other effect.

---

## Publishing

[`MODRINTH.md`](MODRINTH.md) holds a ready-to-paste Modrinth listing: the short summary, the full
description body, and the recommended values for every listing field (categories, environment,
loaders, game versions, dependencies). Both jars are content-identical, so one project with two
loaders is enough. Declare Fabric API as a required dependency for the Fabric file only.

---

## Verification status

Be aware of exactly what has and has not been machine-checked here.

**Verified against primary sources:**

* Minecraft 26.2 = Java 25, protocol 776, data pack format 107.1, resource pack format 88.0, and
  **no enchantment changes** in the 26.2 changelog. Minecraft 26.3 = Java 25, data pack format
  121.0, resource pack format 97.1.
* **The 26.3 enchantment format was derived by diffing vanilla data, not assumed.** Comparing
  `data/minecraft/enchantment/` between the 26.2 and 26.3 asset branches shows 20 definitions
  changed, none added or removed, and no effect components added or removed — every difference
  reduces to the two renames in [Two versions, one source of truth](#two-versions-one-source-of-truth).
  Tags under `data/minecraft/tags/enchantment/` were compared file by file and are identical, which
  is why they stay shared. NeoForge 26.3 exists only as `26.3.0.1-beta` — the official MDK-26.3
  pins that, and unlike `26.1.2` and `26.2.0` the `26.3.0` tag has no `-stable` counterpart — which
  is why 26.3 ships Fabric-only.
* Every enchantment JSON shape was derived from the **actual vanilla 26.2 data files**
  (`data/minecraft/enchantment/*.json`), including the 26.x flattening of `minecraft:attributes`,
  the `prevent_armor_change` / `prevent_equipment_drop` split, and `change_item_damage` replacing
  the older `damage_item`.
* Attribute ids (including 26.2's new `bounciness`, `friction_modifier`, `air_drag_modifier`),
  mob effect ids, damage-type tags, `enchantable/*` item tags, exclusive-set tags and the
  `non_treasure` / `treasure` / `on_random_loot` / `curse` / `tooltip_order` tag contents were all
  read from 26.2 data rather than assumed.
* Build configuration is taken from the **official 26.2 templates**: `NeoForgeMDKs/MDK-26.2-ModDevGradle`
  (NeoForge 26.2.0.87, ModDevGradle 2.0.147, Java 25 toolchain) and `FabricMC/fabric-example-mod@26.2`
  (Loom 1.17-SNAPSHOT, Loader 0.19.5, Gradle 9.5.1, `net.fabricmc.fabric-loom`, `implementation`
  instead of `modImplementation`, no `mappings` line).
* Java API usage (`Identifier.fromNamespaceAndPath`, `ResourceKey#identifier()`,
  `net.minecraft.world.item.enchantment.Enchantment`, `net.minecraft.core.registries.Registries`,
  `@Mod`, `ModInitializer`) was cross-checked against a shipping 26.2 multiloader mod.

**Verified by CI on GitHub Actions** (this workspace has no JDK and cannot reach the Gradle,
NeoForged, Fabric or Mojang Maven repositories, so all of it was proven in CI):

* **Both loaders compile and package, for every supported version.** Three artifacts per run:
  `:fabric:build -Pminecraft_version=26.2`, `:fabric:build -Pminecraft_version=26.3` and
  `:neoforge:build` (26.2) under ModDevGradle 2.0.147 / NeoForge 26.2.0.87, on Gradle 9.5.1 with a
  Java 25 toolchain. The version coordinates above are not guesses — they resolved and built.
* **All three jars contain the right bytes.** `tools/verify_jars.py` runs against the finished
  artifacts and asserts 66 conditions: all 20 enchantment definitions and all 15 tag files are
  present in *each* jar, every packaged enchantment JSON still parses and carries its required
  fields, no class targets a JVM newer than Java 25 (class file major 69), nothing leaked across
  loaders, each loader's metadata is fully expanded with the right id, version and entrypoint, and
  the version pinned in that metadata is the one the packaged data is actually written in. Output is
  mirrored into a commit comment on every run.
* **Real servers accept the data, and the enchantments are registered.** CI boots a dedicated
  server for each of the three artifacts — Fabric 26.2, Fabric 26.3, NeoForge 26.2 — and asks the
  live console to put `volyera:warding` on an item, beside a `minecraft:protection` control so an
  out-of-date SNBT syntax cannot masquerade as a result. All three decode it cleanly, reach `Done`
  with the mod loaded and zero data load errors, and report the mod's pack as enabled —
  `[volyera (Fabric mod)]` on Fabric, `[mod_data]` on NeoForge. See the "Server boot check" comment
  on any recent commit.

Three things this caught that nothing else would have:

* The `levels:` wrapper is **gone** from the `minecraft:enchantments` item component in 26.2. It is
  now a flat map. Minecraft logs the decode failure and then summons the item anyway with the
  enchantment silently dropped, so a check that only looked for a successful summon passed while
  proving nothing. For commands and datapacks that means:

  ```
  /give @s diamond_chestplate[minecraft:enchantments={"volyera:warding":1}]
  ```

* On Fabric the data was not being read at all until `fabric-resource-loader-v1` was added — see
  the requirements above. The jar was correct, the server booted cleanly, no error was logged, and
  the enchantment registry was simply empty.

* The 26.3 format split is invisible until it isn't. A jar carrying the *wrong version's* data
  compiles, packages and boots with zero errors — it just registers nothing, exactly like the two
  failures above. `tools/verify_jars.py` therefore reads the Minecraft version out of the artifact
  name and asserts the JSON inside is written in that version's spelling, and `tools/audit_project.py`
  checks each resource tree against its own format before anything is built.

**Not covered:** the probe exercises one enchantment (`warding`) for registry presence. The other
19 load from the same pack and would have logged a parse or validation error had any of them been
malformed, but their *effects* — the actual damage protection numbers, `bounciness`, the curses —
have never been exercised in gameplay, and nothing client-side has been tested: no tooltips, no
in-world rendering, no enchanting-table UI.

---

## License

MIT — see [LICENSE](LICENSE).
