package io.github.opencnid.strata.telemetry;

import java.util.IdentityHashMap;
import java.util.UUID;

/** Actual object identities. Retired objects never resume an old interval. */
final class FurnaceLifetimes {
    static final int MAX_LIFETIMES=64, MAX_TICKS=16384;
    static final class Entry {
        final String id=UUID.randomUUID().toString();
        final Object level;
        final String position;
        long ordinal, tick=-1;
        Entry(Object level,String position) { this.level=level;this.position=position; }
    }
    private final IdentityHashMap<Object,Entry> entries=new IdentityHashMap<>();
    private int issued, ticks;
    Entry begin(Object tile,Object level,String position,long tick) {
        if(tile==null || level==null || position==null || tick<0 || ticks>=MAX_TICKS)
            throw new IllegalStateException("MACHINE_INTERVAL_QUOTA_OR_IDENTITY");
        Entry entry=entries.get(tile);
        if(entry==null) {
            if(issued>=MAX_LIFETIMES) throw new IllegalStateException("MACHINE_LIFETIME_QUOTA");
            entry=new Entry(level,position);entries.put(tile,entry);issued++;
        }
        if(entry.level!=level || !entry.position.equals(position) || tick<=entry.tick)
            throw new IllegalStateException("MACHINE_LIFETIME_DISCONTINUITY");
        entry.ordinal++;entry.tick=tick;ticks++;return entry;
    }
    Entry retire(Object tile) { return entries.remove(tile); }
}
