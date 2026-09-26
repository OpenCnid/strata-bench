package io.github.opencnid.strata.client;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import static org.junit.jupiter.api.Assertions.*;
import static io.github.opencnid.strata.client.GameMachineInventoryTest.*;

/** Scripted server/application boundary and real action lane; no native-game claim. */
class GameMachinePreflightTest {
    static final int BACKPACK = FURNACE.total() - 1;
    static final GameInventory.Stack DUST = stack("test:dust", 3);
    static GameInventory.Stack bag(String components) { return new GameInventory.Stack("test:bag", 1, components); }
    static GameInventory.View before(String components) throws IOException {
        return view(FURNACE, Map.of(BACKPACK, bag(components)), DUST);
    }
    static GameInventory.View after(String components) throws IOException {
        return view(FURNACE, Map.of(0, DUST, BACKPACK, bag(components)), EMPTY);
    }
    static GameInventory.View replace(GameInventory.View view, int slot, GameInventory.Stack item) {
        var slots = new ArrayList<>(view.slots()); slots.set(slot, item);
        return new GameInventory.View(slots, view.cursor(), view.resultSlot());
    }
    static GameActionLane.Motor start(Port port, GameActionLane.Operation fence) throws IOException {
        return GameMachinePreflight.start(port, FURNACE, 0, false, false, fence, port::emit);
    }
    @Test void noClickUntilAppliedBaselineThenExactServerTransfer() throws Exception {
        var p = new Port(before("local"), after("server")); int[] fences = {0};
        var motor = start(p, () -> fences[0]++);
        assertEquals(0, p.clicks); assertEquals(1, p.refreshes);
        for (int i = 0; i < 3; i++) assertFalse(motor.tick(p::emit));
        assertEquals(4, p.charges); assertEquals(0, fences[0]);
        p.ack(before("server")); assertFalse(motor.tick(p::emit));
        assertEquals(1, fences[0]); assertEquals(1, p.clicks); assertEquals(2, p.refreshes);
        assertFalse(motor.tick(p::emit)); // Prediction cannot complete the action.
        p.ack(after("server")); assertTrue(motor.tick(p::emit)); assertEquals(1, p.clicks);
    }
    @Test void unchangedBaselineAlsoRequiresItsOwnPostClickReply() throws Exception {
        var p = new Port(before("same"), after("same")); var motor = start(p, () -> {});
        p.ack(before("same")); assertFalse(motor.tick(p::emit));
        assertNull(p.feedback); assertEquals(1, p.clicks);
        p.ack(after("same")); assertTrue(motor.tick(p::emit));
    }
    @Test void originalLocalMetadataCannotReplaceServerBaselineAfterClick() throws Exception {
        var p = new Port(before("local"), after("server")); var motor = start(p, () -> {});
        p.ack(before("server")); assertFalse(motor.tick(p::emit)); p.ack(after("local"));
        assertThrows(GameMachineMismatch.class, () -> motor.tick(p::emit));
        assertEquals(1, p.clicks); assertEquals(2, p.refreshes);
    }
    @Test void cursorAndAllResourceOrPositionChangesRefuseBeforeClick() throws Exception {
        var initial = before("local"); var baseline = before("server");
        var bad = new ArrayList<GameInventory.View>();
        bad.add(new GameInventory.View(baseline.slots(), stack("test:dust", 2), -1));
        bad.add(new GameInventory.View(baseline.slots(), new GameInventory.Stack(DUST.id(), DUST.count(), "other"), -1));
        for (int i = 0; i < FURNACE.total(); i++) if (FURNACE.visible(i)) {
            bad.add(replace(baseline, i, stack("test:gift", 1)));
            if (i == BACKPACK) bad.add(replace(baseline, i, new GameInventory.Stack("test:bag", 2, "server")));
        }
        bad.add(replace(replace(baseline, BACKPACK, EMPTY), BACKPACK - 1, bag("server")));
        for (var reply : bad) {
            var p = new Port(initial, after("server")); var motor = start(p, () -> {}); p.ack(reply);
            assertThrows(IOException.class, () -> motor.tick(p::emit));
            assertEquals(0, p.clicks); assertEquals(1, p.refreshes);
        }
    }
    @Test void clickedPlayerOrMachineStackComponentsCannotChangeInPreflight() throws Exception {
        for (int slot : new int[]{0, BACKPACK}) {
            var initial = view(FURNACE, Map.of(slot, bag("local")), EMPTY);
            var p = new Port(initial, initial);
            var motor = GameMachinePreflight.start(p, FURNACE, slot, false, false, () -> {}, p::emit);
            p.ack(replace(initial, slot, bag("server")));
            assertThrows(IOException.class, () -> motor.tick(p::emit)); assertEquals(0, p.clicks);
        }
    }
    @Test void replyCurrentMismatchOrInvalidLayoutNeverAuthorizesClick() throws Exception {
        for (boolean invalidLayout : new boolean[]{false, true}) {
            var p = new Port(before("local"), after("server")); var motor = start(p, () -> {});
            p.ack(invalidLayout ? new GameInventory.View(java.util.List.of(), EMPTY, -1) : before("server"));
            if (!invalidLayout) p.current = before("local");
            assertThrows(IOException.class, () -> motor.tick(p::emit)); assertEquals(0, p.clicks);
        }
    }
    @Test void changedContextOrOriginalInputFencePreventsClick() throws Exception {
        for (boolean context : new boolean[]{false, true}) {
            var p = new Port(before("local"), after("server"));
            var motor = start(p, () -> { if (!context) throw new IOException("STALE_OBSERVATION"); });
            p.ack(before("server")); if (context) p.valid = false;
            assertThrows(IOException.class, () -> motor.tick(p::emit)); assertEquals(0, p.clicks);
        }
    }
    @Test void finalBaselineRecheckCannotSilentlyFreezeChangedMetadata() throws Exception {
        var baseline = before("server");
        var p = new Port(before("local"), after("server")) {
            int reads;
            public GameInventory.View view() { return ++reads >= 3 ? beforeUnchecked() : current; }
            GameInventory.View beforeUnchecked() { return replace(baseline, BACKPACK, bag("changed")); }
        };
        var motor = start(p, () -> {}); p.ack(baseline);
        assertThrows(IOException.class, () -> motor.tick(p::emit)); assertEquals(0, p.clicks);
    }
    @Test void hiddenOrUnsupportedQuickMoveRejectsWithoutEvenARead() throws Exception {
        for (int slot : new int[]{3, BACKPACK}) {
            var p = new Port(before("local"), after("server"));
            assertThrows(IOException.class, () -> GameMachinePreflight.start(p, FURNACE, slot, false, true, () -> {}, p::emit));
            assertEquals(0, p.clicks); assertEquals(0, p.refreshes);
        }
    }
    @Test void serverBaselineDoesNotDisableExistingSinglePreclickEchoRefresh() throws Exception {
        var p = new Port(before("local"), after("server")); var motor = start(p, () -> {});
        p.ack(before("server")); assertFalse(motor.tick(p::emit));
        p.ack(before("server")); assertFalse(motor.tick(p::emit));
        assertEquals(3, p.refreshes); assertEquals(1, p.clicks);
        p.ack(before("server")); assertThrows(GameMachineMismatch.class, () -> motor.tick(p::emit));
        assertEquals(3, p.refreshes); assertEquals(1, p.clicks);
    }
    @Test void realLaneCancelDeadlineAndBudgetNeverReplayOrRefundPreflight(@TempDir Path root) throws Exception {
        for (String cause : new String[]{"cancel", "deadline", "budget"}) {
            var f = new GameActionLaneTest.Fixture(Files.createDirectory(root.resolve(cause)), cause.equals("budget") ? 4 : 100);
            var p = new Port(before("local"), after("server"));
            f.port.customMotor = emit -> GameMachinePreflight.start(p, FURNACE, 0, false, false, () -> {}, emit);
            try (var lane = f.open()) {
                f.arm(lane, 1); f.deliver(lane); var request = f.batch(1, "machine-preflight", 1);
                request.add("action", SettingsJson.readGame("""
                    {"kind":"click_slot","window_id":4,"expected_window_revision":1,"slot":0,"button":"left","mode":"pickup"}
                    """));
                lane.accept(request); f.start(lane);
                assertEquals(0, p.clicks); assertEquals(1, p.refreshes);
                if (cause.equals("cancel")) lane.cancel("machine-preflight");
                else if (cause.equals("deadline")) { f.time.advance(5000); lane.tick(); }
                else { lane.tick(); lane.tick(); }
                var status = lane.status("machine-preflight");
                assertEquals(cause.equals("cancel") ? "CANCELLED" : cause.equals("deadline") ? "DEADLINE_EXCEEDED" : "BUDGET_EXHAUSTED",
                    status.get("error_code").getAsString());
                assertTrue(status.get("release_confirmed").getAsBoolean());
                assertEquals(cause.equals("budget") ? 3 : 2, status.get("attempted_events").getAsInt());
                assertEquals(status, lane.accept(request)); assertEquals(0, p.clicks);
            }
        }
    }
}
