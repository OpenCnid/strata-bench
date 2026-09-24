package io.github.opencnid.strata.telemetry;

import static org.junit.jupiter.api.Assertions.*;
import java.util.HashMap;

/** Synthetic owner hierarchy; actual FTB bytecode and live hooks are separate evidence. */
final class TeamRankOwnershipChecks {
    static class Base {}
    static class ServerTeam extends Base {}
    static class PlayerTeam extends ServerTeam {}
    static class ClientCopy extends Base {}
    static class UnknownClientSubclass extends ClientCopy {}
    private static long count() {
        return SetupHistory.capture("startup",null).getAsJsonObject("attempts").get("team_map_write").getAsLong();
    }
    @SuppressWarnings("unchecked")
    static void check() {
        var server=(HashMap<String,String>)TeamMapSupport.rankMap(new PlayerTeam(),ServerTeam.class,ClientCopy.class);
        var client=(HashMap<String,String>)TeamMapSupport.rankMap(new ClientCopy(),ServerTeam.class,ClientCopy.class);
        assertInstanceOf(ObservedTeamHashMap.class,server);
        assertEquals(HashMap.class,client.getClass());
        long before=count();
        server.put("player","member");
        assertEquals(before+1,count());
        // Exact ClientTeam(Team) copy operation found in the pinned FTB bytecode.
        client.putAll(server);
        assertEquals(server,client);assertEquals(before+1,count());
        client.put("player","owner");client.clear();
        assertEquals("member",server.get("player"));assertEquals(before+1,count());
        var alias=server.entrySet().iterator().next();
        alias.setValue("owner");alias.setValue("member");
        server.putIfAbsent("player","owner"); // Failed/no-op attempts remain sticky.
        assertEquals(before+4,count());
        assertThrows(IllegalStateException.class,()->TeamMapSupport.rankMap(new Base(),ServerTeam.class,ClientCopy.class));
        assertThrows(IllegalStateException.class,()->TeamMapSupport.rankMap(new UnknownClientSubclass(),ServerTeam.class,ClientCopy.class));
        assertThrows(IllegalStateException.class,()->TeamMapSupport.rankMap(null,ServerTeam.class,ClientCopy.class));
        assertThrows(IllegalStateException.class,()->TeamMapSupport.rankMap(new Object())); // No FTB runtime on this classpath.
    }
    private TeamRankOwnershipChecks() {}
}
