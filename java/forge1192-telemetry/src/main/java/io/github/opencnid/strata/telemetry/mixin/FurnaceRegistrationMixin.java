package io.github.opencnid.strata.telemetry.mixin;

import io.github.opencnid.strata.telemetry.FurnaceRegistration;
import io.github.opencnid.strata.telemetry.FurnaceRegistrationMarker;
import net.minecraft.world.item.crafting.AbstractCookingRecipe;
import net.minecraft.world.item.crafting.RecipeManager;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

@Pseudo
@Mixin(targets="cofh.thermal.core.util.managers.machine.FurnaceRecipeManager",remap=false)
abstract class FurnaceRegistrationMixin implements FurnaceRegistrationMarker {
    @Inject(method="refresh(Lnet/minecraft/world/item/crafting/RecipeManager;)V",at=@At("HEAD"),remap=false,require=1,expect=1,allow=1)
    private void strata$refreshBegin(RecipeManager registry,CallbackInfo ci) { FurnaceRegistration.begin(this,registry); }
    @Inject(method="refresh(Lnet/minecraft/world/item/crafting/RecipeManager;)V",at=@At("RETURN"),remap=false,require=1,expect=1,allow=1)
    private void strata$refreshEnd(RecipeManager registry,CallbackInfo ci) { FurnaceRegistration.end(this); }
    @Inject(method="clear()V",at=@At("HEAD"),remap=false,require=1,expect=1,allow=1)
    private void strata$clear(CallbackInfo ci) { FurnaceRegistration.clear(this); }
    @Inject(method="convert(Lnet/minecraft/world/item/crafting/AbstractCookingRecipe;)Lcofh/thermal/core/util/recipes/machine/FurnaceRecipe;",at=@At("RETURN"),remap=false,require=1,expect=1,allow=1)
    private void strata$converted(AbstractCookingRecipe source,CallbackInfoReturnable<Object> cir) { FurnaceRegistration.converted(this,source,cir.getReturnValue()); }
}
