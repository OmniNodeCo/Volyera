# Modrinth listing for Volyera

Everything below is ready to paste into Modrinth. The **Summary** goes in the
short summary field; the **Description** is the Markdown body.

---

## Summary (short field, ≤ 256 characters)

> 20 new armour enchantments for Minecraft 26.2 — elemental wards, mobility boons and two real curses. Fully data-driven, so the Fabric and NeoForge jars ship identical content. Fabric needs Fabric API.

*(200 characters)*

---

## Description (Markdown body)

**Volyera** adds twenty armour enchantments to Minecraft **26.2 "Chaos Cubed"** — elemental wards
that retaliate against what hits you, mobility boons that change how your boots feel, a few quiet
utility upgrades, and two curses worth being afraid of.

Every one of them is **data-driven**: Volyera defines its enchantments with vanilla's own enchantment
effect components rather than custom code. That is why the Fabric and NeoForge jars behave
identically, and why pack makers can retune any number with a datapack. On Fabric it still needs
**Fabric API**, because Fabric API's resource-loader module is what makes the game read a mod's
`data/` folder at all; NeoForge does that natively and needs nothing extra.

<br>

### The enchantments

#### Any armour piece

| Enchantment | Max | What it does |
|---|:---:|---|
| 🛡️ **Warding** | IV | Reduces most incoming damage *and* adds armour toughness, so it holds up better against heavy hits than raw protection. Part of the Protection family. |
| 🔥 **Emberheart** | III | Strong fire protection, you burn 20% less per level, and melee attackers get set alight — at a durability cost. Part of the Protection family. |
| 🧱 **Bulwark** | III | +1 armour toughness and +10% knockback resistance per level. |
| 🗿 **Colossus** | II | +1 heart, +2 armour and +15% knockback resistance per level. Rare. |
| ❄️ **Glacial Ward** | III | Immune to freezing damage, extra protection in powder snow, and a chance to inflict Slowness on whatever hits you. |
| ⛈️ **Stormwarden** | II | Immune to lightning, heavily protected from it, and +10% speed per level while a thunderstorm is raging. |
| 💗 **Rejuvenation** | III | Grants a short burst of Regeneration every five seconds. |
| 🌵 **Thornmail** | III | A chance to wound melee attackers for thorns damage, wearing your armour down as it does. |
| 🍀 **Prosperity** | III | +1 luck per level, for better drops from blocks and mobs. |
| 👑 **Gilded Aegis** | I | **Treasure.** Toughness, knockback resistance, a bonus heart *and* luck in a single enchantment. |

#### Helmet

| Enchantment | Max | What it does |
|---|:---:|---|
| 🌊 **Tidewarden** | III | Immune to drowning, +1 breath and +20% swim speed per level. |
| 👁️ **Keeneye** | III | +0.5 block and entity interaction range per level. |

#### Leggings

| Enchantment | Max | What it does |
|---|:---:|---|
| 🌑 **Shadowstride** | III | +12% sneaking speed and +40% movement efficiency per level — soul sand stops slowing you down. |
| 💨 **Momentum** | III | +10% speed per level, but only once you are already moving quickly. |

#### Boots

| Enchantment | Max | What it does |
|---|:---:|---|
| 🪶 **Featherstep** | III | +3 safe fall distance, −20% fall damage and fall protection per level. |
| 🦘 **Springstep** | III | Bouncy, taller steps and a better jump. Built on 26.2's brand-new **bounciness** attribute. |
| 🌀 **Abysswalker** | III | Full swim speed *and* normal mining speed while submerged. |

#### Chestplate

| Enchantment | Max | What it does |
|---|:---:|---|
| ⚔️ **Vanguard** | II | +2 armour per level and a chance to inflict Weakness on melee attackers. |

#### Curses *(treasure only)*

| Enchantment | Max | What it does |
|---|:---:|---|
| ⚓ **Curse of Anchoring** | I | Slows you, pulls you down, reduces step height — **and cannot be taken off.** |
| 🥀 **Curse of Frailty** | I | Softens your armour and quietly eats its durability over time. |

<br>

### Getting them

Volyera hooks into vanilla's own enchantment tags instead of inventing new rules, so everything
behaves the way you would expect:

- The **17 non-treasure** enchantments show up in the **enchanting table**, in **villager trades**,
  and in **loot chests**.
