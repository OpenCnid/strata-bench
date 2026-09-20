package io.github.opencnid.strata.client;

import com.google.gson.JsonObject;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import mezz.jei.api.IModPlugin;
import mezz.jei.api.JeiPlugin;
import mezz.jei.api.constants.RecipeTypes;
import mezz.jei.api.constants.VanillaTypes;
import mezz.jei.api.recipe.RecipeIngredientRole;
import mezz.jei.api.runtime.IJeiRuntime;
import net.minecraft.client.Minecraft;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.crafting.CraftingRecipe;
import net.minecraftforge.fml.ModList;
import net.minecraftforge.registries.ForgeRegistries;

/** Optional exact-pack JEI plugin. Uses only the public API, never transfer/cheat hooks. */
@JeiPlugin
public final class JeiRecipePlugin implements IModPlugin {
    private record Runtime(IJeiRuntime jei, long generation) {}
    private static volatile Runtime active = new Runtime(null, 0);
    private static final GameRecipeQuery projection = new GameRecipeQuery();
    public ResourceLocation getPluginUid() { return new ResourceLocation("strata_client", "visible_recipes"); }
    private static synchronized void bind(IJeiRuntime runtime) {
        JeiRenderedLayouts.clear(); active = new Runtime(runtime, active.generation + 1);
    }
    public void onRuntimeAvailable(IJeiRuntime runtime) { JeiRenderedLayouts.install(); bind(runtime); }
    public void onRuntimeUnavailable() { bind(null); }

    /** Exact public XMod/JEI runtime identity for the ordinary task callback. */
    record View(Runtime binding,Object helper,net.minecraft.client.gui.screens.Screen screen) {
        void validate()throws IOException {
            if(active!=binding || binding.jei==null || recipeHelper()!=helper
                    || integrationRuntime()!=binding.jei || binding.jei.getRecipesGui()!=screen)throw viewChanged();
        }
        void ingredient(ItemStack stack)throws IOException {
            validate();
            if(stack==null || stack.isEmpty() || binding.jei.getIngredientManager().getIngredientTypeChecked(stack).orElse(null)!=VanillaTypes.ITEM_STACK
                    || !binding.jei.getIngredientVisibility().isIngredientVisible(VanillaTypes.ITEM_STACK,stack))
                throw new IOException("GAME_QUEST_RECIPE_INGREDIENT_UNSUPPORTED");
        }
        Object runtime(){return binding;}
        IJeiRuntime jei(){return binding.jei;}
    }
    static View taskView(java.util.Map<String,String> artifacts)throws IOException {
        GameQuestRecipeView.requireArtifacts(artifacts);
        var binding=active;Object helper=recipeHelper();
        if(binding.jei==null || !(binding.jei.getRecipesGui() instanceof net.minecraft.client.gui.screens.Screen screen)
                || !screen.getClass().getName().equals("mezz.jei.gui.recipes.RecipesGui")
                || !helper.getClass().getName().equals("dev.ftb.mods.ftbxmodcompat.ftbquests.jei.helper.JEIRecipeHelper")
                || !NativeQuests.bool(NativeQuests.call(helper,"isRecipeModAvailable")))throw viewChanged();
        var view=new View(binding,helper,screen);view.validate();return view;
    }
    private static Object recipeHelper()throws IOException {
        try {return NativeQuests.type("FTBQuests").getMethod("getRecipeModHelper").invoke(null);}
        catch(ReflectiveOperationException | SecurityException failure){throw viewChanged();}
    }
    private static Object integrationRuntime()throws IOException {
        try {return Class.forName("dev.ftb.mods.ftbxmodcompat.ftbquests.jei.FTBQuestsJEIIntegration").getField("runtime").get(null);}
        catch(ReflectiveOperationException | SecurityException | LinkageError failure){throw viewChanged();}
    }
    private static IOException viewChanged(){return new IOException("GAME_QUEST_RECIPE_SOURCE_UNAVAILABLE");}

