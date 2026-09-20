package io.github.opencnid.strata.client.mixin;

import com.mojang.blaze3d.vertex.PoseStack;
import io.github.opencnid.strata.client.JeiRenderedLayouts;
import net.minecraft.client.gui.Font;
import net.minecraft.network.chat.Component;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Coerce;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Pseudo
@Mixin(targets = "mezz.jei.common.util.StringUtil", remap = false)
abstract class JeiHeaderDrawMixin {
    @Inject(method = "drawCenteredStringWithShadow(Lcom/mojang/blaze3d/vertex/PoseStack;Lnet/minecraft/client/gui/Font;Lnet/minecraft/network/chat/Component;Lmezz/jei/common/util/ImmutableRect2i;)V", at = @At("HEAD"), remap = false)
    private static void strata$beginTitle(PoseStack pose, Font font, Component text, @Coerce Object area, CallbackInfo callback) {
        JeiRenderedLayouts.header(true, "category", pose, font, text, area);
    }
    @Inject(method = "drawCenteredStringWithShadow(Lcom/mojang/blaze3d/vertex/PoseStack;Lnet/minecraft/client/gui/Font;Lnet/minecraft/network/chat/Component;Lmezz/jei/common/util/ImmutableRect2i;)V", at = @At("RETURN"), remap = false)
    private static void strata$endTitle(PoseStack pose, Font font, Component text, @Coerce Object area, CallbackInfo callback) {
        JeiRenderedLayouts.header(false, "category", pose, font, text, area);
    }
    @Inject(method = "drawCenteredStringWithShadow(Lcom/mojang/blaze3d/vertex/PoseStack;Lnet/minecraft/client/gui/Font;Ljava/lang/String;Lmezz/jei/common/util/ImmutableRect2i;)V", at = @At("HEAD"), remap = false)
    private static void strata$beginPage(PoseStack pose, Font font, String text, @Coerce Object area, CallbackInfo callback) {
        JeiRenderedLayouts.header(true, "page", pose, font, text, area);
    }
    @Inject(method = "drawCenteredStringWithShadow(Lcom/mojang/blaze3d/vertex/PoseStack;Lnet/minecraft/client/gui/Font;Ljava/lang/String;Lmezz/jei/common/util/ImmutableRect2i;)V", at = @At("RETURN"), remap = false)
    private static void strata$endPage(PoseStack pose, Font font, String text, @Coerce Object area, CallbackInfo callback) {
        JeiRenderedLayouts.header(false, "page", pose, font, text, area);
    }
}
