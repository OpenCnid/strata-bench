package io.github.opencnid.strata.client;

import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;

/** Bounded ordinary keyboard or mouse gesture. Completion means released input, never verified effects. */
final class KeyInputSession implements GameActionLane.Motor {
    static final long MAX_HOLD_MS = 2000;
    enum Modifier {
        NONE(0, 0), SHIFT(340, 1), CONTROL(341, 2), ALT(342, 4);
        final int key, mask;
        Modifier(int key, int mask) { this.key = key; this.mask = mask; }
    }
    enum Device { KEYBOARD, MOUSE }
    record Request(int key, Modifier modifier, long holdMs, Device device) {
        Request(int key, Modifier modifier, long holdMs) { this(key, modifier, holdMs, Device.KEYBOARD); }
        void validate(Set<Integer> pool) throws IOException {
            if (device == null || modifier == null || holdMs < 1 || holdMs > MAX_HOLD_MS
                    || (device == Device.KEYBOARD ? key < 32 || key > 342 || key >= 340 && modifier != Modifier.NONE : key < 0 || key > 1)
                    || !pool.contains(key) || modifier != Modifier.NONE && !pool.contains(modifier.key)) {
                throw new IOException("SETTINGS_INPUT_UNSUPPORTED");
            }
        }
    }
    interface Port {
        void validate() throws IOException;
        long monotonicMillis();
        // The port updates its window's polled state BEFORE delivering each callback.
        void event(int key, boolean down, int modifiers) throws IOException;
        default void mouseEvent(int button, boolean down, int modifiers) throws IOException {
            throw new IOException("SETTINGS_INPUT_UNSUPPORTED");
        }
        void clear() throws IOException;
    }
    private final Port port;
    private final Request request;
    private final GameActionLane.Emitter emitter, safetyEmitter;
    private final List<Integer> held = new ArrayList<>();
    private final long started;
    private boolean closed;
    private boolean releaseConfirmed;
    private String failure;

    private KeyInputSession(Port port, Request request, GameActionLane.Emitter emitter,
            GameActionLane.Emitter safetyEmitter) {
        this.port = port; this.request = request; this.emitter = emitter; this.safetyEmitter = safetyEmitter;
        started = port.monotonicMillis();
    }
    static KeyInputSession start(Port port, Request request, Set<Integer> pool,
            GameActionLane.Emitter emitter, GameActionLane.Emitter safetyEmitter) throws IOException {
        request.validate(Set.copyOf(pool)); port.validate();
        KeyInputSession session = new KeyInputSession(port, request, emitter, safetyEmitter);
        try {
            if (request.modifier != Modifier.NONE) session.press(request.modifier.key);
            session.press(request.key);
            return session;
        } catch (IOException | RuntimeException | Error error) {
            try { session.cancel(); } catch (IOException | RuntimeException | Error cleanup) { error.addSuppressed(cleanup); }
            throw error;
        }
    }
    private void press(int key) throws IOException {
        emitter.invoke(() -> {
            // A throwing callback has an ambiguous effect and still needs release.
            held.add(key);
            int modifiers = request.modifier.mask;
            // Standalone vanilla sneak/sprint keys must carry their ordinary
            // modifier flag without pressing the same physical key twice.
            if (request.device == Device.KEYBOARD && request.key >= 340) modifiers = 1 << (request.key - 340);
            event(key, true, modifiers);
        });
    }
    private void event(int key, boolean pressed, int modifiers) throws IOException {
        if (request.device == Device.MOUSE && key == request.key) port.mouseEvent(key, pressed, modifiers);
        else port.event(key, pressed, modifiers);
    }
    boolean closed() { return closed; }
    com.google.gson.JsonObject releaseReceipt() throws IOException {
        if (!releaseConfirmed) throw new IOException("SETTINGS_INPUT_RELEASE_UNCONFIRMED");
        var value = new com.google.gson.JsonObject();
        value.addProperty("schema", "strata/NativeInputRelease/2");
        value.addProperty("device", request.device.name().toLowerCase(java.util.Locale.ROOT));
        value.addProperty("key", request.key);
        value.addProperty("modifier", request.modifier.name());
        var order = new com.google.gson.JsonArray(); order.add(request.key);
        if (request.modifier != Modifier.NONE) order.add(request.modifier.key);
        value.add("release_order", order);
        value.addProperty("callbacks_confirmed", true);
        value.addProperty("clear_confirmed", true);
        return value;
    }
    private static String failureCode(Throwable error) {
        return error instanceof IOException && error.getMessage() != null
            ? error.getMessage() : "SETTINGS_INPUT_FAILED";
    }

    void watchdog() throws IOException {
        if (closed) return;
        try {
            port.validate();
            long elapsed = port.monotonicMillis() - started;
            if (elapsed < 0) throw new IOException("SETTINGS_INPUT_CLOCK_INVALID");
            if (elapsed > MAX_HOLD_MS) throw new IOException("SETTINGS_INPUT_HOLD_TIMEOUT");
        } catch (IOException | RuntimeException | Error error) {
            failure = failureCode(error);
            try { release(); } catch (IOException | RuntimeException | Error cleanup) { error.addSuppressed(cleanup); }
            throw error;
        }
    }

    @Override public boolean tick(GameActionLane.Emitter next) throws IOException {
        if (failure != null) throw new IOException(failure);
        if (closed) return true;
        try {
            watchdog();
            long elapsed = port.monotonicMillis() - started;
            if (elapsed < request.holdMs) { next.invoke(() -> {}); return false; }
            release(); return true;
        } catch (IOException | RuntimeException | Error error) {
            failure = failureCode(error);
            try { release(); } catch (IOException | RuntimeException | Error cleanup) { error.addSuppressed(cleanup); }
            throw error;
        }
    }

    /** Safety cleanup attempts every release even if journaling or one callback fails. */
    void cancel() throws IOException {
        if (closed) return;
        failure = "SETTINGS_INPUT_CANCELLED";
        release();
    }
    private void release() throws IOException {
        if (closed) return;
        closed = true;
        Throwable primary = null;
        for (int index = held.size() - 1; index >= 0; index--) {
            int key = held.get(index);
            int modifiers = key == request.modifier.key ? 0 : request.modifier.mask;
            boolean[] invoked = {false};
            try {
                safetyEmitter.invoke(() -> { invoked[0] = true; event(key, false, modifiers); });
            } catch (IOException | RuntimeException | Error error) {
                if (primary == null) primary = error; else primary.addSuppressed(error);
                if (!invoked[0]) try { event(key, false, modifiers); }
                catch (IOException | RuntimeException | Error cleanup) { primary.addSuppressed(cleanup); }
            }
        }
        held.clear();
        boolean[] cleared = {false};
        try { safetyEmitter.invoke(() -> { cleared[0] = true; port.clear(); }); }
        catch (IOException | RuntimeException | Error error) {
            if (primary == null) primary = error; else primary.addSuppressed(error);
            if (!cleared[0]) try { port.clear(); }
            catch (IOException | RuntimeException | Error cleanup) { primary.addSuppressed(cleanup); }
        }
        if (primary != null) {
            failure = "SETTINGS_INPUT_RELEASE_UNCONFIRMED";
            throw new IOException(failure, primary);
        }
        releaseConfirmed = true;
    }
}
