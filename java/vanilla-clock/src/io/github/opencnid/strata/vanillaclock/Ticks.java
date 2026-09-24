package io.github.opencnid.strata.vanillaclock;

import java.util.*;
import java.util.function.LongSupplier;

/** Ordered, monotonic actual callbacks. Unknown/partial work never becomes a tick. */
public final class Ticks {
    private final Thread owner = Thread.currentThread();
    private final LongSupplier clock;
    private final long origin;
    private final Map<UUID,Long> avatars = new TreeMap<>();
    private final Set<UUID> seen = new HashSet<>();
    private final List<Long> durations = new ArrayList<>();
    private long previous, start, ticks, work, sampledAt, sampledTicks, sampledWork;
    private Long first, last;
    private boolean inTick, closed, failed;
    public Ticks(LongSupplier clock) { this.clock = clock; origin = clock.getAsLong(); }
    private void require(boolean condition) {
        if (!condition) { failed = true; throw new IllegalStateException("VANILLA_CLOCK_INVALID"); }
    }
    private long now() {
        require(!failed && !closed && owner == Thread.currentThread());
        long n = clock.getAsLong() - origin;
        require(n >= previous); previous = n; return n;
    }
    public void startTick() {
        long n = now(); require(!inTick);
        if (first == null) first = n;
        start = n; seen.clear(); inTick = true;
    }
    public void avatar(UUID id) {
        now(); require(inTick && id != null && seen.add(id));
        require(avatars.containsKey(id) || avatars.size() < 64);
        avatars.put(id, Math.addExact(avatars.getOrDefault(id, 0L), 1));
    }
    public boolean endTick() {
        long n = now(); require(inTick && durations.size() < 4096);
        ticks = Math.addExact(ticks, 1); work = Math.addExact(work, n - start);
        durations.add(n - start); last = n; inTick = false;
        return n - sampledAt >= 1_000_000_000L;
    }
    public String sample(boolean terminal) {
        long n = now(); require(!inTick && work <= n);
        var body = new StringBuilder("{\"schema\":\"strata/VanillaClockSample/1\",\"terminal\":").append(terminal)
            .append(",\"run_elapsed_ns\":").append(n)
            .append(",\"window_start_ns\":").append(sampledAt)
            .append(",\"window_end_ns\":").append(n)
            .append(",\"first_tick_ns\":").append(first).append(",\"last_tick_ns\":").append(last)
            .append(",\"completed_server_ticks\":").append(ticks)
            .append(",\"observed_tick_work_ns\":").append(work)
            .append(",\"window_ticks\":").append(ticks - sampledTicks)
            .append(",\"window_work_ns\":").append(work - sampledWork)
            .append(",\"tick_work_ns\":").append(durations)
            .append(",\"avatar_tick_events\":{");
        String separator = "";
        for (var entry : avatars.entrySet()) {
            body.append(separator).append('"').append(entry.getKey()).append("\":").append(entry.getValue());
            separator = ",";
        }
        body.append("}}");
        sampledAt = n; sampledTicks = ticks; sampledWork = work; durations.clear();
        closed = terminal;
        return body.toString();
    }
}
