package io.github.opencnid.strata.client;

import com.google.gson.JsonObject;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Map;
import java.util.Properties;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.EnumSource;
import static org.junit.jupiter.api.Assertions.*;

class SettingsCrashProbeTest {
    static final String ORIGINAL = "lastServer:synthetic.invalid\r\nbobView:true\r\n"
        + "key_key.mod.action:key.keyboard.unknown\r\nkey_key.inventory:key.keyboard.e\r\nopaque:日本語";

    static String classpath() throws Exception {
        // Gradle's worker launcher classpath need not be its test class loader's classpath.
        return String.join(java.io.File.pathSeparator,
            Path.of(SettingsCrashFixture.class.getProtectionDomain().getCodeSource().getLocation().toURI()).toString(),
            Path.of(SettingsStore.class.getProtectionDomain().getCodeSource().getLocation().toURI()).toString(),
            Path.of(JsonObject.class.getProtectionDomain().getCodeSource().getLocation().toURI()).toString());
    }

    static int child(String mode, Path profile, Path directory) throws Exception {
        Path log = directory.resolve(mode + ".log");
        Process process = new ProcessBuilder(Path.of(System.getProperty("java.home"), "bin", "java.exe").toString(),
            "-cp", classpath(), SettingsCrashFixture.class.getName(), mode, profile.toString(), directory.toString())
            .redirectErrorStream(true).redirectOutput(log.toFile()).start();
        try {
            assertTrue(process.waitFor(10, TimeUnit.SECONDS), "fixture deadline");
            return process.exitValue();
        } finally {
            if (process.isAlive()) {
                process.destroyForcibly();
                assertTrue(process.waitFor(5, TimeUnit.SECONDS), "fixture cleanup");
            }
        }
    }

    static void plan(Path directory, SettingsStore.WriteBoundary boundary) throws IOException {
        Files.writeString(directory.resolve("fault-plan.json"), "{\"schema\":\"strata/SettingsCrashPlan/1\",\"boundary\":\""
            + boundary.name().toLowerCase(java.util.Locale.ROOT) + "\"}");
    }

    @ParameterizedTest @EnumSource(SettingsStore.WriteBoundary.class)
    void abruptJvmAndNewProcessRecoveryPreserveExactPartialStates(SettingsStore.WriteBoundary boundary,
                                                                 @TempDir Path root) throws Exception {
        Path profile = Files.createDirectory(root.resolve("profile")), directory = Files.createDirectory(root.resolve("private"));
        Files.writeString(profile.resolve("options.txt"), ORIGINAL);
        plan(directory, boundary);
        assertEquals(SettingsCrashProbe.EXIT_CODE, child("crash", profile, directory),
            () -> { try { return Files.readString(directory.resolve("crash.log")); } catch (IOException e) { return "log unavailable"; } });
        assertFalse(Files.exists(directory.resolve("unexpected-clean-shutdown.txt")));
        JsonObject reached = SettingsJson.read(Files.readString(directory.resolve("fault-reached.json")));
        JsonObject armed = SettingsJson.read(Files.readString(directory.resolve("armed.json")));
        assertTrue(reached.get("synthetic_runtime").getAsBoolean());
        assertFalse(reached.get("gameplay_capability_qualified").getAsBoolean());
        assertEquals(boundary.name().toLowerCase(java.util.Locale.ROOT), reached.get("boundary").getAsString());
        assertEquals(KeyOptions.sha256(Files.readString(directory.resolve("armed.json"))), reached.get("armed_sha256").getAsString());
        boolean applying = boundary.name().startsWith("APPLY");
        boolean runtimeAfter = boundary == SettingsStore.WriteBoundary.APPLY_RUNTIME_WRITTEN
            || boundary == SettingsStore.WriteBoundary.APPLY_OPTIONS_WRITTEN
            || boundary == SettingsStore.WriteBoundary.ROLLBACK_PREPARED;
        boolean diskAfter = boundary == SettingsStore.WriteBoundary.APPLY_OPTIONS_WRITTEN
            || boundary == SettingsStore.WriteBoundary.ROLLBACK_PREPARED
            || boundary == SettingsStore.WriteBoundary.ROLLBACK_RUNTIME_WRITTEN;
        String phase = applying ? "prepared" : "rollback_prepared";
        JsonObject state = reached.getAsJsonObject("state");
        assertEquals(phase, state.get("active_phase").getAsString());
        assertEquals(runtimeAfter ? SettingsCrashProbe.AFTER : SettingsCrashProbe.BEFORE,
            state.getAsJsonObject("bindings").getAsJsonObject(SettingsCrashFixture.TARGET).get("runtime_value").getAsString());
        assertEquals("key.keyboard.e", state.getAsJsonObject("bindings").getAsJsonObject(SettingsCrashFixture.PROTECTED).get("runtime_value").getAsString());
        String expectedDisk = diskAfter ? ORIGINAL.replace("key.keyboard.unknown", "key.keyboard.f13") : ORIGINAL;
        assertEquals(expectedDisk, Files.readString(profile.resolve("options.txt")));
        assertEquals(expectedDisk, Files.readString(directory.resolve("options-at-fault.txt")));
        assertEquals(ORIGINAL, Files.readString(directory.resolve("options-before.txt")));
        byte[] journalPrefix = Files.readAllBytes(directory.resolve("settings-journal.jsonl"));
        assertEquals(0, child("recover", profile, directory),
            () -> { try { return Files.readString(directory.resolve("recover.log")); } catch (IOException e) { return "log unavailable"; } });
        JsonObject recovered = SettingsJson.read(Files.readString(directory.resolve("recovered.json")));
        assertEquals(phase, recovered.get("initial_phase").getAsString());
        assertEquals("rolled_back", recovered.get("final_phase").getAsString());
        assertEquals(1, recovered.get("runtime_writes").getAsInt());
        assertEquals(armed.getAsJsonObject("before").get("bindings"), recovered.getAsJsonObject("after").get("bindings"));
        assertEquals(ORIGINAL, Files.readString(profile.resolve("options.txt")));
        byte[] fullJournal = Files.readAllBytes(directory.resolve("settings-journal.jsonl"));
        assertArrayEquals(journalPrefix, java.util.Arrays.copyOf(fullJournal, journalPrefix.length));
        var journal = new SettingsJournal(directory.resolve("settings-journal.jsonl"),
            KeyOptions.sha256(profile + "\n" + SettingsCrashFixture.FINGERPRINT), 16777216);
        assertEquals(1, journal.entries().stream().filter(e -> "prepared".equals(e.get("kind").getAsString())).count());
        assertEquals("rolled_back", journal.entries().get(journal.entries().size() - 1).get("kind").getAsString());
    }

