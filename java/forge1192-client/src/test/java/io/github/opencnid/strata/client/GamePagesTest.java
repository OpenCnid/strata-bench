package io.github.opencnid.strata.client;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import java.io.IOException;
import java.util.concurrent.atomic.AtomicLong;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class GamePagesTest {
    @Test void plannerClockUsesTheSameOriginAndRejectsPreOriginRollback() throws Exception {
        var clock = new AtomicLong(9000);
        var pages = new GamePages(clock::get); assertEquals(0, pages.elapsed());
        clock.set(9050); assertEquals(50, pages.elapsed());
        pages.reset(); assertEquals(50, pages.elapsed());
        clock.set(8999); assertThrows(IOException.class, pages::elapsed);
    }
    @Test void privateSceneAssociationSharesPagesAndRejectsExpiredOrResetAuthority() throws Exception {
        var now = new AtomicLong(1000); var pages = new GamePages(now::get);
        var first = pages.capture(state("overworld"), blocks(129), new JsonArray());
        String id = first.get("snapshot_id").getAsString();
        String next = first.getAsJsonObject("state").get("next_cursor").getAsString();
        assertEquals(id, pages.sceneId(id, "overworld")); assertEquals(id, pages.sceneId(next, "overworld"));
        assertThrows(IOException.class, () -> pages.sceneId(next, "nether"));
        now.addAndGet(30000); assertThrows(IOException.class, () -> pages.sceneId(next, "overworld"));
        var fresh = pages.capture(state("overworld"), blocks(1), new JsonArray()); pages.reset();
        assertThrows(IOException.class, () -> pages.sceneId(fresh.get("snapshot_id").getAsString(), "overworld"));
    }
    @Test void privateSelectedSlotFenceBindsAllPagesAndRevisionsWithoutExport() throws Exception {
        var now = new AtomicLong(1000); var pages = new GamePages(now::get);
        var first = pages.capture(state("minecraft:overworld"), blocks(129), new JsonArray(), 1000, "selected-slot:0");
        String id = first.get("snapshot_id").getAsString(), next = first.getAsJsonObject("state").get("next_cursor").getAsString();
        for (String cursor : new String[]{id, next}) {
            pages.requireInputFence(cursor, "minecraft:overworld", "selected-slot:0");
            assertThrows(IOException.class, () -> pages.requireInputFence(cursor, "minecraft:overworld", "selected-slot:1"));
            assertFalse(pages.page(cursor, "minecraft:overworld").toString().contains("selected-slot"));
        }
        var changed = pages.capture(state("minecraft:overworld"), blocks(129), new JsonArray(), 1000, "selected-slot:1");
        assertTrue(changed.get("state_revision").getAsLong() > first.get("state_revision").getAsLong());
        now.addAndGet(30000);
        assertThrows(IOException.class, () -> pages.requireInputFence(id, "minecraft:overworld", "selected-slot:0"));
    }
    @Test void timestampsFitThePublicMicrosecondLimit() {
        assertEquals("2026-09-18T12:00:00.123Z", GamePages.utc(java.time.Instant.parse("2026-09-18T12:00:00.123456789Z")));
    }
    @Test void readingDoesNotIncrementRevisionButVisibleChangesDo() throws Exception {
        AtomicLong now = new AtomicLong(1000); GamePages pages = new GamePages(now::get);
        JsonObject state = state("minecraft:overworld"); state.addProperty("health", 20);
        JsonArray blocks = blocks(1); blocks.get(0).getAsJsonObject().addProperty("observed_at", "first");
        var first = pages.capture(state, blocks, new JsonArray());
        now.addAndGet(50); blocks.get(0).getAsJsonObject().addProperty("observed_at", "second");
        state.addProperty("active_request_id", "current-action");
        var same = pages.capture(state, blocks, new JsonArray());
        assertEquals(first.get("state_revision"), same.get("state_revision"));
        assertNotEquals(first.get("snapshot_id"), same.get("snapshot_id"));
        state.addProperty("health", 19);
        assertTrue(pages.capture(state, blocks, new JsonArray()).get("state_revision").getAsLong() > first.get("state_revision").getAsLong());
    }
    JsonObject state(String dimension) {
        JsonObject result = new JsonObject(); result.addProperty("dimension", dimension); return result;
    }
    JsonArray blocks(int n) {
        JsonArray values = new JsonArray();
        for (int i = 0; i < n; i++) { JsonObject cell = new JsonObject(); cell.addProperty("id", i); values.add(cell); }
        return values;
    }
    @Test void paginationOwnsBytesAndPreservesCaptureAgeAndRevision() throws Exception {
        AtomicLong now = new AtomicLong(1000);
        GamePages pages = new GamePages(now::get);
        long start = pages.beginCapture(); now.addAndGet(50);
        JsonArray blocks = blocks(257);
        JsonObject first = pages.capture(state("minecraft:overworld"), blocks, new JsonArray(), start);
        assertEquals(50, first.get("age_ms").getAsInt());
        assertEquals(0, first.get("captured_elapsed_ms").getAsInt());
        var firstState = first.getAsJsonObject("state");
        assertEquals(128, firstState.getAsJsonArray("nearby_blocks").size());
        blocks.get(128).getAsJsonObject().addProperty("id", -100);
        now.addAndGet(30);
        var second = pages.page(firstState.get("next_cursor").getAsString(), "minecraft:overworld");
        assertEquals(128, second.getAsJsonObject("state").getAsJsonArray("nearby_blocks").get(0).getAsJsonObject().get("id").getAsInt());
        assertEquals(first.get("state_revision"), second.get("state_revision"));
        assertEquals(80, second.get("age_ms").getAsInt());
        var last = pages.page(second.getAsJsonObject("state").get("next_cursor").getAsString(), "minecraft:overworld");
        assertFalse(last.getAsJsonObject("state").get("truncated").getAsBoolean());
        assertTrue(last.getAsJsonObject("state").get("next_cursor").isJsonNull());
        second.getAsJsonObject("state").getAsJsonArray("nearby_blocks").remove(0);
        assertEquals(128, pages.page(firstState.get("next_cursor").getAsString(), "minecraft:overworld").getAsJsonObject("state").getAsJsonArray("nearby_blocks").size());
    }
    @Test void guessedWrongDimensionExpiredEvictedAndResetPagesReject() throws Exception {
        AtomicLong now = new AtomicLong(1000); GamePages pages = new GamePages(now::get);
        var first = pages.capture(state("minecraft:overworld"), blocks(129), new JsonArray());
        String cursor = first.getAsJsonObject("state").get("next_cursor").getAsString();
        assertThrows(IOException.class, () -> pages.page("guess", "minecraft:overworld"));
        assertThrows(IOException.class, () -> pages.page(cursor, "minecraft:the_nether"));
        now.addAndGet(30000);
        assertThrows(IOException.class, () -> pages.page(cursor, "minecraft:overworld"));
        first = pages.capture(state("minecraft:overworld"), blocks(129), new JsonArray());
        String evicted = first.getAsJsonObject("state").get("next_cursor").getAsString();
        for (int i = 0; i < 4; i++) pages.capture(state("minecraft:overworld"), blocks(129), new JsonArray());
        assertThrows(IOException.class, () -> pages.page(evicted, "minecraft:overworld"));
        String reset = pages.capture(state("minecraft:overworld"), blocks(129), new JsonArray()).getAsJsonObject("state").get("next_cursor").getAsString();
        pages.reset(); assertThrows(IOException.class, () -> pages.page(reset, "minecraft:overworld"));
    }
    @Test void oversizedScenesAndInvalidClocksReject() {
        AtomicLong now = new AtomicLong(1000); GamePages pages = new GamePages(now::get);
        assertThrows(IOException.class, () -> pages.capture(state("minecraft:overworld"), blocks(16385), new JsonArray()));
        assertThrows(IOException.class, () -> pages.capture(state("minecraft:overworld"), new JsonArray(), new JsonArray(), 2000));
    }
}
