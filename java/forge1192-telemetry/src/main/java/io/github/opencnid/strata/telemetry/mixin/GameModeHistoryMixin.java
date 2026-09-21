package io.github.opencnid.strata.telemetry.mixin;

import io.github.opencnid.strata.telemetry.SetupHistory;
import io.github.opencnid.strata.telemetry.SetupHistoryMarker;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import net.minecraft.server.level.ServerPlayerGameMode;
import net.minecraft.world.level.GameType;

@Mixin(ServerPlayerGameMode.class)
abstract class GameModeHistoryMixin implements SetupHistoryMarker {
    @Inject(method="m_9273_(Lnet/minecraft/world/level/GameType;Lnet/minecraft/world/level/GameType;)V",
        at=@At("HEAD"), remap=false, require=1, expect=1, allow=1)
    private void strata$mode(GameType next, GameType previous, CallbackInfo ci) {
        if (((ServerPlayerGameMode)(Object)this).getGameModeForPlayer() != next)
            SetupHistory.attempt("actor_mode_change");
    }
}
