package io.github.opencnid.strata.client;

import java.io.IOException;
import java.util.HashSet;
import java.util.Set;

/** Session-local software key state; never overrides another window or thread. */
final class KeyPollingState {
    private final long window;
    private final Thread owner = Thread.currentThread();
    private final Set<Integer> down = new HashSet<>();
    private boolean closed;
    private long polls;
    KeyPollingState(long window) { this.window = window; }
    Boolean polled(long target, int key) {
        if (owner != Thread.currentThread() || window != target || closed) return null;
        polls++; return down.contains(key);
    }
    long polls() { return polls; }
    void event(int key, boolean pressed) throws IOException {
        requireOwner();
        if (closed) throw new IOException("SETTINGS_INPUT_CLOSED");
        if (pressed) down.add(key); else down.remove(key);
    }
    void clear() throws IOException { requireOwner(); down.clear(); }
    void close() throws IOException { clear(); closed = true; }
    private void requireOwner() throws IOException {
        if (owner != Thread.currentThread()) throw new IOException("CLIENT_THREAD_REQUIRED");
    }
}
