package io.github.opencnid.strata.client;

import com.google.gson.JsonArray;
import com.google.gson.JsonNull;
import com.google.gson.JsonObject;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

/** Bounded projection of two current Thermal GUIs, never a world/tile search. */
final class GameMachineMenu {
    static final String POLICY = "thermal-current-gui-energy-fluid-base-slots/1";
    static final Map<String, String> ARTIFACTS = Map.of(
        "thermal_expansion-1.19.2-10.3.1.25.jar", "ddf119c33990e991875968c0e810583af091044a3368c28838646f30ace33f4c",
        "thermal_core-1.19.2-10.3.0.9.jar", "20c99f015b9b3d034da1f017a14876bc6f15838d72dc450cfd0c1bdd803c10b5",
        "cofh_core-1.19.2-10.3.1.48.jar", "1e47ecfa7e3bedb7043854d44c53537aacb4b75807c2f7de5df6ab2fa785203d");
    static void requireArtifacts(Map<String, String> loaded) throws IOException {
        for (var pin : ARTIFACTS.entrySet()) if (!pin.getValue().equals(loaded.get(pin.getKey())))
            throw new IOException("GAME_MACHINE_ARTIFACT_UNSUPPORTED");
    }
    static final String INPUT_POLICY = "thermal-display-independent-slot-cursor-fence/1";
    static JsonObject inputWindow(JsonObject window) throws IOException {
        var projected = window.deepCopy();
        if (projected.has("machine") && !projected.get("machine").isJsonNull()) {
            var machine = projected.get("machine");
            if (!machine.isJsonObject()) throw new IOException("GAME_MACHINE_DISPLAY_UNSUPPORTED");
            var display = machine.getAsJsonObject();
            SettingsJson.fields(display, "policy", "kind", "energy", "tanks");
            if (!POLICY.equals(SettingsJson.string(display, "policy"))
                    || !SettingsJson.string(display, "kind").equals(SettingsJson.string(projected, "type")))
                throw new IOException("GAME_MACHINE_DISPLAY_UNSUPPORTED");
            var type = projected.get("type").getAsString();
            if (!type.equals(Kind.FURNACE.id) && !type.equals(Kind.CRUCIBLE.id)) throw new IOException("GAME_MACHINE_DISPLAY_UNSUPPORTED");
            projected.remove("machine");
        }
        return projected;
    }
    enum Kind {
        FURNACE("Furnace", "thermal:machine_furnace", 3),
        CRUCIBLE("Crucible", "thermal:machine_crucible", 2);
        final String stem, id;
        final int baseSlots;
        Kind(String stem, String id, int baseSlots) { this.stem = stem; this.id = id; this.baseSlots = baseSlots; }
        String menuClass() { return "cofh.thermal.expansion.inventory.container.machine.Machine" + stem + "Container"; }
        String screenClass() { return "cofh.thermal.expansion.client.gui.machine.Machine" + stem + "Screen"; }
        String tileClass() { return "cofh.thermal.expansion.block.entity.machine.Machine" + stem + "Tile"; }
    }
    record Energy(int stored, int capacity) {}
    record Fluid(String id, int amount, int capacity, boolean hasComponents) {}
    interface Source {
        void validate() throws IOException;
        Energy energy() throws IOException;
        Fluid fluid() throws IOException;
    }
    static Kind kind(String menuClass) throws IOException {
        for (var kind : Kind.values()) if (kind.menuClass().equals(menuClass)) return kind;
        throw new IOException("GAME_CONTAINER_UNSUPPORTED");
    }
    static List<Integer> visibleSlots(Kind kind, int augmentCount, int total) throws IOException {
        if (augmentCount < 0 || augmentCount > 9 || total != kind.baseSlots + augmentCount + 36)
            throw new IOException("GAME_CONTAINER_UNSUPPORTED");
        var visible = new ArrayList<Integer>();
        for (int i = 0; i < kind.baseSlots; i++) visible.add(i);
        // Augment-panel slots are deliberately absent, not falsely reported empty.
        for (int i = kind.baseSlots + augmentCount; i < total; i++) visible.add(i);
        return List.copyOf(visible);
    }
    static JsonObject read(Kind kind, Source source) throws IOException {
        source.validate();
        var energy = source.energy();
        if (energy == null || energy.capacity <= 0 || energy.stored < 0 || energy.stored > energy.capacity)
            throw new IOException("GAME_MACHINE_DISPLAY_UNSUPPORTED");
        var result = new JsonObject();
        result.addProperty("policy", POLICY); result.addProperty("kind", kind.id);
        var power = new JsonObject(); power.addProperty("stored", energy.stored); power.addProperty("capacity", energy.capacity);
        result.add("energy", power);
        var tanks = new JsonArray();
        if (kind == Kind.CRUCIBLE) {
            var fluid = source.fluid();
            if (fluid == null || fluid.capacity <= 0 || fluid.amount < 0 || fluid.amount > fluid.capacity
                    || fluid.hasComponents || (fluid.amount == 0) != (fluid.id == null)
                    || fluid.id != null && (fluid.id.length() > 256 || !fluid.id.matches("[a-z0-9_.-]+:[a-z0-9_./-]+")))
                throw new IOException("GAME_MACHINE_DISPLAY_UNSUPPORTED");
            var tank = new JsonObject(); tank.addProperty("capacity_mb", fluid.capacity);
            if (fluid.id == null) tank.add("contents", JsonNull.INSTANCE);
            else {
                var contents = new JsonObject(); contents.addProperty("fluid_id", fluid.id); contents.addProperty("amount_mb", fluid.amount);
                tank.add("contents", contents);
            }
            tanks.add(tank);
        }
        result.add("tanks", tanks);
        source.validate(); // Do not return a snapshot from a replaced menu/body.
        return result;
    }
}
