package io.github.opencnid.strata.client;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import java.io.IOException;
import java.util.LinkedHashMap;
import java.util.Map;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

/** Synthetic immutable states; these tests establish delivery authority, not Minecraft collisions. */
class GameObservedMapTest {
    GameObservedMap.Position pos(int x) { return new GameObservedMap.Position(x, 64, -2); }
    Map<GameObservedMap.Position, GameObservedMap.Cell<String>> cells(int start, int count, String value) {
        var result = new LinkedHashMap<GameObservedMap.Position, GameObservedMap.Cell<String>>();
        for (int i = start; i < start + count; i++) result.put(pos(i), new GameObservedMap.Cell<>("minecraft:stone", value));
        return result;
    }
    JsonObject page(String dimension, long captured, long revision, int start, int count) {
        var snapshot = new JsonObject(); var state = new JsonObject(); var blocks = new JsonArray();
        snapshot.addProperty("captured_elapsed_ms", captured); snapshot.addProperty("state_revision", revision);
        state.addProperty("dimension", dimension); state.add("nearby_blocks", blocks); snapshot.add("state", state);
        for (int i = start; i < start + count; i++) {
            var position = new JsonObject(); position.addProperty("x", i); position.addProperty("y", 64); position.addProperty("z", -2);
            var block = new JsonObject(); block.add("position", position); block.addProperty("block_id", "minecraft:stone"); blocks.add(block);
        }
        return snapshot;
    }
    @Test void captureAndUndeliveredPagesCannotPopulatePlannerMap() throws Exception {
        var map = new GameObservedMap<String>();
        var original = cells(0, 256, "original"); map.remember("scene", "overworld", 10, 1, original);
        original.put(pos(0), new GameObservedMap.Cell<>("minecraft:stone", "foreign"));
        assertTrue(map.snapshot().isEmpty());
        map.deliver("scene", page("overworld", 10, 1, 0, 128));
        assertEquals(128, map.snapshot().size()); assertEquals("original", map.at(pos(0)).cell().state());
        assertNull(map.at(pos(128))); assertNull(map.at(pos(999)));
        map.deliver("scene", page("overworld", 10, 1, 128, 128));
        assertEquals(256, map.snapshot().size());
        assertThrows(UnsupportedOperationException.class, () -> map.snapshot().clear());
    }
    @Test void malformedOrInventedCellMakesEntirePageFailWithoutPartialPromotion() throws Exception {
        var map = new GameObservedMap<String>(); map.remember("scene", "overworld", 10, 1, cells(0, 3, "state"));
        for (String fault : new String[]{"id", "position", "duplicate", "fraction"}) {
            var page = page("overworld", 10, 1, 0, 2); var blocks = page.getAsJsonObject("state").getAsJsonArray("nearby_blocks");
            var bad = blocks.get(1).getAsJsonObject();
            switch (fault) {
                case "id" -> bad.addProperty("block_id", "minecraft:air");
                case "position" -> bad.getAsJsonObject("position").addProperty("x", 999);
                case "duplicate" -> blocks.set(1, blocks.get(0).deepCopy());
                case "fraction" -> bad.getAsJsonObject("position").addProperty("x", 1.5);
            }
            assertThrows(IOException.class, () -> map.deliver("scene", page));
            assertTrue(map.snapshot().isEmpty());
        }
    }
    @Test void oldPageCannotOverwriteNewerDeliveredState() throws Exception {
        var map = new GameObservedMap<String>();
        map.remember("old", "overworld", 10, 1, cells(0, 1, "old"));
        map.remember("new", "overworld", 20, 2, cells(0, 1, "new"));
        map.deliver("new", page("overworld", 20, 2, 0, 1));
        map.deliver("old", page("overworld", 10, 1, 0, 1));
        assertEquals("new", map.at(pos(0)).cell().state()); assertEquals(20, map.at(pos(0)).captured());
    }
    @Test void sameClockUsesRevisionAndAmbiguousEqualVersionRejects() throws Exception {
        var map = new GameObservedMap<String>();
        map.remember("old", "overworld", 10, 1, cells(0, 1, "old"));
        map.remember("new", "overworld", 10, 2, cells(0, 1, "new"));
        map.remember("conflict", "overworld", 10, 2, cells(0, 1, "different-private-state"));
        map.deliver("new", page("overworld", 10, 2, 0, 1));
        map.deliver("old", page("overworld", 10, 1, 0, 1));
        assertThrows(IOException.class, () -> map.deliver("conflict", page("overworld", 10, 2, 0, 1)));
        assertEquals("new", map.at(pos(0)).cell().state());
    }
    @Test void dimensionAndAuthorityResetDiscardCapturedAndDeliveredStates() throws Exception {
        var map = new GameObservedMap<String>();
        map.remember("old", "overworld", 10, 1, cells(0, 1, "old")); map.deliver("old", page("overworld", 10, 1, 0, 1));
        map.remember("new", "nether", 20, 2, cells(0, 1, "new")); assertTrue(map.snapshot().isEmpty());
        assertThrows(IOException.class, () -> map.deliver("old", page("overworld", 10, 1, 0, 1)));
        assertThrows(IOException.class, () -> map.deliver("new", page("overworld", 20, 2, 0, 1)));
        map.deliver("new", page("nether", 20, 2, 0, 1)); map.reset();
        assertTrue(map.snapshot().isEmpty()); assertThrows(IOException.class, () -> map.deliver("new", page("nether", 20, 2, 0, 1)));
    }
    @Test void boundedSceneCacheAndSnapshotIdentityPreventWrongCaptureDelivery() throws Exception {
        var map = new GameObservedMap<String>();
        for (int i = 0; i < 5; i++) map.remember("scene" + i, "overworld", i, i, cells(0, 1, "value"));
        assertThrows(IOException.class, () -> map.deliver("scene0", page("overworld", 0, 0, 0, 1)));
        assertThrows(IOException.class, () -> map.deliver("scene4", page("overworld", 3, 4, 0, 1)));
        assertThrows(IOException.class, () -> map.deliver("scene4", page("overworld", 4, 3, 0, 1)));
        assertThrows(IOException.class, () -> map.remember("scene4", "overworld", 4, 4, cells(0, 1, "value")));
        assertTrue(map.snapshot().isEmpty());
    }
    @Test void deliveryCeilingEvictsOldestAndRepeatDoesNotRefreshItsAge() throws Exception {
        var map = new GameObservedMap<String>(); map.remember("scene", "overworld", 10, 1, cells(0, 1152, "state"));
        for (int i = 0; i < 8; i++) map.deliver("scene", page("overworld", 10, 1, i * 128, 128));
        map.deliver("scene", page("overworld", 10, 1, 0, 1));
        map.deliver("scene", page("overworld", 10, 1, 1024, 128));
        assertEquals(1024, map.snapshot().size()); assertNull(map.at(pos(0))); assertNull(map.at(pos(127)));
        assertNotNull(map.at(pos(128))); assertNotNull(map.at(pos(1151)));
    }
    @Test void oversizedSceneAndPageReject() throws Exception {
        var map = new GameObservedMap<String>();
        assertThrows(IOException.class, () -> map.remember("scene", "overworld", 0, 0, cells(0, 16385, "state")));
        map.remember("scene", "overworld", 10, 1, cells(0, 129, "state"));
        assertThrows(IOException.class, () -> map.deliver("scene", page("overworld", 10, 1, 0, 129)));
        assertTrue(map.snapshot().isEmpty());
    }
}
