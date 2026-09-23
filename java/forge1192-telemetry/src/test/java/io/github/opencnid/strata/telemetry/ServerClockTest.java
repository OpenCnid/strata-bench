package io.github.opencnid.strata.telemetry;

import static org.junit.jupiter.api.Assertions.*;
import java.util.UUID;
import java.util.concurrent.atomic.AtomicLong;
import org.junit.jupiter.api.Test;

class ServerClockTest {
    private static final UUID PLAYER = UUID.fromString("11111111-1111-1111-1111-111111111111");

    @Test void includesStartupTailIdleAndActualPlayerEventsWithoutInventingTicks() {
        var time = new AtomicLong(100);
        var clock = new ServerClock(time::get);
        time.set(200); clock.startTick();
        time.set(210); clock.avatarTick(PLAYER);
        time.set(220); clock.endTick();
        // A disconnected interval is still wall time; no avatar event is invented.
        time.set(300); clock.startTick(); time.set(320); clock.endTick();
        time.set(400); clock.startTick(); clock.avatarTick(PLAYER); time.set(410); clock.endTick();
        time.set(500); var value = clock.stop();
        assertEquals(400, value.get("elapsed_wall_ns").getAsLong());
        assertEquals(3, value.get("completed_server_ticks").getAsLong());
        assertEquals(50, value.get("observed_tick_work_ns").getAsLong());
        assertEquals(2, value.getAsJsonObject("avatar_tick_events").get(PLAYER.toString()).getAsLong());
        assertThrows(IllegalStateException.class, clock::stop);
    }

    @Test void zeroTickAndSignedNanoTimeWrapAreSupported() {
        var time = new AtomicLong(Long.MAX_VALUE - 10);
        var clock = new ServerClock(time::get);
        time.addAndGet(20);
        var value = clock.stop();
        assertEquals(20, value.get("elapsed_wall_ns").getAsLong());
        assertEquals(0, value.get("completed_server_ticks").getAsLong());
        assertEquals(0, value.getAsJsonObject("avatar_tick_events").size());
    }

    @Test void missingStartAndIncompleteTicksCannotClose() {
        var clock = new ServerClock(() -> 0);
        assertThrows(IllegalStateException.class, clock::endTick);
        assertThrows(IllegalStateException.class, clock::stop);
        var open = new ServerClock(() -> 0); open.startTick();
        assertThrows(IllegalStateException.class, open::stop);
    }

    @Test void duplicateServerOrAvatarCallbacksPermanentlyInvalidateTheClock() {
        var clock = new ServerClock(() -> 0); clock.startTick();
        assertThrows(IllegalStateException.class, clock::startTick);
        assertThrows(IllegalStateException.class, clock::endTick);
        var duplicate = new ServerClock(() -> 0); duplicate.startTick(); duplicate.avatarTick(PLAYER);
        assertThrows(IllegalStateException.class, () -> duplicate.avatarTick(PLAYER));
        assertThrows(IllegalStateException.class, duplicate::stop);
    }

    @Test void avatarOutsideServerTickAndPostStopEventsReject() {
        var clock = new ServerClock(() -> 0);
        assertThrows(IllegalStateException.class, () -> clock.avatarTick(PLAYER));
        var closed = new ServerClock(() -> 0); closed.stop();
        assertThrows(IllegalStateException.class, closed::startTick);
    }

    @Test void clockRollbackIsSticky() {
        var time = new AtomicLong(100); var clock = new ServerClock(time::get);
        time.set(110); clock.startTick(); time.set(105);
        assertThrows(IllegalStateException.class, clock::endTick);
        time.set(200); assertThrows(IllegalStateException.class, clock::stop);
    }

    @Test void offThreadCallbackCannotProduceASuccessfulTerminalRecord() throws Exception {
        var clock = new ServerClock(() -> 0);
        var other = new Thread(() -> assertThrows(IllegalStateException.class, clock::startTick));
        other.start(); other.join(5000); assertFalse(other.isAlive());
        assertThrows(IllegalStateException.class, clock::stop);
    }

    @Test void boundedRosterCannotGrowSilently() {
        var clock = new ServerClock(() -> 0); clock.startTick();
        for (int i = 0; i < 64; i++) clock.avatarTick(new UUID(0, i));
        assertThrows(IllegalStateException.class, () -> clock.avatarTick(new UUID(0, 64)));
        assertThrows(IllegalStateException.class, clock::stop);
    }
}
