package io.github.opencnid.strata.client;

import com.google.gson.JsonObject;
import java.io.IOException;

/** Explicit source selection for a single recipe, never a grant to enumerate hidden definitions. */
record GameRecipeSelection(GameRecipeQuery.Query query, long generation, long revision) {
    static GameRecipeSelection read(JsonObject value) throws IOException {
        SettingsJson.fields(value,"query","source_generation","revision");
        if (!value.get("query").isJsonObject()) throw new IOException("GAME_RECIPE_QUERY_INVALID");
        var query = GameRecipeQuery.Query.read(value.getAsJsonObject("query"));
        if (!query.crafting()) throw new IOException("MECHANIC_UNSUPPORTED");
        return new GameRecipeSelection(query,
            SettingsJson.integer(value,"source_generation"),SettingsJson.integer(value,"revision"));
    }
    JsonObject definition(JsonObject page, String id, boolean initial) throws IOException {
        if (!query.json().equals(page.get("query")) || SettingsJson.integer(page,"source_generation") != generation
                || !GameRecipeQuery.POLICY.equals(SettingsJson.string(page,"policy"))
                || initial && SettingsJson.integer(page,"revision") != revision) throw new IOException("GAME_RECIPE_CHANGED");
        for (var row:page.getAsJsonArray("recipes")) {
            var value=row.getAsJsonObject();
            if (!id.equals(SettingsJson.string(value,"recipe_id"))) continue;
            if (!value.has("supported") || !value.get("supported").isJsonPrimitive()
                    || !value.get("supported").getAsJsonPrimitive().isBoolean()
                    || !value.get("supported").getAsBoolean()) throw new IOException("MECHANIC_UNSUPPORTED");
            var definition=value.deepCopy(); definition.remove("craft_authority"); return definition;
        }
        throw new IOException("RECIPE_NOT_KNOWN");
    }
}
