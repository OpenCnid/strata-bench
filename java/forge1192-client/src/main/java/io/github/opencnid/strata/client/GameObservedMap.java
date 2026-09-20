package io.github.opencnid.strata.client;

import com.google.gson.JsonObject;
import java.io.IOException;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.Map;

/** No world/reader reference: a planner can only read states on durably delivered pages. */
final class GameObservedMap<T> {
    static final int MAX_DELIVERED = 1024;
    record Position(int x, int y, int z) {}
    record Cell<T>(String id, T state) {}
    record Known<T>(Cell<T> cell, long captured, long revision) {}
    private record Scene<T>(String dimension, long captured, long revision,
                            Map<Position, Cell<T>> cells) {}
    private final Map<String, Scene<T>> scenes = new LinkedHashMap<>();
    private final Map<Position, Known<T>> delivered = new LinkedHashMap<>();
    private String dimension;

    void reset() { scenes.clear(); delivered.clear(); dimension = null; }

    void remember(String id, String dimension, long captured, long revision,
                  Map<Position, Cell<T>> cells) throws IOException {
        if (captured < 0 || revision < 0 || cells.size() > GameVisibility.MAX_CELLS) {
            throw new IOException("GAME_SCENE_CAPACITY");
        }
        if (this.dimension != null && !this.dimension.equals(dimension)) reset();
        this.dimension = dimension;
        if (scenes.containsKey(id)) throw new IOException("GAME_SCENE_IDENTITY_CONFLICT");
        scenes.put(id, new Scene<>(dimension, captured, revision, Map.copyOf(cells)));
        while (scenes.size() > 4) scenes.remove(scenes.keySet().iterator().next());
    }

    void deliver(String sceneId, JsonObject snapshot) throws IOException {
        Scene<T> scene = scenes.get(sceneId);
        JsonObject state = snapshot.getAsJsonObject("state");
        if (scene == null || !scene.dimension.equals(SettingsJson.string(state, "dimension"))
                || scene.captured != SettingsJson.integer(snapshot, "captured_elapsed_ms")
                || scene.revision != SettingsJson.integer(snapshot, "state_revision")) {
            throw new IOException("STALE_OBSERVATION");
        }
        var blocks = state.getAsJsonArray("nearby_blocks");
        if (blocks.size() > 128) throw new IOException("GAME_PAGE_CAPACITY");
        Map<Position, Known<T>> additions = new LinkedHashMap<>();
        var seen = new HashSet<Position>();
        for (var element : blocks) {
            JsonObject block = element.getAsJsonObject();
            var point = GameBatch.vector(block, "position");
            if (point.x() != Math.rint(point.x()) || point.y() != Math.rint(point.y())
                    || point.z() != Math.rint(point.z())) throw new IOException("GAME_CELL_INVALID");
            Position position = new Position((int) point.x(), (int) point.y(), (int) point.z());
            Cell<T> cell = scene.cells.get(position);
            if (!seen.add(position) || cell == null || !cell.id.equals(SettingsJson.string(block, "block_id"))) {
                throw new IOException("GAME_DELIVERY_CONFLICT");
            }
            Known<T> previous = delivered.get(position);
            if (previous != null) {
                if (previous.captured > scene.captured
                        || previous.captured == scene.captured && previous.revision > scene.revision) continue;
                if (previous.captured == scene.captured && previous.revision == scene.revision) {
                    if (!previous.cell.equals(cell)) throw new IOException("GAME_DELIVERY_CONFLICT");
                    continue; // Re-delivery cannot refresh eviction order or observation age.
                }
            }
            additions.put(position, new Known<>(cell, scene.captured, scene.revision));
        }
        // Validate the whole page before changing any planner authority.
        additions.forEach((position, cell) -> { delivered.remove(position); delivered.put(position, cell); });
        while (delivered.size() > MAX_DELIVERED) delivered.remove(delivered.keySet().iterator().next());
    }

    Known<T> at(Position position) { return delivered.get(position); }
    Map<Position, Known<T>> snapshot() { return Map.copyOf(delivered); }
}
