package io.github.opencnid.strata.client;

import java.io.IOException;
import java.nio.file.Path;
import java.util.Map;
import java.util.Properties;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.screens.TitleScreen;
import net.minecraftforge.client.loading.ClientModLoader;
import net.minecraftforge.common.MinecraftForge;
import net.minecraftforge.event.TickEvent;

/** One explicitly armed title-only process crash. No endpoint, world or input event. */
final class ClientSettingsCrashProbe {
    private static boolean attempted;
    static final String PROPERTY = "strata.settingsCrashDirectory";

    static void validateModes(Properties properties, Map<String, String> environment) {
        if (properties.getProperty(PROPERTY) == null) return;
        for (String incompatible : new String[] {"strata.settingsTransactionDirectory", "strata.settingsBridgeDirectory",
                "strata.settingsDiscoveryDirectory", "strata.gameBridgeDirectory", "strata.privateFrameDirectory",
                "strata.collisionProbeDirectory"}) {
            if (properties.getProperty(incompatible) != null) throw new IllegalStateException("SETTINGS_DIAGNOSTICS_CONFLICT");
        }
        if (environment.containsKey("STRATA_SETTINGS_DISCOVERY_DIR")) {
            throw new IllegalStateException("SETTINGS_DIAGNOSTICS_CONFLICT");
        }
    }

    static void install() { MinecraftForge.EVENT_BUS.addListener(ClientSettingsCrashProbe::tick); }

    private static void tick(TickEvent.ClientTickEvent event) {
        if (attempted || event.phase != TickEvent.Phase.END || ClientModLoader.isLoading()) return;
        String directory = System.getProperty(PROPERTY);
        if (directory == null) { attempted = true; return; }
        Minecraft client = Minecraft.getInstance();
        if (!(client.screen instanceof TitleScreen) || client.player != null || client.level != null) return;
        attempted = true;
        try {
            validateModes(System.getProperties(), System.getenv());
            NativeSettingsRuntime runtime = new NativeSettingsRuntime(client);
            SettingsCrashProbe.run(client.gameDirectory.toPath().toAbsolutePath().normalize(), Path.of(directory),
                runtime.fingerprint(), runtime, NativeSettingsRuntime.TARGET, runtime.ownershipEvidence(), false);
        } catch (IOException error) { throw new IllegalStateException("STRATA_SETTINGS_CRASH_PROBE_FAILED", error); }
    }
}
