package com.volyera;

import net.minecraft.tags.BlockTags;
import net.minecraft.tags.TagKey;
import net.minecraft.world.item.Tier;
import net.minecraft.world.item.crafting.Ingredient;
import net.minecraft.world.level.block.Block;

/**
 * Voidsteel sits between diamond and netherite: slightly more durable and
 * harder-hitting than diamond, and it enchants exceptionally well.
 */
public final class VoidsteelTier implements Tier {
	public static final VoidsteelTier INSTANCE = new VoidsteelTier();

	private VoidsteelTier() {
	}

	@Override
	public int getUses() {
		return 1796;
	}

	@Override
	public float getSpeed() {
		return 8.5F;
	}

	@Override
	public float getAttackDamageBonus() {
		return 4.0F;
	}

	@Override
	public TagKey<Block> getIncorrectBlocksForDrops() {
		return BlockTags.INCORRECT_FOR_DIAMOND_TOOL;
	}

	@Override
	public int getEnchantmentValue() {
		return 18;
	}

	@Override
	public Ingredient getRepairIngredient() {
		return Ingredient.of(VolyeraItems.VOIDSTEEL_INGOT);
	}
}
