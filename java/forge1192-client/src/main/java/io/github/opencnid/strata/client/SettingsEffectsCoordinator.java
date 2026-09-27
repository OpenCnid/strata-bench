package io.github.opencnid.strata.client;

import com.google.gson.JsonObject;
import java.io.IOException;
import java.util.LinkedHashMap;
import java.util.Set;

/** Shared production settings coordinator; Minecraft-specific observation/input is a separate port. */
final class SettingsEffectsCoordinator {
    private final SettingsStore store;
    private final SettingsStore.RuntimePort runtime;
    private final NativeSettingsProtocol protocol;
    private final GameActionLane lane;
    private final SettingsEffectRun.Port port;
    private final boolean requireRepair;
    private final boolean allowCommit;
    private final boolean allowRestart;
    private final LinkedHashMap<String, SettingsEffectRun> runs = new LinkedHashMap<>();
    private SettingsEffectRun active;
    SettingsEffectsCoordinator(SettingsStore store, SettingsStore.RuntimePort runtime,
            GameActionLane lane, SettingsEffectRun.Port port) throws IOException {
        this(store, runtime, lane, port, false);
    }
    SettingsEffectsCoordinator(SettingsStore store, SettingsStore.RuntimePort runtime,
            GameActionLane lane, SettingsEffectRun.Port port, boolean requireRepair) throws IOException {
        this(store, runtime, lane, port, requireRepair, false);
    }
    SettingsEffectsCoordinator(SettingsStore store, SettingsStore.RuntimePort runtime,
            GameActionLane lane, SettingsEffectRun.Port port, boolean requireRepair, boolean allowCommit) throws IOException {
        this(store, runtime, lane, port, requireRepair, allowCommit, false);
    }
    SettingsEffectsCoordinator(SettingsStore store, SettingsStore.RuntimePort runtime,
            GameActionLane lane, SettingsEffectRun.Port port, boolean requireRepair, boolean allowCommit, boolean allowRestart) throws IOException {
        runtime.requireClientThread();
        if (lane == null) throw new IOException("CAPABILITY_MISSING");
        if (allowCommit && !requireRepair) throw new IOException("SETTINGS_COMMIT_MODE_INVALID");
        if (allowRestart && !requireRepair) throw new IOException("SETTINGS_RESTART_MODE_INVALID");
        this.store = store; this.runtime = runtime; this.lane = lane; this.port = port;
        this.requireRepair = requireRepair;
        this.allowCommit = allowCommit;
        this.allowRestart = allowRestart;
        protocol = new NativeSettingsProtocol(store, runtime);
    }
    static void validate(JsonObject request, String session, long now) throws IOException {
        String operation = SettingsJson.string(request, "operation");
        JsonObject args = request.getAsJsonObject("args");
        if (operation.equals("settings_repair_bind")) new NativeRepairAdmission(args);
        else if (operation.equals("settings_restart_prepare")) new NativeRepairRestart(args);
        else if (operation.equals("settings_restart_continue")) NativeRepairRestart.checkpoint(args);
        else if (operation.equals("settings_restart_status")) { SettingsJson.fields(args, "restart_id"); GameBatch.id(args, "restart_id"); }
        else if (operation.equals("settings_commit")) new SettingsCommitDecision(args);
        else if (operation.equals("settings_commit_status")) { SettingsJson.fields(args, "transaction_id"); GameBatch.id(args, "transaction_id"); }
        else if (operation.equals("settings_repair_status")) { SettingsJson.fields(args, "transaction_id"); GameBatch.id(args, "transaction_id"); }
        else if (operation.equals("settings_effect_start")) SettingsEffectRun.Request.read(args);
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
        if (operation.equals("settings_restart_status")) return lane.repairRestartStatus(GameBatch.id(args, "restart_id"));
        if (operation.equals("settings_restart_prepare") || operation.equals("settings_restart_continue")) {
            if (!allowRestart || !requireRepair) throw new IOException("CAPABILITY_MISSING");
            if (active != null) throw new IOException("RECONFIGURING");
            var restart = operation.equals("settings_restart_prepare") ? new NativeRepairRestart(args) : NativeRepairRestart.checkpoint(args);
            var admission = lane.repairAdmission();
            if (!admission.transaction.equals(restart.transaction) || !admission.planDigest.equals(restart.planDigest)
                    || !store.fingerprint().equals(admission.settingsFingerprint)) throw new IOException("SETTINGS_RESTART_NOT_OWNED");
            if (!store.verificationHead(restart.transaction).equals(restart.expected)) throw new IOException("SETTINGS_REVISION_CONFLICT");
            return operation.equals("settings_restart_prepare") ? lane.prepareRepairRestart(restart) : lane.continueRepairRestart(args);
        }
        if (operation.equals("settings_repair_bind")) {
            if (!requireRepair) throw new IOException("CAPABILITY_MISSING");
            var admission = new NativeRepairAdmission(args);
            if (!admission.settingsFingerprint.equals(store.fingerprint())) throw new IOException("SETTINGS_REPAIR_NOT_OWNED");
            if (!lane.hasRepair()) {
                var snapshot = store.snapshot();
                var consumers = new java.util.HashSet<>(runtime.bindings().keySet());
                consumers.addAll(port.fixedControls());
                if (snapshot.revision() != SettingsJson.integer(admission.patch, "expected_revision")
                        || !snapshot.digest().equals(GameBatch.digest(admission.patch, "expected_digest"))
                        || !consumers.containsAll(admission.effectBindings)) throw new IOException("SETTINGS_REVISION_CONFLICT");
            }
            return lane.admitRepair(admission);
        }
        if (operation.equals("settings_repair_status")) {
            if (!lane.repairAdmission().transaction.equals(GameBatch.id(args, "transaction_id"))) throw new IOException("SETTINGS_REPAIR_NOT_OWNED");
            return lane.repairStatus();
        }
        if (operation.equals("settings_commit_status")) {
            if (!lane.repairAdmission().transaction.equals(GameBatch.id(args, "transaction_id"))) throw new IOException("SETTINGS_REPAIR_NOT_OWNED");
            return store.commitStatus(GameBatch.id(args, "transaction_id"));
        }
        SettingsCommitDecision decision = operation.equals("settings_commit") ? new SettingsCommitDecision(args) : null;
        if (decision != null) {
            var admission = lane.repairAdmission();
            if (!allowCommit || !requireRepair || !admission.transaction.equals(decision.transaction)
                    || !admission.planDigest.equals(decision.planDigest)) throw new IOException("SETTINGS_REPAIR_NOT_OWNED");
        }
        boolean ownedRepair = requireRepair || lane.hasRepair();
        if (ownedRepair && !Set.of("settings_snapshot", "settings_status", "settings_effect_status").contains(operation)) {
            var admission = lane.repairAdmission();
            if (operation.equals("settings_apply") && !admission.patch.equals(args)) throw new IOException("SETTINGS_REPAIR_NOT_OWNED");
            if (operation.equals("settings_rollback") && !admission.transaction.equals(GameBatch.id(args, "transaction_id"))) throw new IOException("SETTINGS_REPAIR_NOT_OWNED");
            if (operation.equals("settings_effect_start")) {
                var effect = SettingsEffectRun.Request.read(args); admission.effect(effect);
                if (allowRestart) lane.repairRestartStage(effect.stage());
            }
            if (!operation.equals("settings_rollback")) {
                lane.repairReady();
                if (SettingsJson.integer(request, "deadline_unix_ms") > admission.expires) throw new IOException("SETTINGS_DEADLINE_INVALID");
            }
        }
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
        JsonObject nested = decision == null ? nested(request) : null;
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
        boolean repairRollback = ownedRepair && operation.equals("settings_rollback");
        lane.beginReconfiguration(id, SettingsJson.integer(request, "deadline_unix_ms"), repairRollback);
        try {
            JsonObject admission = new JsonObject(); admission.addProperty("schema", "strata/NativeSettingsWriteAdmission/1");
            admission.addProperty("operation", operation); admission.addProperty("settings_fingerprint", store.fingerprint());
            admission.addProperty("transaction_id", GameBatch.id(args, "transaction_id"));
            admission.addProperty("args_sha256", KeyOptions.sha256(args.toString()));
            if (!repairRollback) lane.reconfigurationObservation(id, admission);
            JsonObject[] result = {null};
            lane.reconfigurationEmit(id, operation.equals("settings_rollback"),
                () -> result[0] = decision == null ? protocol.execute(nested) : store.commit(decision));
            lane.endReconfiguration(id, "completed", repairRollback); return result[0];
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
