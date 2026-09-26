package io.github.opencnid.strata.telemetry.mixin;

import io.github.opencnid.strata.telemetry.FurnaceRegistration;
import io.github.opencnid.strata.telemetry.RecipeRegistrationMarker;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Coerce;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

@Pseudo
@Mixin(targets="cofh.thermal.lib.util.managers.SingleItemRecipeManager",remap=false)
abstract class RecipeRegistrationMixin implements RecipeRegistrationMarker {
    @Inject(method="addRecipe(Lcofh/thermal/lib/util/recipes/ThermalRecipe;Lcofh/thermal/lib/util/recipes/internal/BaseMachineRecipe$RecipeType;)V",at=@At("HEAD"),remap=false,require=1,expect=1,allow=1)
    private void strata$registerBegin(@Coerce Object recipe,@Coerce Object kind,CallbackInfo ci) { FurnaceRegistration.enter(this,recipe); }
    @Inject(method="addRecipe(Lcofh/thermal/lib/util/recipes/ThermalRecipe;Lcofh/thermal/lib/util/recipes/internal/BaseMachineRecipe$RecipeType;)V",at=@At("RETURN"),remap=false,require=1,expect=1,allow=1)
    private void strata$registerEnd(@Coerce Object recipe,@Coerce Object kind,CallbackInfo ci) { FurnaceRegistration.leave(this); }
    // Callback-only signature reads the exact returned object, never recreates it.
    @Inject(method="addRecipe(IFLjava/util/List;Ljava/util/List;Ljava/util/List;Ljava/util/List;Ljava/util/List;Lcofh/thermal/lib/util/recipes/internal/BaseMachineRecipe$RecipeType;)Lcofh/thermal/lib/util/recipes/internal/IMachineRecipe;",at=@At("RETURN"),remap=false,require=5,expect=5,allow=5)
    private void strata$internal(CallbackInfoReturnable<Object> cir) { FurnaceRegistration.returned(this,cir.getReturnValue()); }
}
