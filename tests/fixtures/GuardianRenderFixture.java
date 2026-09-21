import static org.lwjgl.glfw.GLFW.*;
import static org.lwjgl.opengl.GL11.*;
import static org.lwjgl.opengl.NVXGPUMemoryInfo.*;
import static org.lwjgl.openal.AL10.*;
import static org.lwjgl.openal.ALC10.*;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import java.nio.ByteBuffer;
import java.nio.MappedByteBuffer;
import java.nio.channels.FileChannel;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import org.lwjgl.glfw.GLFWErrorCallback;
import org.lwjgl.opengl.GL;
import org.lwjgl.openal.AL;
import org.lwjgl.openal.ALC;
import org.lwjgl.system.MemoryUtil;

/** Operator fixture based on DesktopRenderFixture; remains alive for forced guardian stop. */
public final class GuardianRenderFixture {
    private static volatile byte[][] retained;
    private static final int FILE_COUNT = 2048, FILE_BYTES = 65536;
    private static volatile FileChannel[] retainedFiles;
    private static volatile MappedByteBuffer[] retainedMaps;

    private static void holdFiles(Path root, String mode, JsonObject result) throws Exception {
        if (mode.equals("none")) return;
        Path data = root.resolve("fixture-data.bin");
        byte[] bytes = new byte[FILE_BYTES];
        for (int i = 0; i < bytes.length; i++) bytes[i] = (byte) (i * 31 + 17);
        try (var file = FileChannel.open(data, StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE)) {
            var buffer = ByteBuffer.wrap(bytes);
            while (buffer.hasRemaining()) file.write(buffer);
            file.force(true);
        }
        int checked = 0;
        if (mode.equals("channels-2048")) {
            retainedFiles = new FileChannel[FILE_COUNT];
            var buffer = ByteBuffer.allocate(1);
            for (int i = 0; i < FILE_COUNT; i++) {
                var file = FileChannel.open(data, StandardOpenOption.READ);
                retainedFiles[i] = file;
                buffer.clear();
                if (file.size() != FILE_BYTES || file.read(buffer, 0) != 1 || buffer.get(0) != 17)
                    throw new IllegalStateException("FILE_RESOURCE_MISMATCH");
                checked++;
            }
        } else {
            retainedMaps = new MappedByteBuffer[FILE_COUNT];
            for (int i = 0; i < FILE_COUNT; i++) {
                // This pinned Windows JDK duplicates a handle for each mapping. Close
                // the original channel, retaining the mapped buffer until process exit.
                try (var file = FileChannel.open(data, StandardOpenOption.READ)) {
                    var map = file.map(FileChannel.MapMode.READ_ONLY, 0, FILE_BYTES);
                    retainedMaps[i] = map;
                    if (!map.isReadOnly() || map.capacity() != FILE_BYTES)
                        throw new IllegalStateException("MAPPED_RESOURCE_MISMATCH");
                    for (int offset = 0; offset < FILE_BYTES; offset += 4096)
                        if (map.get(offset) != bytes[offset])
                            throw new IllegalStateException("MAPPED_RESOURCE_MISMATCH");
                    checked++;
                }
            }
        }
        result.addProperty("file_resources_checked", checked);
        result.addProperty("fixture_file_bytes", FILE_BYTES);
        result.addProperty("mapped_view_bytes", mode.equals("maps-2048") ? FILE_BYTES * FILE_COUNT : 0);
        result.addProperty("file_access", "read-only");
    }

    private static void publish(Path path, JsonObject value) throws Exception {
        Path pending = path.resolveSibling(path.getFileName() + ".pending");
        try (var stream = FileChannel.open(pending, StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE)) {
            ByteBuffer bytes = StandardCharsets.UTF_8.encode(value.toString());
            while (bytes.hasRemaining()) stream.write(bytes);
            stream.force(true);
        }
        Files.move(pending, path); // Fresh paths only; never overwrite previous evidence.
    }

    private static void checkWindow(long window) {
        if (glfwGetWindowAttrib(window, GLFW_VISIBLE) != GLFW_FALSE
                || glfwGetWindowAttrib(window, GLFW_FOCUSED) != GLFW_FALSE)
            throw new IllegalStateException("UNEXPECTED_WINDOW_STATE");
    }

