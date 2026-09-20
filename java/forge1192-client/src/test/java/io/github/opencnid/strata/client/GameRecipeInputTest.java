package io.github.opencnid.strata.client;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;

/** Synthetic constructor/input callbacks. Neither Mixin transformation nor native input is exercised. */
class GameRecipeInputTest {
    static final class Fixture {
        final Object router = new Object(), screen = new Object();
        final List<Object> widgets = List.of(new Object(), new Object(), new Object(), new Object());
        final List<Object> handlers = List.of(new Object(), new Object(), new Object(), new Object());
        final GameRecipeInput.Binding binding = new GameRecipeInput.Binding(router, widgets, handlers);
        List<GameRecipeControls.Control> controls() {
            var rows = new ArrayList<GameRecipeControls.Control>();
            for (int i = 0; i < 4; i++) rows.add(new GameRecipeControls.Control(widgets.get(i),
                GameRecipeControls.KINDS.get(i), "enabled", new GameRecipeSlots.Rect(i * 10, 0, 10, 10)));
            return rows;
        }
        Object[] nativeHandlers() { return new Object[] {new Object(), new Object(), new Object(),
            handlers.get(0), handlers.get(1), handlers.get(2), handlers.get(3)}; }
        void factories(GameRecipeInput.Registry registry) {
            for (int i = 0; i < 4; i++) registry.factory(widgets.get(i), handlers.get(i));
        }
        void register(GameRecipeInput.Registry registry) { factories(registry); registry.router("RecipesGui", router, nativeHandlers()); }
        void route(GameRecipeInput.Gesture gesture, int index, String mode) throws IOException {
            gesture.prepare(mode); Object input = new Object();
            gesture.start(router, screen, input, mode);
            // Earlier ordinary button handlers may decline the event.
            for (int i = 0; i < index; i++) gesture.button(screen, input, handlers.get(i), null);
            gesture.button(screen, input, handlers.get(index), handlers.get(index));
            gesture.end(router, screen, input, true); gesture.finish(true);
        }
    }
    @Test void bindsOnlyTheFourOrderedDrawnWidgetsFromTheOrdinaryConstructor() throws Exception {
        var f = new Fixture(); var registry = new GameRecipeInput.Registry();
        assertThrows(IOException.class, () -> registry.find(f.controls())); f.register(registry);
        var found = registry.find(f.controls()); assertSame(f.router, found.router());
        assertEquals(f.handlers, found.handlers()); assertEquals(f.widgets, found.widgets());
        assertThrows(UnsupportedOperationException.class, () -> found.handlers().clear());
        assertThrows(UnsupportedOperationException.class, () -> found.widgets().clear());
        assertThrows(IOException.class, () -> registry.find(new Fixture().controls()));
    }
    @Test void missingFactoryWrongRouterAndMalformedConstructorsNeverBind() throws Exception {
        for (int fault = 0; fault < 6; fault++) {
            var f = new Fixture(); var registry = new GameRecipeInput.Registry(); f.factories(registry);
            Object[] handlers = f.nativeHandlers(); Object router = f.router; String name = "RecipesGui";
            switch (fault) {
                case 0 -> handlers[6] = new Object();
                case 1 -> handlers = new Object[6];
                case 2 -> handlers = null;
                case 3 -> router = null;
                case 4 -> name = "Inventory";
                case 5 -> handlers[5] = handlers[6];
                default -> fail();
            }
            registry.router(name, router, handlers);
            assertThrows(IOException.class, () -> registry.find(f.controls()), "fault=" + fault);
        }
    }
    @Test void factoriesCannotBeReusedAfterARecipesConstructorAttempt() throws Exception {
        var f = new Fixture(); var registry = new GameRecipeInput.Registry(); f.factories(registry);
        registry.router("RecipesGui", f.router, new Object[7]);
        registry.router("RecipesGui", f.router, f.nativeHandlers());
        assertThrows(IOException.class, () -> registry.find(f.controls()));
        f.register(registry); assertSame(f.router, registry.find(f.controls()).router());
    }
    @Test void duplicateOrNullFactoriesCannotAuthorizeAConstruction() throws Exception {
        for (int fault = 0; fault < 3; fault++) {
            var f = new Fixture(); var registry = new GameRecipeInput.Registry(); f.factories(registry);
            if (fault == 0) registry.factory(f.widgets.get(0), f.handlers.get(0));
            if (fault == 1) registry.factory(null, new Object());
            if (fault == 2) registry.factory(new Object(), null);
            registry.router("RecipesGui", f.router, f.nativeHandlers());
            assertThrows(IOException.class, () -> registry.find(f.controls()));
        }
    }
    @Test void excessPendingFactoriesAndLiveRoutersAreBounded() throws Exception {
        var f = new Fixture(); var registry = new GameRecipeInput.Registry(); f.factories(registry);
        for (int i = 0; i < 29; i++) registry.factory(new Object(), new Object());
        registry.router("RecipesGui", f.router, f.nativeHandlers());
        assertThrows(IOException.class, () -> registry.find(f.controls()));
        var retained = new ArrayList<Fixture>();
        for (int i = 0; i < 16; i++) { var live = new Fixture(); retained.add(live); live.register(registry); }
        f.register(registry); assertThrows(IOException.class, () -> registry.find(f.controls()));
        for (var live : retained) assertSame(live.router, registry.find(live.controls()).router());
    }
    @Test void multipleRoutersForTheSameWidgetsAreAmbiguous() throws Exception {
        var f = new Fixture(); var registry = new GameRecipeInput.Registry(); f.register(registry);
        var otherRouter = new Object();
        f.factories(registry); registry.router("RecipesGui", otherRouter, f.nativeHandlers());
        assertThrows(IOException.class, () -> registry.find(f.controls()));
        java.lang.ref.Reference.reachabilityFence(otherRouter);
    }
    @Test void changedOrderKindsCountsOrIdentityRejectEvenWhenObjectsCompareEqual() throws Exception {
        var f = new Fixture(); var registry = new GameRecipeInput.Registry(); f.register(registry);
        for (int fault = 0; fault < 5; fault++) {
            var rows = new ArrayList<>(f.controls()); var row = rows.get(0);
            switch (fault) {
                case 0 -> java.util.Collections.reverse(rows);
                case 1 -> rows.remove(0);
                case 2 -> rows.set(0, null);
                case 3 -> rows.set(0, new GameRecipeControls.Control(row.widget(), null, row.state(), row.area()));
                case 4 -> rows.set(0, new GameRecipeControls.Control(new Object(), row.kind(), row.state(), row.area()));
                default -> fail();
            }
            assertThrows(IOException.class, () -> registry.find(rows));
        }
        assertThrows(IOException.class, () -> registry.find(null));
        var sameValue = new ArrayList<Object>(); for (int i = 0; i < 4; i++) sameValue.add(new String("same"));
        var identityBinding = new GameRecipeInput.Binding(f.router, sameValue, f.handlers);
        var rows = f.controls(); for (int i = 0; i < 4; i++) rows.set(i, new GameRecipeControls.Control(
            new String("same"), GameRecipeControls.KINDS.get(i), "enabled", rows.get(i).area()));
        assertFalse(identityBinding.matches(rows));
    }
    @Test void distinctHandlersAndWidgetsAreRequiredAndListsAreCopied() {
        var f = new Fixture();
        assertThrows(IllegalArgumentException.class, () -> new GameRecipeInput.Binding(null, f.widgets, f.handlers));
        assertThrows(IllegalArgumentException.class, () -> new GameRecipeInput.Binding(f.router, f.widgets.subList(0, 3), f.handlers));
        for (boolean duplicateWidget : List.of(true, false)) {
            var widgets = new ArrayList<>(f.widgets); var handlers = new ArrayList<>(f.handlers);
            if (duplicateWidget) widgets.set(1, widgets.get(0)); else handlers.set(1, handlers.get(0));
            assertThrows(IllegalArgumentException.class, () -> new GameRecipeInput.Binding(f.router, widgets, handlers));
        }
        var widgets = new ArrayList<>(f.widgets); var binding = new GameRecipeInput.Binding(f.router, widgets, f.handlers);
        widgets.clear(); assertEquals(4, binding.widgets().size());
    }
    @Test void eachButtonRequiresOneCompletePreviewThenOneCompleteExecution() throws Exception {
        var f = new Fixture();
        for (int i = 0; i < 4; i++) {
            var gesture = new GameRecipeInput.Gesture(f.binding, f.screen, i);
            assertSame(f.router, gesture.router()); assertFalse(gesture.executed());
            f.route(gesture, i, "SIMULATE"); gesture.requirePreview(); assertFalse(gesture.executed());
            f.route(gesture, i, "EXECUTE"); assertTrue(gesture.executed());
            assertThrows(IOException.class, gesture::requirePreview);
            assertThrows(IOException.class, () -> gesture.prepare("EXECUTE")); assertFalse(gesture.executed());
        }
    }
    @Test void executionCannotStartBeforePreviewOrBeRetriedAfterWrongOrdering() throws Exception {
        var f = new Fixture();
        for (String mode : List.of("EXECUTE", "IMMEDIATE", "unknown")) {
            var gesture = new GameRecipeInput.Gesture(f.binding, f.screen, 0);
            assertThrows(IOException.class, () -> gesture.prepare(mode));
            assertThrows(IOException.class, () -> gesture.prepare("SIMULATE"));
        }
        var gesture = new GameRecipeInput.Gesture(f.binding, f.screen, 0); f.route(gesture, 0, "SIMULATE");
        assertThrows(IOException.class, () -> gesture.prepare("SIMULATE"));
        assertThrows(IOException.class, () -> gesture.prepare("EXECUTE"));
    }
    @Test void wrongScreenRouterInputModeHandlerOrReturnPoisonTheGesture() throws Exception {
        var f = new Fixture();
        for (int fault = 0; fault < 10; fault++) {
            var gesture = new GameRecipeInput.Gesture(f.binding, f.screen, 0); Object input = new Object();
            gesture.prepare("SIMULATE"); gesture.start(fault == 0 ? new Object() : f.router,
                fault == 1 ? new Object() : f.screen, fault == 2 ? null : input, fault == 3 ? "EXECUTE" : "SIMULATE");
            gesture.button(fault == 4 ? new Object() : f.screen, fault == 5 ? new Object() : input,
                fault == 6 ? f.handlers.get(1) : f.handlers.get(0), fault == 7 ? f.handlers.get(1) : f.handlers.get(0));
            gesture.end(f.router, f.screen, fault == 8 ? new Object() : input, fault != 9);
            assertThrows(IOException.class, () -> gesture.finish(true), "fault=" + fault);
            assertThrows(IOException.class, () -> gesture.prepare("SIMULATE"));
        }
    }
    @Test void missingRepeatedNestedAndAfterReturnCallbacksCannotConfirmInput() throws Exception {
        var f = new Fixture();
        for (int fault = 0; fault < 8; fault++) {
            var gesture = new GameRecipeInput.Gesture(f.binding, f.screen, 0); Object input = new Object();
            gesture.prepare("SIMULATE");
            if (fault != 0) gesture.start(f.router, f.screen, input, "SIMULATE");
            if (fault == 1) gesture.start(f.router, f.screen, input, "SIMULATE");
            if (fault != 2) gesture.button(f.screen, input, f.handlers.get(0), f.handlers.get(0));
            if (fault == 3) gesture.button(f.screen, input, f.handlers.get(0), f.handlers.get(0));
            if (fault != 4) gesture.end(f.router, f.screen, input, true);
            if (fault == 5) gesture.end(f.router, f.screen, input, true);
            if (fault == 6) gesture.button(f.screen, input, f.handlers.get(0), f.handlers.get(0));
            final boolean screenHandled = fault != 7;
            assertThrows(IOException.class, () -> gesture.finish(screenHandled), "fault=" + fault);
            assertThrows(IOException.class, () -> gesture.prepare("SIMULATE"));
        }
    }
    @Test void unrelatedInputBetweenPreviewAndExecutionRevokesThePreview() throws Exception {
        var f = new Fixture(); var gesture = new GameRecipeInput.Gesture(f.binding, f.screen, 0);
        f.route(gesture, 0, "SIMULATE"); gesture.start(new Object(), f.screen, new Object(), "SIMULATE");
        assertThrows(IOException.class, gesture::requirePreview);
        assertThrows(IOException.class, () -> gesture.prepare("EXECUTE"));
    }
    @Test void unknownSourceScreenAndIndicesCannotBeOwned() {
        var f = new Fixture();
        assertThrows(IOException.class, () -> new GameRecipeInput.Gesture(null, f.screen, 0));
        assertThrows(IOException.class, () -> new GameRecipeInput.Gesture(f.binding, null, 0));
        assertThrows(IOException.class, () -> new GameRecipeInput.Gesture(f.binding, f.screen, -1));
        assertThrows(IOException.class, () -> new GameRecipeInput.Gesture(f.binding, f.screen, 4));
    }
    @Test void cancellationUsesTheKnownRouterWithoutExecutingThePreview() throws Exception {
        var f = new Fixture(); var owner = new GameRecipeInput.Ownership();
        var gesture = owner.acquire(f.binding, f.screen, 2); f.route(gesture, 2, "SIMULATE");
        assertThrows(IOException.class, owner::requireIdle);
        assertThrows(IOException.class, () -> owner.acquire(new Fixture().binding, f.screen, 0));
        var calls = new AtomicInteger(); owner.release(router -> { assertSame(f.router, router); calls.incrementAndGet(); });
        assertEquals(1, calls.get()); assertNull(owner.current()); owner.requireIdle(); assertFalse(gesture.executed());
        assertThrows(IOException.class, () -> gesture.prepare("EXECUTE"));
        owner.release(router -> fail("already released"));
    }
    @Test void resetFailureRetainsOwnershipAndDoesNotReplayEitherInputPhase() throws Exception {
        var f = new Fixture(); var owner = new GameRecipeInput.Ownership();
        var gesture = owner.acquire(f.binding, f.screen, 0); f.route(gesture, 0, "SIMULATE");
        assertThrows(IOException.class, () -> owner.release(router -> { throw new IOException("reset failed"); }));
        assertSame(gesture, owner.current()); assertThrows(IOException.class, owner::requireIdle); assertFalse(gesture.executed());
        assertThrows(IOException.class, gesture::requirePreview);
        assertThrows(IOException.class, () -> gesture.prepare("EXECUTE"));
        owner.release(router -> assertSame(f.router, router)); assertNull(owner.current());
        assertThrows(IOException.class, () -> gesture.prepare("EXECUTE"));
    }
    @Test void evenMissingPreviewHooksCanBeCleanedUpWithTheConstructorRouter() throws Exception {
        var f = new Fixture(); var owner = new GameRecipeInput.Ownership(); var gesture = owner.acquire(f.binding, f.screen, 0);
        gesture.prepare("SIMULATE"); assertThrows(IOException.class, () -> gesture.finish(true));
        owner.release(router -> assertSame(f.router, router)); assertNull(owner.current()); assertFalse(gesture.executed());
    }
    @Test void completedExecutionStillRequiresNonExecutingCleanupAndCannotReplay() throws Exception {
        var f = new Fixture(); var owner = new GameRecipeInput.Ownership(); var gesture = owner.acquire(f.binding, f.screen, 3);
        f.route(gesture, 3, "SIMULATE"); f.route(gesture, 3, "EXECUTE"); assertTrue(gesture.executed());
        owner.release(router -> assertSame(f.router, router)); assertNull(owner.current());
        assertThrows(IOException.class, () -> gesture.prepare("SIMULATE"));
    }
}
