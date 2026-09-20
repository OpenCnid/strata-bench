package io.github.opencnid.strata.client;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.atomic.AtomicLong;
import org.junit.jupiter.api.Test;

/** Synthetic scene; exercises real page projection, copied frame and negative source boundaries. */
class GameRecipePageTest {
    static List<GameRecipeControls.Control> controls() {
        var rows = new ArrayList<GameRecipeControls.Control>();
        for (int i = 0; i < 4; i++) rows.add(new GameRecipeControls.Control(new Object(), GameRecipeControls.KINDS.get(i),
            i == 0 ? "enabled" : i == 1 ? "disabled" : "clipped", new GameRecipeSlots.Rect(10 + i * 12, 10, 10, 10)));
        return List.copyOf(rows);
    }
    static List<GameRecipeHeaders.Label> headers() {
        return List.of(new GameRecipeHeaders.Label("category", "text", "Visible café <&> \"title\" \\u2028 \u2028\u2029 😀"),
            new GameRecipeHeaders.Label("page", "text", "1/4"));
    }
    static GameRecipeSlots.Layout layout() {
        return new GameRecipeSlots.Layout("minecraft:crafting", List.of(
            new GameRecipeSlots.Slot(0, "input", new GameRecipeSlots.Display("item", "minecraft:stone", 2)),
            new GameRecipeSlots.Slot(1, "output", new GameRecipeSlots.Display("fluid", "minecraft:water", 1000)),
            new GameRecipeSlots.Slot(2, "catalyst", new GameRecipeSlots.Display("unsupported", null, 0)),
            new GameRecipeSlots.Slot(4, "render_only", new GameRecipeSlots.Display("empty", null, 0))), true);
    }
    static final class Source implements GameRecipePage.Source {
        final Object screen = new Object(), chapter = new Object(), quest = new Object();
        long generation = 2; String kind = "task_recipes";
        List<GameRecipeSlots.Layout> layouts = new ArrayList<>(List.of(layout()));
        List<GameRecipeHeaders.Label> headers = new ArrayList<>(GameRecipePageTest.headers());
        List<GameRecipeControls.Control> controls = new ArrayList<>(GameRecipePageTest.controls());
        int reads, change;
        public GameQuestScreen.Snapshot screen() {
            if (++reads == 2 && change == 1) generation++;
            if (reads == 2 && change == 2) layouts.clear();
            if (reads == 2 && change == 4) headers.clear();
            if (reads == 2 && change == 5) controls.clear();
            return new GameQuestScreen.Snapshot(new GameQuestScreen.Frame(1, screen, chapter, quest,
                "0000000000000001", "0000000000000002", "a".repeat(64), kind), generation, 3);
        }
        public List<GameRecipeSlots.Layout> layouts() throws IOException {
            if (change == 3) throw new IOException("GAME_RECIPE_RENDER_UNAVAILABLE");
            return layouts;
        }
        public List<GameRecipeHeaders.Label> headers() { return headers; }
        public List<GameRecipeControls.Control> controls() { return controls; }
    }
    @Test void completeEnvelopeDeclaresPartialCoverageWithoutPrivateReferences() throws Exception {
        var source = new Source(); var page = new GameRecipePage().page(source);
        assertEquals("slot_header_control_draw_operands", page.get("coverage").getAsString()); assertFalse(page.get("complete").getAsBoolean());
        assertEquals("0000000000000002", page.get("quest_id").getAsString());
        assertEquals(64, page.get("revision").getAsString().length());
        for (String forbidden : List.of("runtime", "screen_object", "parent", "nbt", "allIngredients", "recipe_id"))
            assertFalse(page.toString().contains(forbidden));
        page.getAsJsonArray("layouts").remove(0);
        assertEquals(1, new GameRecipePage().page(source).getAsJsonArray("layouts").size());
    }
    @Test void bookAndMalformedSnapshotCannotMasqueradeAsCurrentRecipePage() {
        var source = new Source(); source.kind = "quest_book";
        assertThrows(IOException.class, () -> new GameRecipePage().page(source));
        source.kind = "task_recipes"; source.generation = -1;
        assertThrows(IOException.class, () -> new GameRecipePage().page(source));
    }
    @Test void changedSourceOrMutableListCannotPublishMixedSnapshot() {
        for (int fault : new int[]{1, 2, 3, 4, 5}) {
            var source = new Source(); source.change = fault;
            assertThrows(IOException.class, () -> new GameRecipePage().page(source));
        }
    }
    @Test void tooManyAndOversizedPagesRejectWithoutTruncation() {
        for (int count : new int[]{33}) {
            var source = new Source(); source.layouts = java.util.Collections.nCopies(count, layout());
            assertThrows(IOException.class, () -> new GameRecipePage().page(source));
        }
        var source = new Source(); var rows = new ArrayList<GameRecipeSlots.Slot>();
        for (int i = 0; i < 128; i++) rows.add(new GameRecipeSlots.Slot(i, "input",
            new GameRecipeSlots.Display("item", "minecraft:" + "x".repeat(220), 1)));
        source.layouts = List.of(new GameRecipeSlots.Layout("minecraft:crafting", rows, false));
        assertThrows(IOException.class, () -> new GameRecipePage().page(source));
    }
    @Test void emptyPageStillHasOriginHeadersControlsAndContentDigest() throws Exception {
        var source = new Source(); var page = new GameRecipePage();
        var full = page.page(source); source.layouts.clear(); var empty = page.page(source);
        assertEquals(0, empty.getAsJsonArray("layouts").size()); assertFalse(empty.get("complete").getAsBoolean());
        assertEquals(full.get("headers"), empty.get("headers")); assertEquals(full.get("controls"), empty.get("controls"));
        assertNotEquals(full.get("revision"), empty.get("revision")); assertEquals(empty, page.page(source));
        source.headers.clear(); assertThrows(IOException.class, () -> page.page(source));
    }
    @Test void clockDeadlineAndRegressionReject() {
        for (long elapsed : new long[]{-1, 100_000_001}) {
            var calls = new AtomicLong(); var page = new GameRecipePage(() -> calls.getAndIncrement() == 0 ? 0 : elapsed);
            assertThrows(IOException.class, () -> page.page(new Source()));
        }
    }
    @Test void digestBindsOriginScreenAndCopiedContent() throws Exception {
        var source = new Source(); var page = new GameRecipePage();
        var first = page.page(source).get("revision"); assertEquals(first, page.page(source).get("revision"));
        source.generation++; assertNotEquals(first, page.page(source).get("revision"));
        source.generation--; source.layouts = List.of(new GameRecipeSlots.Layout("minecraft:smelting", layout().slots(), true));
        assertNotEquals(first, page.page(source).get("revision"));
    }
    @Test void copiedFrameAgeRemainsEnforcedDuringPageRead() throws Exception {
        var clock = new AtomicLong(); var capture = new GameRecipeRenderCapture(clock::get); var source = new Source();
        var key = new GameRecipeRenderCapture.Key(source.screen, new Object(), new Object(), 800, 600);
        capture.beginFrame(key); capture.headers(headers()); capture.controls(controls()); capture.beginLayouts(source); capture.layoutPredicate(source, source, true); capture.drawn(source.screen, layout()); capture.layoutPredicate(source, source, false); capture.endLayouts(source); capture.finishFrame(key);
        var port = new GameRecipePage.Source() {
            public GameQuestScreen.Snapshot screen() { return source.screen(); }
            public List<GameRecipeSlots.Layout> layouts() throws IOException { return capture.copied(key); }
            public List<GameRecipeHeaders.Label> headers() throws IOException { return capture.headers(key); }
            public List<GameRecipeControls.Control> controls() throws IOException { return capture.controls(key); }
        };
        new GameRecipePage().page(port); clock.set(250_000_001);
        assertThrows(IOException.class, () -> new GameRecipePage().page(port));
    }
}
