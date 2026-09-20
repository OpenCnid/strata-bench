package io.github.opencnid.strata.client.mixin;

import com.mojang.blaze3d.vertex.PoseStack;
import io.github.opencnid.strata.client.JeiRenderedLayouts;
import mezz.jei.api.ingredients.ITypedIngredient;
import java.util.Optional;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

@Pseudo
@Mixin(targets = "mezz.jei.library.gui.ingredients.RecipeSlot", remap = false)
abstract class JeiSlotDrawMixin {
    @Inject(method = "draw(Lcom/mojang/blaze3d/vertex/PoseStack;)V", at = @At("HEAD"), remap = false)
    private void strata$beginSlot(PoseStack pose, CallbackInfo callback) { JeiRenderedLayouts.beginSlot(this); }
    @Inject(method = "getDisplayedIngredient()Ljava/util/Optional;", at = @At("RETURN"), remap = false)
    private void strata$selection(CallbackInfoReturnable<Optional<ITypedIngredient<?>>> callback) {
        JeiRenderedLayouts.selection(this, callback.getReturnValue());
    }
    @Inject(method = "drawIngredient(Lcom/mojang/blaze3d/vertex/PoseStack;Lmezz/jei/api/ingredients/ITypedIngredient;II)V",
        at = @At("HEAD"), remap = false)
    private void strata$ingredient(PoseStack pose, ITypedIngredient<?> ingredient, int x, int y, CallbackInfo callback) {
        JeiRenderedLayouts.ingredient(this, ingredient);
    }
    @Inject(method = "draw(Lcom/mojang/blaze3d/vertex/PoseStack;)V", at = @At("RETURN"), remap = false)
    private void strata$endSlot(PoseStack pose, CallbackInfo callback) { JeiRenderedLayouts.endSlot(this); }
}
