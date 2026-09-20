package io.github.opencnid.strata.client;

import static org.junit.jupiter.api.Assertions.*;
import com.google.gson.JsonObject;
import java.awt.image.BufferedImage;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.concurrent.atomic.AtomicLong;
import javax.imageio.ImageIO;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

/** Synthetic PNG/clock producer; does not qualify native Minecraft/GL capture. */
final class PrivateFramesTest {
    @TempDir Path temp;
    final AtomicLong nano = new AtomicLong(1_000_000_000L), wall = new AtomicLong(1000);
    int directories;
    Path root, profile;
    PrivateFrames open() throws IOException {
        root = Files.createDirectory(temp.resolve("frames-" + ++directories));
        profile = Files.createDirectory(temp.resolve("profile-" + directories));
        return new PrivateFrames(root, profile, "a".repeat(64), nano::get, wall::get);
    }
    JsonObject request(PrivateFrames store, int sequence) {
        var value = new JsonObject(); value.addProperty("schema", "strata/PrivateFrameRequest/1");
        value.addProperty("session_id", store.session); value.addProperty("sequence", sequence);
        value.addProperty("expires_unix_ms", wall.get() + 5000); value.addProperty("expected_screen", "synthetic.Screen");
        return value;
    }
    void put(JsonObject value, int sequence) throws IOException {
        Files.writeString(root.resolve("request-" + sequence + ".json"), value.toString());
    }
    static byte[] png() throws IOException {
        var image = new BufferedImage(2, 1, BufferedImage.TYPE_INT_ARGB);
        image.setRGB(0, 0, 0xffcc2244); image.setRGB(1, 0, 0xff113388);
        var output = new ByteArrayOutputStream(); assertTrue(ImageIO.write(image, "png", output));
        return output.toByteArray();
    }
    boolean capture(PrivateFrames store) throws IOException {
        return store.capture("synthetic.Screen", false, 2, 1, 1, PrivateFramesTest::png);
    }

    @Test void requestBoundReceiptPixelsAndNoReplay() throws Exception {
        var store = open(); assertFalse(capture(store));
        put(request(store, 1), 1); assertTrue(capture(store));
        assertFalse(capture(store)); nano.addAndGet(1_000_000_000L); assertFalse(capture(store));
        var receipt = SettingsJson.read(Files.readString(root.resolve("frame-1.json")));
        assertEquals("captured", receipt.get("status").getAsString());
        assertEquals("synthetic.Screen", receipt.getAsJsonObject("capture").get("screen_class").getAsString());
        assertFalse(receipt.get("gameplay_image_capability").getAsBoolean());
        assertEquals(0xffcc2244, ImageIO.read(root.resolve("frame-1.png").toFile()).getRGB(0, 0));
        assertEquals(64, receipt.get("png_sha256").getAsString().length());
        assertTrue(Files.isRegularFile(root.resolve("intent-1.json")));
    }

    @Test void countAndMinimumSpacingBoundSourceCalls() throws Exception {
        var store = open();
        for (int i = 1; i <= 4; i++) {
            put(request(store, i), i);
            if (i > 1) assertFalse(capture(store));
            nano.addAndGet(1_000_000_000L); assertTrue(capture(store));
        }
        put(request(store, 5), 5); nano.addAndGet(1_000_000_000L);
        assertFalse(store.capture("synthetic.Screen", false, 2, 1, 1, () -> { fail("fifth source call"); return null; }));
        assertFalse(Files.exists(root.resolve("frame-5.png")));
    }

    @Test void strictFieldsTypesSessionSequenceAndDeadline() throws Exception {
        for (int kind = 0; kind < 7; kind++) {
            var store = open(); var value = request(store, 1);
            switch (kind) {
                case 0 -> value.addProperty("session_id", "wrong");
                case 1 -> value.addProperty("sequence", 2);
                case 2 -> value.addProperty("sequence", true);
                case 3 -> value.addProperty("extra", "forbidden");
                case 4 -> value.addProperty("expires_unix_ms", wall.get());
                case 5 -> value.addProperty("expires_unix_ms", wall.get() + 10_001);
                case 6 -> value.addProperty("schema", "unknown");
            }
            put(value, 1);
            assertThrows(IOException.class, () -> capture(store));
            assertFalse(Files.exists(root.resolve("intent-1.json")));
        }
    }

