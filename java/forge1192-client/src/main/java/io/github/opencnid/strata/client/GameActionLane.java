package io.github.opencnid.strata.client;

import com.google.gson.JsonArray;
import com.google.gson.JsonNull;
import com.google.gson.JsonObject;
import java.io.IOException;
import java.nio.channels.FileChannel;
import java.nio.channels.FileLock;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Set;

/** Client-thread native safety boundary. The broker remains responsible for public grants and accounting. */
final class GameActionLane implements AutoCloseable {
    interface Clock { long wall(); long mono(); }
    interface Operation { void run() throws IOException; }
    interface Emitter { void invoke(Operation operation) throws IOException; }
    interface Motor { boolean tick(Emitter emitter) throws IOException; }
    interface RuntimePort {
        void requireClientThread() throws IOException;
        String bodyFingerprint() throws IOException;
        long connectionGeneration();
        JsonObject snapshot(String id) throws IOException;
        void resetObservations() throws IOException;
        default void delivered(JsonObject snapshot) throws IOException {}
        default void activeRequest(String id) {}
        void validate(GameBatch batch, JsonObject observation) throws IOException;
        Motor begin(GameBatch batch, JsonObject observation, Emitter emitter) throws IOException;
        void releaseInputs() throws IOException;
    }
    record Authority(String campaign, String agent, String capability, String body, long expires, long primitiveLimit) {
        static Authority read(JsonObject value) throws IOException {
            SettingsJson.fields(value, "schema", "campaign_id", "agent_id", "capability_digest", "body_fingerprint",
                "expires_unix_ms", "primitive_limit");
            if (!"strata/NativeGameAuthority/1".equals(SettingsJson.string(value, "schema"))) throw new IOException("SCHEMA_UNSUPPORTED");
            long limit = SettingsJson.integer(value, "primitive_limit");
            if (limit < 2) throw new IOException("GAME_BUDGET_INVALID");
            return new Authority(GameBatch.id(value, "campaign_id"), GameBatch.id(value, "agent_id"),
                GameBatch.digest(value, "capability_digest"), GameBatch.digest(value, "body_fingerprint"),
                SettingsJson.integer(value, "expires_unix_ms"), limit);
        }
    }
    private static final class Record {
        final GameBatch batch;
        long attempted, confirmed;
        JsonObject terminal;
        Record(GameBatch batch) { this.batch = batch; }
    }
    private record Delivery(String snapshotId, long revision, JsonObject snapshot) {}
    private final Authority authority;
    private final RuntimePort runtime;
    private final Clock clock;
    private final SettingsJournal journal;
    private final FileChannel lockFile;
    private final FileLock lock;
    private final Map<String, Record> records = new LinkedHashMap<>();
    private final Map<String, Delivery> deliveries = new LinkedHashMap<>();
    private long lastEpoch = -1, lastSequence = -1, charged, lastWall, generation;
    private long leaseUntil, expiresMono, actionUntil;
    private String lease = "", fenceReason = "NOT_ARMED";
    private String fenceToken = java.util.UUID.randomUUID().toString();
    private Record active;
    private Delivery activeDelivery;
    private Motor motor;
    private boolean fenced = true, healthy = true, closed, awaitingDispatch;

    GameActionLane(Path root, String fingerprint, Authority authority, RuntimePort runtime) throws IOException {
        this(root, fingerprint, authority, runtime, new Clock() {
            public long wall() { return System.currentTimeMillis(); }
            public long mono() { return System.nanoTime() / 1000000; }
        });
    }
    GameActionLane(Path root, String fingerprint, Authority authority, RuntimePort runtime, Clock clock) throws IOException {
        this.authority = authority; this.runtime = runtime; this.clock = clock;
        runtime.requireClientThread(); SettingsFiles.safeExisting(root);
        Path lockPath = root.resolve("game-actions.lock");
        if (Files.exists(lockPath)) SettingsFiles.safeExisting(lockPath);
        lockFile = FileChannel.open(lockPath, StandardOpenOption.CREATE, StandardOpenOption.WRITE);
        FileLock acquired = null;
        try {
            try { acquired = lockFile.tryLock(); }
            catch (java.nio.channels.OverlappingFileLockException error) { throw new IOException("GAME_LANE_OWNED", error); }
            if (acquired == null) throw new IOException("GAME_LANE_OWNED");
            lock = acquired;
            journal = new SettingsJournal(root.resolve("game-actions.jsonl"),
                KeyOptions.sha256(fingerprint + "\n" + authority), 134217728L, "strata/NativeGameJournalFrame/1");
            recover();
            // An absolute immutable cap cannot be renewed with the lease.
            expiresMono = clock.mono() + Math.max(0, authority.expires - clock.wall());
        } catch (IOException | RuntimeException error) {
            if (acquired != null) acquired.release(); lockFile.close(); throw error;
        }
    }

