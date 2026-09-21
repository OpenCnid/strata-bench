package io.github.opencnid.strata.telemetry;

import static org.junit.jupiter.api.Assertions.*;
import java.util.ArrayList;
import org.junit.jupiter.api.Test;

class SetupHistoryTest {
    @Test void stopRequiresExactPriorAttemptSameSourceSameThreadAndSingleConsumption() {
        var history = new SetupHistory.Monitor(Thread.currentThread(), 100);
        var source = new Object();
        history.stopping(source, Thread.currentThread());
        history.command(source, false, Thread.currentThread());
        history.stopping(source, Thread.currentThread());
        history.command(source, true, Thread.currentThread());
        history.stopping(new Object(), Thread.currentThread());
        history.command(source, true, Thread.currentThread());
        history.stopping(source, new Thread());
        assertEquals(0, history.capture("stop", null).getAsJsonObject("attempts").get("native_stop_command").getAsInt());
        history.command(source, true, Thread.currentThread());
        history.stopping(source, Thread.currentThread());
        history.stopping(source, Thread.currentThread());
        var counts = history.capture("stop", null).getAsJsonObject("attempts");
        assertEquals(4, counts.get("command_attempt").getAsInt());
        assertEquals(1, counts.get("native_stop_command").getAsInt());
    }
    @Test void returnedSnapshotsCannotEraseRevertedChanges() {
        var history = new SetupHistory.Monitor(Thread.currentThread(), 100);
        var initial = history.capture("startup", null);
        history.attempt("actor_mode_change", Thread.currentThread());
        history.attempt("actor_mode_change", Thread.currentThread());
        var after = history.capture("craft_begin", "transaction");
        assertEquals(0, initial.getAsJsonObject("attempts").get("actor_mode_change").getAsLong());
        assertEquals(2, after.getAsJsonObject("attempts").get("actor_mode_change").getAsLong());
        after.getAsJsonObject("attempts").addProperty("actor_mode_change", 0);
        assertEquals(2, history.capture("stop", null).getAsJsonObject("attempts").get("actor_mode_change").getAsLong());
    }
    @Test void allRoutesAndOverflowStayVisibleWithoutUnboundedStorage() {
        var history = new SetupHistory.Monitor(Thread.currentThread(), 2);
        for (String route : SetupHistory.ROUTES)
            for (int i = 0; i < 3; i++) history.attempt(route, Thread.currentThread());
        var snapshot = history.capture("stop", null);
        assertTrue(snapshot.get("overflowed").getAsBoolean());
        assertEquals(SetupHistory.ROUTES.length, snapshot.getAsJsonObject("attempts").size());
        for (String route : SetupHistory.ROUTES)
            assertEquals(2, snapshot.getAsJsonObject("attempts").get(route).getAsLong());
        assertThrows(IllegalArgumentException.class, () -> history.attempt("guessed", Thread.currentThread()));
        assertTrue(history.capture("stop", null).get("overflowed").getAsBoolean());
    }
    @Test void concurrentAttemptsAreStickyAndMarkedOffThread() throws Exception {
        var history = new SetupHistory.Monitor(Thread.currentThread(), 100_000);
        var threads = new ArrayList<Thread>();
        for (int i = 0; i < 8; i++) {
            var thread = new Thread(() -> {
                for (int n = 0; n < 1000; n++) history.attempt("party_change", Thread.currentThread());
            });
            threads.add(thread); thread.start();
        }
        for (var thread : threads) thread.join(5000);
        assertTrue(threads.stream().noneMatch(Thread::isAlive));
        var snapshot = history.capture("stop", null);
        assertEquals(8000, snapshot.get("off_thread_attempts").getAsLong());
        assertEquals(8000, snapshot.getAsJsonObject("attempts").get("party_change").getAsLong());
        assertFalse(snapshot.get("overflowed").getAsBoolean());
    }
}
