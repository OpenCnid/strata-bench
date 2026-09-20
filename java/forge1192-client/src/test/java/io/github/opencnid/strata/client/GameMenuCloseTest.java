package io.github.opencnid.strata.client;

import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.nio.file.Path;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import static org.junit.jupiter.api.Assertions.*;

/** Synthetic inventory resources/feedback; no real menu or Forge hook claim. */
class GameMenuCloseTest {
    static GameInventory.Stack item(String name, int count) { return new GameInventory.Stack("test:" + name, count, "components"); }
    static GameMenuClose.State state(Map<Integer, GameInventory.Stack> items, GameInventory.Stack... returning) {
        var inventory = new ArrayList<GameInventory.Stack>();
        for (int i = 0; i < 41; i++) inventory.add(items.getOrDefault(i, GameInventory.Stack.EMPTY));
        return new GameMenuClose.State(inventory, List.of(returning));
    }
    static final class Port implements GameMenuClose.Port {
        GameMenuClose.State current, prediction, feedback;
        boolean valid = true; int closes, refreshes, charges, limit = 64; long ticket;
        Port(GameMenuClose.State before, GameMenuClose.State after) { current = before; prediction = after; }
        public void validate() throws IOException { if (!valid) throw new IOException("REVISION_CONFLICT"); }
        public GameMenuClose.State read() { return current; }
        public int capacity(int slot, GameInventory.Stack item) { return limit; }
        public void close() { closes++; current = prediction; }
        public long requestSync() { refreshes++; feedback = null; return ++ticket; }
        public GameMenuClose.State reply(long expected) { assertEquals(ticket, expected); return feedback; }
        void ack() { feedback = current; }
        void emit(GameActionLane.Operation op) throws IOException { charges++; op.run(); }
    }
    @Test void normalReturnMergesAndPreservesCursorGridResourcesAfterActualFeedback() throws Exception {
        var before = state(Map.of(4, item("stone", 63)), item("stone", 2), item("bucket", 1));
        var after = state(Map.of(4, item("stone", 64), 5, item("stone", 1), 6, item("bucket", 1)));
        var p = new Port(before, after); var motor = GameMenuClose.start(p, p::emit);
        for (int i = 0; i < 20; i++) assertFalse(motor.tick(p::emit));
        assertEquals(22, p.charges); assertEquals(1, p.closes); assertEquals(1, p.refreshes);
        p.ack(); assertTrue(motor.tick(p::emit));
    }
    @Test void existingOffhandCanMergeButEmptyOffhandIsNotAnEquipmentDestination() throws Exception {
        var full = new java.util.HashMap<Integer, GameInventory.Stack>();
        for (int i = 4; i < 40; i++) full.put(i, item("filled", 64));
        full.put(40, item("stone", 63)); var before = state(full, item("stone", 1));
        full.put(40, item("stone", 64)); var p = new Port(before, state(full));
        var motor = GameMenuClose.start(p, p::emit); p.ack(); assertTrue(motor.tick(p::emit));
        full.remove(40); var noRoom = new Port(state(full, item("stone", 1)), state(full));
        assertThrows(IOException.class, () -> GameMenuClose.start(noRoom, noRoom::emit)); assertEquals(0, noRoom.closes);
    }
    @Test void capacityReservationAccountsForAllUnstackableReturnsBeforeAnyClose() {
        var full = new java.util.HashMap<Integer, GameInventory.Stack>();
        for (int i = 5; i < 40; i++) full.put(i, item("filled", 64));
        var p = new Port(state(full, item("tool", 1), item("other_tool", 1)), state(full)); p.limit = 1;
        assertThrows(IOException.class, () -> GameMenuClose.start(p, p::emit)); assertEquals(0, p.charges);
    }
    @Test void lossGiftChangedComponentsAndRemainingCursorCannotConfirmClose() throws Exception {
        var before = state(Map.of(), item("stone", 2));
        for (var after : List.of(state(Map.of(4, item("stone", 1))), state(Map.of(4, item("stone", 3))),
                state(Map.of(4, new GameInventory.Stack("test:stone", 2, "other"))), state(Map.of(), item("stone", 2)))) {
            var p = new Port(before, after); var motor = GameMenuClose.start(p, p::emit); p.ack();
            assertThrows(IOException.class, () -> motor.tick(p::emit)); assertEquals(1, p.closes);
        }
    }
    @Test void armorChangesFailEvenWhenResourceTotalsAreConserved() throws Exception {
        var p = new Port(state(Map.of(0, item("helmet", 1))), state(Map.of(4, item("helmet", 1))));
        var motor = GameMenuClose.start(p, p::emit); p.ack(); assertThrows(IOException.class, () -> motor.tick(p::emit));
    }
    @Test void replacedMenuOrInterveningInventoryInvalidatesFeedback() throws Exception {
        for (boolean replaced : List.of(false, true)) {
            var p = new Port(state(Map.of(), item("stone", 1)), state(Map.of(4, item("stone", 1))));
            var motor = GameMenuClose.start(p, p::emit); p.ack();
            if (replaced) p.valid = false; else p.current = state(Map.of(5, item("stone", 1)));
            assertThrows(IOException.class, () -> motor.tick(p::emit)); assertEquals(1, p.closes);
        }
    }
    @Test void exhaustedRefreshChargeDoesNotReopenOrReplayClosedMenu() {
        var p = new Port(state(Map.of()), state(Map.of()));
        assertThrows(IOException.class, () -> GameMenuClose.start(p, op -> {
            if (++p.charges == 2) throw new IOException("BUDGET_EXHAUSTED"); op.run();
        }));
        assertEquals(1, p.closes); assertEquals(0, p.refreshes);
    }
    @Test void strictEnvelopeAndUnsupportedResourceBoundsReject(@TempDir Path root) throws Exception {
        var base = new GameActionLaneTest.Fixture(root, 100); var batch = base.batch(1, "close", 1);
        batch.add("action", SettingsJson.readGame("{\"kind\":\"close_window\",\"window_id\":3,\"expected_window_revision\":4}"));
        assertEquals("close_window", new GameBatch(batch).kind);
        batch.getAsJsonObject("action").addProperty("drop", true); assertThrows(IOException.class, () -> new GameBatch(batch));
        var p = new Port(state(Map.of(), item("oversize", 65)), state(Map.of()));
        assertThrows(IOException.class, () -> GameMenuClose.start(p, p::emit)); assertEquals(0, p.charges);
    }
    @Test void durableLaneCancelDeadlineAndBudgetRetainCloseWithoutReplay(@TempDir Path root) throws Exception {
        for (String fault : List.of("cancel", "deadline", "budget")) {
            var directory = java.nio.file.Files.createDirectory(root.resolve(fault));
            var base = new GameActionLaneTest.Fixture(directory, fault.equals("budget") ? 8 : 100);
            var p = new Port(state(Map.of(), item("stone", 1)), state(Map.of(4, item("stone", 1))));
            var runtime = new GameActionLane.RuntimePort() {
                public void requireClientThread() throws IOException { base.port.requireClientThread(); }
                public String bodyFingerprint() { return base.port.body; }
                public long connectionGeneration() { return base.port.generation; }
                public com.google.gson.JsonObject snapshot(String id) throws IOException { return base.port.snapshot(id); }
                public void resetObservations() { base.port.resetObservations(); }
                public void validate(GameBatch b, com.google.gson.JsonObject s) throws IOException { base.port.validate(b, s); }
                public GameActionLane.Motor begin(GameBatch b, com.google.gson.JsonObject s, GameActionLane.Emitter emit) throws IOException { return GameMenuClose.start(p, emit); }
                public void releaseInputs() throws IOException { base.port.releaseInputs(); }
            };
            try (var lane = new GameActionLane(directory, GameActionLaneTest.PROFILE, base.authority, runtime, base.time)) {
                base.arm(lane, 1); base.deliver(lane); var request = base.batch(1, "close", 1);
                request.add("action", SettingsJson.readGame("{\"kind\":\"close_window\",\"window_id\":3,\"expected_window_revision\":4}"));
                lane.accept(request); lane.tick(); base.time.advance(50); lane.tick(); assertEquals(1, p.closes);
                if (fault.equals("cancel")) lane.cancel("close");
                else if (fault.equals("deadline")) { base.time.advance(5000); lane.tick(); }
                else for (int i = 0; i < 20 && !lane.health().get("fenced").getAsBoolean(); i++) { base.time.advance(50); lane.tick(); }
                var receipt = lane.status("close"); assertTrue(receipt.get("release_confirmed").getAsBoolean());
                assertEquals(receipt, lane.accept(request)); p.ack(); lane.tick(); assertEquals(1, p.closes);
                assertEquals(item("stone", 1), p.current.inventory().get(4));
            }
        }
    }
}
