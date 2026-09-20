package io.github.opencnid.strata.client;

import com.google.gson.JsonObject;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.UUID;
import java.util.function.LongSupplier;

/** Operator-only bounded evidence. No gameplay route or arbitrary output filename. */
final class PrivateFrames {
    static final String POLICY = "private-main-target-pre-display-png4/1";
    static final int MAX_PNG = 12 * 1024 * 1024;
    static final int MAX_FRAMES = 4;
    static final long LIFETIME_NS = 600_000_000_000L;
    @FunctionalInterface interface Capture { byte[] read() throws IOException; }
    private final Path root;
    private final LongSupplier nano, wall;
    private final long started;
    final String session = UUID.randomUUID().toString();
    private int next = 1;
    private long last = Long.MIN_VALUE;
    private boolean failed;

    PrivateFrames(Path directory, Path profile, String jarHash, LongSupplier nano, LongSupplier wall) throws IOException {
        root = SettingsFiles.safeExisting(directory);
        profile = SettingsFiles.safeExisting(profile);
        if (!Files.isDirectory(root) || root.startsWith(profile) || profile.startsWith(root)
                || !jarHash.matches("[a-f0-9]{64}")) throw new IOException("FRAME_PRIVATE_ROOT_REQUIRED");
        try (var entries = Files.list(root)) {
            if (entries.findAny().isPresent()) throw new IOException("FRAME_DIRECTORY_NOT_EMPTY");
        }
        this.nano = nano; this.wall = wall; started = nano.getAsLong();
        var value = base("strata/PrivateFrameSession/1");
        value.addProperty("client_jar_sha256", jarHash);
        value.addProperty("max_frames", MAX_FRAMES); value.addProperty("max_png_bytes", MAX_PNG);
        value.addProperty("max_width", 1920); value.addProperty("max_height", 1080);
        value.addProperty("lifetime_ms", LIFETIME_NS / 1_000_000L);
        write("session.json", value);
    }

    private JsonObject base(String schema) {
        var value = new JsonObject(); value.addProperty("schema", schema);
        value.addProperty("policy", POLICY); value.addProperty("session_id", session);
        value.addProperty("operator_development_only", true);
        value.addProperty("campaign_admission", false); value.addProperty("gameplay_image_capability", false);
        value.addProperty("utc_unix_ms", wall.getAsLong());
        value.addProperty("source_clock_id", session);
        value.addProperty("native_monotonic_ns", Long.toString(nano.getAsLong()));
        return value;
    }

    private void write(String name, JsonObject value) throws IOException {
        byte[] bytes = (value + "\n").getBytes(StandardCharsets.UTF_8);
        if (bytes.length > 8192) throw new IOException("FRAME_RECORD_QUOTA");
        SettingsFiles.writeNew(root.resolve(name), bytes);
    }

    boolean capture(String screen, boolean world, int width, int height, long frame, Capture source) throws IOException {
        if (failed || next > MAX_FRAMES) return false;
        long now = nano.getAsLong();
        if (now - started < 0 || now - started > LIFETIME_NS) throw new IOException("FRAME_SESSION_EXPIRED");
        if (last != Long.MIN_VALUE && now - last < 1_000_000_000L) return false;
        Path request = root.resolve("request-" + next + ".json");
        if (!Files.exists(request)) return false;
        SettingsFiles.safeExisting(request);
        if (!Files.isRegularFile(request) || Files.size(request) > 4096) throw new IOException("FRAME_REQUEST_QUOTA");
        String text;
        try (var stream = Files.newInputStream(request)) {
            byte[] bytes = stream.readNBytes(4097);
            if (bytes.length > 4096) throw new IOException("FRAME_REQUEST_QUOTA");
            text = StandardCharsets.UTF_8.newDecoder().decode(ByteBuffer.wrap(bytes)).toString();
        }
        JsonObject command = SettingsJson.read(text);
        SettingsJson.fields(command, "schema", "session_id", "sequence", "expires_unix_ms", "expected_screen");
        long expires = SettingsJson.integer(command, "expires_unix_ms");
        if (!"strata/PrivateFrameRequest/1".equals(SettingsJson.string(command, "schema"))
                || !session.equals(SettingsJson.string(command, "session_id"))
                || SettingsJson.integer(command, "sequence") != next) throw new IOException("FRAME_REQUEST_MISMATCH");
        long remaining = expires - wall.getAsLong();
        if (remaining <= 0 || remaining > 10_000) throw new IOException("FRAME_REQUEST_EXPIRED");
        long captureDeadline = now + remaining * 1_000_000L;
        if (screen == null || screen.length() > 256 || !screen.equals(SettingsJson.string(command, "expected_screen")))
            throw new IOException("FRAME_SCREEN_MISMATCH");
        if (width < 1 || width > 1920 || height < 1 || height > 1080 || frame < 1)
            throw new IOException("FRAME_DIMENSIONS_UNSUPPORTED");
        var intent = base("strata/PrivateFrameIntent/1");
        intent.addProperty("sequence", next); intent.addProperty("request_sha256", KeyOptions.sha256(text));
        intent.addProperty("screen_class", screen); intent.addProperty("world_connected", world);
        intent.addProperty("width", width); intent.addProperty("height", height);
        intent.addProperty("native_frame", Long.toString(frame));
        // Intent is durable before GPU readback. Any failure makes this session terminal.
        write("intent-" + next + ".json", intent);
        failed = true;
        byte[] png = source.read();
        validatePng(png, width, height);
        SettingsFiles.writeNew(root.resolve("frame-" + next + ".png"), png);
        if (wall.getAsLong() >= expires || nano.getAsLong() - captureDeadline >= 0
                || nano.getAsLong() - started > LIFETIME_NS)
            throw new IOException("FRAME_REQUEST_EXPIRED");
        var receipt = base("strata/PrivateFrame/1");
        receipt.add("capture", intent);
        receipt.addProperty("status", "captured");
        receipt.addProperty("png_sha256", java.util.HexFormat.of().formatHex(sha(png)));
        receipt.addProperty("png_bytes", png.length);
        receipt.addProperty("capture_elapsed_ns", Long.toString(nano.getAsLong() - now));
        write("frame-" + next + ".json", receipt);
        next++; last = nano.getAsLong(); failed = false;
        return true;
    }

    static void validatePng(byte[] bytes, int width, int height) throws IOException {
        if (bytes == null || bytes.length < 33 || bytes.length > MAX_PNG)
            throw new IOException("FRAME_PNG_QUOTA");
        ByteBuffer buffer = ByteBuffer.wrap(bytes);
        if (buffer.getLong() != 0x89504e470d0a1a0aL || buffer.getInt() != 13
                || buffer.getInt() != 0x49484452 || buffer.getInt() != width || buffer.getInt() != height)
            throw new IOException("FRAME_PNG_MISMATCH");
        // Full PNG decoding/reference comparison belongs to the external verifier.
    }

    private static byte[] sha(byte[] bytes) {
        try { return java.security.MessageDigest.getInstance("SHA-256").digest(bytes); }
        catch (java.security.NoSuchAlgorithmException impossible) { throw new IllegalStateException(impossible); }
    }

    void fail(String reason) {
        failed = true;
        try {
            var value = base("strata/PrivateFrameFailure/1");
            value.addProperty("sequence", next);
            value.addProperty("reason", reason != null && reason.matches("[A-Z][A-Z0-9_]{1,95}") ? reason : "FRAME_CAPTURE_FAILED");
            write("failure.json", value);
        } catch (IOException ignored) { /* No retry, overwrite or game mutation on evidence failure. */ }
    }
}
