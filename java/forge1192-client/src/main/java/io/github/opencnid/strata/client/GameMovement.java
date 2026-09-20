package io.github.opencnid.strata.client;

import java.io.IOException;
import java.util.List;

/** Ordinary forward-key walking, with neutral startup, coasting and charged per-tick decisions. */
final class GameMovement {
    static final String POLICY = "level-forward-coast-neutral8-charged-ticks/1";
    private static final double SETTLED = .003;
    record Frame(long tick, GameVisibility.Point position, GameVisibility.Point velocity,
                 double health, double absorption, boolean interrupted, String context) {}
    interface Port {
        Frame read() throws IOException;
        void corridor(GameVisibility.Point from, GameVisibility.Point to) throws IOException;
        void controls(double yawDegrees, boolean forward) throws IOException;
    }
    static GameActionLane.Motor start(Port port, List<GameVisibility.Point> route,
                                     GameVisibility.Point target, double tolerance,
                                     GameActionLane.Emitter emitter) throws IOException {
        if (route.size() > GameRoute.MAX_WAYPOINTS || !Double.isFinite(tolerance) || tolerance <= 0 || tolerance > 1) {
            throw new IOException("GAME_TARGET_INVALID");
        }
        List<GameVisibility.Point> points = List.copyOf(route);
        Frame initial = port.read(); valid(initial);
        if (speed(initial) > SETTLED || points.isEmpty() && initial.position.distance(target) > tolerance
                || !points.isEmpty() && points.get(points.size() - 1).distance(target) > 1e-7) {
            throw new IOException("NAVIGATION_PRECONDITION_FAILED");
        }
        if (points.isEmpty()) return ignored -> true;
        port.corridor(initial.position, points.get(0));
        emitter.invoke(() -> port.controls(yaw(initial.position, points.get(0)), false));
        return new GameActionLane.Motor() {
            Frame previous = initial;
            int neutral = 8, index, settledTicks;
            int releasedTicks;
            boolean held;
            long progressTick = initial.tick;
            double best = Double.POSITIVE_INFINITY;
            boolean coasting;
            private void drive(GameActionLane.Emitter emit, double facing, boolean forward) throws IOException {
                // Every new press follows eight neutral ticks, clearing vanilla's double-tap sprint window.
                boolean allowed = forward && (held || releasedTicks >= 8);
                emit.invoke(() -> port.controls(facing, allowed));
                held = allowed; releasedTicks = allowed ? 0 : Math.min(8, releasedTicks + 1);
            }
            public boolean tick(GameActionLane.Emitter emit) throws IOException {
                Frame current = port.read(); valid(current);
                if (current.tick != previous.tick + 1 || current.health < previous.health
                        || current.absorption < previous.absorption || !current.context.equals(initial.context)) {
                    throw new IOException("NAVIGATION_STATE_CHANGED");
                }
                if (current.position.distance(previous.position) > .5 || speed(current) > .35
                        || Math.abs(current.position.y() - initial.position.y()) > 1e-5) {
                    throw new IOException("NAVIGATION_DISPLACED");
                }
                GameVisibility.Point next = points.get(index);
                port.corridor(previous.position, current.position);
                port.corridor(current.position, next);
                previous = current;
                double distance = current.position.distance(next), facing = yaw(current.position, next);
                if (neutral > 0) {
                    neutral--; progressTick = current.tick;
                    final double holdFacing = facing;
                    drive(emit, holdFacing, false); return false;
                }
                double allowed = index == points.size() - 1 ? tolerance : .10;
                if (speed(current) <= SETTLED && distance <= allowed) {
                    if (++settledTicks < 2) {
                        final double holdFacing = facing;
                        drive(emit, holdFacing, false); return false;
                    }
                    if (++index == points.size()) return true;
                    // No turn with residual momentum. A new segment must be checked before its first input.
                    next = points.get(index); port.corridor(current.position, next);
                    distance = current.position.distance(next); facing = yaw(current.position, next);
                    coasting = false; settledTicks = 0; best = Double.POSITIVE_INFINITY; progressTick = current.tick;
                } else settledTicks = 0;
                if (distance < best - .025) { best = distance; progressTick = current.tick; }
                if (current.tick - progressTick >= 30) throw new IOException("NAVIGATION_STALLED");
                double vx = current.velocity.x(), vz = current.velocity.z();
                double toward = distance < 1e-9 ? 0 : (vx * (next.x() - current.position.x()) + vz * (next.z() - current.position.z())) / distance;
                // Candidate's admitted surfaces have friction .6; normal ground drag is .6 * .91.
                // This only selects key release timing. It never changes position or velocity.
                double coastDistance = Math.max(0, toward) / (1 - .6 * .91);
                if (distance <= allowed || distance <= coastDistance + Math.min(.05, allowed / 2)) coasting = true;
                if (coasting && speed(current) <= SETTLED && distance > allowed) coasting = false;
                final boolean forward = !coasting && distance > allowed;
                final double turn = facing;
                drive(emit, turn, forward); // Neutral/coasting ticks consume the same local budget.
                return false;
            }
        };
    }
    private static void valid(Frame frame) throws IOException {
        if (frame == null || frame.tick < 0 || frame.position == null || frame.velocity == null || frame.context == null
                || !Double.isFinite(frame.position.x() + frame.position.y() + frame.position.z()
                    + frame.velocity.x() + frame.velocity.y() + frame.velocity.z() + frame.health + frame.absorption)
                || frame.health <= 0 || frame.absorption < 0 || frame.interrupted) throw new IOException("NAVIGATION_INTERRUPTED");
    }
    private static double speed(Frame frame) { return Math.hypot(frame.velocity.x(), frame.velocity.z()); }
    private static double yaw(GameVisibility.Point from, GameVisibility.Point to) {
        return Math.toDegrees(Math.atan2(to.z() - from.z(), to.x() - from.x())) - 90;
    }
}
