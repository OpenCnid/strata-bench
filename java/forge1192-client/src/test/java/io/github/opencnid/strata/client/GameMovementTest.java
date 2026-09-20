package io.github.opencnid.strata.client;

import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

/** Independent toy dynamics exercise control decisions; they do not establish Minecraft physics. */
class GameMovementTest {
    static GameVisibility.Point p(double x, double z) { return new GameVisibility.Point(x, 64, z); }
    static class Walker implements GameMovement.Port {
        long tick; double x = .5, z = .5, vx, vz, health = 20, absorption;
        boolean forward, interrupted, failCorridor, emitting, sawForward;
        String context = "initial";
        double yaw; int events;
        final List<Boolean> history = new ArrayList<>();
        final List<Double> turnSpeeds = new ArrayList<>();
        public GameMovement.Frame read() {
            return new GameMovement.Frame(tick, p(x, z), new GameVisibility.Point(vx, 0, vz), health, absorption, interrupted, context);
        }
        public void corridor(GameVisibility.Point from, GameVisibility.Point to) throws IOException {
            if (failCorridor) throw new IOException("PATH_BLOCKED");
            assertTrue(from.distance(to) <= 2);
        }
        public void controls(double degrees, boolean down) {
            assertTrue(emitting, "No control change outside the charged emitter");
            if (down && forward && Math.abs(degrees - yaw) > 45) turnSpeeds.add(Math.hypot(vx, vz));
            yaw = degrees; forward = down; sawForward |= down; history.add(down);
        }
        void emit(GameActionLane.Operation operation) throws IOException {
            events++; emitting = true;
            try { operation.run(); } finally { emitting = false; }
        }
        void step() {
            tick++;
            if (forward) { vx += -Math.sin(Math.toRadians(yaw)) * .08; vz += Math.cos(Math.toRadians(yaw)) * .08; }
            x += vx; z += vz; vx *= .5; vz *= .5;
        }
        GameActionLane.Motor start(List<GameVisibility.Point> route, double tolerance) throws IOException {
            return GameMovement.start(this, route, route.isEmpty() ? p(x, z) : route.get(route.size() - 1), tolerance, this::emit);
        }
    }
    @Test void routeCompletesOnlyWhenSettledAndEveryActiveDecisionIsCharged() throws Exception {
        var walker = new Walker(); var route = List.of(p(1.5, .5), p(1.5, 1.5), p(2.5, 1.5));
        var motor = walker.start(route, .10); boolean completed = false;
        for (int i = 0; i < 300; i++) {
            walker.step(); int before = walker.events;
            completed = motor.tick(walker::emit);
            assertEquals(completed ? before : before + 1, walker.events);
            if (completed) break;
        }
        assertTrue(completed); assertTrue(walker.sawForward);
        assertTrue(p(walker.x, walker.z).distance(p(2.5, 1.5)) <= .10);
        assertTrue(Math.hypot(walker.vx, walker.vz) <= .003);
        assertTrue(walker.turnSpeeds.isEmpty());
        assertTrue(walker.history.subList(0, 9).stream().noneMatch(Boolean::booleanValue));
        int neutral = 0; boolean wasDown = false;
        for (boolean down : walker.history) {
            if (down && !wasDown) assertTrue(neutral >= 8, "New press cannot trigger the double-tap sprint window");
            neutral = down ? 0 : neutral + 1; wasDown = down;
        }
    }
    @Test void missingCorridorFailsBeforeFirstInputAndChangesInterruptBeforeNextInput() throws Exception {
        var walker = new Walker(); walker.failCorridor = true;
        assertThrows(IOException.class, () -> walker.start(List.of(p(1.5, .5)), .1)); assertEquals(0, walker.events);
        walker.failCorridor = false; var motor = walker.start(List.of(p(1.5, .5)), .1);
        walker.step(); walker.failCorridor = true; int before = walker.events;
        assertEquals("PATH_BLOCKED", assertThrows(IOException.class, () -> motor.tick(walker::emit)).getMessage());
        assertEquals(before, walker.events);
    }
    @Test void damageAbsorptionLossCollisionAndContextChangesInterrupt() throws Exception {
        for (String fault : List.of("health", "absorption", "collision", "context")) {
            var walker = new Walker(); walker.absorption = 3;
            var motor = walker.start(List.of(p(1.5, .5)), .1); walker.step();
            switch (fault) {
                case "health" -> walker.health--;
                case "absorption" -> walker.absorption--;
                case "collision" -> walker.interrupted = true;
                case "context" -> walker.context = "changed";
            }
            assertThrows(IOException.class, () -> motor.tick(walker::emit)); assertEquals(1, walker.events);
        }
    }
    @Test void bodyTickGapsDuplicateTicksAndUnexpectedDisplacementReject() throws Exception {
        for (String fault : List.of("gap", "duplicate", "teleport", "velocity")) {
            var walker = new Walker(); var motor = walker.start(List.of(p(1.5, .5)), .1);
            switch (fault) {
                case "gap" -> walker.tick += 2;
                case "duplicate" -> { }
                case "teleport" -> { walker.tick++; walker.x += .51; }
                case "velocity" -> { walker.tick++; walker.vx = .36; }
            }
            assertThrows(IOException.class, () -> motor.tick(walker::emit)); assertEquals(1, walker.events);
        }
    }
    @Test void stalledAvatarStopsInsteadOfReplanningThroughUnknownTerrain() throws Exception {
        var walker = new Walker(); var motor = walker.start(List.of(p(1.5, .5)), .1);
        IOException failure = null;
        for (int i = 0; i < 60; i++) {
            walker.tick++; // Input is ignored by this fixture.
            try { assertFalse(motor.tick(walker::emit)); }
            catch (IOException error) { failure = error; break; }
        }
        assertNotNull(failure); assertEquals("NAVIGATION_STALLED", failure.getMessage()); assertTrue(walker.sawForward);
    }
    @Test void emitterFailureDoesNotPerformUnchargedControl() throws Exception {
        var walker = new Walker();
        assertThrows(IOException.class, () -> GameMovement.start(walker, List.of(p(1.5, .5)), p(1.5, .5), .1,
            operation -> { throw new IOException("BUDGET_EXHAUSTED"); }));
        assertEquals(0, walker.history.size());
    }
    @Test void invalidRouteOrMovingStartRejectAndAlreadyReachedTargetEmitsNoWalk() throws Exception {
        var walker = new Walker(); walker.vx = .01;
        assertThrows(IOException.class, () -> walker.start(List.of(p(1.5, .5)), .1)); assertEquals(0, walker.events);
        walker.vx = 0;
        assertThrows(IOException.class, () -> GameMovement.start(walker, List.of(p(1.5, .5)), p(2.5, .5), .1, walker::emit));
        assertThrows(IOException.class, () -> walker.start(List.of(p(1.5, .5)), 0));
        assertTrue(walker.start(List.of(), .1).tick(walker::emit)); assertEquals(0, walker.events);
    }
}
