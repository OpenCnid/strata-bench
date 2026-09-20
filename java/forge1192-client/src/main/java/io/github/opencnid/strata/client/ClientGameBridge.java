package io.github.opencnid.strata.client;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.UUID;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.screens.TitleScreen;
import net.minecraftforge.client.loading.ClientModLoader;
import net.minecraftforge.common.MinecraftForge;
import net.minecraftforge.event.GameShuttingDownEvent;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.event.TagsUpdatedEvent;
import net.minecraftforge.client.event.RecipesUpdatedEvent;

/** Explicit operator opt-in. No desktop input, automatic join, or gameplay admission. */
final class ClientGameBridge {
    private static boolean attempted;
    private static SettingsHttpBridge bridge;
    private static NativeGameRuntime runtime;
    private static GameActionLane lane;
    private static GameBootstrap bootstrap;
    private static final GameStartupReadiness startup = new GameStartupReadiness();
    static void install() {
        MinecraftForge.EVENT_BUS.addListener(ClientGameBridge::tick);
        MinecraftForge.EVENT_BUS.addListener(ClientGameBridge::render);
        MinecraftForge.EVENT_BUS.addListener(ClientGameBridge::tagsUpdated);
        MinecraftForge.EVENT_BUS.addListener(ClientGameBridge::recipesUpdated);
        MinecraftForge.EVENT_BUS.addListener(ClientGameBridge::shutdown);
        MinecraftForge.EVENT_BUS.addListener(net.minecraftforge.eventbus.api.EventPriority.LOWEST, true,
            (net.minecraftforge.client.event.InputEvent.InteractionKeyMappingTriggered event) -> {
            if (runtime != null) runtime.onInput(event);
        });
    }
    private static void tagsUpdated(TagsUpdatedEvent event) {
        Minecraft client = Minecraft.getInstance();
        if (!client.isSameThread() || event.getUpdateCause() != TagsUpdatedEvent.UpdateCause.CLIENT_PACKET_RECEIVED
                || System.getProperty("strata.gameBridgeDirectory") == null) return;
        var connection = client.getConnection();
        startup.tagsUpdated(connection, connection == null ? null : connection.registryAccess(), event.getRegistryAccess());
    }
    private static void recipesUpdated(RecipesUpdatedEvent event) {
        Minecraft client = Minecraft.getInstance();
        if (!client.isSameThread() || System.getProperty("strata.gameBridgeDirectory") == null) return;
        var connection = client.getConnection();
        startup.recipesUpdated(connection, connection == null ? null : connection.getRecipeManager(), event.getRecipeManager());
    }
    private static boolean unobstructed(Minecraft client) {
        return !client.noRender && client.screen == null && client.getOverlay() == null;
    }
    static boolean bodyReady(Minecraft client) {
        return startup.qualified(client.level, client.player, client.getConnection());
    }
    private static void render(TickEvent.RenderTickEvent event) {
        if (event.phase != TickEvent.Phase.END || ClientModLoader.isLoading()
                || System.getProperty("strata.gameBridgeDirectory") == null) return;
        Minecraft client = Minecraft.getInstance();
        startup.rendered(client.level, client.player, client.getConnection(), unobstructed(client));
    }
    private static void tick(TickEvent.ClientTickEvent event) {
        // Recheck/release held use BEFORE Minecraft polls keyUse; a finished item
        // must never cause vanilla's held-key loop to start another use.
        if (event.phase != TickEvent.Phase.START || ClientModLoader.isLoading()) return;
        Minecraft client = Minecraft.getInstance();
        try {
            startup.admit(client.level, client.player, client.getConnection(), unobstructed(client));
            if (bridge != null) {
                runtime.tick(); bridge.drain(); // Reserved safety queue drains before the action motor.
                if (lane != null) lane.tick();
                return;
            }
            if (attempted) return;
            String directory = System.getProperty("strata.gameBridgeDirectory");
            if (directory == null) { attempted = true; return; }
            // The native --server startup path connects directly after resource
            // loading and never installs a TitleScreen. Wait for its complete
            // tag/recipe synchronization and a later unobstructed world render;
            // loading, partial joins and stale render identities stay inert.
            boolean title = client.screen instanceof TitleScreen && client.player == null && client.level == null;
            boolean connected = bodyReady(client);
            if (!title && !connected) return;
            Path root = SettingsFiles.safeExisting(Path.of(directory));
            if (!Files.isDirectory(root) || root.startsWith(client.gameDirectory.toPath().toAbsolutePath().normalize())) {
                throw new IOException("GAME_PRIVATE_OUTPUT_REQUIRED");
            }
            if (runtime == null) runtime = new NativeGameRuntime(client);
            if (Boolean.getBoolean("strata.awaitGameAuthority")) {
                if (bootstrap == null) bootstrap = new GameBootstrap(root, runtime.fingerprint(), runtime.bootstrapIdentity());
                // No transport or action lane exists during this operator-only
                // barrier. The bounded launch owner must issue authority or stop.
                if (!bootstrap.authorityPresent()) return;
            }
            attempted = true;
            Path authority = root.resolve("game-authority.json");
            if (Files.exists(authority)) {
                lane = new GameActionLane(root, runtime.fingerprint(),
                    GameActionLane.Authority.read(SettingsJson.read(SettingsFiles.readOptions(authority))), runtime);
            }
            NativeGameProtocol protocol = new NativeGameProtocol(runtime, lane);
            bridge = new SettingsHttpBridge(protocol::execute, protocol);
            // Credential material belongs only in the operator's private broker directory.
            SettingsFiles.writeNew(root.resolve("game-connection-" + UUID.randomUUID() + ".json"),
                (bridge.descriptor(runtime.fingerprint()) + "\n").getBytes(StandardCharsets.UTF_8));
        } catch (IOException error) {
            attempted = true;
            if (bridge != null) bridge.close();
            bridge = null;
            if (lane != null) try { lane.close(); } catch (IOException ignored) { }
            throw new IllegalStateException("STRATA_GAME_BRIDGE_FAILED", error);
        }
    }
    private static void shutdown(GameShuttingDownEvent event) {
        if (bridge != null) bridge.close();
        if (lane != null) try { lane.close(); }
        catch (IOException error) { throw new IllegalStateException("STRATA_GAME_LANE_STOP_FAILED", error); }
    }
}
