package io.github.opencnid.strata.telemetry;

import com.google.gson.JsonObject;
import java.io.IOException;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class PipeTelemetryTest {
    @Test void receiptsRejectCoercionDuplicationAndAmbiguousAcknowledgments() throws Exception {
        String schema = "strata/TelemetryPipeReceipt/1", hash = "a".repeat(64);
        String valid = "{\"schema\":\"" + schema + "\",\"sequence\":1,\"event_sha256\":\"" + hash + "\"}";
        PipeTelemetry.verifyReceipt(valid, schema, 1, hash);
        for (String invalid : new String[] {
            valid.replace("\"sequence\":1", "\"sequence\":\"1\""),
            valid.replace("\"sequence\":1", "\"sequence\":true"),
            valid.replace("\"sequence\":1", "\"sequence\":1.0"),
            valid.replace("\"sequence\":1", "\"sequence\":1,\"sequence\":1"),
            valid.replace("\"sequence\":1", "\"sequence\":2"),
            valid.replace(hash, "b".repeat(64)),
            valid.replace("\"sequence\":1", "\"sequence\":1,\"key\":\"private\"")
        }) assertThrows(IOException.class, () -> PipeTelemetry.verifyReceipt(invalid, schema, 1, hash));
        assertThrows(IOException.class, () -> PipeTelemetry.verifyReceipt(valid,
            "strata/TelemetryPipeClosed/1", 1, null));
    }

    @Test void rejectsMixedCredentialAndUnsafeEndpointDescriptorsBeforeConnecting() throws Exception {
        JsonObject descriptor = new JsonObject();
        descriptor.addProperty("schema", "strata/ForgeTelemetryConfig/4");
        descriptor.addProperty("pipe_name", "\\\\.\\pipe\\strata-telemetry-" + "a".repeat(64));
        descriptor.addProperty("challenge", "b".repeat(64));
        descriptor.addProperty("controller_pid", 1234);
        descriptor.addProperty("controller_started_unix_ms", 1);
        String valid = descriptor.toString();
        for (String invalid : new String[] {
            valid.replace("strata-telemetry-", "unrelated-"),
            valid.replace("\"controller_pid\":1234", "\"controller_pid\":0"),
            valid.replace("\"controller_pid\":1234", "\"controller_pid\":\"1234\""),
            valid.replace("\"controller_pid\":1234", "\"controller_pid\":1234,\"controller_pid\":1234"),
            valid.replace("\"controller_pid\":1234", "\"controller_pid\":1234,\"key_file\":\"private\""),
            valid.replace("strata/ForgeTelemetryConfig/4", "strata/ForgeTelemetryConfig/3")
        }) assertThrows(IOException.class, () -> PipeTelemetry.open(invalid), invalid);
    }
}
