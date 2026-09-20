package io.github.opencnid.strata.client;

import com.google.gson.JsonObject;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.TreeSet;
import net.minecraft.client.Minecraft;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.crafting.Recipe;
import net.minecraftforge.registries.ForgeRegistries;

/** Explicit exact-pack EMI source. Never consults JEI or fills/transfers recipes. */
final class EmiRecipeSource {
    static final String FILE = "emi-1.1.24+1.19.2+forge.jar";
    static final String HASH = "1f3902eae8d9e6a4c719a7c176d9f9deee12ec0487cf8a05a61c2d3ecf32d43d";
    private static final GameRecipeQuery projection = new GameRecipeQuery();
    private static Object lastManager, lastConnection;
    private static long generation;
    private static final String API = "dev.emi.emi.api.EmiApi", STACK = "dev.emi.emi.api.stack.EmiStack",
        INGREDIENT = "dev.emi.emi.api.stack.EmiIngredient", RECIPE = "dev.emi.emi.api.recipe.EmiRecipe",
        MANAGER = "dev.emi.emi.api.recipe.EmiRecipeManager", CATEGORY = "dev.emi.emi.api.recipe.EmiRecipeCategory",
        CRAFTING = "dev.emi.emi.api.recipe.EmiCraftingRecipe";

    // Public API methods plus the pinned public reload/visibility predicates used by EMI itself.
    // Reflection avoids shipping or shading a second mod and never accesses private members.
    private static Class<?> type(String name) throws IOException {
        try { return Class.forName(name); }
        catch (ReflectiveOperationException | LinkageError e) { throw unavailable(); }
    }
    private static Object call(String owner, Object target, String name, Class<?>[] signature, Object... args) throws IOException {
        try { return type(owner).getMethod(name, signature).invoke(target, args); }
        catch (ReflectiveOperationException | IllegalArgumentException | SecurityException | LinkageError e) { throw unavailable(); }
    }
    private static Object call(String owner, Object target, String name) throws IOException {
        return call(owner, target, name, new Class<?>[0]);
    }
    private static IOException unavailable() { return new IOException("GAME_RECIPE_SOURCE_UNAVAILABLE"); }
    private static IOException unsupported() { return new IOException("MECHANIC_UNSUPPORTED"); }
    private static List<?> list(Object value, int max) throws IOException {
        if (!(value instanceof List<?> values) || values.size() > max) throw new IOException("GAME_RECIPE_BOUNDS");
        return values;
    }
    private static boolean loaded() throws IOException {
        return Boolean.TRUE.equals(call("dev.emi.emi.runtime.EmiReloadManager", null, "isLoaded"));
    }
    private static Object manager() throws IOException { return call(API, null, "getRecipeManager"); }
    private static Object stack(ItemStack value) throws IOException {
        return call(STACK, null, "of", new Class<?>[]{ItemStack.class}, value);
    }
    private static boolean visible(Object value, List<?> index) throws IOException {
        Class<?>[] signature = {type(INGREDIENT)};
        return index.contains(value)
            && Boolean.FALSE.equals(call("dev.emi.emi.runtime.EmiHidden", null, "isHidden", signature, value))
            && Boolean.FALSE.equals(call("dev.emi.emi.runtime.EmiHidden", null, "isDisabled", signature, value));
    }
    private static void time(long started) throws IOException {
        if (System.nanoTime() - started > GameRecipeQuery.MAX_NANOS) throw new IOException("GAME_RECIPE_TIMEOUT");
    }
    static void requireArtifact(Map<String,String> artifacts) throws IOException {
        if (!HASH.equals(artifacts.get(FILE))) throw new IOException("GAME_RECIPE_ARTIFACT_UNSUPPORTED");
    }
    static JsonObject query(GameRecipeQuery.Query query, Map<String,String> artifacts) throws IOException {
        requireArtifact(artifacts);
        if (!query.source().equals("emi") || !query.crafting()) throw unsupported();
        Minecraft client = Minecraft.getInstance();
        if (!client.isSameThread()) throw new IOException("CLIENT_THREAD_REQUIRED");
        final var player = client.player; final var level = client.level; final var connection = client.getConnection();
        if (player == null || level == null || connection == null) throw new IOException("GAME_NOT_CONNECTED");
        if (!loaded()) throw unavailable();
        final Object manager = manager();
        final List<?> index = list(call(API, null, "getIndexStacks"), 65536);
        if (manager == null || index.isEmpty()) throw unavailable();
        if (lastManager != manager || lastConnection != connection) {
            lastManager = manager; lastConnection = connection; generation++;
        }
        final long boundGeneration = generation, started = System.nanoTime();
        var key = new ResourceLocation(query.item());
        if (!ForgeRegistries.ITEMS.containsKey(key)) throw new IOException("TARGET_NOT_OBSERVED");
        Object focus = stack(new ItemStack(ForgeRegistries.ITEMS.getValue(key)));
        if (!visible(focus, index)) throw new IOException("TARGET_NOT_OBSERVED");
        return projection.query(query, new GameRecipeQuery.Source() {
            public long generation() {
                try {
                    return loaded() && manager() == manager && call(API,null,"getIndexStacks") == index
                        && client.player == player && client.level == level && client.getConnection() == connection
                        ? boundGeneration : -1;
                } catch (IOException e) { return -1; }
            }
            public Iterable<? extends GameRecipeQuery.Candidate> focused(GameRecipeQuery.Query requested) throws IOException {
                var matches = list(call(MANAGER, manager, requested.role().equals("input") ? "getRecipesByInput" : "getRecipesByOutput",
                    new Class<?>[]{type(STACK)}, focus), GameRecipeQuery.MAX_MATCHES);
                var result = new ArrayList<GameRecipeQuery.Candidate>();
                for (Object row : matches) {
                    time(started);
                    Object category = call(RECIPE,row,"getCategory");
                    if (!"minecraft:crafting".equals(String.valueOf(call(CATEGORY,category,"getId")))) continue;
                    result.add(new GameRecipeQuery.Candidate() {
                        public boolean visible() throws IOException { time(started); return EmiRecipeSource.visible(focus,index); }
                        public String id() throws IOException {
                            Object id = call(RECIPE,row,"getId");
                            if (!(id instanceof ResourceLocation)) throw unsupported();
                            return id.toString();
                        }
                        public boolean bookUnlocked() throws IOException { return player.getRecipeBook().contains(new ResourceLocation(id())); }
                        public JsonObject definition() throws IOException {
                            time(started);
                            // These exact pinned classes inherit the standard widgets; custom subclasses are not equivalent.
                            if (!java.util.Set.of(CRAFTING, "dev.emi.emi.recipe.EmiShapedRecipe",
                                    "dev.emi.emi.recipe.EmiShapelessRecipe").contains(row.getClass().getName())) throw unsupported();
                            Object backing = call(RECIPE,row,"getBackingRecipe");
                            if (!(backing instanceof Recipe<?> recipe) || !recipe.getId().toString().equals(id())
                                    || connection.getRecipeManager().byKey(recipe.getId()).orElse(null) != recipe) throw unsupported();
                            var definition = NativeRecipes.definition(recipe);
                            var inputs = new ArrayList<List<String>>();
                            for (Object ingredient : list(call(RECIPE,row,"getInputs"),9)) {
                                time(started);
                                if (Boolean.TRUE.equals(call(INGREDIENT,ingredient,"isEmpty"))) { inputs.add(List.of()); continue; }
                                if (!Long.valueOf(1).equals(call(INGREDIENT,ingredient,"getAmount"))
                                        || !Float.valueOf(1).equals(call(INGREDIENT,ingredient,"getChance"))) throw unsupported();
                                var choices = new TreeSet<String>();
                                for (Object choice : list(call(INGREDIENT,ingredient,"getEmiStacks"),64)) {
                                    time(started);
                                    if (Boolean.TRUE.equals(call(STACK,choice,"isEmpty"))) continue;
                                    ItemStack item = plainVisible(choice,index);
                                    if (item.getCount() != 1 || !choices.add(ForgeRegistries.ITEMS.getKey(item.getItem()).toString())) throw unsupported();
                                }
                                inputs.add(List.copyOf(choices));
                            }
                            var outputs = list(call(RECIPE,row,"getOutputs"),1);
                            if (outputs.size()!=1) throw unsupported();
                            ItemStack output = plainVisible(outputs.get(0),index);
                            boolean shapeless;
                            try { shapeless = type(CRAFTING).getField("shapeless").getBoolean(row); }
                            catch (ReflectiveOperationException | SecurityException e) { throw unavailable(); }
                            EmiRecipeDefinition.validate(definition, inputs, NativeGameRuntime.inventoryStack(output), shapeless);
                            time(started); return definition;
                        }
                    });
                }
                return result;
            }
        });
    }
    private static ItemStack plainVisible(Object value, List<?> index) throws IOException {
        if (!visible(value,index) || !Float.valueOf(1).equals(call(STACK,value,"getChance"))
                || !Boolean.FALSE.equals(call(STACK,value,"hasNbt"))) throw unsupported();
        Object raw = call(STACK,value,"getItemStack");
        if (!(raw instanceof ItemStack item) || item.isEmpty() || item.hasTag()
                || !Long.valueOf(item.getCount()).equals(call(STACK,value,"getAmount"))) throw unsupported();
        return item;
    }
}
