package io.github.opencnid.strata.client;

import java.util.ArrayList;
import java.util.HashSet;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

/** Synthetic geometry only; authentic exact-pack observation conformance is separate. */
class GameVisibilityTest {
    private static GameVisibility.Cell air(int x, int y, int z) {
        return new GameVisibility.Cell(x, y, z, "minecraft:air", true);
    }
    @Test void opaqueModdedBlockStopsReadsBeforeHiddenInventoryOrOre() {
        var reads = new ArrayList<Integer>();
        var cells = GameVisibility.trace(new GameVisibility.Point(.5, .5, .5), new GameVisibility.Point(1, 0, 0), 16,
            (x, y, z) -> { reads.add(x); return x == 2 ? new GameVisibility.Cell(x, y, z, "pack:machine", false) : air(x, y, z); });
        assertEquals(java.util.List.of(0, 1, 2), reads);
        assertEquals("pack:machine", cells.get(2).id());
    }
    @Test void unloadedCoordinatesNegativeCoordinatesAndCracksAreConservative() {
        var origin = new GameVisibility.Point(-.5, -.5, -.5);
        var unknown = GameVisibility.trace(origin, new GameVisibility.Point(-1, 0, 0), 16,
            (x, y, z) -> x < -2 ? null : air(x, y, z));
        assertEquals(java.util.List.of(-1, -2), unknown.stream().map(GameVisibility.Cell::x).toList());
        var crack = GameVisibility.trace(origin, new GameVisibility.Point(-1, -1, 0), 16, GameVisibilityTest::air);
        assertEquals(1, crack.size());
        assertTrue(GameVisibility.trace(origin, new GameVisibility.Point(Double.NaN, 0, 0), 16, GameVisibilityTest::air).isEmpty());
        assertTrue(GameVisibility.trace(origin, new GameVisibility.Point(1, 0, 0), 17, GameVisibilityTest::air).isEmpty());
    }
    @Test void entitiesBeyondWallOrInsideOccupiedCellDoNotPassVisibility() {
        var origin = new GameVisibility.Point(.5, .5, .5);
        GameVisibility.Reader reader = (x, y, z) -> x == 2 ? new GameVisibility.Cell(x, y, z, "pack:glass", false) : air(x, y, z);
        assertTrue(GameVisibility.visible(origin, new GameVisibility.Point(1.5, .5, .5), reader));
        assertFalse(GameVisibility.visible(origin, new GameVisibility.Point(2.5, .5, .5), reader));
        assertFalse(GameVisibility.visible(origin, new GameVisibility.Point(3.5, .5, .5), reader));
        assertFalse(GameVisibility.visible(origin, new GameVisibility.Point(20, .5, .5), reader));
    }
    @Test void fixedCaptureIsUniqueBoundedAndDoesNotLookBelowSolidFloor() {
        var reads = new HashSet<String>();
        var eye = new GameVisibility.Point(.5, 2.62, .5);
        var result = GameVisibility.capture(eye, (x, y, z) -> {
            reads.add(x + "," + y + "," + z);
            assertTrue(y >= 0);
            return y == 0 ? new GameVisibility.Cell(x, y, z, "pack:floor", false) : air(x, y, z);
        });
        assertTrue(result.size() > 128);
        assertTrue(result.size() <= GameVisibility.MAX_CELLS);
        assertEquals(result.size(), result.stream().map(GameVisibility.Cell::key).distinct().count());
        assertTrue(result.stream().allMatch(cell -> cell.center().distance(eye) <= 16));
    }
}
