package io.github.opencnid.strata.client;

import com.mojang.blaze3d.platform.InputConstants;
import io.github.opencnid.strata.client.mixin.MouseInputInvoker;
import java.io.IOException;
import java.util.Set;
import net.minecraft.client.KeyMapping;
import net.minecraft.client.Minecraft;
import org.lwjgl.glfw.GLFW;

/** Candidate callback/polling input backend. No public capability or tested pool is implied. */
public final class NativeKeyInput implements KeyInputSession.Port {
    static final String POLICY = "native-window-key-mouse-sprint-companion/6";
    private static volatile NativeKeyInput active;
    private final Minecraft client;
    private final Thread owner;
    private final long window;
    private final Object level, player, connection;
    private final KeyPollingState polling;
    private KeyInputSession session;

    static void install() {
        net.minecraftforge.common.MinecraftForge.EVENT_BUS.addListener(
            (net.minecraftforge.event.GameShuttingDownEvent event) -> {
                try { stopActive(); }
                catch (IOException error) { throw new IllegalStateException("STRATA_KEY_INPUT_RELEASE_FAILED", error); }
            });
        net.minecraftforge.common.MinecraftForge.EVENT_BUS.addListener(
            (net.minecraftforge.event.TickEvent.ClientTickEvent event) -> {
                NativeKeyInput input = active;
                if (event.phase != net.minecraftforge.event.TickEvent.Phase.START
                        || input == null || input.session == null) return;
                try { input.session.watchdog(); }
                catch (IOException error) {
                    // Session retains the typed failure. If release failed, stop this worker.
                    if (active != null || "SETTINGS_INPUT_RELEASE_UNCONFIRMED".equals(error.getMessage())
                            || error.getSuppressed().length != 0) {
                        throw new IllegalStateException("STRATA_KEY_INPUT_RELEASE_FAILED", error);
                    }
                }
            });
    }

    private NativeKeyInput(Minecraft client) throws IOException {
        this.client = client; owner = Thread.currentThread();
        window = client.getWindow().getWindow();
        polling = new KeyPollingState(window);
        level = client.level; player = client.player; connection = client.getConnection();
        validate();
    }
    static KeyInputSession start(Minecraft client, KeyInputSession.Request request,
            Set<Integer> candidatePool, GameActionLane.Emitter emitter,
            GameActionLane.Emitter safetyEmitter) throws IOException {
        if (!client.isSameThread()) throw new IOException("CLIENT_THREAD_REQUIRED");
        if (active != null) throw new IOException("SETTINGS_INPUT_BUSY");
        candidatePool = Set.copyOf(candidatePool);
        request.validate(candidatePool);
        for (int key : candidatePool) {
            if (!(request.device() == KeyInputSession.Device.MOUSE && key == request.key())
                    && GLFW.glfwGetKeyScancode(key) < 0) throw new IOException("SETTINGS_INPUT_UNSUPPORTED");
        }
        if (client.mouseHandler.isLeftPressed() || client.mouseHandler.isMiddlePressed() || client.mouseHandler.isRightPressed())
            throw new IOException("SETTINGS_INPUT_BUSY");
        if (request.device() == KeyInputSession.Device.MOUSE) {
            if (!(client.mouseHandler instanceof MouseInputInvoker)) throw new IOException("SETTINGS_INPUT_MOUSE_HOOK_MISSING");
            if (client.screen != null || !client.mouseHandler.isMouseGrabbed()) throw new IOException("SETTINGS_CONTEXT_UNVERIFIED");
        }
        NativeKeyInput input = new NativeKeyInput(client);
        for (KeyMapping mapping : client.options.keyMappings) {
            if (mapping.isDown()) throw new IOException("SETTINGS_INPUT_BUSY");
        }
        active = input;
        try {
            // Fail before any key event if the exact polling hook was not transformed.
            long before = input.polling.polls();
            InputConstants.isKeyDown(input.window, GLFW.GLFW_KEY_LEFT_SHIFT);
            if (input.polling.polls() != before + 1) throw new IOException("SETTINGS_INPUT_POLL_HOOK_MISSING");
            input.session = KeyInputSession.start(input, request, candidatePool, emitter, safetyEmitter);
            return input.session;
        } catch (IOException | RuntimeException | Error error) {
            // start() cleans up every attempted callback itself. Before it starts,
            // undo only polling ownership; do not mutate unrelated logical inputs.
            if (active == input) {
                input.polling.close(); active = null;
            }
            throw error;
        }
    }

