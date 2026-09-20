package io.github.opencnid.strata.client.mixin;

import io.github.opencnid.strata.client.JeiRecipeInput;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

@Pseudo
@Mixin(targets = "mezz.jei.gui.elements.GuiIconButton", remap = false)
abstract class JeiButtonFactoryMixin {
    @Inject(method = "createInputHandler()Lmezz/jei/gui/input/IUserInputHandler;", at = @At("RETURN"), remap = false)
    private void strata$handler(CallbackInfoReturnable<Object> callback) { JeiRecipeInput.factory(this, callback.getReturnValue()); }
}
