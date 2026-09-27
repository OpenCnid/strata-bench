package io.github.opencnid.strata.livebody;

import java.util.*;

/** Single-thread callback state machine. No filesystem or gameplay authority. */
public final class RosterCapture {
    private final Thread owner = Thread.currentThread();
    private final Object server;
    private final Set<UUID> expected;
    private final Map<UUID,Object> seen = new TreeMap<>();
    private final Map<UUID,Object> identities = new HashMap<>();
    private boolean inTick, captured, stopped, failed;
    private long tick;

    public RosterCapture(Object server, Collection<UUID> roster) {
        this.server = Objects.requireNonNull(server);
        expected = Set.copyOf(roster);
        require(!expected.isEmpty() && expected.size() == roster.size() && expected.size() <= 64);
    }
    private void require(boolean value) {
        if (!value) { failed = true; throw new IllegalStateException("BODY_CALLBACK_SCOPE"); }
    }
    private void check(Object actual) {
        require(!failed && !stopped && owner == Thread.currentThread() && actual == server);
    }
    public void start(Object actual) {
        check(actual); require(!inTick && tick < 1_000_000);
        seen.clear(); inTick = true;
    }
    public void avatar(Object actual, UUID uuid, Object player) {
        check(actual);
        require(inTick && uuid != null && player != null);
        // The witness concerns initial state. A later legitimate respawn must
        // remain gameplay, not become an infrastructure failure or recapture.
        if (captured) return;
        require(expected.contains(uuid) && !seen.containsKey(uuid));
        Object prior = identities.putIfAbsent(uuid, player);
        require(prior == null || prior == player);
        seen.put(uuid, player);
    }
    /** Return exactly one immutable complete-roster capture opportunity. */
    public Map<UUID,Object> end(Object actual) {
        check(actual); require(inTick); inTick = false; tick++;
        return !captured && seen.keySet().equals(expected) ? Map.copyOf(seen) : Map.of();
    }
    public void committed(Object actual) {
        check(actual); require(!inTick && !captured && seen.keySet().equals(expected)); captured = true;
        identities.clear(); seen.clear();
    }
    public void stop(Object actual) {
        check(actual); require(!inTick && captured); stopped = true;
    }
    public long tick() { return tick; }
}
