package io.github.opencnid.strata.telemetry;

import com.google.gson.JsonObject;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import java.util.function.LongSupplier;

/** Private callback exposure, not admitted active time or an inferred 20 Hz clock. */
final class ServerClock {
    static final String POLICY = "server-event-monotonic-cumulative/1";
    private final Thread owner = Thread.currentThread();
    private final LongSupplier nanoTime;
    private final long origin;
    private final Map<UUID, Long> avatars = new HashMap<>();
    private final Set<UUID> tickAvatars = new HashSet<>();
    private long previous, tickStart, ticks, work;
    private boolean inTick, closed, failed;

    ServerClock() { this(System::nanoTime); }
    ServerClock(LongSupplier nanoTime) {
        this.nanoTime = nanoTime;
        origin = nanoTime.getAsLong();
    }

    private void require(boolean condition) {
        if (!condition) {
            failed = true;
            throw new IllegalStateException("TELEMETRY_CLOCK_INVALID");
        }
    }

    private long now() {
        require(!failed && !closed && Thread.currentThread() == owner);
        // nanoTime may be negative or wrap; subtract the process-local origin.
        long elapsed = nanoTime.getAsLong() - origin;
        require(elapsed >= previous);
        previous = elapsed;
        return elapsed;
    }

    synchronized void startTick() {
        long elapsed = now();
        require(!inTick);
        tickStart = elapsed;
        tickAvatars.clear();
        inTick = true;
    }

    synchronized void avatarTick(UUID uuid) {
        now();
        require(inTick && uuid != null && tickAvatars.add(uuid));
        require(avatars.containsKey(uuid) || avatars.size() < 64);
        avatars.put(uuid, Math.addExact(avatars.getOrDefault(uuid, 0L), 1));
    }

    synchronized void endTick() {
        long elapsed = now();
        require(inTick);
        ticks = Math.addExact(ticks, 1);
        work = Math.addExact(work, elapsed - tickStart);
        inTick = false;
    }

    synchronized JsonObject stop() {
        long elapsed = now();
        require(!inTick && work <= elapsed);
        closed = true;
        var result = new JsonObject();
        result.addProperty("policy", POLICY);
        result.addProperty("origin", "server_started_callback");
        result.addProperty("boundary", "server_stopped_callback");
        result.addProperty("elapsed_wall_ns", elapsed);
        result.addProperty("completed_server_ticks", ticks);
        result.addProperty("observed_tick_work_ns", work);
        var counts = new JsonObject();
        avatars.entrySet().stream().sorted(Map.Entry.comparingByKey())
            .forEach(entry -> counts.addProperty(entry.getKey().toString(), entry.getValue()));
        result.add("avatar_tick_events", counts);
        return result;
    }
}
