package io.github.opencnid.strata.client;

import com.google.gson.JsonObject;
import java.io.IOException;

/** Records a private controller decision; this parser does not evaluate physical effects. */
final class SettingsCommitDecision {
    final JsonObject value;
    final String transaction, planDigest, verificationRef;
    final SettingsStore.Snapshot expected;
    SettingsCommitDecision(JsonObject raw) throws IOException {
        SettingsJson.fields(raw, "schema", "transaction_id", "plan_digest", "expected_revision",
            "expected_digest", "verification_ref");
        if (!"strata/NativeSettingsCommitDecision/1".equals(SettingsJson.string(raw, "schema"))) {
            throw new IOException("SETTINGS_COMMIT_INVALID");
        }
        transaction = GameBatch.id(raw, "transaction_id"); planDigest = GameBatch.digest(raw, "plan_digest");
        long revision = SettingsJson.integer(raw, "expected_revision");
        verificationRef = SettingsJson.string(raw, "verification_ref");
        if (revision < 1 || !verificationRef.matches("cas:sha256:[0-9a-f]{64}")) throw new IOException("SETTINGS_COMMIT_INVALID");
        expected = new SettingsStore.Snapshot(revision, GameBatch.digest(raw, "expected_digest"));
        value = raw.deepCopy();
    }
}
