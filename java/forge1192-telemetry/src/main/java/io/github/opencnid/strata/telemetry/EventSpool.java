package io.github.opencnid.strata.telemetry;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.channels.FileChannel;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.UUID;
import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.atomic.AtomicReference;

/** Single writer, bounded queue and explicit failures. Only the durable cursor is an acknowledgment. */
final class EventSpool implements AutoCloseable {
    private static final Gson JSON = new GsonBuilder().disableHtmlEscaping().create();
    private final TelemetryConfig config;
    private final String bootId = UUID.randomUUID().toString();
    private final FileChannel channel;
    private final ArrayBlockingQueue<byte[]> queue = new ArrayBlockingQueue<>(256);
    private final AtomicReference<IOException> failure = new AtomicReference<>();
    private final Thread writer;
    private volatile boolean closing;
    private volatile long durableSeq;
    private long seq, reservedBytes;

    EventSpool(TelemetryConfig config) throws IOException {
        this.config = config;
        TelemetryConfig.safeExisting(config.spoolDirectory());
        Path file = config.spoolDirectory().resolve(bootId + ".jsonl");
        channel = FileChannel.open(file, StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE);
        writer = new Thread(this::writeLoop, "strata-private-telemetry");
        writer.setDaemon(true);
        writer.start();
    }

    String bootId() { return bootId; }
    long durableSeq() { return durableSeq; }

    synchronized void publish(long tick, String kind, String schema, JsonObject payload,
                              JsonArray actors) throws IOException {
        healthy();
        if (closing) throw new IOException("TELEMETRY_CLOSED");
        JsonObject event = new JsonObject();
        event.addProperty("schema", "mcbench/GameEvent/1");
        event.addProperty("is_example", false);
        event.addProperty("campaign_id", config.campaignId());
        event.addProperty("epoch", config.epoch());
        event.addProperty("seq", seq + 1);
        event.addProperty("recorded_at", Instant.now().truncatedTo(ChronoUnit.MICROS).toString());
        event.addProperty("server_boot_id", bootId);
        event.addProperty("server_event_seq", seq + 1);
        event.addProperty("server_tick", tick);
        event.addProperty("kind", kind);
        event.addProperty("payload_schema", schema);
        event.add("payload", payload);
        event.add("actor_ids", actors);
        event.add("evidence_refs", new JsonArray());
        event.addProperty("visibility", "evaluator");
        byte[] bytes = (JSON.toJson(event) + "\n").getBytes(StandardCharsets.UTF_8);
        if (tick < 0 || bytes.length > 1048576 || seq >= config.maxEvents()
                || reservedBytes + bytes.length > config.maxBytes()) {
            fail(new IOException("TELEMETRY_QUOTA_EXHAUSTED"));
            healthy();
        }
        if (!queue.offer(bytes)) {
            fail(new IOException("TELEMETRY_BACKPRESSURE"));
            healthy();
        }
        seq++;
        reservedBytes += bytes.length;
    }

    void healthy() throws IOException {
        IOException error = failure.get();
        if (error != null) throw error;
    }

    private void fail(IOException error) { failure.compareAndSet(null, error); }

    private void writeLoop() {
        try {
            while (!closing || !queue.isEmpty()) {
                byte[] entry = queue.poll(100, java.util.concurrent.TimeUnit.MILLISECONDS);
                if (entry == null) continue;
                ByteBuffer bytes = ByteBuffer.wrap(entry);
                while (bytes.hasRemaining()) channel.write(bytes);
                channel.force(true);
                durableSeq++;
            }
        } catch (IOException error) {
            fail(error);
        } catch (InterruptedException error) {
            fail(new IOException("TELEMETRY_WRITER_INTERRUPTED", error));
            Thread.currentThread().interrupt();
        } finally {
            try { channel.close(); } catch (IOException error) { fail(error); }
        }
    }

    @Override public synchronized void close() throws IOException {
        closing = true;
        try { writer.join(2000); }
        catch (InterruptedException error) {
            Thread.currentThread().interrupt();
            fail(new IOException("TELEMETRY_CLOSE_INTERRUPTED", error));
        }
        if (writer.isAlive()) fail(new IOException("TELEMETRY_DRAIN_TIMEOUT"));
        healthy();
        if (durableSeq != seq) throw new IOException("TELEMETRY_DURABLE_GAP");
    }
}
