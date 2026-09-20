package io.github.opencnid.strata.client;

import com.google.gson.JsonObject;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import static org.junit.jupiter.api.Assertions.*;

/** Real durable action lane with a synthetic walking body; no native physics claim. */
class GameMovementLaneTest {
    static class Fixture implements AutoCloseable {
        final GameActionLaneTest.Fixture base;
        final GameMovementTest.Walker walker = new GameMovementTest.Walker();
        final GameActionLane lane;
        final JsonObject request;
        Fixture(Path root, int budget) throws Exception {
            base = new GameActionLaneTest.Fixture(root, budget);
            var runtime = new GameActionLane.RuntimePort() {
                public void requireClientThread() throws IOException { base.port.requireClientThread(); }
                public String bodyFingerprint() { return base.port.body; }
                public long connectionGeneration() { return base.port.generation; }
                public JsonObject snapshot(String id) throws IOException { return base.port.snapshot(id); }
                public void resetObservations() { base.port.resetObservations(); }
                public void validate(GameBatch batch, JsonObject snapshot) throws IOException { base.port.validate(batch, snapshot); }
                private GameActionLane.Emitter charged(GameActionLane.Emitter emitter) {
                    return operation -> emitter.invoke(() -> walker.emit(operation));
                }
                public GameActionLane.Motor begin(GameBatch batch, JsonObject snapshot, GameActionLane.Emitter emitter) throws IOException {
                    var motor = GameMovement.start(walker,
                        List.of(GameMovementTest.p(1.5, .5), GameMovementTest.p(2.5, .5), GameMovementTest.p(3.5, .5)),
                        GameBatch.target(batch.action), GameBatch.tolerance(batch.action), charged(emitter));
                    return next -> motor.tick(charged(next));
                }
                public void releaseInputs() throws IOException { walker.forward = false; base.port.releaseInputs(); }
            };
            lane = new GameActionLane(root, GameActionLaneTest.PROFILE, base.authority, runtime, base.time);
            base.arm(lane, 1); base.deliver(lane);
            request = base.batch(1, "movement", 1); request.add("action", action());
            lane.accept(request); lane.tick();
        }
        void step() throws IOException { base.time.advance(50); walker.step(); lane.tick(); }
        void walking() throws IOException {
            for (int i = 0; i < 15 && !walker.forward; i++) step();
            assertTrue(walker.forward);
        }
        public void close() throws IOException { lane.close(); }
    }
    static JsonObject action() throws IOException {
        return SettingsJson.readGame("{\"kind\":\"move_to\",\"target\":{\"x\":3.5,\"y\":64,\"z\":0.5},\"tolerance\":0.1}");
    }
    @Test void cancellationReleasesWalkingWithoutReplayingItsDurableIntent(@TempDir Path root) throws Exception {
        try (var f = new Fixture(root, 100)) {
            f.walking(); f.step(); double momentum = f.walker.vx;
            int events = f.walker.events;
            var receipt = f.lane.cancel("movement");
            assertEquals("cancelled", receipt.get("status").getAsString()); assertTrue(receipt.get("release_confirmed").getAsBoolean());
            assertFalse(f.walker.forward); assertEquals(momentum, f.walker.vx); // Release never rewinds normal momentum.
            assertEquals(receipt, f.lane.accept(f.request)); f.step();
            assertEquals(events, f.walker.events);
            long intents = Files.readAllLines(root.resolve("game-actions.jsonl")).stream().filter(line -> line.contains("\"kind\":\"intent\"")).count();
            assertEquals(1, intents);
        }
    }
    @Test void budgetExhaustionDuringWalkingPreservesChargedNeutralAndReleaseTicks(@TempDir Path root) throws Exception {
        try (var f = new Fixture(root, 17)) {
            f.walking();
            for (int i = 0; i < 30 && !f.lane.health().get("fenced").getAsBoolean(); i++) f.step();
            var receipt = f.lane.status("movement");
            assertEquals("BUDGET_EXHAUSTED", receipt.get("error_code").getAsString());
            assertEquals("unknown", receipt.get("status").getAsString()); assertFalse(f.walker.forward);
            assertEquals(17, f.lane.health().get("attempted_primitive_events").getAsLong());
            assertEquals(f.walker.events + 1, receipt.get("attempted_events").getAsLong());
            assertTrue(receipt.get("release_confirmed").getAsBoolean());
        }
    }
    @Test void deadlineAndDamageStopAnActiveWalkWithoutAnotherForwardDispatch(@TempDir Path root) throws Exception {
        for (String fault : List.of("deadline", "damage")) {
            Path directory = Files.createDirectory(root.resolve(fault));
            try (var f = new Fixture(directory, 100)) {
                f.walking(); int events = f.walker.events;
                if (fault.equals("deadline")) { f.base.time.advance(5000); f.lane.tick(); }
                else { f.walker.health--; f.step(); }
                var receipt = f.lane.status("movement");
                assertEquals(fault.equals("deadline") ? "DEADLINE_EXCEEDED" : "NAVIGATION_STATE_CHANGED", receipt.get("error_code").getAsString());
                assertTrue(receipt.get("release_confirmed").getAsBoolean()); assertFalse(f.walker.forward);
                assertEquals(events, f.walker.events);
            }
        }
    }
    @Test void strictMovementEnvelopeAdmitsThirtySecondsAndRejectsBadToleranceAndExtraFields(@TempDir Path root) throws Exception {
        var f = new GameActionLaneTest.Fixture(root, 100); var batch = f.batch(1, "movement", 1);
        batch.add("action", action()); batch.addProperty("duration_ms", 30000);
        assertEquals(30000, new GameBatch(batch).duration);
        batch.addProperty("duration_ms", 30001); assertThrows(IOException.class, () -> new GameBatch(batch));
        batch.addProperty("duration_ms", 30000);
        for (double invalid : new double[]{0, -1, 1.01, Double.NaN}) {
            batch.getAsJsonObject("action").addProperty("tolerance", invalid);
            assertThrows(IOException.class, () -> new GameBatch(batch));
        }
        batch.add("action", action()); batch.getAsJsonObject("action").addProperty("tolerance", "0.1");
        assertThrows(IOException.class, () -> new GameBatch(batch));
        batch.add("action", action()); batch.getAsJsonObject("action").addProperty("dig", true);
        assertThrows(IOException.class, () -> new GameBatch(batch));
        batch.add("action", f.batch(1, "look", 1).getAsJsonObject("action"));
        assertThrows(IOException.class, () -> new GameBatch(batch)); // Non-movement remains capped at ten seconds.
    }
}
