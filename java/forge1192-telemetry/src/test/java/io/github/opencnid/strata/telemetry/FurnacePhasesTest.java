package io.github.opencnid.strata.telemetry;

import com.google.gson.JsonObject;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class FurnacePhasesTest {
    @Test void completeRequiresAllThreeIndependentSnapshots() {
        var machine=new Object();var phases=new FurnacePhases(machine);var state=new JsonObject();
        for(int i=1;i<=3;i++) {phases.advance(machine,i);state.addProperty("phase",i);phases.snapshot(state);}
        assertTrue(phases.complete(machine));
        assertEquals(1,phases.states.get(0).getAsJsonObject().get("phase").getAsInt());
        assertEquals(3,phases.states.get(2).getAsJsonObject().get("phase").getAsInt());
    }
    @Test void failedValidationHasNoFabricatedSnapshot() {
        var machine=new Object();var phases=new FurnacePhases(machine);
        assertFalse(phases.complete(machine));assertEquals("native_validation_failed",phases.refusal);
        assertEquals(0,phases.states.size());
    }
    @Test void unsupportedStillRequiresOrdinaryPhaseOrder() {
        var machine=new Object();var phases=new FurnacePhases(machine);
        phases.advance(machine,1);phases.refusal="native_profile_unsupported";
        assertThrows(IllegalStateException.class,()->phases.complete(machine));
        phases.advance(machine,2);phases.advance(machine,3);assertFalse(phases.complete(machine));
    }
    @Test void reorderedDuplicatedForeignOrMissingPhasesReject() {
        var machine=new Object();var phases=new FurnacePhases(machine);
        assertThrows(IllegalStateException.class,()->phases.advance(machine,2));
        assertThrows(IllegalStateException.class,()->phases.advance(new Object(),1));
        phases.advance(machine,1);
        assertThrows(IllegalStateException.class,()->phases.advance(machine,1));
        phases.advance(machine,2);phases.advance(machine,3);
        assertThrows(IllegalStateException.class,()->phases.complete(machine));
        assertThrows(IllegalStateException.class,()->phases.advance(machine,4));
        assertThrows(IllegalStateException.class,()->phases.complete(new Object()));
    }
}