    private void recover() throws IOException {
        for (JsonObject event : journal.entries().subList(1, Math.toIntExact(journal.revision()))) {
            long wall = SettingsJson.integer(event, "wall_ms");
            if (wall < lastWall) throw new IOException("GAME_JOURNAL_INVALID"); lastWall = wall;
            switch (SettingsJson.string(event, "kind")) {
                case "lease" -> {
                    SettingsJson.fields(event, "kind", "wall_ms", "epoch", "lease_id");
                    long epoch = SettingsJson.integer(event, "epoch");
                    if (epoch <= lastEpoch || records.values().stream().anyMatch(r -> r.terminal == null)) throw new IOException("GAME_JOURNAL_INVALID");
                    lastEpoch = epoch; lease = GameBatch.id(event, "lease_id"); lastSequence = -1;
                }
                case "renew" -> {
                    SettingsJson.fields(event, "kind", "wall_ms", "epoch", "lease_id");
                    if (SettingsJson.integer(event, "epoch") != lastEpoch || !lease.equals(GameBatch.id(event, "lease_id"))) throw new IOException("GAME_JOURNAL_INVALID");
                }
                case "delivery" -> {
                    SettingsJson.fields(event, "kind", "wall_ms", "observation_id", "snapshot_parts");
                    GameBatch.id(event, "observation_id");
                    if (!event.get("snapshot_parts").isJsonArray()) throw new IOException("GAME_JOURNAL_INVALID");
                    StringBuilder text = new StringBuilder();
                    for (var part : event.getAsJsonArray("snapshot_parts")) {
                        if (!part.isJsonPrimitive() || !part.getAsJsonPrimitive().isString()) throw new IOException("GAME_JOURNAL_INVALID");
                        text.append(part.getAsString());
                    }
                    if (text.length() > SettingsHttpBridge.MAX_RESPONSE) throw new IOException("GAME_JOURNAL_INVALID");
                    SettingsJson.readGame(text.toString());
                    // Old deliveries are evidence only, never post-restart authority.
                }
                case "intent" -> {
                    SettingsJson.fields(event, "kind", "wall_ms", "batch_json");
                    GameBatch batch = new GameBatch(SettingsJson.readGame(SettingsJson.string(event, "batch_json")));
                    scope(batch);
                    if (batch.epoch != lastEpoch || !batch.lease.equals(lease) || batch.sequence <= lastSequence
                            || records.containsKey(batch.id) || records.values().stream().anyMatch(r -> r.terminal == null)) throw new IOException("GAME_JOURNAL_INVALID");
                    records.put(batch.id, new Record(batch)); lastSequence = batch.sequence;
                }
                case "primitive" -> {
                    SettingsJson.fields(event, "kind", "wall_ms", "request_id", "safety_release");
                    if (!event.get("safety_release").isJsonPrimitive()
                            || !event.get("safety_release").getAsJsonPrimitive().isBoolean()) throw new IOException("GAME_JOURNAL_INVALID");
                    charged++;
                    if (!event.get("request_id").isJsonNull()) {
                        Record record = records.get(GameBatch.id(event, "request_id"));
                        if (record == null || record.terminal != null) throw new IOException("GAME_JOURNAL_INVALID");
                        record.attempted++;
                    } else if (!event.get("safety_release").getAsBoolean()) throw new IOException("GAME_JOURNAL_INVALID");
                }
                case "terminal" -> {
                    SettingsJson.fields(event, "kind", "wall_ms", "receipt");
                    if (!event.get("receipt").isJsonObject()) throw new IOException("GAME_JOURNAL_INVALID");
                    JsonObject receipt = event.getAsJsonObject("receipt");
                    Record record = records.get(GameBatch.id(receipt, "request_id"));
                    if (record == null || record.terminal != null) throw new IOException("GAME_JOURNAL_INVALID");
                    validateReceipt(record, receipt); record.terminal = receipt.deepCopy();
                }
                default -> throw new IOException("GAME_JOURNAL_INVALID");
            }
        }
        if (clock.wall() < lastWall) throw new IOException("GAME_CLOCK_ROLLBACK");
        for (Record record : records.values()) if (record.terminal == null) {
            record.terminal = receipt(record, "unknown", "PROCESS_INTERRUPTED", false, null);
            JsonObject event = event("terminal"); event.add("receipt", record.terminal); append(event);
        }
    }

