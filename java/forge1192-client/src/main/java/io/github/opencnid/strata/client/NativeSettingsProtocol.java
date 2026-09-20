package io.github.opencnid.strata.client;

import com.google.gson.JsonObject;
import java.io.IOException;
import java.util.Map;
import java.util.Set;
import java.util.TreeMap;

/** Private operator protocol. Caller supplies client-thread dispatch, auth and session fencing. */
final class NativeSettingsProtocol {
    static final String REQUEST_SCHEMA = "strata/NativeSettingsRequest/1";
    static final String RESPONSE_SCHEMA = "strata/NativeSettingsResponse/1";
    private final SettingsStore store;
    private final SettingsStore.RuntimePort runtime;

    NativeSettingsProtocol(SettingsStore store, SettingsStore.RuntimePort runtime) {
        this.store = store;
        this.runtime = runtime;
    }

    static void validate(JsonObject request, String session, long now) throws IOException {
        SettingsJson.fields(request, "schema", "request_id", "session_id", "deadline_unix_ms", "operation", "args");
        if (!REQUEST_SCHEMA.equals(SettingsJson.string(request, "schema"))) throw new IOException("SCHEMA_UNSUPPORTED");
        identifier(SettingsJson.string(request, "request_id"));
        if (!session.equals(SettingsJson.string(request, "session_id"))) throw new IOException("SETTINGS_SESSION_MISMATCH");
        long deadline = SettingsJson.integer(request, "deadline_unix_ms");
        if (deadline <= now || deadline - now > 30000) throw new IOException("SETTINGS_DEADLINE_INVALID");
        String operation = SettingsJson.string(request, "operation");
        if (!Set.of("snapshot", "apply", "status", "rollback", "stop_all").contains(operation)) {
            throw new IOException("SETTINGS_OPERATION_UNSUPPORTED");
        }
        if (!request.get("args").isJsonObject()) throw new IOException("SETTINGS_JSON_TYPE");
        JsonObject args = request.getAsJsonObject("args");
        switch (operation) {
            case "snapshot", "stop_all" -> SettingsJson.fields(args);
            case "status", "rollback" -> {
                SettingsJson.fields(args, "transaction_id");
                identifier(SettingsJson.string(args, "transaction_id"));
            }
            case "apply" -> {
                SettingsJson.fields(args, "transaction_id", "expected_revision", "expected_digest", "changes");
                identifier(SettingsJson.string(args, "transaction_id"));
                if (SettingsJson.integer(args, "expected_revision") < 1
                        || !SettingsJson.string(args, "expected_digest").matches("[0-9a-f]{64}")
                        || !args.get("changes").isJsonObject()) throw new IOException("SETTINGS_PATCH_INVALID");
                changes(args.getAsJsonObject("changes"));
            }
            default -> throw new IOException("SETTINGS_OPERATION_UNSUPPORTED");
        }
    }

    static void identifier(String value) throws IOException {
        if (!value.matches("[A-Za-z0-9_.:-]{1,128}")) throw new IOException("SETTINGS_ID_INVALID");
    }

    private static Map<String, SettingsStore.Change> changes(JsonObject source) throws IOException {
        if (source.size() < 1 || source.size() > 32) throw new IOException("SETTINGS_PATCH_INVALID");
        Map<String, SettingsStore.Change> result = new TreeMap<>();
        for (var entry : source.entrySet()) {
            identifier(entry.getKey());
            if (!entry.getValue().isJsonObject()) throw new IOException("SETTINGS_JSON_TYPE");
            JsonObject change = entry.getValue().getAsJsonObject();
            SettingsJson.fields(change, "before", "after");
            String before = SettingsJson.string(change, "before"), after = SettingsJson.string(change, "after");
            if (before.length() > 256 || after.length() > 256 || before.equals(after)) throw new IOException("SETTINGS_PATCH_INVALID");
            result.put(entry.getKey(), new SettingsStore.Change(before, after));
        }
        return result;
    }

    JsonObject execute(JsonObject request) throws IOException {
        runtime.requireClientThread();
        JsonObject args = request.getAsJsonObject("args");
        return switch (SettingsJson.string(request, "operation")) {
            case "snapshot" -> store.inspect();
            case "apply" -> receipt(store.apply(SettingsJson.string(args, "transaction_id"),
                new SettingsStore.Snapshot(SettingsJson.integer(args, "expected_revision"),
                    SettingsJson.string(args, "expected_digest")), changes(args.getAsJsonObject("changes"))));
            case "status" -> receipt(store.status(SettingsJson.string(args, "transaction_id")));
            case "rollback" -> receipt(store.rollback(SettingsJson.string(args, "transaction_id")));
            case "stop_all" -> { runtime.releaseInputs(); JsonObject value = new JsonObject();
                value.addProperty("native_inputs_released", true); yield value; }
            default -> throw new IOException("SETTINGS_OPERATION_UNSUPPORTED");
        };
    }

    private static JsonObject receipt(SettingsStore.Receipt receipt) {
        JsonObject value = new JsonObject();
        value.addProperty("transaction_id", receipt.id());
        value.addProperty("phase", receipt.phase());
        value.addProperty("revision", receipt.revision());
        value.addProperty("committed", receipt.committed());
        return value;
    }

    static JsonObject response(JsonObject request, String session, String status, JsonObject result, String code) {
        JsonObject value = new JsonObject();
        value.addProperty("schema", RESPONSE_SCHEMA);
        value.addProperty("request_id", request.get("request_id").getAsString());
        value.addProperty("session_id", session);
        value.addProperty("status", status);
        value.add("result", result);
        value.addProperty("error_code", code);
        return value;
    }
}
