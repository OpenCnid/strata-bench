package io.github.opencnid.strata.client;

import static io.github.opencnid.strata.client.NativeQuests.*;
import com.google.gson.JsonObject;
import dev.ftb.mods.ftblibrary.ui.BaseScreen;
import dev.ftb.mods.ftblibrary.ui.BlankPanel;
import dev.ftb.mods.ftblibrary.ui.Button;
import dev.ftb.mods.ftblibrary.ui.Panel;
import dev.ftb.mods.ftblibrary.ui.ScreenWrapper;
import dev.ftb.mods.ftblibrary.ui.Widget;
import dev.ftb.mods.ftblibrary.ui.WidgetType;
import dev.ftb.mods.ftblibrary.ui.input.MouseButton;
import java.io.IOException;
import java.util.List;
import net.minecraft.client.Minecraft;

/** Exact visible RewardButton LEFT callback, initially only the bounded choice-menu opening route. */
final class NativeQuestRewardOpen implements GameQuestRewardOpen.Port {
    interface Components {JsonObject read(GameQuestComponents.Query query)throws IOException;}
    private final Minecraft client;private final GameQuestCatalog.Source source;
    private final GameQuestNavigation.Port navigation;private final Components components;
    private final NativeQuestChoiceMenu.Bindings bindings;private final GameActionLane.Operation context;private final Object file,team;
    NativeQuestRewardOpen(Minecraft client,GameQuestCatalog.Source source,GameQuestNavigation.Port navigation,
                        Components components,GameActionLane.Operation context,NativeQuestChoiceMenu.Bindings bindings)throws IOException {
        this.bindings=bindings;this.client=client;this.source=source;this.navigation=navigation;this.components=components;this.context=context;
        file=field(type("client.ClientQuestFile"),null,"INSTANCE");team=field(file.getClass(),file,"self");
    }
    private void validate()throws IOException {
        context.run();FtbQuestDisplays.requireNormalModifiers();
        if(client.options.advancedItemTooltips)throw new IOException("GAME_QUEST_ADVANCED_TOOLTIP_ACTIVE");
        if(!client.isSameThread() || source.generation()<0 || field(type("client.ClientQuestFile"),null,"INSTANCE")!=file
                || field(file.getClass(),file,"self")!=team || bool(call(file,"canEdit")))throw changed();
    }
    public GameQuestScreen.Snapshot book()throws IOException {validate();return navigation.read();}
    public GameQuestRewardOpen.Target selection(GameQuestRewardOpen.Request request)throws IOException {
        long started=System.nanoTime();validate();
        if(bool(field(file.getClass(),file,"disableGui")) || bool(call(team,"isLocked")))throw new IOException("GAME_QUEST_OPEN_FORBIDDEN");
        request.selection().visible(components.read(request.selection().query()),request.source());
        var state=book();
        if(!(state.frame().screen() instanceof ScreenWrapper wrapper) || wrapper!=client.screen)throw changed();
        var gui=wrapper.getGui();var view=panel(field(gui.getClass(),gui,"viewQuestPanel"),type("gui.quests.ViewQuestPanel"));
        var content=panel(field(view.getClass(),view,"panelContent"),BlankPanel.class);
        var tasks=panel(field(view.getClass(),view,"panelRewards"),BlankPanel.class);
        var quest=state.frame().questObject();var members=bounded(field(quest.getClass(),quest,"rewards"),512);
        var buttons=bounded(tasks.widgets,512);GameQuestRewardOpen.Target selected=null;
        for(Object entry:buttons) {
            checkTime(started);
            if(!(entry instanceof Button button) || entry.getClass()!=type("gui.quests.RewardButton"))throw unsupported();
            // Ancestor membership, clipping and enabled state precede reward identifiers.
            String layout=visibleLayout(gui,List.of(view,content,tasks),button);if(layout==null)continue;
            if(field(button.getClass(),button,"questScreen")!=gui)throw changed();
            Object task=field(button.getClass(),button,"reward");
            if(!members.contains(task) || field(type("quest.reward.Reward"),task,"quest")!=quest || call(task,"getQuestFile")!=file)throw changed();
            if(!request.selection().id().equals(string(call(task,"getCodeString"))))continue;
            if(task.getClass()!=type("quest.reward.ChoiceReward"))throw unsupported();
            // Count only, after visible eligible selection; do not inspect or expose table entries.
            var table=call(task,"getTable");if(table==null || table.getClass()!=type("quest.loot.RewardTable"))throw unsupported();
            var alternatives=bounded(field(table.getClass(),table,"rewards"),512);
            if(alternatives.isEmpty())throw unsupported();
            var claim=call(team,"getClaimType",new Class<?>[]{java.util.UUID.class,type("quest.reward.Reward")},client.player.getUUID(),task);
            if(!bool(call(claim,"canClaim")))throw new IOException("GAME_QUEST_OPEN_FORBIDDEN");
            if(selected!=null)throw new IOException("GAME_QUEST_AMBIGUOUS");
            selected=new GameQuestRewardOpen.Target(task,button,layout);
        }
        validate();checkTime(started);if(selected==null)throw new IOException("TARGET_NOT_OBSERVED");return selected;
    }
    public Object open(GameQuestRewardOpen.Target target)throws IOException {
        validate();((Button)target.button()).onClicked(MouseButton.LEFT);return client.screen;
    }
    public void confirm(GameQuestRewardOpen.Request request,GameQuestRewardOpen.Target target,Object book,Object menu)throws IOException {
        validate();if(client.screen!=menu || !(menu instanceof ScreenWrapper wrapper))throw changed();
        var gui=wrapper.getGui();
        if(gui.getClass()!=type("gui.SelectChoiceRewardScreen") || gui.getPrevScreen()!=book)throw changed();
        if(source.generation()!=request.source())throw changed();
        var query=request.selection().query();
        bindings.bind(new NativeQuestChoiceMenu.Binding(menu,book,target.reward(),query.chapter(),query.quest(),
            request.selection().id(),request.source(),source,file,team));
        try {NativeQuestChoiceMenu.source(client,source,bindings).validate();}
        catch(IOException failure){bindings.clear();throw failure;}
    }

