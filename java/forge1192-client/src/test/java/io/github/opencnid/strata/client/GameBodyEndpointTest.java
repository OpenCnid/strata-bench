package io.github.opencnid.strata.client;

import java.io.IOException;
import java.net.InetAddress;
import java.net.InetSocketAddress;
import java.net.UnixDomainSocketAddress;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class GameBodyEndpointTest {
    @Test void menuJoinedIdentityIsPreservedWithoutResolvingMetadata() throws Exception {
        assertEquals("unresolved.example:25566", GameBodyEndpoint.endpoint("unresolved.example:25566", null));
    }
    @Test void nativeStartupUsesActualIpv4PeerAndPort() throws Exception {
        var ip = InetAddress.getByAddress(new byte[]{127,0,0,1});
        assertEquals("127.0.0.1:25566", GameBodyEndpoint.endpoint(null, new InetSocketAddress(ip,25566)));
        assertNotEquals(GameBodyEndpoint.endpoint(null, new InetSocketAddress(ip,25565)),
            GameBodyEndpoint.endpoint(null, new InetSocketAddress(ip,25566)));
    }
    @Test void ipv6EndpointRetainsUnambiguousAddressAndPort() throws Exception {
        byte[] address = new byte[16]; address[15]=1;
        assertEquals("[0:0:0:0:0:0:0:1]:25566",
            GameBodyEndpoint.endpoint(null,new InetSocketAddress(InetAddress.getByAddress(address),25566)));
    }
    @Test void unresolvedAbsentAndNonTcpEndpointsCannotAuthorizeBody() {
        for (var remote : new java.net.SocketAddress[]{null,
                InetSocketAddress.createUnresolved("unresolved.example",25566),
                UnixDomainSocketAddress.of("local.socket"),new InetSocketAddress(0)}) {
            assertEquals("GAME_SERVER_IDENTITY_UNAVAILABLE",
                assertThrows(IOException.class,()->GameBodyEndpoint.endpoint(null,remote)).getMessage());
        }
    }
    @Test void corruptMetadataIsRejectedWithoutFallingBackToPeer() throws Exception {
        var peer = new InetSocketAddress(InetAddress.getByAddress(new byte[]{127,0,0,1}),25566);
        for (String metadata : new String[]{"","host\nidentity","host\ridentity","host\0identity","x".repeat(4097)})
            assertThrows(IOException.class,()->GameBodyEndpoint.endpoint(metadata,peer));
    }
}
