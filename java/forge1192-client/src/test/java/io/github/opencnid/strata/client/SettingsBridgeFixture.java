package io.github.opencnid.strata.client;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.util.Map;
import java.util.TreeMap;

/** Cross-language test process ONLY. Not included in the client JAR; no game or accounts. */
public final class SettingsBridgeFixture {
    static final class SyntheticRuntime implements SettingsStore.RuntimePort {
        final Thread owner = Thread.currentThread();
        final Map<String, SettingsStore.Binding> bindings = new TreeMap<>();
        SyntheticRuntime(Path profile) throws IOException {
            var persisted = KeyOptions.parse(SettingsFiles.readOptions(profile.resolve("options.txt")));
            bindings.put("fixture:key.mod.action:0", new SettingsStore.Binding("key.mod.action",
                persisted.values().get("key.mod.action"), true));
            bindings.put("minecraft:key.inventory:0", new SettingsStore.Binding("key.inventory",
                persisted.values().get("key.inventory"), false));
        }
        public void requireClientThread() throws IOException {
            if (Thread.currentThread() != owner) throw new IOException("CLIENT_THREAD_REQUIRED");
        }
        public Map<String, SettingsStore.Binding> bindings() { return Map.copyOf(bindings); }
        public void validateKeys(Map<String, String> changes) throws IOException {
            if (!changes.keySet().equals(java.util.Set.of("fixture:key.mod.action:0"))
                    || !java.util.Set.of("key.keyboard.g", "key.keyboard.f13").containsAll(changes.values())) {
                throw new IOException("UNSUPPORTED_PHYSICAL_KEY");
            }
        }
        public void setKeys(Map<String, String> changes) throws IOException {
            requireClientThread(); validateKeys(changes);
            changes.forEach((id, value) -> bindings.put(id, new SettingsStore.Binding(bindings.get(id).translation(), value, true)));
        }
        public void releaseInputs() throws IOException { requireClientThread(); }
    }

    public static void main(String[] args) throws Exception {
        if (args.length != 3) throw new IllegalArgumentException("TEST_ARGUMENTS_REQUIRED");
        Path profile = Path.of(args[0]), journal = Path.of(args[1]), connectionFile = Path.of(args[2]);
        SyntheticRuntime runtime = new SyntheticRuntime(profile);
        try (var store = new SettingsStore(profile, journal, "a".repeat(64), runtime);
                var bridge = new SettingsHttpBridge(new NativeSettingsProtocol(store, runtime)::execute)) {
            SettingsFiles.writeNew(connectionFile, (bridge.descriptor("a".repeat(64)) + "\n").getBytes(StandardCharsets.UTF_8));
            System.out.println("SYNTHETIC_SETTINGS_READY");
            System.out.flush();
            while (System.in.available() == 0) { bridge.drain(); Thread.sleep(5); }
        }
    }
}
