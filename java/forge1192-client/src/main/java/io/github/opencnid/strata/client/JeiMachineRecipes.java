package io.github.opencnid.strata.client;

import com.google.gson.JsonObject;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import mezz.jei.api.constants.VanillaTypes;
import mezz.jei.api.gui.ingredient.IRecipeSlotView;
import mezz.jei.api.helpers.IPlatformFluidHelper;
import mezz.jei.api.ingredients.ITypedIngredient;
import mezz.jei.api.recipe.IFocus;
import mezz.jei.api.recipe.RecipeIngredientRole;
import mezz.jei.api.recipe.category.IRecipeCategory;
import mezz.jei.api.runtime.IJeiRuntime;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.crafting.Ingredient;
import net.minecraft.world.item.crafting.Recipe;
import net.minecraftforge.fluids.FluidStack;
import net.minecraftforge.registries.ForgeRegistries;

/** Exact optional Thermal categories. Only public JEI layouts and displayed metadata. */
final class JeiMachineRecipes {
    static IFocus<?> focus(IJeiRuntime jei, GameRecipeQuery.Query query) throws IOException {
        var role = query.role().equals("input") ? RecipeIngredientRole.INPUT : RecipeIngredientRole.OUTPUT;
        if (query.targetKind().equals("item")) {
            var key = new ResourceLocation(query.item());
            if (!ForgeRegistries.ITEMS.containsKey(key)) throw new IOException("TARGET_NOT_OBSERVED");
            var item = new ItemStack(ForgeRegistries.ITEMS.getValue(key));
            if (item.isEmpty() || !jei.getIngredientVisibility().isIngredientVisible(VanillaTypes.ITEM_STACK, item))
                throw new IOException("TARGET_NOT_OBSERVED");
            return jei.getJeiHelpers().getFocusFactory().createFocus(role, VanillaTypes.ITEM_STACK, item);
        }
        return fluidFocus(jei, jei.getJeiHelpers().getPlatformFluidHelper(), query, role);
    }
    private static <T> IFocus<T> fluidFocus(IJeiRuntime jei, IPlatformFluidHelper<T> helper,
            GameRecipeQuery.Query query, RecipeIngredientRole role) throws IOException {
        var key = new ResourceLocation(query.item());
        if (!ForgeRegistries.FLUIDS.containsKey(key)) throw new IOException("TARGET_NOT_OBSERVED");
        T fluid = helper.create(ForgeRegistries.FLUIDS.getValue(key), helper.bucketVolume());
        if (!(fluid instanceof FluidStack stack) || stack.isEmpty() || stack.hasTag()
                || !jei.getIngredientVisibility().isIngredientVisible(helper.getFluidIngredientType(), fluid))
            throw new IOException("TARGET_NOT_OBSERVED");
        return jei.getJeiHelpers().getFocusFactory().createFocus(role, helper.getFluidIngredientType(), fluid);
    }
    static List<GameRecipeQuery.Candidate> focused(IJeiRuntime jei, GameRecipeQuery.Query query,
            List<? extends IFocus<?>> focuses) throws IOException {
        var type = jei.getRecipeManager().getRecipeType(new ResourceLocation(query.category()))
            .orElseThrow(() -> new IOException("GAME_RECIPE_SOURCE_UNAVAILABLE"));
        String stem = query.category().equals("thermal:furnace") ? "Furnace" : "Crucible";
        if (!type.getRecipeClass().getName().equals("cofh.thermal.core.util.recipes.machine." + stem + "Recipe"))
            throw GameMachineRecipe.unsupported();
        try (var categories = jei.getRecipeManager().createRecipeCategoryLookup().limitTypes(List.of(type)).get()) {
            var entries = categories.limit(2).toList();
            if (entries.size() != 1) throw new IOException("GAME_RECIPE_SOURCE_UNAVAILABLE");
            var category = entries.get(0);
            if (!category.getClass().getName().equals("cofh.thermal.expansion.compat.jei.machine." + stem + "RecipeCategory")
                    || !category.getRecipeType().equals(type)) throw GameMachineRecipe.unsupported();
            return focusedCategory(jei, query, focuses, category);
        }
    }
    private static <R> List<GameRecipeQuery.Candidate> focusedCategory(IJeiRuntime jei, GameRecipeQuery.Query query,
            List<? extends IFocus<?>> focuses, IRecipeCategory<R> category) throws IOException {
        var results = new ArrayList<GameRecipeQuery.Candidate>(); long started = System.nanoTime();
        try (var stream = jei.getRecipeManager().createRecipeLookup(category.getRecipeType()).limitFocus(focuses).get()) {
            var iterator = stream.iterator();
            while (iterator.hasNext()) {
                if (System.nanoTime() - started > GameRecipeQuery.MAX_NANOS) throw new IOException("GAME_RECIPE_TIMEOUT");
                if (results.size() >= GameRecipeQuery.MAX_MATCHES) throw new IOException("GAME_RECIPE_BOUNDS");
                R value = iterator.next();
                // Category and recipe visibility come from default JEI lookups; no includeHidden.
                if (!(value instanceof Recipe<?> recipe)) throw GameMachineRecipe.unsupported();
                results.add(new GameRecipeQuery.Candidate() {
                    public boolean visible() { return true; }
                    public String id() { return recipe.getId().toString(); }
                    public boolean bookUnlocked() { throw new AssertionError("machine discovery has no book authority"); }
                    public JsonObject definition() throws IOException {
                        if (value.getClass() != category.getRecipeType().getRecipeClass()) throw GameMachineRecipe.unsupported();
                        requireSimpleInput(value);
                        var layout = jei.getRecipeManager().createRecipeLayoutDrawable(category, value,
                            jei.getJeiHelpers().getFocusFactory().createFocusGroup(focuses))
                            .orElseThrow(GameMachineRecipe::unsupported);
                        var slots = layout.getRecipeSlotsView().getSlotViews();
                        if (slots.size() != 2 || slots.get(0).getRole() != RecipeIngredientRole.INPUT
                                || slots.get(1).getRole() != RecipeIngredientRole.OUTPUT) throw GameMachineRecipe.unsupported();
                        Object energy = call(value, "getEnergy");
                        if (!(energy instanceof Integer amount)) throw GameMachineRecipe.unsupported();
                        Float chance = null;
                        if (query.category().equals("thermal:furnace")) {
                            Object chances = call(value, "getOutputItemChances");
                            if (!(chances instanceof List<?> list) || list.size() != 1 || !(list.get(0) instanceof Float number))
                                throw GameMachineRecipe.unsupported();
                            chance = number;
                        }
                        return GameMachineRecipe.definition(id(), query.category(), amount, chance,
                            choices(jei, slots.get(0)), choices(jei, slots.get(1)));
                    }
                });
            }
        }
        return results;
    }
    private static void requireSimpleInput(Object recipe) throws IOException {
        Object inputs = call(recipe, "getInputItems");
        if (!(inputs instanceof List<?> list) || list.size() != 1 || !(list.get(0) instanceof Ingredient ingredient)
                || ingredient.getClass() != Ingredient.class || !ingredient.isVanilla() || !ingredient.isSimple())
            throw GameMachineRecipe.unsupported();
    }
    private static List<GameMachineRecipe.Choice> choices(IJeiRuntime jei, IRecipeSlotView slot) throws IOException {
        var result = new ArrayList<GameMachineRecipe.Choice>();
        try (var ingredients = slot.getAllIngredients()) {
            var iterator = ingredients.iterator();
            while (iterator.hasNext()) {
                if (result.size() >= 64) throw GameMachineRecipe.unsupported();
                var typed = iterator.next();
                if (!visible(jei, typed)) throw GameMachineRecipe.unsupported();
                Object value = typed.getIngredient();
                if (typed.getType() == VanillaTypes.ITEM_STACK && value instanceof ItemStack item) {
                    var key = ForgeRegistries.ITEMS.getKey(item.getItem());
                    if (key == null || item.isEmpty() || item.hasTag() || item.getCount() > item.getMaxStackSize())
                        throw GameMachineRecipe.unsupported();
                    result.add(new GameMachineRecipe.Choice("item", key.toString(), item.getCount()));
                } else if (typed.getType() == jei.getJeiHelpers().getPlatformFluidHelper().getFluidIngredientType()
                        && value instanceof FluidStack fluid) {
                    var key = ForgeRegistries.FLUIDS.getKey(fluid.getFluid());
                    if (key == null || fluid.isEmpty() || fluid.hasTag()) throw GameMachineRecipe.unsupported();
                    result.add(new GameMachineRecipe.Choice("fluid", key.toString(), fluid.getAmount()));
                } else throw GameMachineRecipe.unsupported();
            }
        }
        return result;
    }
    private static <T> boolean visible(IJeiRuntime jei, ITypedIngredient<T> ingredient) {
        return jei.getIngredientVisibility().isIngredientVisible(ingredient.getType(), ingredient.getIngredient());
    }
    private static Object call(Object target, String method) throws IOException {
        try { return target.getClass().getMethod(method).invoke(target); }
        catch (ReflectiveOperationException | SecurityException failure) { throw GameMachineRecipe.unsupported(); }
    }
}