    static JsonObject query(GameRecipeQuery.Query query, java.util.Map<String,String> artifacts) throws IOException {
        Minecraft client = Minecraft.getInstance();
        if (!client.isSameThread()) throw new IOException("CLIENT_THREAD_REQUIRED");
        if (client.player == null || client.level == null || client.getConnection() == null) throw new IOException("GAME_NOT_CONNECTED");
        if (!ModList.get().getModContainerById("jei").map(mod -> mod.getModInfo().getVersion().toString())
                .orElse("").equals("11.8.1.1034")) throw new IOException("CAPABILITY_MISSING");
        Runtime bound = active; IJeiRuntime jei = bound.jei;
        if (jei == null) throw new IOException("GAME_RECIPE_SOURCE_UNAVAILABLE");
        if (!query.crafting()) {
            GameMachineRecipe.requireArtifacts(artifacts);
            final var player = client.player; final var level = client.level; final var connection = client.getConnection();
            var machineFocus = List.of(JeiMachineRecipes.focus(jei, query));
            return projection.query(query, new GameRecipeQuery.Source() {
                public long generation() {
                    return active == bound && client.player == player && client.level == level && client.getConnection() == connection
                        ? bound.generation : -1;
                }
                public Iterable<? extends GameRecipeQuery.Candidate> focused(GameRecipeQuery.Query requested) throws IOException {
                    return JeiMachineRecipes.focused(jei, requested, machineFocus);
                }
            });
        }
        var itemId = new ResourceLocation(query.item());
        if (!ForgeRegistries.ITEMS.containsKey(itemId)) throw new IOException("TARGET_NOT_OBSERVED");
        var item = new ItemStack(ForgeRegistries.ITEMS.getValue(itemId));
        if (item.isEmpty() || !jei.getIngredientVisibility().isIngredientVisible(VanillaTypes.ITEM_STACK, item)) {
            throw new IOException("TARGET_NOT_OBSERVED");
        }
        var focus = jei.getJeiHelpers().getFocusFactory().createFocus(
            query.role().equals("input") ? RecipeIngredientRole.INPUT : RecipeIngredientRole.OUTPUT,
            VanillaTypes.ITEM_STACK, item);
        var focuses = List.of(focus);
        // Both default lookups exclude hidden content. Never call includeHidden().
        try (var categories = jei.getRecipeManager().createRecipeCategoryLookup()
                .limitTypes(List.of(RecipeTypes.CRAFTING)).get()) {
            if (categories.limit(2).count() != 1) throw new IOException("GAME_RECIPE_SOURCE_UNAVAILABLE");
        }
        final var player = client.player; final var level = client.level; final var connection = client.getConnection();
        return projection.query(query, new GameRecipeQuery.Source() {
            public long generation() {
                return active == bound && client.player == player && client.level == level && client.getConnection() == connection
                    ? bound.generation : -1;
            }
            public Iterable<? extends GameRecipeQuery.Candidate> focused(GameRecipeQuery.Query ignored) throws IOException {
                var results = new ArrayList<GameRecipeQuery.Candidate>();
                long started = System.nanoTime();
                try (var recipes = jei.getRecipeManager().createRecipeLookup(RecipeTypes.CRAFTING).limitFocus(focuses).get()) {
                    var iterator = recipes.iterator();
                    while (iterator.hasNext()) {
                        if (System.nanoTime() - started > GameRecipeQuery.MAX_NANOS) throw new IOException("GAME_RECIPE_TIMEOUT");
                        if (results.size() >= GameRecipeQuery.MAX_MATCHES) throw new IOException("GAME_RECIPE_BOUNDS");
                        CraftingRecipe recipe = iterator.next();
                        results.add(new GameRecipeQuery.Candidate() {
                            public boolean visible() { return true; } // Supplied only by JEI's non-hidden focused lookup.
                            public String id() { return recipe.getId().toString(); }
                            public boolean bookUnlocked() { return player.getRecipeBook().contains(recipe); }
                            public JsonObject definition() throws IOException {
                                if (connection.getRecipeManager().byKey(recipe.getId()).orElse(null) != recipe) throw new IOException("GAME_RECIPE_CHANGED");
                                var value = NativeRecipes.definition(recipe);
                                // Do not expose hidden alternatives through a visible recipe's tag ingredients.
                                visibleItem(value.getAsJsonObject("result").get("item_id").getAsString());
                                for (var slot : value.getAsJsonArray("ingredients")) for (var choice : slot.getAsJsonArray()) visibleItem(choice.getAsString());
                                return value;
                            }
                            private void visibleItem(String id) throws IOException {
                                var key = new ResourceLocation(id);
                                if (!ForgeRegistries.ITEMS.containsKey(key) || !jei.getIngredientVisibility().isIngredientVisible(
                                        VanillaTypes.ITEM_STACK, new ItemStack(ForgeRegistries.ITEMS.getValue(key)))) throw new IOException("MECHANIC_UNSUPPORTED");
                            }
                        });
                    }
                }
                return results;
            }
        });
    }
}
