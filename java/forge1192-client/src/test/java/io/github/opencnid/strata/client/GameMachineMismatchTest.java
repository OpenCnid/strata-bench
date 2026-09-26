package io.github.opencnid.strata.client;

import com.google.gson.JsonObject;
import java.util.ArrayList;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import java.nio.file.Path;
import static org.junit.jupiter.api.Assertions.*;
import static io.github.opencnid.strata.client.GameMachineInventoryTest.*;

/** Real lane/journal with synthetic menu feedback; not an authentic game pass. */
class GameMachineMismatchTest {
    @Test void everyOwnedBitRetainsOnlyComparisonMasksAndReturnsACopy() throws Exception {
        var empty = view(FURNACE, Map.of(), EMPTY);
        for (int bit = 0; bit <= 36; bit++) {
            var secret = new GameInventory.Stack("secret-id\n".repeat(200), 17, "secret-component".repeat(200));
            var changed = view(FURNACE, bit == 0 ? Map.of() : Map.of(FURNACE.playerStart()+bit-1, secret),
                bit == 0 ? secret : EMPTY);
            var error = new GameMachineMismatch(FURNACE, GameMachineMismatch.Phase.PREDICTION_REPLY,
                false, empty, empty, changed, changed);
            var d = error.diagnostic(); var diff = d.getAsJsonObject("predicted_received");
            for (String kind : new String[]{"id","count","components"}) assertEquals(1L << bit, diff.get(kind).getAsLong());
            assertEquals(0, d.getAsJsonObject("received_current").get("id").getAsLong());
            assertFalse(d.toString().contains("secret")); assertTrue(d.toString().length() < 1024);
            d.addProperty("phase", "tampered"); assertEquals("prediction_reply", error.diagnostic().get("phase").getAsString());
        }
    }

    @Test void machineAndHiddenSlotsNeverEnterTheDiagnostic() throws Exception {
        var empty = view(FURNACE, Map.of(), EMPTY);
        var slots = new ArrayList<>(empty.slots());
        for (int slot = 0; slot < FURNACE.playerStart(); slot++) slots.set(slot, stack("private-machine-item", 9));
        var changed = new GameInventory.View(slots, EMPTY, -1);
        var d = new GameMachineMismatch(FURNACE, GameMachineMismatch.Phase.REPLY_CURRENT,
            true, empty, changed, empty, changed).diagnostic();
        for (String pair : new String[]{"before_predicted","before_received","before_current","predicted_received","received_current"})
            for (String kind : new String[]{"id","count","components"}) assertEquals(0, d.getAsJsonObject(pair).get(kind).getAsLong());
        assertFalse(d.toString().contains("private-machine"));
    }

    @Test void comparisonKindsStaySeparate() throws Exception {
        var original = view(FURNACE, Map.of(), new GameInventory.Stack("item", 1, "component"));
        for (int kind = 0; kind < 3; kind++) {
            var changed = view(FURNACE, Map.of(), new GameInventory.Stack(kind==0?"other":"item", kind==1?2:1, kind==2?"other":"component"));
            var d = new GameMachineMismatch(FURNACE, GameMachineMismatch.Phase.REPLY_CURRENT,
                false, original, original, original, changed).diagnostic().getAsJsonObject("received_current");
            assertEquals(kind==0?1:0,d.get("id").getAsLong());
            assertEquals(kind==1?1:0,d.get("count").getAsLong());
            assertEquals(kind==2?1:0,d.get("components").getAsLong());
        }
    }

    @Test void bothFailureBranchesPublishAfterTerminalReleaseWithoutReplay(@TempDir Path root) throws Exception {
        for (boolean later : new boolean[]{false,true})
            exercise(java.nio.file.Files.createDirectory(root.resolve(later?"current":"reply")),later,false,false,false);
    }

    @Test void exhaustedPreclickRefreshRemainsUnknown(@TempDir Path root) throws Exception {
        exercise(root,false,true,false,false);
    }

    @Test void failingDiagnosticSinkCannotChangeUnknownReceipt(@TempDir Path root) throws Exception {
        exercise(root,false,false,true,false);
    }

    @Test void releaseFailureKeepsItsOriginalPrecedence(@TempDir Path root) throws Exception {
        exercise(root,false,false,false,true);
    }

