package io.github.opencnid.strata.client;

import com.google.gson.JsonObject;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import static org.junit.jupiter.api.Assertions.*;
import static io.github.opencnid.strata.client.GameMachineInventoryTest.*;

class GameMachinePreflightFailureTest {
    static class Probe implements GameInventory.Port {
        final GameInventory.View initial = GameMachineInventoryTest.view(FURNACE, Map.of(), stack("dust", 3));
        final Port p = new Port(initial, GameMachineInventoryTest.view(FURNACE, Map.of(0, stack("dust", 3)), EMPTY));
        String fault = ""; int reads;
        Probe() throws IOException {}
        public void validate() throws IOException { if (fault.equals("context")) throw new IOException("REVISION_CONFLICT"); p.validate(); }
        public GameInventory.View view() throws IOException {
            reads++;
            if (fault.equals("current_view")) throw new IOException("GAME_VIEW_UNAVAILABLE");
            if (fault.equals("current_layout")) return new GameInventory.View(java.util.List.of(), EMPTY, -1);
            if (fault.equals("final_baseline") && reads == 3) return GameMachineInventoryTest.view(FURNACE, Map.of(42, stack("changed", 1)), initial.cursor());
            return p.view();
        }
        public int capacity(int slot, GameInventory.Stack item) { return p.capacity(slot, item); }
        public boolean mayPickup(int slot) { return p.mayPickup(slot); }
        public boolean mayPlace(int slot, GameInventory.Stack item) { return !fault.equals("transfer_start") && p.mayPlace(slot,item); }
        public void click(int slot, int button, boolean quick) { p.click(slot,button,quick); }
        public long requestSync() { return p.requestSync(); }
        public GameInventory.View reply(long ticket) throws IOException {
            if (fault.equals("reply")) throw new IOException("REVISION_CONFLICT");
            return p.reply(ticket);
        }
    }

    @Test void everyFailurePhasePreservesOriginalErrorAndReadClickCounts() throws Exception {
        for (var phase : GameMachinePreflightFailure.Phase.values()) {
            // Requires an earlier accepted read; exercised by the dedicated
            // reacquisition test with its frozen baseline and diagnostic masks.
            if (phase == GameMachinePreflightFailure.Phase.REACQUIRED_BASELINE) continue;
            var p = new Probe();
            var motor = GameMachinePreflight.start(p,FURNACE,0,false,false,() -> {
                if (p.fault.equals("input_fence")) throw new IOException("STALE_OBSERVATION");
            },p.p::emit);
            p.fault = phase.name().toLowerCase(java.util.Locale.ROOT);
            p.p.ack(p.initial);
            String code = switch (phase) {
                case WAIT -> "BUDGET_EXHAUSTED";
                case INPUT_FENCE -> "STALE_OBSERVATION";
                case CURRENT_VIEW -> "GAME_VIEW_UNAVAILABLE";
                case REPLY_LAYOUT, CURRENT_LAYOUT -> "GAME_CONTAINER_UNSUPPORTED";
                case TRANSFER_START -> "PRECONDITION_FAILED";
                default -> "REVISION_CONFLICT";
            };
            if (phase == GameMachinePreflightFailure.Phase.WAIT) { p.p.feedback = null; p.p.limit = p.p.charges; }
            if (phase == GameMachinePreflightFailure.Phase.REPLY_LAYOUT) p.p.feedback = new GameInventory.View(java.util.List.of(),EMPTY,-1);
            if (phase == GameMachinePreflightFailure.Phase.CURRENT_MATCH) p.p.current = view(FURNACE,Map.of(42,stack("changed",1)),p.initial.cursor());
            if (phase == GameMachinePreflightFailure.Phase.SELECTION_MATCH) p.p.ack(view(FURNACE,Map.of(),stack("dust",2)));
            var error = assertThrows(GameMachinePreflightFailure.class,() -> motor.tick(p.p::emit));
            assertEquals(code,error.getMessage()); assertEquals(p.fault,error.diagnostic().get("phase").getAsString());
            assertEquals(0,p.p.clicks); assertEquals(1,p.p.refreshes);
            boolean compared = phase == GameMachinePreflightFailure.Phase.CURRENT_MATCH
                || phase == GameMachinePreflightFailure.Phase.SELECTION_MATCH || phase == GameMachinePreflightFailure.Phase.FINAL_BASELINE;
            assertEquals(!compared,error.diagnostic().get("comparison").isJsonNull());
            assertTrue(p.reads <= 3); // No diagnostic-only reads.
        }
    }