    JsonObject arm(long epoch, String leaseId, long until, String expectedFenceToken) throws IOException {
        thread(); NativeSettingsProtocol.identifier(leaseId);
        if (!fenceToken.equals(expectedFenceToken)) throw new IOException("STALE_FENCE_TOKEN");
        if (!healthy || active != null || epoch <= lastEpoch) throw new IOException("STALE_EPOCH");
        absoluteLimit(); body();
        long remaining = leaseRemaining(until);
        JsonObject event = event("lease"); event.addProperty("epoch", epoch); event.addProperty("lease_id", leaseId); append(event);
        lastEpoch = epoch; lease = leaseId; lastSequence = -1; deliveries.clear();
        generation = runtime.connectionGeneration(); leaseUntil = clock.mono() + remaining;
        runtime.resetObservations();
        if (!release(null)) throw new IOException("GAME_RELEASE_UNCONFIRMED");
        fenced = false; fenceReason = null;
        fenceToken = java.util.UUID.randomUUID().toString();
        return health();
    }
    JsonObject renew(long epoch, String leaseId, long until) throws IOException {
        thread(); ready();
        if (epoch != lastEpoch || !lease.equals(leaseId)) throw new IOException("LEASE_EXPIRED");
        long remaining = leaseRemaining(until);
        JsonObject event = event("renew"); event.addProperty("epoch", epoch); event.addProperty("lease_id", leaseId); append(event);
        leaseUntil = clock.mono() + remaining; return health();
    }
    private long leaseRemaining(long until) throws IOException {
        long remaining = until - clock.wall();
        if (remaining <= 0 || remaining > 6000) throw new IOException("GAME_LEASE_INVALID"); return remaining;
    }

    JsonObject deliver(String observationId, String snapshotId, long revision) throws IOException {
        thread(); ready(); NativeSettingsProtocol.identifier(observationId); NativeSettingsProtocol.identifier(snapshotId);
        if (active != null) throw new IOException("ACTION_IN_PROGRESS");
        JsonObject snapshot = runtime.snapshot(snapshotId);
        if (SettingsJson.integer(snapshot, "age_ms") > 2000 || SettingsJson.integer(snapshot, "state_revision") != revision) throw new IOException("STALE_OBSERVATION");
        Delivery previous = deliveries.get(observationId);
        if (previous != null && (!previous.snapshotId.equals(snapshotId) || previous.revision != revision)) throw new IOException("GAME_IDEMPOTENCY_CONFLICT");
        if (previous == null) {
            String text = snapshot.toString();
            if (text.length() > SettingsHttpBridge.MAX_RESPONSE) throw new IOException("GAME_OBSERVATION_TOO_LARGE");
            JsonArray parts = new JsonArray();
            for (int i = 0; i < text.length(); i += 4096) parts.add(text.substring(i, Math.min(i + 4096, text.length())));
            JsonObject event = event("delivery"); event.addProperty("observation_id", observationId); event.add("snapshot_parts", parts); append(event);
            try { runtime.delivered(snapshot.deepCopy()); }
            catch (IOException | RuntimeException failure) {
                fence("GAME_DELIVERY_UNAVAILABLE"); throw failure;
            }
            deliveries.put(observationId, new Delivery(snapshotId, revision, snapshot.deepCopy()));
            while (deliveries.size() > 16) deliveries.remove(deliveries.keySet().iterator().next());
        }
        JsonObject result = new JsonObject(); result.addProperty("observation_id", observationId);
        result.addProperty("snapshot_id", snapshotId); result.addProperty("state_revision", revision); return result;
    }

