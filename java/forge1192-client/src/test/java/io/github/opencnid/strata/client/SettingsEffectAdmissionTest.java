package io.github.opencnid.strata.client;

import com.google.gson.JsonObject;
import java.io.IOException;
import java.nio.file.Path;
import java.util.Map;
import java.util.Properties;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;
import static org.junit.jupiter.api.Assertions.*;

class SettingsEffectAdmissionTest {
    @Test void enabledModeNeedsItsGameBridgeAndRejectsCompetingWriters() {
        Properties p = new Properties(); p.setProperty(NativeSettingsEffects.PROPERTY, "true");
        assertThrows(IllegalStateException.class, () -> NativeSettingsEffects.validateModes(p, Map.of()));
        p.setProperty("strata.gameBridgeDirectory", "private-root");
        assertDoesNotThrow(() -> NativeSettingsEffects.validateModes(p, Map.of()));
        for (String name : new String[]{"strata.settingsCrashDirectory", "strata.settingsBridgeDirectory",
                "strata.settingsTransactionDirectory", "strata.settingsDiscoveryDirectory", "strata.collisionProbeDirectory"}) {
            p.setProperty(name, "private-other");
            assertThrows(IllegalStateException.class, () -> NativeSettingsEffects.validateModes(p, Map.of())); p.remove(name);
        }
        assertThrows(IllegalStateException.class, () -> NativeSettingsEffects.validateModes(p, Map.of("STRATA_SETTINGS_DISCOVERY_DIR", "other")));
    }
    @Test void ordinaryRuntimeCannotAdmitSettingsOperations(@TempDir Path root) throws Exception {
        var f = new GameActionLaneTest.Fixture(root, 100);
        try (var lane = f.open()) {
            var protocol = new NativeGameProtocol(f.port, lane); var connection = new JsonObject(); connection.addProperty("session_id", "session");
            for (String op : new String[]{"settings_snapshot", "settings_apply", "settings_status", "settings_rollback",
                    "settings_effect_start", "settings_effect_status"}) {
                var request = new NativeGameProtocolTest().request(connection, op);
                assertEquals("CAPABILITY_MISSING", assertThrows(IOException.class,
                    () -> protocol.validate(request, "session", System.currentTimeMillis())).getMessage());
            }
            assertEquals(0, f.port.inputs);
        }
    }
    @ParameterizedTest @ValueSource(ints = {-1, 0, 201, 100000})
    void invalidObservationWindowRejected(int ticks) {
        JsonObject request = SettingsEffectRun.json(new SettingsEffectRun.Request("id", "tx", 2, "a".repeat(64),
            "b".repeat(64), "owner:key:0", "IN_GAME", "before_restart", 50, ticks));
        assertThrows(IOException.class, () -> SettingsEffectRun.Request.read(request));
    }
    @Test void rawKeysUnknownFieldsAndUnboundStagesRejected() {
        var original = SettingsEffectRun.json(new SettingsEffectRun.Request("id", "tx", 2, "a".repeat(64),
            "b".repeat(64), "owner:key:0", "IN_GAME", "before_restart", 50, 2));
        var raw = original.deepCopy(); raw.addProperty("key_code", 302);
        assertThrows(IOException.class, () -> SettingsEffectRun.Request.read(raw));
        for (String field : new String[]{"context", "stage", "expected_digest", "plan_digest"}) {
            var changed = original.deepCopy(); changed.addProperty(field, "unknown");
            assertThrows(IOException.class, () -> SettingsEffectRun.Request.read(changed));
        }
    }
}
