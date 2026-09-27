package io.github.opencnid.strata.client;

import java.io.IOException;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class KeyPollingStateTest {
    @Test void ownWindowPollsPressedAndReleasedKeys() throws Exception {
        var state = new KeyPollingState(100);
        assertEquals(false, state.polled(100, 65)); state.event(65, true);
        assertEquals(true, state.polled(100, 65)); assertEquals(false, state.polled(100, 66));
        state.event(65, false); assertEquals(false, state.polled(100, 65));
        assertEquals(4, state.polls());
    }
    @Test void otherWindowRetainsNativePolling() throws Exception {
        var state = new KeyPollingState(100); state.event(65, true);
        assertNull(state.polled(101, 65)); assertEquals(0, state.polls());
    }
    @Test void otherThreadCannotReadOverrideOrMutateOwnerState() throws Exception {
        var state = new KeyPollingState(100); state.event(65, true);
        var result = new AtomicReference<Throwable>();
        var thread = new Thread(() -> {
            try {
                assertNull(state.polled(100, 65));
                assertThrows(IOException.class, () -> state.event(65, false));
                assertThrows(IOException.class, state::clear); assertThrows(IOException.class, state::close);
            } catch (Throwable error) { result.set(error); }
        });
        thread.start(); thread.join(2000); assertFalse(thread.isAlive()); assertNull(result.get());
        assertEquals(true, state.polled(100, 65));
    }
    @Test void clearRetainsAllUpViewUntilClose() throws Exception {
        var state = new KeyPollingState(100); state.event(340, true); state.event(65, true);
        state.clear(); assertEquals(false, state.polled(100, 340)); assertEquals(false, state.polled(100, 65));
        state.close(); assertNull(state.polled(100, 65));
        assertThrows(IOException.class, () -> state.event(65, true));
    }
    @Test void IndependentStateCannotInheritAnotherSessionsKeys() throws Exception {
        var first = new KeyPollingState(100); first.event(65, true); first.close();
        var next = new KeyPollingState(100); assertEquals(false, next.polled(100, 65));
    }
}
