package io.github.opencnid.strata.telemetry.mixin;

import com.mojang.brigadier.context.CommandContext;
import io.github.opencnid.strata.telemetry.SetupHistory;
import io.github.opencnid.strata.telemetry.SetupHistoryMarker;
import net.minecraft.server.commands.StopCommand;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/** Correlates an exact parsed stop attempt with execution of its pinned native body. */
@Mixin(StopCommand.class)
abstract class StopHistoryMixin implements SetupHistoryMarker {
    @Inject(method="m_138787_(Lcom/mojang/brigadier/context/CommandContext;)I",
        at=@At("HEAD"), remap=false, require=1, expect=1, allow=1)
    private static void strata$stop(CommandContext<?> context, CallbackInfoReturnable<Integer> ci) {
        SetupHistory.stopping(context.getSource());
    }
}
