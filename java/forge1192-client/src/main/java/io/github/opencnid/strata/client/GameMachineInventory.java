package io.github.opencnid.strata.client;

import java.io.IOException;

/** One ordinary machine-menu click. Prediction is checked, never accepted as feedback.
 * Server processing may alter machine storage; only the exact owned-side transfer
 * is confirmed here. Machine production/provenance is not an action postcondition.
 */
final class GameMachineInventory {
    static final String POLICY = "thermal-visible-slot-owned-transfer-feedback/1";
    interface SlotSource { GameInventory.Stack read(int slot) throws IOException; }
    record Layout(GameMachineMenu.Kind kind, int augments) {
        Layout {
            if (kind == null || augments < 0 || augments > 9) throw new IllegalArgumentException("invalid machine layout");
        }
        int playerStart() { return kind.baseSlots + augments; }
        int total() { return playerStart() + 36; }
        boolean visible(int slot) { return slot >= 0 && (slot < kind.baseSlots || slot >= playerStart() && slot < total()); }
        boolean player(int slot) { return slot >= playerStart() && slot < total(); }
        void check(GameInventory.View view) throws IOException {
            if (view.slots().size() != total() || view.resultSlot() != -1) throw new IOException("GAME_CONTAINER_UNSUPPORTED");
        }
    }
    static GameInventory.View project(Layout layout, SlotSource source, GameInventory.Stack cursor) throws IOException {
        var slots = new java.util.ArrayList<GameInventory.Stack>();
        for (int i = 0; i < layout.total(); i++)
            slots.add(layout.visible(i) ? source.read(i) : GameInventory.Stack.EMPTY);
        return new GameInventory.View(slots, cursor, -1);
    }
    static GameActionLane.Motor click(GameInventory.Port port, Layout layout, int slot, boolean right, boolean quick,
                                     GameActionLane.Emitter emit) throws IOException {
        port.validate(); var before = port.view(); layout.check(before);
        if (!layout.visible(slot) || quick && layout.player(slot)) throw new IOException("MECHANIC_UNSUPPORTED");
        var target = before.slots().get(slot); var cursor = before.cursor();
        if (target.empty() && cursor.empty() || quick && (!cursor.empty() || target.empty()))
            throw new IOException("PRECONDITION_FAILED");
        if (!target.empty() && !port.mayPickup(slot)) throw new IOException("PRECONDITION_FAILED");
        if (!quick && !cursor.empty() && !port.mayPlace(slot, cursor)
                && (target.empty() || !target.same(cursor))) throw new IOException("PRECONDITION_FAILED");
        return new Step(port, layout, before, slot, right, quick, emit);
    }
    private static final class Step implements GameActionLane.Motor {
        final GameInventory.Port port; final Layout layout;
        GameInventory.View predicted; IOException predictionFailure; long ticket;
        Step(GameInventory.Port port, Layout layout, GameInventory.View before, int slot, boolean right, boolean quick,
             GameActionLane.Emitter emit) throws IOException {
            this.port = port; this.layout = layout;
            emit.invoke(() -> {
                port.click(slot, right ? 1 : 0, quick);
                try {
                    // Same client-thread call stack: ordinary native menu mechanics
                    // have predicted the click, with no intervening network tasks.
                    predicted = port.view(); checkPrediction(layout, before, predicted, slot, quick);
                } catch (IOException failure) { predictionFailure = failure; }
            });
            // Even a rejected prediction needs authoritative resynchronization
            // after an already-emitted click. Never replay that click to repair it.
            emit.invoke(() -> ticket = port.requestSync());
        }
        public boolean tick(GameActionLane.Emitter emit) throws IOException {
            port.validate(); var received = port.reply(ticket);
            if (received == null) { emit.invoke(() -> {}); return false; }
            layout.check(received);
            if (predictionFailure != null) throw predictionFailure;
            requireOwned(layout, predicted, received);
            // A later GUI update may advance processing, but cannot alter the
            // confirmed owned inventory/cursor before this terminal receipt.
            var current = port.view(); layout.check(current); requireOwned(layout, received, current);
            return true;
        }
    }
    private static void checkPrediction(Layout layout, GameInventory.View before, GameInventory.View after,
                                        int slot, boolean quick) throws IOException {
        layout.check(after);
        if (!GameInventory.conserved(before, after) || before.equals(after)) throw new IOException("PRECONDITION_FAILED");
        for (int i = 0; i < layout.total(); i++) {
            if (i == slot || quick && layout.player(i)) continue;
            if (!before.slots().get(i).equals(after.slots().get(i))) throw new IOException("PRECONDITION_FAILED");
        }
        if (quick) {
            var start = before.slots().get(slot); var end = after.slots().get(slot);
            if (!before.cursor().equals(after.cursor()) || !end.empty() && (!end.same(start) || end.count() >= start.count()))
                throw new IOException("PRECONDITION_FAILED");
        }
    }
    private static void requireOwned(Layout layout, GameInventory.View expected, GameInventory.View actual) throws IOException {
        if (!expected.cursor().equals(actual.cursor())) throw new IOException("GAME_MACHINE_TRANSFER_UNCONFIRMED");
        for (int i = layout.playerStart(); i < layout.total(); i++)
            if (!expected.slots().get(i).equals(actual.slots().get(i))) throw new IOException("GAME_MACHINE_TRANSFER_UNCONFIRMED");
    }
}
