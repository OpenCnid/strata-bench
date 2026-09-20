package io.github.opencnid.strata.client;

import java.io.IOException;
import java.lang.ref.WeakReference;
import java.util.ArrayList;
import java.util.IdentityHashMap;
import java.util.List;

/** Private evidence from ordinary constructors/callbacks, never a reflective lookup of JEI fields. */
final class GameRecipeInput {
    record Binding(Object router, List<Object> widgets, List<Object> handlers) {
        Binding {
            widgets = List.copyOf(widgets); handlers = List.copyOf(handlers);
            if (router == null || widgets.size() != 4 || handlers.size() != 4) throw new IllegalArgumentException();
            for (int i = 0; i < 4; i++) for (int j = 0; j < i; j++)
                if (widgets.get(i) == widgets.get(j) || handlers.get(i) == handlers.get(j)) throw new IllegalArgumentException();
        }
        boolean matches(List<GameRecipeControls.Control> controls) {
            if (controls == null || controls.size() != 4) return false;
            for (int i = 0; i < 4; i++) if (controls.get(i) == null || controls.get(i).widget() != widgets.get(i)
                    || !GameRecipeControls.KINDS.get(i).equals(controls.get(i).kind())) return false;
            return true;
        }
    }
    private record WeakBinding(WeakReference<Object> router, List<WeakReference<Object>> widgets,
                               List<WeakReference<Object>> handlers) {
        WeakBinding(Binding value) { this(new WeakReference<>(value.router), weak(value.widgets), weak(value.handlers)); }
        private static List<WeakReference<Object>> weak(List<Object> values) {
            return values.stream().map(WeakReference::new).toList();
        }
        Binding read() {
            Object current = router.get(); var w = widgets.stream().map(WeakReference::get).toList();
            var h = handlers.stream().map(WeakReference::get).toList();
            if (current == null || w.contains(null) || h.contains(null)) return null;
            return new Binding(current, w, h);
        }
    }
    /** Factories are immediately followed by the exact seven-handler RecipesGui router constructor. */
    static final class Registry {
        private final IdentityHashMap<Object, WeakReference<Object>> factories = new IdentityHashMap<>();
        private final ArrayList<WeakBinding> bindings = new ArrayList<>();
        void factory(Object widget, Object handler) {
            if (widget == null || handler == null) { factories.clear(); return; }
            if (factories.size() >= 32 || factories.containsKey(handler)) { factories.clear(); return; }
            factories.put(handler, new WeakReference<>(widget));
        }
        void router(String name, Object router, Object[] handlers) {
            if (!"RecipesGui".equals(name)) return;
            try {
                if (router == null || handlers == null || handlers.length != 7) return;
                var widgets = new ArrayList<Object>(); var selected = new ArrayList<Object>();
                for (int i = 3; i < 7; i++) {
                    var ref = factories.get(handlers[i]); Object widget = ref == null ? null : ref.get();
                    if (widget == null) return;
                    widgets.add(widget); selected.add(handlers[i]);
                }
                var value = new Binding(router, widgets, selected);
                bindings.removeIf(ref -> ref.read() == null);
                // Unknown excess live routers fail closed instead of retaining an unbounded object graph.
                if (bindings.size() >= 16) return;
                bindings.add(new WeakBinding(value));
            } catch (IllegalArgumentException invalid) { /* No binding can authorize input. */ }
            finally { factories.clear(); }
        }
        Binding find(List<GameRecipeControls.Control> controls) throws IOException {
            Binding found = null;
            for (var weak : bindings) {
                var value = weak.read(); if (value == null || !value.matches(controls)) continue;
                if (found != null) throw unavailable(); found = value;
            }
            if (found == null) throw unavailable(); return found;
        }
    }
    /** Exactly one complete ordinary router call must select the recorded button in each phase. */
    static final class Gesture {
        private final Binding binding;
        private final Object screen, handler;
        private String phase;
        private Object input;
        private int stage, consumed;
        private boolean invalid, began, ended;
        Gesture(Binding binding, Object screen, int index) throws IOException {
            if (binding == null || screen == null || index < 0 || index >= 4) throw unavailable();
            this.binding = binding; this.screen = screen; handler = binding.handlers.get(index);
        }
        Object router() { return binding.router; }
        void invalidate() { invalid = true; }
        void prepare(String next) throws IOException {
            if (invalid || phase != null || !(stage == 0 && "SIMULATE".equals(next)
                    || stage == 1 && "EXECUTE".equals(next))) { invalid = true; throw unavailable(); }
            phase = next; input = null; consumed = 0; began = false; ended = false;
        }
        void start(Object router, Object source, Object input, String mode) {
            if (invalid || phase == null || began || router != binding.router || source != screen
                    || input == null || !phase.equals(mode)) { invalid = true; return; }
            began = true; this.input = input;
        }
        void button(Object source, Object input, Object receiver, Object returned) {
            if (returned == null) return;
            if (invalid || phase == null || !began || ended || source != screen || input != this.input
                    || receiver != handler || returned != handler || ++consumed != 1) invalid = true;
        }
        void end(Object router, Object source, Object input, boolean handled) {
            if (invalid || phase == null || !began || ended || router != binding.router || source != screen
                    || input != this.input || !handled || consumed != 1) { invalid = true; return; }
            ended = true;
        }
        void finish(boolean screenHandled) throws IOException {
            if (invalid || !screenHandled || phase == null || !began || !ended || consumed != 1) {
                invalid = true; throw unavailable();
            }
            stage++; phase = null; input = null;
        }
        void requirePreview() throws IOException {
            if (invalid || stage != 1 || phase != null) throw unavailable();
        }
        boolean executed() { return !invalid && stage == 2 && phase == null; }
    }
    @FunctionalInterface interface Reset { void reset(Object router) throws IOException; }
    /** Keep the known router owned until its non-executing native reset returns successfully. */
    static final class Ownership {
        private Gesture gesture;
        Gesture current() { return gesture; }
        void requireIdle() throws IOException { if (gesture != null) throw new IOException("GAME_RECIPE_INPUT_BUSY"); }
        Gesture acquire(Binding binding, Object screen, int index) throws IOException {
            requireIdle(); gesture = new Gesture(binding, screen, index); return gesture;
        }
        void release(Reset reset) throws IOException {
            if (gesture == null) return;
            gesture.invalidate();
            reset.reset(gesture.router());
            gesture = null;
        }
    }
    private static IOException unavailable() { return new IOException("GAME_RECIPE_INPUT_UNCONFIRMED"); }
}
