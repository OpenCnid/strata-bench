package io.github.opencnid.strata.client;

import com.google.gson.JsonObject;
import java.io.IOException;
import java.nio.file.Path;
import java.util.Map;
import java.util.Properties;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import static org.junit.jupiter.api.Assertions.*;

class NativeRepairAdmissionTest {
    static JsonObject admission(long expires) throws Exception {
        JsonObject value = SettingsJson.read("""
            {"schema":"strata/NativeSettingsRepairAdmission/1","policy":"operator-owned-native-settings-repair/1",
            "worker_plan":{"schema":"strata/WorkerRepairPlan/1","policy":"operator-owned-fixed-repair-pause/1",
            "campaign_id":"campaign","agent_id":"avatar","epoch":1,"lease_id":"lease-1","transaction_id":"tx",
            "plan_digest":"%s","expires_unix_ms":1},"settings_fingerprint":"%s",
            "patch":{"transaction_id":"tx","expected_revision":1,"expected_digest":"%s",
            "changes":{"fixture:key.mod.action:0":{"before":"key.keyboard.g","after":"key.keyboard.f13"}}},
            "effect_bindings":["fixture:key.mod.action:0"]}
            """.formatted("d".repeat(64), "a".repeat(64), "e".repeat(64)));
        value.getAsJsonObject("worker_plan").addProperty("expires_unix_ms", expires); return value;
    }
    @Test void exactLeaseAndFenceRequiredThenArmCannotBypassHold(@TempDir Path root) throws Exception {
        var f = new GameActionLaneTest.Fixture(root, 100);
        try (var lane = f.open()) {
            f.arm(lane, 1); var raw = admission(f.time.wall() + 1000);
            assertEquals("INPUT_RELEASE_REQUIRED", assertThrows(IOException.class,
                () -> lane.admitRepair(new NativeRepairAdmission(raw))).getMessage());
            lane.stopAll();
            var foreign = raw.deepCopy(); foreign.getAsJsonObject("worker_plan").addProperty("lease_id", "foreign");
            assertThrows(IOException.class, () -> lane.admitRepair(new NativeRepairAdmission(foreign)));
            assertEquals("bound", lane.admitRepair(new NativeRepairAdmission(raw)).get("phase").getAsString());
            long charged = lane.health().get("attempted_primitive_events").getAsLong();
            lane.admitRepair(new NativeRepairAdmission(raw));
            assertEquals(charged, lane.health().get("attempted_primitive_events").getAsLong());
            var extended = raw.deepCopy(); extended.getAsJsonObject("worker_plan").addProperty("expires_unix_ms", f.time.wall() + 2000);
            assertThrows(IOException.class, () -> lane.admitRepair(new NativeRepairAdmission(extended)));
            assertEquals("REPAIR_RECOVERY_REQUIRED", assertThrows(IOException.class, () -> f.arm(lane, 2)).getMessage());
        }
    }
    @Test void expiryReleasesAndReopeningNeverRearmsTheOldPlan(@TempDir Path root) throws Exception {
        var f = new GameActionLaneTest.Fixture(root, 100); var raw = admission(f.time.wall() + 1000);
        try (var lane = f.open()) {
            f.arm(lane, 1); lane.stopAll(); lane.admitRepair(new NativeRepairAdmission(raw));
            f.time.advance(1001); int releases = f.port.releases; lane.tick();
            assertTrue(f.port.releases > releases);
            assertEquals("REPAIR_DEADLINE_EXPIRED", lane.repairStatus().get("reason").getAsString());
            assertThrows(IOException.class, () -> lane.beginReconfiguration("late", f.time.wall() + 100));
        }
        try (var reopened = f.open()) {
            assertEquals("recovery_required", reopened.admitRepair(new NativeRepairAdmission(raw)).get("phase").getAsString());
            assertThrows(IOException.class, () -> f.arm(reopened, 2));
        }
    }
    @Test void bodyChangeRevokesTheBoundRepair(@TempDir Path root) throws Exception {
        var f = new GameActionLaneTest.Fixture(root, 100);
        try (var lane = f.open()) {
            f.arm(lane, 1); lane.stopAll(); lane.admitRepair(new NativeRepairAdmission(admission(f.time.wall() + 1000)));
            f.port.generation++; lane.tick();
            assertEquals("REPAIR_FENCE_LOST", lane.repairStatus().get("reason").getAsString());
        }
    }
    @Test void connectionChangeBeforeAdmissionCannotReuseTheOldLease(@TempDir Path root) throws Exception {
        var f = new GameActionLaneTest.Fixture(root, 100);
        try (var lane = f.open()) {
            f.arm(lane, 1); lane.stopAll(); f.port.generation++;
            assertEquals("INPUT_RELEASE_REQUIRED", assertThrows(IOException.class,
                () -> lane.admitRepair(new NativeRepairAdmission(admission(f.time.wall() + 1000)))).getMessage());
            assertFalse(lane.hasRepair());
        }
    }
    @Test void malformedPatchPlanAndEffectBindingsFailBeforeAdmission() throws Exception {
        var raw = admission(10000);
        for (String field : raw.keySet()) {
            var missing = raw.deepCopy(); missing.remove(field);
            assertThrows(IOException.class, () -> new NativeRepairAdmission(missing));
        }
        raw.getAsJsonArray("effect_bindings").add("fixture:key.mod.action:0");
        assertThrows(IOException.class, () -> new NativeRepairAdmission(raw));
        var valid = new NativeRepairAdmission(admission(10000));
        var other = new SettingsEffectRun.Request("effect", "foreign", 1, "e".repeat(64), "d".repeat(64),
            "fixture:key.mod.action:0", "IN_GAME", "before_restart", 50, 1);
        assertThrows(IOException.class, () -> valid.effect(other));
    }
    @Test void ownedRepairModeCannotBeEnabledWithoutTheEffectsProfile() {
        var p = new Properties(); p.setProperty(NativeSettingsEffects.REPAIR_PROPERTY, "true");
        assertThrows(IllegalStateException.class, () -> NativeSettingsEffects.validateModes(p, Map.of()));
        p.setProperty(NativeSettingsEffects.PROPERTY, "true"); p.setProperty("strata.gameBridgeDirectory", "private");
        assertDoesNotThrow(() -> NativeSettingsEffects.validateModes(p, Map.of()));
        p.setProperty(NativeSettingsEffects.REPAIR_PROPERTY, "yes");
        assertThrows(IllegalStateException.class, () -> NativeSettingsEffects.validateModes(p, Map.of()));
    }
}
