package net.volyera.neoforge;

import net.neoforged.fml.common.Mod;
import net.volyera.Volyera;

/**
 * NeoForge entrypoint, discovered via the {@code @Mod} annotation and declared
 * in {@code META-INF/neoforge.mods.toml}.
 *
 * <p>Like the Fabric side there is nothing to register: the enchantments live
 * in this jar's {@code data/volyera/enchantment} folder, which NeoForge exposes
 * as a built-in datapack. The constructor only needs to exist so that FML
 * instantiates the mod and the shared bootstrap runs.
 */
@Mod(Volyera.MOD_ID)
public class VolyeraNeoForge {

    public VolyeraNeoForge() {
        Volyera.onCommonInit("NeoForge");
    }
}
