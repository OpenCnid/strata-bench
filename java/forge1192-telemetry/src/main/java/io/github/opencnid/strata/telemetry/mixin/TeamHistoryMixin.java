package io.github.opencnid.strata.telemetry.mixin;

import io.github.opencnid.strata.telemetry.SetupHistory;
import io.github.opencnid.strata.telemetry.SetupHistoryMarker;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

@Pseudo
@Mixin(targets="dev.ftb.mods.ftbteams.data.Team", remap=false)
abstract class TeamHistoryMixin implements SetupHistoryMarker {
    @Inject(method="deserializeNBT(Lnet/minecraft/nbt/CompoundTag;)V", at=@At("HEAD"), remap=false, require=1, expect=1, allow=1)
    private void strata$entry0(CallbackInfo ci) {
        SetupHistory.attempt("team_deserialize");
    }
    @Inject(method="changedTeam(Ldev/ftb/mods/ftbteams/data/Team;Ljava/util/UUID;Lnet/minecraft/server/level/ServerPlayer;Z)V", at=@At("HEAD"), remap=false, require=1, expect=1, allow=1)
    private void strata$entry1(CallbackInfo ci) {
        SetupHistory.attempt("party_change");
    }
    @Inject(method="denyInvite(Lnet/minecraft/commands/CommandSourceStack;)I", at=@At("HEAD"), remap=false, require=1, expect=1, allow=1)
    private void strata$entry2(CallbackInfoReturnable<?> ci) {
        SetupHistory.attempt("party_change");
    }
}
