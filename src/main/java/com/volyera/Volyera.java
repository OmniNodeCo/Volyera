package com.volyera;

import net.fabricmc.api.ModInitializer;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class Volyera implements ModInitializer {
	public static final String MOD_ID = "volyera";
	public static final Logger LOGGER = LoggerFactory.getLogger(MOD_ID);

	@Override
	public void onInitialize() {
		VolyeraItems.init();
		LOGGER.info("Volyera awakened: the voidsteel arsenal has been bound.");
	}
}
