package io.github.opencnid.strata.telemetry;

/** Observe writes to the three immutable-valued pack-mode keys, never their contents. */
public final class ObservedGlobalMap extends ObservedHashMap<String,Object> {
    @Override protected void writing(Object key) {
        if ("packmode".equals(key) || "isExpertMode".equals(key) || "isNormalMode".equals(key))
            SetupHistory.attempt("global_mode_write");
    }
    @Override protected void clearing() { SetupHistory.attempt("global_mode_write"); }
}