    @Test void exactMasksCoverOwnedAndMachinePositionsWithoutValuesOrHiddenSlots() throws Exception {
        var empty = view(FURNACE,Map.of(),EMPTY);
        for (int bit = 0; bit <= 36; bit++) {
            var secret = new GameInventory.Stack("private-id",9,"private-components");
            var changed = view(FURNACE,bit==0?Map.of():Map.of(FURNACE.playerStart()+bit-1,secret),bit==0?secret:EMPTY);
            var error = failure(empty,changed); var d = error.diagnostic();
            for (String field : new String[]{"id","count","components"})
                assertEquals(1L << bit,d.getAsJsonObject("comparison").getAsJsonObject("owned").get(field).getAsLong());
            assertFalse(d.toString().contains("private-")); assertTrue(d.toString().length()<768);
            d.addProperty("phase","mutated"); assertEquals("current_match",error.diagnostic().get("phase").getAsString());
        }
        for (int slot=0;slot<FURNACE.playerStart();slot++) {
            var slots = new ArrayList<>(empty.slots()); slots.set(slot,new GameInventory.Stack("private-id",9,"private-components"));
            var d = failure(empty,new GameInventory.View(slots,EMPTY,-1)).diagnostic().getAsJsonObject("comparison");
            for (String field : new String[]{"id","count","components"}) {
                assertEquals(slot<FURNACE.kind().baseSlots?1L<<slot:0,d.getAsJsonObject("machine").get(field).getAsLong());
                assertEquals(0,d.getAsJsonObject("owned").get(field).getAsLong());
                assertEquals(slot==0,d.getAsJsonObject("selected").get(field).getAsBoolean());
            }
        }
    }
    static GameMachinePreflightFailure failure(GameInventory.View expected,GameInventory.View actual) {
        return new GameMachinePreflightFailure(GameMachinePreflightFailure.Phase.CURRENT_MATCH,
            new IOException("REVISION_CONFLICT"),FURNACE,0,expected,actual);
    }

    @Test void componentOnlyDriftDoesNotBecomeAnIdOrCountDifference() throws Exception {
        var a=view(FURNACE,Map.of(42,new GameInventory.Stack("bag",1,"a")),EMPTY);
        var b=view(FURNACE,Map.of(42,new GameInventory.Stack("bag",1,"b")),EMPTY);
        var mask=failure(a,b).diagnostic().getAsJsonObject("comparison").getAsJsonObject("owned");
        assertEquals(0,mask.get("id").getAsLong()); assertEquals(0,mask.get("count").getAsLong());
        assertEquals(1L<<36,mask.get("components").getAsLong());
    }

    @Test void publicationFollowsTerminalAndCannotChangeReceiptOrReplay(@TempDir Path root) throws Exception {
        for (String mode : new String[]{"normal","sink_failure","release_failure"}) {
            var path=Files.createDirectory(root.resolve(mode)); var f=new GameActionLaneTest.Fixture(path,100);
            var p=new Probe(); var diagnostics=new ArrayList<JsonObject>();
            f.port.customMotor=emit -> GameMachinePreflight.start(p,FURNACE,0,false,false,() -> {},emit);
            try (var lane=f.open()) {
                f.port.diagnostic=(id,d) -> {
                    try {
                        assertEquals("unknown",lane.status(id).get("status").getAsString());
                        assertTrue(Files.readString(path.resolve("game-actions.jsonl")).contains("\"kind\":\"terminal\""));
                        assertTrue(f.port.releases>0); diagnostics.add(d);
                    } catch(IOException failure) { fail(failure); }
                    if (mode.equals("sink_failure")) throw new IllegalStateException("private sink failure");
                };
                f.arm(lane,1);f.deliver(lane);var request=f.batch(1,"preflight-failure",1);
                request.add("action",SettingsJson.readGame("""
                    {"kind":"click_slot","window_id":4,"expected_window_revision":1,"slot":0,"button":"left","mode":"pickup"}
                    """));
                lane.accept(request);f.start(lane);p.p.ack(p.initial);
                p.p.current=view(FURNACE,Map.of(42,stack("unexpected",1)),p.initial.cursor());
                f.port.failRelease=mode.equals("release_failure");lane.tick();
                var receipt=lane.status("preflight-failure");
                assertEquals(mode.equals("release_failure")?"GAME_RELEASE_UNCONFIRMED":"REVISION_CONFLICT",receipt.get("error_code").getAsString());
                assertEquals(!mode.equals("release_failure"),receipt.get("release_confirmed").getAsBoolean());
                assertEquals(1,diagnostics.size());assertEquals("current_match",diagnostics.get(0).get("phase").getAsString());
                assertEquals(receipt,lane.accept(request));assertEquals(1,diagnostics.size());assertEquals(0,p.p.clicks);
                assertFalse(receipt.toString().contains("comparison"));assertTrue(lane.health().get("fenced").getAsBoolean());
            }
        }
    }
}
