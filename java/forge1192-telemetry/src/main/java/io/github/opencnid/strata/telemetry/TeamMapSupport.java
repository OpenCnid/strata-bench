package io.github.opencnid.strata.telemetry;

import java.util.Map;

/** Read existing fields without warming the lazily built name cache. */
public final class TeamMapSupport {
    public interface RankSource { Map<?,?> strata$rankMap(); }
    public interface CacheSource { Map<?,?> strata$nameCache(); }
    static boolean verified() {
        try {
            var type=Class.forName("dev.ftb.mods.ftbteams.data.TeamManager");
            var manager=type.getField("INSTANCE").get(null);
            if(!(manager instanceof CacheSource source)) return false;
            var players=type.getMethod("getKnownPlayers").invoke(manager);
            var teams=type.getMethod("getTeamMap").invoke(manager);
            if(!(players instanceof ObservedTeamLinkedMap<?,?> known)
                || !(teams instanceof ObservedTeamLinkedMap<?,?> all)
                || known.size()>128 || all.size()>128) return false;
            for(var map:java.util.List.of(known,all)) {
                for(var team:map.values()) {
                    if(!(team instanceof RankSource ranks)
                        || !(ranks.strata$rankMap() instanceof ObservedTeamHashMap<?,?> observed)
                        || !observed.armed()) return false;
                }
            }
            var cache=source.strata$nameCache();
            return cache==null || cache instanceof ObservedTeamHashMap<?,?> observed && observed.armed();
        } catch(ReflectiveOperationException|RuntimeException error) { return false; }
    }
    private TeamMapSupport() {}
}
