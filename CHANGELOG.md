# Changelog

All notable changes to Volyera are documented here.
Versioning follows [Semantic Versioning](https://semver.org/): MAJOR.MINOR.PATCH.

## [1.1.0] - 2026-08-31

### Added
- **The Voidsteel Arsenal** — a new weapon tier forged from the dark between the stars:
  - **Void Shard** — crafted from 4 amethyst shards around an ender pearl (yields 4).
  - **Voidsteel Ingot** — 2 void shards + iron ingot + obsidian (shapeless).
  - **Voidsteel Sword** — 8 damage / 1.6 speed, 1796 durability.
  - **Voidsteel Dagger** — 5 damage / blistering 3.0 speed.
  - **Voidsteel War Axe** — 10 damage / 1.0 speed.
- Weapons enchant exceptionally well (enchantability 18) and accept all sword/axe
  enchantments — including Voidstrike, Lifeleech, Frostbrand, and Tempest.
- Custom **Volyera creative tab**, hand-made pixel-art textures, crafting recipes
  with vanilla-style recipe-book unlocks.

### Changed
- The mod now contains code and requires **Fabric API** (still tiny). Jars are
  produced by `./gradlew build` or the GitHub Actions workflow.

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
