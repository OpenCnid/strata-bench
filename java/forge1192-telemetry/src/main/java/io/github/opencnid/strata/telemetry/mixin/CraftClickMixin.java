package io.github.opencnid.strata.telemetry.mixin;

import io.github.opencnid.strata.telemetry.CraftCapture;
import io.github.opencnid.strata.telemetry.CraftClickMarker;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.inventory.ClickType;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/** Pinned 1.19.2 server click bracket. No callback cancellation or game-state writes. */
@Mixin(AbstractContainerMenu.class)
abstract class CraftClickMixin implements CraftClickMarker {
    @Inject(method="m_150399_(IILnet/minecraft/world/inventory/ClickType;Lnet/minecraft/world/entity/player/Player;)V",
        at=@At("HEAD"), remap=false, require=1, expect=1, allow=1)
    private void strata$begin(int slot, int button, ClickType type, Player player, CallbackInfo ci) {
        CraftCapture.begin((AbstractContainerMenu)(Object)this, slot, button, type, player);
    }
    @Inject(method="m_150399_(IILnet/minecraft/world/inventory/ClickType;Lnet/minecraft/world/entity/player/Player;)V",
        at=@At("RETURN"), remap=false, require=1, expect=1, allow=1)
    private void strata$end(int slot, int button, ClickType type, Player player, CallbackInfo ci) {
        CraftCapture.end((AbstractContainerMenu)(Object)this, player);
    }
}
