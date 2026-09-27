package io.github.opencnid.strata.client;

import java.io.IOException;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.EnumSource;
import org.junit.jupiter.params.provider.ValueSource;
import static org.junit.jupiter.api.Assertions.*;

/** Synthetic clock/callback boundary; no native key sendability or effect qualification. */
class KeyInputSessionTest {
    @Test void sprintCompanionPressesAndReleasesBothInOrder() throws Exception {
        Port p = new Port();
        var input = KeyInputSession.start(p, new KeyInputSession.Request(341, KeyInputSession.Modifier.NONE, 50,
            KeyInputSession.Device.KEYBOARD, 87), Set.of(341, 87), p::emit, p::emit);
        assertEquals(Set.of(341, 87), p.down);
        p.now = 150; assertTrue(input.tick(p::emit));
        assertEquals(List.of("341:true:2", "87:true:2", "87:false:2", "341:false:0"), p.events);
        assertEquals(5, p.charges); assertTrue(p.down.isEmpty());
        var receipt = input.releaseReceipt();
        assertEquals("strata/NativeInputRelease/3", receipt.get("schema").getAsString());
        assertEquals(87, receipt.get("companion").getAsInt());
        assertEquals("[87,341]", receipt.getAsJsonArray("release_order").toString());
    }
    @ParameterizedTest @ValueSource(ints = {1, 2, 3, 4, 5})
    void pairedAccountingFailureAlwaysAttemptsBothReleases(int failure) {
        Port p = new Port(); p.failCharge = failure;
        assertThrows(IOException.class, () -> {
            var input = KeyInputSession.start(p, new KeyInputSession.Request(341, KeyInputSession.Modifier.NONE, 50,
                KeyInputSession.Device.KEYBOARD, 87), Set.of(341, 87), p::emit, p::emit);
            p.now = 150; input.tick(p::emit);
            fail("failed charge cannot confirm a complete gesture");
        });
        assertTrue(p.down.isEmpty()); assertEquals(1, p.clears);
    }
    @ParameterizedTest @ValueSource(strings = {"341:true:2", "87:true:2", "87:false:2", "341:false:0"})
    void pairedCallbackFailureStillAttemptsCompleteCleanup(String failure) {
        Port p = new Port(); p.failEvent = failure;
        assertThrows(IOException.class, () -> {
            var input = KeyInputSession.start(p, new KeyInputSession.Request(341, KeyInputSession.Modifier.NONE, 50,
                KeyInputSession.Device.KEYBOARD, 87), Set.of(341, 87), p::emit, p::emit);
            p.now = 150; input.tick(p::emit);
        });
        assertTrue(p.down.isEmpty()); assertEquals(1, p.clears);
    }
    @ParameterizedTest @ValueSource(ints = {0, 31, 340, 341, 342, 343})
    void pairedCompanionCannotBeMouseModifierOrDuplicate(int companion) {
        Port p = new Port();
        assertThrows(IOException.class, () -> KeyInputSession.start(p,
            new KeyInputSession.Request(341, KeyInputSession.Modifier.NONE, 50, KeyInputSession.Device.KEYBOARD, companion),
            new HashSet<>(List.of(341, companion)), p::emit, p::emit));
        assertTrue(p.events.isEmpty()); assertEquals(0, p.charges);
    }
    @ParameterizedTest @ValueSource(booleans = {false, true})
    void pairedCancellationAndTimeoutReleaseForwardAndSprint(boolean timeout) throws Exception {
        Port p = new Port();
        var input = KeyInputSession.start(p, new KeyInputSession.Request(341, KeyInputSession.Modifier.NONE, 50,
            KeyInputSession.Device.KEYBOARD, 87), Set.of(341, 87), p::emit, p::emit);
        if (timeout) { p.now = 2101; assertThrows(IOException.class, input::watchdog); }
        else input.cancel();
        assertTrue(p.down.isEmpty()); assertEquals(1, p.clears); assertEquals(5, p.charges);
    }
    static final Set<Integer> POOL = Set.of(65, 302, 340, 341, 342);
    static final class Port implements KeyInputSession.Port {
        final List<String> events = new ArrayList<>();
        final Set<Integer> down = new HashSet<>();
        long now = 100;
        int charges, clears, mouseEvents, failCharge = -1;
        String failEvent, contextFailure = "CONTEXT_CHANGED";
        boolean valid = true, failClear;
        public void validate() throws IOException { if (!valid) throw new IOException(contextFailure); }
        public long monotonicMillis() { return now; }
        public void event(int key, boolean pressed, int modifiers) throws IOException {
            if (pressed) down.add(key); else down.remove(key);
            String value = key + ":" + pressed + ":" + modifiers; events.add(value);
            if (value.equals(failEvent)) throw new IOException("CALLBACK_FAILED");
        }
        public void mouseEvent(int button, boolean pressed, int modifiers) throws IOException {
            mouseEvents++; event(button, pressed, modifiers);
        }
        public void clear() throws IOException {
            clears++; down.clear(); if (failClear) throw new IOException("CLEAR_FAILED");
        }
        void emit(GameActionLane.Operation operation) throws IOException {
            charges++; if (charges == failCharge) throw new IOException("JOURNAL_FAILED"); operation.run();
        }
        KeyInputSession start(KeyInputSession.Modifier modifier) throws IOException {
            return KeyInputSession.start(this, new KeyInputSession.Request(65, modifier, 50), POOL, this::emit, this::emit);
        }
    }

