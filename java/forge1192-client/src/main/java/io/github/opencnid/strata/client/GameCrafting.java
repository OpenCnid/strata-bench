package io.github.opencnid.strata.client;

import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

/** One requested recipe. Normal book-fill and slot inputs always await actual menu feedback. */
final class GameCrafting {
    static final String POLICY = "known-recipe-server-preview-bound20/5";
    static final int MAX_PREVIEW_READS = 20;
    interface Port extends GameInventory.Port {
        int gridWidth();
        int inventoryStart();
        int inventoryEnd(); // exclusive; no armor/offhand or unopened storage
        GameInventory.Stack output();
        void fillRecipe() throws IOException;
        /** Optional ordinary manual grid fill; null retains the existing book-fill path. */
        default GameActionLane.Motor gridMotor(GameActionLane.Emitter emit) throws IOException { return null; }
        /** Validate this exact filled grid/recipe and derive native remaining items from its own stacks. */
        List<GameInventory.Stack> remainders(GameInventory.View filled) throws IOException;
    }
    static GameActionLane.Motor start(Port port, int count, GameActionLane.Emitter emit) throws IOException {
        if (count < 1 || count > 64 || port.gridWidth() < 2 || port.gridWidth() > 3) throw new IOException("GAME_CRAFT_BOUNDS");
        return new Motor(port, count, emit);
    }
    private static final class Motor implements GameActionLane.Motor {
        enum Phase { BASELINE, FILL, MANUAL_FILL, TAKE, STORE, REMAINDER_PICKUP, REMAINDER_STORE }
        final Port port; final int gridSize; int remaining, remainderIndex;
        Phase phase; long ticket;
        GameInventory.View before, filled, taken, reacquireBaseline, previewBaseline;
        int previewReads;
        List<GameInventory.Stack> remainders;
        List<Integer> destinations;
        GameActionLane.Motor step;
        Motor(Port port, int count, GameActionLane.Emitter emit) throws IOException {
            this.port = port; remaining = count; gridSize = port.gridWidth() * port.gridWidth(); fill(emit);
        }
        private GameInventory.View view() throws IOException {
            port.validate(); var view = port.view();
            if (view.resultSlot() != 0 || view.slots().size() > 1024 || port.inventoryStart() <= gridSize
                    || port.inventoryEnd() <= port.inventoryStart() || port.inventoryEnd() > view.slots().size()
                    || port.output().empty() || port.output().count() > 64) throw new IOException("GAME_CRAFT_CONTEXT_UNSUPPORTED");
            return view;
        }
        private void fill(GameActionLane.Emitter emit) throws IOException {
            reacquireBaseline = null;
            previewBaseline = null; previewReads = 0;
            requireClean(view());
            // Local component materialization is not a resource baseline. Take
            // the first snapshot from actual server feedback before any fill.
            phase = Phase.BASELINE;
            emit.invoke(() -> ticket = port.requestSync());
        }
        private void requireClean(GameInventory.View value) throws IOException {
            if (!value.cursor().empty()) throw new IOException("PRECONDITION_FAILED");
            for (int i = 0; i <= gridSize; i++) if (!value.slots().get(i).empty()) throw new IOException("PRECONDITION_FAILED");
            if (emptyDestinations(value).isEmpty()) throw new IOException("INVENTORY_FULL");
        }
        private void startFill(GameActionLane.Emitter emit) throws IOException {
            requireClean(before);
            reacquireBaseline = null;
            step = port.gridMotor(emit);
            if (step != null) { phase = Phase.MANUAL_FILL; return; }
            phase = Phase.FILL;
            emit.invoke(port::fillRecipe);
            emit.invoke(() -> ticket = port.requestSync());
        }
        private List<Integer> emptyDestinations(GameInventory.View view) {
            var result = new ArrayList<Integer>();
            for (int i = port.inventoryStart(); i < port.inventoryEnd(); i++) if (view.slots().get(i).empty()) result.add(i);
            return result;
        }
        private GameInventory.View feedback(GameActionLane.Emitter emit) throws IOException {
            port.validate(); var reply = port.reply(ticket);
            if (reply == null) { emit.invoke(() -> {}); return null; }
            // The first actual reply remains the exact authority for a retry.
            // A new server component, output, grid or remainder cannot replace it.
            if (reacquireBaseline != null && !reply.equals(reacquireBaseline)) throw new IOException("REVISION_CONFLICT");
            var current = view();
            if (!reply.equals(current)) {
                port.mismatch(reply,current);
                boolean metadataOnly = reply.slots().size()==current.slots().size()
                    && reply.resultSlot()==current.resultSlot() && reply.cursor().equals(current.cursor());
                for (int i=0;metadataOnly && i<reply.slots().size();i++) {
                    var a=reply.slots().get(i);var b=current.slots().get(i);
                    metadataOnly = i>=port.inventoryStart() && i<port.inventoryEnd()
                        ? a.id().equals(b.id()) && a.count()==b.count() : a.equals(b);
                }
                if (reacquireBaseline == null && metadataOnly) {
                    reacquireBaseline = reply;
                    emit.invoke(() -> ticket = port.requestSync()); return null;
                }
                throw new IOException("REVISION_CONFLICT");
            }
            return reply;
        }
        public boolean tick(GameActionLane.Emitter emit) throws IOException {
            port.validate();
            if (phase == Phase.BASELINE) {
                before = feedback(emit); if (before == null) return false;
                startFill(emit); return false;
            }
            if (phase == Phase.MANUAL_FILL) {
                if (!step.tick(emit)) return false;
                // Intermediate slot transfers may see changing derived previews.
                // Require a fresh full server reply for this completed grid and
                // its intended output before any result-slot click is admitted.
                phase = Phase.FILL;
                emit.invoke(() -> ticket = port.requestSync()); return false;
            }
            if (phase == Phase.FILL) {
                filled = feedback(emit); if (filled == null) return false;
            }
            if (phase == Phase.FILL || phase == Phase.MANUAL_FILL) {
                if (!filled.cursor().empty() || !GameInventory.conserved(before, filled)
                        || previewBaseline != null && !sameResources(previewBaseline, filled)
                        || !filled.slots().get(0).empty() && !filled.slots().get(0).equals(port.output())) {
                    port.mismatch(before,filled);
                    System.getLogger(GameCrafting.class.getName()).log(System.Logger.Level.WARNING,
                        "STRATA_CRAFT_FILL_CHECK cursor_clean="+filled.cursor().empty()
                        +" conserved="+GameInventory.conserved(before,filled)
                        +" output_matches="+filled.slots().get(0).equals(port.output()));
                    throw new IOException("PRECONDITION_FAILED");
                }
                boolean ingredient = false;
                for (int i = 1; i <= gridSize; i++) {
                    int count = filled.slots().get(i).count();
                    if (count < 0 || count > 1) throw new IOException("GAME_CRAFT_FILL_UNSUPPORTED");
                    ingredient |= count == 1;
                }
                if (!ingredient) throw new IOException("PRECONDITION_FAILED");
                remainders = List.copyOf(port.remainders(filled));
                if (remainders.size() != gridSize || remainders.stream().anyMatch(item -> item.count() < 0 || item.count() > 64)) {
                    throw new IOException("GAME_REMAINDER_UNSUPPORTED");
                }
                if (filled.slots().get(0).empty()) {
                    // Pinned FastWorkbench queues result computation at server
                    // END ticks. A complete ingredient reply can precede it.
                    // Freeze every real resource and await fresh server contents;
                    // never repeat the fill, invent output, or click the result.
                    if (previewReads == MAX_PREVIEW_READS) throw new IOException("PRECONDITION_FAILED");
                    if (previewBaseline == null) previewBaseline = filled;
                    previewReads++;
                    reacquireBaseline = null;
                    emit.invoke(() -> ticket = port.requestSync()); return false;
                }
                destinations = emptyDestinations(filled);
                if (destinations.size() < 1 + remainders.stream().filter(item -> !item.empty()).count()) throw new IOException("INVENTORY_FULL");
                var stored = new ArrayList<GameInventory.Stack>(); stored.add(port.output());
                remainders.stream().filter(item -> !item.empty()).forEach(stored::add);
                for (int i = 0; i < stored.size(); i++) {
                    if (!port.mayPlace(destinations.get(i), stored.get(i))
                            || port.capacity(destinations.get(i), stored.get(i)) < stored.get(i).count()) throw new IOException("INVENTORY_FULL");
                }
                if (!port.mayPickup(0)) throw new IOException("PRECONDITION_FAILED");
                // Output click is allowed only here, after recipe/grid/result and resource validation.
                phase = Phase.TAKE;
                reacquireBaseline = null;
                emit.invoke(() -> port.click(0, 0, false));
                emit.invoke(() -> ticket = port.requestSync()); return false;
            }
            if (phase == Phase.TAKE) {
                taken = feedback(emit); if (taken == null) return false;
                if (!taken.cursor().equals(port.output()) || taken.slots().size() != filled.slots().size()) throw new IOException("PRECONDITION_FAILED");
                for (int i = 1; i < taken.slots().size(); i++) {
                    var expected = i <= gridSize ? remainders.get(i - 1) : filled.slots().get(i);
                    if (!expected.equals(taken.slots().get(i))) throw new IOException("PRECONDITION_FAILED");
                }
                phase = Phase.STORE;
                step = GameInventory.click(port, destinations.get(0), false, false, emit); return false;
            }
            if (!step.tick(emit)) return false;
            var state = view();
            if (phase == Phase.REMAINDER_PICKUP) {
                if (!state.cursor().equals(remainders.get(remainderIndex))) throw new IOException("PRECONDITION_FAILED");
                int destination = destinations.remove(1);
                phase = Phase.REMAINDER_STORE; step = GameInventory.click(port, destination, false, false, emit); return false;
            }
            if (!state.cursor().empty()) throw new IOException("PRECONDITION_FAILED");
            if (phase == Phase.REMAINDER_STORE) remainderIndex++;
            while (remainderIndex < gridSize && remainders.get(remainderIndex).empty()) remainderIndex++;
            if (remainderIndex < gridSize) {
                if (!state.slots().get(remainderIndex + 1).equals(remainders.get(remainderIndex))) throw new IOException("PRECONDITION_FAILED");
                phase = Phase.REMAINDER_PICKUP;
                step = GameInventory.click(port, remainderIndex + 1, false, false, emit); return false;
            }
            for (int i = 0; i <= gridSize; i++) if (!state.slots().get(i).empty()) throw new IOException("PRECONDITION_FAILED");
            if (--remaining == 0) return true;
            remainderIndex = 0; fill(emit); return false;
        }
        private static boolean sameResources(GameInventory.View a, GameInventory.View b) {
            return a.resultSlot() == b.resultSlot() && a.slots().size() == b.slots().size()
                && a.cursor().equals(b.cursor())
                && a.slots().subList(1,a.slots().size()).equals(b.slots().subList(1,b.slots().size()));
        }
    }
}
