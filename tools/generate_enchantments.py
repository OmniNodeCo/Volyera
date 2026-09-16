#!/usr/bin/env python3
"""
Volyera - enchantment data generator & validator.

Minecraft 26.2 enchantments are *data-driven*: an enchantment is a JSON document
in `data/<namespace>/enchantment/<id>.json` whose behaviour is assembled from
vanilla "enchantment effect components". Because the format is pure data, the
exact same files are shipped by both the Fabric and the NeoForge jar (see
`common/src/main/resources`), so there is no loader-specific enchantment code.

This script is the authoring source for those files. It exists for two reasons:

  1. Consistency - every enchantment is built from the same small set of helpers,
     so costs/weights/effects stay on vanilla's curves.
  2. Validation - `validate()` cross-checks every generated document against the
     vocabulary that vanilla 26.2 actually uses, so a typo in an effect name,
     attribute id, damage-type tag or item tag fails here instead of silently
     breaking the datapack at game load.

Usage:
    python3 tools/generate_enchantments.py            # regenerate + validate
    python3 tools/generate_enchantments.py --check    # validate only, fail on drift

The vocabulary constants below were extracted from the real Minecraft 26.2
generated data (`data/minecraft/enchantment/*.json`, `data/minecraft/tags/**`),
not guessed.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

NS = "volyera"
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMMON_SRC = os.path.join(REPO_ROOT, "common", "src")

# Resources that every supported Minecraft version parses identically: the
# translations and all tag files. The vanilla tag trees for 26.2 and 26.3 were
# diffed file by file and are byte-identical, so they stay shared.
RES_ROOT = os.path.join(COMMON_SRC, "main", "resources")
VOL_TAG_DIR = os.path.join(RES_ROOT, "data", NS, "tags", "enchantment")
MC_TAG_DIR = os.path.join(RES_ROOT, "data", "minecraft", "tags", "enchantment")

# Minecraft versions this generator can emit. 26.3 renamed the condition
# discriminator from "condition" to "type" and made damage-source tag
# references "#"-prefixed. Both are breaking and neither is accepted by the
# other version's codec, so the enchantment definitions - and only those - are
# emitted once per version into their own resource tree.
SUPPORTED_VERSIONS = ("26.2", "26.3")


def _vparts(version: str) -> tuple[int, ...]:
    return tuple(int(part) for part in version.split("."))


def version_res(version: str) -> str:
    """Resource tree holding what only that Minecraft version can parse."""
    return os.path.join(COMMON_SRC, "mc" + version.replace(".", ""), "resources")


TARGET = SUPPORTED_VERSIONS[0]
COND_KEY = "condition"   # "type" from 26.3
TAG_PREFIX = ""          # "#"  from 26.3
ENCH_DIR = os.path.join(version_res(TARGET), "data", NS, "enchantment")


def set_target(version: str) -> None:
    """Point the emitters at one Minecraft version."""
    global TARGET, COND_KEY, TAG_PREFIX, ENCH_DIR
    if version not in SUPPORTED_VERSIONS:
        raise ValueError(f"unsupported Minecraft version {version!r}; "
                         f"expected one of {SUPPORTED_VERSIONS}")
    modern = _vparts(version) >= (26, 3)
    TARGET = version
    COND_KEY = "type" if modern else "condition"
    TAG_PREFIX = "#" if modern else ""
    ENCH_DIR = os.path.join(version_res(version), "data", NS, "enchantment")


def cond(kind: str, **fields: Any) -> dict:
    """A condition object, keyed however the target version wants it."""
    return {COND_KEY: kind, **fields}

# ---------------------------------------------------------------------------
# Vocabulary verified against vanilla Minecraft 26.2 data
# ---------------------------------------------------------------------------

# Effect component keys used by vanilla 26.2 enchantments.
EFFECT_COMPONENTS = {
    "minecraft:attributes", "minecraft:damage", "minecraft:post_attack",
    "minecraft:damage_protection", "minecraft:location_changed", "minecraft:knockback",
    "minecraft:prevent_armor_change", "minecraft:armor_effectiveness",
    "minecraft:hit_block", "minecraft:smash_damage_per_fallen_block",
    "minecraft:projectile_spawned", "minecraft:damage_immunity", "minecraft:ammo_use",
    "minecraft:equipment_drops", "minecraft:trident_return_acceleration",
    "minecraft:fishing_luck_bonus", "minecraft:post_piercing_attack",
    "minecraft:fishing_time_reduction", "minecraft:repair_with_xp",
    "minecraft:projectile_count", "minecraft:projectile_spread",
    "minecraft:projectile_piercing", "minecraft:crossbow_charge_time",
    "minecraft:crossbow_charging_sounds", "minecraft:trident_sound",
    "minecraft:trident_spin_attack_strength", "minecraft:block_experience",
    "minecraft:tick", "minecraft:item_damage", "minecraft:prevent_equipment_drop",
}

# Entity / value effect "type" discriminators seen in vanilla 26.2 data.
EFFECT_TYPES = {
    "minecraft:add", "minecraft:all_of", "minecraft:ignite", "minecraft:set",
    "minecraft:remove_binomial", "minecraft:apply_mob_effect", "minecraft:replace_disk",
    "minecraft:multiply", "minecraft:change_item_damage", "minecraft:spawn_particles",
    "minecraft:play_sound", "minecraft:explode", "minecraft:attribute",
    "minecraft:damage_entity", "minecraft:summon_entity",
}

# Level-based value providers.
VALUE_TYPES = {
    "minecraft:linear", "minecraft:clamped", "minecraft:fraction", "minecraft:lookup",
    "minecraft:enchantment_level", "minecraft:levels_squared", "minecraft:constant",
}

CONDITIONS = {
    "minecraft:entity_properties", "minecraft:all_of", "minecraft:any_of",
    "minecraft:damage_source_properties", "minecraft:inverted", "minecraft:match_tool",
    "minecraft:random_chance", "minecraft:weather_check",
    "minecraft:enchantment_active_check", "minecraft:location_check",
}

ATTRIBUTES = {
    "armor", "armor_toughness", "attack_damage", "attack_knockback", "attack_speed",
    "block_break_speed", "block_interaction_range", "bounciness", "burning_time",
    "entity_interaction_range", "explosion_knockback_resistance",
    "fall_damage_multiplier", "flying_speed", "follow_range", "friction_modifier",
    "air_drag_modifier", "gravity", "jump_strength", "knockback_resistance", "luck",
    "max_absorption", "max_health", "mining_efficiency", "movement_efficiency",
    "movement_speed", "oxygen_bonus", "safe_fall_distance", "scale", "sneaking_speed",
    "step_height", "submerged_mining_speed", "sweeping_damage_ratio", "tempt_range",
    "water_movement_efficiency", "spawn_reinforcements",
}

OPERATIONS = {"add_value", "add_multiplied_base", "add_multiplied_total"}

SLOTS = {"mainhand", "offhand", "hand", "any", "armor", "head", "chest", "legs", "feet", "body"}

DAMAGE_TYPE_TAGS = {
    "is_fire", "is_fall", "is_explosion", "is_projectile", "is_drowning", "is_freezing",
    "is_lightning", "is_player_attack", "bypasses_invulnerability", "bypasses_armor",
    "bypasses_effects", "bypasses_enchantments", "bypasses_resistance", "no_impact",
    "no_anger", "burn_from_stepping", "mace_smash", "damages_helmet",
}

MOB_EFFECTS = {
    "absorption", "bad_omen", "blindness", "breath_of_the_nautilus", "conduit_power",
    "darkness", "dolphins_grace", "fire_resistance", "glowing", "haste", "health_boost",
    "hero_of_the_village", "hunger", "infested", "instant_damage", "instant_health",
    "invisibility", "jump_boost", "levitation", "luck", "mining_fatigue", "nausea",
    "night_vision", "oozing", "poison", "raid_omen", "regeneration", "resistance",
    "saturation", "slow_falling", "slowness", "speed", "strength", "trial_omen",
    "unluck", "water_breathing", "weakness", "weaving", "wind_charged", "wither",
}

# Item tags under `minecraft:tags/item/enchantable/` in 26.2.
ENCHANTABLE_TAGS = {
    "armor", "bow", "chest_armor", "crossbow", "durability", "equippable", "fire_aspect",
    "fishing", "foot_armor", "head_armor", "leg_armor", "lunge", "mace", "melee_weapon",
    "mining", "mining_loot", "sharp_weapon", "sweeping", "trident", "vanishing", "weapon",
}

VANILLA_EXCLUSIVE_SETS = {"armor", "boots", "bow", "crossbow", "damage", "mining", "riptide"}

DAMAGE_TYPES = {"thorns", "magic", "player_attack", "mob_attack", "generic"}

# ---------------------------------------------------------------------------
# Small builders (all emit exactly the shapes vanilla 26.2 uses)
# ---------------------------------------------------------------------------


def lin(base: float, per_level: float) -> dict:
    """Level-scaled value: `base` at level 1, +`per_level` for each level above."""
    return {"type": "minecraft:linear", "base": float(base),
            "per_level_above_first": float(per_level)}


def attribute(name: str, amount: Any, operation: str = "add_value",
              modifier_id: str | None = None) -> dict:
    """Entry for the (flattened) `minecraft:attributes` component."""
    assert name in ATTRIBUTES, f"unknown attribute {name}"
    assert operation in OPERATIONS, f"unknown operation {operation}"
    return {
        "amount": amount,
        "attribute": f"minecraft:{name}",
        "id": modifier_id or f"{NS}:enchantment.{name}",
        "operation": operation,
    }


def attribute_effect(name: str, amount: Any, operation: str = "add_value",
                     modifier_id: str | None = None) -> dict:
    """`minecraft:attribute` *entity* effect, for conditional application
    (used by vanilla soul_speed inside `minecraft:location_changed`)."""
    e = attribute(name, amount, operation, modifier_id)
    e["type"] = "minecraft:attribute"
    return e


def source_tags(*pairs: tuple[str, bool]) -> dict:
    """A `damage_source_properties` condition over damage-type tags."""
    for tag, _ in pairs:
        assert tag in DAMAGE_TYPE_TAGS, f"unknown damage type tag {tag}"
    return cond(
        "minecraft:damage_source_properties",
        predicate={"tags": [{"expected": exp, "id": f"{TAG_PREFIX}minecraft:{tag}"}
                            for tag, exp in pairs]},
    )


def not_invulnerable() -> tuple[str, bool]:
    """Vanilla always excludes damage that bypasses invulnerability."""
    return ("bypasses_invulnerability", False)


def protection(value: Any, *tags: tuple[str, bool]) -> dict:
    """A `minecraft:damage_protection` entry (EPF points added to the total)."""
    req_tags = list(tags) + [not_invulnerable()]
    return {"effect": {"type": "minecraft:add", "value": value},
            "requirements": source_tags(*req_tags)}


def immunity(*tags: tuple[str, bool]) -> dict:
    """A `minecraft:damage_immunity` entry - full immunity to matching damage."""
    req_tags = list(tags) + [not_invulnerable()]
    return {"effect": {}, "requirements": source_tags(*req_tags)}


def level_chance(base: float, per_level: float) -> dict:
    """`random_chance` whose odds scale with enchantment level (vanilla thorns)."""
    return cond("minecraft:random_chance",
                chance={"type": "minecraft:enchantment_level",
                        "amount": lin(base, per_level)})


def post_attack(effect: dict, *, affected: str = "attacker",
                enchanted: str = "victim", requirements: dict | None = None) -> dict:
    """Retaliation / on-hit entry for `minecraft:post_attack`."""
    assert affected in {"attacker", "victim"}, affected
    assert enchanted in {"attacker", "victim"}, enchanted
    out = {"affected": affected, "effect": effect, "enchanted": enchanted}
    if requirements is not None:
        out["requirements"] = requirements
    return out


def all_of(*effects: dict) -> dict:
    return {"type": "minecraft:all_of", "effects": list(effects)}


def conditional(*terms: dict) -> dict:
    return cond("minecraft:all_of", terms=list(terms))


def entity_flags(**flags: bool) -> dict:
    return cond("minecraft:entity_properties", entity="this",
                predicate={"minecraft:flags": flags})


def periodic(ticks: int) -> dict:
    return cond("minecraft:entity_properties", entity="this",
                predicate={"minecraft:periodic_tick": int(ticks)})


def horizontal_speed_at_least(speed: float) -> dict:
    return cond("minecraft:entity_properties", entity="this",
                predicate={"minecraft:movement": {"horizontal_speed": {"min": float(speed)}}})


def mob_effect(effect: str, *, min_duration: Any, max_duration: Any,
               min_amplifier: Any = 0.0, max_amplifier: Any = 0.0) -> dict:
    assert effect in MOB_EFFECTS, f"unknown mob effect {effect}"
    return {"type": "minecraft:apply_mob_effect",
            "to_apply": f"minecraft:{effect}",
            "min_duration": min_duration, "max_duration": max_duration,
            "min_amplifier": min_amplifier, "max_amplifier": max_amplifier}


def damage_entity(damage_type: str, min_damage: float, max_damage: Any) -> dict:
    assert damage_type in DAMAGE_TYPES, f"unknown damage type {damage_type}"
    return {"type": "minecraft:damage_entity", "damage_type": f"minecraft:{damage_type}",
            "min_damage": float(min_damage), "max_damage": max_damage}


def item_damage(amount: float) -> dict:
    """Durability cost applied to the enchanted item (vanilla thorns / soul speed)."""
    return {"type": "minecraft:change_item_damage", "amount": float(amount)}


def ignite(seconds: Any) -> dict:
    return {"type": "minecraft:ignite", "duration": seconds}


def enchantment(id: str, *, effects: dict[str, list | dict], max_level: int,
                weight: int, anvil_cost: int, min_cost: tuple[int, int],
                max_cost: tuple[int, int], slots: list[str], supported_items: str,
                primary_items: str | None = None,
                exclusive_set: str | None = None) -> dict:
    for slot in slots:
        assert slot in SLOTS, f"unknown slot {slot}"
    doc: dict[str, Any] = {
        "anvil_cost": int(anvil_cost),
        "description": {"translate": f"enchantment.{NS}.{id}"},
        "effects": effects,
    }
    if exclusive_set:
        doc["exclusive_set"] = exclusive_set
    doc.update({
        "max_cost": {"base": int(max_cost[0]), "per_level_above_first": int(max_cost[1])},
        "max_level": int(max_level),
        "min_cost": {"base": int(min_cost[0]), "per_level_above_first": int(min_cost[1])},
        "primary_items": primary_items,
        "slots": slots,
        "supported_items": supported_items,
        "weight": int(weight),
    })
    if primary_items is None:
        del doc["primary_items"]
    return doc


def volyera_tag(name: str) -> str:
    return f"#{NS}:{name}"


def armor(supported: str = "armor") -> str:
    assert supported in ENCHANTABLE_TAGS, supported
    return f"#minecraft:enchantable/{supported}"


# ---------------------------------------------------------------------------
# The roster
# ---------------------------------------------------------------------------
# Design notes:
#  * EPF: each point of `damage_protection` is 4% damage reduction, all sources
#    pooled and capped at 20 points, so numbers stay comparable to vanilla.
#  * `warding` / `emberheart` deliberately join vanilla's protection family via
#    the exclusive-set tags (declared in both directions, see `tag_files()`).
#  * `springstep` showcases 26.2's new `bounciness` attribute.
# ---------------------------------------------------------------------------

ARMOR, HEAD, LEGS, FEET, CHEST, EQUIPPABLE = (
    armor("armor"), armor("head_armor"), armor("leg_armor"),
    armor("foot_armor"), armor("chest_armor"), armor("equippable"),
)

PROTECTION_FAMILY = volyera_tag("exclusive_set/protection_family")
FORTRESS = volyera_tag("exclusive_set/fortress")
DESCENT = volyera_tag("exclusive_set/descent")
RETALIATION = volyera_tag("exclusive_set/retaliation")


def build_enchantments() -> dict[str, dict]:
    e: dict[str, dict] = {}

    # -- Any armour piece ---------------------------------------------------
    e["warding"] = enchantment(
        "warding",
        effects={
            # Slightly below Protection's 1.0 EPF/level, but it also stiffens
            # the armour itself, so it wins against heavy hits.
            "minecraft:damage_protection": [protection(lin(0.75, 0.75))],
            "minecraft:attributes": [attribute("armor_toughness", lin(0.5, 0.5))],
        },
        max_level=4, weight=5, anvil_cost=1,
        min_cost=(1, 11), max_cost=(12, 11),
        slots=["armor"], supported_items=ARMOR, exclusive_set=PROTECTION_FAMILY,
    )

    e["emberheart"] = enchantment(
        "emberheart",
        effects={
            "minecraft:damage_protection": [
                protection(lin(2.5, 2.5), ("is_fire", True))],
            "minecraft:attributes": [
                attribute("burning_time", lin(-0.20, -0.20), "add_multiplied_base")],
            # Fire retaliation: attackers get set alight and your armour pays
            # a point of durability for it, exactly like vanilla Thorns.
            "minecraft:post_attack": [post_attack(
                all_of(ignite(lin(3.0, 3.0)), item_damage(1.0)),
                affected="attacker", enchanted="victim",
                requirements=level_chance(0.20, 0.10))],
        },
        max_level=3, weight=2, anvil_cost=4,
        min_cost=(10, 8), max_cost=(26, 8),
        slots=["armor"], supported_items=ARMOR, exclusive_set=PROTECTION_FAMILY,
    )

    e["bulwark"] = enchantment(
        "bulwark",
        effects={"minecraft:attributes": [
            attribute("armor_toughness", lin(1.0, 1.0)),
            attribute("knockback_resistance", lin(0.10, 0.10)),
        ]},
        max_level=3, weight=5, anvil_cost=4,
        min_cost=(5, 8), max_cost=(21, 8),
        slots=["armor"], supported_items=ARMOR, exclusive_set=FORTRESS,
    )

    e["colossus"] = enchantment(
        "colossus",
        effects={"minecraft:attributes": [
            attribute("max_health", lin(2.0, 2.0)),
            attribute("armor", lin(2.0, 2.0)),
            attribute("knockback_resistance", lin(0.15, 0.15)),
        ]},
        max_level=2, weight=1, anvil_cost=8,
        min_cost=(20, 20), max_cost=(60, 20),
        slots=["armor"], supported_items=ARMOR, exclusive_set=FORTRESS,
    )

    e["glacial_ward"] = enchantment(
        "glacial_ward",
        effects={
            "minecraft:damage_immunity": [immunity(("is_freezing", True))],
            "minecraft:damage_protection": [
                protection(lin(3.0, 3.0), ("is_freezing", True))],
            "minecraft:post_attack": [post_attack(
                mob_effect("slowness", min_duration=2.0, max_duration=lin(2.0, 1.0),
                           min_amplifier=lin(0.0, 1.0), max_amplifier=lin(0.0, 1.0)),
                affected="attacker", enchanted="victim",
                requirements=level_chance(0.35, 0.15))],
        },
        max_level=3, weight=2, anvil_cost=4,
        min_cost=(10, 8), max_cost=(26, 8),
        slots=["armor"], supported_items=ARMOR,
    )

    e["stormwarden"] = enchantment(
        "stormwarden",
        effects={
            "minecraft:damage_immunity": [immunity(("is_lightning", True))],
            "minecraft:damage_protection": [
                protection(lin(4.0, 4.0), ("is_lightning", True))],
            # Rides the storm: a speed bonus while a thunderstorm is active.
            "minecraft:location_changed": [{
                "effect": attribute_effect("movement_speed", lin(0.10, 0.10),
                                           "add_multiplied_total"),
                "requirements": cond("minecraft:weather_check", thundering=True),
            }],
        },
        max_level=2, weight=1, anvil_cost=4,
        min_cost=(12, 10), max_cost=(32, 10),
        slots=["armor"], supported_items=ARMOR,
    )

    e["rejuvenation"] = enchantment(
        "rejuvenation",
        effects={"minecraft:tick": [{
            "effect": mob_effect("regeneration", min_duration=2.0,
                                 max_duration=lin(2.0, 1.0),
                                 min_amplifier=0.0, max_amplifier=0.0),
            "requirements": periodic(100),
        }]},
        max_level=3, weight=2, anvil_cost=4,
        min_cost=(8, 10), max_cost=(28, 10),
        slots=["armor"], supported_items=ARMOR,
    )

    e["thornmail"] = enchantment(
        "thornmail",
        effects={"minecraft:post_attack": [post_attack(
            all_of(damage_entity("thorns", 1.0, lin(3.0, 1.5)), item_damage(2.0)),
            affected="attacker", enchanted="victim",
            requirements=level_chance(0.20, 0.10))]},
        max_level=3, weight=2, anvil_cost=8,
        min_cost=(10, 20), max_cost=(50, 20),
        slots=["armor"], supported_items=ARMOR, exclusive_set=RETALIATION,
    )

    e["prosperity"] = enchantment(
        "prosperity",
        effects={"minecraft:attributes": [attribute("luck", lin(1.0, 1.0))]},
        max_level=3, weight=2, anvil_cost=4,
        min_cost=(8, 8), max_cost=(24, 8),
        slots=["armor"], supported_items=ARMOR,
    )

    e["gilded_aegis"] = enchantment(
        "gilded_aegis",
        effects={"minecraft:attributes": [
            attribute("armor_toughness", 2.0),
            attribute("knockback_resistance", 0.25),
            attribute("max_health", 2.0),
            attribute("luck", 2.0),
        ]},
        max_level=1, weight=1, anvil_cost=8,
        min_cost=(25, 0), max_cost=(50, 0),
        slots=["armor"], supported_items=ARMOR,
    )

    # -- Helmet -------------------------------------------------------------
    e["tidewarden"] = enchantment(
        "tidewarden",
        effects={
            "minecraft:damage_immunity": [immunity(("is_drowning", True))],
            "minecraft:attributes": [
                attribute("oxygen_bonus", lin(1.0, 1.0)),
                attribute("water_movement_efficiency", lin(0.20, 0.20)),
            ],
        },
        max_level=3, weight=2, anvil_cost=4,
        min_cost=(10, 10), max_cost=(30, 10),
        slots=["head"], supported_items=HEAD,
    )

    e["keeneye"] = enchantment(
        "keeneye",
        effects={"minecraft:attributes": [
            attribute("block_interaction_range", lin(0.5, 0.5)),
            attribute("entity_interaction_range", lin(0.5, 0.5)),
        ]},
        max_level=3, weight=1, anvil_cost=8,
        min_cost=(10, 12), max_cost=(34, 12),
        slots=["head"], supported_items=HEAD,
    )

    # -- Leggings -----------------------------------------------------------
    e["shadowstride"] = enchantment(
        "shadowstride",
        effects={"minecraft:attributes": [
            attribute("sneaking_speed", lin(0.12, 0.12)),
            attribute("movement_efficiency", lin(0.40, 0.40)),
        ]},
        max_level=3, weight=2, anvil_cost=8,
        min_cost=(15, 15), max_cost=(60, 15),
        slots=["legs"], supported_items=LEGS,
    )

    e["momentum"] = enchantment(
        "momentum",
        effects={"minecraft:location_changed": [{
            "effect": attribute_effect("movement_speed", lin(0.10, 0.10),
                                       "add_multiplied_total"),
            "requirements": horizontal_speed_at_least(0.15),
        }]},
        max_level=3, weight=2, anvil_cost=4,
        min_cost=(8, 10), max_cost=(28, 10),
        slots=["legs"], supported_items=LEGS,
    )

    # -- Boots --------------------------------------------------------------
    e["featherstep"] = enchantment(
        "featherstep",
        effects={
            "minecraft:damage_protection": [
                protection(lin(2.0, 2.0), ("is_fall", True))],
            "minecraft:attributes": [
                attribute("safe_fall_distance", lin(3.0, 3.0)),
                attribute("fall_damage_multiplier", lin(-0.20, -0.20),
                          "add_multiplied_base"),
            ],
        },
        max_level=3, weight=5, anvil_cost=2,
        min_cost=(5, 6), max_cost=(11, 6),
        slots=["feet"], supported_items=FEET, exclusive_set=DESCENT,
    )

    e["springstep"] = enchantment(
        "springstep",
        effects={"minecraft:attributes": [
            # 26.2's new bounciness attribute (added with the sulfur cubes).
            attribute("bounciness", lin(0.25, 0.25)),
            attribute("step_height", lin(0.20, 0.20)),
            attribute("jump_strength", lin(0.04, 0.04)),
        ]},
        max_level=3, weight=2, anvil_cost=4,
        min_cost=(10, 10), max_cost=(30, 10),
        slots=["feet"], supported_items=FEET, exclusive_set=DESCENT,
    )

    e["abysswalker"] = enchantment(
        "abysswalker",
        effects={"minecraft:attributes": [
            attribute("water_movement_efficiency", lin(0.33333334, 0.33333334)),
            attribute("submerged_mining_speed", lin(2.0, 2.0)),
        ]},
        max_level=3, weight=2, anvil_cost=4,
        min_cost=(10, 10), max_cost=(25, 10),
        slots=["feet"], supported_items=FEET,
        exclusive_set="#minecraft:exclusive_set/boots",
    )

    # -- Chestplate ---------------------------------------------------------
    e["vanguard"] = enchantment(
        "vanguard",
        effects={
            "minecraft:attributes": [attribute("armor", lin(2.0, 2.0))],
            "minecraft:post_attack": [post_attack(
                mob_effect("weakness", min_duration=2.0, max_duration=lin(2.0, 1.0),
                           min_amplifier=0.0, max_amplifier=0.0),
                affected="attacker", enchanted="victim",
                requirements=level_chance(0.25, 0.15))],
        },
        max_level=2, weight=2, anvil_cost=8,
        min_cost=(15, 15), max_cost=(45, 15),
        slots=["armor"], supported_items=CHEST, primary_items=CHEST,
        exclusive_set=RETALIATION,
    )

    # -- Curses (treasure only) ---------------------------------------------
    e["curse_of_anchoring"] = enchantment(
        "curse_of_anchoring",
        effects={
            "minecraft:attributes": [
                attribute("movement_speed", lin(-0.05, -0.05), "add_multiplied_total"),
                attribute("gravity", lin(0.02, 0.02)),
                attribute("step_height", lin(-0.20, -0.20)),
            ],
            # You cannot take it off. Same component vanilla Binding Curse uses.
            "minecraft:prevent_armor_change": {},
        },
        max_level=1, weight=1, anvil_cost=8,
        min_cost=(25, 0), max_cost=(50, 0),
        slots=["armor"], supported_items=EQUIPPABLE,
    )

    e["curse_of_frailty"] = enchantment(
        "curse_of_frailty",
        effects={
            "minecraft:attributes": [attribute("armor_toughness", lin(-1.0, -1.0))],
            "minecraft:tick": [{
                "effect": item_damage(1.0),
                "requirements": conditional(periodic(40),
                                            level_chance(0.50, 0.0)),
            }],
        },
        max_level=1, weight=1, anvil_cost=8,
        min_cost=(25, 0), max_cost=(50, 0),
        slots=["armor"], supported_items=EQUIPPABLE,
    )

    for name, doc in e.items():
        normalize_modifier_ids(name, doc)
    return e


def normalize_modifier_ids(name: str, doc: dict) -> dict:
    """Give every attribute modifier in an enchantment the id
    `volyera:enchantment.<enchantment>`.

    Vanilla uses one modifier id per enchantment and reuses it for every
    attribute that enchantment touches (soul_speed, for instance, applies both
    `movement_speed` and `movement_efficiency` under
    `minecraft:enchantment.soul_speed`). Attribute modifiers are keyed by id
    *and* attribute, so two different enchantments sharing an id would clash on
    the same attribute whenever both are worn - Stormwarden and Momentum both
    touch `movement_speed`, so this matters.
    """
    wanted = f"{NS}:enchantment.{name}"

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            if node.get("type") == "minecraft:attribute" or (
                    "attribute" in node and "operation" in node):
                node["id"] = wanted
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(doc.get("effects", {}))
    return doc


TREASURE = ["gilded_aegis", "curse_of_anchoring", "curse_of_frailty"]
CURSES = ["curse_of_anchoring", "curse_of_frailty"]


def tag_files(enchantments: dict[str, dict]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Returns (volyera tags, minecraft tag merges).

    Files placed under `data/minecraft/tags/...` *merge* with vanilla's copies
    (datapack tags are additive unless `replace: true`), which is how Volyera
    hooks into the enchanting table, villager trades, loot and vanilla's own
    exclusive sets without overwriting anything.
    """
    all_ids = [f"{NS}:{i}" for i in sorted(enchantments)]
    non_treasure = [f"{NS}:{i}" for i in sorted(enchantments) if i not in TREASURE]

    volyera = {
        # Everything the mod adds, handy for other packs/mods to reference.
        "all": {"values": all_ids},
        "treasure": {"values": [f"{NS}:{i}" for i in sorted(TREASURE)]},
        "curse": {"values": [f"{NS}:{i}" for i in sorted(CURSES)]},
        "armor": {"values": [f"{NS}:{i}" for i in sorted(enchantments)
                             if "armor" in enchantments[i]["slots"]]},
        # Mutual-exclusion groups. Declared here *and* in vanilla's matching
        # tags below so the conflict is symmetric regardless of which side of
        # the comparison the game checks.
        "exclusive_set/protection_family": {"values": [
            f"{NS}:warding", f"{NS}:emberheart",
            "minecraft:protection", "minecraft:fire_protection",
            "minecraft:blast_protection", "minecraft:projectile_protection",
        ]},
        "exclusive_set/fortress": {"values": [f"{NS}:bulwark", f"{NS}:colossus"]},
        "exclusive_set/descent": {"values": [f"{NS}:featherstep", f"{NS}:springstep"]},
        "exclusive_set/retaliation": {"values": [
            f"{NS}:thornmail", f"{NS}:vanguard", "minecraft:thorns"]},
    }

    minecraft = {
        # `in_enchanting_table`, `tradeable` and `on_random_loot` all point at
        # `#minecraft:non_treasure`, so this one tag makes them enchantable,
        # tradeable and lootable.
        "non_treasure": {"values": non_treasure},
        "treasure": {"values": [f"{NS}:{i}" for i in sorted(TREASURE)]},
        # Treasure enchantments stay out of the table but remain findable.
        "on_random_loot": {"values": [f"{NS}:{i}" for i in sorted(TREASURE)]},
        "curse": {"values": [f"{NS}:{i}" for i in sorted(CURSES)]},
        "exclusive_set/armor": {"values": [f"{NS}:warding", f"{NS}:emberheart"]},
        "exclusive_set/boots": {"values": [f"{NS}:abysswalker"]},
        "tooltip_order": {"values": [f"{NS}:{i}" for i in enchantments]},
    }
    return volyera, minecraft


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate(enchantments: dict[str, dict]) -> list[str]:
    errors: list[str] = []

    def err(msg: str) -> None:
        errors.append(msg)

    def check_value(where: str, v: Any) -> None:
        if isinstance(v, dict):
            t = v.get("type")
            if t is not None and t not in VALUE_TYPES | EFFECT_TYPES | CONDITIONS:
                err(f"{where}: unknown discriminated type {t!r}")
            for k, sub in v.items():
                check_value(f"{where}.{k}", sub)
        elif isinstance(v, list):
            for i, sub in enumerate(v):
                check_value(f"{where}[{i}]", sub)

    def check_effect(where: str, fx: Any) -> None:
        if not isinstance(fx, dict):
            return
        t = fx.get("type")
        if t is not None:
            if t not in EFFECT_TYPES:
                err(f"{where}: unknown effect type {t!r}")
            if t == "minecraft:apply_mob_effect":
                me = str(fx.get("to_apply", "")).split(":")[-1]
                if me not in MOB_EFFECTS:
                    err(f"{where}: unknown mob effect {me!r}")
            if t == "minecraft:damage_entity":
                dt = str(fx.get("damage_type", "")).split(":")[-1]
                if dt not in DAMAGE_TYPES:
                    err(f"{where}: unknown damage type {dt!r}")
            if t == "minecraft:attribute":
                a = str(fx.get("attribute", "")).split(":")[-1]
                if a not in ATTRIBUTES:
                    err(f"{where}: unknown attribute {a!r}")
                if fx.get("operation") not in OPERATIONS:
                    err(f"{where}: unknown operation {fx.get('operation')!r}")
        for sub in fx.get("effects", []) or []:
            check_effect(f"{where}.effects", sub)
        check_value(where, fx)

    def check_condition(where: str, c: Any) -> None:
        if isinstance(c, list):
            for i, sub in enumerate(c):
                check_condition(f"{where}[{i}]", sub)
            return
        if not isinstance(c, dict):
            return
        kind = c.get(COND_KEY)
        if kind is not None:
            # From 26.3 the discriminator is "type", which condition objects
            # share with effect and value objects, so only reject a kind that
            # belongs to neither vocabulary.
            if kind not in CONDITIONS and kind not in EFFECT_TYPES \
                    and kind not in VALUE_TYPES:
                err(f"{where}: unknown condition {kind!r}")
            if kind == "minecraft:damage_source_properties":
                for tag in c.get("predicate", {}).get("tags", []):
                    if tag["id"].split(":")[-1] not in DAMAGE_TYPE_TAGS:
                        err(f"{where}: unknown damage type tag {tag['id']!r}")
        for key in ("requirements", "term"):
            if key in c:
                check_condition(f"{where}.{key}", c[key])
        for key in ("terms", "predicates"):
            if key in c:
                check_condition(f"{where}.{key}", c[key])
        if "chance" in c:
            check_value(f"{where}.chance", c["chance"])

    for name, doc in enchantments.items():
        where = f"enchantment {name}"
        if not doc.get("supported_items", "").startswith("#minecraft:enchantable/"):
            err(f"{where}: unexpected supported_items {doc.get('supported_items')!r}")
        else:
            tag = doc["supported_items"].rsplit("/", 1)[-1]
            if tag not in ENCHANTABLE_TAGS:
                err(f"{where}: unknown enchantable tag {tag!r}")
        if doc.get("primary_items"):
            tag = doc["primary_items"].rsplit("/", 1)[-1]
            if tag not in ENCHANTABLE_TAGS:
                err(f"{where}: unknown primary_items tag {tag!r}")
        for slot in doc["slots"]:
            if slot not in SLOTS:
                err(f"{where}: unknown slot {slot!r}")
        if doc["max_level"] < 1:
            err(f"{where}: max_level must be >= 1")
        if doc["min_cost"]["base"] > doc["max_cost"]["base"]:
            err(f"{where}: min_cost base exceeds max_cost base")

        excl = doc.get("exclusive_set")
        if excl:
            if excl.startswith("#minecraft:exclusive_set/"):
                if excl.rsplit("/", 1)[-1] not in VANILLA_EXCLUSIVE_SETS:
                    err(f"{where}: unknown vanilla exclusive set {excl!r}")
            elif not excl.startswith(f"#{NS}:exclusive_set/"):
                err(f"{where}: unexpected exclusive_set {excl!r}")

        for comp, payload in doc["effects"].items():
            if comp not in EFFECT_COMPONENTS:
                err(f"{where}: unknown effect component {comp!r}")
                continue
            # Flattened components (attributes) hold effect objects directly;
            # the rest are lists of ConditionalEffect wrappers.
            entries = payload if isinstance(payload, list) else [payload]
            for entry in entries:
                if not isinstance(entry, dict):
                    continue
                if comp == "minecraft:attributes":
                    a = str(entry.get("attribute", "")).split(":")[-1]
                    if a not in ATTRIBUTES:
                        err(f"{where}.{comp}: unknown attribute {a!r}")
                    if entry.get("operation") not in OPERATIONS:
                        err(f"{where}.{comp}: unknown operation {entry.get('operation')!r}")
                    check_value(f"{where}.{comp}.amount", entry.get("amount"))
                    continue
                if "effect" in entry:
                    check_effect(f"{where}.{comp}.effect", entry["effect"])
                if "requirements" in entry:
                    check_condition(f"{where}.{comp}.requirements", entry["requirements"])
                for role in ("affected", "enchanted"):
                    if role in entry and entry[role] not in ("attacker", "victim"):
                        err(f"{where}.{comp}: bad {role} {entry[role]!r}")

        # Attribute modifier ids must follow the vanilla one-id-per-enchantment
        # convention, otherwise two enchantments touching the same attribute
        # (Stormwarden and Momentum both use movement_speed) would collide.
        expected_id = f"{NS}:enchantment.{name}"
        seen: set[str] = set()

        def check_ids(node: Any) -> None:
            if isinstance(node, dict):
                if "attribute" in node and "operation" in node:
                    mid = node.get("id")
                    if mid != expected_id:
                        err(f"{where}: attribute modifier id {mid!r} should be "
                            f"{expected_id!r}")
                    seen.add(str(node.get("attribute")))
                for value in node.values():
                    check_ids(value)
            elif isinstance(node, list):
                for value in node:
                    check_ids(value)

        check_ids(doc.get("effects", {}))
        attrs = [str(a.get("attribute")) for a in
                 doc["effects"].get("minecraft:attributes", [])]
        if len(attrs) != len(set(attrs)):
            err(f"{where}: duplicate attribute in minecraft:attributes {attrs}")
    return errors


