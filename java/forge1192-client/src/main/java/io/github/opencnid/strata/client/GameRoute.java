package io.github.opencnid.strata.client;

import java.io.IOException;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.TreeSet;
import java.util.function.LongSupplier;

/** Fixed level-walking search. Its only terrain input is a filtered collision view. */
final class GameRoute {
    static final String POLICY = "delivered-shapes-level-bfs512-radius16/1";
    static final int MAX_EXPANSIONS = 512, MAX_READS = 4096, MAX_WAYPOINTS = 64;
    static final long MAX_NANOS = 20_000_000;
    private static final double EPS = 1e-7, MARGIN = .025;
    record Box(double minX, double minY, double minZ, double maxX, double maxY, double maxZ) {
        Box {
            if (!Double.isFinite(minX + minY + minZ + maxX + maxY + maxZ)
                    || minX < 0 || minY < 0 || minZ < 0 || maxX > 1 || maxY > 1 || maxZ > 1
                    || minX >= maxX || minY >= maxY || minZ >= maxZ) {
                throw new IllegalArgumentException("NAVIGATION_SHAPE_UNSUPPORTED");
            }
        }
    }
    record Cell(List<Box> boxes) {
        Cell {
            boxes = List.copyOf(boxes);
            if (boxes.size() > 16) throw new IllegalArgumentException("NAVIGATION_SHAPE_UNSUPPORTED");
        }
    }
    interface View { Cell at(GameObservedMap.Position position) throws IOException; }
    private record Node(int x, int z) {}
    private final View view;
    private final double halfWidth, height;
    private final LongSupplier clock;
    private final Map<GameObservedMap.Position, Cell> cache = new HashMap<>();
    private long started;

    GameRoute(View view, double width, double height) { this(view, width, height, System::nanoTime); }
    GameRoute(View view, double width, double height, LongSupplier clock) {
        if (!Double.isFinite(width) || !Double.isFinite(height) || width < .1 || width > 2 || height < .1 || height > 3) {
            throw new IllegalArgumentException("NAVIGATION_BODY_UNSUPPORTED");
        }
        this.view = view; this.halfWidth = width / 2 + MARGIN; this.height = height + MARGIN; this.clock = clock;
    }

    List<GameVisibility.Point> plan(GameVisibility.Point start, GameVisibility.Point target, double tolerance) throws IOException {
        valid(start); valid(target);
        if (!Double.isFinite(tolerance) || tolerance <= 0 || tolerance > 1) throw new IOException("GAME_TARGET_INVALID");
        if (Math.abs(start.y() - target.y()) > EPS) throw new IOException("NAVIGATION_LEVEL_REQUIRED");
        if (start.distance(target) > 16) throw new IOException("NAVIGATION_RANGE");
        cache.clear(); started = clock.getAsLong();
        if (!segment(start, start)) throw new IOException("PATH_BLOCKED");
        if (start.distance(target) <= tolerance) return List.of();
        Node first = new Node((int)Math.floor(start.x()), (int)Math.floor(start.z()));
        var center = point(first, start.y());
        if (!segment(start, center)) throw new IOException("PATH_BLOCKED");
        var queue = new ArrayDeque<Node>(); queue.add(first);
        Map<Node, Node> parent = new LinkedHashMap<>(); parent.put(first, null);
        int expansions = 0;
        int[][] directions = {{1, 0}, {0, 1}, {-1, 0}, {0, -1}};
        while (!queue.isEmpty()) {
            budget();
            if (++expansions > MAX_EXPANSIONS) throw new IOException("NAVIGATION_BUDGET_EXHAUSTED");
            Node current = queue.remove(); var p = point(current, start.y());
            if (p.distance(target) <= 1 && segment(p, target)) {
                var reverse = new ArrayList<GameVisibility.Point>();
                for (Node cursor = current; cursor != null; cursor = parent.get(cursor)) {
                    if (reverse.size() >= MAX_WAYPOINTS - 1) throw new IOException("NAVIGATION_BUDGET_EXHAUSTED");
                    reverse.add(point(cursor, start.y()));
                }
                java.util.Collections.reverse(reverse);
                if (reverse.get(0).distance(start) < EPS) reverse.remove(0);
                if (reverse.isEmpty() || reverse.get(reverse.size() - 1).distance(target) > EPS) reverse.add(target);
                return List.copyOf(reverse);
            }
            for (var direction : directions) {
                Node next = new Node(current.x + direction[0], current.z + direction[1]);
                if (parent.containsKey(next)) continue;
                var nextPoint = point(next, start.y());
                if (nextPoint.distance(start) > 16 || !segment(p, nextPoint)) continue;
                parent.put(next, current); queue.add(next);
            }
        }
        throw new IOException("PATH_BLOCKED");
    }