    JsonObject accept(JsonObject input) throws IOException {
        thread(); GameBatch batch = new GameBatch(input); scope(batch);
        Record previous = records.get(batch.id);
        if (previous != null) {
            if (!previous.batch.json.equals(batch.json)) throw new IOException("GAME_IDEMPOTENCY_CONFLICT");
            return status(batch.id); // An expired identical request is only a status query.
        }
        ready();
        if (batch.epoch != lastEpoch || !batch.lease.equals(lease)) throw new IOException("STALE_EPOCH");
        if (batch.sequence <= lastSequence) throw new IOException("STALE_SEQUENCE");
        if (active != null) throw new IOException("ACTION_IN_PROGRESS");
        Delivery delivery = deliveries.get(batch.observation);
        if (delivery == null || delivery.revision != batch.revision) throw new IOException("STALE_OBSERVATION");
        JsonObject current = runtime.snapshot(delivery.snapshotId);
        if (SettingsJson.integer(current, "age_ms") > 2000) throw new IOException("STALE_OBSERVATION");
        long remaining = batch.deadline - clock.wall();
        if (remaining <= 0 || remaining > 30250) throw new IOException("DEADLINE_EXCEEDED");
        int minimum = batch.kind.equals("recipe_navigate") ? GameRecipeNavigation.Request.read(batch.action).minimum()
            : Set.of("dig", "interact_block", "attack", "interact_entity", "place", "equip", "click_slot", "craft", "close_window").contains(batch.kind) ? 3 : 2;
        if (charged + minimum > authority.primitiveLimit) throw new IOException("BUDGET_EXHAUSTED");
        runtime.validate(batch, delivery.snapshot);
        journal.reserve(262144); // Pending terminal/release evidence has priority over new reads.
        JsonObject event = event("intent"); event.addProperty("batch_json", batch.json.toString()); append(event);
        active = new Record(batch); records.put(batch.id, active); lastSequence = batch.sequence;
        activeDelivery = delivery; motor = null;
        awaitingDispatch = true;
        runtime.activeRequest(batch.id);
        actionUntil = clock.mono() + Math.min(batch.duration, remaining);
        return status(batch.id);
    }

