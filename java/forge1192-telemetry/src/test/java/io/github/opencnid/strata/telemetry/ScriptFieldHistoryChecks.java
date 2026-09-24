package io.github.opencnid.strata.telemetry;

import static org.junit.jupiter.api.Assertions.*;
import java.lang.reflect.Field;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.lang.invoke.MethodHandle;
import java.lang.invoke.MethodHandles;
import java.lang.invoke.VarHandle;
import java.util.Arrays;
import java.util.List;
import dev.ftb.mods.ftbteams.data.FieldHistoryFixture;

final class ScriptFieldHistoryChecks {
    public static Object unrelated;
    private static long count(String route) {
        return SetupHistory.capture("startup",null).getAsJsonObject("attempts").get(route).getAsLong();
    }
    static void check() throws Exception {
        var fixture=new FieldHistoryFixture();
        Field field=FieldHistoryFixture.class.getField("actualTeam");
        long initial=count("team_script_field_write");
        ScriptFieldHistory.beforeSet(field);field.set(fixture,null);
        assertNull(fixture.actualTeam);
        ScriptFieldHistory.beforeSet(field);field.set(fixture,fixture);
        assertSame(fixture,fixture.actualTeam);
        Method setter=Field.class.getMethod("set",Object.class,Object.class);
        for(Object value:new Object[]{null,fixture}) {
            Object[] args={fixture,value};
            ScriptFieldHistory.beforeInvoke(setter,field,args);setter.invoke(field,args);
            assertSame(value,fixture.actualTeam);
        }
        Method invoke=Method.class.getMethod("invoke",Object.class,Object[].class);
        for(Object value:new Object[]{null,fixture}) {
            Object[] nested={field,new Object[]{fixture,value}};
            ScriptFieldHistory.beforeInvoke(invoke,setter,nested);invoke.invoke(setter,nested);
            assertSame(value,fixture.actualTeam);
        }
        assertEquals(initial+6,count("team_script_field_write"));
        Field number=FieldHistoryFixture.class.getField("count");
        Method setInt=Field.class.getMethod("setInt",Object.class,int.class);
        ScriptFieldHistory.beforeInvoke(setInt,number,new Object[]{fixture,7});
        setInt.invoke(number,fixture,7);assertEquals(7,fixture.count);
        ScriptFieldHistory.beforeInvoke(setter,number,new Object[]{fixture,"invalid"});
        assertThrows(InvocationTargetException.class,()->setter.invoke(number,fixture,"invalid"));
        assertEquals(7,fixture.count);
        Field singleton=FieldHistoryFixture.class.getField("INSTANCE");
        ScriptFieldHistory.beforeSet(singleton);singleton.set(null,fixture);
        ScriptFieldHistory.beforeSet(singleton);singleton.set(null,null);
        assertEquals(initial+10,count("team_script_field_write"));
        Field other=ScriptFieldHistoryChecks.class.getField("unrelated");
        ScriptFieldHistory.beforeSet(other);
        ScriptFieldHistory.beforeInvoke(setter,other,new Object[]{null,null});
        ScriptFieldHistory.beforeInvoke(Field.class.getMethod("get",Object.class),field,new Object[]{fixture});
        ScriptFieldHistory.beforeInvoke(invoke,null,null);
        assertEquals(initial+10,count("team_script_field_write"));
        Object receiver=field;Object[] args={fixture,null};Method method=setter;
        for(int i=0;i<17;i++) { args=new Object[]{receiver,args};receiver=method;method=invoke; }
        long overflows=count("script_reflection_overflow");
        ScriptFieldHistory.beforeInvoke(method,receiver,args);
        assertEquals(overflows+1,count("script_reflection_overflow"));
        assertSame(fixture,fixture.actualTeam);
        handles(fixture);
    }
    private static void handles(FieldHistoryFixture fixture) throws Exception {
        long initial=count("script_handle_unresolved");
        long fields=count("team_script_field_write");
        var lookup=MethodHandles.lookup();
        var setter=lookup.unreflectSetter(FieldHistoryFixture.class.getField("actualTeam")).bindTo(fixture);
        Method call=MethodHandle.class.getMethod("invokeWithArguments",List.class);
        for(Object value:new Object[]{null,fixture}) {
            Object[] args={Arrays.asList(value)};
            ScriptFieldHistory.beforeInvoke(call,setter,args);call.invoke(setter,args);
            assertSame(value,fixture.actualTeam);
        }
        assertEquals(initial+2,count("script_handle_unresolved"));
        // Getter targets are also unresolved; never call these observed writes.
        var getter=lookup.unreflectGetter(FieldHistoryFixture.class.getField("actualTeam")).bindTo(fixture);
        ScriptFieldHistory.beforeInvoke(call,getter,new Object[]{List.of()});
        assertSame(fixture,call.invoke(getter,List.of()));
        Method invoke=Method.class.getMethod("invoke",Object.class,Object[].class);
        Object[] nested={setter,new Object[]{List.of(fixture)}};
        ScriptFieldHistory.beforeInvoke(invoke,call,nested);invoke.invoke(call,nested);
        var integer=lookup.unreflectSetter(FieldHistoryFixture.class.getField("count")).bindTo(fixture);
        ScriptFieldHistory.beforeInvoke(call,integer,new Object[]{List.of("invalid")});
        assertThrows(InvocationTargetException.class,()->call.invoke(integer,List.of("invalid")));
        assertEquals(initial+5,count("script_handle_unresolved"));
        var variable=lookup.findVarHandle(FieldHistoryFixture.class,"count",int.class);
        ScriptFieldHistory.beforeInvoke(VarHandle.class.getMethod("set",Object[].class),variable,null);
        variable.set(fixture,8);
        ScriptFieldHistory.beforeInvoke(VarHandle.class.getMethod("get",Object[].class),variable,null);
        assertEquals(8,(int)variable.get(fixture));
        ScriptFieldHistory.beforeInvoke(VarHandle.class.getMethod("compareAndSet",Object[].class),variable,null);
        assertFalse(variable.compareAndSet(fixture,99,100));
        var converted=variable.toMethodHandle(VarHandle.AccessMode.SET).bindTo(fixture);
        ScriptFieldHistory.beforeInvoke(call,converted,new Object[]{List.of(7)});
        call.invoke(converted,List.of(7));assertEquals(7,fixture.count);
        assertEquals(initial+9,count("script_handle_unresolved"));
        ScriptFieldHistory.beforeInvoke(MethodHandle.class.getMethod("type"),setter,null);
        ScriptFieldHistory.beforeInvoke(VarHandle.class.getMethod("coordinateTypes"),variable,null);
        assertEquals(initial+9,count("script_handle_unresolved"));
        assertEquals(fields,count("team_script_field_write"));
    }
}
