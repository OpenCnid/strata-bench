package io.github.opencnid.strata.client;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import java.io.IOException;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.atomic.AtomicLong;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import static org.junit.jupiter.api.Assertions.*;

/** Synthetic input ports exercise sequencing/fencing; not a Minecraft effects test. */
class GameGesturesTest {
    @Test void realLaneCancelsHeldUseAndRetainsBudgetExhaustionWithoutReplay(@TempDir Path root) throws Exception {
        for (boolean exhaust : List.of(false, true)) {
            Path directory = java.nio.file.Files.createDirectory(root.resolve(exhaust ? "exhaust" : "cancel"));
            var f = new GameActionLaneTest.Fixture(directory, exhaust ? 3 : 100);
            var use = new Use();
            var held = new java.util.concurrent.atomic.AtomicBoolean();
            var runtime = new GameActionLane.RuntimePort() {
                public void requireClientThread() throws IOException { f.port.requireClientThread(); }
                public String bodyFingerprint() { return f.port.bodyFingerprint(); }
                public long connectionGeneration() { return f.port.connectionGeneration(); }
                public JsonObject snapshot(String id) throws IOException { return f.port.snapshot(id); }
                public void resetObservations() { f.port.resetObservations(); }
                public void validate(GameBatch batch, JsonObject snapshot) throws IOException { f.port.validate(batch, snapshot); }
                public GameActionLane.Motor begin(GameBatch batch, JsonObject snapshot, GameActionLane.Emitter emit) throws IOException {
                    return GameGestures.use(use, "off", 2000, f.time::mono, op -> {
                        emit.invoke(() -> { op.run(); held.set(true); });
                    });
                }
                public void releaseInputs() throws IOException { held.set(false); f.port.releaseInputs(); }
            };
            try (var lane = new GameActionLane(directory, GameActionLaneTest.PROFILE, f.authority, runtime, f.time)) {
                f.arm(lane, 1); f.deliver(lane);
                var batch = f.batch(1, "use", 1);
                batch.add("action", SettingsJson.readGame("{\"kind\":\"use_item\",\"hand\":\"off\",\"hold_ms\":2000}"));
                lane.accept(batch); f.start(lane); assertTrue(held.get()); assertEquals(1, use.starts);
                f.time.advance(50); lane.tick();
                if (exhaust) {
                    assertEquals("unknown", lane.status("use").get("status").getAsString());
                    assertEquals("BUDGET_EXHAUSTED", lane.status("use").get("error_code").getAsString());
                } else {
                    assertEquals(1, use.holds);
                    assertEquals("cancelled", lane.cancel("use").get("status").getAsString());
                }
                assertFalse(held.get()); assertTrue(lane.status("use").get("release_confirmed").getAsBoolean());
                int before = use.holds; f.time.advance(50); lane.tick();
                lane.accept(batch); assertEquals(1, use.starts); assertEquals(before, use.holds);
                String journal = java.nio.file.Files.readString(directory.resolve("game-actions.jsonl"));
                assertEquals(1, journal.lines().filter(line -> line.contains("\"kind\":\"intent\"")).count());
            }
        }
    }
    static final class Use implements GameGestures.UsePort {
        int starts, holds; boolean using = true, context = true, initialHold;
        public void validate() throws IOException { if (!context) throw new IOException("GAME_SCREEN_OPEN"); }
        public void start(String hand, boolean hold) { starts++; initialHold = hold; }
        public boolean stillUsing(String hand) { return using; }
        public void hold() { holds++; }
    }
    @Test void heldUseChargesEveryTickAndNeverRestartsFinishedOrRejectedUse() throws Exception {
        for (boolean finishesEarly : List.of(false, true)) {
            var time = new AtomicLong(1000); var port = new Use(); var charged = new AtomicLong();
            GameActionLane.Emitter emit = operation -> { charged.incrementAndGet(); operation.run(); };
            var motor = GameGestures.use(port, "off", 125, time::get, emit);
            assertEquals(1, charged.get()); assertTrue(port.initialHold);
            time.addAndGet(50); assertFalse(motor.tick(emit)); assertEquals(2, charged.get());
            if (finishesEarly) port.using = false; else time.addAndGet(75);
            assertTrue(motor.tick(emit)); assertEquals(1, port.starts); assertEquals(1, port.holds);
        }
        var port = new Use(); port.using = false;
        var motor = GameGestures.use(port, "main", 2000, () -> 0, GameActionLane.Operation::run);
        assertTrue(motor.tick(GameActionLane.Operation::run)); assertEquals(0, port.holds); assertEquals(1, port.starts);
    }
    @Test void tapAndLostContextCannotLeaveAnotherHeldTick() throws Exception {
        var port = new Use();
        var motor = GameGestures.use(port, "main", 0, () -> 0, GameActionLane.Operation::run);
        assertFalse(port.initialHold); assertTrue(motor.tick(GameActionLane.Operation::run)); assertEquals(0, port.holds);
        var hold = GameGestures.use(port, "main", 2000, () -> 0, GameActionLane.Operation::run);
        port.context = false;
        assertThrows(IOException.class, () -> hold.tick(GameActionLane.Operation::run)); assertEquals(0, port.holds);
    }
    @Test void failedChargePreventsInitialUseAndHeldInput() throws Exception {
        var port = new Use();
        GameActionLane.Emitter exhausted = op -> { throw new IOException("BUDGET_EXHAUSTED"); };
        assertThrows(IOException.class, () -> GameGestures.use(port, "main", 2000, () -> 0, exhausted));
        assertEquals(0, port.starts);
        var motor = GameGestures.use(port, "main", 2000, () -> 0, GameActionLane.Operation::run);
        assertThrows(IOException.class, () -> motor.tick(exhausted)); assertEquals(0, port.holds);
    }
    JsonObject snapshot(String id) {
        JsonObject snapshot = new JsonObject(), state = new JsonObject(), entity = new JsonObject();
        entity.addProperty("id", id); entity.addProperty("type", "minecraft:pig");
        JsonArray entities = new JsonArray(); entities.add(entity); state.add("nearby_entities", entities);
        snapshot.add("state", state); return snapshot;
    }
    static final class Target implements GameGestures.EntityPort {
        List<String> calls = new ArrayList<>(); String failure; boolean changedAfterLook;
        public GameVisibility.Point resolve(String id, String type, boolean attack) throws IOException {
            calls.add("resolve"); if (failure != null) throw new IOException(failure);
            return new GameVisibility.Point(1, 65, 2);
        }
        public void look(GameVisibility.Point p) { calls.add("look"); if (changedAfterLook) failure = "PRECONDITION_FAILED"; }
        public void trigger(String id, String type, boolean attack) { calls.add(attack ? "attack" : "interact"); }
    }
    @Test void onlyDeliveredEntitiesCanDispatchAndTurningRechecksIdentity() throws Exception {
        for (boolean attack : List.of(false, true)) {
            var port = new Target();
            assertThrows(IOException.class, () -> GameGestures.entity(port, snapshot("other"), "target", attack, GameActionLane.Operation::run));
            assertTrue(port.calls.isEmpty());
            var motor = GameGestures.entity(port, snapshot("target"), "target", attack, GameActionLane.Operation::run);
            assertTrue(motor.tick(GameActionLane.Operation::run));
            assertEquals(List.of("resolve", "look", "resolve", attack ? "attack" : "interact"), port.calls);
            var changed = new Target(); changed.changedAfterLook = true;
            assertThrows(IOException.class, () -> GameGestures.entity(changed, snapshot("target"), "target", attack, GameActionLane.Operation::run));
            assertEquals(List.of("resolve", "look", "resolve"), changed.calls);
        }
    }
    @Test void occludedOutOfReachAndReusedTargetsCannotEmit() {
        for (String reason : List.of("TARGET_OCCLUDED", "OUT_OF_REACH", "PRECONDITION_FAILED")) {
            var port = new Target(); port.failure = reason;
            var inputs = new AtomicLong();
            assertThrows(IOException.class, () -> GameGestures.entity(port, snapshot("target"), "target", true,
                op -> { inputs.incrementAndGet(); op.run(); }));
            assertEquals(0, inputs.get());
        }
        assertNotEquals(GameGestures.entityId(1, "first", "session"), GameGestures.entityId(1, "second", "session"));
        assertNotEquals(GameGestures.entityId(1, "first", "session"), GameGestures.entityId(1, "first", "fresh-probe"));
    }
    @Test void unicodeChatIsTextButCommandsControlsAndMalformedSurrogatesReject() throws Exception {
        for (String text : List.of("Hello", "café 中文 🧭", "🧭".repeat(128))) assertEquals(text, GameGestures.chat(text));
        for (String text : List.of("/op user", "  /give user stone", "\nhello", "hello\rworld", "hi\tthere", "", "  ",
                "a".repeat(257), "🧭".repeat(129), "\u00a7cHello", "\u0000", "\ud800", "\udc00", "\ud800x")) {
            assertThrows(IOException.class, () -> GameGestures.chat(text));
        }
    }
    @Test void strictGestureBatchBoundsRejectBeforeDispatch(@TempDir Path root) throws Exception {
        var f = new GameActionLaneTest.Fixture(root, 100);
        JsonObject batch = f.batch(1, "gesture", 1), action = new JsonObject();
        action.addProperty("kind", "use_item"); action.addProperty("hand", "off"); action.addProperty("hold_ms", 2000);
        batch.add("action", action); new GameBatch(batch);
        action.addProperty("hold_ms", 2001); assertThrows(IOException.class, () -> new GameBatch(batch));
        action.addProperty("hold_ms", 1.5); assertThrows(IOException.class, () -> new GameBatch(batch));
        action.addProperty("hold_ms", 2000); batch.addProperty("duration_ms", 1000);
        assertThrows(IOException.class, () -> new GameBatch(batch));
        batch.addProperty("duration_ms", 5000); action.addProperty("hand", "both");
        assertThrows(IOException.class, () -> new GameBatch(batch));
        action.remove("hand"); action.remove("hold_ms"); action.addProperty("kind", "chat"); action.addProperty("text", "/op user");
        assertThrows(IOException.class, () -> new GameBatch(batch));
        action.addProperty("text", "Hello"); new GameBatch(batch);
        action.addProperty("packet", "hidden"); assertThrows(IOException.class, () -> new GameBatch(batch));
    }
}
