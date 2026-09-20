package io.github.opencnid.strata.client;

import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

/** Display/native parity fixtures only; authentic EMI source still requires a game run. */
class EmiRecipeDefinitionTest {
    @Test void shapedPaddingAndExactAlternativesAreRequired() throws Exception {
        var definition=GameRecipesTest.recipe("test:r");
        var slots=new ArrayList<List<String>>();slots.add(List.of("test:a","test:b"));
        for(int i=1;i<9;i++)slots.add(List.of());
        var output=new GameInventory.Stack("test:expert_output",2,"");
        EmiRecipeDefinition.validate(definition,slots,output,false);
        slots.set(0,List.of("test:a"));
        assertThrows(IOException.class,()->EmiRecipeDefinition.validate(definition,slots,output,false));
        slots.set(0,List.of("test:a","test:b"));slots.set(1,List.of("test:extra"));
        assertThrows(IOException.class,()->EmiRecipeDefinition.validate(definition,slots,output,false));
    }
    @Test void shapelessOutputAndShapeCannotBeSubstituted() throws Exception {
        var slots=List.of(List.of("test:a"),List.of("test:b"));
        var output=new GameInventory.Stack("test:c",1,"");
        var definition=GameRecipes.definition("test:r","minecraft:crafting_shapeless",0,0,slots,output);
        EmiRecipeDefinition.validate(definition,slots,output,true);
        assertThrows(IOException.class,()->EmiRecipeDefinition.validate(definition,slots,output,false));
        assertThrows(IOException.class,()->EmiRecipeDefinition.validate(definition,slots,new GameInventory.Stack("test:c",2,""),true));
        assertThrows(IOException.class,()->EmiRecipeDefinition.validate(definition,List.of(slots.get(1),slots.get(0)),output,true));
    }
    @Test void emiSelectionDoesNotAuthorizeJeiPageOrMachineRecipes() throws Exception {
        var query=new GameRecipeQuery.Query("emi","minecraft:crafting","item","test:out","output",0);
        assertEquals(query,GameRecipeQuery.Query.read(query.json()));
        assertThrows(IllegalArgumentException.class,()->new GameRecipeQuery.Query("emi","thermal:furnace","item","test:out","output",0));
        assertThrows(IllegalArgumentException.class,()->new GameRecipeQuery.Query("emi","minecraft:crafting","fluid","test:out","output",0));
        var source=new GameRecipeQueryTest.Source();source.entries.add(GameRecipeQueryTest.candidate("test:r",false,null));
        var projection=new GameRecipeQuery(()->0);var page=projection.query(query,source);
        var selection=new GameRecipeSelection(query,1,page.get("revision").getAsLong());
        selection.definition(page,"test:r",true);
        var other=projection.query(GameRecipeQueryTest.QUERY,source);
        assertThrows(IOException.class,()->selection.definition(other,"test:r",false));
    }
    @Test void wrongOrAbsentArtifactCannotLoadEmiRuntime() throws Exception {
        assertThrows(IOException.class,()->EmiRecipeSource.requireArtifact(Map.of()));
        assertThrows(IOException.class,()->EmiRecipeSource.requireArtifact(Map.of(EmiRecipeSource.FILE,"0".repeat(64))));
        EmiRecipeSource.requireArtifact(Map.of(EmiRecipeSource.FILE,EmiRecipeSource.HASH));
    }
}
