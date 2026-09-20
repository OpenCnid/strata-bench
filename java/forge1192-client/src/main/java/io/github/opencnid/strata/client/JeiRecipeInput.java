package io.github.opencnid.strata.client;

import java.io.IOException;
import java.util.List;
import java.util.Optional;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.screens.Screen;

/** Observes ordinary public JEI routing. It never obtains a router/handler through private fields. */
public final class JeiRecipeInput {
    private static final String BUTTON = "mezz.jei.gui.elements.GuiIconButton";
    private static final String HANDLER = BUTTON + "$UserInputHandler";
    private static final String ROUTER = "mezz.jei.gui.input.handlers.UserInputRouter";
    private static final GameRecipeInput.Registry registry = new GameRecipeInput.Registry();
    private static final GameRecipeInput.Ownership ownership = new GameRecipeInput.Ownership();
    private JeiRecipeInput() {}
    private static boolean thread() { return Minecraft.getInstance().isSameThread(); }
    private static boolean exact(Object value, String name) { return value != null && value.getClass().getName().equals(name); }
    public static void factory(Object widget, Object handler) {
        if (thread() && exact(widget, BUTTON) && exact(handler, HANDLER)) registry.factory(widget, handler);
    }
    public static void router(Object router, String name, Object handlers) {
        if (thread() && exact(router, ROUTER) && handlers instanceof Object[] array) registry.router(name, router, array);
    }
    public static void route(boolean begin, Object router, Screen screen, Object input, boolean handled) {
        var gesture = ownership.current();
        if (!thread() || gesture == null) return;
        try {
            if (!exact(router, ROUTER) || !exact(input, "mezz.jei.gui.input.UserInput")) throw new IOException();
            if (begin) {
                Object mode = NativeQuests.call(input, "getClickState");
                if (!(mode instanceof Enum<?> value)) throw new IOException();
                gesture.start(router, screen, input, value.name());
            } else gesture.end(router, screen, input, handled);
        } catch (IOException | RuntimeException | LinkageError unavailable) { gesture.invalidate(); }
    }
    public static void button(Object receiver, Screen screen, Object input, Optional<?> result) {
        var gesture = ownership.current();
        if (!thread() || gesture == null) return;
        if (!exact(receiver, HANDLER) || result == null) { gesture.invalidate(); return; }
        gesture.button(screen, input, receiver, result.orElse(null));
    }
    static void available(List<GameRecipeControls.Control> controls) throws IOException {
        requireIdle();
        registry.find(controls);
    }
    static void requireIdle() throws IOException {
        if (!thread()) throw new IOException("CLIENT_THREAD_REQUIRED");
        ownership.requireIdle();
    }
    static void preview(Screen screen, List<GameRecipeControls.Control> controls, int index, double x, double y) throws IOException {
        available(controls);
        var gesture = ownership.acquire(registry.find(controls), screen, index);
        gesture.prepare("SIMULATE");
        gesture.finish(screen.mouseClicked(x, y, 0));
    }
    static void requirePreview() throws IOException {
        var gesture = ownership.current();
        if (!thread() || gesture == null) throw new IOException("GAME_RECIPE_INPUT_UNCONFIRMED");
        gesture.requirePreview();
    }
    static void execute(Screen screen, double x, double y) throws IOException {
        requirePreview(); var gesture = ownership.current(); gesture.prepare("EXECUTE");
        gesture.finish(screen.mouseReleased(x, y, 0));
        if (!gesture.executed()) throw new IOException("GAME_RECIPE_INPUT_UNCONFIRMED");
    }
    /** Pinned public router reset unfocuses handlers and clears pending keys without executing a click. */
    static void release() throws IOException {
        if (!thread()) throw new IOException("CLIENT_THREAD_REQUIRED");
        // Retain ownership on failure; never claim cleanup merely by discarding our witness.
        ownership.release(router -> NativeQuests.call(router, "handleGuiChange"));
    }
}
