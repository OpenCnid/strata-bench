package io.github.opencnid.strata.client.mixin;

import com.mojang.blaze3d.platform.InputConstants;
import io.github.opencnid.strata.client.NativeKeyInput;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/** Only an owned input session overrides polling, on its own client thread/window. */
@Mixin(InputConstants.class)
abstract class KeyPollingMixin {
    @Inject(method = "m_84830_(JI)Z", at = @At("HEAD"), cancellable = true,
        remap = false, require = 1, expect = 1, allow = 1)
    private static void strata$keyPoll(long window, int key, CallbackInfoReturnable<Boolean> callback) {
        Boolean value = NativeKeyInput.polled(window, key);
        if (value != null) callback.setReturnValue(value);
    }
}
