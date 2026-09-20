package io.github.opencnid.strata.client;

import com.google.gson.JsonObject;
import java.io.IOException;
import java.util.Set;

/** Resolves only coordinates in the delivered page; no world/registry lookup here. */
final class GamePlacement {
    private static final Set<String> AIR = Set.of("minecraft:air", "minecraft:cave_air", "minecraft:void_air");
    record Target(int x, int y, int z, int dx, int dy, int dz, String supportId, String destinationId) {}
    static Target observed(JsonObject snapshot, JsonObject action) throws IOException {
        var p = GameBatch.vector(action, "support"); var face = GameBatch.vector(action, "face");
        if (Math.abs(face.x()) + Math.abs(face.y()) + Math.abs(face.z()) != 1
                || face.x() != Math.rint(face.x()) || face.y() != Math.rint(face.y()) || face.z() != Math.rint(face.z())) {
            throw new IOException("GAME_FACE_INVALID");
        }
        int x = (int) Math.floor(p.x()), y = (int) Math.floor(p.y()), z = (int) Math.floor(p.z());
        int dx = (int) face.x(), dy = (int) face.y(), dz = (int) face.z();
        String support = find(snapshot, x, y, z), destination = find(snapshot, x + dx, y + dy, z + dz);
        if (AIR.contains(support) || !AIR.contains(destination)) throw new IOException("PRECONDITION_FAILED");
        return new Target(x, y, z, dx, dy, dz, support, destination);
    }
    private static String find(JsonObject snapshot, int x, int y, int z) throws IOException {
        String id = null;
        for (var value : snapshot.getAsJsonObject("state").getAsJsonArray("nearby_blocks")) {
            var block = value.getAsJsonObject(); var p = block.getAsJsonObject("position");
            if (p.get("x").getAsDouble() == x && p.get("y").getAsDouble() == y && p.get("z").getAsDouble() == z) {
                if (id != null) throw new IOException("GAME_TARGET_AMBIGUOUS");
                id = SettingsJson.string(block, "block_id");
            }
        }
        if (id == null) throw new IOException("TARGET_NOT_OBSERVED");
        return id;
    }
}
