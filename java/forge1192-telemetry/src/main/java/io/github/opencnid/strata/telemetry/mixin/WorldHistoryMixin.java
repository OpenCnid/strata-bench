package io.github.opencnid.strata.telemetry.mixin;

import io.github.opencnid.strata.telemetry.SetupHistory;
import io.github.opencnid.strata.telemetry.SetupHistoryMarker;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import net.minecraft.world.level.storage.PrimaryLevelData;

@Mixin(PrimaryLevelData.class)
abstract class WorldHistoryMixin implements SetupHistoryMarker {
    @Inject(method="m_5458_(Lnet/minecraft/world/level/GameType;)V",
        at=@At("HEAD"), remap=false, require=1, expect=1, allow=1)
    private void strata$mode(CallbackInfo ci) { SetupHistory.attempt("world_mode"); }
    @Inject(method="m_6166_(Lnet/minecraft/world/Difficulty;)V",
        at=@At("HEAD"), remap=false, require=1, expect=1, allow=1)
    private void strata$difficulty(CallbackInfo ci) { SetupHistory.attempt("world_difficulty"); }
}
