package io.github.opencnid.strata.client;

import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;

/** Fixed menu motor. Predicted slots never satisfy a server-feedback requirement. */
final class GameInventory {
    record Stack(String id, int count, String components) {
        static final Stack EMPTY = new Stack("", 0, "");
        boolean empty() { return count == 0; }
        Stack withCount(int n) { return n == 0 ? EMPTY : new Stack(id, n, components); }
        boolean same(Stack other) { return !empty() && !other.empty() && id.equals(other.id) && components.equals(other.components); }
    }
    record View(List<Stack> slots, Stack cursor, int resultSlot) {
        View { slots = List.copyOf(slots); }
    }
    interface Port {
        void validate() throws IOException;
        View view() throws IOException;
        int capacity(int slot, Stack item) throws IOException;
        boolean mayPickup(int slot) throws IOException;
        boolean mayPlace(int slot, Stack item) throws IOException;
        void click(int slot, int button, boolean quickMove) throws IOException;
        long requestSync() throws IOException;
        View reply(long ticket) throws IOException; // null until actual full server contents arrive
    }
    private record Expected(View before, int slot, Stack target, Stack cursor, boolean quickMove) {}
    static GameActionLane.Motor click(Port port, int slot, boolean right, boolean quickMove,
                                     GameActionLane.Emitter emit) throws IOException {
        return new Steps(port, List.of(slot), right, quickMove, -1, null, emit);
    }
    static GameActionLane.Motor equip(Port port, int source, int destination, String expectedId,
                                     GameActionLane.Emitter emit) throws IOException {
        port.validate(); View view = port.view();
        if (view.slots.size() != 46 || source < 5 || source > 45 || destination < 5 || destination > 45
                || !view.cursor.empty() || !view.slots.get(source).id.equals(expectedId)) throw new IOException("PRECONDITION_FAILED");
        if (!port.mayPlace(destination, view.slots.get(source))) throw new IOException("PRECONDITION_FAILED");
        if (source == destination) return ignored -> true;
        return new Steps(port, List.of(source, destination), false, false, source, expectedId, emit);
    }
    private static final class Steps implements GameActionLane.Motor {
        final Port port; final List<Integer> slots; final boolean right, quick;
        final int returnSlot; final String equippedId; final int destination;
        int index; long ticket; Expected expected;
        Steps(Port port, List<Integer> slots, boolean right, boolean quick, int returnSlot, String equippedId,
              GameActionLane.Emitter emit) throws IOException {
            this.port = port; this.slots = new ArrayList<>(slots); this.right = right; this.quick = quick;
            this.returnSlot = returnSlot; this.equippedId = equippedId; destination = slots.get(slots.size() - 1);
            next(emit);
        }
        void next(GameActionLane.Emitter emit) throws IOException {
            port.validate();
            View before = port.view(); int slot = slots.get(index);
            expected = predict(port, before, slot, right, quick);
            emit.invoke(() -> port.click(slot, right ? 1 : 0, quick));
            emit.invoke(() -> ticket = port.requestSync());
        }
        public boolean tick(GameActionLane.Emitter emit) throws IOException {
            port.validate(); View received = port.reply(ticket);
            if (received == null) { emit.invoke(() -> {}); return false; } // Charge the active feedback-wait motor tick.
            verify(expected, received);
            // The native handler has applied this exact reply; unsolicited changes
            // between reply and continuation invalidate the rest of the fixed motor.
            if (!received.equals(port.view())) throw new IOException("REVISION_CONFLICT");
            index++;
            if (returnSlot >= 0 && index == 2 && !received.cursor.empty()) slots.add(returnSlot);
            if (index < slots.size()) { next(emit); return false; }
            if (equippedId != null && (!received.cursor.empty() || !received.slots.get(destination).id.equals(equippedId))) {
                throw new IOException("PRECONDITION_FAILED");
            }
            return true;
        }
    }
    private static Expected predict(Port port, View view, int slot, boolean right, boolean quick) throws IOException {
        if (slot < 0 || slot >= view.slots.size() || slot == view.resultSlot) throw new IOException("MECHANIC_UNSUPPORTED");
        Stack target = view.slots.get(slot), cursor = view.cursor;
        if (!target.empty() && !port.mayPickup(slot)) throw new IOException("PRECONDITION_FAILED");
        if (quick) {
            if (!cursor.empty() || target.empty()) throw new IOException("PRECONDITION_FAILED");
            return new Expected(view, slot, target, cursor, true);
        }
        Stack afterTarget = target, afterCursor = cursor;
        if (cursor.empty()) {
            if (!target.empty()) {
                int moved = right ? (target.count + 1) / 2 : target.count;
                afterCursor = target.withCount(moved); afterTarget = target.withCount(target.count - moved);
            }
        } else {
            if (!port.mayPlace(slot, cursor)) throw new IOException("PRECONDITION_FAILED");
            int capacity = port.capacity(slot, cursor);
            if (target.empty() || target.same(cursor)) {
                int moved = Math.min(right ? 1 : cursor.count, Math.max(0, capacity - target.count));
                afterTarget = cursor.withCount(target.count + moved); afterCursor = cursor.withCount(cursor.count - moved);
            } else {
                if (cursor.count > capacity) throw new IOException("PRECONDITION_FAILED");
                afterTarget = cursor; afterCursor = target;
            }
        }
        return new Expected(view, slot, afterTarget, afterCursor, false);
    }
    private static void verify(Expected expected, View actual) throws IOException {
        View before = expected.before;
        if (before.slots.size() != actual.slots.size() || before.resultSlot != actual.resultSlot
                || !conserved(before, actual)) throw new IOException("PRECONDITION_FAILED");
        Stack target = actual.slots.get(expected.slot);
        if (expected.quickMove) {
            if (!actual.cursor.empty() || target.same(expected.target) && target.count >= expected.target.count) {
                throw new IOException("PRECONDITION_FAILED");
            }
        } else if (!Objects.equals(expected.target, target) || !Objects.equals(expected.cursor, actual.cursor)) {
            throw new IOException("PRECONDITION_FAILED");
        }
    }
    static boolean conserved(View before, View after) {
        var totals = new java.util.HashMap<String, Long>();
        for (int direction : new int[]{1, -1}) {
            View view = direction == 1 ? before : after;
            for (int i = -1; i < view.slots.size(); i++) {
                if (i >= 0 && i == view.resultSlot) continue;
                Stack stack = i == -1 ? view.cursor : view.slots.get(i);
                if (!stack.empty()) totals.merge(stack.id + "\n" + stack.components, direction * (long) stack.count, Long::sum);
            }
        }
        return totals.values().stream().allMatch(total -> total == 0);
    }
}
