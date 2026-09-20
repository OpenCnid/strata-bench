package io.github.opencnid.strata.client.mixin;

import io.github.opencnid.strata.client.JeiRecipeInput;
import java.util.Optional;
import net.minecraft.client.gui.screens.Screen;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Coerce;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

@Pseudo
@Mixin(targets = "mezz.jei.gui.elements.GuiIconButton$UserInputHandler", remap = false)
abstract class JeiButtonInputMixin {
    @Inject(method = "handleUserInput(Lnet/minecraft/client/gui/screens/Screen;Lmezz/jei/gui/input/UserInput;Lmezz/jei/common/input/IInternalKeyMappings;)Ljava/util/Optional;",
        at = @At("RETURN"), remap = false)
    private void strata$button(Screen screen, @Coerce Object input, @Coerce Object keys, CallbackInfoReturnable<Optional<?>> callback) {
        JeiRecipeInput.button(this, screen, input, callback.getReturnValue());
    }
}