# ---------------------------------------------------------------------------
# Language file
# ---------------------------------------------------------------------------

DISPLAY_NAMES = {
    "warding": "Warding",
    "emberheart": "Emberheart",
    "bulwark": "Bulwark",
    "colossus": "Colossus",
    "glacial_ward": "Glacial Ward",
    "stormwarden": "Stormwarden",
    "rejuvenation": "Rejuvenation",
    "thornmail": "Thornmail",
    "prosperity": "Prosperity",
    "gilded_aegis": "Gilded Aegis",
    "tidewarden": "Tidewarden",
    "keeneye": "Keeneye",
    "shadowstride": "Shadowstride",
    "momentum": "Momentum",
    "featherstep": "Featherstep",
    "springstep": "Springstep",
    "abysswalker": "Abysswalker",
    "vanguard": "Vanguard",
    "curse_of_anchoring": "Curse of Anchoring",
    "curse_of_frailty": "Curse of Frailty",
}

DESCRIPTIONS = {
    "warding": "Reduces most incoming damage and stiffens your armour against heavy hits. Cannot be combined with the Protection family.",
    "emberheart": "Greatly reduces fire damage, shortens how long you burn, and sets melee attackers alight at the cost of durability. Cannot be combined with the Protection family.",
    "bulwark": "Increases armour toughness and knockback resistance. Cannot be combined with Colossus.",
    "colossus": "Grants bonus hearts, armour and knockback resistance. Rare, and cannot be combined with Bulwark.",
    "glacial_ward": "Immunity to freezing damage, extra protection in powder snow, and a chance to slow anything that strikes you.",
    "stormwarden": "Immunity to lightning, heavy protection during thunderstorms, and a speed boost while the storm rages.",
    "rejuvenation": "Periodically grants a short burst of regeneration while worn.",
    "thornmail": "A chance to wound melee attackers for thorns damage, wearing your armour down as it does. Cannot be combined with Vanguard.",
    "prosperity": "Increases your luck, improving drops from blocks and mobs.",
    "gilded_aegis": "A treasure enchantment granting armour toughness, knockback resistance, bonus hearts and luck all at once.",
    "tidewarden": "Grants immunity to drowning, extra breath and faster swimming. Helmet only.",
    "keeneye": "Extends your block and entity interaction range. Helmet only.",
    "shadowstride": "Moves you faster while sneaking and negates slowdown from blocks like soul sand. Leggings only.",
    "momentum": "Grants a stacking speed bonus once you are already moving quickly. Leggings only.",
    "featherstep": "Increases safe fall distance, reduces fall damage and protects against it. Cannot be combined with Springstep.",
    "springstep": "Makes you bouncy, raises step height and improves jump strength. Uses 26.2's bounciness attribute. Cannot be combined with Featherstep.",
    "abysswalker": "Swim at full speed and mine normally while submerged. Cannot be combined with Frost Walker or Depth Strider.",
    "vanguard": "Grants bonus armour and a chance to weaken melee attackers. Chestplate only, and cannot be combined with Thornmail.",
    "curse_of_anchoring": "Slows you, pulls you down and cannot be removed once worn. Found only as treasure.",
    "curse_of_frailty": "Softens your armour and quietly eats its durability over time. Found only as treasure.",
}


