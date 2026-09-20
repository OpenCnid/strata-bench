package io.github.opencnid.strata.client;

import static org.junit.jupiter.api.Assertions.*;
import com.google.gson.JsonObject;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

/** Ordinary Back callback and rendered results are synthetic; the real motor/lane/journal are exercised. */
class GameRecipeHistoryTest {
    static final class Port extends GameRecipeNavigationTest.Port {
        final ArrayDeque<String> history = new ArrayDeque<>();
        int calls; boolean failAfter;
        public void checkHistory(GameRecipeNavigation.State state) throws IOException {
            ownership.requireIdle(); if (forbidden) throw new IOException("GAME_QUEST_CHANGED");
        }
        public void historyBack(GameRecipeNavigation.State state) throws IOException {
            checkHistory(state); calls++;
            if (!history.isEmpty()) page = history.pop();
            if (!preserveFrame) frame = null;
            if (failAfter) throw new IOException("INJECTED_AFTER_HISTORY");
        }
    }
    static GameRecipeNavigation.Request request(Port port) throws IOException { return GameRecipeNavigationTest.request(port, "history_back"); }
    static GameActionLane.Motor start(Port port, GameActionLane.Emitter emitter) throws IOException {
        return GameRecipeNavigation.start(port, request(port), emitter);
    }
    static JsonObject batch(GameActionLaneTest.Fixture fixture, Port port) throws IOException {
        var action = GameRecipeNavigationTest.action(port.read(), "history_back"); var request = GameRecipeNavigation.Request.read(action);
        fixture.port.customMotor = emit -> GameRecipeNavigation.start(port, request, emit); fixture.port.customRelease = port::release;
        var batch = fixture.batch(1, "history", 1); batch.add("action", action); return batch;
    }
    @Test void backInvokesOnceAndWaitsForFreshPageWithoutMousePhasesOrClosing() throws Exception {
        var port = new Port(); Object screen = port.screen; var target = KeyOptions.sha256("previous"); port.history.push(target);
        var charges = new AtomicInteger(); GameActionLane.Emitter emit = op -> { charges.incrementAndGet(); op.run(); };
        var motor = start(port, emit); assertEquals(1, port.calls); assertEquals(target, port.page);
        assertEquals(0, port.previews); assertEquals(0, port.executes); assertNull(port.ownership.current());
        assertSame(screen, port.screen); assertEquals(1, charges.get());
        assertTrue(motor.tick(emit)); assertEquals(2, charges.get()); assertTrue(motor.tick(op -> fail("replayed callback")));
        assertEquals(1, port.calls); port.release();
    }
    @Test void exhaustedHistoryIsANoOpThatKeepsTheScreenAndStillCharges() throws Exception {
        var port = new Port(); String before = port.page; Object screen = port.screen;
        var motor = start(port, GameActionLane.Operation::run);
        assertTrue(motor.tick(GameActionLane.Operation::run)); assertEquals(before, port.page); assertSame(screen, port.screen);
        assertEquals(1, port.calls); assertTrue(port.history.isEmpty()); assertEquals(0, port.executes);
    }
    @Test void historyIsIndependentOfDrawnPageButtonsAndDoesNotReadAHiddenStackSelector() throws Exception {
        var port = new Port(); var controls = new ArrayList<>(port.controls);
        for (int i = 0; i < controls.size(); i++) { var old = controls.get(i);
            controls.set(i, new GameRecipeControls.Control(old.widget(), old.kind(), "disabled", old.area())); }
        port.controls = controls; port.unavailable = true; // No page-button input routing is used.
        var motor = start(port, GameActionLane.Operation::run); assertTrue(motor.tick(GameActionLane.Operation::run)); assertEquals(1, port.calls);
        var value = GameRecipeNavigationTest.action(port.read(), "history_back"); value.addProperty("history_index", 0);
        assertThrows(IOException.class, () -> GameRecipeNavigation.Request.read(value));
    }
    @Test void unsupportedHistoryPortAndPendingPageGestureCannotInvokeBack() throws Exception {
        var unsupported = new GameRecipeNavigationTest.Port();
        assertEquals("GAME_RECIPE_HISTORY_UNSUPPORTED", assertThrows(IOException.class, () -> GameRecipeNavigation.start(unsupported,
            GameRecipeNavigationTest.request(unsupported, "history_back"), op -> fail("emission"))).getMessage());
        var busy = new Port(); busy.ownership.acquire(busy.input.binding, busy.screen, 0);
        assertThrows(IOException.class, () -> start(busy, op -> fail("emission"))); assertEquals(0, busy.calls); busy.release();
    }
    @Test void staleOrRacedPageAndScreenAuthorityRejectBeforeCallback() throws Exception {
        for (int fault = 0; fault < 6; fault++) {
            var port = new Port(); var request = request(port);
            switch (fault) {
                case 0 -> port.source++;
                case 1 -> port.generation++;
                case 2 -> port.revision++;
                case 3 -> port.page = KeyOptions.sha256("changed");
                case 4 -> port.raceRead = port.reads + 2;
                case 5 -> port.forbidden = true;
                default -> fail();
            }
            assertThrows(IOException.class, () -> GameRecipeNavigation.start(port, request, op -> fail("emission")));
            assertEquals(0, port.calls);
        }
        var port = new Port(); var request = request(port);
        assertThrows(IOException.class, () -> GameRecipeNavigation.start(port, request, op -> { port.revision++; op.run(); }));
        assertEquals(0, port.calls);
    }
    @Test void noOpCannotConfirmAgainstTheOldFrameAndMissingFramesRemainBounded() throws Exception {
        var port = new Port(); port.preserveFrame = true; port.autoRender = false;
        var motor = start(port, GameActionLane.Operation::run); assertFalse(motor.tick(GameActionLane.Operation::run));
        port.frame = new Object(); assertTrue(motor.tick(GameActionLane.Operation::run)); assertEquals(1, port.calls);
        var missing = new Port(); missing.autoRender = false; var waits = new AtomicInteger();
        var stalled = start(missing, GameActionLane.Operation::run);
        for (int i = 0; i < 200; i++) assertFalse(stalled.tick(op -> { waits.incrementAndGet(); op.run(); }));
        assertEquals("GAME_RECIPE_RENDER_TIMEOUT", assertThrows(IOException.class, () -> stalled.tick(op -> fail("extra wait"))).getMessage());
        assertEquals(200, waits.get()); assertEquals(1, missing.calls);
    }
    @Test void sourceScreenOrOriginChangeAfterBackCannotBeConfirmedOrRetried() throws Exception {
        for (int fault = 0; fault < 3; fault++) {
            var port = new Port(); var motor = start(port, GameActionLane.Operation::run);
            if (fault == 0) port.screen = new Object(); if (fault == 1) port.source++; if (fault == 2) port.context = KeyOptions.sha256("changed");
            assertThrows(IOException.class, () -> motor.tick(GameActionLane.Operation::run));
            assertThrows(IOException.class, () -> motor.tick(op -> fail("retry"))); assertEquals(1, port.calls);
        }
    }
    @Test void laneChargesCallbackWaitReleaseAndDeduplicatesAnExhaustedHistory(@TempDir Path root) throws Exception {
        var fixture = new GameActionLaneTest.Fixture(root, 4); var port = new Port(); var batch = batch(fixture, port);
        try (var lane = fixture.open()) {
            fixture.arm(lane, 1); fixture.deliver(lane); lane.accept(batch); fixture.start(lane); lane.tick();
            var receipt = lane.status("history"); assertEquals("emitted", receipt.get("status").getAsString());
            assertEquals(3, receipt.get("emitted_events").getAsInt()); assertEquals(4, lane.health().get("attempted_primitive_events").getAsInt());
            lane.accept(batch); assertEquals(1, port.calls); assertNotNull(port.screen);
        }
        try (var lane = fixture.open()) { assertEquals("emitted", lane.accept(batch).get("status").getAsString()); }
        assertEquals(1, port.calls);
    }
    @Test void historyAdmissionNeedsThreeUnitsAndDoesNotDispatchWhenShort(@TempDir Path root) throws Exception {
        var fixture = new GameActionLaneTest.Fixture(root, 3); var port = new Port(); var batch = batch(fixture, port);
        try (var lane = fixture.open()) {
            fixture.arm(lane, 1); fixture.deliver(lane);
            assertEquals("BUDGET_EXHAUSTED", assertThrows(IOException.class, () -> lane.accept(batch)).getMessage()); assertEquals(0, port.calls);
        }
    }
    @Test void cancellationBeforeAndAfterBackNeverClosesOrReplays(@TempDir Path root) throws Exception {
        for (boolean dispatch : List.of(false, true)) {
            var fixture = new GameActionLaneTest.Fixture(Files.createDirectory(root.resolve("dispatch-" + dispatch)), 100);
            var port = new Port(); Object screen = port.screen; var batch = batch(fixture, port);
            try (var lane = fixture.open()) {
                fixture.arm(lane, 1); fixture.deliver(lane); lane.accept(batch); if (dispatch) fixture.start(lane);
                lane.cancel("history"); assertEquals("cancelled", lane.status("history").get("status").getAsString());
                assertTrue(lane.health().get("fenced").getAsBoolean()); assertSame(screen, port.screen);
                assertEquals(dispatch ? 1 : 0, port.calls); assertEquals(0, port.executes); lane.accept(batch); assertEquals(dispatch ? 1 : 0, port.calls);
            }
        }
    }
    @Test void aThrownCallbackRetainsItsPartialEffectAndUnknownOutcomeAfterRestart(@TempDir Path root) throws Exception {
        var fixture = new GameActionLaneTest.Fixture(root, 100); var port = new Port(); port.failAfter = true;
        var previous = KeyOptions.sha256("earlier"); port.history.push(previous); var batch = batch(fixture, port);
        try (var lane = fixture.open()) {
            fixture.arm(lane, 1); fixture.deliver(lane); lane.accept(batch); fixture.start(lane);
            var receipt = lane.status("history"); assertEquals("unknown", receipt.get("status").getAsString());
            assertTrue(receipt.get("emitted_events").isJsonNull()); assertEquals(2, receipt.get("attempted_events").getAsInt());
            assertEquals(previous, port.page); assertTrue(port.history.isEmpty()); lane.accept(batch); assertEquals(1, port.calls);
        }
        try (var lane = fixture.open()) { assertEquals("unknown", lane.accept(batch).get("status").getAsString()); }
        assertEquals(1, port.calls);
    }
    @Test void deadlineExhaustionAndFailedSafetyReleaseFenceWithoutRepeatingBack(@TempDir Path root) throws Exception {
        for (int fault = 0; fault < 3; fault++) {
            var fixture = new GameActionLaneTest.Fixture(Files.createDirectory(root.resolve("fault-" + fault)), fault == 1 ? 4 : 100);
            var port = new Port(); port.autoRender = false; var batch = batch(fixture, port);
            try (var lane = fixture.open()) {
                fixture.arm(lane, 1); fixture.deliver(lane); lane.accept(batch); fixture.start(lane);
                if (fault == 0) { fixture.time.advance(5001); lane.tick(); }
                if (fault == 1) { lane.tick(); lane.tick(); }
                if (fault == 2) { fixture.port.failRelease = true; lane.cancel("history"); fixture.port.failRelease = false; }
                assertTrue(lane.health().get("fenced").getAsBoolean()); assertNotEquals("emitted", lane.status("history").get("status").getAsString());
                if (fault == 2) assertFalse(lane.status("history").get("release_confirmed").getAsBoolean());
                lane.accept(batch); assertEquals(1, port.calls); assertNotNull(port.screen);
            }
        }
    }
}
