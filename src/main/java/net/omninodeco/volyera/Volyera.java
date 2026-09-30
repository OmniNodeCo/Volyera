package net.omninodeco.volyera;

import net.fabricmc.api.ModInitializer;

import net.minecraft.resources.Identifier;

import net.omninodeco.volyera.items.ModItems;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class Volyera implements ModInitializer {

	public static final String MOD_ID = "Volyera";
	public static final Logger LOGGER = LoggerFactory.getLogger(MOD_ID);

	@Override
	public void onInitialize() {
		ModItems.registerModItems();

	}
}