    void tick() throws IOException {
        thread();
        if (!fenced) {
            try { ready(); }
            catch (IOException error) { fence(code(error)); return; }
        }
        if (active == null) return;
        if (clock.mono() >= actionUntil || clock.wall() >= active.batch.deadline) { fence("DEADLINE_EXCEEDED"); return; }
        if (awaitingDispatch) { awaitingDispatch = false; return; }
        try {
            if (motor == null) {
                JsonObject snapshot = runtime.snapshot(activeDelivery.snapshotId);
                if (SettingsJson.integer(snapshot, "age_ms") > 2000) throw new IOException("STALE_OBSERVATION");
                runtime.validate(active.batch, activeDelivery.snapshot);
                motor = runtime.begin(active.batch, activeDelivery.snapshot, operation -> emit(active, false, operation));
            } else if (motor.tick(operation -> emit(active, false, operation))) {
                finish("emitted", null);
            }
        } catch (IOException | RuntimeException error) {
            boolean uncertain = active != null && active.attempted > 0;
            if (uncertain) markFenced(code(error));
            finish(uncertain ? "unknown" : "failed", code(error));
        }
    }
    JsonObject cancel(String id) throws IOException {
        thread(); NativeSettingsProtocol.identifier(id);
        if (!records.containsKey(id)) {
            // A cancel may overtake an HTTP-queued acceptance. Fence that future dispatch too.
            fence("CANCELLED_BEFORE_ACCEPTANCE"); throw new IOException("GAME_REQUEST_UNKNOWN");
        }
        if (active != null && active.batch.id.equals(id)) fence("CANCELLED");
        return status(id);
    }
    JsonObject stopAll() throws IOException { thread(); fence("STOP_ALL"); return health(); }
    private void fence(String reason) throws IOException {
        markFenced(reason);
        if (active != null) finish("cancelled", reason); else release(null);
        deliveries.clear();
    }
    private void finish(String status, String error) throws IOException {
        if (active == null) return;
        Record record = active;
        boolean released = release(record);
        if (!released) { status = "unknown"; error = "GAME_RELEASE_UNCONFIRMED"; }
        Long emitted = released && record.confirmed == record.attempted ? record.confirmed : null;
        record.terminal = receipt(record, status, error, released, emitted);
        active = null; activeDelivery = null; motor = null; deliveries.clear();
        runtime.activeRequest(null);
        JsonObject event = event("terminal"); event.add("receipt", record.terminal);
        try { append(event); }
        catch (IOException failure) {
            record.terminal = receipt(record, "unknown", "EVIDENCE_UNAVAILABLE", released, emitted);
            throw failure;
        }
    }
    private void emit(Record record, boolean safety, Operation operation) throws IOException {
        if (!safety) {
            ready();
            if (record != active || clock.mono() >= actionUntil || clock.wall() >= record.batch.deadline) throw new IOException("DEADLINE_EXCEEDED");
            // Preserve one reserved release event; uncertain attempted events are never refunded.
            if (charged + 1 >= authority.primitiveLimit) throw new IOException("BUDGET_EXHAUSTED");
        }
        JsonObject event = event("primitive");
        event.addProperty("request_id", record == null ? null : record.batch.id);
        event.addProperty("safety_release", safety); append(event);
        charged++; if (record != null) record.attempted++;
        operation.run();
        if (record != null) record.confirmed++;
    }
    private boolean release(Record record) {
        boolean[] invoked = {false};
        try { emit(record, true, () -> { invoked[0] = true; runtime.releaseInputs(); }); return true; }
        catch (IOException | RuntimeException error) {
            healthy = false; markFenced("GAME_RELEASE_UNCONFIRMED");
            // Journal failure cannot suppress a safety release. Its unrecorded outcome is unknown.
            if (!invoked[0]) try { runtime.releaseInputs(); } catch (IOException | RuntimeException ignored) { }
            return false;
        }
    }
    JsonObject status(String id) throws IOException {
        thread(); Record record = records.get(id);
        if (record == null) throw new IOException("GAME_REQUEST_UNKNOWN");
        return record.terminal != null ? record.terminal.deepCopy() : receipt(record,
            record == active && motor != null ? "executing" : "accepted", null, false, record.confirmed);
    }
    JsonObject health() throws IOException {
        thread();
        if (!fenced) {
            try { ready(); } catch (IOException error) { fence(code(error)); }
        }
        JsonObject value = new JsonObject();
        value.addProperty("schema", "strata/NativeGameLane/1"); value.addProperty("fenced", fenced);
        value.addProperty("fence_token", fenceToken);
        value.addProperty("reason", fenceReason); value.addProperty("journal_healthy", healthy);
        value.addProperty("epoch", lastEpoch < 0 ? null : lastEpoch);
        value.addProperty("active_request_id", active == null ? null : active.batch.id);
        value.addProperty("attempted_primitive_events", charged); value.addProperty("primitive_limit", authority.primitiveLimit);
        return value;
    }
    JsonObject authority() throws IOException {
        thread();
        JsonObject value = new JsonObject();
        value.addProperty("schema", "strata/NativeGameAuthority/1");
        value.addProperty("campaign_id", authority.campaign); value.addProperty("agent_id", authority.agent);
        value.addProperty("capability_digest", authority.capability); value.addProperty("body_fingerprint", authority.body);
        value.addProperty("expires_unix_ms", authority.expires); value.addProperty("primitive_limit", authority.primitiveLimit);
        return value;
    }
    private void scope(GameBatch batch) throws IOException {
        if (!batch.campaign.equals(authority.campaign) || !batch.agent.equals(authority.agent)) throw new IOException("FORBIDDEN");
        if (!batch.capability.equals(authority.capability) || batch.controlRevision != batch.epoch) throw new IOException("CAPABILITY_MISSING");
    }
    private void body() throws IOException {
        if (!authority.body.equals(runtime.bodyFingerprint())) throw new IOException("GAME_BODY_MISMATCH");
    }
    private void ready() throws IOException {
        if (fenced || !healthy || clock.mono() >= leaseUntil) throw new IOException("LEASE_EXPIRED");
        absoluteLimit(); body();
        if (generation != runtime.connectionGeneration()) throw new IOException("CONNECTION_CHANGED");
    }
    private void absoluteLimit() throws IOException {
        if (clock.wall() < lastWall) throw new IOException("GAME_CLOCK_ROLLBACK");
        if (clock.wall() >= authority.expires || clock.mono() >= expiresMono) throw new IOException("BUDGET_EXHAUSTED");
    }
    private void thread() throws IOException {
        runtime.requireClientThread(); if (closed) throw new IOException("GAME_LANE_CLOSED");
    }
    private JsonObject event(String kind) {
        JsonObject value = new JsonObject(); value.addProperty("kind", kind); value.addProperty("wall_ms", clock.wall()); return value;
    }
    private void append(JsonObject event) throws IOException {
        try {
            long wall = SettingsJson.integer(event, "wall_ms");
            if (wall < lastWall) throw new IOException("GAME_CLOCK_ROLLBACK");
            journal.append(event); lastWall = wall;
        } catch (IOException error) { healthy = false; markFenced("EVIDENCE_UNAVAILABLE"); throw error; }
    }
    private void markFenced(String reason) {
        fenced = true; fenceReason = reason; fenceToken = java.util.UUID.randomUUID().toString();
    }
    private static String code(Exception error) {
        String code = error.getMessage(); return code != null && code.matches("[A-Z][A-Z0-9_]{1,95}") ? code : "GAME_EXECUTION_UNKNOWN";
    }
    private static JsonObject receipt(Record record, String status, String code, boolean released, Long emitted) {
        JsonObject value = new JsonObject(); value.addProperty("schema", "strata/NativeGameActionReceipt/1");
        value.addProperty("request_id", record.batch.id); value.addProperty("epoch", record.batch.epoch);
        value.addProperty("action_seq", record.batch.sequence); value.addProperty("status", status);
        value.addProperty("attempted_events", record.attempted); value.addProperty("emitted_events", emitted);
        value.addProperty("release_confirmed", released); value.addProperty("error_code", code);
        value.addProperty("requires_resync", !Set.of("accepted", "executing").contains(status)); return value;
    }
    private static void validateReceipt(Record record, JsonObject value) throws IOException {
        SettingsJson.fields(value, "schema", "request_id", "epoch", "action_seq", "status", "attempted_events",
            "emitted_events", "release_confirmed", "error_code", "requires_resync");
        if (!"strata/NativeGameActionReceipt/1".equals(SettingsJson.string(value, "schema"))
                || SettingsJson.integer(value, "epoch") != record.batch.epoch
                || SettingsJson.integer(value, "action_seq") != record.batch.sequence
                || SettingsJson.integer(value, "attempted_events") != record.attempted
                || !Set.of("emitted", "cancelled", "unknown", "failed").contains(SettingsJson.string(value, "status"))) throw new IOException("GAME_JOURNAL_INVALID");
        if (!value.get("emitted_events").isJsonNull() && SettingsJson.integer(value, "emitted_events") > record.attempted) throw new IOException("GAME_JOURNAL_INVALID");
        GameBatch.bool(value, "requires_resync", true);
        if (!value.get("release_confirmed").isJsonPrimitive() || !value.get("release_confirmed").getAsJsonPrimitive().isBoolean()) throw new IOException("GAME_JOURNAL_INVALID");
        if (!value.get("error_code").isJsonNull() && !SettingsJson.string(value, "error_code").matches("[A-Z][A-Z0-9_]{1,95}")) throw new IOException("GAME_JOURNAL_INVALID");
    }
    @Override public void close() throws IOException {
        if (closed) return;
        try { runtime.requireClientThread(); if (active != null || !fenced) fence("CLOSED"); }
        finally { closed = true; lock.release(); lockFile.close(); }
    }
}
