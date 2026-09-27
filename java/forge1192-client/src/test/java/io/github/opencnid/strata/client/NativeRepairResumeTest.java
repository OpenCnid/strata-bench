package io.github.opencnid.strata.client;

import com.google.gson.JsonObject;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Map;
import java.util.Properties;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;
import org.junit.jupiter.api.io.TempDir;
import static org.junit.jupiter.api.Assertions.*;

/** Actual journals/settings coordinator; synthetic body, clock and controller verification. */
class NativeRepairResumeTest {
    static NativeRepairResume decision(GameActionLaneTest.Fixture f, SettingsStore.Snapshot head, String phase) throws Exception {
        JsonObject raw = new JsonObject();
        raw.addProperty("schema", "strata/NativeSettingsResumeDecision/1"); raw.addProperty("policy", NativeRepairResume.POLICY);
        raw.addProperty("resume_id", "resume-1");
        raw.add("worker_plan", NativeRepairAdmissionTest.admission(f.time.wall() + 1000).getAsJsonObject("worker_plan"));
        raw.addProperty("expected_revision", head.revision()); raw.addProperty("expected_digest", head.digest());
        raw.addProperty("completion_phase", phase); raw.addProperty("verification_ref", "cas:sha256:" + "c".repeat(64));
        raw.addProperty("connection_generation", f.port.generation); raw.addProperty("lease_until_unix_ms", f.time.wall() + 900);
        return new NativeRepairResume(raw);
    }
    static void admit(GameActionLaneTest.Fixture f, GameActionLane lane, NativeRepairResume request) throws Exception {
        f.arm(lane, 1); lane.stopAll();
        JsonObject admission = NativeRepairAdmissionTest.admission(request.plan.get("expires_unix_ms").getAsLong());
        admission.add("worker_plan", request.plan.deepCopy()); lane.admitRepair(new NativeRepairAdmission(admission));
    }
    static JsonObject call(SettingsEffectsCoordinator coordinator, NativeRepairResume decision) throws Exception {
        JsonObject request = new JsonObject(); request.addProperty("operation", "settings_resume");
        request.add("args", decision.value); return coordinator.execute(request);
    }
    @ParameterizedTest @ValueSource(strings={"committed", "rolled_back"})
    void completedSettingsResumeOneLeaseWithoutResettingHistory(String phase, @TempDir Path root) throws Exception {
        var helper = new SettingsStoreTest(); var settings = helper.fixture(Files.createDirectory(root.resolve("settings")));
        Path laneRoot = Files.createDirectory(root.resolve("lane")); var f = new GameActionLaneTest.Fixture(laneRoot, 100);
        NativeRepairResume request;
        try (var store = settings.open(); var lane = f.open()) {
            f.arm(lane, 1); f.deliver(lane); lane.accept(f.batch(1,"before",1)); f.start(lane); lane.tick(); lane.stopAll();
            store.apply("tx", store.snapshot(), helper.change());
            if (phase.equals("committed")) {
                var commit = SettingsCommitTest.decision(store.verificationHead("tx")).value.deepCopy();
                commit.addProperty("plan_digest", "d".repeat(64)); store.commit(new SettingsCommitDecision(commit));
            } else store.rollback("tx");
            request = decision(f, store.snapshot(), phase);
            lane.admitRepair(new NativeRepairAdmission(NativeRepairAdmissionTest.admission(f.time.wall()+1000)));
            var coordinator = new SettingsEffectsCoordinator(store, settings.runtime(), lane, null, true, true, false, true);
            var originalAuthority = lane.authority();
            long charged = lane.health().get("attempted_primitive_events").getAsLong();
            assertTrue(call(coordinator, request).get("input_resumed").getAsBoolean());
            assertEquals(originalAuthority, lane.authority());
            assertEquals(1, lane.health().get("epoch").getAsLong());
            assertTrue(lane.health().get("attempted_primitive_events").getAsLong() > charged);
            long after = lane.health().get("attempted_primitive_events").getAsLong();
            assertTrue(call(coordinator, request).get("input_resumed").getAsBoolean());
            assertEquals(after, lane.health().get("attempted_primitive_events").getAsLong());
            assertThrows(IOException.class, () -> lane.accept(f.batch(1,"stale",2)));
            f.deliver(lane); assertThrows(IOException.class, () -> lane.accept(f.batch(1,"old-sequence",1)));
            lane.accept(f.batch(1,"after",2)); f.start(lane); lane.tick();
            assertEquals("emitted", lane.status("after").get("status").getAsString());
            assertEquals("emitted", lane.status("before").get("status").getAsString());
            lane.stopAll(); assertFalse(call(coordinator, request).get("input_resumed").getAsBoolean());
            f.arm(lane, 2);
            assertFalse(call(coordinator, request).get("input_resumed").getAsBoolean());
        }
        try (var lane = f.open()) {
            assertTrue(lane.health().get("fenced").getAsBoolean());
            assertFalse(lane.resumeRepair(request).get("input_resumed").getAsBoolean());
            assertThrows(IOException.class, () -> lane.admitRepair(new NativeRepairAdmission(
                NativeRepairAdmissionTest.admission(request.plan.get("expires_unix_ms").getAsLong()))));
        }
    }
    @ParameterizedTest @ValueSource(strings={"stop", "expired", "generation", "foreign", "extended", "released", "journal"})
    void failedOrChangedRepairCannotResume(String fault, @TempDir Path root) throws Exception {
        var f = new GameActionLaneTest.Fixture(root,100);
        var request = decision(f, new SettingsStore.Snapshot(1,"e".repeat(64)),"rolled_back");
        try(var lane=f.open()) {
            admit(f,lane,request);
            if(fault.equals("stop"))lane.stopAll();
            if(fault.equals("expired"))f.time.advance(1001);
            if(fault.equals("generation"))f.port.generation++;
            var raw=request.value.deepCopy();
            if(fault.equals("foreign"))raw.getAsJsonObject("worker_plan").addProperty("lease_id","foreign");
            if(fault.equals("extended"))raw.addProperty("lease_until_unix_ms", f.time.wall()+2000);
            if(fault.equals("released"))f.port.failRelease=true;
            if(fault.equals("journal"))Files.writeString(root.resolve("game-actions.jsonl"),"corrupt",java.nio.file.StandardOpenOption.APPEND);
            assertThrows(IOException.class,()->lane.resumeRepair(new NativeRepairResume(raw)));
            assertTrue(lane.health().get("fenced").getAsBoolean()); assertFalse(lane.hasResume("tx"));
        }
    }
    @Test void modeAndParserCannotEnableUnscopedResume() throws Exception {
        var p=new Properties();p.setProperty(NativeSettingsEffects.RESUME_PROPERTY,"true");
        assertThrows(IllegalStateException.class,()->NativeSettingsEffects.validateModes(p,Map.of()));
        p.setProperty(NativeSettingsEffects.REPAIR_PROPERTY,"true");p.setProperty(NativeSettingsEffects.PROPERTY,"true");
        p.setProperty("strata.gameBridgeDirectory","private");
        assertDoesNotThrow(()->NativeSettingsEffects.validateModes(p,Map.of()));
        p.setProperty(NativeSettingsEffects.RESUME_PROPERTY,"yes");
        assertThrows(IllegalStateException.class,()->NativeSettingsEffects.validateModes(p,Map.of()));
    }
    @Test void timeSpentDurablyRecordingResumeCannotRefreshItsLease(@TempDir Path root) throws Exception {
        var f = new GameActionLaneTest.Fixture(root,100);
        boolean[] advanced={false};
        var clock = new GameActionLane.Clock() {
            void afterAppend() {
                try {
                    Path log=root.resolve("game-actions.jsonl");
                    if(!advanced[0] && Files.exists(log) && Files.readString(log).contains("\"kind\":\"repair_resumed\"")) {
                        advanced[0]=true;f.time.advance(2000);
                    }
                } catch(IOException error) { throw new java.io.UncheckedIOException(error); }
            }
            public long wall(){afterAppend();return f.time.wall();}
            public long mono(){afterAppend();return f.time.mono();}
        };
        try(var lane=new GameActionLane(root,GameActionLaneTest.PROFILE,f.authority,f.port,clock)) {
            var req=decision(f,new SettingsStore.Snapshot(1,"e".repeat(64)),"rolled_back");admit(f,lane,req);
            assertFalse(lane.resumeRepair(req).get("input_resumed").getAsBoolean());
            assertTrue(advanced[0]);assertTrue(lane.health().get("fenced").getAsBoolean());
            long charged=lane.health().get("attempted_primitive_events").getAsLong();
            assertFalse(lane.resumeRepair(req).get("input_resumed").getAsBoolean());
            assertEquals(charged,lane.health().get("attempted_primitive_events").getAsLong());
        }
    }
}
