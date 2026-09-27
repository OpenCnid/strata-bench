package io.github.opencnid.strata.client;

import com.google.gson.JsonObject;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.LinkedHashMap;
import java.util.Set;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.screens.ChatScreen;
import net.minecraft.client.gui.screens.Screen;

/** Explicit private conformance route; shared game authority, no second input writer or effect verdict. */
final class NativeSettingsEffects implements AutoCloseable, SettingsEffectRun.Port {
    static final String PROPERTY = "strata.settingsEffects";
    private final Minecraft client;
    private final NativeSettingsRuntime runtime;
    private final SettingsStore store;
    private final NativeSettingsProtocol protocol;
    private final GameActionLane lane;
    private final LinkedHashMap<String, SettingsEffectRun> runs = new LinkedHashMap<>();
    private SettingsEffectRun active;
    private long tick;

    NativeSettingsEffects(Minecraft client, Path gameRoot, GameActionLane lane) throws IOException {
        this.client = client; this.lane = lane;
        if (lane == null) throw new IOException("CAPABILITY_MISSING");
        Path root = SettingsFiles.safeExisting(gameRoot).resolve("settings-effects");
        if (!Files.exists(root)) Files.createDirectory(root);
        root = SettingsFiles.safeExisting(root);
        runtime = new NativeSettingsRuntime(client);
        store = new SettingsStore(client.gameDirectory.toPath().toAbsolutePath().normalize(), root, runtime.fingerprint(), runtime);
        protocol = new NativeSettingsProtocol(store, runtime);
    }
    static boolean enabled() { return Boolean.getBoolean(PROPERTY); }
    static void validateModes(java.util.Properties properties, java.util.Map<String, String> environment) {
        String value = properties.getProperty(PROPERTY);
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
    static void validate(JsonObject request, String session, long now) throws IOException {
        String operation = SettingsJson.string(request, "operation");
        JsonObject args = request.getAsJsonObject("args");
        if (operation.equals("settings_effect_start")) SettingsEffectRun.Request.read(args);
        else if (operation.equals("settings_effect_status")) { SettingsJson.fields(args, "id"); GameBatch.id(args, "id"); }
        else {
            JsonObject nested = nested(request);
            NativeSettingsProtocol.validate(nested, session, now);
        }
    }
    private static JsonObject nested(JsonObject request) throws IOException {
        JsonObject nested = request.deepCopy(); nested.addProperty("schema", NativeSettingsProtocol.REQUEST_SCHEMA);
        nested.addProperty("operation", SettingsJson.string(request, "operation").substring("settings_".length()));
        return nested;
    }
    JsonObject execute(JsonObject request) throws IOException {
        runtime.requireClientThread();
        String operation = SettingsJson.string(request, "operation");
        JsonObject args = request.getAsJsonObject("args");
        if (operation.equals("settings_effect_status")) {
            SettingsEffectRun run = runs.get(GameBatch.id(args, "id"));
            if (run == null) throw new IOException("SETTINGS_VERIFICATION_UNKNOWN");
            return run.status();
        }
        if (operation.equals("settings_effect_start")) {
            var parsed = SettingsEffectRun.Request.read(args);
            SettingsEffectRun previous = runs.get(parsed.id());
            if (previous != null) {
                if (!previous.status().getAsJsonObject("request").equals(SettingsEffectRun.json(parsed))) throw new IOException("SETTINGS_IDEMPOTENCY_CONFLICT");
                return previous.status();
            }
            if (active != null) throw new IOException("RECONFIGURING");
            var run = new SettingsEffectRun(parsed, store, lane, this);
            runs.put(parsed.id(), run); active = run;
            while (runs.size() > 16) runs.remove(runs.keySet().iterator().next());
            try { run.start(SettingsJson.integer(request, "deadline_unix_ms")); }
            catch (IOException | RuntimeException error) { active = null; throw error; }
            return run.status();
        }
        JsonObject nested = nested(request);
        if (operation.equals("settings_snapshot") || operation.equals("settings_status")) return protocol.execute(nested);
        if (active != null) throw new IOException("RECONFIGURING");
        String interrupted = lane.interruptedReconfiguration();
        if (operation.equals("settings_rollback") && interrupted != null) {
            JsonObject[] result = {null};
            // Recovery may only restore transaction-owned values through the CAS store.
            lane.reconfigurationEmit(interrupted, true, () -> result[0] = protocol.execute(nested));
            lane.endReconfiguration(interrupted, "unknown"); return result[0];
        }
        String id = "settings-write:" + KeyOptions.sha256(GameBatch.id(request, "request_id"));
        lane.beginReconfiguration(id, SettingsJson.integer(request, "deadline_unix_ms"));
        try {
            JsonObject admission = new JsonObject(); admission.addProperty("schema", "strata/NativeSettingsWriteAdmission/1");
            admission.addProperty("operation", operation); admission.addProperty("settings_fingerprint", store.fingerprint());
            admission.addProperty("transaction_id", GameBatch.id(args, "transaction_id"));
            admission.addProperty("args_sha256", KeyOptions.sha256(args.toString()));
            lane.reconfigurationObservation(id, admission);
            JsonObject[] result = {null};
            lane.reconfigurationEmit(id, operation.equals("settings_rollback"), () -> result[0] = protocol.execute(nested));
            lane.endReconfiguration(id, "completed"); return result[0];
        } catch (IOException | RuntimeException error) {
            try { lane.endReconfiguration(id, "unknown"); } catch (IOException cleanup) { error.addSuppressed(cleanup); }
            throw error;
        }
    }
    void tick() throws IOException {
        tick++;
        if (active == null) return;
        try { active.tick(); }
        catch (IOException error) {
            if ("SETTINGS_INPUT_RELEASE_UNCONFIRMED".equals(error.getMessage())
                    || !lane.health().get("journal_healthy").getAsBoolean()) throw error;
            // Typed terminal failure remains queryable so the owner can roll back.
        }
        finally { if (!active.status().get("state").getAsString().equals("running")) active = null; }
    }
    void screenOpening(Screen current, Screen next, boolean cancelled) throws IOException {
        if (active == null) return;
        JsonObject value = new JsonObject(); value.addProperty("client_tick", tick);
        value.addProperty("from_screen", screen(current)); value.addProperty("requested_screen", screen(next));
        value.addProperty("cancelled_at_observer", cancelled);
        active.screenChanged(value);
    }
    void stop() throws IOException { if (active != null) try { active.cancel(); } finally { active = null; } }
    private static Set<Integer> candidates(KeyInputSession.Request request) {
        Set<Integer> result = new java.util.HashSet<>(); result.add(request.key());
        if (request.modifier() != KeyInputSession.Modifier.NONE) result.add(request.modifier().key);
        return Set.copyOf(result);
    }
    @Override public void validateBinding(String id, long hold) throws IOException {
        var request = runtime.effectKey(id, hold); request.validate(candidates(request));
    }
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
        return value;
    }
    @Override public void close() throws IOException { try { stop(); } finally { store.close(); } }
}
