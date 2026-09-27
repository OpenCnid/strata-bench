package io.github.opencnid.strata.client;

import com.google.gson.JsonObject;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Set;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.screens.ChatScreen;
import net.minecraft.client.gui.screens.Screen;

/** Explicit private conformance route; shared game authority, no second input writer or effect verdict. */
final class NativeSettingsEffects implements AutoCloseable, SettingsEffectRun.Port {
    static final String PROPERTY = "strata.settingsEffects";
    static final String REPAIR_PROPERTY = "strata.settingsRepairOwner";
    static final String COMMIT_PROPERTY = "strata.settingsCommitOwner";
    static final String COMMIT_POLICY = "operator-recorded-settings-commit/1";
    static final String RESTART_PROPERTY = "strata.settingsRestartOwner";
    static final String RESTART_POLICY = "operator-owned-settings-restart/1";
    static final String RESUME_PROPERTY = "strata.settingsResumeOwner";
    private final Minecraft client;
    private final NativeSettingsRuntime runtime;
    private final SettingsStore store;
    private final SettingsEffectsCoordinator coordinator;
    private long tick;

    NativeSettingsEffects(Minecraft client, Path gameRoot, GameActionLane lane) throws IOException {
        this.client = client;
        if (lane == null) throw new IOException("CAPABILITY_MISSING");
        Path root = SettingsFiles.safeExisting(gameRoot).resolve("settings-effects");
        if (!Files.exists(root)) Files.createDirectory(root);
        root = SettingsFiles.safeExisting(root);
        runtime = new NativeSettingsRuntime(client);
        store = new SettingsStore(client.gameDirectory.toPath().toAbsolutePath().normalize(), root, runtime.fingerprint(), runtime);
        coordinator = new SettingsEffectsCoordinator(store, runtime, lane, this, Boolean.getBoolean(REPAIR_PROPERTY),
            Boolean.getBoolean(COMMIT_PROPERTY), Boolean.getBoolean(RESTART_PROPERTY), Boolean.getBoolean(RESUME_PROPERTY));
    }
    static boolean enabled() { return Boolean.getBoolean(PROPERTY); }
    static void validateModes(java.util.Properties properties, java.util.Map<String, String> environment) {
        String value = properties.getProperty(PROPERTY);
        String repair = properties.getProperty(REPAIR_PROPERTY);
        String commit = properties.getProperty(COMMIT_PROPERTY);
        String restart = properties.getProperty(RESTART_PROPERTY);
        String resume = properties.getProperty(RESUME_PROPERTY);
        if (resume != null && !resume.equals("false") && (!resume.equals("true") || !"true".equals(repair))) {
            throw new IllegalStateException("SETTINGS_RESUME_MODE_INVALID");
        }
        if (restart != null && !restart.equals("false") && (!restart.equals("true") || !"true".equals(repair))) {
            throw new IllegalStateException("SETTINGS_RESTART_MODE_INVALID");
        }
        if (commit != null && !commit.equals("false") && (!commit.equals("true") || !"true".equals(repair))) {
            throw new IllegalStateException("SETTINGS_COMMIT_MODE_INVALID");
        }
        if (repair != null && !repair.equals("false") && (!repair.equals("true") || !"true".equals(value))) {
            throw new IllegalStateException("SETTINGS_REPAIR_MODE_INVALID");
        }
        if (value == null || value.equals("false")) return;
        if (!value.equals("true") || properties.getProperty("strata.gameBridgeDirectory") == null) {
            throw new IllegalStateException("SETTINGS_EFFECT_MODE_INVALID");
        }
        for (String incompatible : new String[]{"strata.settingsCrashDirectory", "strata.settingsBridgeDirectory",
                "strata.settingsTransactionDirectory", "strata.settingsDiscoveryDirectory", "strata.collisionProbeDirectory"}) {
            if (properties.getProperty(incompatible) != null) throw new IllegalStateException("SETTINGS_DIAGNOSTICS_CONFLICT");
        }
        if (environment.containsKey("STRATA_SETTINGS_DISCOVERY_DIR")) throw new IllegalStateException("SETTINGS_DIAGNOSTICS_CONFLICT");
    }
    JsonObject execute(JsonObject request) throws IOException { return coordinator.execute(request); }
    void tick() throws IOException { tick++; coordinator.tick(); }
    void screenOpening(Screen current, Screen next, boolean cancelled) throws IOException {
        JsonObject value = new JsonObject(); value.addProperty("client_tick", tick);
        value.addProperty("from_screen", screen(current)); value.addProperty("requested_screen", screen(next));
        value.addProperty("cancelled_at_observer", cancelled);
        coordinator.screenOpening(value);
    }
    void stop() throws IOException { coordinator.stop(); }
    private static Set<Integer> candidates(KeyInputSession.Request request) {
        Set<Integer> result = new java.util.HashSet<>(); result.add(request.key());
        if (request.companion() != null) result.add(request.companion());
        if (request.modifier() != KeyInputSession.Modifier.NONE) result.add(request.modifier().key);
        return Set.copyOf(result);
    }
    @Override public void validateBinding(String id, long hold) throws IOException {
        var request = runtime.effectKey(id, hold); request.validate(candidates(request));
    }
    @Override public Set<String> fixedControls() { return Set.of(NativeSettingsRuntime.FIXED_ESCAPE); }
    @Override public KeyInputSession start(String id, long hold, GameActionLane.Emitter ordinary,
            GameActionLane.Emitter safety) throws IOException {
        var request = runtime.effectKey(id, hold);
        return NativeKeyInput.start(client, request, candidates(request), ordinary, safety);
    }
    private static String screen(Screen screen) { return screen == null ? "none" : screen.getClass().getName(); }
    @Override public JsonObject observe() throws IOException {
        runtime.requireClientThread();
        if (client.player == null || client.level == null || client.getConnection() == null) throw new IOException("SETTINGS_CONTEXT_UNVERIFIED");
        JsonObject value = new JsonObject(); value.addProperty("client_tick", tick);
        value.addProperty("context", client.screen == null ? "IN_GAME" : client.screen instanceof ChatScreen ? "CHAT" : "GUI");
        value.addProperty("screen", screen(client.screen)); value.addProperty("window_active", client.isWindowActive());
        value.addProperty("menu_id", client.player.containerMenu.containerId);
        value.addProperty("menu_type", client.player.containerMenu.getClass().getName());
        value.addProperty("x", client.player.getX()); value.addProperty("y", client.player.getY()); value.addProperty("z", client.player.getZ());
        value.addProperty("sneaking", client.player.isShiftKeyDown()); value.addProperty("sprinting", client.player.isSprinting());
        value.addProperty("using_item", client.player.isUsingItem());
        value.addProperty("swinging", client.player.swinging);
        value.addProperty("mouse_grabbed", client.mouseHandler.isMouseGrabbed());
        value.addProperty("mouse_left", client.mouseHandler.isLeftPressed());
        value.addProperty("mouse_right", client.mouseHandler.isRightPressed());
        return value;
    }
    @Override public void close() throws IOException { try { stop(); } finally { store.close(); } }
}
