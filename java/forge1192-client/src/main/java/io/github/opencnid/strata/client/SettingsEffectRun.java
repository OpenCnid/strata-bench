package io.github.opencnid.strata.client;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import java.io.IOException;
import java.util.Set;

/** Transaction-bound raw observations. A completed run never asserts that a binding passed. */
final class SettingsEffectRun {
    record Request(String id, String transaction, long revision, String digest, String planDigest,
            String binding, String context, String stage, long holdMs, int settleTicks) {
        static Request read(JsonObject value) throws IOException {
            SettingsJson.fields(value, "id", "transaction_id", "expected_revision", "expected_digest", "plan_digest",
                "binding_id", "context", "stage", "hold_ms", "settle_ticks");
            String context = SettingsJson.string(value, "context"), stage = SettingsJson.string(value, "stage");
            long hold = SettingsJson.integer(value, "hold_ms"), ticks = SettingsJson.integer(value, "settle_ticks");
            long revision = SettingsJson.integer(value, "expected_revision");
            if (revision < 1 || hold < 1 || hold > KeyInputSession.MAX_HOLD_MS || ticks < 1 || ticks > 200
                    || !Set.of("IN_GAME", "GUI", "CHAT").contains(context)
                    || !Set.of("baseline", "before_restart", "after_restart").contains(stage)) throw new IOException("SETTINGS_EFFECT_REQUEST_INVALID");
            String transaction;
            if (stage.equals("baseline")) {
                if (!value.get("transaction_id").isJsonNull()) throw new IOException("SETTINGS_EFFECT_REQUEST_INVALID");
                transaction = null;
            } else transaction = GameBatch.id(value, "transaction_id");
            return new Request(GameBatch.id(value, "id"), transaction, revision,
                GameBatch.digest(value, "expected_digest"), GameBatch.digest(value, "plan_digest"),
                GameBatch.id(value, "binding_id"), context, stage, hold, (int) ticks);
        }
    }
    interface Port {
        default Set<String> fixedControls() { return Set.of(); }
        void validateBinding(String binding, long holdMs) throws IOException;
        JsonObject observe() throws IOException;
        KeyInputSession start(String binding, long holdMs, GameActionLane.Emitter ordinary,
            GameActionLane.Emitter safety) throws IOException;
    }
    private final Request request;
    private final SettingsStore store;
    private final GameActionLane lane;
    private final Port port;
    private final JsonArray observations = new JsonArray();
    private final SettingsStore.Snapshot head;
    private KeyInputSession input;
    private int settling, bytes;
    private String state = "prepared", error;

