package io.github.opencnid.strata.client;

import java.io.IOException;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;

/** Fixed aim candidates for one already-delivered block; no world lookup or input. */
final class GameBlockTarget {
    static final String POLICY = "observed-outline-centers64-local16/1";
    static final int MAX_BOXES = 64;
    record Box(double minX, double minY, double minZ, double maxX, double maxY, double maxZ) {
        GameVisibility.Point center(GameVisibility.Point origin) {
            return new GameVisibility.Point(origin.x() + (minX + maxX) / 2,
                origin.y() + (minY + maxY) / 2, origin.z() + (minZ + maxZ) / 2);
        }
    }
    static final class UnsupportedShape extends RuntimeException {}
    static final class Builder {
        private final List<Box> boxes = new ArrayList<>();
        void add(double x0, double y0, double z0, double x1, double y1, double z1) {
            if (boxes.size() >= MAX_BOXES) throw new UnsupportedShape();
            for (double v : new double[]{x0,y0,z0,x1,y1,z1}) {
                if (!Double.isFinite(v) || Math.abs(v) > 16) throw new UnsupportedShape();
            }
            if (x0 >= x1 || y0 >= y1 || z0 >= z1) throw new UnsupportedShape();
            boxes.add(new Box(x0,y0,z0,x1,y1,z1));
        }
        List<Box> build() { return List.copyOf(boxes); }
    }
    @FunctionalInterface interface Clip<T> {
        /** Null means no hit on the requested block. Exceptions abort, without another try. */
        T hit(GameVisibility.Point candidate) throws IOException;
    }
    static <T> T select(GameVisibility.Point eye, GameVisibility.Point origin, double reach,
                        List<Box> boxes, Clip<T> clip) throws IOException {
        if (!Double.isFinite(reach) || reach <= 0) throw new IOException("OUT_OF_REACH");
        if (boxes.size() > MAX_BOXES) throw new IOException("MECHANIC_UNSUPPORTED");
        // The builder validates before allocating more than 64 component records.
        var centers = boxes.stream().map(box -> box.center(origin)).distinct()
            .sorted(Comparator.comparingDouble((GameVisibility.Point p) -> eye.distance(p))
                .thenComparingDouble(GameVisibility.Point::x).thenComparingDouble(GameVisibility.Point::y)
                .thenComparingDouble(GameVisibility.Point::z)).toList();
        boolean inReach = false;
        for (var center : centers) {
            if (eye.distance(center) > reach) continue;
            inReach = true;
            T hit = clip.hit(center);
            if (hit != null) return hit;
        }
        throw new IOException(!centers.isEmpty() && !inReach ? "OUT_OF_REACH" : "TARGET_OCCLUDED");
    }
}
