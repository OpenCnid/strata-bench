package io.github.opencnid.strata.client;

import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

/** Independent toy menu: scripted recipe, no native/server correctness claim. */
class GameCraftingTest {
    @Test void delayedServerPreviewRequiresFreshReplyWithoutRepeatingFill() throws Exception {
        var p=new Port(1);var motor=startedFill(p);p.slots.set(0,EMPTY);
        for(int i=0;i<3;i++) {p.ack();assertFalse(motor.tick(p::emit));}
        assertEquals(1,p.fills);assertEquals(0,p.clicks);
        // A local preview is not a new server reply.
        p.slots.set(0,p.output);assertFalse(motor.tick(p::emit));assertEquals(0,p.takes);
        p.ack();assertFalse(motor.tick(p::emit));assertEquals(1,p.takes);
        p.complete(motor);assertEquals(1,p.fills);assertEquals(p.output,p.slots.get(9));
    }
    @Test void previewWaitRejectsResourceMetadataAndWrongOutputChanges() throws Exception {
        for(int fault=0;fault<5;fault++) {
            var p=new Port(1);var motor=startedFill(p);p.slots.set(0,EMPTY);
            p.ack();assertFalse(motor.tick(p::emit));
            if(fault==0) {p.slots.set(1,EMPTY);p.slots.set(2,item("ingredient",1));}
            if(fault==1) p.slots.set(1,new GameInventory.Stack("test:ingredient",1,"changed"));
            if(fault==2) p.cursor=item("held",1);
            if(fault==3) p.slots.set(0,item("wrong",4));
            if(fault==4) p.matched=false;
            p.ack();assertThrows(IOException.class,()->motor.tick(p::emit));
            assertEquals(1,p.fills);assertEquals(0,p.clicks);
        }
    }
    @Test void missingPreviewAndExhaustedReadBudgetNeverTakeOrRefill() throws Exception {
        var p=new Port(1);var motor=startedFill(p);p.slots.set(0,EMPTY);
        for(int i=0;i<GameCrafting.MAX_PREVIEW_READS;i++) {p.ack();assertFalse(motor.tick(p::emit));}
        long ticket=p.ticket;p.ack();assertThrows(IOException.class,()->motor.tick(p::emit));
        assertEquals(ticket,p.ticket);assertEquals(1,p.fills);assertEquals(0,p.clicks);
        var next=new Port(1);var pending=startedFill(next);next.slots.set(0,EMPTY);next.ack();
        assertThrows(IOException.class,()->pending.tick(op->{throw new IOException("BUDGET_EXHAUSTED");}));
        assertEquals(1,next.fills);assertEquals(0,next.clicks);
    }
    @Test void fillAndTakeBarriersRequireOriginalExactMetadataAfterOneRead() throws Exception {
        for(boolean take:List.of(false,true)) for(int outcome=0;outcome<3;outcome++) {
            var p=new Port(1);var original=item("backpack",1);
            var changed=new GameInventory.Stack(original.id(),1,"client-generated-uuid");
            p.slots.set(44,original);var motor=startedFill(p);
            if(take) {p.ack();assertFalse(motor.tick(p::emit));}
            p.ack();var authoritative=p.reply;p.slots.set(44,changed);
            int clicks=p.clicks;long ticket=p.ticket;
            assertFalse(motor.tick(p::emit));assertEquals(ticket+1,p.ticket);assertEquals(clicks,p.clicks);
            if(outcome==0) {
                p.slots.set(44,original);p.ack();assertFalse(motor.tick(p::emit));
                p.complete(motor);assertEquals(1,p.takes);assertEquals(p.output,p.slots.get(9));
            } else {
                if(outcome==1) p.reply=authoritative;else p.ack();
                assertThrows(IOException.class,()->motor.tick(p::emit));
                assertEquals(ticket+1,p.ticket);assertEquals(clicks,p.clicks);
            }
        }
    }
    static GameActionLane.Motor startedFill(Port p) throws IOException {
        var motor=GameCrafting.start(p,1,p::emit);p.ack();assertFalse(motor.tick(p::emit));return motor;
    }
    @Test void initialClientMetadataCannotBecomeTheConservationBaseline() throws Exception {
        var p=new Port(1);var original=item("backpack",1);
        p.slots.set(44,new GameInventory.Stack(original.id(),1,"local-uuid"));
        var motor=GameCrafting.start(p,1,p::emit);
        assertEquals(0,p.fills);assertEquals(1,p.charges);
        for(int i=0;i<3;i++) assertFalse(motor.tick(p::emit));
        assertEquals(0,p.fills); // Prediction cannot cause a fill before the actual reply.
        p.slots.set(44,original);p.ack();assertFalse(motor.tick(p::emit));
        p.complete(motor);assertEquals(1,p.takes);assertEquals(original,p.slots.get(44));
    }
    static final GameInventory.Stack EMPTY = GameInventory.Stack.EMPTY;
    static GameInventory.Stack item(String id, int count) { return new GameInventory.Stack("test:" + id, count, "components"); }
    static final class Port implements GameCrafting.Port {
        final List<GameInventory.Stack> slots = new ArrayList<>();
        GameInventory.Stack cursor = EMPTY, output = item("result", 4), remainder = EMPTY;
        GameInventory.View reply;
        boolean valid = true, matched = true, placement = true;
        int fills, takes, clicks, charges, capacity = 64; long ticket;
        Port(int count) { for (int i = 0; i < 46; i++) slots.add(EMPTY); slots.set(9, item("ingredient", count)); }
        public int gridWidth() { return 2; }
        public int inventoryStart() { return 9; }
        public int inventoryEnd() { return 45; }
        public GameInventory.Stack output() { return output; }
        public void validate() throws IOException { if (!valid) throw new IOException("REVISION_CONFLICT"); }
        public GameInventory.View view() { return new GameInventory.View(slots, cursor, 0); }
        public int capacity(int slot, GameInventory.Stack stack) { return capacity; }
        public boolean mayPickup(int slot) { return true; }
        public boolean mayPlace(int slot, GameInventory.Stack stack) { return placement; }
        public void fillRecipe() {
            fills++; int source = -1;
            for (int i = 9; i < 45; i++) if (slots.get(i).id().equals("test:ingredient")) { source = i; break; }
            if (source < 0) return;
            var input = slots.get(source); slots.set(source, input.count() == 1 ? EMPTY : input.withCount(input.count() - 1));
            slots.set(1, input.withCount(1)); slots.set(0, output);
        }
        public List<GameInventory.Stack> remainders(GameInventory.View filled) throws IOException {
            if (!matched) throw new IOException("PRECONDITION_FAILED"); return List.of(remainder, EMPTY, EMPTY, EMPTY);
        }
        public void click(int slot, int button, boolean quick) {
            assertEquals(0, button); assertFalse(quick); clicks++;
            if (slot == 0) { takes++; cursor = output; slots.set(0, EMPTY); slots.set(1, remainder); }
            else { var previous = slots.get(slot); slots.set(slot, cursor); cursor = previous; }
        }
        public long requestSync() { reply = null; return ++ticket; }
        public GameInventory.View reply(long expected) { assertEquals(ticket, expected); return reply; }
        void ack() { reply = view(); }
        void emit(GameActionLane.Operation op) throws IOException { charges++; op.run(); }
        void complete(GameActionLane.Motor motor) throws IOException {
            for (int i = 0; i < 100; i++) { ack(); if (motor.tick(this::emit)) return; }
            fail("bounded toy craft did not finish");
        }
    }
    @Test void fillAndOutputPredictionNeverAuthorizeContinuationWithoutFeedback() throws Exception {
        var p = new Port(1); var motor = startedFill(p);
        assertEquals(3, p.charges); assertEquals(1, p.fills); assertEquals(0, p.clicks);
        for (int i = 0; i < 10; i++) assertFalse(motor.tick(p::emit));
        assertEquals(13, p.charges); assertEquals(0, p.clicks);
        p.ack(); assertFalse(motor.tick(p::emit)); assertEquals(1, p.takes);
        for (int i = 0; i < 10; i++) assertFalse(motor.tick(p::emit));
        assertEquals(1, p.clicks); p.complete(motor);
        assertEquals(p.output, p.slots.get(9)); assertTrue(p.cursor.empty());
    }
    @Test void repeatedRecipeConsumesOneSetAtATimeAndKeepsExactOutput() throws Exception {
        var p = new Port(2); var motor = GameCrafting.start(p, 2, p::emit); p.complete(motor);
        assertEquals(2, p.fills); assertEquals(2, p.takes); assertEquals(4, p.clicks);
        assertEquals(p.output, p.slots.get(9)); assertEquals(p.output, p.slots.get(10));
        assertTrue(p.cursor.empty()); assertTrue(p.slots.subList(0, 5).stream().allMatch(GameInventory.Stack::empty));
    }
    @Test void returnedContainerIsConfirmedAndStoredWithoutDroppingOrQuickMove() throws Exception {
        var p = new Port(1); p.remainder = item("container", 1);
        var motor = startedFill(p); p.complete(motor);
        assertEquals(p.output, p.slots.get(9)); assertEquals(p.remainder, p.slots.get(10));
        assertEquals(4, p.clicks); assertTrue(p.cursor.empty());
    }
    @Test void wrongFillGiftsBulkStackAndWrongRecipeCannotTakeOutput() throws Exception {
        for (int fault = 0; fault < 4; fault++) {
            var p = new Port(1); var motor = startedFill(p);
            if (fault == 0) p.slots.set(12, item("gift", 1));
            if (fault == 1) { p.slots.set(1, item("ingredient", 2)); }
            if (fault == 2) p.slots.set(0, item("wrong", 4));
            if (fault == 3) p.matched = false;
            p.ack(); assertThrows(IOException.class, () -> motor.tick(p::emit)); assertEquals(0, p.takes);
        }
    }
    @Test void outputRejectionWrongConsumptionAndRemainderDriftStopFurtherClicks() throws Exception {
        for (int fault = 0; fault < 3; fault++) {
            var p = new Port(1); var motor = startedFill(p); p.ack(); motor.tick(p::emit);
            if (fault == 0) p.cursor = EMPTY;
            if (fault == 1) p.slots.set(1, item("ingredient", 1));
            if (fault == 2) p.slots.set(12, item("changed", 1));
            p.ack(); assertThrows(IOException.class, () -> motor.tick(p::emit)); assertEquals(1, p.clicks);
        }
    }
    @Test void resourcesCursorDirtyGridAndCountBoundsRejectBeforeFill() {
        for (int fault = 0; fault < 5; fault++) {
            var p = new Port(1); int count = 1;
            if (fault == 0) p.cursor = item("held", 1);
            if (fault == 1) p.slots.set(1, item("occupied", 1));
            if (fault == 2) for (int i = 9; i < 45; i++) p.slots.set(i, item("occupied", 64));
            if (fault == 3) count = 0; if (fault == 4) count = 65;
            final int requested = count;
            assertThrows(IOException.class, () -> GameCrafting.start(p, requested, p::emit)); assertEquals(0, p.charges);
        }
    }
    @Test void missingRecipeResourcesReturnNoOutputAndNeverRetryFill() throws Exception {
        var p = new Port(1); p.slots.set(9, EMPTY); var motor = startedFill(p);
        p.ack(); assertThrows(IOException.class, () -> motor.tick(p::emit)); assertEquals(1, p.fills); assertEquals(0, p.takes);
    }
    @Test void reserveRemainderSpaceCapacityAndPermissionBeforeTakingOutput() throws Exception {
        for (int fault = 0; fault < 3; fault++) {
            var p = new Port(2); p.remainder = item("container", 1);
            if (fault == 0) for (int i = 11; i < 45; i++) p.slots.set(i, item("occupied", 64));
            if (fault == 1) p.capacity = 1; if (fault == 2) p.placement = false;
            var motor = startedFill(p); p.ack();
            assertThrows(IOException.class, () -> motor.tick(p::emit)); assertEquals(0, p.takes);
        }
    }
    @Test void changedMenuAndInterveningStateInvalidateFeedback() throws Exception {
        for (boolean changedMenu : List.of(false, true)) {
            var p = new Port(1); var motor = startedFill(p); p.ack();
            if (changedMenu) p.valid = false; else p.slots.set(15, item("new", 1));
            assertThrows(IOException.class, () -> motor.tick(p::emit)); assertEquals(0, p.clicks);
        }
    }
    @Test void exhaustedRefreshOrCancelledTickDoesNotReplayFillOrTake() throws Exception {
        var p = new Port(1);
        var pending=GameCrafting.start(p,1,p::emit);p.ack();
        assertThrows(IOException.class, () -> pending.tick(op -> {
            if (++p.charges == 3) throw new IOException("BUDGET_EXHAUSTED"); op.run();
        }));
        assertEquals(1, p.fills); assertEquals(1, p.ticket);
        var next = new Port(1); var motor = startedFill(next); next.ack();
        assertThrows(IOException.class, () -> motor.tick(op -> { throw new IOException("CANCELLED"); }));
        assertEquals(1, next.fills); assertEquals(0, next.takes);
    }
}
