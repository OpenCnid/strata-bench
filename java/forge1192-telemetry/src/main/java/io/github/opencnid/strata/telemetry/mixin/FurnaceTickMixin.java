package io.github.opencnid.strata.telemetry.mixin;

import io.github.opencnid.strata.telemetry.FurnaceCapture;
import io.github.opencnid.strata.telemetry.FurnaceTickMarker;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

@Pseudo
@Mixin(targets="cofh.thermal.lib.block.entity.MachineBlockEntity", remap=false)
abstract class FurnaceTickMixin implements FurnaceTickMarker {
    @Inject(method="processTick()I", at=@At("HEAD"), remap=false, require=1, expect=1, allow=1)
    private void strata$tickEnter(CallbackInfoReturnable<Integer> ci) { FurnaceCapture.tickEnter(this); }

    // Preserve both original returns: zero remaining work and ordinary debit.
    @Inject(method="processTick()I", at=@At("RETURN"), remap=false, require=2, expect=2, allow=2)
    private void strata$tickExit(CallbackInfoReturnable<Integer> ci) { FurnaceCapture.tickExit(this,ci.getReturnValueI()); }
}
