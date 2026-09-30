package net.omninodeco.volyera.items;

import net.minecraft.core.registries.Registries;
import net.minecraft.world.item.Item;
import net.omninodeco.volyera.Volyera;

import java.rmi.registry.Registry;

public class ModItems {


    private static Item registerItem(String name, Item item) {
        return Registry.register(Registries.ITEM, Identifier.of(Volyera.MOD_ID, name), item);
    }

    public static void registerModItems() {
        Volyera.LOGGER.info("Registering ModItems for " + Volyera.MOD_ID);
    }
}
