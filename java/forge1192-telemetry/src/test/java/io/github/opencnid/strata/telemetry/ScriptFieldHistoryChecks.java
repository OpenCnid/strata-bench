package io.github.opencnid.strata.telemetry;

import static org.junit.jupiter.api.Assertions.*;
import java.lang.reflect.Field;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
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
    }
}
