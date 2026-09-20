package io.github.opencnid.strata.client;

import java.io.IOException;
import java.util.List;
import java.util.Locale;
import mezz.jei.api.constants.VanillaTypes;
import mezz.jei.api.gui.IRecipeLayoutDrawable;
import mezz.jei.api.gui.ingredient.IRecipeSlotDrawable;
import mezz.jei.api.ingredients.ITypedIngredient;
import mezz.jei.api.runtime.IJeiRuntime;
import net.minecraft.client.renderer.Rect2i;
import net.minecraft.world.item.ItemStack;
import net.minecraftforge.fluids.FluidStack;
import net.minecraftforge.registries.ForgeRegistries;

/** Internal copied slot displays. Never queries alternatives or serializes ingredient components. */
final class JeiSlotCopies {
    private final GameRecipeSlots slots = new GameRecipeSlots();
    void begin(Object object, GameRecipeRenderCapture.Key key) throws IOException {
        if (!(object instanceof IRecipeLayoutDrawable<?> layout)
                || !object.getClass().getName().equals("mezz.jei.library.gui.recipes.RecipeLayout")) throw invalid();
        var viewport = new GameRecipeSlots.Rect(0, 0, key.width(), key.height());
        var area = rect(layout.getRect());
        if (!viewport.intersects(area)) throw invalid(); // No category/content getter for wholly off-screen layouts.
        List<?> expected = layout.getRecipeSlotsView().getSlotViews();
        slots.begin(object, viewport, area,
            layout.getRecipeCategory().getRecipeType().getUid().toString(), expected);
    }
    void beginSlot(Object object) throws IOException {
        if (!(object instanceof IRecipeSlotDrawable slot)
                || !object.getClass().getName().equals("mezz.jei.library.gui.ingredients.RecipeSlot")) throw invalid();
        slots.beginSlot(object, rect(slot.getRect()), () -> slot.getRole().name().toLowerCase(Locale.ROOT));
    }
    void ingredient(Object slot, Object object, IJeiRuntime runtime) throws IOException {
        // The geometry guard runs before this reader, so off-screen operands are never inspected.
        slots.ingredient(slot, object, () -> {
            if (!(object instanceof ITypedIngredient<?> typed)) throw invalid();
            return copy(typed, runtime);
        });
    }
    void selection(Object slot, Object selected) throws IOException {
        // Category decorations may query a slot outside its actual draw. Such getters grant no capture authority.
        if (slots.activeSlot(slot)) slots.selection(slot, selected);
    }
    private static <T> GameRecipeSlots.Display copy(ITypedIngredient<T> typed, IJeiRuntime runtime) throws IOException {
        if (!typed.getClass().getName().equals("mezz.jei.library.ingredients.TypedIngredient"))
            return new GameRecipeSlots.Display("unsupported", null, 0);
        var type = typed.getType();
        boolean item = type == VanillaTypes.ITEM_STACK;
        boolean fluid = type == runtime.getJeiHelpers().getPlatformFluidHelper().getFluidIngredientType();
        if (!item && !fluid) return new GameRecipeSlots.Display("unsupported", null, 0);
        T value = typed.getIngredient();
        if (!runtime.getIngredientVisibility().isIngredientVisible(type, value)) throw invalid();
        if (item && value instanceof ItemStack stack && !stack.isEmpty() && !stack.hasTag()) {
            var key = ForgeRegistries.ITEMS.getKey(stack.getItem());
            if (key == null || stack.getCount() < 1) throw invalid();
            return new GameRecipeSlots.Display("item", key.toString(), stack.getCount());
        }
        if (fluid && value instanceof FluidStack stack && !stack.isEmpty() && !stack.hasTag()) {
            var key = ForgeRegistries.FLUIDS.getKey(stack.getFluid());
            if (key == null || stack.getAmount() < 1) throw invalid();
            return new GameRecipeSlots.Display("fluid", key.toString(), stack.getAmount());
        }
        return new GameRecipeSlots.Display("unsupported", null, 0);
    }
    void endSlot(Object slot) throws IOException { slots.endSlot(slot); }
    GameRecipeSlots.Layout finish(Object layout) throws IOException { return slots.finish(layout); }
    void clear() { slots.clear(); }
    private static GameRecipeSlots.Rect rect(Rect2i value) throws IOException {
        if (value == null) throw invalid();
        var result = new GameRecipeSlots.Rect(value.getX(), value.getY(), value.getWidth(), value.getHeight()); result.validate(); return result;
    }
    private static IOException invalid() { return new IOException("GAME_RECIPE_SLOT_CAPTURE_INVALID"); }
}
