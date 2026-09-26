package io.github.opencnid.strata.telemetry;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;

/** One server-thread completion, retaining failure instead of inventing a phase. */
final class FurnacePhases {
    final Object machine;
    final JsonArray states = new JsonArray();
    int phase;
    String refusal;
    FurnacePhases(Object machine) { this.machine = machine; }
    void advance(Object actual, int next) {
        if (actual != machine || next != phase + 1 || next > 3)
            throw new IllegalStateException("MACHINE_CAPTURE_PHASE");
        phase = next;
    }
    void snapshot(JsonObject value) { states.add(value.deepCopy()); }
    boolean complete(Object actual) {
        if (actual != machine || phase != 0 && phase != 3)
            throw new IllegalStateException("MACHINE_CAPTURE_INCOMPLETE");
        if (phase == 0) refusal = "native_validation_failed";
        if (refusal == null && states.size() != 3)
            throw new IllegalStateException("MACHINE_CAPTURE_INCOMPLETE");
        return refusal == null;
    }
}
