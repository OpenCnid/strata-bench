package io.github.opencnid.strata.telemetry.mixin;

import io.github.opencnid.strata.telemetry.FurnaceCapture;
import io.github.opencnid.strata.telemetry.FurnaceIntervalMarker;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Pseudo
@Mixin(targets="cofh.thermal.lib.block.entity.MachineBlockEntity",remap=false)
abstract class FurnaceIntervalMixin implements FurnaceIntervalMarker {
    @Inject(method="tickServer()V",at=@At("HEAD"),remap=false,require=1,expect=1,allow=1)
    private void strata$serverEnter(CallbackInfo ci) { FurnaceCapture.serverEnter(this); }
    @Inject(method="tickServer()V",at=@At("RETURN"),remap=false,require=1,expect=1,allow=1)
    private void strata$serverExit(CallbackInfo ci) { FurnaceCapture.serverExit(this); }
    @Inject(method="tickServer()V",at=@At(value="INVOKE",target="Lcofh/thermal/lib/block/entity/MachineBlockEntity;transferInput()V",shift=At.Shift.BEFORE),remap=false,require=2,expect=2,allow=2)
    private void strata$transfer_inputEnter(CallbackInfo ci) { FurnaceCapture.stepEnter(this,"transfer_input"); }
    @Inject(method="tickServer()V",at=@At(value="INVOKE",target="Lcofh/thermal/lib/block/entity/MachineBlockEntity;transferInput()V",shift=At.Shift.AFTER),remap=false,require=2,expect=2,allow=2)
    private void strata$transfer_inputExit(CallbackInfo ci) { FurnaceCapture.stepExit(this,"transfer_input"); }
    @Inject(method="tickServer()V",at=@At(value="INVOKE",target="Lcofh/thermal/lib/block/entity/MachineBlockEntity;transferOutput()V",shift=At.Shift.BEFORE),remap=false,require=2,expect=2,allow=2)
    private void strata$transfer_outputEnter(CallbackInfo ci) { FurnaceCapture.stepEnter(this,"transfer_output"); }
    @Inject(method="tickServer()V",at=@At(value="INVOKE",target="Lcofh/thermal/lib/block/entity/MachineBlockEntity;transferOutput()V",shift=At.Shift.AFTER),remap=false,require=2,expect=2,allow=2)
    private void strata$transfer_outputExit(CallbackInfo ci) { FurnaceCapture.stepExit(this,"transfer_output"); }
    @Inject(method="tickServer()V",at=@At(value="INVOKE",target="Lcofh/thermal/lib/block/entity/MachineBlockEntity;chargeEnergy()V",shift=At.Shift.BEFORE),remap=false,require=1,expect=1,allow=1)
    private void strata$chargeEnter(CallbackInfo ci) { FurnaceCapture.stepEnter(this,"charge"); }
    @Inject(method="tickServer()V",at=@At(value="INVOKE",target="Lcofh/thermal/lib/block/entity/MachineBlockEntity;chargeEnergy()V",shift=At.Shift.AFTER),remap=false,require=1,expect=1,allow=1)
    private void strata$chargeExit(CallbackInfo ci) { FurnaceCapture.stepExit(this,"charge"); }
    @Inject(method="tickServer()V",at=@At(value="INVOKE",target="Lcofh/thermal/lib/block/entity/MachineBlockEntity;processOff()V",shift=At.Shift.BEFORE),remap=false,require=2,expect=2,allow=2)
    private void strata$offEnter(CallbackInfo ci) { FurnaceCapture.stepEnter(this,"off"); }
    @Inject(method="tickServer()V",at=@At(value="INVOKE",target="Lcofh/thermal/lib/block/entity/MachineBlockEntity;processOff()V",shift=At.Shift.AFTER),remap=false,require=2,expect=2,allow=2)
    private void strata$offExit(CallbackInfo ci) { FurnaceCapture.stepExit(this,"off"); }
    @Inject(method="tickServer()V",at=@At(value="FIELD",target="Lcofh/thermal/lib/block/entity/MachineBlockEntity;isActive:Z",opcode=181,shift=At.Shift.BEFORE),remap=false,require=1,expect=1,allow=1)
    private void strata$activateEnter(CallbackInfo ci) { FurnaceCapture.stepEnter(this,"activate"); }
    @Inject(method="tickServer()V",at=@At(value="FIELD",target="Lcofh/thermal/lib/block/entity/MachineBlockEntity;isActive:Z",opcode=181,shift=At.Shift.AFTER),remap=false,require=1,expect=1,allow=1)
    private void strata$activateExit(CallbackInfo ci) { FurnaceCapture.stepExit(this,"activate"); }
}
