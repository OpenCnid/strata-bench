package io.github.opencnid.strata.client;

import com.google.gson.JsonObject;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Locale;
import java.util.Map;

/** Explicit private conformance fixture. Never constructed by an ordinary settings store. */
final class SettingsCrashProbe {
    static final int EXIT_CODE = 86;
    static final String TRANSACTION = "operator-crash-1";
    static final String BEFORE = "key.keyboard.unknown", AFTER = "key.keyboard.f13";

    static SettingsStore.WriteBoundary readPlan(Path directory) throws IOException {
        Path path = SettingsFiles.safeExisting(directory.resolve("fault-plan.json"));
        if (!Files.isRegularFile(path) || Files.size(path) > 4096) throw new IOException("SETTINGS_FAULT_PLAN_INVALID");
        byte[] bytes;
        try (var input = Files.newInputStream(path)) { bytes = input.readNBytes(4097); }
        if (bytes.length > 4096) throw new IOException("SETTINGS_FAULT_PLAN_INVALID");
        JsonObject plan = SettingsJson.read(StandardCharsets.UTF_8.newDecoder().decode(ByteBuffer.wrap(bytes)).toString());
        SettingsJson.fields(plan, "schema", "boundary");
        if (!"strata/SettingsCrashPlan/1".equals(SettingsJson.string(plan, "schema"))) {
            throw new IOException("SETTINGS_FAULT_PLAN_INVALID");
        }
        String boundary = SettingsJson.string(plan, "boundary");
        for (var candidate : SettingsStore.WriteBoundary.values()) {
            if (candidate.name().toLowerCase(Locale.ROOT).equals(boundary)) return candidate;
        }
        throw new IOException("SETTINGS_FAULT_PLAN_INVALID");
    }

    private static void write(Path path, JsonObject value) throws IOException {
        byte[] bytes = (value + "\n").getBytes(StandardCharsets.UTF_8);
        if (bytes.length > 524288) throw new IOException("SETTINGS_FAULT_REPORT_TOO_LARGE");
        SettingsFiles.writeNew(path, bytes);
    }

    static void run(Path profile, Path directory, String fingerprint, SettingsStore.RuntimePort runtime,
                    String target, JsonObject ownership, boolean syntheticRuntime) throws IOException {
        runtime.requireClientThread();
        profile = SettingsFiles.safeExisting(profile);
        directory = SettingsFiles.safeExisting(directory);
        if (!Files.isDirectory(profile) || !Files.isDirectory(directory)
                || directory.startsWith(profile) || profile.startsWith(directory)) {
            throw new IOException("SETTINGS_PRIVATE_ROOT_REQUIRED");
        }
        var boundary = readPlan(directory);
        // Any prior start requires recovery, never another forward fixture invocation.
        for (String name : new String[] {"settings-journal.jsonl", "armed.json", "fault-reached.json",
                                         "options-before.txt", "options-at-fault.txt"}) {
            if (Files.exists(directory.resolve(name))) throw new IOException("SETTINGS_PROBE_ALREADY_STARTED");
        }
        var binding = runtime.bindings().get(target);
        if (binding == null || !binding.mutable() || !BEFORE.equals(binding.value())) {
            throw new IOException("SETTINGS_PROBE_REQUIRES_INITIAL_UNBOUND_KEY");
        }
        Path options = profile.resolve("options.txt"), output = directory;
        String original = SettingsFiles.readOptions(options);
        SettingsStore[] active = new SettingsStore[1];
        try (SettingsStore store = new SettingsStore(profile, directory, fingerprint, runtime, 16777216, point -> {
            if (point != boundary) return;
            // Capture actual runtime/file/journal state before abrupt exit, without rollback,
            // shutdown hooks or synthesizing the missing transaction receipt.
            JsonObject report = new JsonObject();
            report.addProperty("schema", "strata/SettingsCrashReached/1");
            report.addProperty("boundary", point.name().toLowerCase(Locale.ROOT));
            report.addProperty("transaction_id", TRANSACTION);
            report.addProperty("synthetic_runtime", syntheticRuntime);
            report.addProperty("operator_development_only", true);
            report.addProperty("gameplay_capability_qualified", false);
            report.addProperty("expected_exit_code", EXIT_CODE);
            report.addProperty("armed_sha256", KeyOptions.sha256(SettingsFiles.readOptions(output.resolve("armed.json"))));
            report.add("state", active[0].inspect());
            SettingsFiles.writeNew(output.resolve("options-at-fault.txt"),
                SettingsFiles.readOptions(options).getBytes(StandardCharsets.UTF_8));
            // report is deliberately last: absence never proves the boundary was reached.
            write(output.resolve("fault-reached.json"), report);
            java.lang.Runtime.getRuntime().halt(EXIT_CODE);
            throw new IOException("SETTINGS_FAULT_HALT_RETURNED");
        })) {
            active[0] = store;
            JsonObject armed = new JsonObject();
            armed.addProperty("schema", "strata/SettingsCrashArmed/1");
            armed.addProperty("boundary", boundary.name().toLowerCase(Locale.ROOT));
            armed.addProperty("transaction_id", TRANSACTION);
            armed.addProperty("synthetic_runtime", syntheticRuntime);
            armed.addProperty("operator_development_only", true);
            armed.addProperty("gameplay_capability_qualified", false);
            armed.addProperty("fingerprint", fingerprint);
            armed.add("ownership", ownership.deepCopy());
            armed.add("before", store.inspect());
            SettingsFiles.writeNew(directory.resolve("options-before.txt"), original.getBytes(StandardCharsets.UTF_8));
            write(directory.resolve("armed.json"), armed);
            store.apply(TRANSACTION, store.snapshot(), Map.of(target, new SettingsStore.Change(BEFORE, AFTER)));
            store.rollback(TRANSACTION);
            throw new IOException("SETTINGS_FAULT_NOT_REACHED");
        }
    }
}