- **Gilded Aegis** and both **curses** are treasure: never on the enchanting table, but findable in
  loot. Treasure enchantments also cost double in trades, exactly like vanilla.
- Both curses render red and cannot be scrubbed off at a grindstone.

Costs, weights and anvil costs follow vanilla's curves, so Volyera slots into a normal survival
world rather than flattening it.

<br>

### Conflicts, on purpose

Some Volyera enchantments deliberately compete with vanilla ones, and the conflicts are declared in
both directions so they behave consistently:

- **Warding** and **Emberheart** join vanilla's armour exclusive set — you choose one protection
  line, just as you already choose between Protection and Fire Protection.
- **Abysswalker** competes with **Frost Walker** and **Depth Strider**.
- Within Volyera: **Bulwark** ⟷ **Colossus**, **Featherstep** ⟷ **Springstep**,
  **Thornmail** ⟷ **Vanguard** (and vanilla Thorns).

Everything else stacks.

<br>

### Requirements

| | |
|---|---|
| **Minecraft** | 26.2 (Java Edition) |
| **Java** | 25 or newer |
| **Loaders** | Fabric · NeoForge |
| **Fabric Loader** | 0.19.5+ |
| **NeoForge** | 26.2.0.87+ |
| **Fabric API** | **Required on Fabric** (`fabric-resource-loader-v1`, part of Fabric API 0.160.0+) — not needed on NeoForge |

Install the jar for your loader into your `mods` folder. Works on dedicated servers — put it on
both sides so names and tooltips resolve correctly.

<br>

### For pack makers and mod developers

- Every number lives in JSON under `data/volyera/enchantment/`. Override it from a datapack loaded
  after Volyera — no fork needed.
- Handy tags: `#volyera:all`, `#volyera:armor`, `#volyera:treasure`, `#volyera:curse`, plus the
  `#volyera:exclusive_set/*` groups.
- Enchantment IDs follow `volyera:<name>` (for example `volyera:emberheart`).
- Tooltip descriptions ship under `enchantment.volyera.<name>.desc`, which is the key
  **Enchantment Descriptions** looks for first — so descriptions appear automatically if you have it.

<br>

### Licence & source

MIT. Source, issue tracker and the generator tooling live in the repository linked in the sidebar.
The enchantment data is produced by a script that validates every file against the vocabulary
vanilla 26.2 actually defines, so nothing here relies on undocumented or removed effect components.

---

## Other listing fields

| Field | Value |
|---|---|
| **Name** | Volyera |
| **Slug** | `volyera` |
| **License** | MIT |
| **Categories** | Equipment · Magic · Library & API *(optional)* |
| **Environments** | Client: **required** · Server: **required** |
| **Project type** | Mod |
| **Loaders** | Fabric, NeoForge |
| **Game versions** | 26.2 |
| **Source URL** | `https://github.com/OmniNodeCo/Volyera` |
| **Issues URL** | `https://github.com/OmniNodeCo/Volyera/issues` |

### Dependencies

On the **Fabric** file, declare **Fabric API** as a *required* dependency. Volyera uses none of its
APIs — it needs only `fabric-resource-loader-v1`, the module that registers a mod's `data/` folder
with the game's pack repository, without which the enchantments are never loaded. Modrinth resolves
that module to the Fabric API project, so list Fabric API itself.

On the **NeoForge** file, declare **no** dependencies: NeoForge loads mod data natively.

Consider suggesting **Enchantment Descriptions** as an optional companion, since Volyera ships
`.desc` keys for it.

### Version files

Upload both jars to each version, tagged by loader:

| File | Loaders | Name it |
|---|---|---|
| `volyera-fabric-26.2-1.0.0.jar` | Fabric | Volyera 1.0.0 (Fabric, MC 26.2) |
| `volyera-neoforge-26.2-1.0.0.jar` | NeoForge | Volyera 1.0.0 (NeoForge, MC 26.2) |

Set **Release channel** to *Release*, **Game versions** to `26.2`. Modrinth lets one version carry
multiple loaders, but because these are separate jars it is cleaner to publish two versions.

### Gallery suggestions

The listing has no images yet. Shots that would carry it: an enchanting table offering Emberheart;
a chestplate with Warding IV + Thornmail III in the tooltip; Springstep bouncing on a sulfur cube;
the red Curse of Anchoring tooltip. Add a 16:9 banner and a square icon — `fabric.mod.json` and
`neoforge.mods.toml` will need an `icon` / `logoFile` entry once you have one.