def build_lang(enchantments: dict[str, dict]) -> dict[str, str]:
    lang: dict[str, str] = {}
    for key in enchantments:
        name = DISPLAY_NAMES[key]
        lang[f"enchantment.{NS}.{key}"] = name
        # `.desc` is the key Enchantment Descriptions looks for first, so the
        # mod's tooltips are populated without any extra work from us.
        lang[f"enchantment.{NS}.{key}.desc"] = DESCRIPTIONS[key]
    return lang


# ---------------------------------------------------------------------------
# Generated Java
# ---------------------------------------------------------------------------

JAVA_PACKAGE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "common", "src", "main", "java", "net", "volyera")

# Short doc comment per enchantment, used in the generated Java constants.
JAVA_DOC = {
    "warding": "Any armour. Damage reduction plus armour toughness; protection family.",
    "emberheart": "Any armour. Fire protection, shorter burns, ignites melee attackers.",
    "bulwark": "Any armour. Armour toughness and knockback resistance.",
    "colossus": "Any armour. Bonus hearts, armour and knockback resistance. Rare.",
    "glacial_ward": "Any armour. Freezing immunity and a chance to slow attackers.",
    "stormwarden": "Any armour. Lightning immunity; faster while a thunderstorm rages.",
    "rejuvenation": "Any armour. Periodic burst of regeneration.",
    "thornmail": "Any armour. Reflects thorns damage at melee attackers.",
    "prosperity": "Any armour. Luck, for better block and mob drops.",
    "gilded_aegis": "Any armour. Treasure: toughness, knockback resistance, hearts, luck.",
    "tidewarden": "Helmet. Drowning immunity, extra breath, faster swimming.",
    "keeneye": "Helmet. Longer block and entity interaction range.",
    "shadowstride": "Leggings. Faster sneaking, ignores soul-sand-style slowdown.",
    "momentum": "Leggings. Speed bonus that builds once you are moving quickly.",
    "featherstep": "Boots. Safer, softer and partly protected falls.",
    "springstep": "Boots. Bounciness (new in 26.2), step height and jump strength.",
    "abysswalker": "Boots. Full swim speed and normal mining while submerged.",
    "vanguard": "Chestplate. Bonus armour and a chance to weaken attackers.",
    "curse_of_anchoring": "Treasure curse. Slows you, weighs you down, cannot be removed.",
    "curse_of_frailty": "Treasure curse. Less toughness and steady durability drain.",
}