    public static void main(String[] args) throws Exception {
        if (args.length != 6 || !(args[4].equals("true") || args[4].equals("false")))
            throw new IllegalArgumentException("FIXTURE_ARGUMENTS");
        Path root = Path.of(args[0]);
        int heap = Integer.parseInt(args[1]), texture = Integer.parseInt(args[2]);
        String scope = args[3];
        boolean audio = Boolean.parseBoolean(args[4]);
        String fileMode = args[5];
        if (!root.isAbsolute() || !Files.isDirectory(root) || !scope.matches("[0-9a-f]{32}")
                || !(heap == 0 || heap == 3072) || !(texture == 0 || texture == 256 || texture == 1024)
                || !(fileMode.equals("none") || fileMode.equals("channels-2048") || fileMode.equals("maps-2048"))
                || (!fileMode.equals("none") && !(heap == 3072 && texture == 1024 && audio)))
            throw new IllegalArgumentException("FIXTURE_ARGUMENTS");
        var result = new JsonObject(); result.addProperty("schema", "strata/GuardianRenderFixture/3");
        result.addProperty("scope", scope); result.addProperty("pid", ProcessHandle.current().pid());
        result.addProperty("minecraft", false); result.addProperty("visible", false);
        result.addProperty("heap_mib", heap); result.addProperty("texture_mib", texture);
        result.addProperty("audio", audio);
        result.addProperty("file_mode", fileMode);
        publish(root.resolve("boot.json"), result);
        long armDeadline = System.nanoTime() + 10_000_000_000L;
        while (!Files.exists(root.resolve("armed"))) {
            if (System.nanoTime() >= armDeadline) throw new IllegalStateException("ARM_TIMEOUT");
            Thread.sleep(10);
        }
        if (!Files.readString(root.resolve("armed")).equals(scope))
            throw new IllegalStateException("ARM_MISMATCH");

        final int[] error = {0};
        var callback = GLFWErrorCallback.create((code, message) -> error[0] = code);
        long window = 0; boolean initialized = false; ByteBuffer pixel = null, upload = null;
        long audioDevice = 0, audioContext = 0;
        int audioBuffer = 0, audioSource = 0;
        int[] textures = new int[texture / 16];
        try {
            glfwSetErrorCallback(callback);
            if (!glfwInit()) throw new IllegalStateException("GLFW_INIT_FAILED");
            initialized = true; glfwDefaultWindowHints();
            glfwWindowHint(GLFW_VISIBLE, GLFW_FALSE); glfwWindowHint(GLFW_FOCUSED, GLFW_FALSE);
            glfwWindowHint(GLFW_FOCUS_ON_SHOW, GLFW_FALSE);
            glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR, 3); glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, 2);
            glfwWindowHint(GLFW_OPENGL_PROFILE, GLFW_OPENGL_CORE_PROFILE);
            glfwWindowHint(GLFW_OPENGL_FORWARD_COMPAT, GLFW_TRUE);
            window = glfwCreateWindow(64, 64, "Strata guardian graphics fixture", 0, 0);
            if (window == 0) throw new IllegalStateException("GLFW_CONTEXT_FAILED");
            glfwMakeContextCurrent(window); GL.createCapabilities(); glfwSwapInterval(0);
            result.addProperty("gl_version", glGetString(GL_VERSION));
            result.addProperty("gl_vendor", glGetString(GL_VENDOR));
            result.addProperty("gl_renderer", glGetString(GL_RENDERER));
            if (audio) {
                audioDevice = alcOpenDevice((ByteBuffer) null);
                if (audioDevice == 0) throw new IllegalStateException("AUDIO_DEVICE_UNAVAILABLE");
                var capabilities = ALC.createCapabilities(audioDevice);
                audioContext = alcCreateContext(audioDevice, (java.nio.IntBuffer) null);
                if (audioContext == 0 || !alcMakeContextCurrent(audioContext))
                    throw new IllegalStateException("AUDIO_CONTEXT_UNAVAILABLE");
                AL.createCapabilities(capabilities);
                result.addProperty("al_version", alGetString(AL_VERSION));
                result.addProperty("al_renderer", alGetString(AL_RENDERER));
                result.addProperty("al_device", alcGetString(audioDevice, ALC_DEVICE_SPECIFIER));
                audioBuffer = alGenBuffers(); audioSource = alGenSources();
                ByteBuffer silence = MemoryUtil.memCalloc(4410 * 2);
                try { alBufferData(audioBuffer, AL_FORMAT_MONO16, silence, 44100); }
                finally { MemoryUtil.memFree(silence); }
                alSourcei(audioSource, AL_BUFFER, audioBuffer);
                alSourcei(audioSource, AL_LOOPING, AL_TRUE);
                alSourcef(audioSource, AL_GAIN, 0.0f); // Only this fixture's source; no system volume change.
                alSourcePlay(audioSource);
                if (alGetError() != AL_NO_ERROR || alcGetError(audioDevice) != ALC_NO_ERROR
                        || alGetSourcei(audioSource, AL_SOURCE_STATE) != AL_PLAYING)
                    throw new IllegalStateException("SILENT_AUDIO_NOT_PLAYING");
            }
            if (texture != 0) {
                if (!GL.getCapabilities().GL_NVX_gpu_memory_info)
                    throw new IllegalStateException("GPU_HEADROOM_UNAVAILABLE");
                int free = glGetInteger(GL_GPU_MEMORY_INFO_CURRENT_AVAILABLE_VIDMEM_NVX);
                result.addProperty("gpu_free_kib_before", free);
                if (free < (2048 + texture) * 1024 || glGetInteger(GL_MAX_TEXTURE_SIZE) < 2048)
                    throw new IllegalStateException("GPU_HEADROOM_INSUFFICIENT");
                upload = MemoryUtil.memAlloc(16 * 1024 * 1024);
                for (int i = 0; i < upload.capacity(); i += 4) upload.putInt(i, 0x19750921 ^ i);
                for (int i = 0; i < textures.length; i++) {
                    upload.putInt(0, i);
                    textures[i] = glGenTextures(); glBindTexture(GL_TEXTURE_2D, textures[i]);
                    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST);
                    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST);
                    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA8, 2048, 2048, 0, GL_RGBA, GL_UNSIGNED_BYTE, upload);
                    if (glGetTexLevelParameteri(GL_TEXTURE_2D, 0, GL_TEXTURE_WIDTH) != 2048
                            || glGetError() != GL_NO_ERROR) throw new IllegalStateException("TEXTURE_ALLOCATION_FAILED");
                }
                glFinish(); glBindTexture(GL_TEXTURE_2D, 0);
                result.addProperty("gpu_free_kib_loaded", glGetInteger(GL_GPU_MEMORY_INFO_CURRENT_AVAILABLE_VIDMEM_NVX));
            }
            retained = new byte[heap / 16][];
            for (int i = 0; i < retained.length; i++) {
                byte[] block = new byte[16 * 1024 * 1024];
                for (int j = 0; j < block.length; j += 4096) block[j] = 1;
                retained[i] = block;
            }
            holdFiles(root, fileMode, result);
            pixel = MemoryUtil.memAlloc(4);
            glDisable(GL_DITHER); glViewport(0, 0, 64, 64);
            var samples = new JsonArray();
            for (int i = 0; i < 20; i++) {
                float red = i % 2 == 0 ? 0.25f : 0.75f;
                glClearColor(red, 0.5f, 0.125f, 1f); glClear(GL_COLOR_BUFFER_BIT);
                glReadBuffer(GL_BACK); glReadPixels(32, 32, 1, 1, GL_RGBA, GL_UNSIGNED_BYTE, pixel);
                int r = Byte.toUnsignedInt(pixel.get(0)), g = Byte.toUnsignedInt(pixel.get(1));
                int b = Byte.toUnsignedInt(pixel.get(2)), a = Byte.toUnsignedInt(pixel.get(3));
                if (Math.abs(r - Math.round(red * 255)) > 1 || Math.abs(g - 128) > 1
                        || Math.abs(b - 32) > 1 || a != 255 || glGetError() != GL_NO_ERROR)
                    throw new IllegalStateException("PIXEL_MISMATCH");
                checkWindow(window); samples.add(r); glfwSwapBuffers(window); glfwPollEvents();
                Thread.sleep(17);
            }
            result.add("red_samples", samples); result.addProperty("frames", 20);
            if (audio) {
                if (alGetSourcei(audioSource, AL_SOURCE_STATE) != AL_PLAYING
                        || alGetSourcef(audioSource, AL_GAIN) != 0.0f || alGetError() != AL_NO_ERROR)
                    throw new IllegalStateException("SILENT_AUDIO_NOT_PLAYING");
                result.addProperty("audio_state", "playing"); result.addProperty("silent_pcm", true);
                result.addProperty("source_gain", 0);
            }
            result.addProperty("status", "ready"); result.addProperty("resources_held", true);
            publish(root.resolve("ready.json"), result);
            long stopDeadline = System.nanoTime() + 20_000_000_000L;
            while (System.nanoTime() < stopDeadline) {
                checkWindow(window); glClear(GL_COLOR_BUFFER_BIT);
                glfwSwapBuffers(window); glfwPollEvents(); Thread.sleep(17);
            }
            throw new IllegalStateException("GUARDIAN_DID_NOT_STOP");
        } catch (Throwable failure) {
            result.addProperty("status", "fail"); result.addProperty("failure_class", failure.getClass().getSimpleName());
            result.addProperty("failure", failure instanceof IllegalStateException ? failure.getMessage() : "RENDER_UNAVAILABLE");
        } finally {
            if (retainedFiles != null)
                for (var file : retainedFiles) if (file != null) file.close();
            if (audioContext != 0) {
                if (audioSource != 0) { alSourceStop(audioSource); alDeleteSources(audioSource); }
                if (audioBuffer != 0) alDeleteBuffers(audioBuffer);
                alcMakeContextCurrent(0); alcDestroyContext(audioContext);
            }
            if (audioDevice != 0) alcCloseDevice(audioDevice);
            if (pixel != null) MemoryUtil.memFree(pixel);
            if (upload != null) MemoryUtil.memFree(upload);
            if (window != 0) { for (int textureId : textures) if (textureId != 0) glDeleteTextures(textureId); glfwDestroyWindow(window); }
            if (initialized) glfwTerminate();
            glfwSetErrorCallback(null); callback.free();
            // MappedByteBuffer has no supported explicit close; retain its strong
            // references and report that release still requires terminal process proof.
            result.addProperty("resources_held", retainedMaps != null);
            result.addProperty("mapping_release_requires_exit", retainedMaps != null);
            result.addProperty("glfw_error", error[0]);
            publish(root.resolve("terminal.json"), result);
        }
    }
}
