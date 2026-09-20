package io.github.opencnid.strata.client;

import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

/** Synthetic geometry, including the audited installed MayappleBlock dimensions. */
class GameBlockTargetTest {
    static GameVisibility.Point point(double x,double y,double z) { return new GameVisibility.Point(x,y,z); }
    static Vec3 vector(GameVisibility.Point p) { return new Vec3(p.x(),p.y(),p.z()); }
    static List<GameBlockTarget.Box> box(double x0,double y0,double z0,double x1,double y1,double z1) {
        var b=new GameBlockTarget.Builder();b.add(x0,y0,z0,x1,y1,z1);return b.build();
    }
    @Test void auditedMayappleOutlineIsHitBelowTheMissedCellCenter() throws Exception {
        var eye=point(-50.5,8.62,10.5);var origin=point(-49,7,9);
        var actualOutline=new AABB(-49+4/16.0,7,9+4/16.0,-49+13/16.0,7+6/16.0,9+13/16.0);
        assertTrue(actualOutline.clip(vector(eye),new Vec3(-48.5,7.5,9.5)).isEmpty());
        var result=GameBlockTarget.select(eye,origin,4.5,box(4/16.0,0,4/16.0,13/16.0,6/16.0,13/16.0),
            candidate -> actualOutline.clip(vector(eye),vector(candidate)).orElse(null));
        assertNotNull(result);
        assertTrue(result.y>=7 && result.y<=7+6/16.0);
        assertTrue(vector(eye).distanceTo(result)<4.5);
    }
    @Test void fullCubeRetainsCellCenterAndEmptyOutlineNeverInventsAHit() throws Exception {
        var result=GameBlockTarget.select(point(0,2,0),point(-2,0,3),5,
            box(0,0,0,1,1,1),candidate -> candidate);
        assertEquals(point(-1.5,.5,3.5),result);
        var error=assertThrows(IOException.class,()->GameBlockTarget.select(point(0,0,0),point(0,0,0),
            5,List.of(),candidate -> fail("empty shape must not probe")));
        assertEquals("TARGET_OCCLUDED",error.getMessage());
    }
    @Test void disjointComponentsUseStableNearestFirstAndNeverAUnionGap() throws Exception {
        var b=new GameBlockTarget.Builder();
        b.add(.75,0,0,1,1,1);b.add(0,0,0,.25,1,1);
        var probes=new ArrayList<GameVisibility.Point>();
        var hit=GameBlockTarget.select(point(-2,.5,.5),point(0,0,0),5,b.build(),candidate -> {
            probes.add(candidate);return candidate.x()<.5 ? null : candidate;
        });
        assertEquals(List.of(point(.125,.5,.5),point(.875,.5,.5)),probes);
        assertEquals(point(.875,.5,.5),hit);
        var error=assertThrows(IOException.class,()->GameBlockTarget.select(point(-2,.5,.5),point(0,0,0),
            5,b.build(),candidate -> null));
        assertEquals("TARGET_OCCLUDED",error.getMessage());
    }
    @Test void unreachableCandidatesNeverRaycastAndNoReachExtensionOccurs() {
        for (double reach:new double[]{.1,0,-1,Double.NaN,Double.POSITIVE_INFINITY}) {
            var error=assertThrows(IOException.class,()->GameBlockTarget.select(point(10,2,0),point(0,0,0),
                reach,box(0,0,0,1,1,1),candidate -> fail("out of reach must not probe")));
            assertEquals("OUT_OF_REACH",error.getMessage());
        }
    }
    @Test void shapeCollectionBoundsRejectBeforeGrowingAndCopiesAreImmutable() {
        var b=new GameBlockTarget.Builder();
        for (int i=0;i<64;i++) b.add(0,0,0,1,1,1);
        var frozen=b.build();assertEquals(64,frozen.size());
        assertThrows(GameBlockTarget.UnsupportedShape.class,()->b.add(0,0,0,1,1,1));
        assertThrows(UnsupportedOperationException.class,()->frozen.clear());
        for (double invalid:new double[]{Double.NaN,Double.POSITIVE_INFINITY,17}) {
            assertThrows(GameBlockTarget.UnsupportedShape.class,()->new GameBlockTarget.Builder().add(0,0,0,invalid,1,1));
        }
        assertThrows(GameBlockTarget.UnsupportedShape.class,()->new GameBlockTarget.Builder().add(0,0,0,0,1,1));
    }
    @Test void repeatedCentersAreProbedOnceAndProbeFailureAbortsImmediately() {
        var b=new GameBlockTarget.Builder();b.add(0,0,0,1,1,1);b.add(0,0,0,1,1,1);
        b.add(.5,0,0,1,1,1);
        var probes=new ArrayList<GameVisibility.Point>();
        assertThrows(IOException.class,()->GameBlockTarget.select(point(0,0,0),point(0,0,0),5,b.build(),p->{
            probes.add(p);return null;
        }));
        assertEquals(2,probes.size());probes.clear();
        var error=assertThrows(IOException.class,()->GameBlockTarget.select(point(0,0,0),point(0,0,0),5,b.build(),p->{
            probes.add(p);throw new IOException("WORLD_CHANGED");
        }));
        assertEquals("WORLD_CHANGED",error.getMessage());assertEquals(1,probes.size());
    }
}
