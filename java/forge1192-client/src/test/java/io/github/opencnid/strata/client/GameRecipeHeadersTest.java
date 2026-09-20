package io.github.opencnid.strata.client;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.util.List;
import java.util.concurrent.atomic.AtomicLong;
import org.junit.jupiter.api.Test;

/** Synthetic header callbacks; native Mixin/Font/viewport parity remains an authentic test. */
class GameRecipeHeadersTest {
    private static final GameRecipeHeaders.Label TITLE = new GameRecipeHeaders.Label("category", "text", "Visible...");
    private static final GameRecipeHeaders.Label PAGE = new GameRecipeHeaders.Label("page", "text", "2/9");
    private static List<GameRecipeHeaders.Label> render(GameRecipeHeaders state, Object screen) throws Exception {
        Object category = new Object(), title = new Object(), page = new Object();
        state.begin(screen); state.beginCategory(category);
        state.beginLabel(title, TITLE); state.endLabel(title, TITLE); state.endCategory(category);
        state.beginLabel(page, PAGE); state.endLabel(page, PAGE);
        return state.beforeLayouts();
    }
    @Test void onlyCompleteOrderedCallbacksPublishImmutableCopies() throws Exception {
        var state = new GameRecipeHeaders(); var screen = new Object();
        var labels = render(state, screen); assertEquals(List.of(TITLE, PAGE), labels);
        assertFalse(state.observing()); assertFalse(state.complete());
        assertThrows(UnsupportedOperationException.class, () -> labels.clear());
        state.end(screen); assertTrue(state.complete()); state.clear(); assertFalse(state.complete());
        render(state, screen); state.end(screen); assertTrue(state.complete());
    }
    @Test void missingNestedReorderedAndWrongOwnerCallbacksReject() throws Exception {
        var state = new GameRecipeHeaders(); var screen = new Object(); var category = new Object();
        assertThrows(IOException.class, state::beforeLayouts);
        state.begin(screen); assertThrows(IOException.class, () -> state.begin(screen));
        assertThrows(IOException.class, () -> state.beginLabel(screen, PAGE));
        state.beginCategory(category); assertThrows(IOException.class, () -> state.endCategory(category));
        state.beginLabel(screen, TITLE); assertThrows(IOException.class, () -> state.beginLabel(screen, TITLE));
        assertThrows(IOException.class, () -> state.endLabel(new Object(), TITLE));
        assertThrows(IOException.class, () -> state.endLabel(screen, new GameRecipeHeaders.Label("category", "text", "changed")));
        state.endLabel(screen, TITLE); assertThrows(IOException.class, () -> state.endCategory(new Object()));
        state.endCategory(category); assertThrows(IOException.class, state::beforeLayouts);
        state.beginLabel(screen, PAGE); state.endLabel(screen, PAGE); state.beforeLayouts();
        assertThrows(IOException.class, state::beforeLayouts); assertThrows(IOException.class, () -> state.end(new Object()));
    }
    @Test void clippedAndUnsupportedMarkersCannotCarryText() throws Exception {
        for (String status : List.of("clipped", "unsupported")) {
            var value = new GameRecipeHeaders.Label("category", status, null).json(); assertTrue(value.get("text").isJsonNull());
            assertThrows(IOException.class, () -> new GameRecipeHeaders.Label("category", status, "private full title").json());
        }
        assertThrows(IOException.class, () -> new GameRecipeHeaders.Label("page", "text", null).json());
        assertThrows(IOException.class, () -> new GameRecipeHeaders.Label("full_title", "text", "private").json());
        assertThrows(IOException.class, () -> new GameRecipeHeaders.Label(null, null, null).json());
    }
    @Test void textBoundsCountUnicodeAndRejectLoneSurrogates() throws Exception {
        new GameRecipeHeaders.Label("category", "text", "😀".repeat(1024)).json();
        new GameRecipeHeaders.Label("page", "text", "").json();
        for (String value : List.of("x".repeat(1025), "😀".repeat(1025), "\ud800", "\udfff"))
            assertThrows(IOException.class, () -> new GameRecipeHeaders.Label("category", "text", value).json());
    }
    @Test void frameRequiresHeaderEvidenceAndExpiresItWithTheFrame() throws Exception {
        var clock = new AtomicLong(); var capture = new GameRecipeRenderCapture(clock::get);
        Object screen = new Object(); var key = new GameRecipeRenderCapture.Key(screen, new Object(), new Object(), 800, 600);
        capture.beginFrame(key); capture.beginLayouts(screen); capture.layoutPredicate(screen, screen, true); capture.drawn(screen, GameRecipePageTest.layout());
        capture.layoutPredicate(screen, screen, false); capture.endLayouts(screen); capture.finishFrame(key);
        assertThrows(IOException.class, () -> capture.headers(key));
        capture.beginFrame(key); capture.headers(List.of(TITLE, PAGE)); capture.beginLayouts(screen);
        capture.layoutPredicate(screen, screen, true); capture.drawn(screen, GameRecipePageTest.layout()); capture.layoutPredicate(screen, screen, false); capture.endLayouts(screen); capture.finishFrame(key);
        assertEquals(List.of(TITLE, PAGE), capture.headers(key));
        clock.set(250_000_001); assertThrows(IOException.class, () -> capture.headers(key));
    }
    @Test void missingLabelWrongOrderAndLateHeaderCannotPublish() {
        var source = new GameRecipePageTest.Source(); source.headers = List.of(TITLE);
        assertThrows(IOException.class, () -> new GameRecipePage().page(source));
        source.headers = List.of(PAGE, TITLE); assertThrows(IOException.class, () -> new GameRecipePage().page(source));
        var capture = new GameRecipeRenderCapture(); Object screen = new Object();
        var key = new GameRecipeRenderCapture.Key(screen, screen, screen, 800, 600);
        capture.beginFrame(key); capture.beginLayouts(screen);
        assertThrows(IOException.class, () -> capture.headers(List.of(TITLE, PAGE)));
        capture.layoutPredicate(screen, screen, true); capture.drawn(screen); capture.layoutPredicate(screen, screen, false); capture.endLayouts(screen); capture.finishFrame(key);
        assertThrows(IOException.class, () -> capture.read(key));
    }
    @Test void headerContentAndStatusParticipateInPageDigest() throws Exception {
        var source = new GameRecipePageTest.Source(); var page = new GameRecipePage();
        var initial = page.page(source).get("revision");
        source.headers = List.of(TITLE, PAGE); assertNotEquals(initial, page.page(source).get("revision"));
        var before = page.page(source).get("revision");
        source.headers = List.of(new GameRecipeHeaders.Label("category", "clipped", null), PAGE);
        assertNotEquals(before, page.page(source).get("revision"));
    }
    @Test void offscreenAndPartialGeometryNeverInvokeTextReader() throws Exception {
        var viewport = new GameRecipeSlots.Rect(0, 0, 100, 100);
        for (var area : List.of(new GameRecipeSlots.Rect(-1, 0, 10, 10), new GameRecipeSlots.Rect(101, 0, 10, 10),
                new GameRecipeSlots.Rect(0, 99, 10, 10), new GameRecipeSlots.Rect(0, 0, 0, 0))) {
            var value = GameRecipeHeaders.clippedCopy("category", viewport, area, () -> { fail("hidden text read"); return null; });
            assertEquals(new GameRecipeHeaders.Label("category", "clipped", null), value);
        }
    }
    @Test void exactRoundedCenterAndShadowBoundsPreserveOmissions() throws Exception {
        var viewport = new GameRecipeSlots.Rect(0, 0, 100, 100);
        var visible = GameRecipeHeaders.clippedCopy("category", viewport, new GameRecipeSlots.Rect(0, 0, 99, 9),
            () -> new GameRecipeHeaders.Measured(TITLE, 98));
        assertEquals(TITLE, visible); // (99-98)/2 rounds up; shadow ends at 100.
        var clipped = GameRecipeHeaders.clippedCopy("category", viewport, new GameRecipeSlots.Rect(0, 0, 100, 9),
            () -> new GameRecipeHeaders.Measured(TITLE, 100));
        assertEquals("clipped", clipped.state()); assertNull(clipped.text());
        for (int width : new int[]{-1, 32769}) assertThrows(IOException.class, () ->
            GameRecipeHeaders.clippedCopy("category", viewport, new GameRecipeSlots.Rect(1, 1, 90, 10),
                () -> new GameRecipeHeaders.Measured(TITLE, width)));
        assertEquals("unsupported", GameRecipeHeaders.clippedCopy("category", viewport, new GameRecipeSlots.Rect(1, 1, 90, 10),
            () -> new GameRecipeHeaders.Measured(new GameRecipeHeaders.Label("category", "unsupported", null), 0)).state());
    }
}
