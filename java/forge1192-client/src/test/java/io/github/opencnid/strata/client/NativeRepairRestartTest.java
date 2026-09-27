package io.github.opencnid.strata.client;

import com.google.gson.JsonObject;
import java.io.IOException;
import java.nio.file.Path;
import java.util.Map;
import java.util.Properties;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import static org.junit.jupiter.api.Assertions.*;

/** Real durable lane; synthetic body/clock. Reopen is not a process-death attestation. */
class NativeRepairRestartTest {
    static NativeRepairRestart request() throws Exception {
        return new NativeRepairRestart(SettingsJson.read("""
            {"schema":"strata/NativeSettingsRestartRequest/1","transaction_id":"tx","plan_digest":"%s",
             "restart_id":"restart-1","expected_revision":3,"expected_digest":"%s"}
            """.formatted("d".repeat(64), "e".repeat(64))));
    }
    static void admit(GameActionLaneTest.Fixture f, GameActionLane lane) throws Exception {
        f.arm(lane, 1); lane.stopAll(); lane.admitRepair(new NativeRepairAdmission(NativeRepairAdmissionTest.admission(f.time.wall() + 1000)));
    }
    @Test void reopenContinuesOnlyThePendingRepairAndNeverArmsGameplay(@TempDir Path root) throws Exception {
        var f = new GameActionLaneTest.Fixture(root, 100); JsonObject checkpoint; long charged;
        try (var lane = f.open()) {
            admit(f, lane);
            assertDoesNotThrow(() -> lane.repairRestartStage("before_restart"));
            assertThrows(IOException.class, () -> lane.repairRestartStage("after_restart"));
            var prepared = lane.prepareRepairRestart(request());
            checkpoint = prepared.getAsJsonObject("checkpoint").deepCopy(); charged = prepared.get("primitive_events").getAsLong();
            assertEquals(prepared, lane.prepareRepairRestart(request()));
            assertThrows(IOException.class, lane::repairReady);
            assertThrows(IOException.class, () -> lane.continueRepairRestart(checkpoint));
            lane.stopAll(); // Planned shutdown releases cannot erase or extend the handoff.
        }
        f.time.advance(200);
        try (var lane = f.open()) {
            assertThrows(IOException.class, lane::repairReady);
            var continued = lane.continueRepairRestart(checkpoint);
            assertEquals("continued", continued.get("phase").getAsString());
            assertFalse(continued.get("input_resumed").getAsBoolean());
            assertTrue(continued.get("primitive_events").getAsLong() >= charged);
            assertEquals(continued, lane.continueRepairRestart(checkpoint));
            assertDoesNotThrow(lane::repairReady);
            assertDoesNotThrow(() -> lane.repairRestartStage("after_restart"));
            assertThrows(IOException.class, () -> lane.repairRestartStage("before_restart"));
            assertThrows(IOException.class, () -> f.arm(lane, 2));
        }
        try (var lane = f.open()) {
            assertEquals("recovery_required", lane.repairRestartStatus("restart-1").get("phase").getAsString());
            assertThrows(IOException.class, () -> lane.continueRepairRestart(checkpoint));
            assertThrows(IOException.class, lane::repairReady);
        }
    }
    @Test void changedCheckpointAndExpiredOriginalAuthorityCannotContinue(@TempDir Path root) throws Exception {
        var f = new GameActionLaneTest.Fixture(root, 100); JsonObject checkpoint;
        try (var lane = f.open()) { admit(f, lane); checkpoint = lane.prepareRepairRestart(request()).getAsJsonObject("checkpoint").deepCopy(); }
        try (var lane = f.open()) {
            var changed = checkpoint.deepCopy(); changed.addProperty("source_instance", "foreign");
            assertThrows(IOException.class, () -> lane.continueRepairRestart(changed));
            f.time.advance(1001);
            assertThrows(IOException.class, () -> lane.continueRepairRestart(checkpoint));
            assertTrue(lane.health().get("fenced").getAsBoolean());
        }
    }
    @Test void unplannedRecoveryAndFailedRepairCannotPrepareRestart(@TempDir Path root) throws Exception {
        var f = new GameActionLaneTest.Fixture(root, 100);
        try (var lane = f.open()) { admit(f, lane); lane.stopAll(); assertThrows(IOException.class, () -> lane.prepareRepairRestart(request())); }
        try (var lane = f.open()) { assertThrows(IOException.class, () -> lane.prepareRepairRestart(request())); }
    }
    @Test void backwardsClockCannotRestoreTheRestartWindow(@TempDir Path root) throws Exception {
        var f = new GameActionLaneTest.Fixture(root, 100); JsonObject checkpoint;
        try (var lane = f.open()) { admit(f, lane); checkpoint = lane.prepareRepairRestart(request()).getAsJsonObject("checkpoint").deepCopy(); }
        f.time.utc--;
        assertEquals("GAME_CLOCK_ROLLBACK", assertThrows(IOException.class, f::open).getMessage());
    }
    @Test void explicitRestartModeRequiresOwnedRepair() {
        var p = new Properties(); p.setProperty(NativeSettingsEffects.RESTART_PROPERTY, "true");
        assertThrows(IllegalStateException.class, () -> NativeSettingsEffects.validateModes(p, Map.of()));
        p.setProperty(NativeSettingsEffects.REPAIR_PROPERTY, "true"); p.setProperty(NativeSettingsEffects.PROPERTY, "true");
        p.setProperty("strata.gameBridgeDirectory", "private");
        assertDoesNotThrow(() -> NativeSettingsEffects.validateModes(p, Map.of()));
        p.setProperty(NativeSettingsEffects.RESTART_PROPERTY, "yes");
        assertThrows(IllegalStateException.class, () -> NativeSettingsEffects.validateModes(p, Map.of()));
    }
}