    @Test void successfulFeedbackHasNoDiagnosticOrAdditionalRefresh(@TempDir Path root) throws Exception {
        var f = new GameActionLaneTest.Fixture(root,100);
        var predicted = view(FURNACE,Map.of(0,stack("dust",3)),EMPTY);
        var p = new Port(view(FURNACE,Map.of(),stack("dust",3)),predicted);
        f.port.customMotor = emit -> GameMachineInventory.click(p,FURNACE,0,false,false,emit);
        f.port.diagnostic = (id,d) -> fail("No diagnostic on successful confirmation");
        try (var lane = f.open()) {
            f.arm(lane,1); f.deliver(lane);
            var request = f.batch(1,"machine-action",1);
            request.add("action",SettingsJson.readGame("""
                {"kind":"click_slot","window_id":4,"expected_window_revision":1,"slot":0,"button":"left","mode":"pickup"}
                """));
            lane.accept(request); f.start(lane); p.ack(predicted); lane.tick();
            assertEquals("emitted",lane.status("machine-action").get("status").getAsString());
            assertEquals(1,p.clicks); assertEquals(1,p.refreshes);
        }
    }

    private void exercise(Path root, boolean later, boolean refresh, boolean brokenSink, boolean releaseFailure) throws Exception {
        var f = new GameActionLaneTest.Fixture(root,100);
        var before = view(FURNACE, Map.of(), stack("dust",3));
        var predicted = view(FURNACE, Map.of(0,stack("dust",3)), EMPTY);
        var mismatch = view(FURNACE, Map.of(FURNACE.playerStart(),stack("unexpected",1)), EMPTY);
        var p = new Port(before,predicted); var diagnostics = new ArrayList<JsonObject>();
        f.port.customMotor = emit -> GameMachineInventory.click(p,FURNACE,0,false,false,emit);
        try (var lane = f.open()) {
            f.port.diagnostic = (id,d) -> {
                assertEquals("machine-action",id); assertTrue(f.port.releases>0);
                try {
                    assertEquals("unknown",lane.status(id).get("status").getAsString());
                    assertTrue(lane.health().get("fenced").getAsBoolean());
                    assertTrue(java.nio.file.Files.readString(root.resolve("game-actions.jsonl")).contains(releaseFailure?"GAME_RELEASE_UNCONFIRMED":"GAME_MACHINE_TRANSFER_UNCONFIRMED"));
                } catch (java.io.IOException e) { fail(e); }
                diagnostics.add(d);
                if (brokenSink) throw new IllegalStateException("private sink unavailable");
            };
            f.arm(lane,1); f.deliver(lane);
            var request = f.batch(1,"machine-action",1);
            request.add("action",SettingsJson.readGame("""
                {"kind":"click_slot","window_id":4,"expected_window_revision":1,"slot":0,"button":"left","mode":"pickup"}
                """));
            lane.accept(request); f.start(lane); f.port.failRelease = releaseFailure;
            if (refresh) { p.ack(before); lane.tick(); assertTrue(diagnostics.isEmpty()); p.ack(before); }
            else { p.feedback = later ? predicted : mismatch; p.current = mismatch; }
            lane.tick();
            var receipt = lane.status("machine-action");
            assertEquals("unknown",receipt.get("status").getAsString());
            assertEquals(releaseFailure?"GAME_RELEASE_UNCONFIRMED":"GAME_MACHINE_TRANSFER_UNCONFIRMED",receipt.get("error_code").getAsString());
            assertTrue(receipt.get("requires_resync").getAsBoolean()); assertEquals(!releaseFailure,receipt.get("release_confirmed").getAsBoolean());
            assertEquals(1,p.clicks); assertEquals(refresh?2:1,p.refreshes); assertEquals(1,diagnostics.size());
            assertEquals(later?"reply_current":"prediction_reply",diagnostics.get(0).get("phase").getAsString());
            assertEquals(refresh,diagnostics.get(0).get("preclick_refresh_used").getAsBoolean());
            assertEquals(receipt,lane.accept(request)); assertEquals(1,diagnostics.size()); assertEquals(1,p.clicks);
            assertFalse(receipt.toString().contains("predicted_received"));
        }
    }
}
