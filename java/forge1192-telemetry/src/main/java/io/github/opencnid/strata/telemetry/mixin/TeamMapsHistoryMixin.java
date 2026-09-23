package io.github.opencnid.strata.telemetry.mixin;

import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.Map;
import io.github.opencnid.strata.telemetry.ObservedTeamHashMap;
import io.github.opencnid.strata.telemetry.ObservedTeamLinkedMap;
import io.github.opencnid.strata.telemetry.TeamMapSupport;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.gen.Accessor;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.Redirect;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

@Pseudo
@Mixin(targets="dev.ftb.mods.ftbteams.data.TeamManager", remap=false)
abstract class TeamMapsHistoryMixin implements TeamMapSupport.CacheSource {
    @Redirect(method="<init>(Lnet/minecraft/server/MinecraftServer;)V",
        at=@At(value="NEW", target="java/util/LinkedHashMap"),
        remap=false, require=2, expect=2, allow=2)
    private LinkedHashMap<?,?> strata$managerMaps() { return new ObservedTeamLinkedMap<>(); }
    @Redirect(method="getTeamNameMap()Ljava/util/Map;",
        at=@At(value="NEW", target="java/util/HashMap"),
        remap=false, require=1, expect=1, allow=1)
    private HashMap<?,?> strata$nameMap() { return new ObservedTeamHashMap<>(false); }
    @Inject(method="getTeamNameMap()Ljava/util/Map;", at=@At("RETURN"),
        remap=false, require=1, expect=1, allow=1)
    private void strata$armCache(CallbackInfoReturnable<Map<?,?>> ci) {
        if(!(ci.getReturnValue() instanceof ObservedTeamHashMap<?,?> observed))
            throw new IllegalStateException("SETUP_TEAM_CACHE_UNOBSERVED");
        observed.arm();
    }
    @Accessor(value="nameMap", remap=false)
    public abstract Map<?,?> strata$nameCache();
}
