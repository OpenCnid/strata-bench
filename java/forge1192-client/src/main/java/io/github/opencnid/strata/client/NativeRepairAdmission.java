package io.github.opencnid.strata.client;

import com.google.gson.JsonObject;
import java.io.IOException;
import java.util.HashSet;
import java.util.Set;

/** Immutable operator plan; permission to collect effects is never an effect verdict. */
final class NativeRepairAdmission {
    static final String POLICY = "operator-owned-native-settings-repair/1";
    final JsonObject value, plan, patch;
    final String campaign, agent, lease, transaction, settingsFingerprint, planDigest;
    final long epoch, expires;
    final Set<String> effectBindings;
    NativeRepairAdmission(JsonObject raw) throws IOException {
        SettingsJson.fields(raw, "schema", "policy", "worker_plan", "settings_fingerprint", "patch", "effect_bindings");
        if (!"strata/NativeSettingsRepairAdmission/1".equals(SettingsJson.string(raw, "schema"))
                || !POLICY.equals(SettingsJson.string(raw, "policy")) || !raw.get("worker_plan").isJsonObject()
                || !raw.get("patch").isJsonObject() || !raw.get("effect_bindings").isJsonArray()) {
            throw new IOException("SETTINGS_REPAIR_INVALID");
        }
        value = raw.deepCopy(); plan = value.getAsJsonObject("worker_plan"); patch = value.getAsJsonObject("patch");
        SettingsJson.fields(plan, "schema", "policy", "campaign_id", "agent_id", "epoch", "lease_id",
            "transaction_id", "plan_digest", "expires_unix_ms");
        if (!"strata/WorkerRepairPlan/1".equals(SettingsJson.string(plan, "schema"))
                || !"operator-owned-fixed-repair-pause/1".equals(SettingsJson.string(plan, "policy"))) {
            throw new IOException("SETTINGS_REPAIR_INVALID");
        }
        campaign = GameBatch.id(plan, "campaign_id"); agent = GameBatch.id(plan, "agent_id");
        lease = GameBatch.id(plan, "lease_id"); transaction = GameBatch.id(plan, "transaction_id");
        epoch = SettingsJson.integer(plan, "epoch"); expires = SettingsJson.integer(plan, "expires_unix_ms");
        planDigest = GameBatch.digest(plan, "plan_digest"); settingsFingerprint = GameBatch.digest(value, "settings_fingerprint");
        if (epoch < 1 || expires < 1) throw new IOException("SETTINGS_REPAIR_INVALID");
        NativeSettingsProtocol.validatePatch(patch);
        if (!transaction.equals(GameBatch.id(patch, "transaction_id"))) throw new IOException("SETTINGS_REPAIR_NOT_OWNED");
        var bindings = value.getAsJsonArray("effect_bindings"); var allowed = new HashSet<String>();
        if (bindings.isEmpty() || bindings.size() > 2048) throw new IOException("SETTINGS_REPAIR_INVALID");
        for (var binding : bindings) {
            if (!binding.isJsonPrimitive() || !binding.getAsJsonPrimitive().isString()) throw new IOException("SETTINGS_REPAIR_INVALID");
            String id = binding.getAsString(); NativeSettingsProtocol.identifier(id);
            if (!allowed.add(id)) throw new IOException("SETTINGS_REPAIR_INVALID");
        }
        if (!allowed.containsAll(patch.getAsJsonObject("changes").keySet())) throw new IOException("SETTINGS_REPAIR_INVALID");
        effectBindings = Set.copyOf(allowed);
    }
    void effect(SettingsEffectRun.Request request) throws IOException {
        if (!request.planDigest().equals(planDigest) || !effectBindings.contains(request.binding())
                || request.transaction() != null && !transaction.equals(request.transaction())) {
            throw new IOException("SETTINGS_REPAIR_NOT_OWNED");
        }
    }
}
