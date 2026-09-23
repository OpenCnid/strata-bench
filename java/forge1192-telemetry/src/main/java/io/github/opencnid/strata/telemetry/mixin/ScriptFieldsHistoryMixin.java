package io.github.opencnid.strata.telemetry.mixin;

import java.lang.reflect.Field;
import io.github.opencnid.strata.telemetry.ScriptFieldHistory;
import io.github.opencnid.strata.telemetry.SetupHistoryMarker;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Redirect;

@Pseudo
@Mixin(targets="dev.latvian.mods.rhino.JavaMembers", remap=false)
abstract class ScriptFieldsHistoryMixin implements SetupHistoryMarker {
    @Redirect(method="put(Ldev/latvian/mods/rhino/Scriptable;Ljava/lang/String;Ljava/lang/Object;Ljava/lang/Object;ZLdev/latvian/mods/rhino/Context;)V",
        at=@At(value="INVOKE", target="Ljava/lang/reflect/Field;set(Ljava/lang/Object;Ljava/lang/Object;)V"),
        remap=false, require=1, expect=1, allow=1)
    private void strata$fieldWrite(Field field, Object receiver, Object value) throws IllegalAccessException {
        ScriptFieldHistory.beforeSet(field);
        // Keep caller-sensitive reflection in the original transformed class.
        field.set(receiver, value);
    }
}
