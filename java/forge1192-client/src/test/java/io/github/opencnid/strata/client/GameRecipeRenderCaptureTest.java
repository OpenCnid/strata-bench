package io.github.opencnid.strata.client;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.util.List;
import java.util.concurrent.atomic.AtomicLong;
import org.junit.jupiter.api.Test;

/** Synthetic renderer event ordering and identities; no real JEI drawing claimed. */
class GameRecipeRenderCaptureTest {
    private final AtomicLong clock = new AtomicLong();
    private final GameRecipeRenderCapture capture = new GameRecipeRenderCapture(clock::get);
    private final Object screen = new Object(), runtime = new Object(), origin = new Object(), renderer = new Object();
    private final Object first = new Object(), second = new Object();
    private GameRecipeRenderCapture.Key key() { return new GameRecipeRenderCapture.Key(screen, runtime, origin, 800, 600); }
    private void frame() {
        capture.beginFrame(key()); capture.beginLayouts(renderer); capture.layoutPredicate(renderer, renderer, true); capture.drawn(first); capture.layoutPredicate(renderer, renderer, true); capture.drawn(second);
        capture.layoutPredicate(renderer, renderer, false); capture.endLayouts(renderer); capture.finishFrame(key());
    }
    private void unavailable() {
        assertEquals("GAME_RECIPE_RENDER_UNAVAILABLE", assertThrows(IOException.class, () -> capture.read(key())).getMessage());
    }
    @Test void requiresCompletedWholeScreenFrameAndKeepsNativeOrder() throws Exception {
        unavailable(); capture.beginFrame(key()); capture.beginLayouts(renderer); capture.layoutPredicate(renderer, renderer, true); capture.drawn(first);
        unavailable(); capture.layoutPredicate(renderer, renderer, true); capture.drawn(second); capture.layoutPredicate(renderer, renderer, false); capture.endLayouts(renderer); unavailable();
        capture.finishFrame(key()); assertEquals(List.of(first, second), capture.read(key()));
        assertThrows(UnsupportedOperationException.class, () -> capture.read(key()).clear());
    }
    @Test void missingDrawHooksOrMissingReturnCannotPublish() {
        capture.beginFrame(key()); capture.finishFrame(key()); unavailable();
        capture.beginFrame(key()); capture.beginLayouts(renderer); capture.layoutPredicate(renderer, renderer, false); capture.endLayouts(renderer); capture.finishFrame(key()); unavailable();
        capture.beginFrame(key()); capture.beginLayouts(renderer); capture.layoutPredicate(renderer, renderer, true); capture.drawn(first); capture.finishFrame(key()); unavailable();
    }
    @Test void newOrAbortedFrameInvalidatesPreviouslyCompleteContents() throws Exception {
        frame(); assertEquals(2, capture.read(key()).size());
        capture.beginFrame(key()); unavailable();
        capture.beginLayouts(renderer); capture.layoutPredicate(renderer, renderer, true); capture.drawn(first); capture.invalidate();
        capture.layoutPredicate(renderer, renderer, false); capture.endLayouts(renderer); capture.finishFrame(key()); unavailable();
        frame(); assertEquals(2, capture.read(key()).size());
    }
    @Test void nestedOrRepeatedDrawLoopsRejectInsteadOfPublishingPartialPage() {
        for (boolean nested : new boolean[]{true, false}) {
            capture.beginFrame(key()); capture.beginLayouts(renderer); capture.layoutPredicate(renderer, renderer, true); capture.drawn(first);
            if (!nested) { capture.layoutPredicate(renderer, renderer, false); capture.endLayouts(renderer); }
            capture.beginLayouts(new Object()); capture.layoutPredicate(renderer, renderer, true); capture.drawn(second); capture.layoutPredicate(renderer, renderer, false); capture.endLayouts(renderer);
            capture.finishFrame(key()); unavailable();
        }
    }
    @Test void unpairedReturnsOutsideLoopAndDuplicateLayoutsReject() {
        capture.beginFrame(key()); capture.layoutPredicate(renderer, renderer, true); capture.drawn(first); capture.beginLayouts(renderer); capture.layoutPredicate(renderer, renderer, false); capture.endLayouts(renderer); capture.finishFrame(key()); unavailable();
        capture.beginFrame(key()); capture.beginLayouts(renderer); capture.layoutPredicate(renderer, renderer, true); capture.drawn(first); capture.layoutPredicate(renderer, renderer, false); capture.endLayouts(new Object()); capture.finishFrame(key()); unavailable();
        capture.beginFrame(key()); capture.beginLayouts(renderer); capture.layoutPredicate(renderer, renderer, true); capture.drawn(first); capture.layoutPredicate(renderer, renderer, true); capture.drawn(first); capture.layoutPredicate(renderer, renderer, false); capture.endLayouts(renderer); capture.finishFrame(key()); unavailable();
        capture.beginFrame(key()); capture.beginLayouts(renderer); capture.layoutPredicate(renderer, renderer, true); capture.drawn(first); capture.layoutPredicate(renderer, renderer, false); capture.endLayouts(renderer); capture.layoutPredicate(renderer, renderer, true); capture.drawn(second); capture.finishFrame(key()); unavailable();
    }
    @Test void screenRuntimeOriginAndGeometryChangesInvalidateOnCompletionAndRead() {
        for (var changed : List.of(
                new GameRecipeRenderCapture.Key(new Object(), runtime, origin, 800, 600),
                new GameRecipeRenderCapture.Key(screen, new Object(), origin, 800, 600),
                new GameRecipeRenderCapture.Key(screen, runtime, new Object(), 800, 600),
                new GameRecipeRenderCapture.Key(screen, runtime, origin, 801, 600),
                new GameRecipeRenderCapture.Key(screen, runtime, origin, 800, 601))) {
            capture.beginFrame(key()); capture.beginLayouts(renderer); capture.layoutPredicate(renderer, renderer, true); capture.drawn(first); capture.layoutPredicate(renderer, renderer, false); capture.endLayouts(renderer);
            capture.finishFrame(changed); unavailable();
            frame(); assertThrows(IOException.class, () -> capture.read(changed)); unavailable();
        }
    }
    @Test void boundedRetentionAndSlowOrRegressedClockReject() throws Exception {
        frame(); clock.set(GameRecipeRenderCapture.MAX_AGE_NANOS); assertEquals(2, capture.read(key()).size());
        clock.incrementAndGet(); unavailable();
        for (long elapsed : new long[]{-1, GameRecipeRenderCapture.MAX_FRAME_NANOS + 1}) {
            clock.set(0); capture.beginFrame(key()); capture.beginLayouts(renderer); capture.layoutPredicate(renderer, renderer, true); capture.drawn(first);
            capture.layoutPredicate(renderer, renderer, false); capture.endLayouts(renderer); clock.set(elapsed); capture.finishFrame(key()); unavailable();
        }
        clock.set(100); frame(); clock.set(99); unavailable();
    }
    @Test void maximumLayoutsAcceptedOverflowIsNotTruncated() throws Exception {
        for (int count : new int[]{32, 33}) {
            capture.beginFrame(key()); capture.beginLayouts(renderer);
            for (int i = 0; i < count; i++) { capture.layoutPredicate(renderer, renderer, true); capture.drawn(new Object()); }
            capture.layoutPredicate(renderer, renderer, false); capture.endLayouts(renderer); capture.finishFrame(key());
            if (count == 32) assertEquals(32, capture.read(key()).size()); else unavailable();
        }
    }
    @Test void invalidKeysAndExplicitResetCannotRestoreOldData() {
        for (var bad : List.of(new GameRecipeRenderCapture.Key(null, runtime, origin, 800, 600),
                new GameRecipeRenderCapture.Key(screen, null, origin, 800, 600),
                new GameRecipeRenderCapture.Key(screen, runtime, null, 800, 600),
                new GameRecipeRenderCapture.Key(screen, runtime, origin, 0, 600),
                new GameRecipeRenderCapture.Key(screen, runtime, origin, 800, 32769))) {
            frame(); capture.beginFrame(bad); capture.beginLayouts(renderer); capture.layoutPredicate(renderer, renderer, true); capture.drawn(first);
            capture.layoutPredicate(renderer, renderer, false); capture.endLayouts(renderer); capture.finishFrame(bad); unavailable();
        }
        frame(); capture.clear(); unavailable(); capture.finishFrame(key()); unavailable();
    }
    @Test void readDoesNotInvokeAnythingOnOpaqueLayoutObjects() throws Exception {
        Object opaque = new Object() { public String toString() { throw new AssertionError("No content inspection"); } };
        capture.beginFrame(key()); capture.beginLayouts(renderer); capture.layoutPredicate(renderer, renderer, true); capture.drawn(opaque); capture.layoutPredicate(renderer, renderer, false); capture.endLayouts(renderer);
        capture.finishFrame(key()); assertSame(opaque, capture.read(key()).get(0));
    }
}
