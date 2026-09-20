package io.github.opencnid.strata.client;

import static io.github.opencnid.strata.client.NativeQuests.*;
import dev.ftb.mods.ftblibrary.ui.BaseScreen;
import dev.ftb.mods.ftblibrary.ui.Button;
import dev.ftb.mods.ftblibrary.ui.Panel;
import dev.ftb.mods.ftblibrary.ui.ScreenWrapper;
import dev.ftb.mods.ftblibrary.ui.input.MouseButton;
import java.io.IOException;
import net.minecraft.client.Minecraft;

/** Item callbacks with scoped wheel hover; ordinary Back may restore the native pointer position. */
final class NativeQuestMenuAction implements GameQuestMenuAction.Port {
    private final Minecraft client;private final GameQuestCatalog.Source quests;private final GameQuestMenu menus;
    private final GameQuestNavigation.Port navigation;private final GameActionLane.Operation context;
    private final GameQuestMenu.Source source;private final ScreenWrapper wrapper,parent;
    private final BaseScreen gui;private final Panel panel;private final Button back;private final Object task,quest;
    NativeQuestMenuAction(Minecraft client,GameQuestCatalog.Source quests,GameQuestMenu menus,
                         GameQuestNavigation.Port navigation,GameActionLane.Operation context)throws IOException {
        this.client=client;this.quests=quests;this.menus=menus;this.navigation=navigation;this.context=context;
        source=NativeQuestItemMenu.source(client,quests);source.validate();wrapper=(ScreenWrapper)client.screen;gui=wrapper.getGui();
        panel=(Panel)field(gui.getClass(),gui,"itemPanel");back=(Button)field(gui.getClass(),gui,"backButton");
        task=field(gui.getClass(),gui,"task");quest=field(task.getClass(),task,"quest");
        if(!(gui.getPrevScreen() instanceof ScreenWrapper previous) || previous.getClass()!=ScreenWrapper.class
                || previous.getGui().getClass()!=type("gui.quests.QuestScreen"))throw unsupported();
        parent=previous;
    }
    private void input()throws IOException {
        context.run();FtbQuestDisplays.requireNormalModifiers();
        if(client.mouseHandler.isMouseGrabbed() || !client.isSameThread() || quests.generation()<0)throw changed();
    }
    public GameQuestMenuAction.State read()throws IOException {
        input();source.validate();
        if(client.screen!=wrapper || gui.getPrevScreen()!=parent || field(gui.getClass(),gui,"task")!=task
                || field(parent.getGui().getClass(),parent.getGui(),"file")!=call(task,"getQuestFile")
                || call(parent.getGui(),"getViewedQuest")!=quest)throw changed();
        if(!gui.shouldDraw() || !gui.isEnabled() || gui.getScrollX()!=0 || gui.getScrollY()!=0
                || gui.attachedScrollbar!=null || panel.attachedScrollbar!=null || !panel.isDefaultScrollVertical()
                || gui.getContentWidth()>gui.width || gui.getContentHeight()>gui.height)throw unsupported();
        var page=menus.page(new GameQuestMenu.Query(0),source);boolean canBack=false;
        for(var row:page.getAsJsonArray("controls")) {
            var control=row.getAsJsonObject();
            if("back".equals(SettingsJson.string(control,"control")))canBack=control.get("enabled").getAsBoolean();
        }
        var scroll=new GameQuestMenuAction.Scroll(panel.getScrollX(),panel.getScrollY(),panel.getScrollStep(),panel.width,panel.height,
            panel.getContentWidth(),panel.getContentHeight());scroll.validate();
        var shape=new StringBuilder().append(client.getWindow().getGuiScaledWidth()).append('/').append(client.getWindow().getGuiScaledHeight())
            .append('/').append(gui.getX()).append('/').append(gui.getY()).append('/').append(gui.width).append('/').append(gui.height);
        for(var widget:gui.widgets)shape.append('/').append(widget.posX).append('/').append(widget.posY).append('/').append(widget.width)
            .append('/').append(widget.height).append('/').append(widget.shouldDraw()).append('/').append(widget.isEnabled());
        for(var widget:panel.widgets)shape.append('/').append(widget.posX).append('/').append(widget.posY).append('/').append(widget.width)
            .append('/').append(widget.height).append('/').append(widget.shouldDraw()).append('/').append(widget.isEnabled());
        boolean wheel=panel.shouldDraw() && panel.isEnabled() && viewport().nonempty();
        source.validate();
        return new GameQuestMenuAction.State(SettingsJson.integer(page,"source_generation"),SettingsJson.integer(page,"menu_generation"),
            SettingsJson.integer(page,"revision"),wrapper,parent,task,KeyOptions.sha256(shape.toString()),scroll,canBack,wheel);
    }
    private GameQuestMenu.Rect viewport()throws IOException {
        try {
            return new GameQuestMenu.Rect(gui.getX()+panel.posX,gui.getY()+panel.posY,panel.width,panel.height)
                .intersect(new GameQuestMenu.Rect(gui.getX(),gui.getY(),gui.width,gui.height))
                .intersect(new GameQuestMenu.Rect(0,0,client.getWindow().getGuiScaledWidth(),client.getWindow().getGuiScaledHeight()));
        }catch(IllegalArgumentException invalid){throw unsupported();}
    }
    public void back(GameQuestMenuAction.State before)throws IOException {
        input();source.validate();back.onClicked(MouseButton.LEFT);
    }
    public void wheel(GameQuestMenuAction.State before,String direction)throws IOException {
        input();source.validate();var visible=viewport();if(!visible.nonempty())throw unsupported();
        int oldX=gui.getMouseX(),oldY=gui.getMouseY();
        // One composite ordinary wheel gesture: target visible panel, wheel once, restore logical hover.
        // Exact item children inherit the no-op wheel handler; the root cannot scroll in this context.
        try {
            gui.updateMouseOver(visible.x()+visible.width()/2,visible.y()+visible.height()/2);
            if(!panel.isMouseOver())throw changed();
            gui.mouseScrolled(direction.equals("up")?1.0:-1.0);
        } finally {gui.updateMouseOver(oldX,oldY);}
    }
    public void confirmBack(GameQuestMenuAction.State before)throws IOException {
        input();if(client.screen!=parent || quests.generation()!=before.source())throw changed();
        var state=navigation.read();
        if(state.frame().screen()!=parent || state.frame().questObject()!=quest)throw changed();
    }
    private static IOException changed(){return new IOException("GAME_QUEST_CHANGED");}
    private static IOException unsupported(){return new IOException("GAME_QUEST_MENU_ACTION_UNSUPPORTED");}
}
