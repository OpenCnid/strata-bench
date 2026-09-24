package io.github.opencnid.strata.telemetry.mixin;

import java.util.HashMap;
import io.github.opencnid.strata.telemetry.ObservedGlobalMap;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Redirect;

/** Install at construction, before script bindings or other code can retain aliases. */
@Pseudo
@Mixin(targets="dev.latvian.mods.kubejs.BuiltinKubeJSPlugin", remap=false)
abstract class GlobalHistoryMixin {
    @Redirect(method="<clinit>()V", at=@At(value="NEW", target="java/util/HashMap"),
        remap=false, require=1, expect=1, allow=1)
    private static HashMap<String,Object> strata$global() { return new ObservedGlobalMap(); }
}
