package io.github.opencnid.strata.client;

import static org.junit.jupiter.api.Assertions.*;
import static io.github.opencnid.strata.client.GameMachineInventoryTest.*;
import static io.github.opencnid.strata.client.GameMachinePreflightTest.*;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

/** Synthetic native-port/lane controls; actual changed-profile play is separate. */
final class GameMachineReacquisitionTest {
    @Test void oneChargedReadRestoresOriginalServerBaselineBeforeOneClick() throws Exception {
        var p = new Port(before("initial-client"), after("server"));
        int[] fences = {0}; var motor = start(p, () -> fences[0]++);
        p.ack(before("server")); p.current = before("local-decoration");
        assertFalse(motor.tick(p::emit));
        assertEquals(0, p.clicks); assertEquals(2, p.refreshes); assertEquals(2, p.charges);
        assertFalse(motor.tick(p::emit)); assertEquals(3, p.charges); // Charged wait.
        p.ack(before("server")); assertFalse(motor.tick(p::emit));
        assertEquals(2, fences[0]); assertEquals(1, p.clicks); assertEquals(3, p.refreshes);
        assertNull(p.feedback); // The preflight read never confirms the click.
        p.ack(after("server")); assertTrue(motor.tick(p::emit));
        assertEquals(1, p.clicks); assertEquals(3, p.refreshes);
    }

    @Test void renewedServerReplyCannotReplaceFirstExactComponents() throws Exception {
        var p = new Port(before("initial"), after("server")); var motor = start(p, () -> {});
        p.ack(before("server")); p.current = before("decoration");
        assertFalse(motor.tick(p::emit));
        p.ack(before("new-server-value"));
        var error = assertThrows(GameMachinePreflightFailure.class, () -> motor.tick(p::emit));
        assertEquals("REVISION_CONFLICT", error.getMessage());
        var d = error.diagnostic();
        assertEquals("machine-preflight-comparison-masks/2", d.get("policy").getAsString());
        assertEquals("reacquired_baseline", d.get("phase").getAsString());
        var owned = d.getAsJsonObject("comparison").getAsJsonObject("owned");
        assertEquals(0, owned.get("id").getAsLong()); assertEquals(0, owned.get("count").getAsLong());
        assertEquals(1L << 36, owned.get("components").getAsLong());
        assertFalse(d.toString().contains("server-value"));
        assertEquals(0, p.clicks); assertEquals(2, p.refreshes);
    }

    @Test void persistentCurrentDriftCannotRequestAnotherRead() throws Exception {
        var p = new Port(before("initial"), after("server")); var motor = start(p, () -> {});
        p.ack(before("server")); p.current = before("local"); assertFalse(motor.tick(p::emit));
        p.ack(before("server")); p.current = before("local");
        var error = assertThrows(GameMachinePreflightFailure.class, () -> motor.tick(p::emit));
        assertEquals("current_match", error.diagnostic().get("phase").getAsString());
        assertEquals(0, p.clicks); assertEquals(2, p.refreshes);
    }

    @Test void currentResourcesCursorAndSelectedComponentsCannotAuthorizeReacquisition() throws Exception {
        var server = before("server");
        var invalid = new java.util.ArrayList<GameInventory.View>();
        for (int slot = 0; slot < FURNACE.total(); slot++) if (FURNACE.visible(slot)) {
            invalid.add(replace(server, slot, stack("test:gift", 1)));
        }
        invalid.add(new GameInventory.View(server.slots(), new GameInventory.Stack(DUST.id(), DUST.count(), "changed"), -1));
        invalid.add(replace(server, BACKPACK, new GameInventory.Stack("test:bag", 2, "server")));
        for (var current : invalid) {
            var p = new Port(before("initial"), after("server")); var motor = start(p, () -> {});
            p.ack(server); p.current = current;
            assertThrows(IOException.class, () -> motor.tick(p::emit));
            assertEquals(0, p.clicks); assertEquals(1, p.refreshes);
        }
        var p = new Port(server, server);
        var motor = GameMachinePreflight.start(p, FURNACE, BACKPACK, false, false, () -> {}, p::emit);
        p.ack(server); p.current = before("selected-drift");
        assertThrows(IOException.class, () -> motor.tick(p::emit));
        assertEquals(0, p.clicks); assertEquals(1, p.refreshes);
    }

