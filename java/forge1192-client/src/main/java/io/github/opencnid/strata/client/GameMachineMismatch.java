package io.github.opencnid.strata.client;

import com.google.gson.JsonObject;
import java.io.IOException;

/** Fixed, value-free private diagnosis; never evidence that a transfer succeeded. */
final class GameMachineMismatch extends IOException {
    enum Phase { PREDICTION_REPLY, REPLY_CURRENT }
    private final JsonObject diagnostic;

    GameMachineMismatch(GameMachineInventory.Layout layout, Phase phase, boolean refreshed,
                        GameInventory.View before, GameInventory.View predicted,
                        GameInventory.View received, GameInventory.View current) {
        super("GAME_MACHINE_TRANSFER_UNCONFIRMED");
        diagnostic = new JsonObject();
        diagnostic.addProperty("policy", "machine-owned-mismatch-masks/1");
        diagnostic.addProperty("phase", phase == Phase.PREDICTION_REPLY ? "prediction_reply" : "reply_current");
        diagnostic.addProperty("preclick_refresh_used", refreshed);
        diagnostic.add("before_predicted", masks(layout, before, predicted));
        diagnostic.add("before_received", masks(layout, before, received));
        diagnostic.add("before_current", masks(layout, before, current));
        diagnostic.add("predicted_received", masks(layout, predicted, received));
        diagnostic.add("received_current", masks(layout, received, current));
    }

    JsonObject diagnostic() { return diagnostic.deepCopy(); }

    static JsonObject masks(GameMachineInventory.Layout layout,
                                    GameInventory.View first, GameInventory.View second) {
        long ids = 0, counts = 0, components = 0;
        // Bit0 is cursor; bits1-36 are owned player slots. No hidden/machine slot.
        for (int bit = 0; bit <= 36; bit++) {
            int slot = layout.playerStart() + bit - 1;
            var a = bit == 0 ? first.cursor() : first.slots().get(slot);
            var b = bit == 0 ? second.cursor() : second.slots().get(slot);
            long mask = 1L << bit;
            if (!a.id().equals(b.id())) ids |= mask;
            if (a.count() != b.count()) counts |= mask;
            if (!a.components().equals(b.components())) components |= mask;
        }
        var result = new JsonObject();
        result.addProperty("id", ids); result.addProperty("count", counts);
        result.addProperty("components", components);
        return result;
    }
}
