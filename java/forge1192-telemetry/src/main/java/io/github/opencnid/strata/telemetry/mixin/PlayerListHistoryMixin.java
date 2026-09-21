package io.github.opencnid.strata.telemetry.mixin;

import io.github.opencnid.strata.telemetry.SetupHistory;
import io.github.opencnid.strata.telemetry.SetupHistoryMarker;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import net.minecraft.server.players.PlayerList;

@Mixin(PlayerList.class)
abstract class PlayerListHistoryMixin implements SetupHistoryMarker {
    @Inject(method="m_11284_(Z)V", at=@At("HEAD"), remap=false, require=1, expect=1, allow=1)
    private void strata$cheats(CallbackInfo ci) { SetupHistory.attempt("allow_cheats"); }
}
