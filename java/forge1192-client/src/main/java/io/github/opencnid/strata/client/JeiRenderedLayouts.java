package io.github.opencnid.strata.client;

import java.io.IOException;
import java.util.List;
import mezz.jei.api.gui.IRecipeLayoutDrawable;
import net.minecraft.client.Minecraft;
import net.minecraftforge.client.event.ScreenEvent;
import net.minecraftforge.common.MinecraftForge;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.eventbus.api.EventPriority;

/** Optional exact-JEI render hooks. Contains no graph lookup, input, or public observation route. */
public final class JeiRenderedLayouts {
    private static final GameRecipeRenderCapture capture = new GameRecipeRenderCapture();
    private static final JeiSlotCopies slots = new JeiSlotCopies();
    private static final GameRecipeHeaders headers = new GameRecipeHeaders();
    private static final GameRecipeControls controls = new GameRecipeControls();
    private static boolean copying;
    private static boolean installed;
    private static JeiRecipePlugin.View view;
    private static GameQuestRecipeView.Binding origin;
    private JeiRenderedLayouts() {}

    static synchronized void install() {
        if (installed) return;
        installed = true;
        MinecraftForge.EVENT_BUS.addListener(EventPriority.LOWEST, true, JeiRenderedLayouts::before);
        MinecraftForge.EVENT_BUS.addListener(EventPriority.LOWEST, JeiRenderedLayouts::after);
        MinecraftForge.EVENT_BUS.addListener(JeiRenderedLayouts::tick);
    }
    static void arm(JeiRecipePlugin.View nextView, GameQuestRecipeView.Binding nextOrigin) throws IOException {
        nextView.validate(); nextOrigin.validate();
        if (nextView.screen() != nextOrigin.screen() || nextView.runtime() != nextOrigin.runtime())
            throw new IOException("GAME_RECIPE_RENDER_UNAVAILABLE");
        if (view != null && view.equals(nextView) && origin != null && origin.same(nextOrigin)) return;
        clear(); view = nextView; origin = nextOrigin;
    }
    static void clear() { view = null; origin = null; capture.clear(); slots.clear(); headers.clear(); controls.clear(); copying = false; }
    private static GameRecipeRenderCapture.Key key() throws IOException {
        Minecraft client = Minecraft.getInstance();
        if (!client.isSameThread() || view == null || origin == null || client.screen != view.screen())
            throw new IOException("GAME_RECIPE_RENDER_UNAVAILABLE");
        view.validate(); origin.validate();
        if (client.screen.width != client.getWindow().getGuiScaledWidth()
                || client.screen.height != client.getWindow().getGuiScaledHeight())
            throw new IOException("GAME_RECIPE_RENDER_UNAVAILABLE");
        return new GameRecipeRenderCapture.Key(client.screen, view.runtime(), origin,
            client.screen.width, client.screen.height);
    }
    private static void before(ScreenEvent.Render.Pre event) {
        if (view == null) return;
        try {
            slots.clear(); headers.clear(); controls.clear(); copying = false;
            if (event.isCanceled() || event.getScreen() != view.screen()) { capture.clear(); return; }
            capture.beginFrame(key());
        } catch (IOException | RuntimeException | LinkageError unavailable) { clear(); }
    }
    private static void after(ScreenEvent.Render.Post event) {
        if (view == null) return;
        try {
            if (event.getScreen() != view.screen()) { capture.clear(); return; }
            if (copying || !headers.complete()) capture.invalidate();
            capture.finishFrame(key());
        } catch (IOException | RuntimeException | LinkageError unavailable) { clear(); }
    }
    private static void tick(TickEvent.ClientTickEvent event) {
        if (event.phase != TickEvent.Phase.END || view == null) return;
        try { key(); } catch (IOException | RuntimeException | LinkageError unavailable) { clear(); }
    }
    /** Called only by the pinned mixin at the beginning of the actual layout draw loop. */
    public static void beginLayouts(Object renderer) {
        headerOperation(() -> { capture.controls(controls.finish()); capture.headers(headers.beforeLayouts()); capture.beginLayouts(renderer); });
    }
    /** Existing native iterator result, without extra traversal or private-list access. */
    public static void layoutPredicate(Object renderer, Object iterator, boolean hasNext) {
        if (view != null && Minecraft.getInstance().isSameThread()) capture.layoutPredicate(renderer, iterator, hasNext);
    }
    public static void beginScreen(Object screen) {
        headerOperation(() -> {
            var key = key(); if (key.screen() != screen) throw new IOException("GAME_RECIPE_HEADER_INVALID");
            headers.begin(screen); controls.begin(new GameRecipeSlots.Rect(0, 0, key.width(), key.height()));
        });
    }
    public static void endScreen(Object screen) { headerOperation(() -> headers.end(screen)); }
    public static void beginCategory(Object category) { headerOperation(() -> headers.beginCategory(category)); }
    public static void endCategory(Object category) { headerOperation(() -> headers.endCategory(category)); }
    public static void header(boolean begin, String kind, com.mojang.blaze3d.vertex.PoseStack pose,
                              net.minecraft.client.gui.Font font, Object text, Object area) {
        if (!headers.observing()) return; // Other normal helper draws grant no header authority.
        headerOperation(() -> {
            var copy = JeiHeaderCopies.copy(kind, pose, font, text, area, key());
            if (begin) headers.beginLabel(text, copy); else headers.endLabel(text, copy);
        });
    }
    private static void headerOperation(GameActionLane.Operation operation) {
        if (view == null || !Minecraft.getInstance().isSameThread()) return;
        try { operation.run(); }
        catch (IOException | RuntimeException | LinkageError unavailable) { capture.invalidate(); headers.clear(); controls.clear(); }
    }
    public static void control(boolean begin, Object object, com.mojang.blaze3d.vertex.PoseStack pose) {
        if (!headers.controlsStage()) return;
        headerOperation(() -> {
            key();
            if (!(object instanceof net.minecraft.client.gui.components.Button button)
                    || !object.getClass().getName().equals("mezz.jei.gui.elements.GuiIconButton") || pose == null)
                throw new IOException("GAME_RECIPE_CONTROLS_INVALID");
            var identity = new com.mojang.math.Matrix4f(); identity.setIdentity();
            if (!pose.last().pose().equals(identity)) throw new IOException("GAME_RECIPE_CONTROLS_INVALID");
            var x = NativeQuests.call(object, "getX"); var y = NativeQuests.call(object, "getY");
            if (!(x instanceof Integer left) || !(y instanceof Integer top)) throw new IOException("GAME_RECIPE_CONTROLS_INVALID");
            var area = new GameRecipeSlots.Rect(left, top, button.getWidth(), button.getHeight());
            if (begin) controls.beginControl(object, area, () -> button.active && button.visible);
            else controls.endControl(object, area, () -> button.active && button.visible);
        });
    }
    public static void beginLayout(Object layout) {
        if (view == null || !Minecraft.getInstance().isSameThread()) return;
        try { if (copying) throw new IOException("GAME_RECIPE_SLOT_CAPTURE_INVALID"); slots.begin(layout, key()); copying = true; }
        catch (IOException | RuntimeException | LinkageError unavailable) { capture.invalidate(); slots.clear(); copying = false; }
    }
    public static void beginSlot(Object slot) { copy(() -> slots.beginSlot(slot)); }
    public static void selection(Object slot, java.util.Optional<?> selected) {
        copy(() -> { if (selected == null) throw new IOException("GAME_RECIPE_SLOT_CAPTURE_INVALID"); slots.selection(slot, selected.orElse(null)); });
    }
    public static void ingredient(Object slot, Object ingredient) { copy(() -> slots.ingredient(slot, ingredient, view.jei())); }
    public static void endSlot(Object slot) { copy(() -> slots.endSlot(slot)); }
    private static void copy(GameActionLane.Operation operation) {
        if (!copying || view == null || !Minecraft.getInstance().isSameThread()) return;
        try { operation.run(); }
        catch (IOException | RuntimeException | LinkageError unavailable) { capture.invalidate(); slots.clear(); copying = false; }
    }
    /** Called on normal return from each actual layout draw, after copying actual slot operands. */
    public static void drawn(Object layout) {
        if (view == null || !Minecraft.getInstance().isSameThread()) return;
        if (!(layout instanceof IRecipeLayoutDrawable<?>)
                || !layout.getClass().getName().equals("mezz.jei.library.gui.recipes.RecipeLayout")) {
            capture.invalidate(); return;
        }
        try {
            if (!copying) throw new IOException("GAME_RECIPE_SLOT_CAPTURE_INVALID");
            capture.drawn(layout, slots.finish(layout));
        } catch (IOException | RuntimeException | LinkageError unavailable) { capture.invalidate(); slots.clear(); }
        finally { copying = false; }
    }
    /** A thrown/aborted draw does not reach this hook and cannot publish a frame. */
    public static void endLayouts(Object renderer) {
        if (view != null && Minecraft.getInstance().isSameThread()) capture.endLayouts(renderer);
    }