    @ParameterizedTest @EnumSource(KeyInputSession.Modifier.class)
    void ordinaryPressThenReverseReleaseWithModifierFlags(KeyInputSession.Modifier modifier) throws Exception {
        Port p = new Port(); var session = p.start(modifier);
        assertTrue(p.down.contains(65));
        p.now = 149; assertFalse(session.tick(p::emit));
        p.now = 150; assertTrue(session.tick(p::emit));
        List<String> expected = new ArrayList<>();
        if (modifier != KeyInputSession.Modifier.NONE) expected.add(modifier.key + ":true:" + modifier.mask);
        expected.add("65:true:" + modifier.mask); expected.add("65:false:" + modifier.mask);
        if (modifier != KeyInputSession.Modifier.NONE) expected.add(modifier.key + ":false:0");
        assertEquals(expected, p.events); assertEquals(expected.size() + 2, p.charges);
        assertTrue(p.down.isEmpty()); assertEquals(1, p.clears);
        var receipt = session.releaseReceipt();
        assertEquals("strata/NativeInputRelease/2", receipt.get("schema").getAsString());
        assertEquals(modifier.name(), receipt.get("modifier").getAsString());
        assertEquals(modifier == KeyInputSession.Modifier.NONE ? 1 : 2, receipt.getAsJsonArray("release_order").size());
        assertEquals(65, receipt.getAsJsonArray("release_order").get(0).getAsInt());
        if (modifier != KeyInputSession.Modifier.NONE)
            assertEquals(modifier.key, receipt.getAsJsonArray("release_order").get(1).getAsInt());
        assertTrue(session.tick(p::emit)); session.cancel(); assertEquals(1, p.clears);
    }
    @ParameterizedTest @ValueSource(ints = {-1, 0, 31, 66, 343, 348, 349, 0x1f642})
    void unsupportedKeysFailBeforeInput(int key) {
        Port p = new Port();
        assertThrows(IOException.class, () -> KeyInputSession.start(p,
            new KeyInputSession.Request(key, KeyInputSession.Modifier.NONE, 50), POOL, p::emit, p::emit));
        assertEquals(0, p.charges); assertTrue(p.events.isEmpty());
    }
    @ParameterizedTest @ValueSource(ints = {340, 341, 342})
    void standaloneModifierPressesOnceAndReleasesWithNoModifier(int key) throws Exception {
        Port p = new Port();
        var session = KeyInputSession.start(p,
            new KeyInputSession.Request(key, KeyInputSession.Modifier.NONE, 50), POOL, p::emit, p::emit);
        assertEquals(Set.of(key), p.down);
        p.now = 150; assertTrue(session.tick(p::emit));
        assertEquals(List.of(key + ":true:" + (1 << (key - 340)), key + ":false:0"), p.events);
        assertTrue(p.down.isEmpty()); assertEquals(3, p.charges); assertEquals(1, p.clears);
    }
    @ParameterizedTest @ValueSource(ints = {340, 341, 342})
    void standaloneModifierCannotAlsoRequestAChord(int key) {
        Port p = new Port();
        assertThrows(IOException.class, () -> KeyInputSession.start(p,
            new KeyInputSession.Request(key, KeyInputSession.Modifier.SHIFT, 50), POOL, p::emit, p::emit));
        assertTrue(p.events.isEmpty()); assertEquals(0, p.charges);
    }
    @ParameterizedTest @ValueSource(longs = {-1, 0, 2001, Long.MAX_VALUE})
    void invalidHoldFailsBeforeInput(long hold) {
        Port p = new Port();
        assertThrows(IOException.class, () -> KeyInputSession.start(p,
            new KeyInputSession.Request(65, KeyInputSession.Modifier.NONE, hold), POOL, p::emit, p::emit));
        assertEquals(0, p.charges);
    }
    @Test void modifierRequiresItsOwnPoolEntry() {
        Port p = new Port();
        assertThrows(IOException.class, () -> KeyInputSession.start(p,
            new KeyInputSession.Request(65, KeyInputSession.Modifier.SHIFT, 50), Set.of(65), p::emit, p::emit));
        assertEquals(0, p.charges);
    }
    @Test void missingContextCannotPress() {
        Port p = new Port(); p.valid = false;
        assertThrows(IOException.class, () -> p.start(KeyInputSession.Modifier.NONE));
        assertEquals(0, p.charges);
    }
    @Test void callbackExceptionReleasesPossiblyDeliveredPressWithoutRetry() {
        Port p = new Port(); p.failEvent = "65:true:1";
        assertThrows(IOException.class, () -> p.start(KeyInputSession.Modifier.SHIFT));
        assertEquals(List.of("340:true:1", "65:true:1", "65:false:1", "340:false:0"), p.events);
        assertTrue(p.down.isEmpty()); assertEquals(1, p.clears);
    }
    @Test void chargeFailureBeforeSecondPressReleasesOnlyAttemptedModifier() {
        Port p = new Port(); p.failCharge = 2;
        assertThrows(IOException.class, () -> p.start(KeyInputSession.Modifier.SHIFT));
        assertEquals(List.of("340:true:1", "340:false:0"), p.events);
        assertEquals(4, p.charges); assertTrue(p.down.isEmpty());
    }
    @Test void cancellationIsNotSuccessfulGestureCompletion() throws Exception {
        Port p = new Port(); var session = p.start(KeyInputSession.Modifier.NONE);
        session.cancel(); session.cancel();
        assertEquals("SETTINGS_INPUT_CANCELLED", assertThrows(IOException.class, () -> session.tick(p::emit)).getMessage());
        assertEquals(3, p.charges); assertEquals(1, p.clears);
    }
    @Test void independentWatchdogReleasesTimedOutHoldAndRetainsFailure() throws Exception {
        Port p = new Port(); var session = p.start(KeyInputSession.Modifier.CONTROL); p.now = 2101;
        assertEquals("SETTINGS_INPUT_HOLD_TIMEOUT", assertThrows(IOException.class, session::watchdog).getMessage());
        assertTrue(session.closed()); assertTrue(p.down.isEmpty());
        assertEquals("SETTINGS_INPUT_HOLD_TIMEOUT", assertThrows(IOException.class, () -> session.tick(p::emit)).getMessage());
    }
    @Test void contextLossStillReleasesAllKeys() throws Exception {
        Port p = new Port(); var session = p.start(KeyInputSession.Modifier.ALT); p.valid = false;
        assertThrows(IOException.class, () -> session.tick(p::emit));
        assertEquals(List.of("342:true:4", "65:true:4", "65:false:4", "342:false:0"), p.events);
        assertTrue(p.down.isEmpty());
    }
    @Test void backwardsClockStopsRatherThanExtendingHold() throws Exception {
        Port p = new Port(); var session = p.start(KeyInputSession.Modifier.NONE); p.now = 99;
        assertEquals("SETTINGS_INPUT_CLOCK_INVALID", assertThrows(IOException.class, () -> session.tick(p::emit)).getMessage());
        assertTrue(p.down.isEmpty());
    }
    @Test void journalFailureCannotSuppressSafetyRelease() throws Exception {
        Port p = new Port(); var session = p.start(KeyInputSession.Modifier.SHIFT); p.failCharge = 3;
        assertThrows(IOException.class, session::cancel);
        assertEquals(List.of("340:true:1", "65:true:1", "65:false:1", "340:false:0"), p.events);
        assertTrue(p.down.isEmpty()); assertEquals(5, p.charges);
    }
    @Test void releaseCallbackFailureDoesNotReplayItOrSkipRemainingCleanup() throws Exception {
        Port p = new Port(); var session = p.start(KeyInputSession.Modifier.SHIFT); p.failEvent = "65:false:1";
        assertThrows(IOException.class, session::cancel);
        assertEquals(List.of("340:true:1", "65:true:1", "65:false:1", "340:false:0"), p.events);
        assertEquals(1, p.clears); assertTrue(p.down.isEmpty());
        assertThrows(IOException.class, session::releaseReceipt);
        assertEquals("SETTINGS_INPUT_RELEASE_UNCONFIRMED", assertThrows(IOException.class, () -> session.tick(p::emit)).getMessage());
    }
    @Test void clearFailureCannotBecomeSuccess() throws Exception {
        Port p = new Port(); var session = p.start(KeyInputSession.Modifier.NONE); p.failClear = true; p.now = 150;
        assertThrows(IOException.class, session::releaseReceipt);
        assertThrows(IOException.class, () -> session.tick(p::emit));
        assertThrows(IOException.class, session::releaseReceipt);
        assertEquals("SETTINGS_INPUT_RELEASE_UNCONFIRMED", assertThrows(IOException.class, () -> session.tick(p::emit)).getMessage());
    }
    @Test void noSessionNeverOverridesNativePolling() {
        assertNull(NativeKeyInput.polled(123, 65)); assertNull(NativeKeyInput.polled(0, 340));
    }
    @Test void waitBudgetFailureStaysFailureAfterRelease() throws Exception {
        Port p = new Port(); var session = p.start(KeyInputSession.Modifier.NONE); p.failCharge = 2;
        assertThrows(IOException.class, () -> session.tick(p::emit));
        assertEquals("JOURNAL_FAILED", assertThrows(IOException.class, () -> session.tick(p::emit)).getMessage());
        assertTrue(p.down.isEmpty()); assertEquals(1, p.clears);
    }
    @Test void reservedSafetyEmitterWorksAfterOrdinaryBudgetExhaustion() throws Exception {
        Port p = new Port(); int[] ordinary = {0}, safety = {0};
        var session = KeyInputSession.start(p, new KeyInputSession.Request(65, KeyInputSession.Modifier.SHIFT, 50), POOL,
            operation -> { ordinary[0]++; operation.run(); },
            operation -> { safety[0]++; operation.run(); });
        session.cancel(); assertEquals(2, ordinary[0]); assertEquals(3, safety[0]);
        assertTrue(p.down.isEmpty());
    }
    @Test void clearStillRunsWhenItsJournalWriteFails() throws Exception {
        Port p = new Port(); var session = p.start(KeyInputSession.Modifier.NONE); p.failCharge = 3;
        assertThrows(IOException.class, session::cancel); assertEquals(1, p.clears);
        assertTrue(p.down.isEmpty());
    }
    @Test void exceptionWithoutMessageCannotBecomeSuccessfulCompletion() throws Exception {
        Port p = new Port(); var session = p.start(KeyInputSession.Modifier.NONE);
        p.valid = false; p.contextFailure = null;
        assertThrows(IOException.class, () -> session.tick(p::emit));
        assertEquals("SETTINGS_INPUT_FAILED", assertThrows(IOException.class, () -> session.tick(p::emit)).getMessage());
        assertTrue(p.down.isEmpty());
    }

