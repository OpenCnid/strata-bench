package io.github.opencnid.strata.client;

import com.google.gson.JsonObject;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Set;

/** Focused player-visible recipe projection; discovery never grants execution authority. */
final class GameRecipeQuery {
    static final String POLICY = "jei-thermal-emi-crafting-visible-focus-pages32/3";
    static final int MAX_MATCHES = 512;
    static final long MAX_NANOS = 100_000_000L;
    record Query(String source, String category, String targetKind, String item, String role, int after) {
        Query(String category, String targetKind, String item, String role, int after) { this("jei", category, targetKind, item, role, after); }
        Query(String item, String role, int after) { this("minecraft:crafting", "item", item, role, after); }
        Query {
            if (source == null || !Set.of("jei", "emi").contains(source)
                    || source.equals("emi") && !"minecraft:crafting".equals(category)
                    || category == null || !Set.of("minecraft:crafting", "thermal:furnace", "thermal:crucible").contains(category)
                    || targetKind == null || !Set.of("item", "fluid").contains(targetKind)
                    || category.equals("minecraft:crafting") && !targetKind.equals("item")
                    || item == null || item.length() > 256 || !item.matches("[a-z0-9_.-]+:[a-z0-9_./-]+")
                    || role == null || !Set.of("input", "output").contains(role) || after < 0 || after > MAX_MATCHES) {
                throw new IllegalArgumentException("GAME_RECIPE_QUERY_INVALID");
            }
        }
        boolean crafting() { return category.equals("minecraft:crafting"); }
        JsonObject json() {
            var result = new JsonObject(); result.addProperty("source", source);
            result.addProperty("category", category); result.addProperty(targetKind + "_id", item);
            result.addProperty("role", role); result.addProperty("after", after); return result;
        }
        static Query read(JsonObject value) throws IOException {
            String target = value.has("fluid_id") ? "fluid" : "item";
            SettingsJson.fields(value, "source", "category", target + "_id", "role", "after");
            long after = SettingsJson.integer(value, "after");
            if (after > MAX_MATCHES) throw new IOException("GAME_RECIPE_BOUNDS");
            try { return new Query(SettingsJson.string(value,"source"), SettingsJson.string(value,"category"), target,
                SettingsJson.string(value, target + "_id"), SettingsJson.string(value, "role"), (int) after); }
            catch (IllegalArgumentException invalid) { throw new IOException("GAME_RECIPE_QUERY_INVALID"); }
        }
    }
    interface Candidate {
        boolean visible() throws IOException;
        String id() throws IOException;
        JsonObject definition() throws IOException;
        boolean bookUnlocked() throws IOException;
    }
    interface Source {
        long generation();
        Iterable<? extends Candidate> focused(Query query) throws IOException;
    }
    private final GameRecipes pages = new GameRecipes();
    private final java.util.function.LongSupplier clock;
    GameRecipeQuery() { this(System::nanoTime); }
    GameRecipeQuery(java.util.function.LongSupplier clock) { this.clock = clock; }
    private long lastGeneration = -1;
    private String lastFocus;
    JsonObject query(Query query, Source source) throws IOException {
        long started = clock.getAsLong();
        long generation = source.generation();
        if (generation < 0 || generation > 9007199254740991L) throw new IOException("GAME_RECIPE_SOURCE_UNAVAILABLE");
        var definitions = new ArrayList<JsonObject>(); int inspected = 0;
        for (var candidate : source.focused(query)) {
            checkTime(started);
            if (++inspected > MAX_MATCHES) throw new IOException("GAME_RECIPE_BOUNDS");
            // Do not even read a hidden candidate's identifier or definition.
            if (!candidate.visible()) continue;
            String id = GameRecipes.id(candidate.id()); JsonObject value;
            try { value = candidate.definition().deepCopy(); }
            catch (IOException unsupported) {
                if (!Set.of("MECHANIC_UNSUPPORTED", "REGISTRY_UNSUPPORTED").contains(unsupported.getMessage())) throw unsupported;
                value = GameRecipes.unsupported(id);
            }
            if (!id.equals(SettingsJson.string(value, "recipe_id"))) throw new IOException("GAME_RECIPE_CHANGED");
            value.addProperty("craft_authority", query.crafting() && candidate.bookUnlocked() ? "recipe_book" : "discovery_only");
            definitions.add(value);
        }
        checkTime(started);
        if (source.generation() != generation) throw new IOException("GAME_RECIPE_CHANGED");
        String focus = query.source + ":" + query.category + ":" + query.targetKind + ":" + query.item + ":" + query.role;
        if (lastGeneration != generation || !focus.equals(lastFocus)) {
            pages.invalidate(); lastGeneration = generation; lastFocus = focus;
        }
        var result = pages.page(definitions, query.after, 1024);
        result.add("query", query.json()); result.addProperty("source_generation", generation);
        result.addProperty("policy", POLICY); checkTime(started); return result;
    }
    private void checkTime(long started) throws IOException {
        if (clock.getAsLong() - started > MAX_NANOS) throw new IOException("GAME_RECIPE_TIMEOUT");
    }
}
