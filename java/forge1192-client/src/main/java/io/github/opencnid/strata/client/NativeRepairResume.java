package io.github.opencnid.strata.client;

import com.google.gson.JsonObject;
import java.io.IOException;

/** Private controller decision. The referenced verification is not evaluated by this parser. */
final class NativeRepairResume {
    static final String POLICY = "operator-owned-settings-resume/1";
    final JsonObject value, plan;
    final String id, transaction, phase, verificationRef;
    final long generation, leaseUntil;
    final SettingsStore.Snapshot expected;

    NativeRepairResume(JsonObject raw) throws IOException {
        SettingsJson.fields(raw, "schema", "policy", "resume_id", "worker_plan", "expected_revision",
            "expected_digest", "completion_phase", "verification_ref", "connection_generation", "lease_until_unix_ms");
        if (!"strata/NativeSettingsResumeDecision/1".equals(SettingsJson.string(raw, "schema"))
                || !POLICY.equals(SettingsJson.string(raw, "policy")) || !raw.get("worker_plan").isJsonObject()) {
            throw new IOException("SETTINGS_RESUME_INVALID");
        }
        value = raw.deepCopy(); plan = value.getAsJsonObject("worker_plan");
        SettingsJson.fields(plan, "schema", "policy", "campaign_id", "agent_id", "epoch", "lease_id",
            "transaction_id", "plan_digest", "expires_unix_ms");
        if (!"strata/WorkerRepairPlan/1".equals(SettingsJson.string(plan, "schema"))
                || !"operator-owned-fixed-repair-pause/1".equals(SettingsJson.string(plan, "policy"))) {
            throw new IOException("SETTINGS_RESUME_INVALID");
        }
        for (String field : new String[]{"campaign_id", "agent_id", "lease_id"}) GameBatch.id(plan, field);
        GameBatch.digest(plan, "plan_digest");
        transaction = GameBatch.id(plan, "transaction_id"); id = GameBatch.id(raw, "resume_id");
        phase = SettingsJson.string(raw, "completion_phase");
        verificationRef = SettingsJson.string(raw, "verification_ref");
        generation = SettingsJson.integer(raw, "connection_generation");
        leaseUntil = SettingsJson.integer(raw, "lease_until_unix_ms");
        long revision = SettingsJson.integer(raw, "expected_revision");
        if (SettingsJson.integer(plan, "epoch") < 1 || SettingsJson.integer(plan, "expires_unix_ms") < 1
                || generation < 0 || leaseUntil < 1 || leaseUntil > SettingsJson.integer(plan, "expires_unix_ms") || revision < 1
                || !java.util.Set.of("committed", "rolled_back").contains(phase)
                || !verificationRef.matches("cas:sha256:[0-9a-f]{64}")) throw new IOException("SETTINGS_RESUME_INVALID");
        expected = new SettingsStore.Snapshot(revision, GameBatch.digest(raw, "expected_digest"));
    }
}
