package io.github.opencnid.strata.client;

import com.google.gson.JsonObject;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.HashMap;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import static org.junit.jupiter.api.Assertions.*;

/** Real journal/locks with synthetic clocks and motors, not Minecraft conformance. */
class GameActionLaneTest {
    static final String CAP = "c".repeat(64), BODY = "b".repeat(64), PROFILE = "a".repeat(64);
    @Test void mapPromotionFollowsDurableDeliveryAndDuplicateDoesNotRepeatIt(@TempDir Path root) throws Exception {
        var f = new Fixture(root, 100);
        try (var lane = f.open()) {
            f.arm(lane, 1); assertEquals(0, f.port.delivered);
            f.deliver(lane); assertEquals(1, f.port.delivered);
            f.deliver(lane); assertEquals(1, f.port.delivered);
        }
    }
    @Test void failedDeliveryJournalCannotPromotePlannerMap(@TempDir Path root) throws Exception {
        var f = new Fixture(root, 100);
        try (var lane = f.open()) {
            f.arm(lane, 1);
            Files.writeString(root.resolve("game-actions.jsonl"), "corruption", java.nio.file.StandardOpenOption.APPEND);
            assertThrows(IOException.class, () -> f.deliver(lane));
            assertEquals(0, f.port.delivered); assertEquals(0, f.port.inputs);
        }
    }
    @Test void failedMapPromotionFencesInsteadOfAcknowledgingActionAuthority(@TempDir Path root) throws Exception {
        var f = new Fixture(root, 100);
        try (var lane = f.open()) {
            f.arm(lane, 1); f.port.failDelivery = true;
            assertThrows(IOException.class, () -> f.deliver(lane));
            assertTrue(lane.health().get("fenced").getAsBoolean());
            assertEquals("GAME_DELIVERY_UNAVAILABLE", lane.health().get("reason").getAsString());
            assertThrows(IOException.class, () -> lane.accept(f.batch(1, "action", 1)));
            assertEquals(0, f.port.inputs);
        }
    }
    @Test void authorityReadReturnsTheLoadedImmutableScopeWithoutArming(@TempDir Path root) throws Exception {
        var f = new Fixture(root, 100);
        try (var lane = f.open()) {
            JsonObject value = lane.authority();
            assertEquals(f.authority, GameActionLane.Authority.read(value));
            value.addProperty("agent_id", "changed-copy");
            assertEquals("avatar", lane.authority().get("agent_id").getAsString());
            assertEquals(0, f.port.releases);
            assertTrue(lane.health().get("fenced").getAsBoolean());
        }
    }
    static final class Time implements GameActionLane.Clock {
        long utc = 1789732800000L, elapsed;
        public long wall() { return utc; }
        public long mono() { return elapsed; }
        void advance(long ms) { utc += ms; elapsed += ms; }
    }
    static final class Port implements GameActionLane.RuntimePort, NativeGameProtocol.RuntimePort {
        interface Begin { GameActionLane.Motor create(GameActionLane.Emitter emitter) throws IOException; }
        Begin customMotor;
        GameActionLane.Operation customRelease;
        final Time time; final Path root; final Thread owner = Thread.currentThread();
        final Map<String, Long> snapshots = new HashMap<>();
        String body = BODY; long generation = 1, revision = 1; int inputs, releases;
        boolean hold, emitEachTick, failAfterInput, failRelease, failDelivery;
        int delivered;
        Port(Time time, Path root) { this.time = time; this.root = root; }
        public void requireClientThread() throws IOException {
            if (owner != Thread.currentThread()) throw new IOException("CLIENT_THREAD_REQUIRED");
        }
        public String bodyFingerprint() { return body; }
        public long connectionGeneration() { return generation; }
        public JsonObject observe(String cursor) throws IOException { return snapshot(cursor); }
        public JsonObject snapshot(String id) throws IOException {
            Long captured = snapshots.get(id);
            if (captured == null) throw new IOException("STALE_OBSERVATION");
            JsonObject value = new JsonObject(), state = new JsonObject();
            value.addProperty("snapshot_id", id); value.addProperty("state_revision", revision);
            value.addProperty("age_ms", time.mono() - captured); state.addProperty("synthetic", true);
            value.add("state", state); return value;
        }
        public void resetObservations() { snapshots.clear(); }
        public void delivered(JsonObject snapshot) throws IOException {
            assertTrue(Files.readString(root.resolve("game-actions.jsonl")).contains("\"kind\":\"delivery\""));
            delivered++;
            if (failDelivery) throw new IOException("INJECTED_DELIVERY_FAILURE");
        }
        public void validate(GameBatch batch, JsonObject snapshot) throws IOException {
            if (batch.revision != revision) throw new IOException("REVISION_CONFLICT");
        }
        public GameActionLane.Motor begin(GameBatch batch, JsonObject snapshot, GameActionLane.Emitter emit) throws IOException {
            if (customMotor != null) return customMotor.create(emit);
            emit.invoke(() -> {
                String journal = Files.readString(root.resolve("game-actions.jsonl"));
                assertTrue(journal.contains("\"kind\":\"intent\""));
                assertTrue(journal.contains("\"kind\":\"primitive\""));
                inputs++;
                if (failAfterInput) throw new IOException("INJECTED_AFTER_EFFECT");
            });
            return emitter -> {
                if (emitEachTick) emitter.invoke(() -> inputs++);
                return !hold;
            };
        }
        public void releaseInputs() throws IOException {
            releases++; if (customRelease != null) customRelease.run();
            if (failRelease) throw new IOException("INJECTED_RELEASE_FAILURE");
        }
    }
    static final class Fixture {
        final Path root; final Time time = new Time(); final Port port;
        final GameActionLane.Authority authority;
        Fixture(Path root, long limit) {
            this.root = root; port = new Port(time, root);
            authority = new GameActionLane.Authority("campaign", "avatar", CAP, BODY, time.wall() + 60000, limit);
        }
        GameActionLane open() throws IOException { return new GameActionLane(root, PROFILE, authority, port, time); }
        void arm(GameActionLane lane, long epoch) throws IOException {
            lane.arm(epoch, "lease-" + epoch, time.wall() + 6000, lane.health().get("fence_token").getAsString());
        }
        void deliver(GameActionLane lane) throws IOException {
            port.snapshots.put("snapshot", time.mono()); lane.deliver("observation", "snapshot", port.revision);
        }
        JsonObject batch(long epoch, String id, long seq) throws IOException {
            JsonObject value = SettingsJson.readGame("""
                {"schema":"mcbench/ActionBatch/1","is_example":false,"campaign_id":"campaign","epoch":1,"seq":1,
                 "recorded_at":"2026-09-18T12:00:00Z","agent_id":"avatar","lease_id":"lease-1","request_id":"request",
                 "observation_id":"observation","mode":"structured","expected_state_revision":1,
                 "capability_digest":"%s","control_revision":1,"keymap_digest":null,
                 "deadline_at":"2026-09-18T12:00:05Z","duration_ms":5000,
                 "action":{"kind":"look_at","target":{"x":-1.25,"y":65.5,"z":2.5}},"events":[],"release_at_end":true}
                """.formatted(CAP));
            value.addProperty("epoch", epoch); value.addProperty("control_revision", epoch);
            value.addProperty("lease_id", "lease-" + epoch); value.addProperty("request_id", id); value.addProperty("seq", seq);
            value.addProperty("expected_state_revision", port.revision);
            value.addProperty("recorded_at", GamePages.utc(Instant.ofEpochMilli(time.wall())));
            value.addProperty("deadline_at", GamePages.utc(Instant.ofEpochMilli(time.wall() + 5000)));
            return value;
        }
        void start(GameActionLane lane) throws IOException { lane.tick(); time.advance(50); lane.tick(); }
    }
    @Test void durableIntentSingleLaneDedupAndTerminalReopen(@TempDir Path root) throws Exception {
        Fixture f = new Fixture(root, 100); JsonObject request;
        try (var lane = f.open()) {
            f.arm(lane, 1); f.deliver(lane); request = f.batch(1, "action", 1);
            assertEquals("accepted", lane.accept(request).get("status").getAsString());
            assertEquals(0, f.port.inputs);
            assertThrows(IOException.class, () -> lane.accept(f.batch(1, "second", 2)));
            f.start(lane); assertEquals(1, f.port.inputs);
            lane.tick();
            var receipt = lane.status("action");
            assertEquals("emitted", receipt.get("status").getAsString());
            assertEquals(2, receipt.get("emitted_events").getAsInt()); // Look plus release.
            assertTrue(receipt.get("release_confirmed").getAsBoolean());
            assertTrue(receipt.get("requires_resync").getAsBoolean());
            f.time.advance(10000);
            assertEquals(receipt, lane.accept(request));
            JsonObject reordered = new JsonObject(); request.entrySet().stream().sorted((a, b) -> b.getKey().compareTo(a.getKey()))
                .forEach(entry -> reordered.add(entry.getKey(), entry.getValue().deepCopy()));
            assertEquals(receipt, lane.accept(reordered)); assertEquals(1, f.port.inputs);
        }
        try (var lane = f.open()) {
            assertTrue(lane.health().get("fenced").getAsBoolean());
            assertEquals("emitted", lane.accept(request).get("status").getAsString());
            assertEquals(1, f.port.inputs);
        }
    }
    @Test void wrongScopeEpochLeaseCapabilitySequenceAndChangedIdsDoNotEmit(@TempDir Path root) throws Exception {
        Fixture f = new Fixture(root, 100);
        try (var lane = f.open()) {
            f.arm(lane, 1); f.deliver(lane);
            for (String field : new String[]{"campaign_id", "agent_id", "lease_id", "capability_digest"}) {
                JsonObject bad = f.batch(1, "action", 1);
                bad.addProperty(field, field.equals("capability_digest") ? "d".repeat(64) : "foreign");
                assertThrows(IOException.class, () -> lane.accept(bad));
            }
            assertThrows(IOException.class, () -> lane.accept(f.batch(0, "action", 1)));
            JsonObject request = f.batch(1, "action", 1); lane.accept(request);
            JsonObject changed = request.deepCopy(); changed.getAsJsonObject("action").getAsJsonObject("target").addProperty("x", 2);
            assertThrows(IOException.class, () -> lane.accept(changed));
            lane.cancel("action"); assertEquals(0, f.port.inputs);
            f.arm(lane, 2); f.deliver(lane); lane.accept(f.batch(2, "next", 1)); f.start(lane); lane.tick();
            f.deliver(lane); assertThrows(IOException.class, () -> lane.accept(f.batch(2, "third", 1)));
        }
    }
    @Test void undeliveredStaleChangedAndPreRestartObservationsReject(@TempDir Path root) throws Exception {
        Fixture f = new Fixture(root, 100);
        try (var lane = f.open()) {
            f.arm(lane, 1);
            assertThrows(IOException.class, () -> lane.accept(f.batch(1, "action", 1)));
            f.deliver(lane); f.time.advance(2001);
            assertThrows(IOException.class, () -> lane.accept(f.batch(1, "action", 1)));
            f.deliver(lane); var batch = f.batch(1, "action", 1); f.port.revision++;
            assertThrows(IOException.class, () -> lane.accept(batch)); assertEquals(0, f.port.inputs);
        }
        try (var lane = f.open()) {
            f.arm(lane, 2);
            assertThrows(IOException.class, () -> lane.accept(f.batch(2, "action", 1)));
        }
    }
    @Test void leaseAndAbsoluteDeadlinesCannotBeRenewedAfterExpiry(@TempDir Path root) throws Exception {
        Fixture f = new Fixture(root, 100);
        try (var lane = f.open()) {
            f.arm(lane, 1); f.deliver(lane); lane.accept(f.batch(1, "action", 1));
            f.time.advance(6001); lane.tick();
            assertEquals(0, f.port.inputs); assertEquals("cancelled", lane.status("action").get("status").getAsString());
            assertThrows(IOException.class, () -> lane.renew(1, "lease-1", f.time.wall() + 6000));
            assertThrows(IOException.class, () -> f.arm(lane, 1));
            f.time.advance(60000); assertThrows(IOException.class, () -> f.arm(lane, 2));
        }
    }
    @Test void cancellationBeforeAndDuringDispatchAndUnknownPendingIdFence(@TempDir Path root) throws Exception {
        Fixture f = new Fixture(root, 100); f.port.hold = true;
        try (var lane = f.open()) {
            f.arm(lane, 1); f.deliver(lane);
            assertThrows(IOException.class, () -> lane.cancel("not-yet-accepted"));
            assertThrows(IOException.class, () -> lane.accept(f.batch(1, "not-yet-accepted", 1)));
            f.arm(lane, 2); f.deliver(lane); lane.accept(f.batch(2, "action", 1)); f.start(lane);
            int emitted = f.port.inputs;
            assertEquals("cancelled", lane.cancel("action").get("status").getAsString());
            f.time.advance(50); lane.tick(); assertEquals(emitted, f.port.inputs);
            assertTrue(lane.status("action").get("release_confirmed").getAsBoolean());
        }
    }
    @Test void emissionFailureHasUnknownEffectsAndNeverReplays(@TempDir Path root) throws Exception {
        Fixture f = new Fixture(root, 100); f.port.failAfterInput = true;
        try (var lane = f.open()) {
            f.arm(lane, 1); f.deliver(lane); var request = f.batch(1, "action", 1); lane.accept(request); f.start(lane);
            var result = lane.status("action");
            assertEquals("unknown", result.get("status").getAsString()); assertTrue(result.get("emitted_events").isJsonNull());
            assertTrue(lane.health().get("fenced").getAsBoolean());
            assertEquals(result, lane.accept(request)); assertEquals(1, f.port.inputs);
        }
    }
    @Test void pendingCrashImageBecomesUnknownAndCostsSurvive(@TempDir Path root) throws Exception {
        Fixture f = new Fixture(root, 100); f.port.hold = true;
        Path recoveredRoot = Files.createDirectory(root.resolve("recovered"));
        JsonObject request;
        try (var lane = f.open()) {
            f.arm(lane, 1); f.deliver(lane); request = f.batch(1, "action", 1); lane.accept(request); f.start(lane);
            Files.copy(root.resolve("game-actions.jsonl"), recoveredRoot.resolve("game-actions.jsonl"));
        }
        Port recoveredPort = new Port(f.time, recoveredRoot);
        try (var lane = new GameActionLane(recoveredRoot, PROFILE, f.authority, recoveredPort, f.time)) {
            assertEquals("unknown", lane.status("action").get("status").getAsString());
            assertTrue(lane.status("action").get("emitted_events").isJsonNull());
            assertEquals(2, lane.health().get("attempted_primitive_events").getAsInt());
            lane.accept(request); assertEquals(0, recoveredPort.inputs);
            assertThrows(IOException.class, () -> lane.arm(1, "lease-1", f.time.wall() + 6000, lane.health().get("fence_token").getAsString()));
        }
    }
    @Test void bodyReconnectAndMonotonicDeadlineFence(@TempDir Path root) throws Exception {
        Fixture f = new Fixture(root, 100); f.port.hold = true;
        try (var lane = f.open()) {
            f.arm(lane, 1); f.deliver(lane); lane.accept(f.batch(1, "first", 1));
            f.port.generation++; lane.tick(); assertEquals(0, f.port.inputs);
            f.arm(lane, 2); f.deliver(lane); lane.accept(f.batch(2, "second", 1)); f.start(lane);
            f.time.elapsed += 5001; // Wall time does not advance: monotonic deadline still wins.
            lane.tick(); assertEquals("cancelled", lane.status("second").get("status").getAsString());
            f.port.body = "d".repeat(64); assertThrows(IOException.class, () -> f.arm(lane, 3));
        }
    }
    @Test void budgetExhaustionReservesReleaseAndNeverRefundsAttempts(@TempDir Path root) throws Exception {
        Fixture f = new Fixture(root, 5); f.port.hold = true; f.port.emitEachTick = true;
        try (var lane = f.open()) {
            f.arm(lane, 1); f.deliver(lane); lane.accept(f.batch(1, "action", 1)); f.start(lane);
            lane.tick(); lane.tick(); lane.tick();
            assertEquals(5, lane.health().get("attempted_primitive_events").getAsInt());
            assertEquals("unknown", lane.status("action").get("status").getAsString());
            assertTrue(lane.status("action").get("release_confirmed").getAsBoolean());
        }
        try (var lane = f.open()) {
            assertEquals(5, lane.health().get("attempted_primitive_events").getAsInt());
            f.arm(lane, 2); f.deliver(lane);
            assertThrows(IOException.class, () -> lane.accept(f.batch(2, "next", 1)));
        }
    }
    @Test void journalFailureBeforeEmissionStillReleasesAndFences(@TempDir Path root) throws Exception {
        Fixture f = new Fixture(root, 100);
        try (var lane = f.open()) {
            f.arm(lane, 1); f.deliver(lane); lane.accept(f.batch(1, "action", 1)); lane.tick();
            Files.writeString(root.resolve("game-actions.jsonl"), "corruption", java.nio.file.StandardOpenOption.APPEND);
            assertThrows(IOException.class, lane::tick);
            assertEquals(0, f.port.inputs); assertTrue(f.port.releases >= 2);
            assertFalse(lane.health().get("journal_healthy").getAsBoolean());
            assertTrue(lane.health().get("fenced").getAsBoolean());
        }
        assertThrows(IOException.class, f::open);
    }
    @Test void releaseFailureCannotAdvertiseHealthyTerminal(@TempDir Path root) throws Exception {
        Fixture f = new Fixture(root, 100);
        try (var lane = f.open()) {
            f.arm(lane, 1); f.deliver(lane); lane.accept(f.batch(1, "action", 1)); f.start(lane);
            f.port.failRelease = true; lane.tick();
            assertEquals("unknown", lane.status("action").get("status").getAsString());
            assertFalse(lane.status("action").get("release_confirmed").getAsBoolean());
            assertTrue(lane.health().get("fenced").getAsBoolean());
        }
    }
    @Test void concurrentOwnerAndChangedAuthorityCannotReuseJournal(@TempDir Path root) throws Exception {
        Fixture f = new Fixture(root, 100);
        try (var lane = f.open()) { assertThrows(Exception.class, f::open); }
        var changed = new GameActionLane.Authority("campaign", "avatar", CAP, BODY, f.authority.expires(), 101);
        assertThrows(IOException.class, () -> new GameActionLane(root, PROFILE, changed, f.port, f.time));
    }
    @Test void strictGameNumbersDoNotRelaxUnsignedFieldsOrSettings(@TempDir Path root) throws Exception {
        Fixture f = new Fixture(root, 100);
        assertThrows(IOException.class, () -> SettingsJson.read("{\"coordinate\":-1.5}"));
        assertEquals(-1.5, SettingsJson.readGame("{\"coordinate\":-1.5}").get("coordinate").getAsDouble());
        for (String number : new String[]{"1.5", "1.0", "1e0", "-1", "9007199254740992"}) {
            assertThrows(IOException.class, () -> SettingsJson.integer(SettingsJson.readGame("{\"epoch\":" + number + "}"), "epoch"));
        }
        assertThrows(IOException.class, () -> SettingsJson.readGame("{\"x\":1,\"x\":2}"));
        assertThrows(IOException.class, () -> SettingsJson.readGame("{\"x\":1e999}"));
        var unsupported = f.batch(1, "action", 1); unsupported.getAsJsonObject("action").addProperty("kind", "raw_packet");
        assertThrows(IOException.class, () -> new GameBatch(unsupported));
        for (String timestamp : new String[]{"0000-01-01T00:00:00Z", "2026-02-30T00:00:00Z", "2026-09-18T12:00:60Z"}) {
            var bad = f.batch(1, "action", 1); bad.addProperty("recorded_at", timestamp);
            assertThrows(IOException.class, () -> new GameBatch(bad));
        }
    }
    @Test void zeroSequenceIsValidForTheFirstActionAndClockRollbackFences(@TempDir Path root) throws Exception {
        Fixture f = new Fixture(root, 100);
        try (var lane = f.open()) {
            f.arm(lane, 0); f.deliver(lane);
            assertEquals("accepted", lane.accept(f.batch(0, "zero", 0)).get("status").getAsString());
            f.start(lane); lane.tick();
            f.time.utc -= 1000;
            assertTrue(lane.health().get("fenced").getAsBoolean());
            assertFalse(lane.health().get("journal_healthy").getAsBoolean());
            assertThrows(IOException.class, () -> f.arm(lane, 1));
        }
    }
    @Test void cancelHasReservedQueueSpaceAndFencesQueuedAcceptance(@TempDir Path root) throws Exception {
        Fixture f = new Fixture(root, 100);
        NativeGameProtocolTest http = new NativeGameProtocolTest();
        try (var lane = f.open()) {
            f.arm(lane, 1); f.deliver(lane);
            var protocol = new NativeGameProtocol(f.port, lane);
            try (var bridge = new SettingsHttpBridge(protocol::execute, protocol)) {
                var connection = bridge.descriptor(PROFILE);
                var request = http.request(connection, "act"); request.getAsJsonObject("args").add("batch", f.batch(1, "queued", 1));
                assertEquals(202, http.send(connection, "POST", "/v1/game", request.toString(), true).statusCode());
                for (int i = 0; i < 7; i++) assertEquals(202, http.send(connection, "POST", "/v1/game", http.request(connection, "capabilities").toString(), true).statusCode());
                var cancel = http.request(connection, "cancel"); cancel.getAsJsonObject("args").addProperty("request_id", "queued");
                assertEquals(202, http.send(connection, "POST", "/v1/game", cancel.toString(), true).statusCode());
                bridge.drain(); lane.tick();
                assertTrue(lane.health().get("fenced").getAsBoolean());
                bridge.drain(); lane.tick();
                assertEquals(0, f.port.inputs);
                var receipt = http.send(connection, "GET", "/v1/game/" + request.get("request_id").getAsString(), null, true);
                assertTrue(receipt.body().contains("LEASE_EXPIRED"));
            }
        }
    }
    @Test void queuedRearmCannotCrossStopAllWithAnOldFenceToken(@TempDir Path root) throws Exception {
        Fixture f = new Fixture(root, 100);
        NativeGameProtocolTest http = new NativeGameProtocolTest();
        try (var lane = f.open()) {
            f.arm(lane, 1);
            var protocol = new NativeGameProtocol(f.port, lane);
            try (var bridge = new SettingsHttpBridge(protocol::execute, protocol)) {
                var connection = bridge.descriptor(PROFILE);
                var arm = http.request(connection, "arm");
                var args = arm.getAsJsonObject("args"); args.addProperty("epoch", 2); args.addProperty("lease_id", "lease-2");
                args.addProperty("lease_until_unix_ms", f.time.wall() + 6000);
                args.addProperty("expected_fence_token", lane.health().get("fence_token").getAsString());
                assertEquals(202, http.send(connection, "POST", "/v1/game", arm.toString(), true).statusCode());
                var stop = http.request(connection, "stop_all");
                assertEquals(202, http.send(connection, "POST", "/v1/game", stop.toString(), true).statusCode());
                bridge.drain(); bridge.drain();
                assertTrue(lane.health().get("fenced").getAsBoolean());
                assertEquals(1, lane.health().get("epoch").getAsInt());
                var result = http.send(connection, "GET", "/v1/game/" + arm.get("request_id").getAsString(), null, true);
                assertTrue(result.body().contains("STALE_FENCE_TOKEN"));
                f.arm(lane, 2); assertFalse(lane.health().get("fenced").getAsBoolean());
            }
        }
    }
}