    private static GameVisibility.Point point(Node node, double y) { return new GameVisibility.Point(node.x + .5, y, node.z + .5); }
    void requireCorridor(GameVisibility.Point from, GameVisibility.Point to) throws IOException {
        valid(from); valid(to);
        if (Math.abs(from.y() - to.y()) > EPS || from.distance(to) > 2) throw new IOException("NAVIGATION_DISPLACED");
        cache.clear(); started = clock.getAsLong();
        if (!segment(from, to)) throw new IOException("PATH_BLOCKED");
    }
    private static void valid(GameVisibility.Point p) throws IOException {
        if (p == null || !Double.isFinite(p.x() + p.y() + p.z()) || Math.abs(p.x()) > 30000000
                || Math.abs(p.z()) > 30000000 || Math.abs(p.y()) > 2048) throw new IOException("GAME_TARGET_INVALID");
    }
    private void budget() throws IOException {
        long elapsed = clock.getAsLong() - started;
        if (elapsed < 0 || elapsed > MAX_NANOS) throw new IOException("NAVIGATION_BUDGET_EXHAUSTED");
    }
    private Cell cell(int x, int y, int z) throws IOException {
        budget(); var key = new GameObservedMap.Position(x, y, z);
        if (!cache.containsKey(key)) {
            if (cache.size() >= MAX_READS) throw new IOException("NAVIGATION_BUDGET_EXHAUSTED");
            cache.put(key, view.at(key)); // Missing/unsupported is a barrier, never inferred air.
        }
        return cache.get(key);
    }

    /** Conservative swept rectangular prism, with continuous support under its full footprint. */
    private boolean segment(GameVisibility.Point a, GameVisibility.Point b) throws IOException {
        double minX = Math.min(a.x(), b.x()) - halfWidth, maxX = Math.max(a.x(), b.x()) + halfWidth;
        double minZ = Math.min(a.z(), b.z()) - halfWidth, maxZ = Math.max(a.z(), b.z()) + halfWidth;
        double feet = a.y(), top = feet + height;
        int floorY = (int)Math.floor(feet - EPS);
        for (int x = (int)Math.floor(minX); x < Math.ceil(maxX - EPS); x++) {
            for (int z = (int)Math.floor(minZ); z < Math.ceil(maxZ - EPS); z++) {
                Cell floor = cell(x, floorY, z);
                if (floor == null || !supported(floor, Math.max(0, minX - x), Math.min(1, maxX - x),
                        Math.max(0, minZ - z), Math.min(1, maxZ - z), feet - floorY)) return false;
                for (int y = (int)Math.floor(feet); y < Math.ceil(top - EPS); y++) {
                    Cell body = cell(x, y, z); if (body == null) return false;
                    for (Box box : body.boxes) {
                        if (box.minX + x < maxX - EPS && box.maxX + x > minX + EPS
                                && box.minY + y < top - EPS && box.maxY + y > feet + EPS
                                && box.minZ + z < maxZ - EPS && box.maxZ + z > minZ + EPS) return false;
                    }
                }
            }
        }
        return true;
    }

    /** Exact rectangular subdivision: corner samples alone could miss a hole in the support. */
    private static boolean supported(Cell cell, double minX, double maxX, double minZ, double maxZ, double y) {
        var xs = new TreeSet<Double>(); var zs = new TreeSet<Double>();
        xs.add(minX); xs.add(maxX); zs.add(minZ); zs.add(maxZ);
        var faces = new ArrayList<Box>();
        for (Box box : cell.boxes) if (Math.abs(box.maxY - y) < EPS) {
            faces.add(box);
            if (box.minX > minX && box.minX < maxX) xs.add(box.minX);
            if (box.maxX > minX && box.maxX < maxX) xs.add(box.maxX);
            if (box.minZ > minZ && box.minZ < maxZ) zs.add(box.minZ);
            if (box.maxZ > minZ && box.maxZ < maxZ) zs.add(box.maxZ);
        }
        var xx = new ArrayList<>(xs); var zz = new ArrayList<>(zs);
        for (int i = 1; i < xx.size(); i++) for (int j = 1; j < zz.size(); j++) {
            double x = (xx.get(i - 1) + xx.get(i)) / 2, z = (zz.get(j - 1) + zz.get(j)) / 2;
            boolean covered = false;
            for (Box box : faces) if (box.minX <= x && box.maxX >= x && box.minZ <= z && box.maxZ >= z) {
                covered = true; break;
            }
            if (!covered) return false;
        }
        return true;
    }
}
