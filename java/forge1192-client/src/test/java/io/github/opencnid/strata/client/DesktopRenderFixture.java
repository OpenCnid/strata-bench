package io.github.opencnid.strata.client;

import static org.lwjgl.glfw.GLFW.*;
import static org.lwjgl.opengl.GL11.*;
import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import java.nio.ByteBuffer;
import java.nio.file.Files;
import java.nio.file.Path;
import org.lwjgl.glfw.GLFWErrorCallback;
import org.lwjgl.opengl.GL;
import org.lwjgl.system.MemoryUtil;

/** Explicit operator test only, excluded from mod JAR. No Minecraft, input injection or screenshots. */
public final class DesktopRenderFixture {
    public static void main(String[] args) throws Exception {
        if (args.length != 1) throw new IllegalArgumentException("FIXTURE_ARGUMENTS");
        var result = new JsonObject(); result.addProperty("schema", "strata/DesktopRenderFixture/1");
        result.addProperty("minecraft", false); result.addProperty("visible", false);
        final int[] error = {0};
        var callback = GLFWErrorCallback.create((code, message) -> error[0] = code);
        long window = 0; boolean initialized = false; ByteBuffer pixel = null;
        long started = System.nanoTime();
        try {
            glfwSetErrorCallback(callback);
            if (!glfwInit()) throw new IllegalStateException("GLFW_INIT_FAILED");
            initialized = true; glfwDefaultWindowHints();
            glfwWindowHint(GLFW_VISIBLE, GLFW_FALSE); glfwWindowHint(GLFW_FOCUSED, GLFW_FALSE);
            glfwWindowHint(GLFW_FOCUS_ON_SHOW, GLFW_FALSE);
            glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR, 3); glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, 2);
            glfwWindowHint(GLFW_OPENGL_PROFILE, GLFW_OPENGL_CORE_PROFILE);
            glfwWindowHint(GLFW_OPENGL_FORWARD_COMPAT, GLFW_TRUE);
            window = glfwCreateWindow(64, 64, "Strata disposable renderer", 0, 0);
            if (window == 0) throw new IllegalStateException("GLFW_CONTEXT_FAILED");
            glfwMakeContextCurrent(window); GL.createCapabilities(); glfwSwapInterval(0);
            result.addProperty("gl_version", glGetString(GL_VERSION));
            result.addProperty("gl_vendor", glGetString(GL_VENDOR));
            result.addProperty("gl_renderer", glGetString(GL_RENDERER));
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
                if (glfwGetWindowAttrib(window, GLFW_VISIBLE) != GLFW_FALSE
                        || glfwGetWindowAttrib(window, GLFW_FOCUSED) != GLFW_FALSE)
                    throw new IllegalStateException("UNEXPECTED_WINDOW_STATE");
                samples.add(r); glfwSwapBuffers(window); glfwPollEvents();
            }
            result.add("red_samples", samples); result.addProperty("frames", 20);
            result.addProperty("status", "pass");
        } catch (Throwable failure) {
            result.addProperty("status", "fail"); result.addProperty("failure_class", failure.getClass().getSimpleName());
            result.addProperty("failure", failure instanceof IllegalStateException ? failure.getMessage() : "RENDER_UNAVAILABLE");
        } finally {
            if (pixel != null) MemoryUtil.memFree(pixel);
            if (window != 0) glfwDestroyWindow(window);
            if (initialized) glfwTerminate();
            glfwSetErrorCallback(null); callback.free();
            result.addProperty("glfw_error", error[0]);
            result.addProperty("elapsed_ms", (System.nanoTime() - started) / 1_000_000L);
        }
        Files.writeString(Path.of(args[0]), result.toString());
    }
}
