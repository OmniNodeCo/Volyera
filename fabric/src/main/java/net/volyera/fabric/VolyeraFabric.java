package net.volyera.fabric;

import net.fabricmc.api.ModInitializer;
import net.volyera.Volyera;

/**
 * Fabric entrypoint, declared under {@code entrypoints.main} in fabric.mod.json.
 *
 * <p>There is deliberately nothing to register here: Volyera's enchantments are
 * loaded from this jar's {@code data/volyera/enchantment} folder, which Fabric
 * Loader exposes as a built-in datapack.
 */
public class VolyeraFabric implements ModInitializer {

    @Override
    public void onInitialize() {
        Volyera.onCommonInit("Fabric");
    }
}