    // Only immutable copied values are returned. Public page transport/visibility parity remains unqualified.
    static List<GameRecipeSlots.Layout> current(GameQuestRecipeView.Binding requested) throws IOException {
        var currentKey = key();
        if (requested == null || origin == null || !origin.same(requested))
            throw new IOException("GAME_RECIPE_RENDER_UNAVAILABLE");
        return capture.copied(currentKey);
    }
    static List<GameRecipeHeaders.Label> currentHeaders(GameQuestRecipeView.Binding requested) throws IOException {
        var currentKey = key();
        if (requested == null || origin == null || !origin.same(requested)) throw new IOException("GAME_RECIPE_RENDER_UNAVAILABLE");
        return capture.headers(currentKey);
    }
    static List<GameRecipeControls.Control> currentControls(GameQuestRecipeView.Binding requested) throws IOException {
        var currentKey = key();
        if (requested == null || origin == null || !origin.same(requested)) throw new IOException("GAME_RECIPE_RENDER_UNAVAILABLE");
        return capture.controls(currentKey);
    }
    static Object currentStamp(GameQuestRecipeView.Binding requested) throws IOException {
        var currentKey = key();
        if (requested == null || origin == null || !origin.same(requested)) throw new IOException("GAME_RECIPE_RENDER_UNAVAILABLE");
        return capture.stamp(currentKey);
    }
    static void invalidateFrame() { capture.invalidate(); }
}
