# Volyera

**Volyera** is a Fabric mod for Minecraft **1.21 / 1.21.1** that weaves six new
enchantments into the world. The enchantments are fully **data-driven**
(built on the 1.21 enchantment data format); since v1.1.0 the mod also adds the
**Voidsteel Arsenal** (weapons + crafting), which uses a small amount of code
and requires the **Fabric API**.

> v1.1.0+ jars are built by `./gradlew build` or the GitHub Actions workflow
> (Actions tab → latest build → `Volyera` artifact). The legacy data-only
> [`dist/volyera-1.0.0.jar`](dist/volyera-1.0.0.jar) (enchantments only, no
> Fabric API needed) remains available.

## Enchantments

| Enchantment | Applies to | Max | Effect |
|---|---|---|---|
| **Voidstrike** | Swords & axes | IV | Bonus damage (+1.0, +0.75/level) and briefly shrouds the victim in *Darkness*, with a burst of void particles. Exclusive with Sharpness/Smite/etc. |
| **Lifeleech** | Swords & axes | III | Striking a *living* creature grants you Regeneration II (2s +1s/level). The undead have no life to leech. |
| **Frostbrand** | Swords | II | Chills victims with Slowness (I→II by level) in a flurry of snowflakes. Exclusive with Fire Aspect. |
| **Tempest** | Swords | II | Massive extra knockback (+1.5, +1.0/level) with a gust of wind on hit. |
| **Featherstep** | Boots | II | Strong dedicated fall-damage protection (+4/level) — stacks with armor, softer landings than Feather Falling. |
| **Duskveil** | Armor | III | Wards the wearer against arcane harm (magic, thorns, sonic booms). Exclusive with the Protection family. |

All six are obtainable from the **enchanting table**, **villager trades**,
and **loot chests** (they're wired into `#minecraft:non_treasure`).

## The Voidsteel Arsenal (v1.1.0+)

| Item | Stats | Recipe |
|---|---|---|
| **Void Shard** | material | 4 amethyst shards around an ender pearl → ×4 |
| **Voidsteel Ingot** | material | 2 void shards + iron ingot + obsidian (shapeless) |
| **Voidsteel Sword** | 8 dmg · 1.6 spd | ingot / ingot / stick |
| **Voidsteel Dagger** | 5 dmg · 3.0 spd | ingot / stick |
| **Voidsteel War Axe** | 10 dmg · 1.0 spd | axe pattern with ingots |

Voidsteel sits between diamond and netherite (1796 durability, enchantability
18) and accepts every sword/axe enchantment, including Volyera's own.

## Installation

1. Install the [Fabric Loader](https://fabricmc.net/use/) for Minecraft 1.21 or 1.21.1.
2. Install the [Fabric API](https://modrinth.com/mod/fabric-api).
3. Drop the Volyera jar into your `mods/` folder.

## Building from source

```bash
./gradlew build
```

The jar is produced in `build/libs/`. A ready-made GitHub Actions workflow lives
in [`ci/build.yml`](ci/build.yml) — copy it to `.github/workflows/build.yml` to
build the jar automatically on every push (the automation used to create this
repo cannot push workflow files itself).

(`scripts/package_jar.py` built the data-only 1.0.0 jar; from 1.1.0 the mod
contains compiled code, so use Gradle or CI instead.)

## Project layout

```
src/main/resources/
├── fabric.mod.json                     # mod metadata (no entrypoints — data only)
├── assets/volyera/
│   ├── icon.png                        # mod icon (pixel art)
│   └── lang/en_us.json                 # enchantment names
└── data/
    ├── volyera/enchantment/*.json      # the six enchantment definitions
    ├── volyera/tags/enchantment/       # Frostbrand↔Fire Aspect exclusivity
    └── minecraft/tags/enchantment/     # enchanting-table/trade/loot wiring
```

## Roadmap

- Custom mobs, items, and blocks (will introduce code entrypoints + Fabric API).
- More enchantments, including treasure-only ones.

## License

MIT
