package io.github.opencnid.strata.client;

import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

/** Scripted native predictions and server replies, not Minecraft execution. */
class GameMachineInventoryTest {
    @Test void realLaneCancelAndDuplicateReceiptNeverReplayWaitingMachineInput(@org.junit.jupiter.api.io.TempDir java.nio.file.Path root) throws Exception {
        var f = new GameActionLaneTest.Fixture(root, 100);
        var p = new Port(view(CRUCIBLE, Map.of(), stack("minecraft:stone", 1)),
            view(CRUCIBLE, Map.of(0, stack("minecraft:stone", 1)), EMPTY));
        f.port.customMotor = emit -> GameMachineInventory.click(p, CRUCIBLE, 0, false, false, emit);
        try (var lane = f.open()) {
            f.arm(lane, 1); f.deliver(lane); var request = machineBatch(f);
            lane.accept(request); f.start(lane); lane.tick();
            assertEquals(1, p.clicks); assertEquals(1, p.refreshes);
            var cancelled = lane.cancel("machine-action");
            assertEquals("cancelled", cancelled.get("status").getAsString());
            assertTrue(cancelled.get("release_confirmed").getAsBoolean());
            assertEquals(4, cancelled.get("emitted_events").getAsInt()); // Click, refresh, wait, release.
            assertEquals(cancelled, lane.accept(request)); assertEquals(1, p.clicks);
        }
    }
    @Test void realLaneUnconfirmedOwnedTransferIsUnknownAndFenced(@org.junit.jupiter.api.io.TempDir java.nio.file.Path root) throws Exception {
        var f = new GameActionLaneTest.Fixture(root, 100);
        var before = view(CRUCIBLE, Map.of(), stack("minecraft:stone", 1));
        var p = new Port(before, view(CRUCIBLE, Map.of(0, stack("minecraft:stone", 1)), EMPTY));
        f.port.customMotor = emit -> GameMachineInventory.click(p, CRUCIBLE, 0, false, false, emit);
        try (var lane = f.open()) {
            f.arm(lane, 1); f.deliver(lane); var request = machineBatch(f);
            lane.accept(request); f.start(lane); p.ack(before); lane.tick();
            assertEquals("executing", lane.status("machine-action").get("status").getAsString());
            assertEquals(2, p.refreshes); assertEquals(1, p.clicks);
            p.ack(before); lane.tick(); // A second unchanged reply remains unknown.
            var status = lane.status("machine-action");
            assertEquals("unknown", status.get("status").getAsString());
            assertEquals("GAME_MACHINE_TRANSFER_UNCONFIRMED", status.get("error_code").getAsString());
            assertTrue(status.get("requires_resync").getAsBoolean()); assertTrue(lane.health().get("fenced").getAsBoolean());
            assertEquals(status, lane.accept(request)); assertEquals(1, p.clicks);
        }
    }
    @Test void realLaneDeadlineAndBudgetStopMachineWaitAndRetainCharges(@org.junit.jupiter.api.io.TempDir java.nio.file.Path root) throws Exception {
        for (boolean deadline : new boolean[]{false, true}) {
            var directory = java.nio.file.Files.createDirectory(root.resolve(deadline ? "deadline" : "budget"));
            var f = new GameActionLaneTest.Fixture(directory, deadline ? 100 : 4);
            var p = new Port(view(CRUCIBLE, Map.of(), stack("minecraft:stone", 1)),
                view(CRUCIBLE, Map.of(0, stack("minecraft:stone", 1)), EMPTY));
            f.port.customMotor = emit -> GameMachineInventory.click(p, CRUCIBLE, 0, false, false, emit);
            try (var lane = f.open()) {
                f.arm(lane, 1); f.deliver(lane); lane.accept(machineBatch(f)); f.start(lane);
                if (deadline) f.time.advance(5000);
                lane.tick(); var status = lane.status("machine-action");
                assertEquals(deadline ? "DEADLINE_EXCEEDED" : "BUDGET_EXHAUSTED", status.get("error_code").getAsString());
                assertTrue(status.get("release_confirmed").getAsBoolean());
                assertEquals(3, status.get("attempted_events").getAsInt()); // No refund of click, refresh, release.
                assertEquals(1, p.clicks); assertEquals(1, p.refreshes);
            }
        }
    }
    private static com.google.gson.JsonObject machineBatch(GameActionLaneTest.Fixture fixture) throws IOException {
        var request = fixture.batch(1, "machine-action", 1);
        request.add("action", SettingsJson.readGame("""
            {"kind":"click_slot","window_id":4,"expected_window_revision":1,"slot":0,"button":"left","mode":"pickup"}
            """));
        return request;
    }
    static final GameMachineInventory.Layout FURNACE = new GameMachineInventory.Layout(GameMachineMenu.Kind.FURNACE, 4);
    static final GameMachineInventory.Layout CRUCIBLE = new GameMachineInventory.Layout(GameMachineMenu.Kind.CRUCIBLE, 4);
    static final GameInventory.Stack EMPTY = GameInventory.Stack.EMPTY;
    static GameInventory.Stack stack(String id, int count) { return new GameInventory.Stack(id, count, "components"); }
    static GameInventory.View view(GameMachineInventory.Layout layout, Map<Integer, GameInventory.Stack> values, GameInventory.Stack cursor) throws IOException {
        return GameMachineInventory.project(layout, i -> values.getOrDefault(i, EMPTY), cursor);
    }
    static class Port implements GameInventory.Port {
        GameInventory.View current, predicted, feedback;
        int clicks, refreshes, charges, limit = 1000;
        boolean valid = true, place = true, pickup = true;
        Port(GameInventory.View before, GameInventory.View after) { current = before; predicted = after; }
        public void validate() throws IOException { if (!valid) throw new IOException("REVISION_CONFLICT"); }
        public GameInventory.View view() { return current; }
        public int capacity(int slot, GameInventory.Stack value) { return 64; }
        public boolean mayPickup(int slot) { return pickup; }
        public boolean mayPlace(int slot, GameInventory.Stack value) { return place; }
        public void click(int slot, int button, boolean quick) { clicks++; current = predicted; }
        public long requestSync() { feedback = null; return ++refreshes; }
        public GameInventory.View reply(long ticket) throws IOException {
            if (ticket != refreshes) throw new IOException("REVISION_CONFLICT"); return feedback;
        }
        void ack(GameInventory.View value) { feedback = current = value; }
        void emit(GameActionLane.Operation operation) throws IOException {
            if (charges == limit) throw new IOException("BUDGET_EXHAUSTED"); charges++; operation.run();
        }
    }
    @Test void predictionNeverCompletesWithoutFeedbackAndWaitsAreCharged() throws Exception {
        var p = new Port(view(CRUCIBLE, Map.of(), stack("minecraft:cobblestone", 2)),
            view(CRUCIBLE, Map.of(0, stack("minecraft:cobblestone", 2)), EMPTY));
        var motor = GameMachineInventory.click(p, CRUCIBLE, 0, false, false, p::emit);
        for (int i = 0; i < 10; i++) assertFalse(motor.tick(p::emit));
        assertEquals(12, p.charges); assertEquals(1, p.clicks); assertEquals(1, p.refreshes);
        p.ack(p.predicted); assertTrue(motor.tick(p::emit));
    }
    @Test void processingMayConsumeDepositedInputBeforeFeedbackWithoutInventingProductionProof() throws Exception {
        var p = new Port(view(CRUCIBLE, Map.of(), stack("minecraft:cobblestone", 2)),
            view(CRUCIBLE, Map.of(0, stack("minecraft:cobblestone", 2)), EMPTY));
        var motor = GameMachineInventory.click(p, CRUCIBLE, 0, false, false, p::emit);
        p.ack(view(CRUCIBLE, Map.of(), EMPTY)); // Input processed; tank/recipe result is deliberately not asserted.
        assertTrue(motor.tick(p::emit)); assertEquals(1, p.clicks);
    }
    @Test void exactPreclickEchoGetsOneChargedReadButNeverAnotherClickOrPredictedSuccess() throws Exception {
        var before = view(FURNACE, Map.of(7, stack("minecraft:andesite", 5)), stack("minecraft:iron_dust", 3));
        var predicted = view(FURNACE, Map.of(0, stack("minecraft:iron_dust", 3), 7, stack("minecraft:andesite", 5)), EMPTY);
        var p = new Port(before, predicted);
        var motor = GameMachineInventory.click(p, FURNACE, 0, false, false, p::emit);
        p.ack(before); p.current = predicted; // An older full packet won the first ticket.
        assertFalse(motor.tick(p::emit));
        assertEquals(2, p.refreshes); assertEquals(1, p.clicks); assertEquals(3, p.charges);
        assertFalse(motor.tick(p::emit)); // Current prediction is still not evidence.
        p.ack(view(FURNACE, Map.of(1, stack("minecraft:iron_ingot", 3), 7, stack("minecraft:andesite", 5)), EMPTY));
        assertTrue(motor.tick(p::emit)); assertEquals(1, p.clicks);
    }
    @Test void staleEchoCannotHideAnUnsolicitedOwnedChangeOrAuthorizeCancelledContinuation() throws Exception {
        var before = view(FURNACE, Map.of(), stack("minecraft:iron_dust", 3));
        var predicted = view(FURNACE, Map.of(0, stack("minecraft:iron_dust", 3)), EMPTY);
        var p = new Port(before, predicted);
        var motor = GameMachineInventory.click(p, FURNACE, 0, false, false, p::emit);
        p.ack(before); p.current = view(FURNACE, Map.of(7, stack("minecraft:diamond", 1)), EMPTY);
        assertThrows(IOException.class, () -> motor.tick(p::emit)); assertEquals(1, p.refreshes);
        var stopped = new Port(before, predicted);
        var waiting = GameMachineInventory.click(stopped, FURNACE, 0, false, false, stopped::emit);
        stopped.ack(before); assertFalse(waiting.tick(stopped::emit));
        stopped.valid = false;
        assertThrows(IOException.class, () -> waiting.tick(stopped::emit));
        assertEquals(1, stopped.clicks); assertEquals(2, stopped.refreshes);
    }
    @Test void newMachineOutputAndChargingDoNotInvalidateExactWithdrawnOwnedStack() throws Exception {
        var cell = new GameInventory.Stack("thermal:energy_cell", 1, "charge-before");
        var p = new Port(view(FURNACE, Map.of(1, stack("minecraft:iron_ingot", 2), 2, cell), EMPTY),
            view(FURNACE, Map.of(2, cell), stack("minecraft:iron_ingot", 2)));
        var motor = GameMachineInventory.click(p, FURNACE, 1, false, false, p::emit);
        p.ack(view(FURNACE, Map.of(1, stack("minecraft:iron_ingot", 1),
            2, new GameInventory.Stack("thermal:energy_cell", 1, "charge-after")), stack("minecraft:iron_ingot", 2)));
        assertTrue(motor.tick(p::emit));
    }
    @Test void sameOutputCanBePickedUpIntoAnExistingCursorThroughNativeSlotRules() throws Exception {
        var p = new Port(view(FURNACE, Map.of(1, stack("minecraft:iron_ingot", 2)), stack("minecraft:iron_ingot", 3)),
            view(FURNACE, Map.of(), stack("minecraft:iron_ingot", 5)));
        p.place = false; // Furnace output prohibits placing, but permits taking into a matching cursor.
        var motor = GameMachineInventory.click(p, FURNACE, 1, false, false, p::emit);
        p.ack(p.predicted); assertTrue(motor.tick(p::emit));
    }
    @Test void rightPickupAndPlaceOneRetainExactOwnedRemainders() throws Exception {
        var p = new Port(view(CRUCIBLE, Map.of(0, stack("minecraft:stone", 5)), EMPTY),
            view(CRUCIBLE, Map.of(0, stack("minecraft:stone", 2)), stack("minecraft:stone", 3)));
        var motor = GameMachineInventory.click(p, CRUCIBLE, 0, true, false, p::emit);
        p.ack(p.predicted); assertTrue(motor.tick(p::emit));
        p = new Port(view(CRUCIBLE, Map.of(), stack("minecraft:stone", 3)),
            view(CRUCIBLE, Map.of(0, stack("minecraft:stone", 1)), stack("minecraft:stone", 2)));
        motor = GameMachineInventory.click(p, CRUCIBLE, 0, true, false, p::emit);
        p.ack(view(CRUCIBLE, Map.of(), stack("minecraft:stone", 2)));
        assertTrue(motor.tick(p::emit));
    }
    @Test void machineToPlayerQuickMoveConfirmsEveryOwnedDestination() throws Exception {
        var p = new Port(view(FURNACE, Map.of(1, stack("minecraft:iron_ingot", 8), 7, stack("minecraft:iron_ingot", 60)), EMPTY),
            view(FURNACE, Map.of(7, stack("minecraft:iron_ingot", 64), 8, stack("minecraft:iron_ingot", 4)), EMPTY));
        var motor = GameMachineInventory.click(p, FURNACE, 1, false, true, p::emit);
        p.ack(view(FURNACE, Map.of(0, stack("minecraft:iron_ore", 1), 1, stack("minecraft:iron_ingot", 1),
            7, stack("minecraft:iron_ingot", 64), 8, stack("minecraft:iron_ingot", 4)), EMPTY));
        assertTrue(motor.tick(p::emit));
    }
    @Test void wrongCursorOrOwnedGiftLossAndComponentChangeRejectEvenIfMachineStateLooksPlausible() throws Exception {
        var before = view(FURNACE, Map.of(1, stack("minecraft:iron_ingot", 2), 7, stack("minecraft:stone", 5)), EMPTY);
        var predicted = view(FURNACE, Map.of(7, stack("minecraft:stone", 5)), stack("minecraft:iron_ingot", 2));
        for (var owned : List.of(stack("minecraft:stone", 6), stack("minecraft:stone", 4),
                new GameInventory.Stack("minecraft:stone", 5, "changed"))) {
            var p = new Port(before, predicted); var motor = GameMachineInventory.click(p, FURNACE, 1, false, false, p::emit);
            p.ack(view(FURNACE, Map.of(7, owned), stack("minecraft:iron_ingot", 2)));
            assertThrows(IOException.class, () -> motor.tick(p::emit)); assertEquals(1, p.clicks);
        }
        var p = new Port(before, predicted); var motor = GameMachineInventory.click(p, FURNACE, 1, false, false, p::emit);
        p.ack(view(FURNACE, Map.of(7, stack("minecraft:stone", 5)), stack("minecraft:iron_ingot", 3)));
        assertThrows(IOException.class, () -> motor.tick(p::emit));
    }
    @Test void changedOwnedStateAfterReplyRejectsButSubsequentMachineProcessingDoesNot() throws Exception {
        var p = new Port(view(CRUCIBLE, Map.of(), stack("minecraft:stone", 1)),
            view(CRUCIBLE, Map.of(0, stack("minecraft:stone", 1)), EMPTY));
        var motor = GameMachineInventory.click(p, CRUCIBLE, 0, false, false, p::emit);
        p.ack(p.predicted); p.current = view(CRUCIBLE, Map.of(), EMPTY);
        assertTrue(motor.tick(p::emit));
        p.current = view(CRUCIBLE, Map.of(6, stack("minecraft:diamond", 1)), EMPTY);
        assertThrows(IOException.class, () -> motor.tick(p::emit));
    }
    @Test void invalidPredictedResourceCreationStillRefreshesAndNeverConfirmsOrReplays() throws Exception {
        var p = new Port(view(CRUCIBLE, Map.of(), stack("minecraft:stone", 1)),
            view(CRUCIBLE, Map.of(0, stack("minecraft:stone", 2)), EMPTY));
        var motor = GameMachineInventory.click(p, CRUCIBLE, 0, false, false, p::emit);
        assertEquals(1, p.refreshes); assertFalse(motor.tick(p::emit));
        p.ack(p.predicted); assertThrows(IOException.class, () -> motor.tick(p::emit));
        assertEquals(1, p.clicks);
    }
    @Test void conservedButUnrequestedPredictedRearrangementRejects() throws Exception {
        var p = new Port(view(CRUCIBLE, Map.of(6, stack("minecraft:dirt", 1)), stack("minecraft:stone", 1)),
            view(CRUCIBLE, Map.of(0, stack("minecraft:stone", 1), 7, stack("minecraft:dirt", 1)), EMPTY));
        var motor = GameMachineInventory.click(p, CRUCIBLE, 0, false, false, p::emit);
        p.ack(p.predicted); assertThrows(IOException.class, () -> motor.tick(p::emit));
    }
    @Test void hiddenTargetPlayerQuickMoveAndPermissionFailureEmitNothing() throws Exception {
        var initial = view(CRUCIBLE, Map.of(6, stack("minecraft:stone", 1)), stack("minecraft:dirt", 1));
        for (int slot : new int[]{-1, 2, 5, 42}) {
            var p = new Port(initial, initial);
            assertThrows(IOException.class, () -> GameMachineInventory.click(p, CRUCIBLE, slot, false, false, p::emit));
            assertEquals(0, p.clicks);
        }
        var p = new Port(initial, initial);
        assertThrows(IOException.class, () -> GameMachineInventory.click(p, CRUCIBLE, 6, false, true, p::emit));
        p.place = false;
        assertThrows(IOException.class, () -> GameMachineInventory.click(p, CRUCIBLE, 0, false, false, p::emit));
        assertEquals(0, p.clicks);
    }
    @Test void hiddenSlotSourceIsNeverReadEvenForFeedbackAndNativeIndicesArePreserved() throws Exception {
        var read = new ArrayList<Integer>();
        var projected = GameMachineInventory.project(CRUCIBLE, i -> {
            if (i >= 2 && i < 6) throw new IOException("private-canary-accessed");
            read.add(i); return i == 6 ? stack("minecraft:stone", 1) : EMPTY;
        }, EMPTY);
        assertEquals(38, read.size()); assertEquals("minecraft:stone", projected.slots().get(6).id());
        for (int i = 2; i < 6; i++) assertEquals(EMPTY, projected.slots().get(i));
    }
    @Test void budgetExhaustionOrLostContextStopsWithoutAnotherClick() throws Exception {
        var p = new Port(view(CRUCIBLE, Map.of(), stack("minecraft:stone", 1)),
            view(CRUCIBLE, Map.of(0, stack("minecraft:stone", 1)), EMPTY));
        p.limit = 2;
        var motor = GameMachineInventory.click(p, CRUCIBLE, 0, false, false, p::emit);
        assertThrows(IOException.class, () -> motor.tick(p::emit)); assertEquals(1, p.clicks);
        p.valid = false; assertThrows(IOException.class, () -> motor.tick(p::emit)); assertEquals(1, p.clicks);
    }
}
