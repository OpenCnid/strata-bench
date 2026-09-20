package io.github.opencnid.strata.client;

import com.google.gson.JsonObject;
import java.io.IOException;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class GameRecipeSelectionTest {
    JsonObject page() throws IOException {
        var source=new GameRecipeQueryTest.Source();
        source.entries.add(GameRecipeQueryTest.candidate("test:recipe",false,null));
        return new GameRecipeQuery(()->0).query(GameRecipeQueryTest.QUERY,source);
    }
    @Test void selectionBindsVisibleQueryGenerationAndInitialRevisionButBookUnlockIsNotDefinitionDrift() throws Exception {
        var page=page();var selection=new GameRecipeSelection(GameRecipeQueryTest.QUERY,1,1);
        var original=selection.definition(page,"test:recipe",true);assertFalse(original.has("craft_authority"));
        page.addProperty("revision",2);
        page.getAsJsonArray("recipes").get(0).getAsJsonObject().addProperty("craft_authority","recipe_book");
        assertThrows(IOException.class,()->selection.definition(page,"test:recipe",true));
        assertEquals(original,selection.definition(page,"test:recipe",false));
        page.addProperty("source_generation",2);
        assertThrows(IOException.class,()->selection.definition(page,"test:recipe",false));
    }
    @Test void hiddenUnknownUnsupportedAndChangedFocusCannotAuthorizeRecipe() throws Exception {
        var selection=new GameRecipeSelection(GameRecipeQueryTest.QUERY,1,1);
        assertEquals("RECIPE_NOT_KNOWN",assertThrows(IOException.class,()->selection.definition(page(),"test:hidden",true)).getMessage());
        var unsupported=page();unsupported.getAsJsonArray("recipes").get(0).getAsJsonObject().addProperty("supported",false);
        assertEquals("MECHANIC_UNSUPPORTED",assertThrows(IOException.class,()->selection.definition(unsupported,"test:recipe",true)).getMessage());
        var wrong=page();wrong.getAsJsonObject("query").addProperty("role","input");
        assertThrows(IOException.class,()->selection.definition(wrong,"test:recipe",true));
    }
    @Test void sourceSelectionRejectsPrivateExtrasAndInvalidGeneration() throws Exception {
        var raw=new JsonObject();raw.add("query",GameRecipeQueryTest.QUERY.json());
        raw.addProperty("source_generation",1);raw.addProperty("revision",1);
        assertEquals(new GameRecipeSelection(GameRecipeQueryTest.QUERY,1,1),GameRecipeSelection.read(raw));
        raw.addProperty("include_hidden",true);assertThrows(IOException.class,()->GameRecipeSelection.read(raw));
        raw.remove("include_hidden");raw.addProperty("source_generation",-1);assertThrows(IOException.class,()->GameRecipeSelection.read(raw));
    }
}
