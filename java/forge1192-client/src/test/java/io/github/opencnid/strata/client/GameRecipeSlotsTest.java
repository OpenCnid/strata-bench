package io.github.opencnid.strata.client;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;

/** Synthetic draw callbacks exercise visibility-before-content and actual-operand copying. */
class GameRecipeSlotsTest {
    private final GameRecipeSlots capture = new GameRecipeSlots();
    private final Object layout = new Object(), first = new Object(), second = new Object(), selected = new Object();
    private final GameRecipeSlots.Rect viewport = new GameRecipeSlots.Rect(0, 0, 800, 600);
    private final GameRecipeSlots.Rect area = new GameRecipeSlots.Rect(100, 100, 200, 100);
    private final GameRecipeSlots.Rect rectangle = new GameRecipeSlots.Rect(1, 1, 16, 16);
    private final GameRecipeSlots.Display item = new GameRecipeSlots.Display("item", "minecraft:stone", 2);
    private void begin(List<?> expected) throws IOException { capture.begin(layout, viewport, area, "minecraft:crafting", expected); }
    private void slot(Object identity, GameRecipeSlots.Display value) throws IOException {
        capture.beginSlot(identity, rectangle, () -> "input"); capture.selection(identity, selected);
        capture.ingredient(identity, selected, () -> value); capture.endSlot(identity);
    }
    @Test void copiesDisplayedOperandsInNativeOrderAndFreezesLists() throws Exception {
        var expected = new ArrayList<>(List.of(first, second)); begin(expected); expected.clear();
        slot(first, item); slot(second, new GameRecipeSlots.Display("fluid", "minecraft:water", 1000));
        var result = capture.finish(layout);
        assertEquals("minecraft:crafting", result.category()); assertFalse(result.clipped());
        assertEquals(List.of(0, 1), result.slots().stream().map(GameRecipeSlots.Slot::index).toList());
        assertEquals("fluid", result.slots().get(1).display().kind());
        assertThrows(UnsupportedOperationException.class, () -> result.slots().clear());
        var json = result.json(); json.getAsJsonArray("slots").remove(0);
        assertEquals(2, result.json().getAsJsonArray("slots").size());
    }
    @Test void emptySlotRequiresObservedEmptySelection() throws Exception {
        begin(List.of(first)); capture.beginSlot(first, rectangle, () -> "output");
        assertThrows(IOException.class, () -> capture.endSlot(first));
        assertThrows(IOException.class, () -> capture.finish(layout));
        begin(List.of(first)); capture.beginSlot(first, rectangle, () -> "output"); capture.selection(first, null);
        capture.endSlot(first); assertEquals("empty", capture.finish(layout).slots().get(0).display().kind());
    }
    @Test void onlyCurrentSlotCanAcceptSelectionReturnHook() throws Exception {
        assertFalse(capture.activeSlot(first)); begin(List.of(first));
        assertFalse(capture.activeSlot(first)); capture.beginSlot(first, rectangle, () -> "input");
        assertTrue(capture.activeSlot(first)); assertFalse(capture.activeSlot(second));
        capture.selection(first, null); capture.endSlot(first); assertFalse(capture.activeSlot(first));
        capture.finish(layout); assertFalse(capture.activeSlot(first));
    }
    @Test void missingOperandHookCannotMisreportNonemptyAsEmpty() throws Exception {
        begin(List.of(first)); capture.beginSlot(first, rectangle, () -> "input"); capture.selection(first, selected);
        assertThrows(IOException.class, () -> capture.endSlot(first));
        assertThrows(IOException.class, () -> capture.finish(layout));
    }
    @Test void wrongRepeatedAndUnselectedOperandsRejectBeforeReader() throws Exception {
        for (int fault = 0; fault < 3; fault++) {
            begin(List.of(first)); capture.beginSlot(first, rectangle, () -> "input");
            if (fault > 0) capture.selection(first, selected);
            if (fault == 2) capture.ingredient(first, selected, () -> item);
            Object operand = fault == 1 ? new Object() : selected;
            assertThrows(IOException.class, () -> capture.ingredient(first, operand, () -> { throw new AssertionError("No reader"); }));
            assertThrows(IOException.class, () -> capture.finish(layout));
        }
    }
    @Test void offscreenPartialAndOutOfLayoutSlotsNeverReadRoleOrIngredient() throws Exception {
        assertTrue(viewport.intersects(area));
        assertFalse(viewport.intersects(new GameRecipeSlots.Rect(800, 0, 16, 16)));
        assertFalse(viewport.intersects(new GameRecipeSlots.Rect(0, -16, 16, 16)));
        assertFalse(viewport.intersects(new GameRecipeSlots.Rect(0, 0, 0, 16)));
        for (var rect : List.of(new GameRecipeSlots.Rect(-101, 0, 16, 16),
                new GameRecipeSlots.Rect(195, 0, 16, 16), new GameRecipeSlots.Rect(0, 0, 0, 16))) {
            begin(List.of(first));
            capture.beginSlot(first, rect, () -> { throw new AssertionError("Off-screen role"); });
            capture.selection(first, selected);
            capture.ingredient(first, selected, () -> { throw new AssertionError("Off-screen ingredient"); });
            capture.endSlot(first); var result = capture.finish(layout);
            assertTrue(result.clipped()); assertTrue(result.slots().isEmpty());
        }
        capture.begin(layout, new GameRecipeSlots.Rect(0, 0, 110, 110), area, "minecraft:crafting", List.of(first));
        capture.beginSlot(first, rectangle, () -> { throw new AssertionError("Viewport clipping before content"); });
        capture.selection(first, null); capture.endSlot(first); assertTrue(capture.finish(layout).clipped());
    }
    @Test void skippedSlotPreservesNativeIndicesAndUnsupportedMarker() throws Exception {
        begin(List.of(first, second)); capture.beginSlot(first, new GameRecipeSlots.Rect(-50, 0, 16, 16), () -> "input");
        capture.selection(first, null); capture.endSlot(first);
        slot(second, new GameRecipeSlots.Display("unsupported", null, 0));
        var result = capture.finish(layout); assertEquals(1, result.slots().get(0).index());
        assertEquals("unsupported", result.slots().get(0).display().kind());
        assertFalse(result.json().toString().contains("ingredient_type"));
    }
    @Test void identityOrderDuplicatesAndMissingDrawsCannotYieldPartialLayout() throws Exception {
        assertThrows(IOException.class, () -> begin(List.of(first, first)));
        begin(List.of(first, second)); assertThrows(IOException.class, () -> slot(second, item));
        assertThrows(IOException.class, () -> capture.finish(layout));
        begin(List.of(first, second)); slot(first, item); assertThrows(IOException.class, () -> capture.finish(layout));
        begin(List.of(first)); slot(first, item); assertThrows(IOException.class, () -> capture.finish(new Object()));
    }
    @Test void nestedLayoutAndUnfinishedSlotRejectThenFreshFrameRecovers() throws Exception {
        begin(List.of(first)); assertThrows(IOException.class, () -> begin(List.of(first)));
        assertThrows(IOException.class, () -> capture.finish(layout));
        begin(List.of(first)); capture.beginSlot(first, rectangle, () -> "input");
        assertThrows(IOException.class, () -> capture.finish(layout));
        begin(List.of(first)); slot(first, item); assertEquals(1, capture.finish(layout).slots().size());
    }
    @Test void failingContentReaderPoisonsWholeLayout() throws Exception {
        begin(List.of(first)); capture.beginSlot(first, rectangle, () -> "input"); capture.selection(first, selected);
        assertThrows(IOException.class, () -> capture.ingredient(first, selected, () -> { throw new IOException("HIDDEN"); }));
        assertThrows(IOException.class, () -> capture.endSlot(first)); assertThrows(IOException.class, () -> capture.finish(layout));
    }
    @Test void boundsRejectOversizedSlotsInvalidIdentifiersRolesAndCounts() throws Exception {
        var many = new ArrayList<>(); for (int i = 0; i < 129; i++) many.add(new Object());
        assertThrows(IOException.class, () -> begin(many));
        for (var bad : List.of(new GameRecipeSlots.Display("item", "minecraft:stone", 0),
                new GameRecipeSlots.Display("empty", "minecraft:stone", 1),
                new GameRecipeSlots.Display("unsupported", "private:id", 0),
                new GameRecipeSlots.Display("fluid", "../private", 1000))) assertThrows(IOException.class, bad::json);
        begin(List.of(first)); capture.beginSlot(first, rectangle, () -> "unknown"); capture.selection(first, null);
        assertThrows(IOException.class, () -> capture.endSlot(first)); assertThrows(IOException.class, () -> capture.finish(layout));
        assertThrows(IOException.class, () -> new GameRecipeSlots.Rect(Integer.MAX_VALUE, 0, 16, 16).validate());
    }
    @Test void completeFrameReturnsCopiesAndRejectsMixedOrExcessivePayloads() throws Exception {
        var frame = new GameRecipeRenderCapture(() -> 0);
        var key = new GameRecipeRenderCapture.Key(new Object(), new Object(), new Object(), 800, 600);
        begin(List.of(first)); slot(first, item); var copied = capture.finish(layout);
        frame.beginFrame(key); frame.beginLayouts(first); frame.layoutPredicate(first, first, true); frame.drawn(layout, copied); frame.layoutPredicate(first, first, false); frame.endLayouts(first); frame.finishFrame(key);
        assertEquals(List.of(copied), frame.copied(key));
        frame.beginFrame(key); frame.beginLayouts(first); frame.layoutPredicate(first, first, true); frame.drawn(layout, copied); frame.layoutPredicate(first, first, true); frame.drawn(second); frame.layoutPredicate(first, first, false); frame.endLayouts(first); frame.finishFrame(key);
        assertThrows(IOException.class, () -> frame.copied(key));
        var rows = new ArrayList<GameRecipeSlots.Slot>();
        for (int i = 0; i < 128; i++) rows.add(new GameRecipeSlots.Slot(i, "input", new GameRecipeSlots.Display("item", "minecraft:" + "x".repeat(220), 1)));
        frame.beginFrame(key); frame.beginLayouts(first); frame.layoutPredicate(first, first, true);
        assertThrows(IOException.class, () -> frame.drawn(layout, new GameRecipeSlots.Layout("minecraft:crafting", rows, false)));
        frame.endLayouts(first); frame.finishFrame(key); assertThrows(IOException.class, () -> frame.copied(key));
        frame.beginFrame(key); frame.beginLayouts(first); frame.layoutPredicate(first, first, true); frame.drawn(layout, copied); frame.layoutPredicate(first, first, true);
        assertThrows(IOException.class, () -> frame.drawn(second, new GameRecipeSlots.Layout("private/invalid", List.of(), false)));
        frame.endLayouts(first); frame.finishFrame(key); assertThrows(IOException.class, () -> frame.copied(key));
    }
}
