# Volyera

**Volyera** is a Fabric mod for Minecraft **1.21 through 26.2** that weaves six
new enchantments into the world. The enchantments are fully **data-driven**
(built on the 1.21 enchantment data format); since v1.1.0 the mod also adds the
**Voidsteel Arsenal** (weapons + crafting), which uses a small amount of code
and requires the **Fabric API**.

> Ready-to-play jars for every supported Minecraft version live in
> [`dist/`](dist/) (refreshed by CI on every push). Pick the jar matching your
> game version, e.g. `volyera-1.2.0+26.2.jar` for Minecraft 26.2.

## Supported Minecraft versions

One jar per version family, all built from this repo:

| Jar | Runs on |
|---|---|
| `volyera-1.2.0+1.21.1.jar` | 1.21, 1.21.1 |
| `volyera-1.2.0+1.21.4.jar` | 1.21.4 |
| `volyera-1.2.0+1.21.5.jar` | 1.21.5 |
| `volyera-1.2.0+1.21.8.jar` | 1.21.6, 1.21.7, 1.21.8 |
| `volyera-1.2.0+1.21.10.jar` | 1.21.9, 1.21.10 |
| `volyera-1.2.0+1.21.11.jar` | 1.21.11 |
| `volyera-1.2.0+26.1.jar` | 26.1, 26.1.1, 26.1.2 |
| `volyera-1.2.0+26.2.jar` | 26.2 (and 26.2.x hotfixes) |

(1.21.2/1.21.3 are not targeted — tiny short-lived releases.)

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

1. Install the [Fabric Loader](https://fabricmc.net/use/) for your Minecraft version.
2. Install the matching [Fabric API](https://modrinth.com/mod/fabric-api).
3. Drop the Volyera jar matching your game version into your `mods/` folder.

## Building from source

```bash
./gradlew build                     # newest target (26.2)
./gradlew build -PmcTarget=1.21.1   # any specific version
./gradlew buildAll                  # every supported version
```

Jars are produced in `build/libs/`. The multi-version machinery lives in
`build.gradle` (target table) and `versions/` (per-era code + resource
variants):

- `versions/code/v1_21_1`  — Tier + SwordItem attributes (1.21–1.21.1)
- `versions/code/v1_21_4`  — ToolMaterial + SwordItem, `setId` (1.21.4)
- `versions/code/v1_21_5`  — `Properties().sword(...)` (1.21.5–1.21.10)
- `versions/code/v1_21_11` — `ResourceLocation` → `Identifier` (1.21.11)
- `versions/code/v26`      — `FabricCreativeModeTab`, unobfuscated MC (26.1+)
- `versions/res/legacy`    — object-style recipe ingredients (1.21–1.21.1)
- `versions/res/modern`    — string ingredients + item model definitions (1.21.4+)

A ready-made matrix workflow lives in [`ci/build.yml`](ci/build.yml) — copy it
to `.github/workflows/build.yml` to build all versions in parallel on every
push (the automation used to create this repo cannot push workflow files).

## Automated publishing to Modrinth

[`ci/publish.yml`](ci/publish.yml) builds all 8 jars and uploads each one to
Modrinth as its own version (correct game-version tags, Fabric + Quilt,
Fabric API marked required), and attaches them to the GitHub release.

One-time setup:

1. Create the project once on [modrinth.com](https://modrinth.com) (upload the
   icon from `src/main/resources/assets/volyera/icon.png`, paste the
   description from `MODRINTH.md`).
2. Modrinth → user settings → **PATs** → create a token with the
   **Create versions** scope → save it as the GitHub Actions **secret**
   `MODRINTH_TOKEN`.
3. Copy the project ID (project page → ⋮ → *Copy ID*) → save it as the GitHub
   Actions **variable** `MODRINTH_ID`.
4. Copy `ci/publish.yml` to `.github/workflows/publish.yml`.

Then every release is one command:

```bash
git tag v1.2.0 && git push origin v1.2.0
```

…or press *Run workflow* on the Actions tab, where the **targets** input lets
you publish only some versions (e.g. `26.2, 1.21.8`) instead of `all`. Bump
`mod_version` in `gradle.properties` (and add a `CHANGELOG.md` entry) before
tagging.

### Troubleshooting `401 (Unauthorized … permission to upload this version)`

Modrinth rejected the token at upload time. Check, in order:

1. **Scope** — the PAT must have the **Create versions** scope ticked
   (Modrinth → Settings → PATs). Recreate it if unsure; scopes can't be
   inspected after creation.
2. **Expiry** — Modrinth PATs require an expiry date; an expired token 401s.
3. **Account** — the PAT must belong to the account (or org member with the
   *Upload version* permission) that owns the project. A token from another
   account can't upload.
4. **Copy/paste** — the secret must be the full token (starts with `mrp_`),
   no spaces or trailing newline. Re-save the `MODRINTH_TOKEN` secret.
5. **Project ID** — `MODRINTH_ID` must be *your* project's ID (project page
   → ⋮ → Copy ID). Publishing to someone else's project 401s the same way.

The workflow's `prepare` job now pre-checks the project ID and token and
prints what it found, so a bad credential fails fast with a clear message.

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
