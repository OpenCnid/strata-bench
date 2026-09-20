package io.github.opencnid.strata.client;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.util.UUID;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.screens.TitleScreen;
import net.minecraftforge.client.loading.ClientModLoader;
import net.minecraftforge.common.MinecraftForge;
import net.minecraftforge.event.GameShuttingDownEvent;
import net.minecraftforge.event.TickEvent;

/** Opt-in private operator bridge; no gameplay grant/capability and no in-world writes. */
final class ClientSettingsBridge {
    private static boolean attempted;
    private static SettingsHttpBridge bridge;
    private static SettingsStore store;

    static void install() {
        MinecraftForge.EVENT_BUS.addListener(ClientSettingsBridge::tick);
        MinecraftForge.EVENT_BUS.addListener(ClientSettingsBridge::shutdown);
    }

    private static void tick(TickEvent.ClientTickEvent event) {
        if (event.phase != TickEvent.Phase.END || ClientModLoader.isLoading()) return;
        Minecraft client = Minecraft.getInstance();
        if (bridge != null) { bridge.drain(); return; }
        if (attempted) return;
        String directory = System.getProperty("strata.settingsBridgeDirectory");
        if (directory == null) { attempted = true; return; }
        if (!(client.screen instanceof TitleScreen) || client.player != null || client.level != null) return;
        attempted = true;
        try {
            if (System.getProperty("strata.settingsTransactionDirectory") != null) throw new IOException("SETTINGS_DIAGNOSTICS_CONFLICT");
            Path root = SettingsFiles.safeExisting(Path.of(directory));
            NativeSettingsRuntime runtime = new NativeSettingsRuntime(client);
            store = new SettingsStore(client.gameDirectory.toPath().toAbsolutePath().normalize(), root, runtime.fingerprint(), runtime);
            NativeSettingsProtocol protocol = new NativeSettingsProtocol(store, runtime);
            bridge = new SettingsHttpBridge(request -> {
                String operation = SettingsJson.string(request, "operation");
                if (!operation.equals("stop_all") && (!(client.screen instanceof TitleScreen)
                        || client.player != null || client.level != null)) throw new IOException("SETTINGS_DEVELOPMENT_CONTEXT_REQUIRED");
                return protocol.execute(request);
            });
            // Contains a credential: leave in private broker storage, never an evidence export.
            SettingsFiles.writeNew(root.resolve("connection-" + UUID.randomUUID() + ".json"),
                (bridge.descriptor(runtime.fingerprint()) + "\n").getBytes(StandardCharsets.UTF_8));
        } catch (IOException error) {
            if (bridge != null) bridge.close();
            bridge = null;
            if (store != null) try { store.close(); } catch (IOException suppressed) { error.addSuppressed(suppressed); }
            throw new IllegalStateException("STRATA_SETTINGS_BRIDGE_FAILED", error);
        }
    }

    private static void shutdown(GameShuttingDownEvent event) {
        if (bridge != null) bridge.close();
        if (store != null) try { store.close(); }
        catch (IOException error) { throw new IllegalStateException("STRATA_SETTINGS_BRIDGE_STOP_FAILED", error); }
    }
}
