package io.github.opencnid.strata.client.mixin;

import com.mojang.blaze3d.vertex.PoseStack;
import io.github.opencnid.strata.client.JeiRenderedLayouts;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Pseudo
@Mixin(targets = "mezz.jei.gui.elements.GuiIconButton", remap = false)
abstract class JeiControlDrawMixin {
    @Inject(method = "m_6305_(Lcom/mojang/blaze3d/vertex/PoseStack;IIF)V", at = @At("HEAD"), remap = false)
    private void strata$begin(PoseStack pose, int x, int y, float delta, CallbackInfo callback) {
        JeiRenderedLayouts.control(true, this, pose);
    }
    @Inject(method = "m_6305_(Lcom/mojang/blaze3d/vertex/PoseStack;IIF)V", at = @At("RETURN"), remap = false)
    private void strata$end(PoseStack pose, int x, int y, float delta, CallbackInfo callback) {
        JeiRenderedLayouts.control(false, this, pose);
    }
}