def build_java(enchantments: dict[str, dict]) -> str:
    """Emit VolyeraEnchantments.java so the typed keys cannot drift from data."""
    lines = [
        "package net.volyera;",
        "",
        "import java.util.List;",
        "",
        "import net.minecraft.core.registries.Registries;",
        "import net.minecraft.resources.ResourceKey;",
        "import net.minecraft.world.item.enchantment.Enchantment;",
        "",
        "/**",
        " * Typed references to the enchantments Volyera ships as data.",
        " *",
        " * <p>These are {@link ResourceKey}s, not registrations. Minecraft 26.2",
        " * enchantments are defined by datapack JSON - see",
        " * {@code data/volyera/enchantment} - and the game registers them itself.",
        " * The keys exist so that Java code, and other mods depending on Volyera,",
        " * can refer to a specific enchantment without repeating a string literal.",
        " *",
        " * <p>This file is generated by {@code tools/generate_enchantments.py} from the",
        " * same roster that produces the JSON. Do not edit it by hand; edit the tool.",
        " */",
        "public final class VolyeraEnchantments {",
        "",
    ]

    for path in enchantments:
        const = path.upper()
        lines.append(f"    /** {JAVA_DOC[path]} */")
        lines.append(f'    public static final ResourceKey<Enchantment> {const} = key("{path}");')
        lines.append("")

    lines.append("    /** Every enchantment Volyera defines, for iteration and sanity checks. */")
    lines.append("    public static final List<ResourceKey<Enchantment>> ALL = List.of(")
    names = [p.upper() for p in enchantments]
    for i, name in enumerate(names):
        comma = "," if i < len(names) - 1 else ""
        lines.append(f"            {name}{comma}")
    lines.append("    );")
    lines.append("")
    lines.append("    private VolyeraEnchantments() {")
    lines.append("    }")
    lines.append("")
    lines.append("    private static ResourceKey<Enchantment> key(String path) {")
    lines.append("        return ResourceKey.create(Registries.ENCHANTMENT, Volyera.id(path));")
    lines.append("    }")
    lines.append("}")
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def expected_files(enchantments: dict[str, dict]) -> dict[str, str]:
    """Every generated file, as path -> exact expected contents."""
    volyera_tags, minecraft_tags = tag_files(enchantments)
    files: dict[str, str] = {}

    def as_json(obj: Any) -> str:
        return json.dumps(obj, indent=2, ensure_ascii=False, sort_keys=True) + "\n"

    for name, doc in enchantments.items():
        files[os.path.join(ENCH_DIR, f"{name}.json")] = as_json(doc)
    for name, doc in volyera_tags.items():
        files[os.path.join(VOL_TAG_DIR, f"{name}.json")] = as_json(doc)
    for name, doc in minecraft_tags.items():
        files[os.path.join(MC_TAG_DIR, f"{name}.json")] = as_json(doc)
    files[os.path.join(RES_ROOT, "assets", NS, "lang", "en_us.json")] = \
        as_json(build_lang(enchantments))
    files[os.path.join(JAVA_PACKAGE_DIR, "VolyeraEnchantments.java")] = \
        build_java(enchantments)
    return files


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--check", action="store_true",
                        help="validate and report drift without writing files")
    parser.add_argument("--mc-version", action="append", metavar="VERSION",
                        choices=SUPPORTED_VERSIONS,
                        help="emit only this Minecraft version, repeatable "
                             "(default: every supported version)")
    args = parser.parse_args()

    versions = args.mc_version or list(SUPPORTED_VERSIONS)
    files: dict[str, str] = {}
    roster = 0

    for version in versions:
        set_target(version)
        enchantments = build_enchantments()

        errors = validate(enchantments)
        if errors:
            print(f"VALIDATION FAILED for Minecraft {version}:", file=sys.stderr)
            for e in errors:
                print(f"  - {e}", file=sys.stderr)
            return 1

        for table, label in ((DISPLAY_NAMES, "DISPLAY_NAMES"), (JAVA_DOC, "JAVA_DOC")):
            mismatch = sorted(set(table) ^ set(enchantments))
            if mismatch:
                print(f"{label} does not match the roster: {mismatch}", file=sys.stderr)
                return 1

        # Tags, translations and the Java constants are version-agnostic, so
        # later iterations simply overwrite them with identical bytes.
        files.update(expected_files(enchantments))
        roster = len(enchantments)
        print(f"  {version}: {len(enchantments)} enchantments validated "
              f"(condition key {COND_KEY!r}, damage-source tag ids "
              f"{'#' if TAG_PREFIX else 'un'}prefixed)")

    enchantment_files = roster * len(versions)
    print(f"validated {roster} enchantments for {', '.join(versions)}: OK")

    if args.check:
        drift = []
        for path, want in sorted(files.items()):
            if not os.path.exists(path):
                drift.append(f"missing {path}")
            elif open(path, encoding="utf-8").read() != want:
                drift.append(f"stale   {path}")
        # Enchantment definitions used to live in the shared tree; a leftover
        # copy there would be picked up by every version and silently override
        # the correct one.
        legacy = os.path.join(RES_ROOT, "data", NS, "enchantment")
        if os.path.isdir(legacy):
            for name in sorted(os.listdir(legacy)):
                drift.append(f"legacy  {os.path.join(legacy, name)}")
        if drift:
            print("DRIFT DETECTED (run without --check to regenerate):", file=sys.stderr)
            for d in drift:
                print(f"  - {d}", file=sys.stderr)
            return 1
        print(f"no drift: all {len(files)} generated files are up to date")
        return 0

    for path, content in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(content)

    print(f"wrote {len(files)} files: {enchantment_files} enchantment definitions "
          f"({roster} x {len(versions)} versions), "
          f"{len(files) - enchantment_files - 2} tag files, 1 lang file, 1 Java file")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
