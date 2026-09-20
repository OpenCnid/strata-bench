package io.github.opencnid.strata.client;

import java.io.IOException;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicLong;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

/** Synthetic geometry. No world, game physics or authentic collision conformance is asserted. */
class GameRouteTest {
    static final GameRoute.Cell AIR = new GameRoute.Cell(List.of());
    static final GameRoute.Cell SOLID = cell(0, 0, 0, 1, 1, 1);
    static GameRoute.Cell cell(double x, double y, double z, double xx, double yy, double zz) {
        return new GameRoute.Cell(List.of(new GameRoute.Box(x, y, z, xx, yy, zz)));
    }
    GameObservedMap.Position p(int x, int y, int z) { return new GameObservedMap.Position(x, y, z); }
    GameVisibility.Point feet(double x, double y, double z) { return new GameVisibility.Point(x, y, z); }
    Map<GameObservedMap.Position, GameRoute.Cell> floor(int min, int max) {
        var map = new HashMap<GameObservedMap.Position, GameRoute.Cell>();
        for (int x = min; x <= max; x++) for (int z = min; z <= max; z++) {
            map.put(p(x, 63, z), SOLID); map.put(p(x, 64, z), AIR); map.put(p(x, 65, z), AIR);
        }
        return map;
    }
    GameRoute route(Map<GameObservedMap.Position, GameRoute.Cell> map) { return new GameRoute(map::get, .6, 1.8, () -> 0); }
    @Test void deterministicShortestLevelRouteAndExactFractionalEndpoint() throws Exception {
        var map = floor(-1, 6); var planner = route(map);
        var start = feet(.5, 64, .5); var target = feet(5.2, 64, .65);
        var first = planner.plan(start, target, .1);
        assertEquals(target, first.get(first.size() - 1)); assertEquals(5, first.size());
        assertEquals(first, planner.plan(start, target, .1));
        assertThrows(UnsupportedOperationException.class, () -> first.clear());
        assertTrue(planner.plan(start, feet(.55, 64, .5), .1).isEmpty());
    }
    @Test void obstacleDetourUsesSupportedCellsAndNoDiagonalCornerCutting() throws Exception {
        var map = floor(-1, 4); map.put(p(1, 64, 0), SOLID);
        var path = route(map).plan(feet(.5, 64, .5), feet(3.5, 64, .5), .1);
        assertTrue(path.stream().anyMatch(point -> point.z() != .5));
        assertTrue(path.stream().noneMatch(point -> point.x() == 1.5 && point.z() == .5));
        // Only corner-diagonal destination is known; there is no swept supported passage.
        var sparse = new HashMap<GameObservedMap.Position, GameRoute.Cell>();
        for (int x = 0; x < 2; x++) for (int y = 63; y <= 65; y++) sparse.put(p(x, y, x), y == 63 ? SOLID : AIR);
        assertThrows(IOException.class, () -> route(sparse).plan(feet(.5, 64, .5), feet(1.5, 64, 1.5), .1));
    }
    @Test void unknownHeadroomMissingFloorAndIntermediateHoleAreBarriers() {
        for (int absentY : new int[]{63, 64, 65}) {
            var map = floor(0, 3);
            for (int z = 0; z <= 3; z++) map.remove(p(1, absentY, z));
            assertEquals("PATH_BLOCKED", assertThrows(IOException.class,
                () -> route(map).plan(feet(.5, 64, .5), feet(2.5, 64, .5), .1)).getMessage());
        }
    }
    @Test void rejectsNarrowGapsLowCeilingsAndFractionalSupportHoles() {
        var ceiling = floor(0, 2); ceiling.put(p(0, 65, 0), cell(0, .7, 0, 1, 1, 1));
        assertThrows(IOException.class, () -> route(ceiling).plan(feet(.5, 64, .5), feet(1.5, 64, .5), .1));
        var narrow = floor(0, 2); narrow.put(p(0, 64, 0), cell(0, 0, 0, .25, 1, 1));
        assertThrows(IOException.class, () -> route(narrow).plan(feet(.5, 64, .5), feet(1.5, 64, .5), .1));
        var hole = floor(0, 2);
        hole.put(p(0, 63, 0), new GameRoute.Cell(List.of(
            new GameRoute.Box(0, 0, 0, .49, 1, 1), new GameRoute.Box(.51, 0, 0, 1, 1, 1))));
        assertThrows(IOException.class, () -> route(hole).plan(feet(.5, 64, .5), feet(1.5, 64, .5), .1));
    }
    @Test void unionOfFacesSupportsContinuousFloorAndSlabsStayAtTheirActualHeight() throws Exception {
        var map = floor(0, 3);
        map.put(p(1, 63, 0), new GameRoute.Cell(List.of(
            new GameRoute.Box(0, 0, 0, .5, 1, 1), new GameRoute.Box(.5, 0, 0, 1, 1, 1))));
        assertFalse(route(map).plan(feet(.5, 64, .5), feet(2.5, 64, .5), .1).isEmpty());
        var slabs = new HashMap<GameObservedMap.Position, GameRoute.Cell>();
        for (int x = 0; x <= 3; x++) {
            slabs.put(p(x, 64, 0), cell(0, 0, 0, 1, .5, 1));
            slabs.put(p(x, 65, 0), AIR); slabs.put(p(x, 66, 0), AIR);
        }
        var path = route(slabs).plan(feet(.5, 64.5, .5), feet(2.5, 64.5, .5), .1);
        assertTrue(path.stream().allMatch(point -> point.y() == 64.5));
        assertEquals("NAVIGATION_LEVEL_REQUIRED", assertThrows(IOException.class,
            () -> route(slabs).plan(feet(.5, 64.5, .5), feet(2.5, 65, .5), .1)).getMessage());
    }
    @Test void boundsInvalidGeometryAndUnderlyingReaderFailureNeverBecomeAPath() {
        var map = floor(0, 3); var planner = route(map); var start = feet(.5, 64, .5);
        assertThrows(IOException.class, () -> planner.plan(start, feet(Double.NaN, 64, 0), .1));
        assertThrows(IOException.class, () -> planner.plan(start, feet(20, 64, .5), .1));
        assertThrows(IOException.class, () -> planner.plan(start, start, Double.NaN));
        assertThrows(IllegalArgumentException.class, () -> new GameRoute(map::get, Double.NaN, 1.8));
        assertThrows(IllegalArgumentException.class, () -> cell(0, 0, 0, 2, 1, 1));
        assertThrows(IllegalArgumentException.class, () -> cell(0, 0, 0, 1, Double.NaN, 1));
        var failure = new GameRoute(position -> { throw new IOException("READER_FAILED"); }, .6, 1.8, () -> 0);
        assertEquals("READER_FAILED", assertThrows(IOException.class, () -> failure.plan(start, start, .1)).getMessage());
    }
    @Test void timeBudgetAndExpansionBoundAbortWithoutReturningPartialRoute() {
        var tick = new AtomicLong(); var reads = new AtomicInteger();
        var planner = new GameRoute(position -> { reads.incrementAndGet(); return SOLID; }, .6, 1.8,
            () -> tick.getAndAdd(GameRoute.MAX_NANOS + 1));
        assertEquals("NAVIGATION_BUDGET_EXHAUSTED", assertThrows(IOException.class,
            () -> planner.plan(feet(.5, 64, .5), feet(2.5, 64, .5), .1)).getMessage());
        assertEquals(0, reads.get());
        var large = floor(-16, 16);
        // A sealed goal inside a large known plane forces bounded search rather than partial success.
        large.put(p(10, 64, 0), SOLID);
        assertEquals("NAVIGATION_BUDGET_EXHAUSTED", assertThrows(IOException.class,
            () -> route(large).plan(feet(.5, 64, .5), feet(10.5, 64, .5), .1)).getMessage());
    }
    @Test void newPlanCannotReusePriorCachedTerrain() throws Exception {
        var map = floor(0, 2); var planner = route(map);
        var start = feet(.5, 64, .5); var target = feet(1.5, 64, .5);
        assertFalse(planner.plan(start, target, .1).isEmpty()); map.clear();
        assertThrows(IOException.class, () -> planner.plan(start, target, .1));
    }
}
