package io.github.opencnid.strata.client;

import com.google.gson.JsonObject;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

/** Synthetic visibility/lifecycle fixtures; JEI UI parity needs the authentic client. */
class GameRecipeQueryTest {
    static final GameRecipeQuery.Query QUERY = new GameRecipeQuery.Query("test:out", "output", 0);
    static GameRecipeQuery.Candidate candidate(String id, boolean book, String failure) {
        return new GameRecipeQuery.Candidate() {
            public boolean visible() { return true; }
            public String id() { return id; }
            public boolean bookUnlocked() { return book; }
            public JsonObject definition() throws IOException {
                if (failure != null) throw new IOException(failure);
                return GameRecipesTest.recipe(id);
            }
        };
    }
    static class Source implements GameRecipeQuery.Source {
        long generation = 1;
        List<GameRecipeQuery.Candidate> entries = new ArrayList<>();
        public long generation() { return generation; }
        public Iterable<? extends GameRecipeQuery.Candidate> focused(GameRecipeQuery.Query query) { return entries; }
    }
    @Test void hiddenCandidatesAreNeverIdentifiedAndDiscoveryDoesNotGrantCraftAuthority() throws Exception {
        var source = new Source();
        source.entries.add(new GameRecipeQuery.Candidate() {
            public boolean visible() { return false; }
            public String id() { throw new AssertionError("hidden identifier read"); }
            public boolean bookUnlocked() { throw new AssertionError("hidden book read"); }
            public JsonObject definition() { throw new AssertionError("hidden definition read"); }
        });
        source.entries.add(candidate("test:locked", false, null));
        source.entries.add(candidate("test:unlocked", true, null));
        var page = new GameRecipeQuery(() -> 0).query(QUERY, source);
        var rows = page.getAsJsonArray("recipes"); assertEquals(2, rows.size());
        assertEquals("discovery_only", rows.get(0).getAsJsonObject().get("craft_authority").getAsString());
        assertEquals("recipe_book", rows.get(1).getAsJsonObject().get("craft_authority").getAsString());
        assertFalse(page.toString().contains("private")); assertEquals(QUERY.json(), page.getAsJsonObject("query"));
    }
    @Test void unsupportedDefinitionsReturnOnlyVisibleIdentifierAndBookStatus() throws Exception {
        var source = new Source(); source.entries.add(candidate("test:custom", false, "MECHANIC_UNSUPPORTED"));
        var row = new GameRecipeQuery(() -> 0).query(QUERY, source).getAsJsonArray("recipes").get(0).getAsJsonObject();
        assertEquals(3, row.size()); assertFalse(row.get("supported").getAsBoolean());
        source.entries.set(0, candidate("test:custom", false, "GAME_RECIPE_CHANGED"));
        assertEquals("GAME_RECIPE_CHANGED", assertThrows(IOException.class,
            () -> new GameRecipeQuery(() -> 0).query(QUERY, source)).getMessage());
    }
    @Test void pagesAreStableButRuntimeFocusAndBookChangesInvalidateRevision() throws Exception {
        var source = new Source(); for (int i=0;i<70;i++) source.entries.add(candidate(String.format("test:r%03d",i),false,null));
        var projection = new GameRecipeQuery(() -> 0);
        var page = projection.query(QUERY,source); long revision=page.get("revision").getAsLong();
        assertEquals(32,page.getAsJsonArray("recipes").size()); assertEquals(32,page.get("next_cursor").getAsInt());
        assertEquals(revision,projection.query(new GameRecipeQuery.Query("test:out","output",32),source).get("revision").getAsLong());
        source.generation++; assertEquals(++revision,projection.query(QUERY,source).get("revision").getAsLong());
        var input = new GameRecipeQuery.Query("test:out","input",0);
        assertEquals(++revision,projection.query(input,source).get("revision").getAsLong());
        source.entries.set(0,candidate("test:r000",true,null));
        assertEquals(++revision,projection.query(input,source).get("revision").getAsLong());
    }
    @Test void reloadDuringProjectionAndMissingSourceRejectEntirePage() throws Exception {
        var source = new Source() {
            public Iterable<? extends GameRecipeQuery.Candidate> focused(GameRecipeQuery.Query query) {
                generation++; return entries;
            }
        };
        assertEquals("GAME_RECIPE_CHANGED",assertThrows(IOException.class,
            () -> new GameRecipeQuery(() -> 0).query(QUERY,source)).getMessage());
        source.generation=-1;
        assertEquals("GAME_RECIPE_SOURCE_UNAVAILABLE",assertThrows(IOException.class,
            () -> new GameRecipeQuery(() -> 0).query(QUERY,source)).getMessage());
    }
    @Test void matchAndTimeBoundsFailWithoutPartialResults() throws Exception {
        var source=new Source(); for (int i=0;i<513;i++) source.entries.add(candidate("test:r"+i,false,null));
        assertEquals("GAME_RECIPE_BOUNDS",assertThrows(IOException.class,
            () -> new GameRecipeQuery(() -> 0).query(QUERY,source)).getMessage());
        final long[] clock={0};
        assertEquals("GAME_RECIPE_TIMEOUT",assertThrows(IOException.class,
            () -> new GameRecipeQuery(() -> {clock[0]+=GameRecipeQuery.MAX_NANOS+1;return clock[0];}).query(QUERY,new Source())).getMessage());
    }
    @Test void wrapperIsWithinByteBoundAndDuplicateIdsReject() throws Exception {
        var source=new Source();
        for (int i=0;i<64;i++) source.entries.add(candidate("test:r"+i,false,null));
        var page=new GameRecipeQuery(() -> 0).query(QUERY,source);
        assertTrue(page.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8).length <= 32768);
        source.entries.add(candidate("test:r0",false,null));
        assertEquals("GAME_RECIPE_AMBIGUOUS",assertThrows(IOException.class,
            () -> new GameRecipeQuery(() -> 0).query(QUERY,source)).getMessage());
    }
    @Test void queryRequiresExactSourceCategoryRoleAndBounds() throws Exception {
        assertEquals(QUERY,GameRecipeQuery.Query.read(QUERY.json()));
        for (String field:List.of("source","category","item_id","role")) {
            var value=QUERY.json(); value.addProperty(field,"unknown");
            assertThrows(IOException.class,() -> GameRecipeQuery.Query.read(value));
        }
        for (int cursor:List.of(-1,513)) {
            var value=QUERY.json(); value.addProperty("after",cursor);
            assertThrows(IOException.class,() -> GameRecipeQuery.Query.read(value));
        }
        var hidden=QUERY.json(); hidden.addProperty("include_hidden",true);
        assertThrows(IOException.class,() -> GameRecipeQuery.Query.read(hidden));
        assertThrows(IllegalArgumentException.class,() -> new GameRecipeQuery.Query("test:out",null,0));
    }
}
