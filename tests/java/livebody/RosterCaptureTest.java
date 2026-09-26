package io.github.opencnid.strata.livebody;

import java.util.*;
import java.util.concurrent.atomic.AtomicReference;

/** Synthetic lifecycle/identity cases only. */
public final class RosterCaptureTest {
    interface Attempt { void run() throws Exception; }
    static void require(boolean value) { if (!value) throw new AssertionError(); }
    static void refuses(Attempt attempt) throws Exception {
        try { attempt.run(); } catch (IllegalStateException expected) { return; }
        throw new AssertionError("invalid roster accepted");
    }
    public static void main(String[] args) throws Exception {
        Object server = new Object(), first = new Object(), second = new Object();
        UUID a = new UUID(0, 1), b = new UUID(0, 2);
        List<UUID> ids = List.of(a, b);
        RosterCapture roster = new RosterCapture(server, ids);
        roster.start(server); roster.avatar(server, a, first); require(roster.end(server).isEmpty());
        roster.start(server); roster.avatar(server, b, second); require(roster.end(server).isEmpty());
        roster.start(server); roster.avatar(server, a, first); roster.avatar(server, b, second);
        require(roster.end(server).equals(Map.of(a, first, b, second)) && roster.tick() == 3);
        roster.committed(server);
        roster.start(server); roster.avatar(server, a, new Object()); roster.avatar(server, b, new Object());
        require(roster.end(server).isEmpty()); roster.stop(server);
        refuses(() -> roster.start(server));
        for (int mode = 0; mode < 10; mode++) {
            RosterCapture invalid = new RosterCapture(server, ids);
            switch (mode) {
                case 0 -> refuses(() -> invalid.end(server));
                case 1 -> { invalid.start(server); refuses(() -> invalid.start(server)); }
                case 2 -> { invalid.start(server); invalid.avatar(server, a, first);
                    refuses(() -> invalid.avatar(server, a, first)); }
                case 3 -> { invalid.start(server); refuses(() -> invalid.avatar(server, new UUID(0, 3), first)); }
                case 4 -> refuses(() -> invalid.start(new Object()));
                case 5 -> refuses(() -> invalid.stop(server));
                case 6 -> { invalid.start(server); invalid.avatar(server, a, first); invalid.end(server);
                    refuses(() -> invalid.committed(server)); }
                case 7 -> { invalid.start(server); invalid.avatar(server, a, first); invalid.end(server);
                    invalid.start(server); refuses(() -> invalid.avatar(server, a, second)); }
                case 8 -> {
                    AtomicReference<Throwable> caught = new AtomicReference<>();
                    Thread thread = new Thread(() -> { try { invalid.start(server); }
                        catch (Throwable error) { caught.set(error); } });
                    thread.start(); thread.join(); require(caught.get() instanceof IllegalStateException);
                }
                case 9 -> { invalid.start(server); refuses(() -> invalid.avatar(server, null, first)); }
            }
            refuses(() -> invalid.start(server)); // Every invalid callback poisons the attempt.
        }
        refuses(() -> new RosterCapture(server, List.of()));
        refuses(() -> new RosterCapture(server, List.of(a, a)));
        List<UUID> oversized = new ArrayList<>();
        for (int i = 0; i < 65; i++) oversized.add(new UUID(0, i));
        refuses(() -> new RosterCapture(server, oversized));
        System.out.println("roster-callback-cases-pass");
    }
}
