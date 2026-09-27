package io.github.opencnid.strata.client;

import com.google.gson.JsonNull;
import com.google.gson.JsonObject;
import java.io.IOException;

/** Private fixed phase/comparison data; the original public error is unchanged. */
final class GameMachinePreflightFailure extends IOException {
    enum Phase {
        CONTEXT, REPLY, WAIT, REPLY_LAYOUT, INPUT_FENCE, CURRENT_VIEW, CURRENT_LAYOUT,
        CURRENT_MATCH, SELECTION_MATCH, FINAL_BASELINE, TRANSFER_START, REACQUIRED_BASELINE
    }
    private final JsonObject diagnostic;

    GameMachinePreflightFailure(Phase phase, IOException original, GameMachineInventory.Layout layout,
                                int clicked, GameInventory.View expected, GameInventory.View actual) {
        super(original.getMessage(), original);
        diagnostic = new JsonObject();
        diagnostic.addProperty("policy", "machine-preflight-comparison-masks/2");
        diagnostic.addProperty("phase", phase.name().toLowerCase(java.util.Locale.ROOT));
        diagnostic.add("comparison", JsonNull.INSTANCE);
        if (expected != null && actual != null) {
            var comparison = new JsonObject();
            comparison.add("owned", GameMachineMismatch.masks(layout, expected, actual));
            long ids = 0, counts = 0, components = 0;
            // Base slots only: never inspect hidden augment contents.
            for (int i = 0; i < layout.kind().baseSlots; i++) {
                var a = expected.slots().get(i); var b = actual.slots().get(i);
                if (!a.id().equals(b.id())) ids |= 1L << i;
                if (a.count() != b.count()) counts |= 1L << i;
                if (!a.components().equals(b.components())) components |= 1L << i;
            }
            var machine = new JsonObject();
            machine.addProperty("id", ids); machine.addProperty("count", counts); machine.addProperty("components", components);
            comparison.add("machine", machine);
            var a = expected.slots().get(clicked); var b = actual.slots().get(clicked);
            var selected = new JsonObject();
            selected.addProperty("id", !a.id().equals(b.id()));
            selected.addProperty("count", a.count() != b.count());
            selected.addProperty("components", !a.components().equals(b.components()));
            comparison.add("selected", selected);
            diagnostic.add("comparison", comparison);
        }
    }

    JsonObject diagnostic() { return diagnostic.deepCopy(); }
}
