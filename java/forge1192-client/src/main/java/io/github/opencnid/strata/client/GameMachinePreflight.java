package io.github.opencnid.strata.client;

import java.io.IOException;

/** Establish an applied server baseline before emitting a machine-menu click. */
final class GameMachinePreflight {
    static final String POLICY = "thermal-visible-slot-server-baseline-owned-transfer/4";

    static GameActionLane.Motor start(GameInventory.Port port, GameMachineInventory.Layout layout,
                                     int slot, boolean right, boolean quick,
                                     GameActionLane.Operation inputFence,
                                     GameActionLane.Emitter emit) throws IOException {
        var initial = GameMachineInventory.validateClick(port, layout, slot, quick);
        long[] ticket = {0};
        emit.invoke(() -> ticket[0] = port.requestSync());
        return new GameActionLane.Motor() {
            GameActionLane.Motor transfer;
            GameInventory.View reacquireBaseline;
            public boolean tick(GameActionLane.Emitter next) throws IOException {
                if (transfer != null) return transfer.tick(next);
                var phase = GameMachinePreflightFailure.Phase.CONTEXT;
                GameInventory.View expected = null, actual = null;
                try {
                    port.validate();
                    phase = GameMachinePreflightFailure.Phase.REPLY;
                    var received = port.reply(ticket[0]);
                    if (received == null) {
                        phase = GameMachinePreflightFailure.Phase.WAIT;
                        next.invoke(() -> {}); return false;
                    }
                    phase = GameMachinePreflightFailure.Phase.REPLY_LAYOUT;
                    layout.check(received);
                    // Recheck original observation age/revision before input.
                    phase = GameMachinePreflightFailure.Phase.INPUT_FENCE;
                    inputFence.run();
                    if (reacquireBaseline != null) {
                        phase = GameMachinePreflightFailure.Phase.REACQUIRED_BASELINE;
                        expected = reacquireBaseline; actual = received;
                        // A second read must restore the FIRST exact server
                        // state, never establish a more convenient baseline.
                        if (!received.equals(reacquireBaseline)) throw new IOException("REVISION_CONFLICT");
                    }
                    expected = null; actual = null;
                    phase = GameMachinePreflightFailure.Phase.CURRENT_VIEW;
                    var current = port.view();
                    phase = GameMachinePreflightFailure.Phase.CURRENT_LAYOUT;
                    layout.check(current);
                    phase = GameMachinePreflightFailure.Phase.CURRENT_MATCH;
                    expected = received; actual = current;
                    if (!received.equals(current)) {
                        if (reacquireBaseline == null
                                && sameSelection(layout, initial, received, slot)
                                && sameSelection(layout, received, current, slot)) {
                            // One charged read for untouched player component
                            // drift only. No mutation has occurred. The original
                            // observation fence, deadline and budget still apply.
                            reacquireBaseline = received;
                            next.invoke(() -> ticket[0] = port.requestSync());
                            return false;
                        }
                        throw new IOException("REVISION_CONFLICT");
                    }
                    phase = GameMachinePreflightFailure.Phase.SELECTION_MATCH;
                    expected = initial; actual = received;
                    if (!sameSelection(layout, initial, received, slot)) throw new IOException("REVISION_CONFLICT");
                    phase = GameMachinePreflightFailure.Phase.TRANSFER_START;
                    expected = null; actual = null;
                    // Same client-thread stack; original exact transfer rules.
                    transfer = GameMachineInventory.clickConfirmed(port, layout, received, slot, right, quick, next);
                    return false;
                } catch (GameMachinePreflightFailure failure) {
                    throw failure; // Keep the final-baseline comparison, if present.
                } catch (IOException failure) {
                    throw new GameMachinePreflightFailure(phase, failure, layout, slot, expected, actual);
                }
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
