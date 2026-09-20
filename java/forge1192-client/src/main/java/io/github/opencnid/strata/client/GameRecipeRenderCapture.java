package io.github.opencnid.strata.client;

import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import java.util.function.LongSupplier;

/** Private render provenance only. Opaque layouts are never public observations. */
final class GameRecipeRenderCapture {
    static final int MAX_LAYOUTS = 32;
    static final long MAX_FRAME_NANOS = 100_000_000L, MAX_AGE_NANOS = 250_000_000L;
    record Key(Object screen, Object runtime, Object origin, int width, int height) {
        boolean valid() { return screen != null && runtime != null && origin != null
            && width > 0 && height > 0 && width <= 32768 && height <= 32768; }
        boolean same(Key other) { return other != null && screen == other.screen && runtime == other.runtime
            && origin == other.origin && width == other.width && height == other.height; }
    }
    private record Frame(Key key, List<Object> layouts, List<GameRecipeSlots.Layout> copies, List<GameRecipeHeaders.Label> headers,
                         List<GameRecipeControls.Control> controls, long finished) {}
    private final LongSupplier clock;
    private Key pending;
    private Object owner, iterator;
    private final ArrayList<Object> layouts = new ArrayList<>();
    private final ArrayList<GameRecipeSlots.Layout> copies = new ArrayList<>();
    private List<GameRecipeHeaders.Label> headers;
    private List<GameRecipeControls.Control> controls;
    private int copiedBytes = 2; // JSON array brackets; commas are charged per subsequent layout.
    private boolean started, ended, invalid, awaitingDraw, exhausted;
    private long began;
    private Frame completed;

    GameRecipeRenderCapture() { this(System::nanoTime); }
    GameRecipeRenderCapture(LongSupplier clock) { this.clock = clock; }

    void beginFrame(Key key) {
        clear();
        if (key == null || !key.valid()) return;
        pending = key; began = clock.getAsLong();
    }
    void beginLayouts(Object renderer) {
        if (pending == null) return;
        if (renderer == null || started) { invalidate(); return; }
        owner = renderer; started = true;
    }
    /** Observe only the result of JEI's existing loop predicate; never query or advance its iterator. */
    void layoutPredicate(Object renderer, Object currentIterator, boolean hasNext) {
        if (pending == null) return;
        if (invalid || !started || ended || renderer != owner || currentIterator == null || exhausted || awaitingDraw
                || iterator != null && iterator != currentIterator || hasNext && layouts.size() >= MAX_LAYOUTS) {
            invalidate(); return;
        }
        iterator = currentIterator;
        awaitingDraw = hasNext; exhausted = !hasNext;
    }
    void headers(List<GameRecipeHeaders.Label> value) throws IOException {
        if (pending == null || invalid || started || headers != null || value == null || value.size() != 2
                || value.stream().anyMatch(java.util.Objects::isNull)
                || !"category".equals(value.get(0).kind()) || !"page".equals(value.get(1).kind())) {
            invalidate(); throw new IOException("GAME_RECIPE_HEADER_INVALID");
        }
        try {
            for (var label : value) label.json();
            headers = List.copyOf(value);
        } catch (IOException | RuntimeException error) { invalidate(); throw error; }
    }
    void controls(List<GameRecipeControls.Control> value) throws IOException {
        if (pending == null || invalid || started || controls != null || value == null || value.size() != 4) {
            invalidate(); throw new IOException("GAME_RECIPE_CONTROLS_INVALID");
        }
        try {
            for (int i = 0; i < 4; i++) {
                var control = value.get(i);
                if (control == null || !GameRecipeControls.KINDS.get(i).equals(control.kind())) throw new IOException("GAME_RECIPE_CONTROLS_INVALID");
                control.json();
            }
            controls = List.copyOf(value);
        } catch (IOException | RuntimeException error) { invalidate(); throw error; }
    }
    void drawn(Object layout) {
        if (pending == null) return;
        if (invalid || !started || ended || !awaitingDraw || exhausted || layout == null || layouts.size() >= MAX_LAYOUTS) { invalidate(); return; }
        for (Object previous : layouts) if (previous == layout) { invalidate(); return; }
        layouts.add(layout); awaitingDraw = false;
    }
    void drawn(Object layout, GameRecipeSlots.Layout copy) throws IOException {
        if (pending == null) return;
        try {
            if (copy == null) throw new IOException("GAME_RECIPE_RENDER_UNAVAILABLE");
            int bytes = copy.json().toString().getBytes(java.nio.charset.StandardCharsets.UTF_8).length + (copies.isEmpty() ? 0 : 1);
            if (copiedBytes + bytes > 32768) throw new IOException("GAME_RECIPE_RENDER_BOUNDS");
            drawn(layout);
            if (!invalid) { copies.add(copy); copiedBytes += bytes; }
        } catch (IOException | RuntimeException error) { invalidate(); throw error; }
    }
    void endLayouts(Object renderer) {
        if (pending == null) return;
        if (!started || ended || renderer != owner || iterator == null || awaitingDraw || !exhausted) { invalidate(); return; }
        ended = true;
    }
    void finishFrame(Key key) {
        long now = clock.getAsLong();
        if (pending != null && !invalid && started && ended && (!layouts.isEmpty() || headers != null && controls != null) && pending.same(key)
                && now - began >= 0 && now - began <= MAX_FRAME_NANOS) {
            completed = new Frame(key, List.copyOf(layouts), List.copyOf(copies), headers, controls, now);
        } else completed = null;
        pending = null; owner = null; iterator = null; layouts.clear(); copies.clear(); copiedBytes = 2;
    }
    List<Object> read(Key key) throws IOException {
        long age = completed == null ? -1 : clock.getAsLong() - completed.finished;
        if (pending != null || completed == null || !completed.key.same(key) || age < 0 || age > MAX_AGE_NANOS) {
            completed = null;
            throw new IOException("GAME_RECIPE_RENDER_UNAVAILABLE");
        }
        return completed.layouts;
    }
    List<GameRecipeSlots.Layout> copied(Key key) throws IOException {
        read(key);
        if (completed.copies.size() != completed.layouts.size()) {
            completed = null; throw new IOException("GAME_RECIPE_RENDER_UNAVAILABLE");
        }
        return completed.copies;
    }
    List<GameRecipeHeaders.Label> headers(Key key) throws IOException {
        read(key);
        if (completed.headers == null) { completed = null; throw new IOException("GAME_RECIPE_HEADER_INVALID"); }
        return completed.headers;
    }
    List<GameRecipeControls.Control> controls(Key key) throws IOException {
        read(key);
        if (completed.controls == null) { completed = null; throw new IOException("GAME_RECIPE_CONTROLS_INVALID"); }
        return completed.controls;
    }
    Object stamp(Key key) throws IOException { read(key); return completed; }
    void invalidate() { invalid = true; completed = null; layouts.clear(); copies.clear(); headers = null; controls = null; copiedBytes = 2; }
    void clear() {
        pending = null; owner = null; iterator = null; layouts.clear(); copies.clear(); headers = null; controls = null; copiedBytes = 2; completed = null;
        started = false; ended = false; invalid = false; awaitingDraw = false; exhausted = false;
    }
}
