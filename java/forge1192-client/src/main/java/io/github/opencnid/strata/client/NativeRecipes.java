package io.github.opencnid.strata.client;

import com.google.gson.JsonObject;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import java.util.TreeMap;
import net.minecraft.client.Minecraft;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.Container;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.inventory.CraftingContainer;
import net.minecraft.world.inventory.RecipeBookMenu;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.crafting.Ingredient;
import net.minecraft.world.item.crafting.Recipe;
import net.minecraft.world.item.crafting.ShapedRecipe;
import net.minecraft.world.item.crafting.ShapelessRecipe;
import net.minecraftforge.registries.ForgeRegistries;

/** Actual unlocked recipe book, without exposing the server's complete recipe manager. */
final class NativeRecipes {
    private final Minecraft client;
    private final GameRecipes catalog = new GameRecipes();
    NativeRecipes(Minecraft client) { this.client = client; }
    private void connected() throws IOException {
        if (!client.isSameThread()) throw new IOException("CLIENT_THREAD_REQUIRED");
        if (client.player == null || client.level == null || client.getConnection() == null) throw new IOException("GAME_NOT_CONNECTED");
    }
    JsonObject page(int after) throws IOException {
        connected(); var known = new TreeMap<String, Recipe<?>>(); int inspected = 0;
        var book = client.player.getRecipeBook();
        for (var collection : book.getCollections()) for (var recipe : collection.getRecipes()) {
            if (++inspected > 10000) throw new IOException("GAME_RECIPE_BOUNDS");
            if (!book.contains(recipe)) continue; // Never inspect a locked definition.
            String id = GameRecipes.id(recipe.getId().toString()); var old = known.put(id, recipe);
            if (old != null && old != recipe) throw new IOException("GAME_RECIPE_AMBIGUOUS");
            if (client.getConnection().getRecipeManager().byKey(recipe.getId()).orElse(null) != recipe) {
                throw new IOException("GAME_RECIPE_CHANGED");
            }
        }
        var definitions = new ArrayList<JsonObject>(); int total = 0;
        for (var entry : known.entrySet()) {
            JsonObject value;
            try { value = definition(entry.getValue()); }
            catch (IOException unsupported) {
                if (!java.util.Set.of("MECHANIC_UNSUPPORTED", "REGISTRY_UNSUPPORTED").contains(unsupported.getMessage())) throw unsupported;
                value = GameRecipes.unsupported(entry.getKey());
            }
            total += value.toString().length(); if (total > 4 * 1024 * 1024) throw new IOException("GAME_RECIPE_BOUNDS");
            definitions.add(value);
        }
        return catalog.page(definitions, after);
    }
    Recipe<?> resolve(String id) throws IOException {
        connected(); var location = new ResourceLocation(GameRecipes.id(id));
        if (!client.player.getRecipeBook().contains(location)) throw new IOException("RECIPE_NOT_KNOWN");
        var recipe = client.getConnection().getRecipeManager().byKey(location).orElse(null);
        if (recipe == null) throw new IOException("GAME_RECIPE_CHANGED");
        definition(recipe); return recipe;
    }
    void validate(Recipe<?> recipe, JsonObject original) throws IOException {
        if (resolve(recipe.getId().toString()) != recipe || !definition(recipe).equals(original)) throw new IOException("GAME_RECIPE_CHANGED");
    }
    static JsonObject definition(Recipe<?> recipe) throws IOException {
        boolean shaped = recipe.getClass() == ShapedRecipe.class;
        if ((!shaped && recipe.getClass() != ShapelessRecipe.class) || recipe.isSpecial()) throw new IOException("MECHANIC_UNSUPPORTED");
        var key = ForgeRegistries.RECIPE_SERIALIZERS.getKey(recipe.getSerializer());
        String expected = shaped ? "minecraft:crafting_shaped" : "minecraft:crafting_shapeless";
        if (key == null || !expected.equals(key.toString())) throw new IOException("MECHANIC_UNSUPPORTED");
        ItemStack output = recipe.getResultItem();
        if (output.isEmpty() || output.hasTag() || output.getCount() > output.getMaxStackSize()) throw new IOException("MECHANIC_UNSUPPORTED");
        var ingredients = new ArrayList<List<String>>();
        if (recipe.getIngredients().size() > 9) throw new IOException("MECHANIC_UNSUPPORTED");
        for (Ingredient ingredient : recipe.getIngredients()) {
            if (ingredient.getClass() != Ingredient.class || !ingredient.isVanilla() || !ingredient.isSimple()) throw new IOException("MECHANIC_UNSUPPORTED");
            var items = ingredient.getItems(); if (items.length > 64) throw new IOException("MECHANIC_UNSUPPORTED");
            var choices = new java.util.TreeSet<String>();
            for (var item : items) {
                if (item.isEmpty() || item.hasTag()) throw new IOException("MECHANIC_UNSUPPORTED");
                var itemKey = ForgeRegistries.ITEMS.getKey(item.getItem());
                if (itemKey == null) throw new IOException("REGISTRY_UNSUPPORTED"); choices.add(itemKey.toString());
            }
            ingredients.add(List.copyOf(choices));
        }
        return GameRecipes.definition(recipe.getId().toString(), expected, shaped ? ((ShapedRecipe) recipe).getWidth() : 0,
            shaped ? ((ShapedRecipe) recipe).getHeight() : 0, ingredients, NativeGameRuntime.inventoryStack(output));
    }
    @SuppressWarnings({"rawtypes", "unchecked"}) // Both exact allowed recipe classes accept CraftingContainer.
    List<ItemStack> remainders(Recipe<?> recipe, RecipeBookMenu<?> menu) throws IOException {
        if (!((RecipeBookMenu) menu).recipeMatches(recipe)) throw new IOException("PRECONDITION_FAILED");
        var dummy = new AbstractContainerMenu(null, -1) {
            public ItemStack quickMoveStack(Player player, int slot) { throw new UnsupportedOperationException(); }
            public boolean stillValid(Player player) { return false; }
            public void slotsChanged(Container container) { }
        };
        var grid = new CraftingContainer(dummy, menu.getGridWidth(), menu.getGridHeight());
        for (int i = 0; i < grid.getContainerSize(); i++) grid.setItem(i, menu.slots.get(i + 1).getItem().copy());
        Recipe<CraftingContainer> crafting = (Recipe<CraftingContainer>) recipe;
        if (!crafting.matches(grid, client.level) || !NativeGameRuntime.inventoryStack(crafting.assemble(grid))
                .equals(NativeGameRuntime.inventoryStack(recipe.getResultItem()))) throw new IOException("MECHANIC_UNSUPPORTED");
        var result = new ArrayList<ItemStack>();
        for (var item : crafting.getRemainingItems(grid)) {
            if (item.getCount() > item.getMaxStackSize()) throw new IOException("GAME_REMAINDER_UNSUPPORTED");
            result.add(item.copy());
        }
        return result;
    }
}
