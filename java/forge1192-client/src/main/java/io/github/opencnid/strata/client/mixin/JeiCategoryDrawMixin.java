package io.github.opencnid.strata.client.mixin;

import com.mojang.blaze3d.vertex.PoseStack;
import io.github.opencnid.strata.client.JeiRenderedLayouts;
import net.minecraft.client.gui.Font;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Pseudo
@Mixin(targets = "mezz.jei.gui.recipes.RecipeCategoryTitle", remap = false)
abstract class JeiCategoryDrawMixin {
    @Inject(method = "draw(Lcom/mojang/blaze3d/vertex/PoseStack;Lnet/minecraft/client/gui/Font;)V", at = @At("HEAD"), remap = false)
    private void strata$begin(PoseStack pose, Font font, CallbackInfo callback) { JeiRenderedLayouts.beginCategory(this); }
    @Inject(method = "draw(Lcom/mojang/blaze3d/vertex/PoseStack;Lnet/minecraft/client/gui/Font;)V", at = @At("RETURN"), remap = false)
    private void strata$end(PoseStack pose, Font font, CallbackInfo callback) { JeiRenderedLayouts.endCategory(this); }
}
