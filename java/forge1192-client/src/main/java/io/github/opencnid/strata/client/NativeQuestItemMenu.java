package io.github.opencnid.strata.client;

import static io.github.opencnid.strata.client.NativeQuests.*;
import dev.ftb.mods.ftblibrary.ui.BaseScreen;
import dev.ftb.mods.ftblibrary.ui.Panel;
import dev.ftb.mods.ftblibrary.ui.ScreenWrapper;
import dev.ftb.mods.ftblibrary.ui.Widget;
import dev.ftb.mods.ftblibrary.ui.WidgetType;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import net.minecraft.client.Minecraft;
import net.minecraft.world.item.ItemStack;
import net.minecraftforge.registries.ForgeRegistries;

/** Exact current FTB item screen; no raw task predicates, NBT, private reflection or UI mutations. */
final class NativeQuestItemMenu {
    private static final String SCREEN="dev.ftb.mods.ftbquests.gui.quests.ValidItemsScreen";
    static GameQuestMenu.Source source(Minecraft client,GameQuestCatalog.Source quests)throws IOException {
        if(quests.generation()<0)throw unavailable();
        if(client.screen==null || !client.screen.getClass().equals(ScreenWrapper.class))throw unavailable();
        final var wrapper=(ScreenWrapper)client.screen;final BaseScreen gui=wrapper.getGui();requireClass(gui,SCREEN);
        final Object task=field(gui.getClass(),gui,"task");requireClass(task,"dev.ftb.mods.ftbquests.quest.task.ItemTask");
        final Object quest=field(task.getClass(),task,"quest");requireClass(quest,"dev.ftb.mods.ftbquests.quest.Quest");
        final Object chapter=call(quest,"getChapter");requireClass(chapter,"dev.ftb.mods.ftbquests.quest.Chapter");
        final Object file=field(type("client.ClientQuestFile"),null,"INSTANCE"),team=field(file.getClass(),file,"self");
        final var teamType=type("quest.TeamData");
        final Object panelValue=field(gui.getClass(),gui,"itemPanel"),backValue=field(gui.getClass(),gui,"backButton"),submitValue=field(gui.getClass(),gui,"submitButton");
        if(!(panelValue instanceof Panel panel) || !(backValue instanceof Widget back) || !(submitValue instanceof Widget submit))throw unavailable();
        requireClass(panel,SCREEN+"$1");requireClass(back,SCREEN+"$2");requireClass(submit,SCREEN+"$3");
        if(panel.widgets.size()>GameQuestMenu.MAX_ITEMS)throw new IOException("GAME_QUEST_BOUNDS");
        final List<Widget> items=List.copyOf(panel.widgets);
        for(var item:items)requireClass(item,SCREEN+"$ValidItemButton");
        return new GameQuestMenu.Source() {
            public void validate()throws IOException {
                FtbQuestDisplays.requireNormalModifiers();
                if(client.options.advancedItemTooltips)throw new IOException("GAME_QUEST_ADVANCED_TOOLTIP_ACTIVE");
                if(!client.isSameThread() || quests.generation()<0 || client.screen!=wrapper || wrapper.getGui()!=gui
                        || gui.contextMenu!=null || gui.parent!=null || gui.getScreen()!=client.getWindow()
                        || field(type("client.ClientQuestFile"),null,"INSTANCE")!=file || field(file.getClass(),file,"self")!=team
                        || call(task,"getQuestFile")!=file || call(quest,"getQuestFile")!=file || call(chapter,"getQuestFile")!=file
                        || field(task.getClass(),task,"quest")!=quest || call(quest,"getChapter")!=chapter)throw unavailable();
                if(!bounded(call(file,"getVisibleChapters",new Class<?>[]{teamType},team),4096).contains(chapter)
                        || !bool(call(chapter,"isVisible",new Class<?>[]{teamType},team))
                        || !bounded(call(chapter,"getQuests"),4096).contains(quest)
                        || !bool(call(quest,"isVisible",new Class<?>[]{teamType},team))
                        || bool(call(quest,"hideDetailsUntilStartable")) && !bool(call(team,"canStartTasks",new Class<?>[]{type("quest.Quest")},quest))
                        || !bounded(field(quest.getClass(),quest,"tasks"),512).contains(task))throw new IOException("TARGET_NOT_OBSERVED");
                if(!gui.widgets.equals(List.of(panel,back,submit)) || !panel.widgets.equals(items)
                        || panel.parent!=gui || back.parent!=gui || submit.parent!=gui || items.stream().anyMatch(item->item.parent!=panel)
                        || panel.isOffset() || gui.isOffset() || gui.getScrollX()!=0 || gui.getScrollY()!=0
                        || !panel.getOnlyRenderWidgetsInside() || !panel.getOnlyInteractWithWidgetsInside())
                    throw new IOException("GAME_QUEST_LAYOUT_UNSUPPORTED");
                for(var control:List.of(back,submit))if(control.shouldDraw() && bounds(control,false).intersect(panelRect()).nonempty())
                    throw new IOException("GAME_QUEST_LAYOUT_UNSUPPORTED");
            }
            public long generation(){return quests.generation();}
            public Object screen(){return client.screen;}
            public GameQuestMenu.Context context()throws IOException {
                validate();return new GameQuestMenu.Context(string(call(chapter,"getCodeString")),string(call(quest,"getCodeString")),
                    string(call(task,"getCodeString")),string(field(gui.getClass(),gui,"title")));
            }
            private GameQuestMenu.Rect root()throws IOException {return rect(gui.getX(),gui.getY(),gui.width,gui.height);}
            private GameQuestMenu.Rect canvas()throws IOException {return rect(0,0,client.getWindow().getGuiScaledWidth(),client.getWindow().getGuiScaledHeight());}
            private GameQuestMenu.Rect panelRect()throws IOException {
                var root=root();return rect(root.x()+panel.posX,root.y()+panel.posY,panel.width,panel.height);
            }
            private GameQuestMenu.Rect bounds(Widget widget,boolean child)throws IOException {
                var parent=child ? panelRect():root();
                int dx=child ? GameQuestMenu.scrollOffset(panel.getScrollX()):0,dy=child ? GameQuestMenu.scrollOffset(panel.getScrollY()):0;
                return rect(parent.x()+dx+widget.posX,parent.y()+dy+widget.posY,widget.width,widget.height);
            }
            private boolean visible(Widget widget,boolean child)throws IOException {
                validate();if(!gui.shouldDraw() || !widget.shouldDraw() || child && !panel.shouldDraw())return false;
                var clip=canvas().intersect(root());if(child)clip=clip.intersect(panelRect());
                return bounds(widget,child).intersect(clip).nonempty();
            }
            public String layout()throws IOException {
                validate();var value=new StringBuilder().append(canvas()).append(root()).append(panelRect())
                    .append(panel.getScrollX()).append('/').append(panel.getScrollY()).append(gui.shouldDraw()).append(panel.shouldDraw())
                    .append('/').append(panel.getScrollStep()).append('/').append(panel.getContentWidth()).append('/').append(panel.getContentHeight())
                    .append('/').append(panel.isDefaultScrollVertical()).append('/').append(panel.attachedScrollbar!=null)
                    .append('/').append(gui.getContentWidth()).append('/').append(gui.getContentHeight()).append('/').append(gui.attachedScrollbar!=null)
                    .append('/').append(gui.isEnabled()).append('/').append(panel.isEnabled());
                for(var item:items)value.append(bounds(item,true)).append(item.shouldDraw());
                for(var control:List.of(back,submit))value.append(bounds(control,false)).append(control.shouldDraw()).append(control.isEnabled()).append(control.getWidgetType()!=WidgetType.DISABLED);
                return KeyOptions.sha256(value.toString());
            }
            public Iterable<? extends GameQuestMenu.Item> items() {
                var result=new ArrayList<GameQuestMenu.Item>();
                for(var widget:items)result.add(new GameQuestMenu.Item() {
                    public boolean visible()throws IOException{return visibleItem(widget);}
                    public GameQuestMenu.ItemDisplay display()throws IOException {
                        Object value=field(widget.getClass(),widget,"stack");
                        if(!(value instanceof ItemStack stack) || stack.isEmpty())throw unavailable();
                        var key=ForgeRegistries.ITEMS.getKey(stack.getItem());if(key==null)throw unavailable();
                        return new GameQuestMenu.ItemDisplay(key.toString(),stack.getCount(),plain(stack.getHoverName()),FtbQuestDisplays.itemTooltip(stack,client));
                    }
                });return result;
            }
            private boolean visibleItem(Widget widget)throws IOException{return visible(widget,true);}
            private boolean visibleControl(Widget widget)throws IOException{return visible(widget,false);}
            public Iterable<? extends GameQuestMenu.Control> controls() {
                var result=new ArrayList<GameQuestMenu.Control>();
                for(var widget:List.of(back,submit))result.add(new GameQuestMenu.Control() {
                    public boolean visible()throws IOException{return visibleControl(widget);}
                    public GameQuestMenu.ControlDisplay display()throws IOException {
                        return new GameQuestMenu.ControlDisplay(widget==back?"back":"submit",plain(widget.getTitle()),
                            widget.isEnabled() && widget.getWidgetType()!=WidgetType.DISABLED,FtbQuestDisplays.widgetTooltip(widget));
                    }
                });return result;
            }
        };
    }
    private static List<?> bounded(Object value,int max)throws IOException {
        if(!(value instanceof List<?> list) || list.size()>max)throw new IOException("GAME_QUEST_BOUNDS");return list;
    }
    private static GameQuestMenu.Rect rect(int x,int y,int width,int height)throws IOException {
        try{return new GameQuestMenu.Rect(x,y,width,height);}catch(IllegalArgumentException invalid){throw new IOException("GAME_QUEST_LAYOUT_UNSUPPORTED");}
    }
    private static void requireClass(Object value,String name)throws IOException {if(value==null || !value.getClass().getName().equals(name))throw unavailable();}
    private static IOException unavailable(){return new IOException("GAME_QUEST_MENU_UNSUPPORTED");}
}
