package io.github.opencnid.strata.client.mixin;

import io.github.opencnid.strata.client.ClientFrameProbe;
import net.minecraft.client.Minecraft;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/** Exact Forge 1.19.2 SRG callsite, after final main-target blit and before swap. */
@Mixin(Minecraft.class)
abstract class MinecraftFrameMixin {
    @Inject(method = "m_91383_(Z)V", at = @At(value = "INVOKE",
        target = "Lcom/mojang/blaze3d/platform/Window;m_85435_()V", remap = false),
        remap = false, require = 1, expect = 1, allow = 1)
    private void strata$privateFrame(boolean renderLevel, CallbackInfo callback) {
        ClientFrameProbe.beforeDisplay();
    }
}
