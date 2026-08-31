package com.volyera;

import java.util.function.Function;

import net.fabricmc.fabric.api.creativetab.v1.FabricCreativeModeTab;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.resources.Identifier;
import net.minecraft.tags.BlockTags;
import net.minecraft.tags.TagKey;
import net.minecraft.world.item.AxeItem;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Rarity;
import net.minecraft.world.item.ToolMaterial;

/** Item registration for Minecraft 26.1+ (calendar versions). */
public final class VolyeraItems {
	public static final TagKey<Item> REPAIRS_VOIDSTEEL =
			TagKey.create(Registries.ITEM, id("repairs_voidsteel"));

	/** Voidsteel sits between diamond and netherite; enchants exceptionally well. */
	public static final ToolMaterial VOIDSTEEL_MATERIAL = new ToolMaterial(
			BlockTags.INCORRECT_FOR_DIAMOND_TOOL, // incorrect blocks for drops
			1796, // durability
			8.5F, // mining speed
			4.0F, // attack damage bonus
			18, // enchantment value
			REPAIRS_VOIDSTEEL // repair items
	);

	// --- materials ---
	public static final Item VOID_SHARD = register("void_shard", Item::new, new Item.Properties());
	public static final Item VOIDSTEEL_INGOT = register("voidsteel_ingot", Item::new, new Item.Properties());

	// --- weapons ---
	// Voidsteel Sword: 8 attack damage, 1.6 attack speed.
	public static final Item VOIDSTEEL_SWORD = register("voidsteel_sword", Item::new,
			new Item.Properties().rarity(Rarity.UNCOMMON).sword(VOIDSTEEL_MATERIAL, 3.0F, -2.4F));

	// Voidsteel Dagger: 5 attack damage, but a blistering 3.0 attack speed.
	public static final Item VOIDSTEEL_DAGGER = register("voidsteel_dagger", Item::new,
			new Item.Properties().rarity(Rarity.UNCOMMON).sword(VOIDSTEEL_MATERIAL, 0.0F, -1.0F));

	// Voidsteel War Axe: 10 attack damage, 1.0 attack speed.
	public static final Item VOIDSTEEL_AXE = register("voidsteel_axe",
			settings -> new AxeItem(VOIDSTEEL_MATERIAL, 5.0F, -3.0F, settings),
			new Item.Properties().rarity(Rarity.UNCOMMON));

	public static final ResourceKey<CreativeModeTab> TAB_KEY =
			ResourceKey.create(BuiltInRegistries.CREATIVE_MODE_TAB.key(), id("volyera"));

	public static final CreativeModeTab TAB = Registry.register(
			BuiltInRegistries.CREATIVE_MODE_TAB, TAB_KEY,
			FabricCreativeModeTab.builder()
					.title(Component.translatable("itemGroup.volyera"))
					.icon(() -> new ItemStack(VOIDSTEEL_SWORD))
					.displayItems((params, output) -> {
						output.accept(VOID_SHARD);
						output.accept(VOIDSTEEL_INGOT);
						output.accept(VOIDSTEEL_DAGGER);
						output.accept(VOIDSTEEL_SWORD);
						output.accept(VOIDSTEEL_AXE);
					})
					.build());

	private VolyeraItems() {
	}

	private static Item register(String name, Function<Item.Properties, Item> factory, Item.Properties settings) {
		ResourceKey<Item> key = ResourceKey.create(Registries.ITEM, id(name));
		Item item = factory.apply(settings.setId(key));
		return Registry.register(BuiltInRegistries.ITEM, key, item);
	}

	static Identifier id(String path) {
		return Identifier.fromNamespaceAndPath(Volyera.MOD_ID, path);
	}

	/** Triggers static initialization from the mod entrypoint. */
	public static void init() {
	}
}
