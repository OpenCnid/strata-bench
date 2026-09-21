package io.github.opencnid.strata.telemetry;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.Base64;
import java.util.HexFormat;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import static org.junit.jupiter.api.Assertions.*;

class SpoolAuthenticationTest {
    @TempDir Path root;

    private SpoolAuthentication authentication() throws Exception {
        byte[] key = new byte[32];
        for (int i=0; i<32; i++) key[i]=(byte)i;
        Path file = root.resolve("producer.key"); Files.write(file, key);
        return new SpoolAuthentication("a".repeat(64), file,
            HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(key)), "b".repeat(64));
    }

    @Test void knownWireAnswerAndOneUseBootGrant() throws Exception {
        SpoolAuthentication auth = authentication();
        var signer = auth.signer("fixture");
        byte[] event = "{\"synthetic\":true}\n".getBytes(StandardCharsets.UTF_8);
        JsonObject wire = JsonParser.parseString(new String(signer.wrap(event, 1), StandardCharsets.UTF_8)).getAsJsonObject();
        assertEquals("0e3924b837f58e1fc289fedfb54d5f8eb19987ea510a89f75ab2a403c7545666", wire.get("mac").getAsString());
        assertArrayEquals(event, Base64.getDecoder().decode(wire.get("event_base64").getAsString()));
        assertThrows(IOException.class, () -> signer.wrap(event, 1));
        JsonObject second = JsonParser.parseString(new String(signer.wrap(event, 2), StandardCharsets.UTF_8)).getAsJsonObject();
        assertEquals(wire.get("mac"), second.get("previous_mac"));
        assertThrows(IOException.class, () -> auth.signer("second-boot"));
        String claim = Files.readString(root.resolve("producer.key.claimed"));
        assertTrue(claim.contains("fixture"));
        assertFalse(claim.contains(Base64.getEncoder().encodeToString(Files.readAllBytes(auth.keyFile()))));
    }

    @Test void changedOrMalformedKeyCannotClaim() throws Exception {
        SpoolAuthentication auth = authentication();
        Files.write(auth.keyFile(), new byte[32]);
        assertThrows(IOException.class, () -> auth.signer("fixture"));
        assertFalse(Files.exists(root.resolve("producer.key.claimed")));
        Files.write(auth.keyFile(), new byte[33]);
        assertThrows(IOException.class, () -> auth.signer("fixture"));
    }

    @Test void actualWriterEmitsOnlySignedFramesAndPreservesDurableCursor() throws Exception {
        SpoolAuthentication auth = authentication();
        Path output = Files.createDirectory(root.resolve("spool"));
        TelemetryConfig config = new TelemetryConfig("fixture", 1, output, 65536, 20, List.of(), List.of(), auth);
        String boot;
        try (EventSpool spool = new EventSpool(config)) {
            boot = spool.bootId();
            for (int i=0; i<10; i++) spool.publish(i, "fixture", "strata/Test/1", new JsonObject(), new JsonArray());
        }
        List<String> records = Files.readAllLines(output.resolve(boot + ".authenticated.jsonl"));
        assertEquals(10, records.size());
        for (int i=0; i<records.size(); i++) {
            JsonObject outer = JsonParser.parseString(records.get(i)).getAsJsonObject();
            assertEquals(i+1, outer.get("sequence").getAsInt());
            JsonObject event = JsonParser.parseString(new String(Base64.getDecoder().decode(
                outer.get("event_base64").getAsString()), StandardCharsets.UTF_8)).getAsJsonObject();
            assertEquals(i+1, event.get("server_event_seq").getAsInt());
            assertEquals(boot, event.get("server_boot_id").getAsString());
        }
        assertFalse(Files.exists(output.resolve(boot + ".jsonl")));
        assertThrows(IOException.class, () -> new EventSpool(config));
    }

    @Test void encodedBytesCountAgainstTheExistingQuota() throws Exception {
        SpoolAuthentication auth = authentication();
        Path output = Files.createDirectory(root.resolve("spool"));
        EventSpool spool = new EventSpool(new TelemetryConfig("fixture", 1, output,
            65536, 20, List.of(), List.of(), auth));
        JsonObject payload = new JsonObject(); payload.addProperty("large", "x".repeat(52000));
        IOException error = assertThrows(IOException.class, () -> spool.publish(1, "fixture", "strata/Test/1", payload, new JsonArray()));
        assertEquals("TELEMETRY_QUOTA_EXHAUSTED", error.getMessage());
        assertThrows(IOException.class, spool::close);
        assertEquals(0, spool.durableSeq());
        assertEquals(0, Files.size(output.resolve(spool.bootId() + ".authenticated.jsonl")));
    }
}
