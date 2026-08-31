# Volyera

**Volyera** is a Fabric mod for Minecraft **1.21 / 1.21.1** that weaves six new
enchantments into the world. It is fully **data-driven** (built on the 1.21
enchantment data format), so the released jar contains no compiled code — it
works as a lightweight jar addon that only requires the Fabric Loader. The
Fabric API is *not* required.

> Ready-to-play jar: [`dist/volyera-1.0.0.jar`](dist/volyera-1.0.0.jar) — drop
> it into your `mods/` folder.

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

## Installation

1. Install the [Fabric Loader](https://fabricmc.net/use/) for Minecraft 1.21 or 1.21.1.
2. Drop `volyera-1.0.0.jar` into your `mods/` folder.
3. That's it — no Fabric API needed.

## Building from source

```bash
./gradlew build
```

The jar is produced in `build/libs/`. A ready-made GitHub Actions workflow lives
in [`ci/build.yml`](ci/build.yml) — copy it to `.github/workflows/build.yml` to
build the jar automatically on every push (the automation used to create this
repo cannot push workflow files itself).

Because the mod is currently 100% data-driven, the jar can also be assembled
without a toolchain — see `scripts/package_jar.py`, which zips
`src/main/resources` into a valid mod jar.

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
