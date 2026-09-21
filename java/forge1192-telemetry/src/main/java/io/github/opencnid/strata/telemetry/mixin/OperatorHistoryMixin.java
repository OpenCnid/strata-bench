package io.github.opencnid.strata.telemetry.mixin;

import io.github.opencnid.strata.telemetry.SetupHistory;
import io.github.opencnid.strata.telemetry.SetupHistoryMarker;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import net.minecraft.server.players.StoredUserList;
import net.minecraft.server.players.ServerOpList;

@Mixin(StoredUserList.class)
abstract class OperatorHistoryMixin implements SetupHistoryMarker {
    @Inject(method="m_11381_(Lnet/minecraft/server/players/StoredUserEntry;)V",
        at=@At("HEAD"), remap=false, require=1, expect=1, allow=1)
    private void strata$add(CallbackInfo ci) {
        if ((Object)this instanceof ServerOpList) SetupHistory.attempt("operator_add");
    }
    @Inject(method="m_11393_(Ljava/lang/Object;)V",
        at=@At("HEAD"), remap=false, require=1, expect=1, allow=1)
    private void strata$remove(CallbackInfo ci) {
        if ((Object)this instanceof ServerOpList) SetupHistory.attempt("operator_remove");
    }
    @Inject(method="m_11399_()V", at=@At("HEAD"), remap=false, require=1, expect=1, allow=1)
    private void strata$reload(CallbackInfo ci) {
        if ((Object)this instanceof ServerOpList) SetupHistory.attempt("operator_reload");
    }
}
