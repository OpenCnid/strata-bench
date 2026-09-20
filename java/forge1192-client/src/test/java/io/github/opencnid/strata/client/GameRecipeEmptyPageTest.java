package io.github.opencnid.strata.client;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.util.List;
import java.util.concurrent.atomic.AtomicLong;
import org.junit.jupiter.api.Test;

/** Synthetic native-loop witness. Does not claim transformed JEI or final pixel visibility. */
class GameRecipeEmptyPageTest {
    final AtomicLong clock = new AtomicLong();
    final GameRecipeRenderCapture capture = new GameRecipeRenderCapture(clock::get);
    final Object renderer = new Object(), iterator = new Object(), layout = new Object();
    final GameRecipeRenderCapture.Key key = new GameRecipeRenderCapture.Key(new Object(), new Object(), new Object(), 800, 600);
    void begin() throws IOException {
        capture.beginFrame(key); capture.headers(GameRecipePageTest.headers()); capture.controls(GameRecipePageTest.controls());
        capture.beginLayouts(renderer);
    }
    void finish() { capture.endLayouts(renderer); capture.finishFrame(key); }
    void empty() throws IOException { begin(); capture.layoutPredicate(renderer, iterator, false); finish(); }
    void unavailable() { assertThrows(IOException.class, () -> capture.copied(key)); }
    @Test void observedEmptyLoopRequiresNormalEndAndCompleteFrame() throws Exception {
        begin(); capture.layoutPredicate(renderer, iterator, false); unavailable(); capture.endLayouts(renderer); unavailable();
        capture.finishFrame(key); assertEquals(List.of(), capture.copied(key));
        assertEquals(2, capture.headers(key).size()); assertEquals(4, capture.controls(key).size());
        assertThrows(UnsupportedOperationException.class, () -> capture.copied(key).add(GameRecipePageTest.layout()));
    }
    @Test void missingPredicateOrMissingDrawNeverMeansEmpty() throws Exception {
        begin(); finish(); unavailable();
        begin(); capture.layoutPredicate(renderer, iterator, true); capture.layoutPredicate(renderer, iterator, false); finish(); unavailable();
        begin(); capture.drawn(layout, GameRecipePageTest.layout()); capture.layoutPredicate(renderer, iterator, false); finish(); unavailable();
    }
    @Test void everyPositivePredicateHasExactlyOneCompletedDrawAndATerminalFalse() throws Exception {
        begin(); capture.layoutPredicate(renderer, iterator, true); capture.drawn(layout, GameRecipePageTest.layout());
        capture.layoutPredicate(renderer, iterator, false); finish(); assertEquals(1, capture.copied(key).size());
        begin(); capture.layoutPredicate(renderer, iterator, true); capture.drawn(layout, GameRecipePageTest.layout()); finish(); unavailable();
        begin(); capture.layoutPredicate(renderer, iterator, true); capture.drawn(layout, GameRecipePageTest.layout());
        capture.drawn(new Object(), GameRecipePageTest.layout()); capture.layoutPredicate(renderer, iterator, false); finish(); unavailable();
    }
    @Test void replacedIteratorRendererOrNullIdentityCannotPublish() throws Exception {
        begin(); capture.layoutPredicate(new Object(), iterator, false); finish(); unavailable();
        begin(); capture.layoutPredicate(renderer, null, false); finish(); unavailable();
        begin(); capture.layoutPredicate(renderer, iterator, true); capture.drawn(layout, GameRecipePageTest.layout());
        capture.layoutPredicate(renderer, new Object(), false); finish(); unavailable();
    }
    @Test void repeatedOrLatePredicatesAndAbortedDrawRemainInvalid() throws Exception {
        for (int fault = 0; fault < 4; fault++) {
            begin(); capture.layoutPredicate(renderer, iterator, fault == 3);
            if (fault == 0) capture.layoutPredicate(renderer, iterator, false);
            if (fault == 1) capture.layoutPredicate(renderer, iterator, true);
            if (fault == 2) { capture.endLayouts(renderer); capture.layoutPredicate(renderer, iterator, false); }
            // fault 3 is an interrupted/throwing draw: no completed draw or terminal false.
            finish(); unavailable();
        }
    }
    @Test void emptyLoopRequiresBothHeaderAndControlEvidence() throws Exception {
        for (int missing = 0; missing < 3; missing++) {
            capture.beginFrame(key);
            if (missing == 0) capture.headers(GameRecipePageTest.headers());
            if (missing == 1) capture.controls(GameRecipePageTest.controls());
            capture.beginLayouts(renderer); capture.layoutPredicate(renderer, iterator, false); finish(); unavailable();
        }
    }
    @Test void emptyFramesExpireInvalidateAndProduceNewPrivateStamps() throws Exception {
        empty(); var first = capture.stamp(key); empty(); assertNotSame(first, capture.stamp(key));
        capture.invalidate(); unavailable(); empty(); clock.set(250_000_001); unavailable();
        clock.set(0); begin(); capture.layoutPredicate(renderer, iterator, false); clock.set(100_000_001); finish(); unavailable();
        clock.set(0); empty(); capture.beginFrame(key); unavailable();
    }
    @Test void sourceOrScreenGeometryChangeCannotReuseAnEmptyFrame() throws Exception {
        for (var changed : List.of(new GameRecipeRenderCapture.Key(new Object(), key.runtime(), key.origin(), 800, 600),
                new GameRecipeRenderCapture.Key(key.screen(), new Object(), key.origin(), 800, 600),
                new GameRecipeRenderCapture.Key(key.screen(), key.runtime(), new Object(), 800, 600),
                new GameRecipeRenderCapture.Key(key.screen(), key.runtime(), key.origin(), 801, 600))) {
            empty(); assertThrows(IOException.class, () -> capture.copied(changed)); unavailable();
            begin(); capture.layoutPredicate(renderer, iterator, false); capture.endLayouts(renderer); capture.finishFrame(changed); unavailable();
        }
    }
    @Test void newFramesResetWitnessAndDoNotRetainPreviousLayouts() throws Exception {
        begin(); capture.layoutPredicate(renderer, iterator, true); capture.drawn(layout, GameRecipePageTest.layout());
        capture.layoutPredicate(renderer, iterator, false); finish(); assertEquals(1, capture.copied(key).size());
        empty(); assertTrue(capture.copied(key).isEmpty());
        begin(); capture.layoutPredicate(renderer, new Object(), false); finish(); assertTrue(capture.copied(key).isEmpty());
    }
}
