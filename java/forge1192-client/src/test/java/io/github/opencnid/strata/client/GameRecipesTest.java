package io.github.opencnid.strata.client;

import com.google.gson.JsonObject;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class GameRecipesTest {
    static JsonObject recipe(String id) throws IOException {
        return GameRecipes.definition(id, "minecraft:crafting_shaped", 2, 1,
            List.of(List.of("test:b", "test:a"), List.of()), new GameInventory.Stack("test:expert_output", 2, "private"));
    }
    @Test void publicProjectionHasSortedAlternativesAndNoPrivateStackComponents() throws Exception {
        var value = recipe("test:expert");
        assertEquals("test:a", value.getAsJsonArray("ingredients").get(0).getAsJsonArray().get(0).getAsString());
        assertFalse(value.toString().contains("private"));
        assertEquals(2, value.getAsJsonObject("result").get("count").getAsInt());
        assertEquals(2, GameRecipes.unsupported("test:custom").size());
    }
    @Test void stableBoundedPagesChangeRevisionOnVisibleDefinitionChange() throws Exception {
        var catalog = new GameRecipes(); var entries = new ArrayList<JsonObject>();
        for (int i = 0; i < 70; i++) entries.add(recipe(String.format("test:r%03d", i)));
        var first = catalog.page(entries, 0); long revision = first.get("revision").getAsLong();
        assertEquals(32, first.getAsJsonArray("recipes").size()); assertEquals(32, first.get("next_cursor").getAsInt());
        var second = catalog.page(entries, 32); assertEquals(revision, second.get("revision").getAsLong());
        var last = catalog.page(entries, 64); assertEquals(6, last.getAsJsonArray("recipes").size()); assertTrue(last.get("next_cursor").isJsonNull());
        entries.remove(0); assertEquals(revision + 1, catalog.page(entries, 0).get("revision").getAsLong());
        assertThrows(IOException.class, () -> catalog.page(entries, 70));
    }
    @Test void duplicateMalformedAndUnboundedDefinitionsReject() throws Exception {
        var catalog = new GameRecipes();
        assertThrows(IOException.class, () -> catalog.page(List.of(recipe("test:same"), recipe("test:same")), 0));
        assertThrows(IOException.class, () -> recipe("not-namespaced"));
        assertThrows(IOException.class, () -> catalog.page(List.of(), -1));
        assertThrows(IOException.class, () -> GameRecipes.definition("test:r", "test:custom", 1, 1,
            List.of(List.of("test:item")), new GameInventory.Stack("test:out", 1, "")));
        assertThrows(IOException.class, () -> GameRecipes.definition("test:r", "minecraft:crafting_shapeless", 0, 0,
            List.of(List.of()), new GameInventory.Stack("test:out", 1, "")));
    }
    @Test void byteLimitShortensPageAndUnsupportedEntriesRemainExplicit() throws Exception {
        var choices = new ArrayList<String>(); for (int i = 0; i < 64; i++) choices.add("test:" + "x".repeat(60) + i);
        var entry = GameRecipes.definition("test:large", "minecraft:crafting_shaped", 2, 2,
            List.of(choices, choices, choices, choices), new GameInventory.Stack("test:out", 1, ""));
        var other = entry.deepCopy(); other.addProperty("recipe_id", "test:large2");
        var page = new GameRecipes().page(List.of(entry, other, GameRecipes.unsupported("test:unknown")), 0);
        assertEquals(1, page.getAsJsonArray("recipes").size()); assertEquals(1, page.get("next_cursor").getAsInt());
        assertTrue(page.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8).length <= 32768);
    }
}
