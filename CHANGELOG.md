# Changelog

All notable changes to Volyera are documented here.
Versioning follows [Semantic Versioning](https://semver.org/): MAJOR.MINOR.PATCH.

## [1.0.0] - 2026-08-31

Initial release. 🎉

### Added
- **Voidstrike** (Swords & Axes, I–IV) — bonus damage (+1.0, +0.75/level) and
  briefly shrouds the victim in Darkness with a burst of void particles.
  Mutually exclusive with the Sharpness/Smite damage family.
- **Lifeleech** (Swords & Axes, I–III) — striking a living creature grants
  Regeneration II (2s +1s/level). Does not trigger on the undead.
- **Frostbrand** (Swords, I–II) — inflicts Slowness (I→II by level) with
  snowflake particles and a freeze sound. Mutually exclusive with Fire Aspect.
- **Tempest** (Swords, I–II) — massive extra knockback (+1.5, +1.0/level) with
  a wind-burst gust on hit.
- **Featherstep** (Boots, I–II) — dedicated fall-damage protection (+4/level).
- **Duskveil** (Armor, I–III) — wards the wearer against arcane harm (magic,
  thorns, sonic boom). Mutually exclusive with the Protection family.
- All enchantments are obtainable from the enchanting table, villager trades,
  and loot chests (wired into `#minecraft:non_treasure`).
- Pixel-art mod icon.

### Notes
- 100% data-driven (Minecraft 1.21 enchantment format) — the jar contains no
  compiled code and only requires the Fabric Loader. Fabric API is not needed.
- Supported game versions: **1.21, 1.21.1** · Loader: **Fabric** (also runs
  under Quilt).
