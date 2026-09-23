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
@Mixin(targets="dev.ftb.mods.ftbteams.data.PartyTeam", remap=false)
abstract class PartyHistoryMixin implements SetupHistoryMarker {
    @Inject(method="join(Lnet/minecraft/commands/CommandSourceStack;)I", at=@At("HEAD"), remap=false, require=1, expect=1, allow=1)
    private void strata$entry0(CallbackInfoReturnable<?> ci) {
        SetupHistory.attempt("party_change");
    }
    @Inject(method="invite(Lnet/minecraft/server/level/ServerPlayer;Ljava/util/Collection;)I", at=@At("HEAD"), remap=false, require=1, expect=1, allow=1)
    private void strata$entry1(CallbackInfoReturnable<?> ci) {
        SetupHistory.attempt("party_change");
    }
    @Inject(method="kick(Lnet/minecraft/commands/CommandSourceStack;Ljava/util/Collection;)I", at=@At("HEAD"), remap=false, require=1, expect=1, allow=1)
    private void strata$entry2(CallbackInfoReturnable<?> ci) {
        SetupHistory.attempt("party_change");
    }
    @Inject(method="promote(Lnet/minecraft/server/level/ServerPlayer;Ljava/util/Collection;)I", at=@At("HEAD"), remap=false, require=1, expect=1, allow=1)
    private void strata$entry3(CallbackInfoReturnable<?> ci) {
        SetupHistory.attempt("party_change");
    }
    @Inject(method="demote(Lnet/minecraft/server/level/ServerPlayer;Ljava/util/Collection;)I", at=@At("HEAD"), remap=false, require=1, expect=1, allow=1)
    private void strata$entry4(CallbackInfoReturnable<?> ci) {
        SetupHistory.attempt("party_change");
    }
    @Inject(method="transferOwnership(Lnet/minecraft/commands/CommandSourceStack;Lcom/mojang/authlib/GameProfile;)I", at=@At("HEAD"), remap=false, require=1, expect=1, allow=1)
    private void strata$entry5(CallbackInfoReturnable<?> ci) {
        SetupHistory.attempt("party_change");
    }
    @Inject(method="leave(Ljava/util/UUID;)I", at=@At("HEAD"), remap=false, require=1, expect=1, allow=1)
    private void strata$entry6(CallbackInfoReturnable<?> ci) {
        SetupHistory.attempt("party_change");
    }
    @Inject(method="addAlly(Lnet/minecraft/commands/CommandSourceStack;Ljava/util/Collection;)I", at=@At("HEAD"), remap=false, require=1, expect=1, allow=1)
    private void strata$entry7(CallbackInfoReturnable<?> ci) {
        SetupHistory.attempt("party_change");
    }
    @Inject(method="removeAlly(Lnet/minecraft/commands/CommandSourceStack;Ljava/util/Collection;)I", at=@At("HEAD"), remap=false, require=1, expect=1, allow=1)
    private void strata$entry8(CallbackInfoReturnable<?> ci) {
        SetupHistory.attempt("party_change");
    }
    @Inject(method="forceDisband(Lnet/minecraft/commands/CommandSourceStack;)I", at=@At("HEAD"), remap=false, require=1, expect=1, allow=1)
    private void strata$entry9(CallbackInfoReturnable<?> ci) {
        SetupHistory.attempt("party_change");
    }
}
