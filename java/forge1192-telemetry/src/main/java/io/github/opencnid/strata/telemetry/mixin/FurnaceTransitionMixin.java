package io.github.opencnid.strata.telemetry.mixin;

import io.github.opencnid.strata.telemetry.FurnaceCapture;
import io.github.opencnid.strata.telemetry.FurnaceTransitionMarker;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Pseudo
@Mixin(targets="cofh.thermal.lib.block.entity.MachineBlockEntity", remap=false)
abstract class FurnaceTransitionMixin implements FurnaceTransitionMarker {
    @Inject(method="processStart()V", at=@At("HEAD"), remap=false, require=1, expect=1, allow=1)
    private void strata$startEnter(CallbackInfo ci) { FurnaceCapture.transitionEnter(this,"start"); }

    @Inject(method="processStart()V", at=@At("RETURN"), remap=false, require=1, expect=1, allow=1)
    private void strata$startExit(CallbackInfo ci) { FurnaceCapture.transitionExit(this,"start"); }

    // Only the native stop-branch refund; never redirect or replace modify().
    @Inject(method="tickServer()V", at=@At(value="INVOKE",
        target="Lcofh/lib/energy/EnergyStorageCoFH;modify(I)V", shift=At.Shift.BEFORE),
        remap=false, require=1, expect=1, allow=1)
    private void strata$refundEnter(CallbackInfo ci) { FurnaceCapture.transitionEnter(this,"refund"); }

    @Inject(method="tickServer()V", at=@At(value="INVOKE",
        target="Lcofh/lib/energy/EnergyStorageCoFH;modify(I)V", shift=At.Shift.AFTER),
        remap=false, require=1, expect=1, allow=1)
    private void strata$refundExit(CallbackInfo ci) { FurnaceCapture.transitionExit(this,"refund"); }
}