    @ParameterizedTest @EnumSource(KeyInputSession.Modifier.class)
    void mouseButtonsUseOrdinaryCallbackThenReverseRelease(KeyInputSession.Modifier modifier) throws Exception {
        for (int button : new int[]{0, 1}) {
            Port p = new Port();
            var request = new KeyInputSession.Request(button, modifier, 50, KeyInputSession.Device.MOUSE);
            var session = KeyInputSession.start(p, request, Set.of(0, 1, 340, 341, 342), p::emit, p::emit);
            assertTrue(p.down.contains(button));
            assertFalse(session.tick(p::emit)); p.now = 150; assertTrue(session.tick(p::emit));
            assertEquals(2, p.mouseEvents); assertTrue(p.down.isEmpty());
            assertEquals("mouse", session.releaseReceipt().get("device").getAsString());
            assertEquals(button, session.releaseReceipt().getAsJsonArray("release_order").get(0).getAsInt());
            if (modifier != KeyInputSession.Modifier.NONE)
                assertEquals(modifier.key, session.releaseReceipt().getAsJsonArray("release_order").get(1).getAsInt());
            session.cancel(); assertEquals(2, p.mouseEvents);
        }
    }
    @ParameterizedTest @ValueSource(ints = {-1, 2, 7, 32, 65, 340})
    void unsupportedMouseButtonsNeverReachCallbacks(int button) {
        Port p = new Port();
        assertThrows(IOException.class, () -> KeyInputSession.start(p,
            new KeyInputSession.Request(button, KeyInputSession.Modifier.NONE, 50, KeyInputSession.Device.MOUSE),
            Set.of(button), p::emit, p::emit));
        assertEquals(0, p.mouseEvents); assertEquals(0, p.charges);
    }
    @Test void ambiguousMousePressStillReleasesButtonThenModifier() {
        Port p = new Port(); p.failEvent = "0:true:1";
        assertThrows(IOException.class, () -> KeyInputSession.start(p,
            new KeyInputSession.Request(0, KeyInputSession.Modifier.SHIFT, 50, KeyInputSession.Device.MOUSE),
            Set.of(0, 340), p::emit, p::emit));
        assertEquals(List.of("340:true:1", "0:true:1", "0:false:1", "340:false:0"), p.events);
        assertEquals(2, p.mouseEvents); assertTrue(p.down.isEmpty());
    }
    @Test void mouseReleaseFailureDoesNotSkipModifierAndCannotProduceReceipt() throws Exception {
        Port p = new Port();
        var session = KeyInputSession.start(p,
            new KeyInputSession.Request(1, KeyInputSession.Modifier.CONTROL, 50, KeyInputSession.Device.MOUSE),
            Set.of(1, 341), p::emit, p::emit);
        p.failEvent = "1:false:2"; p.now = 150;
        assertThrows(IOException.class, () -> session.tick(p::emit));
        assertEquals(List.of("341:true:2", "1:true:2", "1:false:2", "341:false:0"), p.events);
        assertTrue(p.down.isEmpty()); assertThrows(IOException.class, session::releaseReceipt);
    }
    @Test void timedOutMouseHoldReleasesWithoutNewAuthority() throws Exception {
        Port p = new Port();
        var session = KeyInputSession.start(p,
            new KeyInputSession.Request(0, KeyInputSession.Modifier.NONE, 50, KeyInputSession.Device.MOUSE),
            Set.of(0), p::emit, p::emit);
        p.now = 2101; assertThrows(IOException.class, session::watchdog);
        assertTrue(p.down.isEmpty()); assertEquals(2, p.mouseEvents);
        assertThrows(IOException.class, () -> session.tick(p::emit));
    }
}
