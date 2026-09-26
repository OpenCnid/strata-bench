package io.github.opencnid.strata.telemetry.mixin;

import io.github.opencnid.strata.telemetry.FurnaceCapture;
import io.github.opencnid.strata.telemetry.FurnaceCaptureMarker;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Pseudo
@Mixin(targets="cofh.thermal.lib.block.entity.MachineBlockEntity", remap=false)
abstract class FurnaceCaptureMixin implements FurnaceCaptureMarker {
    @Inject(method="processFinish()V", at=@At("HEAD"), remap=false, require=1, expect=1, allow=1)
    private void strata$furnaceEnter(CallbackInfo ci) { FurnaceCapture.enter(this); }

    // validateInputs has already refreshed curRecipe and returned true here.
    @Inject(method="processFinish()V", at=@At(value="INVOKE", target="Lcofh/thermal/lib/block/entity/MachineBlockEntity;resolveOutputs()V"), remap=false, require=1, expect=1, allow=1)
    private void strata$furnaceBegin(CallbackInfo ci) { FurnaceCapture.phase(this, 1); }

    @Inject(method="processFinish()V", at=@At(value="INVOKE", target="Lcofh/thermal/lib/block/entity/MachineBlockEntity;resolveOutputs()V", shift=At.Shift.AFTER), remap=false, require=1, expect=1, allow=1)
    private void strata$furnaceOutputs(CallbackInfo ci) { FurnaceCapture.phase(this, 2); }

    @Inject(method="processFinish()V", at=@At(value="INVOKE", target="Lcofh/thermal/lib/block/entity/MachineBlockEntity;resolveInputs()V", shift=At.Shift.AFTER), remap=false, require=1, expect=1, allow=1)
    private void strata$furnaceInputs(CallbackInfo ci) { FurnaceCapture.phase(this, 3); }

    // Two original returns: failed validation and ordinary completion.
    @Inject(method="processFinish()V", at=@At("RETURN"), remap=false, require=2, expect=2, allow=2)
    private void strata$furnaceExit(CallbackInfo ci) { FurnaceCapture.exit(this); }
}