    private static Panel panel(Object value,Class<?> exact)throws IOException {
        if(!(value instanceof Panel panel) || value.getClass()!=exact)throw unsupported();return panel;
    }
    /** Conservative fixed widget path. Reject offsets/overlap instead of targeting through another control. */
    private String visibleLayout(BaseScreen gui,List<Panel> path,Button button)throws IOException {
        if(!gui.shouldDraw() || !button.shouldDraw() || !button.isEnabled() || button.getWidgetType()==WidgetType.DISABLED)return null;
        var bounds=rect(gui.getX(),gui.getY(),gui.width,gui.height);
        var clip=rect(0,0,client.getWindow().getGuiScaledWidth(),client.getWindow().getGuiScaledHeight()).intersect(bounds);
        Panel parent=gui;var fingerprint=new StringBuilder().append(bounds).append(clip);
        var occluders=new java.util.ArrayList<GameQuestMenu.Rect>();
        for(Widget child:List.of(path.get(0),path.get(1),path.get(2),button)) {
            if(parent.isOffset() || parent.widgets.size()>512 || child.parent!=parent || !parent.widgets.contains(child))throw unsupported();
            if(!parent.shouldDraw() || !parent.isEnabled() || !child.shouldDraw() || !child.isEnabled())return null;
            var next=childBounds(bounds,parent,child);
            var shown=next.intersect(clip);if(!shown.nonempty())return null;
            // Library draws in list order and tests input in reverse order. Lower layers do not occlude.
            for(int index=parent.widgets.indexOf(child)+1;index<parent.widgets.size();index++) {
                var sibling=parent.widgets.get(index);
                if(sibling.shouldDraw() || sibling.isEnabled())occluders.add(childBounds(bounds,parent,sibling).intersect(clip));
            }
            fingerprint.append(parent.getScrollX()).append('/').append(parent.getScrollY()).append(next)
                .append(parent.getOnlyRenderWidgetsInside()).append(parent.getOnlyInteractWithWidgetsInside());
            if(child instanceof Panel panel) {
                // Widget.checkMouseOver requires every ancestor's own mouse-over, even without render clipping.
                clip=clip.intersect(next);
                parent=panel;bounds=next;
            } else for(var occluder:occluders)if(occluder.intersect(shown).nonempty())throw unsupported();
        }
        return KeyOptions.sha256(fingerprint.toString());
    }
    private static GameQuestMenu.Rect childBounds(GameQuestMenu.Rect parent,Panel panel,Widget child)throws IOException {
        return rect(parent.x()+GameQuestMenu.scrollOffset(panel.getScrollX())+child.posX,
            parent.y()+GameQuestMenu.scrollOffset(panel.getScrollY())+child.posY,child.width,child.height);
    }
    private static GameQuestMenu.Rect rect(int x,int y,int w,int h)throws IOException {
        try{return new GameQuestMenu.Rect(x,y,w,h);}catch(IllegalArgumentException invalid){throw unsupported();}
    }
    private static List<?> bounded(Object value,int max)throws IOException {
        if(!(value instanceof List<?> list) || list.size()>max)throw new IOException("GAME_QUEST_BOUNDS");return list;
    }
    private static void checkTime(long start)throws IOException {if(System.nanoTime()-start>100_000_000L)throw new IOException("GAME_QUEST_TIMEOUT");}
    private static IOException changed(){return new IOException("GAME_QUEST_CHANGED");}
    private static IOException unsupported(){return new IOException("GAME_QUEST_REWARD_OPEN_UNSUPPORTED");}
}