    @Test void originalSelectionMismatchCannotHideBehindCurrentMetadataDrift() throws Exception {
        var p = new Port(before("initial"), after("server")); var motor = start(p, () -> {});
        var changed = new GameInventory.View(before("server").slots(), stack("test:dust", 2), -1);
        p.ack(changed); p.current = replace(changed, BACKPACK, bag("decoration"));
        assertThrows(IOException.class, () -> motor.tick(p::emit));
        assertEquals(0, p.clicks); assertEquals(1, p.refreshes);
    }

    @Test void renewedReplyStillRunsOriginalObservationFenceBeforeInput() throws Exception {
        var p = new Port(before("initial"), after("server")); int[] fences = {0};
        var motor = start(p, () -> { if (++fences[0] == 2) throw new IOException("STALE_OBSERVATION"); });
        p.ack(before("server")); p.current = before("local"); assertFalse(motor.tick(p::emit));
        p.ack(before("server"));
        var error = assertThrows(GameMachinePreflightFailure.class, () -> motor.tick(p::emit));
        assertEquals("STALE_OBSERVATION", error.getMessage());
        assertEquals("input_fence", error.diagnostic().get("phase").getAsString());
        assertTrue(error.diagnostic().get("comparison").isJsonNull());
        assertEquals(0, p.clicks); assertEquals(2, p.refreshes);
    }

    @Test void postClickReplyMustStillMatchFirstBaselineExactly() throws Exception {
        var p = new Port(before("initial"), after("server")); var motor = start(p, () -> {});
        p.ack(before("server")); p.current = before("local"); assertFalse(motor.tick(p::emit));
        p.ack(before("server")); assertFalse(motor.tick(p::emit));
        p.ack(after("new-value"));
        assertThrows(GameMachineMismatch.class, () -> motor.tick(p::emit));
        assertEquals(1, p.clicks); assertEquals(3, p.refreshes);
    }

    @Test void realLaneCancelDeadlineAndBudgetFencePendingReacquisition(@TempDir Path root) throws Exception {
        for (String cause : new String[]{"cancel", "deadline", "budget"}) {
            var f = new GameActionLaneTest.Fixture(Files.createDirectory(root.resolve(cause)), cause.equals("budget") ? 4 : 100);
            var p = new Port(before("initial"), after("server"));
            f.port.customMotor = emit -> GameMachinePreflight.start(p, FURNACE, 0, false, false, () -> {}, emit);
            try (var lane = f.open()) {
                f.arm(lane, 1); f.deliver(lane); var request = f.batch(1, "machine-reacquire", 1);
                request.add("action", SettingsJson.readGame("""
                    {"kind":"click_slot","window_id":4,"expected_window_revision":1,"slot":0,"button":"left","mode":"pickup"}
                    """));
                lane.accept(request); f.start(lane);
                p.ack(before("server")); p.current = before("local"); lane.tick();
                assertEquals(0, p.clicks); assertEquals(2, p.refreshes);
                if (cause.equals("cancel")) lane.cancel("machine-reacquire");
                else if (cause.equals("deadline")) { f.time.advance(5000); lane.tick(); }
                else lane.tick();
                var status = lane.status("machine-reacquire");
                assertEquals(cause.equals("cancel") ? "CANCELLED" : cause.equals("deadline") ? "DEADLINE_EXCEEDED" : "BUDGET_EXHAUSTED",
                    status.get("error_code").getAsString());
                assertTrue(status.get("release_confirmed").getAsBoolean());
                assertEquals(3, status.get("attempted_events").getAsInt());
                assertEquals(status, lane.accept(request));
                p.ack(before("server")); lane.tick(); assertEquals(0, p.clicks);
            }
        }
    }
}
