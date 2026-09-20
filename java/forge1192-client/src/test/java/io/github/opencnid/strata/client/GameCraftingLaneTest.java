package io.github.opencnid.strata.client;

import com.google.gson.JsonObject;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import static org.junit.jupiter.api.Assertions.*;

/** Durable lane and real craft motor, synthetic menu feedback/effects. */
class GameCraftingLaneTest {
    static class Fixture implements AutoCloseable {
        final GameActionLaneTest.Fixture base;
        final GameCraftingTest.Port menu = new GameCraftingTest.Port(1);
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
                public GameActionLane.Motor begin(GameBatch batch, JsonObject snapshot, GameActionLane.Emitter emitter) throws IOException {
                    return GameCrafting.start(menu, 1, emitter);
                }
                public void releaseInputs() throws IOException { base.port.releaseInputs(); }
            };
            lane = new GameActionLane(root, GameActionLaneTest.PROFILE, base.authority, runtime, base.time);
            base.arm(lane, 1); base.deliver(lane);
            request = base.batch(1, "crafting", 1); request.add("action", action());
            lane.accept(request); lane.tick(); base.time.advance(50); lane.tick();
        }
        void step() throws IOException { base.time.advance(50); lane.tick(); }
        public void close() throws IOException { lane.close(); }
    }
    static JsonObject action() throws IOException {
        return SettingsJson.readGame("{\"kind\":\"craft\",\"recipe_id\":\"test:expert\",\"count\":1,\"window_id\":0,\"expected_window_revision\":1}");
    }
    @Test void cancellationPreservesFilledGridAndNeverReplaysRecipe(@TempDir Path root) throws Exception {
        try (var f = new Fixture(root, 100)) {
            assertEquals(1, f.menu.fills); assertEquals(0, f.menu.takes);
            f.step(); var receipt = f.lane.cancel("crafting");
            assertEquals("cancelled", receipt.get("status").getAsString()); assertTrue(receipt.get("release_confirmed").getAsBoolean());
            assertEquals(1, f.menu.slots.get(1).count()); assertEquals(0, f.menu.takes);
            assertEquals(receipt, f.lane.accept(f.request)); f.menu.ack(); f.step(); assertEquals(0, f.menu.takes);
            assertEquals(1, Files.readAllLines(root.resolve("game-actions.jsonl")).stream().filter(x -> x.contains("\"kind\":\"intent\"")).count());
        }
    }
    @Test void exhaustedWaitBudgetRetainsFillAndReleaseCharges(@TempDir Path root) throws Exception {
        try (var f = new Fixture(root, 8)) {
            for (int i = 0; i < 20 && !f.lane.health().get("fenced").getAsBoolean(); i++) f.step();
            var receipt = f.lane.status("crafting");
            assertEquals("BUDGET_EXHAUSTED", receipt.get("error_code").getAsString());
            assertEquals("unknown", receipt.get("status").getAsString()); assertTrue(receipt.get("release_confirmed").getAsBoolean());
            assertEquals(8, f.lane.health().get("attempted_primitive_events").getAsInt());
            assertEquals(1, f.menu.fills); assertEquals(0, f.menu.takes);
        }
    }
    @Test void deadlineAfterTakingOutputRetainsCursorWithoutInventingRollback(@TempDir Path root) throws Exception {
        try (var f = new Fixture(root, 100)) {
            f.menu.ack(); f.step(); assertEquals(1, f.menu.takes);
            f.base.time.advance(5000); f.lane.tick();
            var receipt = f.lane.status("crafting"); assertEquals("DEADLINE_EXCEEDED", receipt.get("error_code").getAsString());
            assertEquals(f.menu.output, f.menu.cursor); assertEquals(1, f.menu.clicks);
            assertTrue(receipt.get("release_confirmed").getAsBoolean());
        }
    }
    @Test void strictCraftEnvelopeRejectsImplicitChainsAndInvalidCounts(@TempDir Path root) throws Exception {
        var base = new GameActionLaneTest.Fixture(root, 100); var request = base.batch(1, "craft", 1); request.add("action", action());
        assertEquals("craft", new GameBatch(request).kind);
        for (int count : new int[]{0, 65}) {
            request.getAsJsonObject("action").addProperty("count", count); assertThrows(IOException.class, () -> new GameBatch(request));
        }
        request.add("action", action()); request.getAsJsonObject("action").addProperty("gather", true);
        assertThrows(IOException.class, () -> new GameBatch(request));
        request.add("action", action()); request.addProperty("duration_ms", 10001);
        assertThrows(IOException.class, () -> new GameBatch(request));
    }
}
