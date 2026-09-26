package io.github.opencnid.strata.client;

import java.io.IOException;

/** Establish an applied server baseline before emitting a machine-menu click. */
final class GameMachinePreflight {
    static final String POLICY = "thermal-visible-slot-server-baseline-owned-transfer/3";

    static GameActionLane.Motor start(GameInventory.Port port, GameMachineInventory.Layout layout,
                                     int slot, boolean right, boolean quick,
                                     GameActionLane.Operation inputFence,
                                     GameActionLane.Emitter emit) throws IOException {
        var initial = GameMachineInventory.validateClick(port, layout, slot, quick);
        long[] ticket = {0};
        emit.invoke(() -> ticket[0] = port.requestSync());
        return new GameActionLane.Motor() {
            GameActionLane.Motor transfer;
            public boolean tick(GameActionLane.Emitter next) throws IOException {
                if (transfer != null) return transfer.tick(next);
                port.validate();
                var received = port.reply(ticket[0]);
                if (received == null) { next.invoke(() -> {}); return false; }
                layout.check(received);
                // A read may take time: recheck the original delivered observation,
                // age, window revision and input permissions before any mutation.
                inputFence.run();
                var current = port.view(); layout.check(current);
                if (!received.equals(current) || !sameSelection(layout, initial, received, slot))
                    throw new IOException("REVISION_CONFLICT");
                // This is the first click, on the same client-thread call stack.
                // The transfer freezes this exact server-applied state and keeps
                // all existing prediction/conservation/post-click comparisons.
                transfer = GameMachineInventory.clickConfirmed(port, layout, received, slot, right, quick, next);
                return false;
            }
        };
    }

    private static boolean sameSelection(GameMachineInventory.Layout layout, GameInventory.View initial,
                                         GameInventory.View received, int clicked) {
        if (!initial.cursor().equals(received.cursor())) return false;
        for (int i = 0; i < layout.total(); i++) {
            var a = initial.slots().get(i); var b = received.slots().get(i);
            // Only untouched player metadata may be reacquired BEFORE input.
            // Never substitute a different selected item, resource or position.
            if (layout.player(i) && i != clicked) {
                if (!a.id().equals(b.id()) || a.count() != b.count()) return false;
            } else if (!a.equals(b)) return false;
        }
        return true;
    }

    private GameMachinePreflight() {}
}
