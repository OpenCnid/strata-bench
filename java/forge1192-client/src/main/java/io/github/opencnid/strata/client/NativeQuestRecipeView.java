package io.github.opencnid.strata.client;

import java.io.IOException;
import net.minecraft.client.Minecraft;

/** Origin-bound copied page, ordinary navigation and close; no private recipe contents/history lookup. */
final class NativeQuestRecipeView implements GameQuestNavigation.Port {
    private final Minecraft client;private final GameQuestRecipeView.Bindings bindings;
    private final GameQuestRecipeView.Binding binding;private final NativeQuestNavigation book;
    private final GameQuestScreen tracker;private final GameActionLane.Operation context;
    private boolean closing;
    NativeQuestRecipeView(Minecraft client,GameQuestRecipeView.Bindings bindings,NativeQuestNavigation book,
                          GameQuestScreen tracker,GameActionLane.Operation context)throws IOException {
        this.client=client;this.bindings=bindings;this.book=book;this.tracker=tracker;this.context=context;
        binding=bindings.current(client.screen);
    }
    private void input()throws IOException {
        context.run();FtbQuestDisplays.requireNormalModifiers();binding.validate();
        if(!client.isSameThread() || client.mouseHandler.isMouseGrabbed() || client.mouseHandler.isLeftPressed()
                || client.mouseHandler.isMiddlePressed() || client.mouseHandler.isRightPressed())throw changed();
    }
    public GameQuestScreen.Snapshot read()throws IOException {
        input();
        if(closing && client.screen==binding.parent().screen())return book.read();
        return tracker.capture(()->{
            input();if(bindings.current(client.screen)!=binding)throw changed();
            var parent=book.retained(binding.parent().screen());
            if(!GameQuestRecipeView.sameOrigin(binding.parent(),parent))throw changed();
            var tasks=NativeQuests.field(parent.questObject().getClass(),parent.questObject(),"tasks");
            if(!(tasks instanceof java.util.List<?> list) || list.size()>512 || !list.contains(binding.task())
                    || NativeQuests.field(binding.task().getClass(),binding.task(),"quest")!=parent.questObject())throw changed();
            var screen=client.screen;
            if(screen!=binding.screen())throw changed();
            String layout=client.getWindow().getGuiScaledWidth()+"/"+client.getWindow().getGuiScaledHeight()+"/"+screen.width+"/"+screen.height;
            return GameQuestRecipeView.frame(binding,parent,KeyOptions.sha256(layout));
        });
    }
    public void selection(GameQuestNavigation.Request request)throws IOException {
        input();if(!request.operation().equals("close") || request.selection()!=null || closing)throw changed();
    }
    com.google.gson.JsonObject page() throws IOException {
        return new GameRecipePage().page(new GameRecipePage.Source() {
            public GameQuestScreen.Snapshot screen() throws IOException { return read(); }
            public java.util.List<GameRecipeSlots.Layout> layouts() throws IOException {
                input(); if (bindings.current(client.screen) != binding) throw changed();
                return JeiRenderedLayouts.current(binding);
            }
            public java.util.List<GameRecipeHeaders.Label> headers() throws IOException {
                input(); if (bindings.current(client.screen) != binding) throw changed();
                return JeiRenderedLayouts.currentHeaders(binding);
            }
            public java.util.List<GameRecipeControls.Control> controls() throws IOException {
                input(); if (bindings.current(client.screen) != binding) throw changed();
                return JeiRenderedLayouts.currentControls(binding);
            }
        });
    }
    private GameRecipeNavigation.State navigationState() throws IOException {
        var before = read(); var stamp = JeiRenderedLayouts.currentStamp(binding);
        var page = page(); var controls = JeiRenderedLayouts.currentControls(binding); var after = read();
        if (!before.frame().same(after.frame()) || before.generation() != after.generation() || before.revision() != after.revision()
                || stamp != JeiRenderedLayouts.currentStamp(binding)) throw changed();
        return new GameRecipeNavigation.State(after, SettingsJson.string(page, "revision"), stamp, controls);
    }
    private void checkControl(GameRecipeNavigation.State state, int index) throws IOException {
        input();
        if (index < 0 || index >= 4 || client.screen != state.screen().frame().screen()
                || bindings.current(client.screen) != binding) throw changed();
        var selected = state.controls().get(index); var object = selected.widget(); var area = selected.area();
        var viewport = new GameRecipeSlots.Rect(0, 0, client.screen.width, client.screen.height);
        if (!viewport.contains(area) || !"enabled".equals(selected.state())
                || !(object instanceof net.minecraft.client.gui.components.Button button)
                || !object.getClass().getName().equals("mezz.jei.gui.elements.GuiIconButton")) throw changed();
        var x = NativeQuests.call(object, "getX"); var y = NativeQuests.call(object, "getY");
        if (!(x instanceof Integer left) || !(y instanceof Integer top) || !button.active || !button.visible
                || !area.equals(new GameRecipeSlots.Rect(left, top, button.getWidth(), button.getHeight()))) throw changed();
    }
    GameRecipeNavigation.Port navigation() {
        return new GameRecipeNavigation.Port() {
            public GameRecipeNavigation.State read() throws IOException { return navigationState(); }
            public void ready(GameRecipeNavigation.State state) throws IOException { JeiRecipeInput.available(state.controls()); }
            public void checkControl(GameRecipeNavigation.State state, int index) throws IOException {
                NativeQuestRecipeView.this.checkControl(state, index);
            }
            public void preview(GameRecipeNavigation.State state, int index) throws IOException {
                checkControl(state, index); var area = state.controls().get(index).area();
                JeiRecipeInput.preview(client.screen, state.controls(), index, area.x() + area.width() / 2.0, area.y() + area.height() / 2.0);
            }
            public void requirePreview() throws IOException { input(); JeiRecipeInput.requirePreview(); }
            public void checkHistory(GameRecipeNavigation.State state) throws IOException {
                input(); JeiRecipeInput.requireIdle();
                if (client.screen != state.screen().frame().screen() || bindings.current(client.screen) != binding
                        || !client.screen.getClass().getName().equals("mezz.jei.gui.recipes.RecipesGui")) throw changed();
            }
            public void historyBack(GameRecipeNavigation.State state) throws IOException {
                checkHistory(state);
                // Public concrete-screen callback used by JEI's own Back handler; not part of IRecipesGui.
                // Never inspect history, call private logic, or use onClose as an exhausted-history fallback.
                try { NativeQuests.call(client.screen, "back"); }
                finally { JeiRenderedLayouts.invalidateFrame(); }
            }
            public void execute(GameRecipeNavigation.State state, int index) throws IOException {
                checkControl(state, index); var area = state.controls().get(index).area();
                try { JeiRecipeInput.execute(client.screen, area.x() + area.width() / 2.0, area.y() + area.height() / 2.0); }
                finally { JeiRenderedLayouts.invalidateFrame(); }
            }
            public GameRecipeNavigation.State after() throws IOException {
                NativeQuestRecipeView.this.read(); // Always check source, origin and idle inputs, even without a rendered frame.
                try { return navigationState(); }
                catch (IOException unavailable) {
                    if ("GAME_RECIPE_RENDER_UNAVAILABLE".equals(unavailable.getMessage())) return null;
                    throw unavailable;
                }
            }
        };
    }
    public void navigate(GameQuestNavigation.Request request)throws IOException {
        selection(request);if(bindings.current(client.screen)!=binding)throw changed();
        // JEI back() is recipe history. Its normal Screen.onClose returns to the captured parent.
        closing=true;client.screen.onClose();bindings.clear();
    }
    public void confirmRecipeClose(GameQuestScreen.Snapshot before)throws IOException {
        input();if(!closing || before.frame().screen()!=binding.screen() || client.screen!=binding.parent().screen())throw changed();
        GameQuestRecipeView.confirmReturn(binding,read().frame());
    }
    private static IOException changed(){return new IOException("GAME_QUEST_CHANGED");}
}
