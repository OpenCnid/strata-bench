package io.github.opencnid.strata.client;

import com.google.gson.JsonArray;
import com.google.gson.JsonNull;
import com.google.gson.JsonObject;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.TreeMap;

/** Bounded public projection. The native caller supplies only player-known definitions. */
final class GameRecipes {
    static final String POLICY = "player-book-exact-shaped-shapeless-pages32/1";
    private String digest;
    private long revision;
    void invalidate() { digest = null; }
    static String id(String value) throws IOException {
        if (value == null || value.length() > 256 || !value.matches("[a-z0-9_.-]+:[a-z0-9_./-]+")) {
            throw new IOException("REGISTRY_UNSUPPORTED");
        }
        return value;
    }
    static JsonObject unsupported(String id) throws IOException {
        var value = new JsonObject(); value.addProperty("recipe_id", id(id)); value.addProperty("supported", false); return value;
    }
    static JsonObject definition(String id, String serializer, int width, int height,
            List<List<String>> ingredients, GameInventory.Stack output) throws IOException {
        boolean shaped = serializer.equals("minecraft:crafting_shaped");
        if ((!shaped && !serializer.equals("minecraft:crafting_shapeless"))
                || (shaped ? width < 1 || width > 3 || height < 1 || height > 3 || ingredients.size() != width * height
                           : width != 0 || height != 0 || ingredients.isEmpty() || ingredients.size() > 9)
                || output.empty() || output.count() < 1 || output.count() > 64) throw new IOException("MECHANIC_UNSUPPORTED");
        var value = unsupported(id); value.addProperty("supported", true); value.addProperty("serializer", serializer);
        value.addProperty("width", width); value.addProperty("height", height);
        var slots = new JsonArray(); boolean nonempty = false;
        for (var alternatives : ingredients) {
            if (alternatives.size() > 64 || (!shaped && alternatives.isEmpty())) throw new IOException("MECHANIC_UNSUPPORTED");
            var row = new JsonArray(); var unique = new java.util.TreeSet<String>();
            for (String item : alternatives) if (!unique.add(id(item))) throw new IOException("MECHANIC_UNSUPPORTED");
            unique.forEach(row::add); nonempty |= !unique.isEmpty(); slots.add(row);
        }
        if (!nonempty) throw new IOException("MECHANIC_UNSUPPORTED");
        value.add("ingredients", slots); var result = new JsonObject();
        result.addProperty("item_id", id(output.id())); result.addProperty("count", output.count()); value.add("result", result);
        if (bytes(value) > 30000) throw new IOException("MECHANIC_UNSUPPORTED");
        return value;
    }
    JsonObject page(List<JsonObject> definitions, int after) throws IOException {
        return page(definitions, after, 0);
    }
    JsonObject page(List<JsonObject> definitions, int after, int reservedBytes) throws IOException {
        if (reservedBytes < 0 || reservedBytes > 2048) throw new IOException("GAME_RECIPE_BOUNDS");
        if (after < 0 || after > 10000 || definitions.size() > 10000) throw new IOException("GAME_RECIPE_BOUNDS");
        var ordered = new TreeMap<String, JsonObject>(); int size = 0;
        for (var entry : definitions) {
            String id = id(SettingsJson.string(entry, "recipe_id"));
            if (ordered.put(id, entry) != null) throw new IOException("GAME_RECIPE_AMBIGUOUS");
            size += bytes(entry); if (size > 4 * 1024 * 1024) throw new IOException("GAME_RECIPE_BOUNDS");
        }
        String nextDigest = KeyOptions.sha256(ordered.values().toString());
        if (!nextDigest.equals(digest)) { revision++; digest = nextDigest; }
        if (after > ordered.size()) throw new IOException("GAME_RECIPE_BOUNDS");
        var result = new JsonObject(); result.addProperty("revision", revision);
        var recipes = new JsonArray(); result.add("recipes", recipes); result.add("next_cursor", JsonNull.INSTANCE);
        var entries = List.copyOf(ordered.values()); int next = after;
        while (next < entries.size() && recipes.size() < 32) {
            var entry = entries.get(next);
            if (bytes(result) + bytes(entry) + 32 + reservedBytes > 32768) break;
            recipes.add(entry.deepCopy()); next++;
        }
        if (next < entries.size()) {
            if (next == after) throw new IOException("GAME_RECIPE_BOUNDS");
            result.addProperty("next_cursor", next);
        }
        return result;
    }
    private static int bytes(JsonObject value) { return value.toString().getBytes(StandardCharsets.UTF_8).length; }
}