    @Test void duplicateMalformedAndOversizeRequestsReject() throws Exception {
        for (String content : new String[]{"{\"x\":1,\"x\":2}", "{", "x".repeat(4097)}) {
            var store = open(); Files.writeString(root.resolve("request-1.json"), content);
            assertThrows(IOException.class, () -> capture(store));
            assertFalse(Files.exists(root.resolve("frame-1.png")));
        }
    }

    @Test void changedScreenAndUnsupportedSizeCannotReadPixels() throws Exception {
        for (int kind = 0; kind < 4; kind++) {
            var store = open(); put(request(store, 1), 1);
            String screen = kind == 0 ? "different.Screen" : "synthetic.Screen";
            int width = kind == 1 ? 1921 : 2, height = kind == 2 ? 1081 : 1;
            long frame = kind == 3 ? 0 : 1;
            assertThrows(IOException.class, () -> store.capture(screen, false, width, height, frame,
                () -> { fail("pixels read before validation"); return null; }));
        }
    }

    @Test void sourceFailureHasIntentAndNoReplay() throws Exception {
        var store = open(); put(request(store, 1), 1);
        assertThrows(IOException.class, () -> store.capture("synthetic.Screen", false, 2, 1, 1,
            () -> { throw new IOException("FRAME_SYNTHETIC_FAILURE"); }));
        assertTrue(Files.isRegularFile(root.resolve("intent-1.json")));
        assertFalse(Files.exists(root.resolve("frame-1.json"))); assertFalse(capture(store));
        store.fail("message containing a private path");
        assertEquals("FRAME_CAPTURE_FAILED", SettingsJson.read(Files.readString(root.resolve("failure.json")))
            .get("reason").getAsString());
    }

    @Test void sessionAndMidCaptureExpiryNeverPublishSuccess() throws Exception {
        var expired = open(); put(request(expired, 1), 1); nano.addAndGet(PrivateFrames.LIFETIME_NS + 1);
        assertThrows(IOException.class, () -> capture(expired));
        var store = open(); put(request(store, 1), 1);
        assertThrows(IOException.class, () -> store.capture("synthetic.Screen", false, 2, 1, 1,
            () -> { wall.addAndGet(5000); return png(); }));
        assertTrue(Files.exists(root.resolve("frame-1.png"))); // Retained partial evidence, no completed receipt.
        assertFalse(Files.exists(root.resolve("frame-1.json"))); assertFalse(capture(store));
    }

    @Test void privateDisjointEmptyRootAndRestartRequired() throws Exception {
        var store = open();
        assertThrows(IOException.class, () -> new PrivateFrames(root, profile, "a".repeat(64), nano::get, wall::get));
        assertThrows(IOException.class, () -> new PrivateFrames(profile, profile, "a".repeat(64), nano::get, wall::get));
        assertThrows(IOException.class, () -> new PrivateFrames(temp, profile, "a".repeat(64), nano::get, wall::get));
        var session = SettingsJson.read(Files.readString(root.resolve("session.json")));
        assertEquals(store.session, session.get("session_id").getAsString());
        assertEquals(4, session.get("max_frames").getAsInt());
    }

    @Test void backwardWallClockCannotExtendCaptureDeadline() throws Exception {
        var store = open(); put(request(store, 1), 1);
        assertThrows(IOException.class, () -> store.capture("synthetic.Screen", false, 2, 1, 1,
            () -> { nano.addAndGet(5_000_000_000L); wall.addAndGet(-500); return png(); }));
        assertFalse(Files.exists(root.resolve("frame-1.json")));
        assertFalse(capture(store));
    }

    @Test void corruptMismatchedAndOversizePngReject() throws Exception {
        assertThrows(IOException.class, () -> PrivateFrames.validatePng(new byte[0], 2, 1));
        assertThrows(IOException.class, () -> PrivateFrames.validatePng(new byte[PrivateFrames.MAX_PNG + 1], 2, 1));
        assertThrows(IOException.class, () -> PrivateFrames.validatePng(png(), 3, 1));
        byte[] corrupt = png(); corrupt[0] = 0;
        assertThrows(IOException.class, () -> PrivateFrames.validatePng(corrupt, 2, 1));
        PrivateFrames.validatePng(png(), 2, 1);
    }
}