    SettingsEffectRun(Request request, SettingsStore store, GameActionLane lane, Port port) throws IOException {
        // All constructors pass through the same strict parser as the transport.
        Request.read(json(request));
        this.request = request; this.store = store; this.lane = lane; this.port = port;
        head = new SettingsStore.Snapshot(request.revision, request.digest);
        verifyHead(); port.validateBinding(request.binding, request.holdMs);
    }
    void start(long deadline) throws IOException {
        if (!state.equals("prepared")) throw new IOException("SETTINGS_VERIFICATION_CONSUMED");
        JsonObject before;
        try {
            before = port.observe();
            if (!request.context.equals(SettingsJson.string(before, "context"))) throw new IOException("SETTINGS_CONTEXT_UNVERIFIED");
            lane.beginReconfiguration(request.id, deadline);
        } catch (IOException | RuntimeException error) {
            state = "refused"; this.error = error.getMessage() == null ? "SETTINGS_EFFECT_UNKNOWN" : error.getMessage(); throw error;
        }
        state = "running";
        try {
            verifyHead(); before = port.observe();
            if (!request.context.equals(SettingsJson.string(before, "context"))) throw new IOException("SETTINGS_CONTEXT_UNVERIFIED");
            JsonObject admission = new JsonObject(); admission.addProperty("schema", "strata/NativeSettingsEffectAdmission/2");
            admission.addProperty("settings_fingerprint", store.fingerprint()); admission.add("request", json(request));
            append("admission", admission);
            append("before", before);
            input = port.start(request.binding, request.holdMs,
                operation -> lane.reconfigurationEmit(request.id, false, operation),
                operation -> lane.reconfigurationEmit(request.id, true, operation));
        } catch (IOException | RuntimeException error) {
            fail(error); throw error;
        }
    }
    static JsonObject json(Request r) {
        JsonObject v = new JsonObject(); v.addProperty("id", r.id); v.addProperty("transaction_id", r.transaction);
        v.addProperty("expected_revision", r.revision); v.addProperty("expected_digest", r.digest);
        v.addProperty("plan_digest", r.planDigest); v.addProperty("binding_id", r.binding);
        v.addProperty("context", r.context); v.addProperty("stage", r.stage);
        v.addProperty("hold_ms", r.holdMs); v.addProperty("settle_ticks", r.settleTicks); return v;
    }
    private void verifyHead() throws IOException {
        // Baseline input measures the unmodified or restored map. It never
        // fabricates a pending transaction and cannot bypass recovery ownership.
        var actual = request.stage.equals("baseline") ? store.snapshot() : store.verificationHead(request.transaction);
        if (!head.equals(actual)) throw new IOException("SETTINGS_REVISION_CONFLICT");
    }
    private void append(String phase, JsonObject value) throws IOException {
        JsonObject observation = new JsonObject(); observation.addProperty("phase", phase);
        observation.addProperty("index", observations.size()); observation.add("value", value.deepCopy());
        int length = observation.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8).length;
        if (observations.size() >= 256 || bytes + length > 196608) throw new IOException("SETTINGS_EFFECT_BOUNDS");
        lane.reconfigurationObservation(request.id, observation); observations.add(observation); bytes += length;
    }
    void tick() throws IOException {
        if (!state.equals("running")) return;
        try {
            lane.reconfigurationReady(request.id); verifyHead();
            boolean released = input.tick(operation -> lane.reconfigurationEmit(request.id, false, operation));
            if (released && settling == 0) append("input_release", input.releaseReceipt());
            append(released ? "released" : "held", port.observe());
            if (released) {
                // Continue observing normal game ticks for delayed server/GUI effects.
                if (++settling >= request.settleTicks) {
                    lane.endReconfiguration(request.id, "completed"); state = "observed";
                } else lane.reconfigurationEmit(request.id, false, () -> {});
            }
        } catch (IOException | RuntimeException error) { fail(error); throw error; }
    }
    void screenChanged(JsonObject observation) throws IOException {
        if (!state.equals("running")) return;
        try { verifyHead(); append("screen_opening", observation); }
        catch (IOException | RuntimeException error) { fail(error); throw error; }
    }
    void cancel() throws IOException {
        if (state.equals("running")) fail(new IOException("SETTINGS_VERIFICATION_CANCELLED"));
    }
    private void fail(Exception cause) throws IOException {
        state = "unknown";
        String code = cause.getMessage(); error = code != null && code.matches("[A-Z][A-Z0-9_]{1,95}") ? code : "SETTINGS_EFFECT_UNKNOWN";
        IOException cleanupFailure = null;
        if (input != null) try { input.cancel(); }
        catch (IOException cleanup) { cleanupFailure = cleanup; cause.addSuppressed(cleanup); }
        try { lane.endReconfiguration(request.id, "unknown"); }
        catch (IOException cleanup) { if (cleanupFailure == null) cleanupFailure = cleanup; cause.addSuppressed(cleanup); }
        if (cleanupFailure != null) throw new IOException("SETTINGS_INPUT_RELEASE_UNCONFIRMED", cause);
    }
    JsonObject status() {
        JsonObject value = new JsonObject(); value.addProperty("schema", "strata/NativeSettingsEffects/4");
        value.add("request", json(request)); value.addProperty("state", state); value.addProperty("error_code", error);
        value.addProperty("verified", false); value.addProperty("committed", false);
        value.add("observations", observations.deepCopy()); return value;
    }
    String id() { return request.id; }
}
