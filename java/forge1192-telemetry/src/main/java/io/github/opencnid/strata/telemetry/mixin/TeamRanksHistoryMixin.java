package io.github.opencnid.strata.telemetry.mixin;

import java.util.HashMap;
import java.util.Map;
import io.github.opencnid.strata.telemetry.TeamMapSupport;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.gen.Accessor;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Redirect;

@Pseudo
@Mixin(targets="dev.ftb.mods.ftbteams.data.TeamBase", remap=false)
abstract class TeamRanksHistoryMixin implements TeamMapSupport.RankSource {
    @Redirect(method="<init>()V", at=@At(value="NEW", target="java/util/HashMap"),
        remap=false, require=1, expect=1, allow=1)
    private HashMap<?,?> strata$ranks() { return TeamMapSupport.rankMap(this); }
    @Accessor(value="ranks", remap=false)
    public abstract Map<?,?> strata$rankMap();
}
