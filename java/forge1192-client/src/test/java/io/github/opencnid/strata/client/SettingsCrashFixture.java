package io.github.opencnid.strata.client;

import com.google.gson.JsonObject;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.LinkedHashMap;
import java.util.Map;

/** Disposable actual JVM with deliberately synthetic bindings and ordinary disk options. */
public final class SettingsCrashFixture {
    static final String TARGET = "fixture:key.mod.action:0", PROTECTED = "minecraft:key.inventory:0";
    static final String FINGERPRINT = "b".repeat(64);

    static final class Runtime implements SettingsStore.RuntimePort {
        final Thread owner = Thread.currentThread();
        final Map<String, SettingsStore.Binding> map = new LinkedHashMap<>();
        int writes;
        Runtime(Path options) throws IOException {
            var keys = KeyOptions.parse(SettingsFiles.readOptions(options)).values();
            map.put(TARGET, new SettingsStore.Binding("key.mod.action", keys.get("key.mod.action"), true));
            map.put(PROTECTED, new SettingsStore.Binding("key.inventory", keys.get("key.inventory"), false));
        }
        @Override public void requireClientThread() throws IOException {
            if (Thread.currentThread() != owner) throw new IOException("CLIENT_THREAD_REQUIRED");
        }
        @Override public Map<String, SettingsStore.Binding> bindings() { return Map.copyOf(map); }
        @Override public void validateKeys(Map<String, String> changes) throws IOException {
            if (changes.values().stream().anyMatch(v -> !SettingsCrashProbe.BEFORE.equals(v)
                    && !SettingsCrashProbe.AFTER.equals(v))) throw new IOException("UNSUPPORTED_PHYSICAL_KEY");
        }
        @Override public void setKeys(Map<String, String> changes) throws IOException {
            requireClientThread(); writes++;
            changes.forEach((id, value) -> {
                var prior = map.get(id);
                map.put(id, new SettingsStore.Binding(prior.translation(), value, prior.mutable()));
            });
        }
        @Override public void releaseInputs() throws IOException { requireClientThread(); }
    }

    public static void main(String[] args) throws Exception {
        if (args.length != 3) throw new IOException("FIXTURE_ARGUMENTS_INVALID");
        Path profile = Path.of(args[1]), directory = Path.of(args[2]);
        Runtime runtime = new Runtime(profile.resolve("options.txt"));
        if (args[0].equals("crash")) {
            // A halt must bypass this hook. The test independently checks its absence.
            java.lang.Runtime.getRuntime().addShutdownHook(new Thread(() -> {
                try { Files.writeString(directory.resolve("unexpected-clean-shutdown.txt"), "synthetic hook ran"); }
                catch (IOException ignored) {}
            }));
            SettingsCrashProbe.run(profile, directory, FINGERPRINT, runtime, TARGET, new JsonObject(), true);
        } else if (args[0].equals("recover")) {
            try (SettingsStore store = new SettingsStore(profile, directory, FINGERPRINT, runtime)) {
                JsonObject report = new JsonObject();
                report.addProperty("initial_phase", store.status(SettingsCrashProbe.TRANSACTION).phase());
                report.add("before", store.inspect());
                report.addProperty("final_phase", store.rollback(SettingsCrashProbe.TRANSACTION).phase());
                report.add("after", store.inspect());
                report.addProperty("runtime_writes", runtime.writes);
                // No apply branch: recovery cannot accidentally dispatch the forward write.
                SettingsFiles.writeNew(directory.resolve("recovered.json"),
                    (report + "\n").getBytes(java.nio.charset.StandardCharsets.UTF_8));
            }
        } else throw new IOException("FIXTURE_ARGUMENTS_INVALID");
    }
}
