package io.github.opencnid.strata.client;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.atomic.AtomicLong;
import org.junit.jupiter.api.Test;

/** Synthetic button callbacks; no authentic GUI input is performed. */
class GameRecipeControlsTest {
    static final GameRecipeSlots.Rect VIEW = new GameRecipeSlots.Rect(0, 0, 100, 100);
    static final GameRecipeSlots.Rect BOX = new GameRecipeSlots.Rect(10, 10, 10, 10);
    static List<GameRecipeControls.Control> render(GameRecipeControls controls) throws Exception {
        controls.begin(VIEW);
        for (int i = 0; i < 4; i++) {
            Object button = new Object(); final boolean enabled = i % 2 == 0;
            controls.beginControl(button, BOX, () -> enabled); controls.endControl(button, BOX, () -> enabled);
        }
        return controls.finish();
    }
    @Test void actualOrderAndEnabledStatesAreImmutableWithoutWidgetExport() throws Exception {
        var controls = new GameRecipeControls(); var rows = render(controls);
        assertEquals(GameRecipeControls.KINDS, rows.stream().map(GameRecipeControls.Control::kind).toList());
        assertEquals(List.of("enabled", "disabled", "enabled", "disabled"), rows.stream().map(GameRecipeControls.Control::state).toList());
        assertThrows(UnsupportedOperationException.class, rows::clear);
        for (var row : rows) assertEquals(java.util.Set.of("kind", "state"), row.json().keySet());
        assertThrows(IOException.class, controls::finish);
        controls.clear(); assertEquals(4, render(controls).size());
    }
    @Test void incompleteNestedDuplicateAndWrongButtonDrawsCannotPublish() throws Exception {
        var controls = new GameRecipeControls(); var button = new Object();
        assertThrows(IOException.class, controls::finish); controls.begin(VIEW);
        controls.beginControl(button, BOX, () -> true);
        assertThrows(IOException.class, () -> controls.beginControl(new Object(), BOX, () -> true));
        assertThrows(IOException.class, controls::finish);
        assertThrows(IOException.class, () -> controls.endControl(new Object(), BOX, () -> true));
        controls.endControl(button, BOX, () -> true);
        assertThrows(IOException.class, () -> controls.beginControl(button, BOX, () -> true));
        assertThrows(IOException.class, controls::finish);
        controls.clear(); render(controls);
        assertThrows(IOException.class, () -> controls.beginControl(button, BOX, () -> true));
    }
    @Test void changedBoundsAndChangedEnabledStateReject() throws Exception {
        for (boolean move : List.of(true, false)) {
            var controls = new GameRecipeControls(); var button = new Object(); controls.begin(VIEW);
            controls.beginControl(button, BOX, () -> true);
            assertThrows(IOException.class, () -> controls.endControl(button,
                move ? new GameRecipeSlots.Rect(11, 10, 10, 10) : BOX, () -> move));
        }
    }
    @Test void clippedGeometryNeverReadsEnabledFlags() throws Exception {
        var controls = new GameRecipeControls(); controls.begin(VIEW);
        for (var area : List.of(new GameRecipeSlots.Rect(-1, 0, 10, 10), new GameRecipeSlots.Rect(101, 0, 10, 10),
                new GameRecipeSlots.Rect(99, 0, 10, 10), new GameRecipeSlots.Rect(0, 0, 0, 0))) {
            var button = new Object();
            GameRecipeSlots.Reader<Boolean> hidden = () -> { fail("hidden enabled state read"); return null; };
            controls.beginControl(button, area, hidden); controls.endControl(button, area, hidden);
        }
        for (var row : controls.finish()) assertEquals("clipped", row.state());
    }
    @Test void invalidGeometryNullStateAndMalformedRowsReject() throws Exception {
        var controls = new GameRecipeControls(); controls.begin(VIEW);
        assertThrows(IOException.class, () -> controls.beginControl(new Object(), new GameRecipeSlots.Rect(0, 0, -1, 10), () -> true));
        assertThrows(IOException.class, () -> controls.beginControl(new Object(), BOX, () -> null));
        assertThrows(IOException.class, () -> new GameRecipeControls.Control(new Object(), "private", "enabled", BOX).json());
        assertThrows(IOException.class, () -> new GameRecipeControls.Control(new Object(), "page_next", "unknown", BOX).json());
        assertThrows(IOException.class, () -> new GameRecipeControls.Control(null, "page_next", "enabled", BOX).json());
    }
    @Test void copiedControlsRequireSameCompleteFreshFrame() throws Exception {
        var clock = new AtomicLong(); var capture = new GameRecipeRenderCapture(clock::get);
        var owner = new Object(); var key = new GameRecipeRenderCapture.Key(owner, owner, owner, 100, 100);
        capture.beginFrame(key); capture.beginLayouts(owner); capture.layoutPredicate(owner, owner, true); capture.drawn(owner); capture.layoutPredicate(owner, owner, false); capture.endLayouts(owner); capture.finishFrame(key);
        assertThrows(IOException.class, () -> capture.controls(key));
        capture.beginFrame(key); var rows = render(new GameRecipeControls()); capture.controls(rows);
        capture.beginLayouts(owner); capture.layoutPredicate(owner, owner, true); capture.drawn(owner); capture.layoutPredicate(owner, owner, false); capture.endLayouts(owner); capture.finishFrame(key);
        assertEquals(rows, capture.controls(key)); clock.set(250_000_001);
        assertThrows(IOException.class, () -> capture.controls(key));
    }
    @Test void wrongControlOrderOrLateControlsPoisonCapture() throws Exception {
        var capture = new GameRecipeRenderCapture(); var owner = new Object();
        var key = new GameRecipeRenderCapture.Key(owner, owner, owner, 100, 100);
        var rows = new ArrayList<>(render(new GameRecipeControls())); java.util.Collections.reverse(rows);
        capture.beginFrame(key); assertThrows(IOException.class, () -> capture.controls(rows));
        capture.beginLayouts(owner); capture.layoutPredicate(owner, owner, true); capture.drawn(owner); capture.layoutPredicate(owner, owner, false); capture.endLayouts(owner); capture.finishFrame(key);
        assertThrows(IOException.class, () -> capture.controls(key));
        capture.beginFrame(key); capture.beginLayouts(owner);
        assertThrows(IOException.class, () -> capture.controls(GameRecipePageTest.controls()));
    }
    @Test void controlStateChangesBindPageDigestButNeverExposeGeometry() throws Exception {
        var source = new GameRecipePageTest.Source(); var page = new GameRecipePage(); var before = page.page(source);
        var rows = new ArrayList<>(source.controls); var first = rows.get(0);
        rows.set(0, new GameRecipeControls.Control(first.widget(), first.kind(), "disabled", first.area())); source.controls = rows;
        var after = page.page(source); assertNotEquals(before.get("revision"), after.get("revision"));
        for (var row : after.getAsJsonArray("controls")) assertEquals(java.util.Set.of("kind", "state"), row.getAsJsonObject().keySet());
        source.controls = rows.subList(1, 4); assertThrows(IOException.class, () -> page.page(source));
    }
}
