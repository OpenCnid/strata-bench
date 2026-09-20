package io.github.opencnid.strata.client;

import java.io.IOException;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class GameMachineMenuTest {
    @Test void displayChangesDoNotChangeInputProjectionButSlotsCursorAndWindowIdentityDo() throws Exception {
        var window = new com.google.gson.JsonObject(); window.addProperty("id", 4); window.addProperty("revision", 7);
        window.addProperty("type", "thermal:machine_crucible"); window.add("slots", new com.google.gson.JsonArray());
        window.add("cursor_item", com.google.gson.JsonNull.INSTANCE);
        window.add("machine", GameMachineMenu.read(GameMachineMenu.Kind.CRUCIBLE, new Source()));
        var original = window.deepCopy(); var input = GameMachineMenu.inputWindow(window);
        window.getAsJsonObject("machine").getAsJsonObject("energy").addProperty("stored", 399);
        window.getAsJsonObject("machine").getAsJsonArray("tanks").get(0).getAsJsonObject().getAsJsonObject("contents").addProperty("amount_mb", 300);
        assertEquals(input, GameMachineMenu.inputWindow(window)); assertNotEquals(original, window);
        assertTrue(window.has("machine")); // Public telemetry remains intact.
        for (String field : java.util.List.of("id", "revision", "slots", "cursor_item")) {
            var changed = window.deepCopy(); changed.addProperty(field, "changed");
            assertNotEquals(input, GameMachineMenu.inputWindow(changed));
        }
    }
    @Test void unknownMachinePolicyCannotDiscardActionPreconditions() throws Exception {
        var window = new com.google.gson.JsonObject(); window.addProperty("type", "thermal:machine_crucible");
        window.add("machine", GameMachineMenu.read(GameMachineMenu.Kind.CRUCIBLE, new Source()));
        window.getAsJsonObject("machine").addProperty("policy", "unknown/1");
        assertThrows(IOException.class, () -> GameMachineMenu.inputWindow(window));
        window.getAsJsonObject("machine").addProperty("policy", GameMachineMenu.POLICY);
        window.addProperty("type", "minecraft:chest");
        assertThrows(IOException.class, () -> GameMachineMenu.inputWindow(window));
    }
    @Test void exactArtifactBytesRequiredEvenWhenVersionLabelsMatch() throws Exception {
        GameMachineMenu.requireArtifacts(GameMachineMenu.ARTIFACTS);
        assertThrows(IOException.class, () -> GameMachineMenu.requireArtifacts(java.util.Map.of()));
        for (String file : GameMachineMenu.ARTIFACTS.keySet()) {
            var changed = new java.util.HashMap<>(GameMachineMenu.ARTIFACTS); changed.put(file, "0".repeat(64));
            assertThrows(IOException.class, () -> GameMachineMenu.requireArtifacts(changed));
            changed.remove(file);
            assertThrows(IOException.class, () -> GameMachineMenu.requireArtifacts(changed));
        }
    }
    static class Source implements GameMachineMenu.Source {
        int validations, energyReads, fluidReads;
        int rejectValidation;
        GameMachineMenu.Energy energy = new GameMachineMenu.Energy(400, 1000);
        GameMachineMenu.Fluid fluid = new GameMachineMenu.Fluid("minecraft:lava", 250, 4000, false);
        public void validate() throws IOException {
            if (++validations == rejectValidation) throw new IOException("REVISION_CONFLICT");
        }
        public GameMachineMenu.Energy energy() { energyReads++; return energy; }
        public GameMachineMenu.Fluid fluid() { fluidReads++; return fluid; }
    }
    @Test void furnaceDoesNotReadAnyTankAndReturnsOnlyDisplayFields() throws Exception {
        var source = new Source(); var value = GameMachineMenu.read(GameMachineMenu.Kind.FURNACE, source);
        assertEquals(0, source.fluidReads); assertEquals(2, source.validations);
        assertEquals(4, value.size()); assertEquals(400, value.getAsJsonObject("energy").get("stored").getAsInt());
        assertEquals(0, value.getAsJsonArray("tanks").size());
    }
    @Test void crucibleIncludesOnlyItsVisibleOutputTankAndEmptyIsExplicit() throws Exception {
        var source = new Source(); var value = GameMachineMenu.read(GameMachineMenu.Kind.CRUCIBLE, source);
        assertEquals("minecraft:lava", value.getAsJsonArray("tanks").get(0).getAsJsonObject().getAsJsonObject("contents").get("fluid_id").getAsString());
        assertEquals(1, source.fluidReads);
        source.fluid = new GameMachineMenu.Fluid(null, 0, 4000, false);
        assertTrue(GameMachineMenu.read(GameMachineMenu.Kind.CRUCIBLE, source).getAsJsonArray("tanks").get(0).getAsJsonObject().get("contents").isJsonNull());
    }
    @Test void closedOrReplacedContextRejectsBeforeReadingResources() {
        var source = new Source(); source.rejectValidation = 1;
        assertThrows(IOException.class, () -> GameMachineMenu.read(GameMachineMenu.Kind.CRUCIBLE, source));
        assertEquals(0, source.energyReads); assertEquals(0, source.fluidReads);
    }
    @Test void contextLossDuringReadNeverReturnsItsSnapshot() {
        var source = new Source(); source.rejectValidation = 2;
        assertThrows(IOException.class, () -> GameMachineMenu.read(GameMachineMenu.Kind.CRUCIBLE, source));
        assertEquals(1, source.fluidReads);
    }
    @Test void negativeOverCapacityAndDisabledEnergyReject() {
        var source = new Source();
        for (var energy : new GameMachineMenu.Energy[]{null, new GameMachineMenu.Energy(-1, 1000),
                new GameMachineMenu.Energy(1001, 1000), new GameMachineMenu.Energy(0, 0)}) {
            source.energy = energy;
            assertThrows(IOException.class, () -> GameMachineMenu.read(GameMachineMenu.Kind.FURNACE, source));
        }
    }
    @Test void taggedUnknownMalformedAndOverCapacityFluidsReject() {
        var source = new Source();
        for (var fluid : new GameMachineMenu.Fluid[]{null, new GameMachineMenu.Fluid("test:secret", 1, 100, true),
                new GameMachineMenu.Fluid(null, 1, 100, false), new GameMachineMenu.Fluid("not-id", 1, 100, false),
                new GameMachineMenu.Fluid("test:fluid", 101, 100, false), new GameMachineMenu.Fluid("test:fluid", 0, 100, false),
                new GameMachineMenu.Fluid(null, -1, 100, false), new GameMachineMenu.Fluid(null, 0, 0, false)}) {
            source.fluid = fluid;
            assertThrows(IOException.class, () -> GameMachineMenu.read(GameMachineMenu.Kind.CRUCIBLE, source));
        }
    }
    @Test void augmentIndicesAreOmittedWithoutReindexingPlayerSlots() throws Exception {
        var furnace = GameMachineMenu.visibleSlots(GameMachineMenu.Kind.FURNACE, 4, 43);
        assertEquals(39, furnace.size()); assertEquals(0, furnace.get(0)); assertEquals(2, furnace.get(2));
        assertEquals(7, furnace.get(3)); assertEquals(42, furnace.get(38));
        for (int hidden = 3; hidden < 7; hidden++) assertFalse(furnace.contains(hidden));
        assertEquals(38, GameMachineMenu.visibleSlots(GameMachineMenu.Kind.CRUCIBLE, 4, 42).size());
    }
    @Test void alteredLayoutsAndUnknownOrDerivedClassesReject() throws Exception {
        assertEquals(GameMachineMenu.Kind.CRUCIBLE, GameMachineMenu.kind(GameMachineMenu.Kind.CRUCIBLE.menuClass()));
        assertThrows(IOException.class, () -> GameMachineMenu.kind(GameMachineMenu.Kind.CRUCIBLE.menuClass() + "$Subclass"));
        assertThrows(IOException.class, () -> GameMachineMenu.kind("unknown.Menu"));
        assertThrows(IOException.class, () -> GameMachineMenu.visibleSlots(GameMachineMenu.Kind.FURNACE, 4, 42));
        assertThrows(IOException.class, () -> GameMachineMenu.visibleSlots(GameMachineMenu.Kind.FURNACE, 10, 49));
        assertThrows(IOException.class, () -> GameMachineMenu.visibleSlots(GameMachineMenu.Kind.FURNACE, -1, 38));
    }
}
