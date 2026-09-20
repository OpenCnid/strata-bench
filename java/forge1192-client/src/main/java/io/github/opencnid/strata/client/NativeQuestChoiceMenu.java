package io.github.opencnid.strata.client;

import static io.github.opencnid.strata.client.NativeQuests.*;
import dev.ftb.mods.ftblibrary.ui.BaseScreen;
import dev.ftb.mods.ftblibrary.ui.Panel;
import dev.ftb.mods.ftblibrary.ui.PanelScrollBar;
import dev.ftb.mods.ftblibrary.ui.ScreenWrapper;
import dev.ftb.mods.ftblibrary.ui.Widget;
import dev.ftb.mods.ftblibrary.ui.WidgetType;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import net.minecraft.client.Minecraft;

/** Opening-bound current choice widgets. Never reads the screen's private reward/table fields. */
final class NativeQuestChoiceMenu {
    record Binding(Object menu,Object parent,Object reward,String chapter,String quest,String id,long generation,
                   GameQuestCatalog.Source source,Object file,Object team) { }
    static final class Bindings {
        private Binding value;
        void bind(Binding next)throws IOException {
            if(next==null || next.menu()==null || next.parent()==null || next.menu()==next.parent() || next.reward()==null
                    || next.file()==null || next.team()==null || next.source()==null || next.generation()<0
                    || next.generation()>9007199254740991L || next.source().generation()!=next.generation())throw changed();
            for(String id:new String[]{next.chapter(),next.quest(),next.id()})if(id==null || !id.matches("[0-9A-F]{16}"))throw changed();
            if(value!=null && (value.menu()!=next.menu() || value.parent()!=next.parent() || value.reward()!=next.reward()
                    || value.generation()!=next.generation() || value.file()!=next.file() || value.team()!=next.team()
                    || !value.chapter().equals(next.chapter()) || !value.quest().equals(next.quest()) || !value.id().equals(next.id())))throw changed();
            value=next;
        }
        void tick(Object screen){if(value!=null && (value.menu()!=screen || value.source().generation()!=value.generation()))clear();}
        Binding current(Object screen)throws IOException {
            tick(screen);if(value==null)throw changed();return value;
        }
        void clear(){value=null;}
    }
    static GameQuestMenu.Source source(Minecraft client,GameQuestCatalog.Source quests,Bindings bindings)throws IOException {
        final Binding bound=bindings.value;
        if(bound==null || client.screen!=bound.menu() || client.screen.getClass()!=ScreenWrapper.class)throw unsupported();
        final var wrapper=(ScreenWrapper)client.screen;final BaseScreen gui=wrapper.getGui();
        if(gui.getClass()!=type("gui.SelectChoiceRewardScreen") || !(bound.parent() instanceof ScreenWrapper parent)
                || parent.getClass()!=ScreenWrapper.class || parent.getGui().getClass()!=type("gui.quests.QuestScreen"))throw unsupported();
        // Discover the two public children by their exact known layout. No private panel lookup.
        if(gui.widgets.size()!=2 || !(gui.widgets.get(0) instanceof Panel panel)
                || !panel.getClass().getName().equals("dev.ftb.mods.ftblibrary.ui.misc.ButtonListBaseScreen$1")
                || !(gui.widgets.get(1) instanceof PanelScrollBar scrollbar) || scrollbar.getClass()!=PanelScrollBar.class
                || panel.widgets.size()>GameQuestMenu.MAX_ITEMS)throw unsupported();
        final var items=List.copyOf(panel.widgets);
        for(var item:items)if(!item.getClass().getName().equals("dev.ftb.mods.ftbquests.gui.SelectChoiceRewardScreen$ChoiceRewardButton"))throw unsupported();
        final Object quest=field(bound.reward().getClass(),bound.reward(),"quest");
        return new GameQuestMenu.Source() {
            public void validate()throws IOException {
                FtbQuestDisplays.requireNormalModifiers();
                if(client.options.advancedItemTooltips)throw new IOException("GAME_QUEST_ADVANCED_TOOLTIP_ACTIVE");
                if(!client.isSameThread() || !gui.shouldDraw() || bindings.value==null || bindings.value.menu()!=bound.menu()
                        || quests.generation()!=bound.generation() || bound.source().generation()!=bound.generation()
                        || client.screen!=wrapper || wrapper.getGui()!=gui || gui.getPrevScreen()!=parent
                        || gui.contextMenu!=null || gui.parent!=null || gui.getScreen()!=client.getWindow()
                        || field(type("client.ClientQuestFile"),null,"INSTANCE")!=bound.file()
                        || field(bound.file().getClass(),bound.file(),"self")!=bound.team()
                        || bool(field(bound.file().getClass(),bound.file(),"disableGui")) || bool(call(bound.team(),"isLocked"))
                        || field(parent.getGui().getClass(),parent.getGui(),"file")!=bound.file()
                        || call(parent.getGui(),"getViewedQuest")!=quest || call(bound.reward(),"getQuestFile")!=bound.file())throw changed();
                var teamType=type("quest.TeamData");var rewardType=type("quest.reward.Reward");var chapter=call(quest,"getChapter");
                if(!contains(call(bound.file(),"getVisibleChapters",new Class<?>[]{teamType},bound.team()),chapter,4096)
                        || !contains(call(chapter,"getQuests"),quest,4096)
                        || call(chapter,"getQuestFile")!=bound.file() || call(quest,"getQuestFile")!=bound.file()
                        || !bool(call(chapter,"isVisible",new Class<?>[]{teamType},bound.team()))
                        || !bool(call(quest,"isVisible",new Class<?>[]{teamType},bound.team()))
                        || bool(call(quest,"hideDetailsUntilStartable")) && !bool(call(bound.team(),"canStartTasks",new Class<?>[]{type("quest.Quest")},quest))
                        || !(field(quest.getClass(),quest,"rewards") instanceof List<?> rewards) || rewards.size()>512 || !rewards.contains(bound.reward())
                        || bool(call(bound.team(),"isRewardBlocked",new Class<?>[]{rewardType},bound.reward())))throw changed();
                var auto=call(bound.reward(),"getAutoClaimType");
                if(!(auto instanceof Enum<?> mode) || !auto.getClass().getName().equals("dev.ftb.mods.ftbquests.quest.reward.RewardAutoClaim")
                        || mode.name().equals("INVISIBLE"))throw changed();
                var claim=call(bound.team(),"getClaimType",new Class<?>[]{java.util.UUID.class,rewardType},client.player.getUUID(),bound.reward());
                if(!bool(call(claim,"canClaim")))throw changed();
                if(!bound.chapter().equals(string(call(chapter,"getCodeString"))) || !bound.quest().equals(string(call(quest,"getCodeString")))
                        || !bound.id().equals(string(call(bound.reward(),"getCodeString"))))throw changed();
                if(!gui.widgets.equals(List.of(panel,scrollbar)) || !panel.widgets.equals(items)
                        || panel.parent!=gui || scrollbar.parent!=gui || items.stream().anyMatch(item->item.parent!=panel)
                        || panel.attachedScrollbar!=scrollbar || panel.isOffset() || gui.isOffset()
                        || gui.getScrollX()!=0 || gui.getScrollY()!=0 || !panel.getOnlyRenderWidgetsInside()
                        || !panel.getOnlyInteractWithWidgetsInside())throw unsupported();
            }
            public long generation(){return quests.generation();}
            public Object screen(){return client.screen;}
            public GameQuestMenu.Context context()throws IOException {
                validate();return new GameQuestMenu.Context(bound.chapter(),bound.quest(),null,bound.id(),plain(gui.getTitle()));
            }
            private GameQuestMenu.Rect root()throws IOException{return rect(gui.getX(),gui.getY(),gui.width,gui.height);}
            private GameQuestMenu.Rect canvas()throws IOException{return rect(0,0,client.getWindow().getGuiScaledWidth(),client.getWindow().getGuiScaledHeight());}
            private GameQuestMenu.Rect panelRect()throws IOException{return rect(gui.getX()+panel.posX,gui.getY()+panel.posY,panel.width,panel.height);}
            private GameQuestMenu.Rect bounds(Widget widget)throws IOException {
                var p=panelRect();return rect(p.x()+GameQuestMenu.scrollOffset(panel.getScrollX())+widget.posX,
                    p.y()+GameQuestMenu.scrollOffset(panel.getScrollY())+widget.posY,widget.width,widget.height);
            }
            private boolean shown(Widget widget)throws IOException {
                validate();if(!gui.shouldDraw() || !panel.shouldDraw() || !widget.shouldDraw())return false;
                var shown=bounds(widget).intersect(canvas()).intersect(root()).intersect(panelRect());
                var bar=rect(gui.getX()+scrollbar.posX,gui.getY()+scrollbar.posY,scrollbar.width,scrollbar.height);
                if(scrollbar.shouldDraw() && bar.intersect(shown).nonempty())throw unsupported();
                return shown.nonempty();
            }
            public String layout()throws IOException {
                validate();var text=new StringBuilder().append(canvas()).append(root()).append(panelRect())
                    .append('/').append(panel.getScrollX()).append('/').append(panel.getScrollY())
                    .append('/').append(gui.shouldDraw()).append('/').append(panel.shouldDraw())
                    .append('/').append(gui.isEnabled()).append('/').append(panel.isEnabled())
                    .append('/').append(scrollbar.posX).append('/').append(scrollbar.posY).append('/').append(scrollbar.width)
                    .append('/').append(scrollbar.height).append('/').append(scrollbar.shouldDraw());
                text.append('/').append(scrollbar.isEnabled()).append('/').append(scrollbar.plane)
                    .append('/').append(scrollbar.getValue()).append('/').append(scrollbar.getMinValue()).append('/').append(scrollbar.getMaxValue())
                    .append('/').append(scrollbar.getScrollStep()).append('/').append(panel.getContentWidth()).append('/').append(panel.getContentHeight());
                for(var item:items)text.append(bounds(item)).append('/').append(item.shouldDraw()).append('/').append(item.isEnabled())
                    .append('/').append(item.getWidgetType()==WidgetType.DISABLED);
                return KeyOptions.sha256(text.toString());
            }
            public Iterable<? extends GameQuestMenu.Item> items() {
                var rows=new ArrayList<GameQuestMenu.Item>();
                for(var item:items)rows.add(new GameQuestMenu.Item() {
                    public boolean visible()throws IOException{return shown(item);}
                    public GameQuestMenu.ChoiceDisplay display()throws IOException {
                        if(!shown(item))throw changed();
                        return new GameQuestMenu.ChoiceDisplay(plain(item.getTitle()),gui.isEnabled() && panel.isEnabled()
                            && item.isEnabled() && item.getWidgetType()!=WidgetType.DISABLED,FtbQuestDisplays.widgetTooltip(item));
                    }
                });return rows;
            }
            public Iterable<? extends GameQuestMenu.Control> controls(){return List.of();}
        };
    }
    private static GameQuestMenu.Rect rect(int x,int y,int w,int h)throws IOException {
        try{return new GameQuestMenu.Rect(x,y,w,h);}catch(IllegalArgumentException invalid){throw unsupported();}
    }
    private static boolean contains(Object value,Object member,int maximum)throws IOException {
        if(!(value instanceof List<?> list) || list.size()>maximum)throw new IOException("GAME_QUEST_BOUNDS");return list.contains(member);
    }
    private static IOException changed(){return new IOException("GAME_QUEST_CHANGED");}
    private static IOException unsupported(){return new IOException("GAME_QUEST_CHOICE_MENU_UNSUPPORTED");}
}
