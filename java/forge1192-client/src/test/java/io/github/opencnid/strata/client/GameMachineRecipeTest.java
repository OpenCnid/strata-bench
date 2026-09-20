package io.github.opencnid.strata.client;

import com.google.gson.JsonObject;
import java.io.IOException;
import java.util.List;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

/** Synthetic projection/authority cases. Exact client JEI and rendering are separate gates. */
class GameMachineRecipeTest {
    @Test void machineDiscoveryRequiresAllFourExactLoadedArtifacts() throws Exception {
        var artifacts=new java.util.HashMap<>(GameMachineMenu.ARTIFACTS);
        artifacts.put(GameMachineRecipe.JEI_FILE,GameMachineRecipe.JEI_HASH);
        GameMachineRecipe.requireArtifacts(artifacts);
        for (String key:List.copyOf(artifacts.keySet())) {
            String original=artifacts.remove(key);
            assertThrows(IOException.class,()->GameMachineRecipe.requireArtifacts(artifacts));
            artifacts.put(key,"0".repeat(64));
            assertThrows(IOException.class,()->GameMachineRecipe.requireArtifacts(artifacts));
            artifacts.put(key,original);
        }
    }
    static final GameMachineRecipe.Choice INPUT = new GameMachineRecipe.Choice("item", "fixture:input", 1);
    static final GameMachineRecipe.Choice OUTPUT = new GameMachineRecipe.Choice("fluid", "fixture:fluid", 250);
    static JsonObject fixture(String category) throws IOException {
        return GameMachineRecipe.definition("fixture:machine", category, 4000,
            category.equals("thermal:furnace") ? 0.5f : null, List.of(INPUT),
            List.of(category.equals("thermal:furnace") ? new GameMachineRecipe.Choice("item", "fixture:output", 2) : OUTPUT));
    }
    @Test void projectsCrucibleFluidAmountsAndFurnaceVisibleTooltip() throws Exception {
        var fluid = fixture("thermal:crucible");
        assertEquals(250, fluid.getAsJsonArray("slots").get(1).getAsJsonObject().getAsJsonArray("ingredients")
            .get(0).getAsJsonObject().get("amount_mb").getAsInt());
        assertTrue(fluid.get("output_tooltip").isJsonNull());
        var furnace = fixture("thermal:furnace"); assertEquals(4000, furnace.get("energy_rf").getAsInt());
        assertEquals(50, furnace.getAsJsonObject("output_tooltip").get("percent").getAsInt());
        assertFalse(fluid.has("xp")); assertFalse(fluid.has("craft_authority"));
    }
    @Test void tooltipMatchesDisplayedAbsoluteRoundedPercentageWithoutHiddenSign() throws Exception {
        assertEquals(GameMachineRecipe.tooltip(0.129f), GameMachineRecipe.tooltip(-0.129f));
        assertEquals(12, GameMachineRecipe.tooltip(0.129f).getAsJsonObject().get("percent").getAsInt());
        assertEquals("additional_chance", GameMachineRecipe.tooltip(2.5f).getAsJsonObject().get("kind").getAsString());
        assertTrue(GameMachineRecipe.tooltip(-2f).isJsonNull());
        assertEquals(0, GameMachineRecipe.tooltip(0f).getAsJsonObject().get("percent").getAsInt());
        for (float value : new float[] {Float.NaN, Float.POSITIVE_INFINITY, Float.NEGATIVE_INFINITY, 1000001})
            assertThrows(IOException.class, () -> GameMachineRecipe.tooltip(value));
    }
    @Test void projectionBoundsAndLayoutRejectUnknownAndAmbiguousDefinitions() throws Exception {
        for (var inputs : List.of(List.<GameMachineRecipe.Choice>of(), List.of(INPUT, INPUT), List.of(OUTPUT),
                List.of(new GameMachineRecipe.Choice("item", "fixture:input", 65)),
                List.of(new GameMachineRecipe.Choice("item", "fixture:input", 0)),
                List.of(new GameMachineRecipe.Choice("item", "private wildcard", 1)))) {
            assertThrows(IOException.class, () -> GameMachineRecipe.definition("fixture:machine", "thermal:crucible", 1, null, inputs, List.of(OUTPUT)));
        }
        assertThrows(IOException.class, () -> GameMachineRecipe.definition("fixture:m", "thermal:other", 1, null, List.of(INPUT), List.of(OUTPUT)));
        assertThrows(IOException.class, () -> GameMachineRecipe.definition("fixture:m", "thermal:furnace", 1, 1f, List.of(INPUT), List.of(OUTPUT)));
        assertThrows(IOException.class, () -> GameMachineRecipe.definition("fixture:m", "thermal:crucible", 1, 1f, List.of(INPUT), List.of(OUTPUT)));
        assertThrows(IOException.class, () -> GameMachineRecipe.definition("fixture:m", "thermal:crucible", 1, null, List.of(INPUT), List.of(OUTPUT, OUTPUT)));
    }
    @Test void hiddenEnergyIsAbsentAndAlternativesAreDeterministicallyBounded() throws Exception {
        var inputs = new java.util.ArrayList<GameMachineRecipe.Choice>();
        for (int i=63; i>=0; i--) inputs.add(new GameMachineRecipe.Choice("item", String.format("fixture:r%02d",i),1));
        var value=GameMachineRecipe.definition("fixture:m","thermal:crucible",-1,null,inputs,List.of(OUTPUT));
        assertTrue(value.get("energy_rf").isJsonNull());
        assertEquals("fixture:r00",value.getAsJsonArray("slots").get(0).getAsJsonObject().getAsJsonArray("ingredients")
            .get(0).getAsJsonObject().get("item_id").getAsString());
        inputs.add(new GameMachineRecipe.Choice("item","fixture:extra",1));
        assertThrows(IOException.class,()->GameMachineRecipe.definition("fixture:m","thermal:crucible",1,null,inputs,List.of(OUTPUT)));
    }
    @Test void machineQueryCannotGrantCraftingAndNeverReadsRecipeBook() throws Exception {
        var query=new GameRecipeQuery.Query("thermal:crucible","fluid","fixture:fluid","output",0);
        var source=new GameRecipeQueryTest.Source();
        source.entries.add(new GameRecipeQuery.Candidate() {
            public boolean visible() { return true; }
            public String id() { return "fixture:machine"; }
            public boolean bookUnlocked() { throw new AssertionError("private book read"); }
            public JsonObject definition() throws IOException { return fixture("thermal:crucible"); }
        });
        var value=new GameRecipeQuery(()->0).query(query,source);
        assertEquals("discovery_only",value.getAsJsonArray("recipes").get(0).getAsJsonObject().get("craft_authority").getAsString());
        var selection=new JsonObject();selection.add("query",query.json());selection.addProperty("source_generation",1);selection.addProperty("revision",1);
        assertEquals("MECHANIC_UNSUPPORTED",assertThrows(IOException.class,()->GameRecipeSelection.read(selection)).getMessage());
    }
    @Test void categoryAndTargetKindHaveDistinctRevisionsAndStrictQueryShapes() throws Exception {
        var projection=new GameRecipeQuery(()->0); var source=new GameRecipeQueryTest.Source();
        long previous=0;
        for (String category:List.of("thermal:furnace","thermal:crucible")) for(String kind:List.of("item","fluid")) {
            var query=new GameRecipeQuery.Query(category,kind,"fixture:target","output",0);
            assertEquals(query,GameRecipeQuery.Query.read(query.json()));
            assertTrue(projection.query(query,source).get("revision").getAsLong()>previous);
            previous=projection.query(query,source).get("revision").getAsLong();
            var both=query.json();both.addProperty(kind.equals("item") ? "fluid_id" : "item_id","fixture:extra");
            assertThrows(IOException.class,()->GameRecipeQuery.Query.read(both));
        }
        assertThrows(IllegalArgumentException.class,()->new GameRecipeQuery.Query("minecraft:crafting","fluid","fixture:f","input",0));
    }
}
