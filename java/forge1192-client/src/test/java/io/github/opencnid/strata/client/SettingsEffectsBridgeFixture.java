package io.github.opencnid.strata.client;

import com.google.gson.JsonObject;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.util.Map;
import java.util.Set;

/** Real production coordinator/HTTP/journals, synthetic body and input. Test classes never enter the client JAR. */
public final class SettingsEffectsBridgeFixture {
    static final class Runtime implements SettingsStore.RuntimePort, GameActionLane.RuntimePort,
            NativeGameProtocol.RuntimePort, SettingsEffectRun.Port, KeyInputSession.Port {
        private final SettingsBridgeFixture.SyntheticRuntime settings;
        private KeyInputSession input;
        private SettingsEffectsCoordinator coordinator;
        private long tick;
        private boolean down, screen;
        Runtime(Path profile) throws IOException { settings = new SettingsBridgeFixture.SyntheticRuntime(profile); }
        public void requireClientThread() throws IOException { settings.requireClientThread(); }
        public Map<String, SettingsStore.Binding> bindings() { return settings.bindings(); }
        public void validateKeys(Map<String, String> changes) throws IOException { settings.validateKeys(changes); }
        public void setKeys(Map<String, String> changes) throws IOException { settings.setKeys(changes); }
        public void releaseInputs() throws IOException { if (input != null) input.cancel(); down = false; }
        public String bodyFingerprint() { return "b".repeat(64); }
        public long connectionGeneration() { return 1; }
        public JsonObject snapshot(String id) throws IOException { throw new IOException("CAPABILITY_MISSING"); }
        public JsonObject observe(String cursor) throws IOException { throw new IOException("CAPABILITY_MISSING"); }
        public void resetObservations() {}
        public void validate(GameBatch batch, JsonObject observation) throws IOException { throw new IOException("CAPABILITY_MISSING"); }
        public GameActionLane.Motor begin(GameBatch batch, JsonObject observation, GameActionLane.Emitter emitter) throws IOException {
            throw new IOException("CAPABILITY_MISSING");
        }
        public boolean settingsEffectsEnabled() { return true; }
        public JsonObject settingsRequest(JsonObject request) throws IOException { return coordinator.execute(request); }
        public void stopSettingsEffects() throws IOException { coordinator.stop(); }
        public void validateBinding(String binding, long hold) throws IOException {
            if (!binding.equals("fixture:key.mod.action:0")) throw new IOException("SETTINGS_CONSUMER_UNQUALIFIED");
        }
        public KeyInputSession start(String binding, long hold, GameActionLane.Emitter ordinary,
                GameActionLane.Emitter safety) throws IOException {
            validateBinding(binding, hold);
            int key = bindings().get(binding).value().equals("key.keyboard.f13") ? 302 : 71;
            input = KeyInputSession.start(this, new KeyInputSession.Request(key, KeyInputSession.Modifier.NONE, hold),
                Set.of(key), ordinary, safety); return input;
        }
        public void validate() throws IOException { requireClientThread(); }
        public long monotonicMillis() { return System.nanoTime() / 1000000; }
        public void event(int key, boolean pressed, int modifiers) { down = pressed; if (pressed) screen = true; }
        public void clear() { down = false; }
        public JsonObject observe() {
            JsonObject value = new JsonObject(); value.addProperty("client_tick", tick);
            value.addProperty("context", screen ? "GUI" : "IN_GAME");
            value.addProperty("screen", screen ? "fixture.Screen" : "none"); value.addProperty("window_active", true);
            value.addProperty("menu_id", 0); value.addProperty("menu_type", "fixture.Menu");
            value.addProperty("x", 1.0); value.addProperty("y", 64.0); value.addProperty("z", 2.0);
            value.addProperty("sneaking", false); value.addProperty("sprinting", false); value.addProperty("using_item", false);
            return value;
        }
    }
    public static void main(String[] args) throws Exception {
        if (args.length != 4) throw new IllegalArgumentException("TEST_ARGUMENTS_REQUIRED");
        Path profile = Path.of(args[0]), settingsRoot = Path.of(args[1]), gameRoot = Path.of(args[2]), descriptor = Path.of(args[3]);
        Runtime runtime = new Runtime(profile);
        var authority = GameActionLane.Authority.read(SettingsJson.read(SettingsFiles.readOptions(gameRoot.resolve("game-authority.json"))));
        try (var store = new SettingsStore(profile, settingsRoot, "d".repeat(64), runtime);
                var lane = new GameActionLane(gameRoot, "a".repeat(64), authority, runtime)) {
            runtime.coordinator = new SettingsEffectsCoordinator(store, runtime, lane, runtime,
                Boolean.getBoolean(NativeSettingsEffects.REPAIR_PROPERTY), Boolean.getBoolean(NativeSettingsEffects.COMMIT_PROPERTY));
            NativeGameProtocol protocol = new NativeGameProtocol(runtime, lane);
            try (var bridge = new SettingsHttpBridge(protocol::execute, protocol)) {
                SettingsFiles.writeNew(descriptor, (bridge.descriptor("a".repeat(64)) + "\n").getBytes(StandardCharsets.UTF_8));
                System.out.println("SYNTHETIC_SETTINGS_EFFECTS_READY"); System.out.flush();
                try {
                    while (System.in.available() == 0) {
                        if (java.nio.file.Files.exists(gameRoot.resolve("fixture-freeze"))) {
                            // Named between-tick fault boundary; never package this test-only hook.
                            SettingsFiles.writeNew(gameRoot.resolve("fixture-frozen"), "frozen\n".getBytes(StandardCharsets.UTF_8));
                            while (System.in.available() == 0) Thread.sleep(5);
                            break;
                        }
                        runtime.tick++; bridge.drain(); runtime.coordinator.tick(); lane.tick(); Thread.sleep(5);
                    }
                } finally { runtime.coordinator.stop(); }
            }
        }
    }
}