    /** Called only by the exact InputConstants mixin; other windows/threads retain native behavior. */
    public static Boolean polled(long window, int key) {
        NativeKeyInput input = active;
        return input == null ? null : input.polling.polled(window, key);
    }
    static void stopActive() throws IOException {
        NativeKeyInput input = active;
        if (input == null) return;
        if (!input.client.isSameThread()) throw new IOException("CLIENT_THREAD_REQUIRED");
        if (input.session != null) input.session.cancel(); else input.clear();
    }
    @Override public void validate() throws IOException {
        if (!client.isSameThread() || owner != Thread.currentThread()) throw new IOException("CLIENT_THREAD_REQUIRED");
        if (level == null || player == null || connection == null || client.level != level
                || client.player != player || client.getConnection() != connection
                || client.getWindow().getWindow() != window || !client.isWindowActive()
                || client.noRender || client.getOverlay() != null) {
            throw new IOException("SETTINGS_INPUT_CONTEXT_CHANGED");
        }
    }
    @Override public long monotonicMillis() { return System.nanoTime() / 1000000; }
    @Override public void event(int key, boolean pressed, int modifiers) throws IOException {
        if (!client.isSameThread()) throw new IOException("CLIENT_THREAD_REQUIRED");
        if (pressed) validate();
        polling.event(key, pressed);
        client.keyboardHandler.keyPress(window, key, GLFW.glfwGetKeyScancode(key),
            pressed ? GLFW.GLFW_PRESS : GLFW.GLFW_RELEASE, modifiers);
    }
    @Override public void mouseEvent(int button, boolean pressed, int modifiers) throws IOException {
        if (!client.isSameThread()) throw new IOException("CLIENT_THREAD_REQUIRED");
        if (!(client.mouseHandler instanceof MouseInputInvoker callback)) throw new IOException("SETTINGS_INPUT_MOUSE_HOOK_MISSING");
        if (pressed) {
            validate();
            if (client.screen != null || !client.mouseHandler.isMouseGrabbed()) throw new IOException("SETTINGS_CONTEXT_UNVERIFIED");
        }
        callback.strata$button(window, button, pressed ? GLFW.GLFW_PRESS : GLFW.GLFW_RELEASE, modifiers);
    }
    @Override public void clear() throws IOException {
        if (!client.isSameThread()) throw new IOException("CLIENT_THREAD_REQUIRED");
        polling.clear();
        // Keep the empty polling view until logical state has also been released.
        try {
            KeyMapping.releaseAll();
            if (client.player != null && client.player.input != null) {
                var state = client.player.input;
                state.up = false; state.down = false; state.left = false; state.right = false;
                state.jumping = false; state.shiftKeyDown = false;
                state.forwardImpulse = 0; state.leftImpulse = 0;
            }
            if (client.gameMode != null) {
                client.gameMode.stopDestroyBlock();
                if (client.player != null && client.player.isUsingItem()) client.gameMode.releaseUsingItem(client.player);
            }
            for (KeyMapping mapping : client.options.keyMappings) {
                int count = 0;
                while (mapping.consumeClick()) if (++count > 2048) throw new IOException("SETTINGS_INPUT_QUEUE_UNBOUNDED");
                if (mapping.isDown()) throw new IOException("SETTINGS_INPUT_RELEASE_UNCONFIRMED");
            }
            if (client.mouseHandler.isLeftPressed() || client.mouseHandler.isMiddlePressed() || client.mouseHandler.isRightPressed())
                throw new IOException("SETTINGS_INPUT_RELEASE_UNCONFIRMED");
        } finally { polling.close(); if (active == this) active = null; }
    }
}
