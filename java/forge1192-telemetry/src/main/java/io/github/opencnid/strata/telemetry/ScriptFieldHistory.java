package io.github.opencnid.strata.telemetry;

import java.lang.reflect.Field;
import java.lang.reflect.Method;
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
    private ScriptFieldHistory() {}
}
