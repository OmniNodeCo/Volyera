package com.volyera;

import net.fabricmc.fabric.api.itemgroup.v1.FabricItemGroup;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.item.AxeItem;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Rarity;
import net.minecraft.world.item.SwordItem;

public final class VolyeraItems {
	// --- materials ---
	public static final Item VOID_SHARD = register("void_shard",
			new Item(new Item.Properties()));
	public static final Item VOIDSTEEL_INGOT = register("voidsteel_ingot",
			new Item(new Item.Properties()));

	// --- weapons ---
	// Voidsteel Sword: 8 attack damage, 1.6 attack speed.
	public static final Item VOIDSTEEL_SWORD = register("voidsteel_sword",
			new SwordItem(VoidsteelTier.INSTANCE, new Item.Properties()
					.rarity(Rarity.UNCOMMON)
					.attributes(SwordItem.createAttributes(VoidsteelTier.INSTANCE, 3, -2.4F))));

	// Voidsteel Dagger: 5 attack damage, but a blistering 3.0 attack speed.
	public static final Item VOIDSTEEL_DAGGER = register("voidsteel_dagger",
			new SwordItem(VoidsteelTier.INSTANCE, new Item.Properties()
					.rarity(Rarity.UNCOMMON)
					.attributes(SwordItem.createAttributes(VoidsteelTier.INSTANCE, 0, -1.0F))));

	// Voidsteel War Axe: 10 attack damage, 1.0 attack speed.
	public static final Item VOIDSTEEL_AXE = register("voidsteel_axe",
			new AxeItem(VoidsteelTier.INSTANCE, new Item.Properties()
					.rarity(Rarity.UNCOMMON)
					.attributes(AxeItem.createAttributes(VoidsteelTier.INSTANCE, 5.0F, -3.0F))));

	public static final CreativeModeTab TAB = Registry.register(
			BuiltInRegistries.CREATIVE_MODE_TAB, id("volyera"),
			FabricItemGroup.builder()
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

	private static Item register(String name, Item item) {
		return Registry.register(BuiltInRegistries.ITEM, id(name), item);
	}

	static ResourceLocation id(String path) {
		return ResourceLocation.fromNamespaceAndPath(Volyera.MOD_ID, path);
	}

	/** Triggers static initialization from the mod entrypoint. */
	public static void init() {
	}
}
