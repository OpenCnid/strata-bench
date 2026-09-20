package io.github.opencnid.strata.client;

import com.google.gson.JsonNull;
import com.google.gson.JsonObject;
import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.UUID;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

/** Actual loopback HTTP, synthetic game port. Does not launch or operate Minecraft. */
class NativeGameProtocolTest {
    static class Port implements NativeGameProtocol.RuntimePort {
        Thread owner = Thread.currentThread(); int reads;
        public String bodyFingerprint() { return "a".repeat(64); }
        public long connectionGeneration() { return 1; }
        public void requireClientThread() throws IOException {
            if (owner != Thread.currentThread()) throw new IOException("CLIENT_THREAD_REQUIRED");
        }
        public JsonObject observe(String cursor) throws IOException {
            requireClientThread(); reads++;
            JsonObject value = new JsonObject(); value.addProperty("x", -1.25); return value;
        }
    }
    JsonObject request(JsonObject connection, String operation) {
        JsonObject value = new JsonObject(), args = new JsonObject();
        value.addProperty("schema", "strata/NativeGameRequest/1");
        value.addProperty("request_id", UUID.randomUUID().toString());
        value.addProperty("session_id", connection.get("session_id").getAsString());
        value.addProperty("deadline_unix_ms", System.currentTimeMillis() + 10000);
        value.addProperty("operation", operation);
        if (operation.equals("observe") || operation.equals("observe_bound")) args.add("cursor", JsonNull.INSTANCE);
        value.add("args", args); return value;
    }
    HttpResponse<String> send(JsonObject c, String method, String path, String body, boolean auth) throws Exception {
        var request = HttpRequest.newBuilder(URI.create("http://127.0.0.1:" + c.get("port").getAsInt() + path))
            .timeout(Duration.ofSeconds(3)).header("Content-Type", "application/json");
        if (auth) request.header("Authorization", "Bearer " + c.get("bearer_token").getAsString());
        return HttpClient.newHttpClient().send(request.method(method, body == null ? HttpRequest.BodyPublishers.noBody()
            : HttpRequest.BodyPublishers.ofString(body)).build(), HttpResponse.BodyHandlers.ofString());
    }
    @Test void readsRunOnClientThreadAndSettingsProtocolCannotCrossToGameBridge() throws Exception {
        Port port = new Port(); NativeGameProtocol protocol = new NativeGameProtocol(port);
        try (var bridge = new SettingsHttpBridge(protocol::execute, protocol)) {
            var c = bridge.descriptor("a".repeat(64));
            assertEquals("strata/NativeGameConnection/1", c.get("schema").getAsString());
            var request = request(c, "observe");
            assertEquals(401, send(c, "POST", "/v1/game", request.toString(), false).statusCode());
            assertEquals(202, send(c, "POST", "/v1/game", request.toString(), true).statusCode());
            assertEquals(0, port.reads); bridge.drain(); assertEquals(1, port.reads);
            var response = send(c, "GET", "/v1/game/" + request.get("request_id").getAsString(), null, true);
            assertEquals(200, response.statusCode());
            assertTrue(response.body().contains("strata/NativeGameResponse/1"));
            assertTrue(response.body().contains("-1.25"));
            assertEquals(200, send(c, "POST", "/v1/game", request.toString(), true).statusCode());
            bridge.drain(); assertEquals(1, port.reads);
            request = request(c, "observe"); request.addProperty("schema", NativeSettingsProtocol.REQUEST_SCHEMA);
            assertTrue(send(c, "POST", "/v1/game", request.toString(), true).body().contains("SCHEMA_UNSUPPORTED"));
            assertEquals(404, send(c, "POST", "/v1/settings", "{}", true).statusCode());
        }
    }
    @Test void capabilitiesRejectActionsRawStateAndOldSessions() throws Exception {
        Port port = new Port(); NativeGameProtocol protocol = new NativeGameProtocol(port);
        try (var bridge = new SettingsHttpBridge(protocol::execute, protocol)) {
            var c = bridge.descriptor("a".repeat(64));
            for (String operation : new String[]{"act", "eval", "raw_packet", "admin", "connect", "settings"}) {
                assertTrue(send(c, "POST", "/v1/game", request(c, operation).toString(), true).body().contains("CAPABILITY_MISSING"));
            }
            JsonObject request = request(c, "observe"); request.getAsJsonObject("args").addProperty("chunk", "hidden");
            assertEquals(400, send(c, "POST", "/v1/game", request.toString(), true).statusCode());
            request = request(c, "observe"); request.addProperty("session_id", "previous");
            assertTrue(send(c, "POST", "/v1/game", request.toString(), true).body().contains("GAME_SESSION_MISMATCH"));
            assertEquals(0, port.reads);
            var capabilities = NativeGameProtocol.capabilities();
            assertFalse(capabilities.get("campaign_admission").getAsBoolean());
            assertTrue(capabilities.getAsJsonArray("actions").isEmpty());
            assertFalse(capabilities.get("keybindings").getAsBoolean());
        }
    }
    @Test void boundObservationCapturesIdentityOnTheSameClientThread() throws Exception {
        Port port = new Port(); NativeGameProtocol protocol = new NativeGameProtocol(port);
        JsonObject connection = new JsonObject(); connection.addProperty("session_id", "session");
        JsonObject request = request(connection, "observe_bound");
        protocol.validate(request, "session", System.currentTimeMillis());
        var value = protocol.execute(request);
        assertEquals("strata/NativeBoundSnapshot/1", value.get("schema").getAsString());
        assertEquals("a".repeat(64), value.get("body_fingerprint").getAsString());
        assertEquals(1, value.get("connection_generation").getAsLong());
        assertEquals(-1.25, value.getAsJsonObject("snapshot").get("x").getAsDouble());
        assertEquals(1, port.reads);
        request.getAsJsonObject("args").addProperty("body_fingerprint", "guessed");
        assertThrows(IOException.class, () -> protocol.validate(request, "session", System.currentTimeMillis()));
    }
}
