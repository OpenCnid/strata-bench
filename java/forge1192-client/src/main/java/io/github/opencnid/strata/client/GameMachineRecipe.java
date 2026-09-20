package io.github.opencnid.strata.client;

import com.google.gson.JsonArray;
import com.google.gson.JsonNull;
import com.google.gson.JsonObject;
import java.io.IOException;
import java.util.List;
import java.util.TreeMap;

/** Pure bounded projection of the two declared JEI machine layouts, never a motor plan. */
final class GameMachineRecipe {
    static final String JEI_FILE = "jei-1.19.2-forge-11.8.1.1034.jar";
    static final String JEI_HASH = "4ca677c4d7b8234da2071b3e93424a2e1eedd06906c20f55ff22a078cfd6e3b2";
    static void requireArtifacts(java.util.Map<String,String> artifacts) throws IOException {
        GameMachineMenu.requireArtifacts(artifacts);
        if (!JEI_HASH.equals(artifacts.get(JEI_FILE))) throw new IOException("GAME_RECIPE_ARTIFACT_UNSUPPORTED");
    }
    record Choice(String kind, String id, int amount) {}
    static JsonObject definition(String id, String category, int energy, Float chance,
            List<Choice> inputs, List<Choice> outputs) throws IOException {
        boolean furnace = category.equals("thermal:furnace");
        if (!furnace && !category.equals("thermal:crucible")) throw unsupported();
        if (furnace != (chance != null)) throw unsupported();
        var value = GameRecipes.unsupported(id); value.addProperty("supported", true);
        value.addProperty("category", category);
        if (energy > 0) value.addProperty("energy_rf", energy); else value.add("energy_rf", JsonNull.INSTANCE);
        var slots = new JsonArray();
        slots.add(slot("input", "item", inputs));
        if (outputs.size() != 1) throw unsupported();
        slots.add(slot("output", furnace ? "item" : "fluid", outputs)); value.add("slots", slots);
        value.add("output_tooltip", tooltip(chance));
        return value;
    }
    private static JsonObject slot(String role, String kind, List<Choice> choices) throws IOException {
        if (choices.isEmpty() || choices.size() > 64) throw unsupported();
        var ordered = new TreeMap<String, JsonObject>();
        for (var choice : choices) {
            if (!kind.equals(choice.kind) || choice.amount < 1 || kind.equals("item") && choice.amount > 64) throw unsupported();
            var row = new JsonObject(); row.addProperty("kind", kind);
            row.addProperty(kind + "_id", GameRecipes.id(choice.id));
            row.addProperty(kind.equals("item") ? "count" : "amount_mb", choice.amount);
            // Different counts of the same ingredient are ambiguous under this initial policy.
            if (ordered.put(choice.id, row) != null) throw unsupported();
        }
        var slot = new JsonObject(); slot.addProperty("role", role); var rows = new JsonArray();
        ordered.values().forEach(rows::add); slot.add("ingredients", rows); return slot;
    }
    static com.google.gson.JsonElement tooltip(Float chance) throws IOException {
        if (chance == null) return JsonNull.INSTANCE;
        if (!Float.isFinite(chance) || Math.abs(chance) > 1000000) throw unsupported();
        // Match TCoreJeiPlugin.defaultOutputTooltip: absolute value, fractional part,
        // truncated integer percent. Do not expose hidden sign or precision as probability.
        float absolute = Math.abs(chance), fraction = absolute < 1 ? absolute : absolute - (int) absolute;
        if (absolute >= 1 && fraction == 0) return JsonNull.INSTANCE;
        var value = new JsonObject(); value.addProperty("kind", absolute < 1 ? "chance" : "additional_chance");
        value.addProperty("percent", (int) (100 * fraction)); return value;
    }
    static IOException unsupported() { return new IOException("MECHANIC_UNSUPPORTED"); }
}
