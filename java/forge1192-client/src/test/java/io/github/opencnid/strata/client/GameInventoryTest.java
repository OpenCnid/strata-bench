package io.github.opencnid.strata.client;

import java.io.IOException;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

/** Independent scripted predictions/replies. No Minecraft/server effect claim. */
class GameInventoryTest {
    @Test void derivedPreviewUpdateDoesNotInvalidateConfirmedOwnedTransfer() throws Exception {
        var before=view(Map.of(1,stack("minecraft:andesite",1),2,stack("minecraft:andesite",1)),stack("minecraft:andesite",3),0);
        var received=view(Map.of(1,stack("minecraft:andesite",1),2,stack("minecraft:andesite",1),3,stack("minecraft:andesite",1)),stack("minecraft:andesite",2),0);
        var port=new Port(before,received);
        var motor=GameInventory.click(port,3,true,false,port::emit);port.ack();
        var slots=new ArrayList<>(received.slots());slots.set(0,stack("minecraft:andesite_slab",6));
        port.current=new GameInventory.View(slots,received.cursor(),0);
        assertTrue(motor.tick(port::emit));assertEquals(List.of(3),port.clicks);assertEquals(2,port.charges);
        assertThrows(IOException.class,()->GameInventory.click(port,0,false,false,port::emit));
        slots.set(10,stack("minecraft:diamond",1));
        assertFalse(GameInventory.sameOwned(received,new GameInventory.View(slots,received.cursor(),0)));
        assertFalse(GameInventory.sameOwned(received,new GameInventory.View(received.slots(),stack("minecraft:andesite",1),0)));
    }
    static GameInventory.Stack stack(String id, int count) { return new GameInventory.Stack(id, count, "component-identity"); }
    static GameInventory.View view(Map<Integer, GameInventory.Stack> values, GameInventory.Stack cursor, int preview) {
        var slots = new ArrayList<GameInventory.Stack>();
        for (int i = 0; i < 46; i++) slots.add(values.getOrDefault(i, GameInventory.Stack.EMPTY));
        return new GameInventory.View(slots, cursor, preview);
    }
    static GameInventory.View view(Map<Integer, GameInventory.Stack> values) { return view(values, GameInventory.Stack.EMPTY, 0); }
    static final class Port implements GameInventory.Port {
        GameInventory.View current, feedback;
        final ArrayDeque<GameInventory.View> predicted = new ArrayDeque<>();
        final List<Integer> clicks = new ArrayList<>();
        boolean valid = true, mayPlace = true, mayPickup = true;
        int capacity = 64, refreshes, charges; long ticket;
        Port(GameInventory.View initial, GameInventory.View... predictions) {
            current = initial; predicted.addAll(List.of(predictions));
        }
        public void validate() throws IOException { if (!valid) throw new IOException("REVISION_CONFLICT"); }
        public GameInventory.View view() { return current; }
        public int capacity(int slot, GameInventory.Stack stack) { return capacity; }
        public boolean mayPlace(int slot, GameInventory.Stack stack) { return mayPlace; }
        public boolean mayPickup(int slot) { return mayPickup; }
        public void click(int slot, int button, boolean quick) {
            clicks.add(slot); if (!predicted.isEmpty()) current = predicted.removeFirst();
        }
        public long requestSync() { refreshes++; feedback = null; return ++ticket; }
        public GameInventory.View reply(long expected) throws IOException {
            if (expected != ticket) throw new IOException("STALE_FEEDBACK"); return feedback;
        }
        void ack() { feedback = current; }
        void emit(GameActionLane.Operation operation) throws IOException { charges++; operation.run(); }
    }
    @Test void predictedSlotsNeverFinishOrTriggerAnotherClickWithoutServerFeedback() throws Exception {
        var stone = stack("minecraft:stone", 3);
        var p = new Port(view(Map.of(10, stone)), view(Map.of(), stone, 0));
        var motor = GameInventory.click(p, 10, false, false, p::emit);
        assertEquals(2, p.charges); assertEquals(List.of(10), p.clicks);
        for (int i = 0; i < 20; i++) assertFalse(motor.tick(p::emit));
        assertEquals(22, p.charges); assertEquals(1, p.refreshes); // Twenty charged wait ticks, no repeated click/refresh.
        p.ack(); assertTrue(motor.tick(p::emit));
    }
    @Test void rejectedOrWrongServerStateCannotConfirmPredictedPickup() throws Exception {
        var before = view(Map.of(10, stack("minecraft:stone", 3)));
        var p = new Port(before, view(Map.of(), stack("minecraft:stone", 3), 0));
        var motor = GameInventory.click(p, 10, false, false, p::emit);
        p.feedback = before;
        assertThrows(IOException.class, () -> motor.tick(p::emit)); assertEquals(List.of(10), p.clicks);
    }
    @Test void rightPickupAndSinglePlacementPreserveRemaindersAndCapacity() throws Exception {
        var p = new Port(view(Map.of(10, stack("minecraft:stone", 5))),
            view(Map.of(10, stack("minecraft:stone", 2)), stack("minecraft:stone", 3), 0));
        var motor = GameInventory.click(p, 10, true, false, p::emit); p.ack(); assertTrue(motor.tick(p::emit));
        p = new Port(view(Map.of(10, stack("minecraft:stone", 63)), stack("minecraft:stone", 3), 0),
            view(Map.of(10, stack("minecraft:stone", 64)), stack("minecraft:stone", 2), 0));
        motor = GameInventory.click(p, 10, true, false, p::emit); p.ack(); assertTrue(motor.tick(p::emit));
        p = new Port(view(Map.of(10, stack("minecraft:stone", 64)), stack("minecraft:stone", 2), 0));
        motor = GameInventory.click(p, 10, true, false, p::emit); p.ack(); assertTrue(motor.tick(p::emit));
    }
    @Test void serverGiftsLossAndComponentReplacementFailConservation() throws Exception {
        for (var changed : List.of(stack("minecraft:stone", 4), stack("minecraft:stone", 2),
                new GameInventory.Stack("minecraft:stone", 3, "changed-components"))) {
            var p = new Port(view(Map.of(10, stack("minecraft:stone", 3))), view(Map.of(), stack("minecraft:stone", 3), 0));
            var motor = GameInventory.click(p, 10, false, false, p::emit);
            p.current = view(Map.of(), changed, 0); p.ack();
            assertThrows(IOException.class, () -> motor.tick(p::emit));
        }
    }
    @Test void cursorCountsEvenWhenMenuHasNoCraftingResultPreview() {
        var before = view(Map.of(10, stack("minecraft:stone", 3)), GameInventory.Stack.EMPTY, -1);
        assertTrue(GameInventory.conserved(before, view(Map.of(), stack("minecraft:stone", 3), -1)));
        assertFalse(GameInventory.conserved(before, view(Map.of(), stack("minecraft:stone", 4), -1)));
        var preview = view(Map.of(0, stack("minecraft:stone", 1), 10, stack("minecraft:dirt", 2)));
        assertTrue(GameInventory.conserved(preview, view(Map.of(0, stack("minecraft:diamond", 1), 10, stack("minecraft:dirt", 2)))));
    }
    @Test void quickMoveRequiresServerTransferAndPreservesAllItemIdentities() throws Exception {
        var before = view(Map.of(10, stack("minecraft:stone", 3)));
        var p = new Port(before, view(Map.of(36, stack("minecraft:stone", 3))));
        var motor = GameInventory.click(p, 10, false, true, p::emit); p.ack(); assertTrue(motor.tick(p::emit));
        var rejected = new Port(before);
        var noOp = GameInventory.click(rejected, 10, false, true, rejected::emit); rejected.ack();
        assertThrows(IOException.class, () -> noOp.tick(rejected::emit));
    }
    @Test void equipmentUsesAtMostThreeExplicitConfirmedClicksAndReturnsDisplacedItem() throws Exception {
        var helmet = stack("minecraft:iron_helmet", 1); var old = stack("minecraft:leather_helmet", 1);
        var p = new Port(view(Map.of(10, helmet, 5, old)),
            view(Map.of(5, old), helmet, 0), view(Map.of(5, helmet), old, 0), view(Map.of(5, helmet, 10, old)));
        p.capacity = 1;
        var motor = GameInventory.equip(p, 10, 5, helmet.id(), p::emit);
        assertEquals(List.of(10), p.clicks); assertFalse(motor.tick(p::emit));
        p.ack(); assertFalse(motor.tick(p::emit)); assertEquals(List.of(10, 5), p.clicks);
        assertFalse(motor.tick(p::emit)); // Destination prediction cannot authorize returning the cursor.
        p.ack(); assertFalse(motor.tick(p::emit)); assertEquals(List.of(10, 5, 10), p.clicks);
        p.ack(); assertTrue(motor.tick(p::emit)); assertEquals(8, p.charges); assertEquals(3, p.refreshes);
    }
    @Test void menuReplacementAndInterveningUpdatesStopEquipmentContinuation() throws Exception {
        var item = stack("minecraft:stone", 1);
        for (boolean replaced : List.of(false, true)) {
            var p = new Port(view(Map.of(10, item)), view(Map.of(), item, 0));
            var motor = GameInventory.equip(p, 10, 36, item.id(), p::emit);
            p.ack(); if (replaced) p.valid = false; else p.current = view(Map.of(12, item));
            assertThrows(IOException.class, () -> motor.tick(p::emit)); assertEquals(List.of(10), p.clicks);
        }
    }
    @Test void missingResourcesInvalidSlotsAndSlotPermissionsEmitNothing() {
        for (int slot : new int[]{-1, 0, 46}) {
            var p = new Port(view(Map.of(10, stack("minecraft:stone", 1))));
            assertThrows(IOException.class, () -> GameInventory.click(p, slot, false, false, p::emit)); assertEquals(0, p.charges);
        }
        var p = new Port(view(Map.of(10, stack("minecraft:stone", 1)))); p.mayPlace = false;
        assertThrows(IOException.class, () -> GameInventory.equip(p, 10, 36, "minecraft:stone", p::emit)); assertEquals(0, p.charges);
        assertThrows(IOException.class, () -> GameInventory.equip(p, 11, 36, "minecraft:stone", p::emit)); assertEquals(0, p.charges);
        p.mayPickup = false;
        assertThrows(IOException.class, () -> GameInventory.click(p, 10, false, false, p::emit)); assertEquals(0, p.charges);
    }
    @Test void exhaustedRefreshChargeDoesNotResendTheAlreadyEmittedClick() {
        var stone = stack("minecraft:stone", 1);
        var p = new Port(view(Map.of(10, stone)), view(Map.of(), stone, 0));
        var charges = new java.util.concurrent.atomic.AtomicInteger();
        assertThrows(IOException.class, () -> GameInventory.click(p, 10, false, false, op -> {
            if (charges.incrementAndGet() == 2) throw new IOException("BUDGET_EXHAUSTED"); op.run();
        }));
        assertEquals(List.of(10), p.clicks); assertEquals(0, p.refreshes);
    }
}
