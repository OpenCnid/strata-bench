package io.github.opencnid.strata.telemetry.mixin;

import io.github.opencnid.strata.telemetry.FurnaceCapture;
import io.github.opencnid.strata.telemetry.FurnaceLifetimeMarker;
import net.minecraft.world.level.block.entity.BlockEntity;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Mixin(BlockEntity.class)
abstract class FurnaceLifetimeMixin implements FurnaceLifetimeMarker {
    @Inject(method="m_7651_()V",at=@At("HEAD"),remap=false,require=1,expect=1,allow=1)
    private void strata$removed(CallbackInfo ci) { FurnaceCapture.retire(this,"removed"); }
    @Inject(method="onChunkUnloaded()V",at=@At("HEAD"),remap=false,require=1,expect=1,allow=1)
    private void strata$unloaded(CallbackInfo ci) { FurnaceCapture.retire(this,"unloaded"); }
    @Inject(method="m_6339_()V",at=@At("HEAD"),remap=false,require=1,expect=1,allow=1)
    private void strata$reactivated(CallbackInfo ci) { FurnaceCapture.retire(this,"reactivated"); }
}
