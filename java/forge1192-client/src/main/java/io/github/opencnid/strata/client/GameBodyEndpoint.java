package io.github.opencnid.strata.client;

import java.io.IOException;
import java.net.Inet6Address;
import java.net.InetSocketAddress;
import java.net.SocketAddress;

/** Private identity input; native startup has no saved ServerData entry. */
final class GameBodyEndpoint {
    static final String POLICY = "server-metadata-or-resolved-tcp/1";
    private GameBodyEndpoint() {}
    static String endpoint(String metadata, SocketAddress remote) throws IOException {
        if (metadata != null) {
            if (metadata.isEmpty() || metadata.length() > 4096 || metadata.indexOf('\n') >= 0
                    || metadata.indexOf('\r') >= 0 || metadata.indexOf('\0') >= 0)
                throw new IOException("GAME_SERVER_IDENTITY_UNAVAILABLE");
            return metadata; // Preserve existing menu-joined body identities.
        }
        if (!(remote instanceof InetSocketAddress tcp) || tcp.isUnresolved()
                || tcp.getPort() < 1 || tcp.getPort() > 65535)
            throw new IOException("GAME_SERVER_IDENTITY_UNAVAILABLE");
        String address = tcp.getAddress().getHostAddress(); // Numeric; no name lookup.
        if (tcp.getAddress() instanceof Inet6Address) address = "[" + address + "]";
        return address + ":" + tcp.getPort();
    }
}
