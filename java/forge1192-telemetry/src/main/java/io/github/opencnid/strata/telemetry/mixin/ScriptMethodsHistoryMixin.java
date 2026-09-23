package io.github.opencnid.strata.telemetry.mixin;

import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import io.github.opencnid.strata.telemetry.ScriptFieldHistory;
import io.github.opencnid.strata.telemetry.SetupHistoryMarker;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Redirect;

@Pseudo
@Mixin(targets="dev.latvian.mods.rhino.MemberBox", remap=false)
abstract class ScriptMethodsHistoryMixin implements SetupHistoryMarker {
    @Redirect(method="invoke(Ljava/lang/Object;[Ljava/lang/Object;Ldev/latvian/mods/rhino/Context;Ldev/latvian/mods/rhino/Scriptable;)Ljava/lang/Object;",
        at=@At(value="INVOKE", target="Ljava/lang/reflect/Method;invoke(Ljava/lang/Object;[Ljava/lang/Object;)Ljava/lang/Object;"),
        remap=false, require=2, expect=2, allow=2)
    private Object strata$reflectiveWrite(Method method, Object receiver, Object[] arguments)
            throws IllegalAccessException, InvocationTargetException {
        ScriptFieldHistory.beforeInvoke(method, receiver, arguments);
        // Preserve the original MemberBox caller/access context.
        return method.invoke(receiver, arguments);
    }
}
