package io.github.opencnid.strata.client;

import static org.junit.jupiter.api.Assertions.*;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

/** Real bounded motor, router witness and lane journal; synthetic screens, render timing and button callbacks. */
class GameRecipeNavigationTest {
    static class Port implements GameRecipeNavigation.Port {
        final GameRecipeInputTest.Fixture input = new GameRecipeInputTest.Fixture();
        final GameRecipeInput.Ownership ownership = new GameRecipeInput.Ownership();
        Object screen = input.screen, frame = new Object();
        final Object chapter = new Object(), quest = new Object();
        long source = 1, generation = 2, revision = 3;
        String page = KeyOptions.sha256("page"), context = KeyOptions.sha256("layout");
        List<GameRecipeControls.Control> controls = input.controls();
        int previews, executes, resets, reads, raceRead = -1;
        boolean unavailable, forbidden, noHooks, failPreview, failExecute, failReset, autoRender = true, preserveFrame;
        public GameRecipeNavigation.State read() throws IOException {
            if (forbidden) throw new IOException("GAME_QUEST_CHANGED");
            if (++reads == raceRead) page = KeyOptions.sha256("raced");
            return new GameRecipeNavigation.State(new GameQuestScreen.Snapshot(new GameQuestScreen.Frame(
                source, screen, chapter, quest, "0000000000000001", "0000000000000002", context, "task_recipes"),
                generation, revision), page, frame, controls);
        }
        public void ready(GameRecipeNavigation.State state) throws IOException {
            ownership.requireIdle(); if (unavailable) throw new IOException("GAME_RECIPE_INPUT_UNCONFIRMED");
        }
        public void checkControl(GameRecipeNavigation.State state, int index) throws IOException {
            if (forbidden) throw new IOException("GAME_QUEST_INPUT_BUSY");
        }
        public void preview(GameRecipeNavigation.State state, int index) throws IOException {
            previews++; var gesture = ownership.acquire(input.binding, screen, index);
            if (noHooks) { gesture.prepare("SIMULATE"); gesture.finish(true); }
            else input.route(gesture, index, "SIMULATE");
            if (failPreview) throw new IOException("INJECTED_AFTER_PREVIEW");
        }
        public void requirePreview() throws IOException { ownership.current().requirePreview(); }
        public void execute(GameRecipeNavigation.State state, int index) throws IOException {
            executes++; input.route(ownership.current(), index, "EXECUTE");
            if (!preserveFrame) frame = null;
            if (failExecute) throw new IOException("INJECTED_AFTER_EXECUTE");
        }
        public GameRecipeNavigation.State after() throws IOException {
            if (forbidden) throw new IOException("GAME_QUEST_CHANGED");
            if (autoRender && frame == null) frame = new Object();
            return frame == null ? null : read();
        }
        void release() throws IOException {
            ownership.release(router -> { assertSame(input.router, router); resets++; if (failReset) throw new IOException("RESET_FAILED"); });
        }
    }
    static JsonObject action(GameRecipeNavigation.State state, String control) {
        var result = new JsonObject(); result.addProperty("kind", "recipe_navigate"); result.addProperty("source", "jei");
        result.addProperty("control", control); result.addProperty("source_generation", state.screen().frame().source());
        result.addProperty("expected_screen_generation", state.screen().generation()); result.addProperty("expected_screen_revision", state.screen().revision());
        result.addProperty("expected_page_revision", state.page()); return result;
    }
    static GameRecipeNavigation.Request request(Port port, String control) throws IOException {
        return GameRecipeNavigation.Request.read(action(port.read(), control));
    }
    @Test void fourControlsPreviewThenExecuteOnSeparateTicksAndWaitForFreshRender() throws Exception {
        for (String control : GameRecipeControls.KINDS) {
            var port = new Port(); var charges = new AtomicInteger();
            GameActionLane.Emitter emit = op -> { charges.incrementAndGet(); op.run(); };
            var motor = GameRecipeNavigation.start(port, request(port, control), emit);
            assertEquals(1, port.previews); assertEquals(0, port.executes); assertEquals(1, charges.get());
            assertFalse(motor.tick(emit)); assertEquals(1, port.executes); assertEquals(2, charges.get());
            assertTrue(motor.tick(emit)); assertEquals(3, charges.get());
            assertTrue(motor.tick(op -> fail("terminal motor replayed"))); port.release();
            assertEquals(1, port.resets); assertNull(port.ownership.current());
        }
    }
    @Test void unchangedContentInANewFrameConfirmsInputButOldFrameDoesNot() throws Exception {
        var port = new Port(); port.autoRender = false; port.preserveFrame = true;
        var motor = GameRecipeNavigation.start(port, request(port, "page_next"), GameActionLane.Operation::run);
        assertFalse(motor.tick(GameActionLane.Operation::run));
        assertFalse(motor.tick(GameActionLane.Operation::run)); assertFalse(motor.tick(GameActionLane.Operation::run));
        port.frame = new Object(); assertTrue(motor.tick(GameActionLane.Operation::run));
        assertEquals(1, port.executes); port.release();
    }
    @Test void missingFramesHaveABoundedChargedWaitAndCannotReplay() throws Exception {
        var port = new Port(); port.autoRender = false; var charges = new AtomicInteger();
        GameActionLane.Emitter emit = op -> { charges.incrementAndGet(); op.run(); };
        var motor = GameRecipeNavigation.start(port, request(port, "page_next"), emit); assertFalse(motor.tick(emit));
        for (int i = 0; i < 200; i++) assertFalse(motor.tick(emit));
        assertEquals("GAME_RECIPE_RENDER_TIMEOUT", assertThrows(IOException.class, () -> motor.tick(emit)).getMessage());
        assertEquals(202, charges.get()); assertEquals(1, port.executes);
        port.frame = new Object(); assertThrows(IOException.class, () -> motor.tick(op -> fail("failed motor replayed"))); port.release();
    }
    @Test void stalePageSourceScreenAndClippedDisabledTargetsRejectBeforeInput() throws Exception {
        for (int fault = 0; fault < 8; fault++) {
            var port = new Port(); var request = request(port, "page_next");
            switch (fault) {
                case 0 -> port.source++;
                case 1 -> port.generation++;
                case 2 -> port.revision++;
                case 3 -> port.page = KeyOptions.sha256("changed");
                case 4, 5 -> { var rows = new ArrayList<>(port.controls); var old = rows.get(2);
                    rows.set(2, new GameRecipeControls.Control(old.widget(), old.kind(), fault == 4 ? "disabled" : "clipped", old.area())); port.controls = rows; }
                case 6 -> port.forbidden = true;
                case 7 -> port.unavailable = true;
                default -> fail();
            }
            assertThrows(IOException.class, () -> GameRecipeNavigation.start(port, request, op -> fail("input emitted")), "fault=" + fault);
            assertEquals(0, port.previews); assertEquals(0, port.executes);
        }
    }
    @Test void pageRacesBeforeAndInsideChargedDispatchReject() throws Exception {
        var port = new Port(); var request = request(port, "category_next"); port.raceRead = port.reads + 2;
        assertThrows(IOException.class, () -> GameRecipeNavigation.start(port, request, op -> fail("input emitted")));
        var second = new Port(); var req = request(second, "page_previous");
        assertThrows(IOException.class, () -> GameRecipeNavigation.start(second, req, op -> { second.page = KeyOptions.sha256("raced"); op.run(); }));
        assertEquals(0, second.previews);
    }
    @Test void pageOrGeometryChangeBetweenPhasesCannotExecute() throws Exception {
        for (boolean geometry : List.of(false, true)) {
            var port = new Port(); var motor = GameRecipeNavigation.start(port, request(port, "page_next"), GameActionLane.Operation::run);
            if (geometry) { var rows = new ArrayList<>(port.controls); var row = rows.get(2);
                rows.set(2, new GameRecipeControls.Control(row.widget(), row.kind(), row.state(), new GameRecipeSlots.Rect(5, 5, 10, 10))); port.controls = rows;
            } else port.page = KeyOptions.sha256("changed");
            assertThrows(IOException.class, () -> motor.tick(GameActionLane.Operation::run));
            assertEquals(1, port.previews); assertEquals(0, port.executes); port.release();
        }
    }
    @Test void missingPreviewHooksAndCompetingInputFailWithoutReleaseClick() throws Exception {
        var missing = new Port(); missing.noHooks = true;
        assertThrows(IOException.class, () -> GameRecipeNavigation.start(missing, request(missing, "page_next"), GameActionLane.Operation::run));
        missing.release(); assertEquals(0, missing.executes); assertEquals(1, missing.resets);
        var port = new Port(); var motor = GameRecipeNavigation.start(port, request(port, "page_next"), GameActionLane.Operation::run);
        port.ownership.current().invalidate(); assertThrows(IOException.class, () -> motor.tick(GameActionLane.Operation::run));
        port.release(); assertEquals(0, port.executes);
    }
    @Test void freshFrameCannotSubstituteAnotherSourceScreenOrOrigin() throws Exception {
        for (int fault = 0; fault < 5; fault++) {
            var port = new Port(); var motor = GameRecipeNavigation.start(port, request(port, "page_next"), GameActionLane.Operation::run);
            motor.tick(GameActionLane.Operation::run);
            switch (fault) {
                case 0 -> port.source++;
                case 1 -> port.screen = new Object();
                case 2 -> port.context = KeyOptions.sha256("resize");
                case 3 -> port.generation++;
                case 4 -> port.forbidden = true;
                default -> fail();
            }
            assertThrows(IOException.class, () -> motor.tick(GameActionLane.Operation::run)); assertEquals(1, port.executes); port.release();
        }
    }
    @Test void strictActionRejectsRawCoordinatesSelectorsCoercionAndOutOfBounds(@TempDir Path root) throws Exception {
        var port = new Port(); var original = action(port.read(), "page_next"); var fixture = new GameActionLaneTest.Fixture(root, 100);
        for (String patch : List.of("{\"kind\":\"quest_navigate\"}", "{\"source\":\"admin\"}", "{\"control\":\"history\"}",
                "{\"mouse_x\":0}", "{\"widget\":\"private\"}", "{\"source_generation\":true}",
                "{\"expected_screen_generation\":-1}", "{\"expected_screen_revision\":1.0}",
                "{\"expected_page_revision\":\"bad\"}", "{\"expected_screen_revision\":9007199254740992}")) {
            var changed = original.deepCopy(); JsonParser.parseString(patch).getAsJsonObject().entrySet().forEach(e -> changed.add(e.getKey(), e.getValue()));
            var batch = fixture.batch(1, "navigate", 1); batch.add("action", changed);
            assertThrows(IOException.class, () -> new GameBatch(batch), patch);
        }
        var valid = fixture.batch(1, "navigate", 1); valid.add("action", original); new GameBatch(valid);
        valid.addProperty("duration_ms", 10001); assertThrows(IOException.class, () -> new GameBatch(valid));
    }
    static JsonObject prepareLane(GameActionLaneTest.Fixture fixture, Port port) throws IOException {
        var action = action(port.read(), "page_next"); var request = GameRecipeNavigation.Request.read(action);
        fixture.port.customMotor = emit -> GameRecipeNavigation.start(port, request, emit);
        fixture.port.customRelease = port::release;
        var batch = fixture.batch(1, "navigate", 1); batch.add("action", action); return batch;
    }
    @Test void realLaneChargesBothPhasesWaitAndReleaseAndDeduplicatesAfterRestart(@TempDir Path root) throws Exception {
        var fixture = new GameActionLaneTest.Fixture(root, 100); var port = new Port(); var batch = prepareLane(fixture, port);
        try (var lane = fixture.open()) {
            fixture.arm(lane, 1); fixture.deliver(lane); lane.accept(batch); fixture.start(lane); lane.tick(); lane.tick();
            assertEquals("emitted", lane.status("navigate").get("status").getAsString());
            assertEquals(4, lane.status("navigate").get("emitted_events").getAsInt());
            assertNull(port.ownership.current()); lane.accept(batch); assertEquals(1, port.executes);
        }
        try (var lane = fixture.open()) { assertEquals("emitted", lane.accept(batch).get("status").getAsString()); }
        assertEquals(1, port.previews); assertEquals(1, port.executes);
    }
    @Test void realLaneCancellationBeforeBetweenAndAfterPhasesNeverReplays(@TempDir Path root) throws Exception {
        for (int stage = 0; stage < 3; stage++) {
            var fixture = new GameActionLaneTest.Fixture(Files.createDirectory(root.resolve("stage-" + stage)), 100);
            var port = new Port(); var batch = prepareLane(fixture, port);
            try (var lane = fixture.open()) {
                fixture.arm(lane, 1); fixture.deliver(lane); lane.accept(batch);
                if (stage > 0) fixture.start(lane); if (stage > 1) lane.tick();
                lane.cancel("navigate"); var receipt = lane.status("navigate");
                assertEquals("cancelled", receipt.get("status").getAsString()); assertTrue(lane.health().get("fenced").getAsBoolean());
                assertEquals(stage == 0 ? 0 : 1, port.previews); assertEquals(stage == 2 ? 1 : 0, port.executes);
                assertNull(port.ownership.current()); lane.accept(batch); assertEquals(stage == 2 ? 1 : 0, port.executes);
            }
        }
    }
    @Test void realLaneDeadlineBudgetAndFailedResetRetainCostsAndFence(@TempDir Path root) throws Exception {
        for (int fault = 0; fault < 3; fault++) {
            var fixture = new GameActionLaneTest.Fixture(Files.createDirectory(root.resolve("fault-" + fault)), fault == 1 ? 5 : 100);
            var port = new Port(); if (fault == 1) port.autoRender = false;
            var batch = prepareLane(fixture, port);
            try (var lane = fixture.open()) {
                fixture.arm(lane, 1); fixture.deliver(lane); lane.accept(batch); fixture.start(lane);
                if (fault == 0) { fixture.time.advance(5001); lane.tick(); }
                else if (fault == 1) { lane.tick(); lane.tick(); lane.tick(); }
                else { port.failReset = true; lane.cancel("navigate"); }
                assertTrue(lane.health().get("fenced").getAsBoolean());
                assertNotEquals("emitted", lane.status("navigate").get("status").getAsString());
                assertTrue(lane.status("navigate").get("attempted_events").getAsInt() >= 1);
                if (fault == 2) assertTrue(lane.status("navigate").get("emitted_events").isJsonNull());
                if (fault == 2) { assertNotNull(port.ownership.current()); port.failReset = false; port.release(); }
                else assertNull(port.ownership.current());
                int before = port.executes; lane.accept(batch); assertEquals(before, port.executes);
            }
        }
    }
    @Test void actualFrameWitnessChangesOnlyOnCompletedFrames() throws Exception {
        var capture = new GameRecipeRenderCapture(() -> 0); Object object = new Object();
        var key = new GameRecipeRenderCapture.Key(object, object, object, 800, 600);
        assertThrows(IOException.class, () -> capture.stamp(key));
        capture.beginFrame(key); capture.beginLayouts(object); capture.layoutPredicate(object, object, true); capture.drawn(object); capture.layoutPredicate(object, object, false); capture.endLayouts(object); capture.finishFrame(key);
        Object before = capture.stamp(key); assertSame(before, capture.stamp(key)); capture.invalidate();
        assertThrows(IOException.class, () -> capture.stamp(key));
        capture.beginFrame(key); capture.beginLayouts(object); capture.layoutPredicate(object, object, true); capture.drawn(object); capture.layoutPredicate(object, object, false); capture.endLayouts(object); capture.finishFrame(key);
        assertNotSame(before, capture.stamp(key));
    }
    @Test void partialEffectsAreUnknownAfterCallbackFailureAndNeverRetried(@TempDir Path root) throws Exception {
        for (boolean afterExecute : List.of(false, true)) {
            var fixture = new GameActionLaneTest.Fixture(Files.createDirectory(root.resolve("after-execute-" + afterExecute)), 100);
            var port = new Port(); port.failPreview = !afterExecute; port.failExecute = afterExecute;
            var batch = prepareLane(fixture, port);
            try (var lane = fixture.open()) {
                fixture.arm(lane, 1); fixture.deliver(lane); lane.accept(batch); fixture.start(lane);
                if (afterExecute) lane.tick();
                var receipt = lane.status("navigate"); assertEquals("unknown", receipt.get("status").getAsString());
                assertTrue(receipt.get("emitted_events").isJsonNull()); assertTrue(receipt.get("attempted_events").getAsInt() >= 2);
                assertEquals(1, port.previews); assertEquals(afterExecute ? 1 : 0, port.executes); assertNull(port.ownership.current());
                lane.accept(batch); assertEquals(afterExecute ? 1 : 0, port.executes);
            }
            try (var lane = fixture.open()) { assertEquals("unknown", lane.accept(batch).get("status").getAsString()); }
            assertEquals(1, port.previews); assertEquals(afterExecute ? 1 : 0, port.executes);
        }
    }
    @Test void laneRequiresEnoughBudgetForBothPhasesOneFrameCheckAndReleaseBeforeInput(@TempDir Path root) throws Exception {
        var fixture = new GameActionLaneTest.Fixture(root, 4); var port = new Port(); var batch = prepareLane(fixture, port);
        try (var lane = fixture.open()) {
            fixture.arm(lane, 1); fixture.deliver(lane);
            assertEquals("BUDGET_EXHAUSTED", assertThrows(IOException.class, () -> lane.accept(batch)).getMessage());
            assertEquals(0, port.previews); assertEquals(0, port.executes);
            assertFalse(Files.readString(root.resolve("game-actions.jsonl")).contains("\"kind\":\"intent\""));
        }
    }
}
