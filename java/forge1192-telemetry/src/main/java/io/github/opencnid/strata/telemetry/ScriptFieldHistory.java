package io.github.opencnid.strata.telemetry;

import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.lang.invoke.MethodHandle;
import java.lang.invoke.VarHandle;
import java.util.Set;

/** Observe the pinned Rhino field-write routes without changing their results. */
public final class ScriptFieldHistory {
    private static final Set<String> SETTERS = Set.of("set", "setBoolean", "setByte", "setChar",
        "setShort", "setInt", "setLong", "setFloat", "setDouble");

    private static void writing(Field field) {
        if(field.getDeclaringClass().getName().startsWith("dev.ftb.mods.ftbteams.data."))
            SetupHistory.attempt("team_script_field_write");
    }
    public static void beforeSet(Field field) {
        writing(field);
    }
    public static void beforeInvoke(Method method, Object receiver, Object[] arguments) {
        // Explicit Method.invoke nesting must not hide a Field.set call. Bound
        // inspection; an unresolved deeper chain taints the private reference.
        for(int depth=0; depth<16; depth++) {
            if(opaqueHandleInvocation(method)) {
                // Adapted handles do not expose a trustworthy target field. Record
                // uncertainty, not a fabricated field-write count, before dispatch.
                SetupHistory.attempt("script_handle_unresolved"); return;
            }
            if(method.getDeclaringClass()==Field.class && SETTERS.contains(method.getName())
                    && receiver instanceof Field field) {
                writing(field); return;
            }
            if(method.getDeclaringClass()!=Method.class || !method.getName().equals("invoke")
                    || !(receiver instanceof Method nested) || arguments==null || arguments.length!=2
                    || arguments[1]!=null && !(arguments[1] instanceof Object[])) return;
            method=nested; receiver=arguments[0]; arguments=(Object[])arguments[1];
        }
        SetupHistory.attempt("script_reflection_overflow");
    }
    private static boolean opaqueHandleInvocation(Method method) {
        if(MethodHandle.class.isAssignableFrom(method.getDeclaringClass()))
            return method.getName().startsWith("invoke");
        if(VarHandle.class.isAssignableFrom(method.getDeclaringClass())) {
            try { VarHandle.AccessMode.valueFromMethodName(method.getName()); return true; }
            catch(IllegalArgumentException notAccessMode) { return false; }
        }
        return false;
    }
    private ScriptFieldHistory() {}
}
