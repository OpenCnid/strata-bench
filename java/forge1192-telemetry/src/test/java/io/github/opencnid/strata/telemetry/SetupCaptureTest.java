package io.github.opencnid.strata.telemetry;

import static org.junit.jupiter.api.Assertions.*;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import org.junit.jupiter.api.Test;

class SetupCaptureTest {
    @Test void modeFlagsAreObservedRatherThanInferredFromOneString() {
        var value=SetupCapture.mode(Map.of("packmode","expert","isExpertMode",false,"isNormalMode",true),2,3);
        assertEquals("observed",value.get("status").getAsString());
        assertFalse(value.get("is_expert").getAsBoolean());
        assertEquals(2,value.get("startup_errors").getAsInt());
        assertEquals(3,value.get("server_errors").getAsInt());
    }
    @Test void absentWrongTypeAndUnknownModeRemainUnavailable() {
        for(var map: java.util.List.of(Map.of(),Map.of("packmode","expert","isExpertMode","true","isNormalMode",false),
            Map.of("packmode","other","isExpertMode",true,"isNormalMode",false)))
            assertEquals("unavailable",SetupCapture.mode(map,0,0).get("status").getAsString());
    }
    @Test void teamProjectionPreservesRankAndSortedBoundedMembers() {
        var a=UUID.fromString("00000000-0000-0000-0000-000000000001");
        var b=UUID.fromString("00000000-0000-0000-0000-000000000002");
        var value=SetupCapture.teamProjection(b,"PARTY",Set.of(b,a),"INVITED");
        assertEquals(a.toString(),value.getAsJsonArray("member_ids").get(0).getAsString());
        assertEquals("INVITED",value.get("actor_rank").getAsString());
        var many=new HashSet<UUID>();for(int i=0;i<129;i++)many.add(new UUID(0,i));
        assertEquals("unavailable",SetupCapture.teamProjection(b,"PARTY",many,"OWNER").get("status").getAsString());
    }
}
