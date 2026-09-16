# Changelog

All notable changes to Volyera are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and the project uses [semantic versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-09-15

First release. Targets Minecraft **26.2 "Chaos Cubed"** (Java 25, data pack format 107.1)
on **Fabric** (Loader 0.19.5+) and **NeoForge** (26.2.0.87+) from one shared source tree.

### Added

20 armour enchantments, all data-driven so both loader jars ship identical content:

- **Any armour** — Warding, Emberheart, Bulwark, Colossus, Glacial Ward, Stormwarden,
  Rejuvenation, Thornmail, Prosperity, Gilded Aegis (treasure).
- **Helmet** — Tidewarden, Keeneye.
- **Leggings** — Shadowstride, Momentum.
- **Boots** — Featherstep, Springstep, Abysswalker.
- **Chestplate** — Vanguard.
- **Curses** (treasure) — Curse of Anchoring, Curse of Frailty.

Supporting content:

- Merges into vanilla's `non_treasure`, `treasure`, `on_random_loot`, `curse`, `tooltip_order`,
  `exclusive_set/armor` and `exclusive_set/boots` enchantment tags, so the enchantments are
  obtainable from the enchanting table, villager trades and loot with vanilla-consistent rules.
- `volyera:all`, `volyera:armor`, `volyera:treasure`, `volyera:curse` and four
  `volyera:exclusive_set/*` tags for packs and other mods to reference.
- `en_us` translations, including `.desc` keys so Enchantment Descriptions populates tooltips
  with no extra integration work.

Tooling:

- `tools/generate_enchantments.py` generates the enchantment JSON, both tag trees, the lang file
  and `VolyeraEnchantments.java` from a single roster, and validates every generated document
  against a vocabulary extracted from real Minecraft data. It emits the 20 enchantment definitions
  **once per supported game version** into `common/src/mc262/` and `common/src/mc263/`, so the two
  formats cannot drift apart by hand. `--check` mode fails on drift and runs in CI.
- `tools/verify_jars.py` reads the target Minecraft version out of each artifact's *name* and
  asserts the enchantment JSON packaged inside is written in that version's spelling — the only
  check standing between a green build and an empty registry.
- GitHub Actions workflow building all three artifacts on JDK 25, verifying them, and booting a live
  server for each one.

### Requirements

- **Fabric:** Fabric Loader 0.19.5+ **and Fabric API** — `0.160.0+26.2` for the 26.2 jar,
  `0.160.6+26.3` for the 26.3 jar. Volyera calls no Fabric API code, but it depends on the
  `fabric-resource-loader-v1` module, which is what registers a mod's `data/` folder with the game's
  pack repository. Fabric Loader contains no pack-repository code of its own, so without that module
  the enchantment files ship in the jar and are never read: the server boots cleanly, logs nothing
  wrong, and the enchantment registry stays empty.
- **NeoForge:** 26.2.0.87+, for Minecraft 26.2 only. No extra dependency — NeoForge treats every mod
  jar as a resource pack natively.
- **No NeoForge 26.3 file, deliberately.** NeoForge has released only `26.3.0.1-beta` for that
  version; unlike `26.1.2` and `26.2.0` there is no `-stable` tag to build against, and the official
  MDK-26.3 pins the beta. `settings.gradle` drops the `:neoforge` module when the target version has
  no `neo_version_<version>` property, so adding one later brings the NeoForge 26.3 jar back with no
  other change.

### Notes

- **26.3 changed the enchantment data format**, in exactly two ways, confirmed by diffing vanilla
  `data/minecraft/enchantment/` between the two versions (20 definitions changed, none added or
  removed, no effect components added or removed):
  - the condition discriminator was renamed — `{"condition": "minecraft:random_chance"}` became
    `{"type": "minecraft:random_chance"}`;
  - damage-source tag references became `#`-prefixed — `"id": "minecraft:is_fire"` became
    `"id": "#minecraft:is_fire"`.

  This affects 11 of Volyera's 20 enchantments. Tags and translations are byte-identical between the
  two versions, so only the definitions are duplicated per version.
- Springstep uses the `bounciness` attribute, which is new in 26.2 and unchanged in 26.3.
- Warding and Emberheart are deliberately exclusive with the vanilla Protection family;
  Abysswalker with Frost Walker and Depth Strider.

[1.0.0]: https://github.com/OmniNodeCo/Volyera/releases/tag/v1.0.0
