package net.volyera;

import net.minecraft.resources.Identifier;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * Loader-agnostic entry point for Volyera.
 *
 * <p>Minecraft 26.2 ships unobfuscated, so Fabric and NeoForge both compile
 * against Mojang's own names. That is why this class - and everything else in
 * {@code common/} - is shared verbatim by both loader modules instead of being
 * duplicated behind an abstraction layer.
 *
 * <p>Volyera's enchantments are data-driven: they are defined as JSON under
 * {@code data/volyera/enchantment} and behave identically on both loaders,
 * because each loader exposes its mod jar's {@code data/} folder as a built-in
 * datapack. Nothing in this package registers an enchantment; the game loads
 * them from data. See {@link VolyeraEnchantments} for typed references to the
 * enchantments the data defines.
 */
public final class Volyera {

    /** Must match {@code mod_id} in gradle.properties and both loader metadata files. */
    public static final String MOD_ID = "volyera";

    public static final Logger LOGGER = LoggerFactory.getLogger(MOD_ID);

    private Volyera() {
    }

    /** Builds a {@code volyera:<path>} identifier. */
    public static Identifier id(String path) {
        return Identifier.fromNamespaceAndPath(MOD_ID, path);
    }

    /**
     * Called from each loader's entrypoint once the mod is constructed.
     *
     * @param loader human-readable loader name, used only for the log line
     */
    public static void onCommonInit(String loader) {
        LOGGER.info("Volyera loaded on {}. {} data-driven enchantments are bundled in data/{}/enchantment.",
                loader, VolyeraEnchantments.ALL.size(), MOD_ID);
    }
}
