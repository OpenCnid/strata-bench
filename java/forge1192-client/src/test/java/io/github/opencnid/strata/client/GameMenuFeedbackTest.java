package io.github.opencnid.strata.client;

import java.io.IOException;
import java.util.List;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class GameMenuFeedbackTest {
    final GameInventory.View empty = new GameInventory.View(List.of(GameInventory.Stack.EMPTY), GameInventory.Stack.EMPTY, -1);
    final GameInventory.View changed = new GameInventory.View(List.of(new GameInventory.Stack("minecraft:stone", 1, "")), GameInventory.Stack.EMPTY, -1);
    @Test void onlyCurrentMenuAndActualAppliedContentsResolveUncertainty() throws Exception {
        var feedback = new GameMenuFeedback<Object>(); Object menu = new Object();
        feedback.markDirty(menu, 2); var request = feedback.request(menu, 2);
        assertTrue(feedback.uncertain()); assertNull(feedback.capture(3)); assertNull(feedback.reply(request.id, menu));
        assertSame(request, feedback.capture(2)); assertNull(feedback.capture(2));
        feedback.apply(request, new Object(), changed, changed); assertTrue(feedback.uncertain());
        feedback.apply(request, menu, changed, changed); assertFalse(feedback.uncertain());
        assertEquals(changed, feedback.reply(request.id, menu));
    }
    @Test void cancellationCannotAuthorizeOldContinuationButRealReplyStillReconcilesState() throws Exception {
        var feedback = new GameMenuFeedback<Object>(); Object menu = new Object();
        feedback.markDirty(menu, 2); var request = feedback.request(menu, 2); feedback.cancel();
        assertTrue(feedback.uncertain()); assertThrows(IOException.class, () -> feedback.reply(request.id, menu));
        assertSame(request, feedback.capture(2)); feedback.apply(request, menu, changed, changed);
        assertFalse(feedback.uncertain()); assertThrows(IOException.class, () -> feedback.reply(request.id, menu));
    }
    @Test void failedRefreshEmissionAndStaleCallbacksCannotClearANewerMutationFence() {
        var feedback = new GameMenuFeedback<Object>(); Object menu = new Object();
        feedback.markDirty(menu, 2); var old = feedback.capture(2);
        feedback.cancel(); assertTrue(feedback.uncertain()); // no refresh command was emitted
        feedback.markDirty(menu, 2); var current = feedback.request(menu, 2);
        feedback.apply(old, menu, empty, empty); assertTrue(feedback.uncertain());
        feedback.apply(current, menu, changed, changed); assertFalse(feedback.uncertain());
    }
    @Test void unappliedOrMalformedContentsStayFencedAndClosingDropsLateCallbacks() {
        var feedback = new GameMenuFeedback<Object>(); Object menu = new Object();
        feedback.markDirty(menu, 2); var request = feedback.request(menu, 2);
        feedback.apply(request, menu, changed, empty); assertTrue(feedback.uncertain());
        feedback.apply(request, menu, changed, changed); assertTrue(feedback.uncertain());
        assertThrows(IOException.class, () -> feedback.reply(request.id, menu));
        var next = feedback.request(menu, 2); feedback.invalid(next);
        assertThrows(IOException.class, () -> feedback.reply(next.id, menu)); assertTrue(feedback.uncertain());
        feedback.close(); feedback.apply(next, menu, changed, changed);
        assertNull(feedback.capture(2)); assertTrue(feedback.uncertain());
    }
}
