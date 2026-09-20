package io.github.opencnid.strata.client;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/** Fixed conservative voxel rays; no registry search, chunk dump or target-adaptive scan. */
final class GameVisibility {
    static final int MAX_CELLS = 16384;
    static final String POLICY = "opaque-voxel-fixed305-radius16/2";
    record Point(double x, double y, double z) {
        Point subtract(Point other) { return new Point(x - other.x, y - other.y, z - other.z); }
        double length() { return Math.sqrt(x * x + y * y + z * z); }
        double distance(Point other) { return subtract(other).length(); }
    }
    record Cell(int x, int y, int z, String id, boolean air) {
        Point center() { return new Point(x + .5, y + .5, z + .5); }
        String key() { return x + "," + y + "," + z; }
    }
    interface Reader { Cell read(int x, int y, int z); }

    static List<Cell> trace(Point origin, Point direction, double radius, Reader read) {
        double length = direction.length();
        if (!Double.isFinite(length) || length == 0 || !Double.isFinite(radius) || radius < 0 || radius > 16) {
            return List.of();
        }
        double[] start = {origin.x, origin.y, origin.z};
        double[] d = {direction.x / length, direction.y / length, direction.z / length};
        int[] cell = new int[3], step = new int[3];
        double[] delta = new double[3], next = new double[3];
        for (int i = 0; i < 3; i++) {
            if (!Double.isFinite(start[i]) || Math.abs(start[i]) > 30000000) return List.of();
            cell[i] = (int) Math.floor(start[i]); step[i] = (int) Math.signum(d[i]);
            delta[i] = d[i] == 0 ? Double.POSITIVE_INFINITY : Math.abs(1 / d[i]);
            next[i] = d[i] == 0 ? Double.POSITIVE_INFINITY
                : ((step[i] > 0 ? cell[i] + 1 : cell[i]) - start[i]) / d[i];
        }
        List<Cell> result = new ArrayList<>();
        for (int n = 0; n < 96; n++) {
            Cell value = read.read(cell[0], cell[1], cell[2]);
            if (value == null) break; // Unknown/unloaded never becomes air.
            result.add(value);
            if (!value.air) break;
            double distance = Math.min(next[0], Math.min(next[1], next[2]));
            if (!Double.isFinite(distance) || distance > radius) break;
            int crossings = 0, axis = 0;
            for (int i = 0; i < 3; i++) if (Math.abs(next[i] - distance) < 1e-9) { crossings++; axis = i; }
            if (crossings != 1) break; // No diagonal crack visibility.
            cell[axis] += step[axis]; next[axis] += delta[axis];
        }
        return result;
    }

    static List<Cell> capture(Point eye, Reader read) {
        Map<String, Cell> cells = new LinkedHashMap<>();
        for (int i = 0; i < 256; i++) {
            double y = 1 - 2 * (i + .5) / 256;
            double a = i * Math.PI * (3 - Math.sqrt(5)), r = Math.sqrt(1 - y * y);
            ray(eye, new Point(Math.cos(a) * r, y, Math.sin(a) * r), read, cells);
        }
        for (int x = -3; x <= 3; x++) for (int z = -3; z <= 3; z++) {
            ray(eye, new Point(x + .13, -2.12, z + .17), read, cells);
        }
        return cells.values().stream().sorted(Comparator.comparingDouble((Cell cell) -> eye.distance(cell.center()))
            .thenComparing(Cell::key)).toList();
    }

    private static void ray(Point eye, Point direction, Reader read, Map<String, Cell> cells) {
        for (Cell cell : trace(eye, direction, 16, read)) {
            if (eye.distance(cell.center()) <= 16) {
                if (!cells.containsKey(cell.key()) && cells.size() >= MAX_CELLS) {
                    throw new IllegalStateException("GAME_SCENE_CAPACITY");
                }
                cells.put(cell.key(), cell);
            }
        }
    }

    static boolean visible(Point eye, Point target, Reader read) {
        double distance = eye.distance(target);
        if (distance > 16) return false;
        if (distance == 0) {
            Cell cell = read.read((int) Math.floor(eye.x), (int) Math.floor(eye.y), (int) Math.floor(eye.z));
            return cell != null && cell.air;
        }
        return trace(eye, target.subtract(eye), distance, read).stream().anyMatch(cell ->
            cell.air && cell.x == Math.floor(target.x) && cell.y == Math.floor(target.y) && cell.z == Math.floor(target.z));
    }
}
