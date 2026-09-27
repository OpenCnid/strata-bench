package io.github.opencnid.strata.telemetry;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class FurnaceLifetimesTest {
    @Test void replacementAtSamePositionAndRetiredObjectGetFreshIdentities() {
        var registry=new FurnaceLifetimes();var tile=new Object();var level=new Object();
        var first=registry.begin(tile,level,"position",100);
        assertEquals(1,first.ordinal);String id=first.id;
        assertSame(first,registry.begin(tile,level,"position",101));assertEquals(2,first.ordinal);
        assertSame(first,registry.retire(tile));assertNull(registry.retire(tile));
        var restored=registry.begin(tile,level,"position",102);
        assertNotEquals(id,restored.id);assertEquals(1,restored.ordinal);
        var replacement=registry.begin(new Object(),level,"position",102);
        assertNotEquals(restored.id,replacement.id);
    }
    @Test void identityRatherThanEqualsProtectsObjectsAndLevels() {
        var registry=new FurnaceLifetimes();Object a=new String("tile"),b=new String("tile"),level=new Object();
        assertNotEquals(registry.begin(a,level,"position",1).id,registry.begin(b,level,"position",1).id);
        assertThrows(IllegalStateException.class,()->registry.begin(a,new Object(),"position",2));
        assertThrows(IllegalStateException.class,()->registry.begin(a,level,"moved",2));
        assertThrows(IllegalStateException.class,()->registry.begin(a,level,"position",1));
        assertThrows(IllegalStateException.class,()->registry.begin(a,level,"position",0));
    }
    @Test void gapsAreRetainedForReaderRatherThanInventingTicks() {
        var registry=new FurnaceLifetimes();var tile=new Object();var level=new Object();
        registry.begin(tile,level,"position",10);var next=registry.begin(tile,level,"position",12);
        assertEquals(2,next.ordinal);assertEquals(12,next.tick);
    }
    @Test void lifetimeAndTickQuotasCannotBeResetByRetirement() {
        var registry=new FurnaceLifetimes();var level=new Object();
        for(int i=0;i<FurnaceLifetimes.MAX_LIFETIMES;i++) {
            var tile=new Object();registry.begin(tile,level,"position",i);registry.retire(tile);
        }
        assertThrows(IllegalStateException.class,()->registry.begin(new Object(),level,"position",100));
        var ticks=new FurnaceLifetimes();var tile=new Object();
        for(int i=0;i<FurnaceLifetimes.MAX_TICKS;i++) ticks.begin(tile,level,"position",i);
        assertThrows(IllegalStateException.class,()->ticks.begin(tile,level,"position",FurnaceLifetimes.MAX_TICKS));
    }
}
