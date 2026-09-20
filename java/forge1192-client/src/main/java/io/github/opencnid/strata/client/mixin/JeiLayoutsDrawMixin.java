package io.github.opencnid.strata.client.mixin;

import com.mojang.blaze3d.vertex.PoseStack;
import io.github.opencnid.strata.client.JeiRenderedLayouts;
import java.util.Optional;
import java.util.Iterator;
import mezz.jei.api.gui.IRecipeLayoutDrawable;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.Redirect;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

@Pseudo
@Mixin(targets = "mezz.jei.gui.recipes.RecipeGuiLayouts", remap = false)
abstract class JeiLayoutsDrawMixin {
    @Inject(method = "draw(Lcom/mojang/blaze3d/vertex/PoseStack;II)Ljava/util/Optional;", at = @At("HEAD"), remap = false)
    private void strata$begin(PoseStack pose, int mouseX, int mouseY, CallbackInfoReturnable<Optional<?>> callback) {
        JeiRenderedLayouts.beginLayouts(this);
    }
    @Redirect(method = "draw(Lcom/mojang/blaze3d/vertex/PoseStack;II)Ljava/util/Optional;",
        at = @At(value = "INVOKE", target = "Ljava/util/Iterator;hasNext()Z"), remap = false, require = 1, expect = 1, allow = 1)
    private boolean strata$hasNext(Iterator<?> iterator) {
        // Preserve the original call count, result and exception. No additional iteration.
        boolean result = iterator.hasNext();
        JeiRenderedLayouts.layoutPredicate(this, iterator, result);
        return result;
    }
    @Redirect(method = "draw(Lcom/mojang/blaze3d/vertex/PoseStack;II)Ljava/util/Optional;",
        at = @At(value = "INVOKE", target = "Lmezz/jei/api/gui/IRecipeLayoutDrawable;drawRecipe(Lcom/mojang/blaze3d/vertex/PoseStack;II)V"), remap = false)
    private void strata$draw(IRecipeLayoutDrawable<?> layout, PoseStack pose, int mouseX, int mouseY) {
        // Preserve the exact native call, arguments and exception; capture only its normal return.
        JeiRenderedLayouts.beginLayout(layout);
        layout.drawRecipe(pose, mouseX, mouseY);
        JeiRenderedLayouts.drawn(layout);
    }
    @Inject(method = "draw(Lcom/mojang/blaze3d/vertex/PoseStack;II)Ljava/util/Optional;", at = @At("RETURN"), remap = false)
    private void strata$end(PoseStack pose, int mouseX, int mouseY, CallbackInfoReturnable<Optional<?>> callback) {
        JeiRenderedLayouts.endLayouts(this);
    }
}
