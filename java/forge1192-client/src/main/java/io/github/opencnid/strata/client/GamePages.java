package io.github.opencnid.strata.client;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import java.io.IOException;
import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.ArrayDeque;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;
import java.util.function.LongSupplier;

/** Bounded immutable scene pages. A cursor never queries new spatial coordinates. */
final class GamePages {
    private record Scene(JsonObject state, JsonArray blocks, JsonArray entities, long captured,
                         long revision, String[] ids, String inputFence) {}
    private record Page(Scene scene, int index) {}
    private final LongSupplier clock;
    private final String clockId = UUID.randomUUID().toString();
    private final long origin;
    private final ArrayDeque<Scene> scenes = new ArrayDeque<>();
    private final Map<String, Page> pages = new HashMap<>();
    private long revision;
    private String lastStateDigest;

    GamePages() { this(() -> System.nanoTime() / 1000000); }
    GamePages(LongSupplier clock) { this.clock = clock; origin = clock.getAsLong(); }
    // Public Utc admits at most six fractional digits. Java Instant may carry nine.
    static String utc(Instant instant) { return instant.truncatedTo(ChronoUnit.MILLIS).toString(); }
    void reset() { scenes.clear(); pages.clear(); lastStateDigest = null; }
    long beginCapture() { return clock.getAsLong(); }
    long elapsed() throws IOException {
        long elapsed = clock.getAsLong() - origin;
        if (elapsed < 0) throw new IOException("GAME_CLOCK_INVALID");
        return elapsed;
    }

    JsonObject capture(JsonObject state, JsonArray blocks, JsonArray entities) throws IOException {
        return capture(state, blocks, entities, beginCapture());
    }
    JsonObject capture(JsonObject state, JsonArray blocks, JsonArray entities, long captured) throws IOException {
        return capture(state, blocks, entities, captured, "");
    }
    JsonObject capture(JsonObject state, JsonArray blocks, JsonArray entities, long captured, String inputFence) throws IOException {
        prune();
        if (captured < origin || captured > clock.getAsLong()) throw new IOException("GAME_CLOCK_INVALID");
        if (blocks.size() > GameVisibility.MAX_CELLS || entities.size() > 16384) throw new IOException("GAME_SCENE_CAPACITY");
        JsonObject comparable = new JsonObject(), core = state.deepCopy();
        core.remove("active_request_id"); // The accepted action's own bookkeeping is not a game-state change.
        comparable.add("state", core);
        comparable.addProperty("input_fence", inputFence);
        comparable.add("blocks", withoutObservationTimes(blocks)); comparable.add("entities", withoutObservationTimes(entities));
        String digest = KeyOptions.sha256(comparable.toString());
        if (!digest.equals(lastStateDigest)) { revision++; lastStateDigest = digest; }
        int count = Math.max(1, (Math.max(blocks.size(), entities.size()) + 127) / 128);
        String[] ids = new String[count];
        for (int i = 0; i < count; i++) ids[i] = UUID.randomUUID().toString();
        Scene scene = new Scene(state.deepCopy(), blocks.deepCopy(), entities.deepCopy(),
            captured, revision, ids, inputFence);
        scenes.addLast(scene);
        for (int i = 0; i < count; i++) pages.put(ids[i], new Page(scene, i));
        while (scenes.size() > 4) remove(scenes.getFirst());
        return render(new Page(scene, 0));
    }

    JsonObject page(String cursor, String dimension) throws IOException {
        return render(lookup(cursor, dimension));
    }
    String sceneId(String cursor, String dimension) throws IOException {
        return lookup(cursor, dimension).scene.ids[0];
    }
    void requireInputFence(String cursor, String dimension, String expected) throws IOException {
        if (!lookup(cursor, dimension).scene.inputFence.equals(expected)) throw new IOException("REVISION_CONFLICT");
    }
    private Page lookup(String cursor, String dimension) throws IOException {
        prune();
        Page page = pages.get(cursor);
        if (page == null || !dimension.equals(page.scene.state.get("dimension").getAsString())) {
            throw new IOException("STALE_OBSERVATION");
        }
        return page;
    }

    private void prune() {
        for (Scene scene : scenes.toArray(Scene[]::new)) {
            if (clock.getAsLong() - scene.captured >= 30000) remove(scene);
        }
    }
    private void remove(Scene scene) {
        for (String id : scene.ids) pages.remove(id);
        scenes.remove(scene);
    }
    private JsonObject render(Page page) {
        Scene scene = page.scene;
        int offset = page.index * 128;
        JsonObject state = scene.state.deepCopy();
        state.add("nearby_blocks", slice(scene.blocks, offset));
        state.add("nearby_entities", slice(scene.entities, offset));
        boolean more = page.index + 1 < scene.ids.length;
        state.addProperty("truncated", more);
        state.addProperty("next_cursor", more ? scene.ids[page.index + 1] : null);
        JsonObject result = new JsonObject();
        result.addProperty("schema", "strata/NativeGameSnapshot/1");
        result.addProperty("snapshot_id", scene.ids[page.index]);
        result.addProperty("state_revision", scene.revision);
        result.addProperty("source_clock_id", clockId);
        result.addProperty("captured_elapsed_ms", scene.captured - origin);
        result.addProperty("age_ms", Math.max(0, clock.getAsLong() - scene.captured));
        result.add("state", state);
        return result;
    }
    private static JsonArray slice(JsonArray source, int offset) {
        JsonArray result = new JsonArray();
        for (int i = offset; i < Math.min(source.size(), offset + 128); i++) result.add(source.get(i).deepCopy());
        return result;
    }
    private static JsonArray withoutObservationTimes(JsonArray source) {
        JsonArray result = source.deepCopy();
        for (var value : result) if (value.isJsonObject()) value.getAsJsonObject().remove("observed_at");
        return result;
    }
}
