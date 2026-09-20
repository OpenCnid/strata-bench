package io.github.opencnid.strata.client;

import com.google.gson.JsonObject;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

/** Require the native plain definition to match the actual standard EMI crafting display. */
final class EmiRecipeDefinition {
    static void validate(JsonObject definition, List<List<String>> visible, GameInventory.Stack output, boolean shapeless) throws IOException {
        String serializer = SettingsJson.string(definition,"serializer");
        if (shapeless != serializer.equals("minecraft:crafting_shapeless")) throw unsupported();
        var result = definition.getAsJsonObject("result");
        if (!output.id().equals(SettingsJson.string(result,"item_id")) || output.count()!=SettingsJson.integer(result,"count")) throw unsupported();
        var expected = new ArrayList<List<String>>();
        for (var slot : definition.getAsJsonArray("ingredients")) {
            var choices = new ArrayList<String>(); slot.getAsJsonArray().forEach(v -> choices.add(v.getAsString()));
            expected.add(List.copyOf(choices));
        }
        if (!shapeless) {
            int width=(int)SettingsJson.integer(definition,"width"), height=(int)SettingsJson.integer(definition,"height");
            var padded=new ArrayList<List<String>>();
            for(int y=0;y<3;y++) for(int x=0;x<3;x++) padded.add(x<width && y<height ? expected.get(y*width+x) : List.of());
            expected=padded;
        }
        // EMI's standard shaped widget indexes a fixed 3x3 list; no trimming/reordering.
        if (!expected.equals(visible)) throw unsupported();
    }
    private static IOException unsupported() { return new IOException("MECHANIC_UNSUPPORTED"); }
}
