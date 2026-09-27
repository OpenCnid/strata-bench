package io.github.opencnid.strata.client;

import com.google.gson.JsonObject;
import java.io.IOException;
import java.util.LinkedHashMap;

/** Shared production settings coordinator; Minecraft-specific observation/input is a separate port. */
final class SettingsEffectsCoordinator {
    private final SettingsStore store;
    private final SettingsStore.RuntimePort runtime;
    private final NativeSettingsProtocol protocol;
    private final GameActionLane lane;
    private final SettingsEffectRun.Port port;
    private final LinkedHashMap<String, SettingsEffectRun> runs = new LinkedHashMap<>();
    private SettingsEffectRun active;
    SettingsEffectsCoordinator(SettingsStore store, SettingsStore.RuntimePort runtime,
            GameActionLane lane, SettingsEffectRun.Port port) throws IOException {
        runtime.requireClientThread();
        if (lane == null) throw new IOException("CAPABILITY_MISSING");
        this.store = store; this.runtime = runtime; this.lane = lane; this.port = port;
        protocol = new NativeSettingsProtocol(store, runtime);
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
            var run = new SettingsEffectRun(parsed, store, lane, port);
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
        runtime.requireClientThread();
        if (active == null) return;
        try { active.tick(); }
        catch (IOException error) {
            if ("SETTINGS_INPUT_RELEASE_UNCONFIRMED".equals(error.getMessage())
                    || !lane.health().get("journal_healthy").getAsBoolean()) throw error;
            // Typed terminal failure remains queryable so the owner can roll back.
        }
        finally { if (!active.status().get("state").getAsString().equals("running")) active = null; }
    }

    void screenOpening(JsonObject value) throws IOException {
        runtime.requireClientThread();
        if (active != null) active.screenChanged(value);
    }
    void stop() throws IOException {
        runtime.requireClientThread();
        if (active != null) try { active.cancel(); } finally { active = null; }
    }
}