    @Test void staleJournalNeverRearmsAndInvalidPlanNeverCreatesOne(@TempDir Path root) throws Exception {
        Path profile = Files.createDirectory(root.resolve("profile")), directory = Files.createDirectory(root.resolve("private"));
        Files.writeString(profile.resolve("options.txt"), ORIGINAL);
        SettingsCrashFixture.Runtime runtime = new SettingsCrashFixture.Runtime(profile.resolve("options.txt"));
        for (String invalid : new String[] {"{}", "{\"schema\":\"strata/SettingsCrashPlan/1\",\"boundary\":\"unknown\"}",
            "{\"schema\":\"strata/SettingsCrashPlan/1\",\"boundary\":\"apply_prepared\",\"eval\":\"no\"}"}) {
            Files.writeString(directory.resolve("fault-plan.json"), invalid);
            assertThrows(IOException.class, () -> SettingsCrashProbe.run(profile, directory, SettingsCrashFixture.FINGERPRINT,
                runtime, SettingsCrashFixture.TARGET, new JsonObject(), true));
            assertFalse(Files.exists(directory.resolve("settings-journal.jsonl")));
        }
        plan(directory, SettingsStore.WriteBoundary.APPLY_PREPARED);
        Files.writeString(directory.resolve("armed.json"), "prior attempt");
        assertEquals("SETTINGS_PROBE_ALREADY_STARTED", assertThrows(IOException.class,
            () -> SettingsCrashProbe.run(profile, directory, SettingsCrashFixture.FINGERPRINT, runtime,
                SettingsCrashFixture.TARGET, new JsonObject(), true)).getMessage());
        assertEquals(0, runtime.writes);
        assertEquals(ORIGINAL, Files.readString(profile.resolve("options.txt")));
    }

    @Test void diagnosticCombinationsRejectBeforeListenerInstallation() {
        Properties properties = new Properties();
        assertDoesNotThrow(() -> ClientSettingsCrashProbe.validateModes(properties, Map.of()));
        properties.setProperty(ClientSettingsCrashProbe.PROPERTY, "explicit-private-root");
        assertDoesNotThrow(() -> ClientSettingsCrashProbe.validateModes(properties, Map.of()));
        for (String incompatible : new String[] {"strata.settingsTransactionDirectory", "strata.settingsBridgeDirectory",
                "strata.settingsDiscoveryDirectory", "strata.gameBridgeDirectory", "strata.privateFrameDirectory", "strata.collisionProbeDirectory"}) {
            properties.setProperty(incompatible, "configured");
            assertThrows(IllegalStateException.class, () -> ClientSettingsCrashProbe.validateModes(properties, Map.of()));
            properties.remove(incompatible);
        }
        assertThrows(IllegalStateException.class, () -> ClientSettingsCrashProbe.validateModes(properties,
            Map.of("STRATA_SETTINGS_DISCOVERY_DIR", "configured")));
    }
}
