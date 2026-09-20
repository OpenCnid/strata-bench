package io.github.opencnid.strata.telemetry;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import static org.junit.jupiter.api.Assertions.*;

class EventSpoolTest {
    @TempDir Path root;

    @Test void orderedDurableRecordsAndIndependentBoots() throws Exception {
        TelemetryConfig config = new TelemetryConfig("fixture", 3, root, 1048576, 100, List.of(), List.of());
        String first;
        try (EventSpool spool = new EventSpool(config)) {
            first = spool.bootId();
            for (int i = 0; i < 20; i++) {
                JsonObject value = new JsonObject();
                value.addProperty("marker", "synthetic");
                spool.publish(i, "fixture", "strata/Test/1", value, new JsonArray());
            }
        }
        List<String> lines = Files.readAllLines(root.resolve(first + ".jsonl"));
        assertEquals(20, lines.size());
        for (int i = 0; i < lines.size(); i++) {
            JsonObject value = JsonParser.parseString(lines.get(i)).getAsJsonObject();
            assertEquals(i + 1, value.get("seq").getAsInt());
            assertEquals(i + 1, value.get("server_event_seq").getAsInt());
            assertEquals(i, value.get("server_tick").getAsInt());
            assertEquals("evaluator", value.get("visibility").getAsString());
        }
        try (EventSpool second = new EventSpool(config)) { assertNotEquals(first, second.bootId()); }
        assertEquals(2, Files.list(root).count());
    }

    @Test void quotaFailureIsStickyAndDoesNotInventDurableAcknowledgments() throws Exception {
        TelemetryConfig config = new TelemetryConfig("fixture", 1, root, 65536, 1, List.of(), List.of());
        EventSpool spool = new EventSpool(config);
        spool.publish(1, "fixture", "strata/Test/1", new JsonObject(), new JsonArray());
        IOException error = assertThrows(IOException.class, () ->
            spool.publish(2, "fixture", "strata/Test/1", new JsonObject(), new JsonArray()));
        assertEquals("TELEMETRY_QUOTA_EXHAUSTED", error.getMessage());
        assertThrows(IOException.class, spool::healthy);
        assertThrows(IOException.class, spool::close);
        assertEquals(1, spool.durableSeq());
        assertEquals(1, Files.readAllLines(root.resolve(spool.bootId() + ".jsonl")).size());
    }

    @Test void oversizedEventAndClosedWriterRejectNewData() throws Exception {
        TelemetryConfig config = new TelemetryConfig("fixture", 1, root, 65536, 10, List.of(), List.of());
        EventSpool spool = new EventSpool(config);
        JsonObject data = new JsonObject();
        data.addProperty("large", "x".repeat(65536));
        assertThrows(IOException.class, () -> spool.publish(1, "fixture", "strata/Test/1", data, new JsonArray()));
        assertThrows(IOException.class, spool::close);
        assertEquals(0, spool.durableSeq());
        EventSpool clean = new EventSpool(config);
        clean.close();
        assertThrows(IOException.class, () -> clean.publish(1, "fixture", "strata/Test/1", new JsonObject(), new JsonArray()));
    }
}
