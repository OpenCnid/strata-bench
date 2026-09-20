package io.github.opencnid.strata.client;

import static io.github.opencnid.strata.client.NativeQuests.*;
import dev.ftb.mods.ftblibrary.ui.BaseScreen;
import dev.ftb.mods.ftblibrary.ui.Panel;
import dev.ftb.mods.ftblibrary.ui.PanelScrollBar;
import dev.ftb.mods.ftblibrary.ui.ScreenWrapper;
import dev.ftb.mods.ftblibrary.ui.ScrollBar;
import java.io.IOException;
import net.minecraft.client.Minecraft;

/** Exact choice Back callback and one attached-scrollbar wheel gesture, never a claim. */
final class NativeQuestChoiceAction implements GameQuestMenuAction.Port {
    private final Minecraft client;private final GameQuestCatalog.Source quests;private final GameQuestMenu menus;
    private final GameQuestNavigation.Port navigation;private final GameActionLane.Operation context;
    private final NativeQuestChoiceMenu.Bindings bindings;private final NativeQuestChoiceMenu.Binding binding;
    private final GameQuestMenu.Source source;private final ScreenWrapper wrapper,parent;
    private final BaseScreen gui;private final Panel panel;private final PanelScrollBar scrollbar;private final Object quest;
    NativeQuestChoiceAction(Minecraft client,GameQuestCatalog.Source quests,GameQuestMenu menus,
                            GameQuestNavigation.Port navigation,GameActionLane.Operation context,
                            NativeQuestChoiceMenu.Bindings bindings)throws IOException {
        this.client=client;this.quests=quests;this.menus=menus;this.navigation=navigation;this.context=context;this.bindings=bindings;
        source=NativeQuestChoiceMenu.source(client,quests,bindings);source.validate();binding=bindings.current(client.screen);
        wrapper=(ScreenWrapper)binding.menu();parent=(ScreenWrapper)binding.parent();gui=wrapper.getGui();
        panel=(Panel)gui.widgets.get(0);scrollbar=(PanelScrollBar)gui.widgets.get(1);
        quest=field(binding.reward().getClass(),binding.reward(),"quest");
    }
    private void input()throws IOException {
        context.run();FtbQuestDisplays.requireNormalModifiers();
        if(client.mouseHandler.isMouseGrabbed() || client.mouseHandler.isLeftPressed() || client.mouseHandler.isMiddlePressed()
                || client.mouseHandler.isRightPressed() || !client.isSameThread() || quests.generation()<0)throw changed();
    }
    public GameQuestMenuAction.State read()throws IOException {
        input();source.validate();if(bindings.current(client.screen)!=binding)throw changed();
        if(!gui.isEnabled() || gui.attachedScrollbar!=null || scrollbar.plane!=ScrollBar.Plane.VERTICAL
                || gui.getContentWidth()>gui.width || gui.getContentHeight()>gui.height)throw unsupported();
        var page=menus.page(new GameQuestMenu.Query(0),source);
        var scroll=new GameQuestMenuAction.Scroll(panel.getScrollX(),panel.getScrollY(),scrollbar.getScrollStep(),panel.width,panel.height,
            panel.getContentWidth(),panel.getContentHeight(),new GameQuestMenuAction.Wheel(scrollbar.getValue(),scrollbar.getMinValue(),scrollbar.getMaxValue()));
        scroll.validate();
        var shape=new StringBuilder().append(client.getWindow().getGuiScaledWidth()).append('/').append(client.getWindow().getGuiScaledHeight())
            .append('/').append(gui.getX()).append('/').append(gui.getY()).append('/').append(gui.width).append('/').append(gui.height)
            .append('/').append(scrollbar.plane).append('/').append(scrollbar.canMouseScrollPlane());
        for(var widget:gui.widgets)shape.append('/').append(widget.posX).append('/').append(widget.posY).append('/').append(widget.width)
            .append('/').append(widget.height).append('/').append(widget.shouldDraw()).append('/').append(widget.isEnabled());
        for(var widget:panel.widgets)shape.append('/').append(widget.posX).append('/').append(widget.posY).append('/').append(widget.width)
            .append('/').append(widget.height).append('/').append(widget.shouldDraw()).append('/').append(widget.isEnabled());
        boolean wheel=panel.shouldDraw() && panel.isEnabled() && scrollbar.isEnabled() && scrollbar.canMouseScrollPlane() && viewport().nonempty();
        source.validate();
        // Back is the ordinary ScreenWrapper Backspace/onBack route, not an invented visible button.
        return new GameQuestMenuAction.State(SettingsJson.integer(page,"source_generation"),SettingsJson.integer(page,"menu_generation"),
            SettingsJson.integer(page,"revision"),wrapper,parent,binding.reward(),KeyOptions.sha256(shape.toString()),scroll,true,wheel);
    }
    private GameQuestMenu.Rect viewport()throws IOException {
        try {
            return new GameQuestMenu.Rect(gui.getX()+panel.posX,gui.getY()+panel.posY,panel.width,panel.height)
                .intersect(new GameQuestMenu.Rect(gui.getX(),gui.getY(),gui.width,gui.height))
                .intersect(new GameQuestMenu.Rect(0,0,client.getWindow().getGuiScaledWidth(),client.getWindow().getGuiScaledHeight()));
        }catch(IllegalArgumentException invalid){throw unsupported();}
    }
    public void back(GameQuestMenuAction.State before)throws IOException {
        input();source.validate();gui.onBack();bindings.clear();
    }
    public void wheel(GameQuestMenuAction.State before,String direction)throws IOException {
        input();source.validate();var visible=viewport();if(!visible.nonempty())throw unsupported();
        int oldX=gui.getMouseX(),oldY=gui.getMouseY();
        try {
            gui.updateMouseOver(visible.x()+visible.width()/2,visible.y()+visible.height()/2);
            if(!panel.isMouseOver() || !scrollbar.canMouseScroll() || !scrollbar.canMouseScrollPlane())throw changed();
            if(!gui.mouseScrolled(direction.equals("up")?1.0:-1.0))throw changed();
        } finally {gui.updateMouseOver(oldX,oldY);}
    }
    public void confirmBack(GameQuestMenuAction.State before)throws IOException {
        input();if(client.screen!=parent || quests.generation()!=before.source())throw changed();
        var state=navigation.read();
        if(state.frame().screen()!=parent || state.frame().questObject()!=quest)throw changed();
    }
    private static IOException changed(){return new IOException("GAME_QUEST_CHANGED");}
    private static IOException unsupported(){return new IOException("GAME_QUEST_CHOICE_ACTION_UNSUPPORTED");}
}
