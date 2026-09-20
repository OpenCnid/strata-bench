package io.github.opencnid.strata.client;

import com.google.gson.JsonObject;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.util.UUID;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import static org.junit.jupiter.api.Assertions.*;

/** Real loopback transport and files; synthetic runtime, no Minecraft/inference. */
class SettingsHttpBridgeTest {
    final HttpClient http = HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(2)).build();

    JsonObject request(JsonObject connection, String operation, JsonObject args) {
        JsonObject value = new JsonObject();
        value.addProperty("schema", NativeSettingsProtocol.REQUEST_SCHEMA);
        value.addProperty("request_id", UUID.randomUUID().toString());
        value.addProperty("session_id", connection.get("session_id").getAsString());
        value.addProperty("deadline_unix_ms", System.currentTimeMillis() + 10000);
        value.addProperty("operation", operation);
        value.add("args", args);
        return value;
    }

    HttpResponse<String> send(JsonObject connection, String method, String suffix, String body, boolean auth) throws Exception {
        var builder = HttpRequest.newBuilder(URI.create("http://127.0.0.1:" + connection.get("port").getAsInt() + "/v1/settings" + suffix))
            .timeout(Duration.ofSeconds(3)).header("Content-Type", "application/json");
        if (auth) builder.header("Authorization", "Bearer " + connection.get("bearer_token").getAsString());
        return http.send(builder.method(method, body == null ? HttpRequest.BodyPublishers.noBody()
            : HttpRequest.BodyPublishers.ofString(body)).build(), HttpResponse.BodyHandlers.ofString());
    }

    JsonObject roundTrip(SettingsHttpBridge bridge, JsonObject connection, JsonObject request) throws Exception {
        assertEquals(202, send(connection, "POST", "", request.toString(), true).statusCode());
        bridge.drain();
        var response = send(connection, "GET", "/" + request.get("request_id").getAsString(), null, true);
        assertEquals(200, response.statusCode());
        return SettingsJson.read(response.body());
    }

    JsonObject patch(SettingsStore.Snapshot snapshot) {
        JsonObject args = new JsonObject(), changes = new JsonObject(), change = new JsonObject();
        args.addProperty("transaction_id", "transaction-1");
        args.addProperty("expected_revision", snapshot.revision());
        args.addProperty("expected_digest", snapshot.digest());
        change.addProperty("before", SettingsStoreTest.BEFORE);
        change.addProperty("after", SettingsStoreTest.AFTER);
        changes.add(SettingsStoreTest.ID, change);
        args.add("changes", changes);
        return args;
    }

    @Test void queuedMutationsUseClientThreadDurableTransactionIdsAndRollback(@TempDir Path root) throws Exception {
        var fixture = new SettingsStoreTest().fixture(root);
        try (var store = fixture.open(); var bridge = new SettingsHttpBridge(new NativeSettingsProtocol(store, fixture.runtime())::execute)) {
            JsonObject connection = bridge.descriptor(SettingsStoreTest.FINGERPRINT);
            JsonObject apply = request(connection, "apply", patch(store.snapshot()));
            var accepted = send(connection, "POST", "", apply.toString(), true);
            assertEquals(202, accepted.statusCode());
            assertEquals(0, fixture.runtime().writes);
            bridge.drain();
            var repeated = send(connection, "POST", "", apply.toString(), true);
            assertEquals(200, repeated.statusCode());
            assertEquals("applied_pending_verification", SettingsJson.read(repeated.body()).getAsJsonObject("result").get("phase").getAsString());
            assertEquals(1, fixture.runtime().writes);
            JsonObject reordered = new JsonObject();
            apply.entrySet().stream().sorted((a, b) -> b.getKey().compareTo(a.getKey()))
                .forEach(entry -> reordered.add(entry.getKey(), entry.getValue().deepCopy()));
            assertEquals(200, send(connection, "POST", "", reordered.toString(), true).statusCode());
            JsonObject changed = apply.deepCopy();
            changed.addProperty("operation", "snapshot"); changed.add("args", new JsonObject());
            assertTrue(send(connection, "POST", "", changed.toString(), true).body().contains("SETTINGS_IDEMPOTENCY_CONFLICT"));
            JsonObject otherRequestSameTransaction = request(connection, "apply", apply.getAsJsonObject("args"));
            assertEquals("completed", roundTrip(bridge, connection, otherRequestSameTransaction).get("status").getAsString());
            assertEquals(1, fixture.runtime().writes);
            long journalSize = Files.size(fixture.journal().resolve("settings-journal.jsonl"));
            JsonObject snapshot = roundTrip(bridge, connection, request(connection, "snapshot", new JsonObject())).getAsJsonObject("result");
            assertEquals("transaction-1", snapshot.get("active_transaction").getAsString());
            assertFalse(snapshot.get("supported").getAsBoolean());
            assertEquals(journalSize, Files.size(fixture.journal().resolve("settings-journal.jsonl")));
            JsonObject id = new JsonObject(); id.addProperty("transaction_id", "transaction-1");
            assertEquals("rolled_back", roundTrip(bridge, connection, request(connection, "rollback", id))
                .getAsJsonObject("result").get("phase").getAsString());
            assertEquals(SettingsStoreTest.ORIGINAL, fixture.text());
        }
    }

    @Test void authenticationSessionSchemaAndBodyBoundsRejectBeforeDispatch(@TempDir Path root) throws Exception {
        var fixture = new SettingsStoreTest().fixture(root);
        try (var store = fixture.open(); var bridge = new SettingsHttpBridge(new NativeSettingsProtocol(store, fixture.runtime())::execute)) {
            JsonObject connection = bridge.descriptor(SettingsStoreTest.FINGERPRINT);
            JsonObject request = request(connection, "snapshot", new JsonObject());
            assertEquals(401, send(connection, "POST", "", request.toString(), false).statusCode());
            request.addProperty("session_id", "old-session");
            assertTrue(send(connection, "POST", "", request.toString(), true).body().contains("SETTINGS_SESSION_MISMATCH"));
            request = request(connection, "snapshot", new JsonObject());
            request.addProperty("unrecognized", true);
            assertEquals(400, send(connection, "POST", "", request.toString(), true).statusCode());
            assertEquals(413, send(connection, "POST", "", "x".repeat(SettingsHttpBridge.MAX_REQUEST + 1), true).statusCode());
            assertEquals(400, send(connection, "POST", "", "{\"schema\":1,\"schema\":2}", true).statusCode());
            assertEquals(405, send(connection, "POST", "/wrong", "{}", true).statusCode());
            assertEquals(404, send(connection, "GET", "/not-known", null, true).statusCode());
            bridge.drain();
            assertEquals(0, fixture.runtime().writes);
        }
    }

    @Test void expirationQueueBoundsAndChangedRequestIdsDoNotDispatch(@TempDir Path root) throws Exception {
        var fixture = new SettingsStoreTest().fixture(root);
        try (var store = fixture.open(); var bridge = new SettingsHttpBridge(new NativeSettingsProtocol(store, fixture.runtime())::execute)) {
            JsonObject connection = bridge.descriptor(SettingsStoreTest.FINGERPRINT);
            JsonObject expired = request(connection, "apply", patch(store.snapshot()));
            expired.addProperty("deadline_unix_ms", System.currentTimeMillis() + 300);
            assertEquals(202, send(connection, "POST", "", expired.toString(), true).statusCode());
            Thread.sleep(350);
            bridge.drain();
            assertTrue(send(connection, "GET", "/" + expired.get("request_id").getAsString(), null, true).body().contains("SETTINGS_DEADLINE_EXPIRED"));
            assertEquals(0, fixture.runtime().writes);
            for (int i = 0; i < 8; i++) {
                assertEquals(202, send(connection, "POST", "", request(connection, "snapshot", new JsonObject()).toString(), true).statusCode());
            }
            JsonObject overflow = request(connection, "snapshot", new JsonObject());
            assertTrue(send(connection, "POST", "", overflow.toString(), true).body().contains("SETTINGS_QUEUE_FULL"));
        }
    }

    @Test void protocolNeverOffersCommitAndDoesNotLeakExceptions() throws Exception {
        try (var bridge = new SettingsHttpBridge(request -> { throw new IllegalStateException("private/path/credential"); })) {
            JsonObject connection = bridge.descriptor(SettingsStoreTest.FINGERPRINT);
            JsonObject commit = request(connection, "commit", new JsonObject());
            assertTrue(send(connection, "POST", "", commit.toString(), true).body().contains("SETTINGS_OPERATION_UNSUPPORTED"));
            JsonObject response = roundTrip(bridge, connection, request(connection, "snapshot", new JsonObject()));
            assertEquals("SETTINGS_EXECUTION_FAILED", response.get("error_code").getAsString());
            assertFalse(response.toString().contains("private"));
        }
    }

    @Test void browserOriginAndShutdownCannotDispatchQueuedMutation(@TempDir Path root) throws Exception {
        var fixture = new SettingsStoreTest().fixture(root);
        try (var store = fixture.open(); var bridge = new SettingsHttpBridge(new NativeSettingsProtocol(store, fixture.runtime())::execute)) {
            JsonObject connection = bridge.descriptor(SettingsStoreTest.FINGERPRINT);
            JsonObject request = request(connection, "apply", patch(store.snapshot()));
            var forbidden = HttpRequest.newBuilder(URI.create("http://127.0.0.1:" + connection.get("port").getAsInt() + "/v1/settings"))
                .header("Origin", "https://example.invalid")
                .header("Authorization", "Bearer " + connection.get("bearer_token").getAsString())
                .header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(request.toString())).build();
            assertEquals(403, http.send(forbidden, HttpResponse.BodyHandlers.ofString()).statusCode());
            assertEquals(202, send(connection, "POST", "", request.toString(), true).statusCode());
            bridge.close();
            bridge.drain();
            assertEquals(0, fixture.runtime().writes);
            assertEquals(SettingsStoreTest.ORIGINAL, fixture.text());
        }
    }
}
