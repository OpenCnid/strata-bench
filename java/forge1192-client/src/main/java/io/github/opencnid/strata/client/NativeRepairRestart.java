package io.github.opencnid.strata.client;

import com.google.gson.JsonObject;
import java.io.IOException;

/** Exact pending-head handoff. This does not attest process death or grant gameplay input. */
final class NativeRepairRestart {
    final JsonObject value;
    final String transaction, planDigest, id;
    final SettingsStore.Snapshot expected;
    NativeRepairRestart(JsonObject raw) throws IOException {
        SettingsJson.fields(raw, "schema", "transaction_id", "plan_digest", "restart_id",
            "expected_revision", "expected_digest");
        if (!"strata/NativeSettingsRestartRequest/1".equals(SettingsJson.string(raw, "schema"))) {
            throw new IOException("SETTINGS_RESTART_INVALID");
        }
        transaction = GameBatch.id(raw, "transaction_id"); planDigest = GameBatch.digest(raw, "plan_digest");
        id = GameBatch.id(raw, "restart_id");
        long revision = SettingsJson.integer(raw, "expected_revision");
        if (revision < 1) throw new IOException("SETTINGS_RESTART_INVALID");
        expected = new SettingsStore.Snapshot(revision, GameBatch.digest(raw, "expected_digest"));
        value = raw.deepCopy();
    }
    static NativeRepairRestart checkpoint(JsonObject raw) throws IOException {
        SettingsJson.fields(raw, "schema", "request", "source_instance");
        if (!"strata/NativeSettingsRestartCheckpoint/1".equals(SettingsJson.string(raw, "schema"))
                || !raw.get("request").isJsonObject()) throw new IOException("SETTINGS_RESTART_INVALID");
        GameBatch.id(raw, "source_instance");
        return new NativeRepairRestart(raw.getAsJsonObject("request"));
    }
}
