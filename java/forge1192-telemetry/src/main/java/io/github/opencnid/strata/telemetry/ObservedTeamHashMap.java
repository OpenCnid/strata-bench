package io.github.opencnid.strata.telemetry;

/** FTB rank maps and the lazily populated name cache; no reset or disable operation. */
public final class ObservedTeamHashMap<K,V> extends ObservedHashMap<K,V> {
    private volatile boolean armed;
    public ObservedTeamHashMap(boolean armed) { this.armed=armed; }
    public void arm() { armed=true; }
    public boolean armed() { return armed; }
    @Override protected void writing(Object key) { if(armed) SetupHistory.attempt("team_map_write"); }
    @Override protected void clearing() { writing(null); }
}
