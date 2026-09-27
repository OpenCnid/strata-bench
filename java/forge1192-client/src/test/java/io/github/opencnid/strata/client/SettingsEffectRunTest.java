package io.github.opencnid.strata.client;

import com.google.gson.JsonObject;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import static org.junit.jupiter.api.Assertions.*;

/** Real settings files and game journal; deliberately synthetic body, clock, input and GUI. */
class SettingsEffectRunTest {
    static final class Fixture implements AutoCloseable, SettingsEffectRun.Port, KeyInputSession.Port {
        final SettingsStoreTest.Fixture settings;
        final SettingsStore store;
        final GameActionLaneTest.Fixture game;
        final GameActionLane lane;
        final List<Boolean> inputs = new ArrayList<>();
        boolean down;
        String context = "IN_GAME";
        Fixture(Path root, int budget) throws Exception {
            this(root, budget, false);
        }
        Fixture(Path root, int budget, boolean currentWall) throws Exception {
            settings = new SettingsStoreTest().fixture(root); store = settings.open();
            game = new GameActionLaneTest.Fixture(Files.createDirectory(root.resolve("game")), budget);
            if (currentWall) game.time.utc = System.currentTimeMillis();
            lane = new GameActionLane(game.root, GameActionLaneTest.PROFILE,
                new GameActionLane.Authority("campaign", "avatar", GameActionLaneTest.CAP, GameActionLaneTest.BODY,
                    game.time.wall() + 60000, budget), game.port, game.time);
            store.apply("transaction", store.snapshot(), Map.of(SettingsStoreTest.ID,
                new SettingsStore.Change(SettingsStoreTest.BEFORE, SettingsStoreTest.AFTER)));
        }
        SettingsEffectRun run(String id) throws IOException {
            var head = store.verificationHead("transaction");
            return new SettingsEffectRun(new SettingsEffectRun.Request(id, "transaction", head.revision(), head.digest(),
                "d".repeat(64), SettingsStoreTest.ID, "IN_GAME", "before_restart", 50, 2), store, lane, this);
        }
        public void validateBinding(String id, long hold) throws IOException {
            if (!id.equals(SettingsStoreTest.ID)) throw new IOException("SETTINGS_CONSUMER_UNQUALIFIED");
        }
        public JsonObject observe() {
            JsonObject value = new JsonObject(); value.addProperty("context", context); value.addProperty("down", down);
            value.addProperty("synthetic", true); return value;
        }
        public KeyInputSession start(String id, long hold, GameActionLane.Emitter ordinary,
                GameActionLane.Emitter safety) throws IOException {
            return KeyInputSession.start(this, new KeyInputSession.Request(302, KeyInputSession.Modifier.NONE, hold),
                Set.of(302), ordinary, safety);
        }
        public void validate() {}
        public long monotonicMillis() { return game.time.mono(); }
        public void event(int key, boolean pressed, int modifiers) { inputs.add(pressed); down = pressed; }
        public void clear() { down = false; }
        public void close() throws Exception { try { store.close(); } finally { lane.close(); } }
    }
    private static SettingsEffectRun baseline(Fixture f, String id, SettingsStore.Snapshot head) throws IOException {
        return new SettingsEffectRun(new SettingsEffectRun.Request(id, null, head.revision(), head.digest(),
            "d".repeat(64), SettingsStoreTest.ID, "IN_GAME", "baseline", 50, 2), f.store, f.lane, f);
    }
    @Test void baselineObservesRestoredMapWithoutCreatingAPatch(@TempDir Path root) throws Exception {
        try (var f = new Fixture(root, 100)) {
            f.store.rollback("transaction");
            var head = f.store.snapshot();
            String options = Files.readString(f.settings.options());
            var run = baseline(f, "baseline", head);
            run.start(f.game.time.wall() + 1000);
            f.game.time.advance(50); run.tick(); run.tick();
            assertEquals("observed", run.status().get("state").getAsString());
            assertTrue(run.status().getAsJsonObject("request").get("transaction_id").isJsonNull());
            assertEquals(head, f.store.snapshot());
            assertEquals(options, Files.readString(f.settings.options()));
            assertEquals("rolled_back", f.store.status("transaction").phase());
            assertEquals(List.of(true, false), f.inputs);
            assertTrue(f.lane.health().get("fenced").getAsBoolean());
            assertTrue(f.lane.health().get("attempted_primitive_events").getAsLong() > 0);
        }
    }
    @Test void baselineCannotBypassAPendingTransaction(@TempDir Path root) throws Exception {
        try (var f = new Fixture(root, 100)) {
            var head = f.store.verificationHead("transaction");
            assertThrows(IOException.class, () -> baseline(f, "baseline", head));
            assertTrue(f.inputs.isEmpty());
        }
    }
    @Test void baselineHeadChangeReleasesInputAndCannotPass(@TempDir Path root) throws Exception {
        try (var f = new Fixture(root, 100)) {
            f.store.rollback("transaction");
            var run = baseline(f, "baseline", f.store.snapshot());
            run.start(f.game.time.wall() + 1000);
            f.settings.runtime().external(SettingsStoreTest.PROTECTED, "key.keyboard.g");
            assertThrows(IOException.class, run::tick);
            assertEquals("unknown", run.status().get("state").getAsString());
            assertFalse(f.down);
        }
    }
    @Test void fullPendingTransactionToObservedRunStaysUnverifiedAndRequiresFreshGameEpoch(@TempDir Path root) throws Exception {
        try (var f = new Fixture(root, 100)) {
            f.game.arm(f.lane, 1); f.game.deliver(f.lane);
            var run = f.run("effect"); run.start(f.game.time.wall() + 1000);
            assertThrows(IOException.class, () -> f.game.arm(f.lane, 2));
            assertThrows(IOException.class, () -> f.lane.accept(f.game.batch(1, "interloper", 1)));
            run.tick(); f.game.time.advance(50); f.context = "GUI"; run.tick(); run.tick();
            var result = run.status(); assertEquals("observed", result.get("state").getAsString());
            assertFalse(result.get("verified").getAsBoolean()); assertFalse(result.get("committed").getAsBoolean());
            assertEquals(6, result.getAsJsonArray("observations").size()); assertEquals(List.of(true, false), f.inputs);
            assertEquals("strata/NativeSettingsEffects/4", result.get("schema").getAsString());
            var observations = result.getAsJsonArray("observations");
            assertEquals("input_release", observations.get(3).getAsJsonObject().get("phase").getAsString());
            assertEquals("released", observations.get(4).getAsJsonObject().get("phase").getAsString());
            assertTrue(observations.get(3).getAsJsonObject().getAsJsonObject("value").get("clear_confirmed").getAsBoolean());
            String journal = Files.readString(f.game.root.resolve("game-actions.jsonl"));
            assertTrue(journal.indexOf("NativeSettingsEffectAdmission/2") < journal.indexOf("reconfiguration_primitive"));
            assertTrue(journal.contains("plan_digest")); assertTrue(journal.contains("settings_fingerprint"));
            assertEquals("applied_pending_verification", f.store.status("transaction").phase());
            assertTrue(f.lane.health().get("fenced").getAsBoolean()); f.game.arm(f.lane, 2);
            assertThrows(IOException.class, () -> f.run("effect").start(f.game.time.wall() + 1000));
            assertEquals(List.of(true, false), f.inputs);
            assertEquals("rolled_back", f.store.rollback("transaction").phase());
        }
    }
    @Test void missingContextCannotEmitOrManufacturePass(@TempDir Path root) throws Exception {
        try (var f = new Fixture(root, 100)) {
            var run = f.run("effect"); f.context = "CHAT";
            assertEquals("SETTINGS_CONTEXT_UNVERIFIED", assertThrows(IOException.class,
                () -> run.start(f.game.time.wall() + 1000)).getMessage());
            assertEquals("refused", run.status().get("state").getAsString()); assertTrue(f.inputs.isEmpty());
        }
    }
    @Test void foreignRuntimeChangeStopsHeldInput(@TempDir Path root) throws Exception {
        try (var f = new Fixture(root, 100)) {
            var run = f.run("effect"); run.start(f.game.time.wall() + 1000);
            f.settings.runtime().external(SettingsStoreTest.PROTECTED, "key.keyboard.g");
            assertThrows(IOException.class, run::tick); assertFalse(f.down);
            assertEquals("unknown", run.status().get("state").getAsString());
            assertThrows(IOException.class, () -> f.store.rollback("transaction"));
        }
    }
    @Test void diskEditCannotBeHiddenByUnchangedRuntime(@TempDir Path root) throws Exception {
        try (var f = new Fixture(root, 100)) {
            var run = f.run("effect");
            Files.writeString(f.settings.options(), f.settings.text().replace("renderDistance:12", "renderDistance:13"));
            assertThrows(IOException.class, () -> run.start(f.game.time.wall() + 1000));
            assertTrue(f.inputs.isEmpty());
        }
    }
    @Test void expiredRunReleasesAndPreservesConsumedCharges(@TempDir Path root) throws Exception {
        try (var f = new Fixture(root, 100)) {
            var run = f.run("effect"); run.start(f.game.time.wall() + 100); f.game.time.advance(101);
            assertThrows(IOException.class, run::tick); assertEquals(List.of(true, false), f.inputs); assertFalse(f.down);
            assertTrue(f.lane.health().get("attempted_primitive_events").getAsLong() >= 5);
            assertEquals("unknown", run.status().get("state").getAsString());
        }
    }
    @Test void exhaustedOrdinaryBudgetCannotPreventSafetyCleanup(@TempDir Path root) throws Exception {
        try (var f = new Fixture(root, 5)) {
            var run = f.run("effect"); run.start(f.game.time.wall() + 1000);
            assertThrows(IOException.class, run::tick); assertFalse(f.down);
            assertEquals(List.of(true, false), f.inputs); assertEquals(5, f.lane.health().get("attempted_primitive_events").getAsLong());
        }
    }
    @Test void generationChangeCannotContinueAcrossBodies(@TempDir Path root) throws Exception {
        try (var f = new Fixture(root, 100)) {
            var run = f.run("effect"); run.start(f.game.time.wall() + 1000); f.game.port.generation++;
            assertThrows(IOException.class, run::tick); assertFalse(f.down); assertEquals(List.of(true, false), f.inputs);
        }
    }
    @Test void screenOpeningIsRawObservationNotAConfirmedEffect(@TempDir Path root) throws Exception {
        try (var f = new Fixture(root, 100)) {
            var run = f.run("effect"); run.start(f.game.time.wall() + 1000);
            JsonObject opening = new JsonObject(); opening.addProperty("cancelled_at_observer", true);
            run.screenChanged(opening); run.cancel();
            assertEquals("screen_opening", run.status().getAsJsonArray("observations").get(2).getAsJsonObject().get("phase").getAsString());
            assertFalse(run.status().get("verified").getAsBoolean()); assertFalse(f.down);
        }
    }
    @Test void interruptedJournalRequiresExplicitRecoveryAndDoesNotRenewDeadline(@TempDir Path root) throws Exception {
        var f = new GameActionLaneTest.Fixture(root, 100);
        long charged;
        try (var lane = f.open()) {
            lane.beginReconfiguration("interrupted", f.time.wall() + 1000);
            lane.reconfigurationEmit("interrupted", false, () -> f.port.inputs++);
            charged = lane.health().get("attempted_primitive_events").getAsLong();
        }
        try (var lane = f.open()) {
            assertEquals("interrupted", lane.interruptedReconfiguration());
            assertThrows(IOException.class, () -> lane.reconfigurationReady("interrupted"));
            assertThrows(IOException.class, () -> f.arm(lane, 1));
            assertTrue(lane.health().get("attempted_primitive_events").getAsLong() >= charged);
            lane.endReconfiguration("interrupted", "unknown"); f.arm(lane, 1);
            assertThrows(IOException.class, () -> lane.beginReconfiguration("interrupted", f.time.wall() + 1000));
            assertEquals(1, f.port.inputs);
        }
    }
    @Test void completedJournalReopensWithoutReplayingInput(@TempDir Path root) throws Exception {
        var f = new GameActionLaneTest.Fixture(root, 100);
        try (var lane = f.open()) {
            lane.beginReconfiguration("done", f.time.wall() + 1000);
            lane.reconfigurationEmit("done", false, () -> f.port.inputs++);
            lane.endReconfiguration("done", "completed");
        }
        try (var lane = f.open()) {
            assertNull(lane.interruptedReconfiguration()); f.arm(lane, 1);
            assertThrows(IOException.class, () -> lane.beginReconfiguration("done", f.time.wall() + 1000));
            assertEquals(1, f.port.inputs);
        }
    }
    @Test void stopAllInvalidatesSettlingAsWellAsHeldInput(@TempDir Path root) throws Exception {
        try (var f = new Fixture(root, 100)) {
            var run = f.run("effect"); run.start(f.game.time.wall() + 1000);
            f.game.time.advance(50); run.tick(); f.lane.stopAll();
            assertThrows(IOException.class, run::tick);
            assertEquals("unknown", run.status().get("state").getAsString()); assertFalse(f.down);
        }
    }
    @Test void releaseDelayCannotExtendDeclaredDeadline(@TempDir Path root) throws Exception {
        var f = new GameActionLaneTest.Fixture(root, 100);
        try (var lane = f.open()) {
            f.port.customRelease = () -> f.time.advance(500);
            lane.beginReconfiguration("effect", f.time.wall() + 100);
            assertThrows(IOException.class, () -> lane.reconfigurationEmit("effect", false, () -> f.port.inputs++));
            assertEquals(0, f.port.inputs); lane.endReconfiguration("effect", "unknown");
        }
    }
    @Test void rolledBackTransactionCannotAuthorizeEffects(@TempDir Path root) throws Exception {
        try (var f = new Fixture(root, 100)) {
            f.store.rollback("transaction"); assertThrows(IOException.class, () -> f.run("effect"));
            assertTrue(f.inputs.isEmpty());
        }
    }
    @Test void realHttpRouteUsesAuthClientDispatchAndDoesNotReplayInput(@TempDir Path root) throws Exception {
        var http = new NativeGameProtocolTest();
        try (var f = new Fixture(root, 100, true)) {
            SettingsEffectRun[] run = {null};
            var port = new NativeGameProtocolTest.Port() {
                public boolean settingsEffectsEnabled() { return true; }
                public JsonObject settingsRequest(JsonObject request) throws IOException {
                    requireClientThread();
                    if (request.get("operation").getAsString().equals("settings_effect_start")) {
                        run[0] = new SettingsEffectRun(SettingsEffectRun.Request.read(request.getAsJsonObject("args")), f.store, f.lane, f);
                        run[0].start(request.get("deadline_unix_ms").getAsLong());
                    }
                    return run[0].status();
                }
            };
            var protocol = new NativeGameProtocol(port, f.lane);
            try (var bridge = new SettingsHttpBridge(protocol::execute, protocol)) {
                var connection = bridge.descriptor(GameActionLaneTest.PROFILE);
                var request = http.request(connection, "settings_effect_start");
                request.add("args", f.run("http-effect").status().getAsJsonObject("request"));
                assertEquals(401, http.send(connection, "POST", "/v1/game", request.toString(), false).statusCode());
                assertEquals(202, http.send(connection, "POST", "/v1/game", request.toString(), true).statusCode());
                assertTrue(f.inputs.isEmpty()); bridge.drain(); assertEquals(List.of(true), f.inputs);
                f.game.time.advance(50); run[0].tick(); run[0].tick();
                assertEquals(200, http.send(connection, "POST", "/v1/game", request.toString(), true).statusCode());
                bridge.drain(); assertEquals(List.of(true, false), f.inputs);
                var status = http.request(connection, "settings_effect_status");
                status.getAsJsonObject("args").addProperty("id", "http-effect");
                assertEquals(202, http.send(connection, "POST", "/v1/game", status.toString(), true).statusCode()); bridge.drain();
                var response = http.send(connection, "GET", "/v1/game/" + status.get("request_id").getAsString(), null, true);
                assertTrue(response.body().contains("\"state\":\"observed\""));
                assertTrue(response.body().contains("\"verified\":false"));
            }
        }
    }
    @Test void ownershipMetadataChangeCannotReuseAKeymapHead(@TempDir Path root) throws Exception {
        try (var f = new Fixture(root, 100)) {
            var run = f.run("effect");
            f.settings.runtime().map.put(SettingsStoreTest.ID,
                new SettingsStore.Binding("key.mod.action", SettingsStoreTest.AFTER, false));
            assertThrows(IOException.class, () -> run.start(f.game.time.wall() + 1000));
            assertTrue(f.inputs.isEmpty());
        }
    }
}
