package io.github.opencnid.strata.client;

import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

/** Explicit ordinary close, never an implicit side effect of movement or another action. */
final class GameMenuClose {
    static final String POLICY = "explicit-close-own-inventory-feedback-conservation/1";
    // Inventory indices here are native inventory-menu slots 5..45 (armor, main/hotbar, offhand).
    record State(List<GameInventory.Stack> inventory, List<GameInventory.Stack> returning) {
        State { inventory = List.copyOf(inventory); returning = List.copyOf(returning); }
        GameInventory.View total() {
            var stacks = new ArrayList<>(inventory); stacks.addAll(returning);
            return new GameInventory.View(stacks, GameInventory.Stack.EMPTY, -1);
        }
    }
    interface Port {
        void validate() throws IOException;
        State read() throws IOException;
        int capacity(int inventoryIndex, GameInventory.Stack item) throws IOException;
        void close() throws IOException;
        long requestSync() throws IOException;
        State reply(long ticket) throws IOException;
    }
    static void bounds(State state) throws IOException {
        if (state.inventory.size() != 41 || state.returning.size() > 10
                || state.total().slots().stream().anyMatch(item -> item.count() < 0 || item.count() > 64)) {
            throw new IOException("GAME_CONTAINER_UNSUPPORTED");
        }
    }
    static void capacity(Port port, State state) throws IOException {
        bounds(state); var projected = new ArrayList<>(state.inventory);
        for (var item : state.returning) {
            int remaining = item.count();
            // Simulate only capacity, never modify real slots. Merge before reserving empties.
            for (boolean empty : new boolean[]{false, true}) {
                for (int slot = 4; slot < 41 && remaining > 0; slot++) {
                    if (empty && slot == 40) continue; // Merge into an existing offhand stack, never equip.
                    var target = projected.get(slot);
                    if (empty ? !target.empty() : !target.same(item)) continue;
                    int limit = port.capacity(slot, item);
                    if (limit < 0 || limit > 64) throw new IOException("GAME_CONTAINER_UNSUPPORTED");
                    int moved = Math.min(remaining, Math.max(0, limit - target.count()));
                    if (moved > 0) { projected.set(slot, item.withCount(target.count() + moved)); remaining -= moved; }
                }
            }
            if (remaining != 0) throw new IOException("INVENTORY_FULL");
        }
    }
    static GameActionLane.Motor start(Port port, GameActionLane.Emitter emit) throws IOException {
        port.validate(); State before = port.read(); capacity(port, before);
        emit.invoke(port::close);
        long[] ticket = {0}; emit.invoke(() -> ticket[0] = port.requestSync());
        return next -> {
            port.validate(); State reply = port.reply(ticket[0]);
            if (reply == null) { next.invoke(() -> {}); return false; }
            bounds(reply);
            if (!reply.equals(port.read())) throw new IOException("REVISION_CONFLICT");
            if (reply.returning.stream().anyMatch(item -> !item.empty()) || !GameInventory.conserved(before.total(), reply.total())) {
                throw new IOException("PRECONDITION_FAILED");
            }
            for (int slot = 0; slot < 4; slot++) if (!before.inventory.get(slot).equals(reply.inventory.get(slot))) {
                throw new IOException("PRECONDITION_FAILED"); // Ordinary return never equips armor.
            }
            return true;
        };
    }
}
