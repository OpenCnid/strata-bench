package io.github.opencnid.strata.client.mixin;

import io.github.opencnid.strata.client.JeiRecipeInput;
import net.minecraft.client.gui.screens.Screen;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Coerce;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

@Pseudo
@Mixin(targets = "mezz.jei.gui.input.handlers.UserInputRouter", remap = false)
abstract class JeiInputRouterMixin {
    @Inject(method = "<init>(Ljava/lang/String;[Lmezz/jei/gui/input/IUserInputHandler;)V", at = @At("RETURN"), remap = false)
    private void strata$router(String name, @Coerce Object[] handlers, CallbackInfo callback) {
        JeiRecipeInput.router(this, name, handlers);
    }
    @Inject(method = "handleUserInput(Lnet/minecraft/client/gui/screens/Screen;Lmezz/jei/gui/input/UserInput;Lmezz/jei/common/input/IInternalKeyMappings;)Z",
        at = @At("HEAD"), remap = false)
    private void strata$begin(Screen screen, @Coerce Object input, @Coerce Object keys, CallbackInfoReturnable<Boolean> callback) {
        JeiRecipeInput.route(true, this, screen, input, false);
    }
    @Inject(method = "handleUserInput(Lnet/minecraft/client/gui/screens/Screen;Lmezz/jei/gui/input/UserInput;Lmezz/jei/common/input/IInternalKeyMappings;)Z",
        at = @At("RETURN"), remap = false)
    private void strata$end(Screen screen, @Coerce Object input, @Coerce Object keys, CallbackInfoReturnable<Boolean> callback) {
        JeiRecipeInput.route(false, this, screen, input, callback.getReturnValueZ());
    }
}
