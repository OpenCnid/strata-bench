package io.github.opencnid.strata.client;

import static io.github.opencnid.strata.client.NativeQuests.*;
import com.google.gson.JsonObject;
import dev.ftb.mods.ftblibrary.ui.BaseScreen;
import dev.ftb.mods.ftblibrary.ui.ScreenWrapper;
import java.io.IOException;
import java.util.List;
import net.minecraft.client.Minecraft;

/** Exact native book link/back/hotkey-close callbacks; no private fields or progress packets. */
final class NativeQuestNavigation implements GameQuestNavigation.Port {
    interface Catalog {JsonObject read(GameQuestCatalog.Query query)throws IOException;}
    private final Minecraft client;private final GameQuestCatalog.Source source;private final GameQuestScreen tracker;
    private final Catalog catalog;private final GameActionLane.Operation context;
    private final Object file,team;private final Class<?> teamType,chapterType,questType,screenType;
    private Object selected;private BaseScreen selectedGui;
    NativeQuestNavigation(Minecraft client,GameQuestCatalog.Source source,GameQuestScreen tracker,Catalog catalog,
                          GameActionLane.Operation context)throws IOException {
        this.client=client;this.source=source;this.tracker=tracker;this.catalog=catalog;this.context=context;
        file=field(type("client.ClientQuestFile"),null,"INSTANCE");team=field(file.getClass(),file,"self");
        teamType=type("quest.TeamData");chapterType=type("quest.Chapter");questType=type("quest.Quest");screenType=type("gui.quests.QuestScreen");
    }
    private void validate()throws IOException {
        context.run();FtbQuestDisplays.requireNormalModifiers();
        if(!client.isSameThread() || source.generation()<0 || field(type("client.ClientQuestFile"),null,"INSTANCE")!=file
                || field(file.getClass(),file,"self")!=team || bool(call(file,"canEdit")))throw changed();
    }
    private BaseScreen gui()throws IOException {return gui(client.screen);}
    private BaseScreen gui(net.minecraft.client.gui.screens.Screen screen)throws IOException {
        if(screen==null || screen.getClass()!=ScreenWrapper.class)throw unsupported();
        var gui=((ScreenWrapper)screen).getGui();
        if(gui==null || gui.getClass()!=screenType || field(screenType,gui,"file")!=file || gui.parent!=null || gui.contextMenu!=null
                || gui.getScreen()!=client.getWindow() || gui.getPrevScreen()!=null || !gui.shouldDraw()
                || field(screenType,gui,"grabbed")!=null || bool(field(screenType,gui,"movingObjects"))
                || !bounded(field(screenType,gui,"selectedObjects")).isEmpty())throw unsupported();
        var panel=field(screenType,gui,"viewQuestPanel");
        if(panel==null || !panel.getClass().getName().equals("dev.ftb.mods.ftbquests.gui.quests.ViewQuestPanel")
                || bool(field(panel.getClass(),panel,"hidePanel")))throw unsupported();
        return gui;
    }
    private boolean visibleChapter(Object chapter)throws IOException {
        return visibleChapterMember(chapter)
            && bounded(call(file,"getVisibleChapters",new Class<?>[]{teamType},team)).contains(chapter)
            ;
    }
    private boolean visibleChapterMember(Object chapter)throws IOException {
        return chapter!=null && chapter.getClass()==chapterType && call(chapter,"getQuestFile")==file
            && bool(call(chapter,"isVisible",new Class<?>[]{teamType},team));
    }
    private boolean visibleQuest(Object chapter,Object quest)throws IOException {
        return visibleChapter(chapter) && bounded(call(chapter,"getQuests")).contains(quest) && visibleQuestMember(chapter,quest);
    }
    private boolean visibleQuestMember(Object chapter,Object quest)throws IOException {
        return quest!=null && quest.getClass()==questType && call(quest,"getQuestFile")==file && call(quest,"getChapter")==chapter
            && bool(call(quest,"isVisible",new Class<?>[]{teamType},team))
            && (!bool(call(quest,"hideDetailsUntilStartable")) || bool(call(team,"canStartTasks",new Class<?>[]{questType},quest)));
    }
    private GameQuestScreen.Frame frame()throws IOException {return frame(client.screen);}
    GameQuestScreen.Frame retained(Object parent)throws IOException {
        if(!(parent instanceof ScreenWrapper wrapper))throw unsupported();return frame(wrapper);
    }
    private GameQuestScreen.Frame frame(net.minecraft.client.gui.screens.Screen screen)throws IOException {
        validate();long generation=source.generation();
        if(screen==null)return new GameQuestScreen.Frame(generation,null,null,null,null,null,KeyOptions.sha256("closed"));
        var gui=gui(screen);Object chapter=field(screenType,gui,"selectedChapter"),quest=call(gui,"getViewedQuest");
        if(chapter!=null && !visibleChapter(chapter) || quest!=null && !visibleQuest(chapter,quest))throw new IOException("TARGET_NOT_OBSERVED");
        String chapterId=chapter==null?null:string(call(chapter,"getCodeString"));
        String questId=quest==null?null:string(call(quest,"getCodeString"));
        // Logical link/back operations use no pointer geometry. Resize remains a conservative fence.
        String layout=client.getWindow().getGuiScaledWidth()+"/"+client.getWindow().getGuiScaledHeight()+"/"+gui.getX()+"/"+gui.getY()+"/"+gui.width+"/"+gui.height;
        validate();return new GameQuestScreen.Frame(generation,screen,chapter,quest,chapterId,questId,KeyOptions.sha256(layout));
    }
    public GameQuestScreen.Snapshot read()throws IOException {return tracker.capture(this::frame);}
    public void selection(GameQuestNavigation.Request request)throws IOException {
        long started=System.nanoTime();validate();var gui=gui();Object target=null;
        if(request.selection()!=null) {
            if(bool(field(file.getClass(),file,"disableGui")) || bool(call(team,"isLocked")))throw new IOException("GAME_QUEST_OPEN_FORBIDDEN");
            var selection=request.selection();selection.visible(catalog.read(selection.query()),request.source(),request.operation());
            Object chapter=null;
            for(var candidate:bounded(call(file,"getVisibleChapters",new Class<?>[]{teamType},team))) {
                checkTime(started);if(!visibleChapterMember(candidate))continue;
                String id=string(call(candidate,"getCodeString"));
                if(id.equals(selection.query().chapter()==null?selection.id():selection.query().chapter())) {
                    if(chapter!=null)throw new IOException("GAME_QUEST_AMBIGUOUS");chapter=candidate;
                }
            }
            if(chapter==null)throw new IOException("TARGET_NOT_OBSERVED");
            if(request.operation().equals("chapter"))target=chapter;
            else for(var quest:bounded(call(chapter,"getQuests"))) {
                checkTime(started);if(!visibleQuestMember(chapter,quest))continue;
                if(selection.id().equals(call(quest,"getCodeString"))) {
                    if(target!=null)throw new IOException("GAME_QUEST_AMBIGUOUS");target=quest;
                }
            }
            if(target==null)throw new IOException("TARGET_NOT_OBSERVED");
        }
        validate();checkTime(started);if(selectedGui!=null && (selectedGui!=gui || selected!=target))throw changed();
        selectedGui=gui;selected=target;
    }
    public void navigate(GameQuestNavigation.Request request)throws IOException {
        validate();var gui=gui();if(gui!=selectedGui)throw changed();
        switch(request.operation()) {
            case "chapter","quest" -> call(gui,"open",new Class<?>[]{type("quest.QuestObject"),boolean.class},selected,false);
            case "back" -> gui.onBack();
            case "close" -> gui.closeGui(true);
            default -> throw unsupported();
        }
    }
    private static List<?> bounded(Object value)throws IOException {
        if(!(value instanceof List<?> list) || list.size()>4096)throw new IOException("GAME_QUEST_BOUNDS");return list;
    }
    private static IOException changed(){return new IOException("GAME_QUEST_CHANGED");}
    private static void checkTime(long start)throws IOException {if(System.nanoTime()-start>100_000_000L)throw new IOException("GAME_QUEST_TIMEOUT");}
    private static IOException unsupported(){return new IOException("GAME_QUEST_SCREEN_UNSUPPORTED");}
}
