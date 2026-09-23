package io.github.opencnid.strata.telemetry;

import static org.junit.jupiter.api.Assertions.*;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.function.Consumer;
import org.junit.jupiter.api.Test;

class ObservedGlobalMapTest {
    private long count() { return SetupHistory.capture("startup",null).getAsJsonObject("attempts").get("global_mode_write").getAsLong(); }
    private long teams() { return SetupHistory.capture("startup",null).getAsJsonObject("attempts").get("team_map_write").getAsLong(); }
    private Map.Entry<String,Object> entry(Map<String,Object> map) {
        return map.entrySet().stream().filter(e->e.getKey().equals("packmode")).findFirst().orElseThrow();
    }
    @Test void liveAliasesAndAllPublicMutationRoutesAreStickyWithHashMapResults() throws Exception {
        SetupHistory.activate();
        try {
            ScriptFieldHistoryChecks.check();
            TeamRankOwnershipChecks.check();
            List<Consumer<Map<String,Object>>> writes=List.of(
                m->m.put("packmode","normal"), m->m.putIfAbsent("packmode","normal"),
                m->m.putAll(Map.of("packmode","normal")), m->m.remove("packmode"),
                m->m.remove("packmode","expert"), m->m.replace("packmode","normal"),
                m->m.replace("packmode","expert","normal"), m->m.computeIfAbsent("packmode",k->"normal"),
                m->m.computeIfPresent("packmode",(k,v)->"normal"), m->m.compute("packmode",(k,v)->null),
                m->m.merge("packmode","normal",(a,b)->b), m->m.replaceAll((k,v)->v), Map::clear,
                m->entry(m).setValue("normal"), m->m.entrySet().remove(Map.entry("packmode","expert")),
                m->m.entrySet().removeIf(e->e.getKey().equals("packmode")),
                m->m.keySet().remove("packmode"), m->m.keySet().retainAll(List.of("unrelated")),
                m->m.values().remove("expert"), m->m.values().removeAll(List.of("expert")),
                m->m.values().clear(), m->m.entrySet().toArray(new Map.Entry[0])[0].setValue("normal")
            );
            for(var operation:writes) {
                var observed=new ObservedGlobalMap(); var plain=new HashMap<String,Object>();
                // One entry makes array selection deterministic, not dependent on hash order.
                observed.put("packmode","expert"); plain.put("packmode","expert");
                long before=count(); operation.accept(observed); operation.accept(plain);
                assertTrue(count()>before); assertEquals(plain,observed); assertEquals(plain.hashCode(),observed.hashCode());
            }
            for(boolean linked:new boolean[]{false,true}) {
                for(var operation:writes) {
                    Map<String,Object> observed=linked?new ObservedTeamLinkedMap<>():new ObservedTeamHashMap<>(true);
                    Map<String,Object> plain=linked?new java.util.LinkedHashMap<>():new HashMap<>();
                    observed.put("packmode","expert");plain.put("packmode","expert");
                    long before=teams();operation.accept(observed);operation.accept(plain);
                    assertTrue(teams()>before);assertEquals(plain,observed);
                    assertEquals(List.copyOf(plain.keySet()),List.copyOf(observed.keySet()));
                }
            }
            var ordered=new ObservedTeamLinkedMap<String,Object>();
            var expected=new java.util.LinkedHashMap<String,Object>();
            for(String key:List.of("z","a","m","b")) { ordered.put(key,key);expected.put(key,key); }
            ordered.remove("a");expected.remove("a");ordered.put("a",2);expected.put("a",2);
            assertEquals(List.copyOf(expected.keySet()),List.copyOf(ordered.keySet()));
            long beforeTeams=teams();
            ((java.util.LinkedHashMap<String,Object>)ordered.clone()).clear();
            assertEquals(beforeTeams,teams());
            var cached=new ObservedTeamHashMap<String,Object>(false);
            cached.put("team","value");assertFalse(cached.armed());assertEquals(beforeTeams,teams());
            cached.arm();cached.arm();assertTrue(cached.armed());
            var retained=cached.entrySet().iterator().next();
            retained.setValue("temporary");retained.setValue("value");
            assertEquals(beforeTeams+2,teams());
            var map=new ObservedGlobalMap();map.put("packmode","expert");
            var alias=entry(map); long before=count();
            alias.setValue("normal");alias.setValue("expert");
            assertEquals(2,count()-before);assertEquals("expert",map.get("packmode"));
            before=count();
            map.put("unrelated",1);map.compute("unrelated",(k,v)->2);map.keySet().remove("unrelated");
            map.put(null,null);map.remove(null);map.get("packmode");map.forEach((k,v)->{});
            map.entrySet().toArray();map.keySet().toArray();map.values().toArray();
            ((HashMap<String,Object>)map.clone()).put("packmode","normal");
            assertEquals(before,count());
            var thread=new Thread(()->map.put("isExpertMode",false));thread.start();thread.join(5000);
            assertFalse(thread.isAlive());
            assertEquals(1,SetupHistory.capture("stop",null).get("off_thread_attempts").getAsInt());
        } finally { SetupHistory.close(); }
    }
}
