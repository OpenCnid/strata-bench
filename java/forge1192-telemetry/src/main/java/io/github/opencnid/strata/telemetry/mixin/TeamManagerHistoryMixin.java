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
@Mixin(targets="dev.ftb.mods.ftbteams.data.TeamManager", remap=false)
abstract class TeamManagerHistoryMixin implements SetupHistoryMarker {
    @Inject(method="load()V", at=@At("HEAD"), remap=false, require=1, expect=1, allow=1)
    private void strata$entry0(CallbackInfo ci) {
        SetupHistory.attempt("team_reload");
    }
    @Inject(method="createPartyTeam(Lnet/minecraft/server/level/ServerPlayer;Ljava/lang/String;)Ldev/ftb/mods/ftbteams/data/PartyTeam;", at=@At("HEAD"), remap=false, require=1, expect=1, allow=1)
    private void strata$entry1(CallbackInfoReturnable<?> ci) {
        SetupHistory.attempt("team_create");
    }
    @Inject(method="createPlayerTeam(Lnet/minecraft/server/level/ServerPlayer;Ljava/util/UUID;Ljava/lang/String;)Ldev/ftb/mods/ftbteams/data/PlayerTeam;", at=@At("HEAD"), remap=false, require=1, expect=1, allow=1)
    private void strata$entry2(CallbackInfoReturnable<?> ci) {
        SetupHistory.attempt("team_create");
    }
    @Inject(method="createServerTeam(Lnet/minecraft/server/level/ServerPlayer;Ljava/lang/String;)Ldev/ftb/mods/ftbteams/data/ServerTeam;", at=@At("HEAD"), remap=false, require=1, expect=1, allow=1)
    private void strata$entry3(CallbackInfoReturnable<?> ci) {
        SetupHistory.attempt("team_create");
    }
}
