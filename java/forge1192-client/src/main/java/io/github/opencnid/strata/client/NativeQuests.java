package io.github.opencnid.strata.client;

import com.google.gson.JsonObject;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import net.minecraft.client.Minecraft;
import net.minecraft.network.chat.Component;
import net.minecraft.world.entity.player.Player;

/** Fixed public FTB client APIs. No server objects, NBT, other teams or evaluator route. */
final class NativeQuests {
    private static final String BASE="dev.ftb.mods.ftbquests.";
    private final Minecraft client;
    private final GameQuestCatalog catalog=new GameQuestCatalog();
    private final GameQuestText texts=new GameQuestText();
    private final GameQuestComponents components=new GameQuestComponents();
    private final GameQuestMenu menus=new GameQuestMenu();
    private final GameQuestScreen screens=new GameQuestScreen();
    private final NativeQuestChoiceMenu.Bindings choices=new NativeQuestChoiceMenu.Bindings();
    private final GameQuestRecipeView.Bindings recipeViews=new GameQuestRecipeView.Bindings();
    private Object lastFile,lastTeam,lastConnection,lastPlayer;
    private long generation;
    NativeQuests(Minecraft client) { this.client=client; }
    void tick(){choices.tick(client.screen);recipeViews.tick(client.screen);}
    GameQuestRewardOpen.Port rewardOpenPort(Map<String,String> artifacts,GameActionLane.Operation context)throws IOException {
        var bound=source(artifacts);
        var navigation=new NativeQuestNavigation(client,bound,screens,query -> catalog.page(query,bound),context);
        return new NativeQuestRewardOpen(client,bound,navigation,query -> components.page(query,bound),context,choices);
    }
    GameQuestMenuAction.Port menuActionPort(Map<String,String> artifacts,GameActionLane.Operation context)throws IOException {
        var bound=source(artifacts);
        var navigation=new NativeQuestNavigation(client,bound,screens,query -> catalog.page(query,bound),context);
        if(client.screen instanceof dev.ftb.mods.ftblibrary.ui.ScreenWrapper wrapper && wrapper.getGui().getClass()==type("gui.SelectChoiceRewardScreen"))
            return new NativeQuestChoiceAction(client,bound,menus,navigation,context,choices);
        return new NativeQuestMenuAction(client,bound,menus,navigation,context);
    }
    GameQuestTaskOpen.Port taskOpenPort(Map<String,String> artifacts,GameActionLane.Operation context)throws IOException {
        var bound=source(artifacts);
        var navigation=new NativeQuestNavigation(client,bound,screens,query -> catalog.page(query,bound),context);
        return new NativeQuestTaskOpen(client,bound,navigation,query -> components.page(query,bound),context,artifacts,recipeViews);
    }
    GameQuestNavigation.Port navigationPort(Map<String,String> artifacts,GameActionLane.Operation context)throws IOException {
        var bound=source(artifacts);
        var book=new NativeQuestNavigation(client,bound,screens,query -> catalog.page(query,bound),context);
        if(client.screen!=null && client.screen.getClass().getName().equals("mezz.jei.gui.recipes.RecipesGui"))
            return new NativeQuestRecipeView(client,recipeViews,book,screens,context);
        return book;
    }
    JsonObject screen(Map<String,String> artifacts)throws IOException {return navigationPort(artifacts,() -> {}).read().json();}
    JsonObject recipePage(Map<String,String> artifacts)throws IOException {
        GameQuestRecipeView.requireArtifacts(artifacts);
        var port = navigationPort(artifacts, () -> {});
        if (!(port instanceof NativeQuestRecipeView recipe)) throw new IOException("GAME_RECIPE_RENDER_UNAVAILABLE");
        return recipe.page();
    }
    GameRecipeNavigation.Port recipeNavigationPort(Map<String,String> artifacts,GameActionLane.Operation context)throws IOException {
        GameQuestRecipeView.requireArtifacts(artifacts);
        var port = navigationPort(artifacts, context);
        if (!(port instanceof NativeQuestRecipeView recipe)) throw new IOException("GAME_RECIPE_RENDER_UNAVAILABLE");
        return recipe.navigation();
    }
    GameQuestOpen.Port openPort(Map<String,String> artifacts,GameActionLane.Operation context)throws IOException {
        var bound=source(artifacts);
        return NativeQuestOpening.port(client,() -> catalog.page(new GameQuestCatalog.Query(null,0),bound),context);
    }
    JsonObject menu(GameQuestMenu.Query query,Map<String,String> artifacts)throws IOException {
        var quests=source(artifacts);
        boolean choice=client.screen instanceof dev.ftb.mods.ftblibrary.ui.ScreenWrapper wrapper
            && wrapper.getGui().getClass()==type("gui.SelectChoiceRewardScreen");
        return menus.page(query,choice?NativeQuestChoiceMenu.source(client,quests,choices):NativeQuestItemMenu.source(client,quests));
    }
    JsonObject page(GameQuestCatalog.Query query,Map<String,String> artifacts) throws IOException {
        return catalog.page(query,source(artifacts));
    }
    JsonObject text(GameQuestText.Query query,Map<String,String> artifacts) throws IOException {
        return texts.page(query,source(artifacts));
    }
    JsonObject components(GameQuestComponents.Query query,Map<String,String> artifacts) throws IOException {
        return components.page(query,source(artifacts));
    }
    private GameQuestCatalog.Source source(Map<String,String> artifacts) throws IOException {
        GameQuestCatalog.requireArtifacts(artifacts);
        if (!client.isSameThread()) throw new IOException("CLIENT_THREAD_REQUIRED");
        final var player=client.player;final var level=client.level;final var connection=client.getConnection();
        if(player==null || level==null || connection==null) throw new IOException("GAME_NOT_CONNECTED");
        Class<?> fileType=type("client.ClientQuestFile"),teamType=type("quest.TeamData"),objectType=type("quest.QuestObject");
        final Object file=field(fileType,null,"INSTANCE");exact(file,"client.ClientQuestFile");
        final Object team=field(file.getClass(),file,"self");exact(team,"quest.TeamData");
        final Object[] chapter={null};
        class Context {
            void validate() throws IOException {
                if(!client.isSameThread() || client.player!=player || client.level!=level || client.getConnection()!=connection
                    || field(fileType,null,"INSTANCE")!=file || field(file.getClass(),file,"self")!=team
                    || field(teamType,team,"file")!=file
                    || !bool(call(file,"isPlayerOnTeam",new Class<?>[]{Player.class,teamType},player,team))
                    || bool(call(file,"canEdit"))) throw new IOException("GAME_QUEST_SOURCE_UNAVAILABLE");
                if(chapter[0]!=null && !bool(call(chapter[0],"isVisible",new Class<?>[]{teamType},team)))
                    throw new IOException("TARGET_NOT_OBSERVED");
            }
        }
        var context=new Context();context.validate();
        if(file!=lastFile || team!=lastTeam || connection!=lastConnection || player!=lastPlayer) {
            lastFile=file;lastTeam=team;lastConnection=connection;lastPlayer=player;generation++;
        }
        final long boundGeneration=generation;
        return new GameQuestCatalog.Source() {
            public long generation() {
                try { context.validate();return boundGeneration; } catch(IOException changed) { return -1; }
            }
            public Iterable<? extends GameQuestCatalog.Entry> entries(GameQuestCatalog.Query requested) throws IOException {
                var chapters=list(call(file,"getVisibleChapters",new Class<?>[]{teamType},team));
                if(requested.chapter()==null) return wrap(chapters,"quest.Chapter");
                Object selected=null;
                for(Object candidate:chapters) {
                    exact(candidate,"quest.Chapter");
                    if(!bool(call(candidate,"isVisible",new Class<?>[]{teamType},team))) continue;
                    if(requested.chapter().equals(call(candidate,"getCodeString"))) {
                        if(selected!=null) throw new IOException("GAME_QUEST_AMBIGUOUS");selected=candidate;
                    }
                }
                if(selected==null) throw new IOException("TARGET_NOT_OBSERVED");
                chapter[0]=selected;
                return wrap(list(call(selected,"getQuests")),"quest.Quest");
            }
            private List<GameQuestCatalog.Entry> wrap(List<?> objects,String kind) throws IOException {
                var result=new ArrayList<GameQuestCatalog.Entry>();
                for(Object object:objects) {
                    exact(object,kind);
                    if(call(object,"getQuestFile")!=file) throw new IOException("GAME_QUEST_CHANGED");
                    result.add(new GameQuestComponents.Quest() {
                        public boolean visible() throws IOException { return bool(call(object,"isVisible",new Class<?>[]{teamType},team)); }
                        public String id() throws IOException { return string(call(object,"getCodeString")); }
                        public String title() throws IOException {
                            Object value=call(object,"getTitle");
                            if(!(value instanceof Component text)) throw unsupported();return text.getString();
                        }
                        public int progress() throws IOException {
                            Object value=call(team,"getRelativeProgress",new Class<?>[]{objectType},object);
                            if(!(value instanceof Integer progress)) throw unsupported();return progress;
                        }
                        public boolean completed() throws IOException { return bool(call(team,"isCompleted",new Class<?>[]{objectType},object)); }
                        public boolean startable() throws IOException {
                            if(!kind.equals("quest.Quest")) throw unsupported();
                            return bool(call(team,"canStartTasks",new Class<?>[]{type("quest.Quest")},object));
                        }
                        public boolean detailsVisible() throws IOException { return !bool(call(object,"hideDetailsUntilStartable")) || startable(); }
                        public Iterable<? extends GameQuestComponents.Entry> components(String part) throws IOException {
                            var objects=list(field(object.getClass(),object,part));
                            if(objects.size()>GameQuestComponents.MAX_ENTRIES)throw new IOException("GAME_QUEST_BOUNDS");
                            var entries=new ArrayList<GameQuestComponents.Entry>();boolean task=part.equals("tasks");
                            Class<?> componentType=type(task ? "quest.task.Task" : "quest.reward.Reward");
                            for(Object component:objects) {
                                if(!componentType.isInstance(component) || field(componentType,component,"quest")!=object
                                        || call(component,"getQuestFile")!=file)throw unsupported();
                                entries.add(new GameQuestComponents.Entry() {
                                    public boolean visible() throws IOException {
                                        context.validate();
                                        if(!bool(call(object,"isVisible",new Class<?>[]{teamType},team)) || !detailsVisible())return false;
                                        if(task)return true;
                                        Object auto=call(component,"getAutoClaimType");
                                        if(!(auto instanceof Enum<?> state) || !auto.getClass().getName().equals(BASE+"quest.reward.RewardAutoClaim"))throw unsupported();
                                        return !bool(call(team,"isRewardBlocked",new Class<?>[]{componentType},component)) && !state.name().equals("INVISIBLE");
                                    }
                                    public String id() throws IOException {return string(call(component,"getCodeString"));}
                                    public GameQuestComponents.Display display() throws IOException {
                                        try {
                                            return task ? FtbQuestDisplays.task(component,team,startable()) : FtbQuestDisplays.reward(component,team,client);
                                        }catch(java.io.UncheckedIOException failure){throw failure.getCause();}
                                    }
                                });
                            }
                            return entries;
                        }
                        public String subtitle() throws IOException { return plain(call(object,"getSubtitle")); }
                        public boolean textVisible() throws IOException {
                            Object flag=field(object.getClass(),object,"hideTextUntilComplete");
                            return !bool(call(flag,"get",new Class<?>[]{boolean.class},false)) || completed();
                        }
                        public List<GameQuestText.Line> description() throws IOException {
                            var raw=list(field(object.getClass(),object,"description"));
                            if(raw.size()>GameQuestText.MAX_LINES) throw new IOException("GAME_QUEST_BOUNDS");
                            Object value=call(object,"getDescription");
                            if(!(value instanceof Component[] parts) || parts.length!=raw.size()) throw unsupported();
                            var lines=new ArrayList<GameQuestText.Line>();
                            for(int i=0;i<parts.length;i++) {
                                if(!(raw.get(i) instanceof String source)) throw unsupported();
                                if(source.equals("{@pagebreak}")) lines.add(new GameQuestText.Line("page_break",null));
                                else {
                                    try {lines.add(new GameQuestText.Line("text",plain(parts[i])));}
                                    catch(UnsupportedText rich) {lines.add(new GameQuestText.Line("unsupported",null));}
                                }
                            }
                            return lines;
                        }
                    });
                }
                return result;
            }
        };
    }
    static final class UnsupportedText extends IOException {
        UnsupportedText() {super("GAME_QUEST_RICH_TEXT_UNSUPPORTED");}
    }
    static String plain(Object value) throws IOException {
        if(!(value instanceof Component component)) throw unsupported();
        plainTree(component,new java.util.IdentityHashMap<>(),0);
        String text=component.getString();GameQuestText.bounded(text,4096);return text;
    }
    private static void plainTree(Component value,java.util.IdentityHashMap<Component,Boolean> seen,int depth) throws IOException {
        if(depth>32 || seen.size()>=128 || seen.put(value,true)!=null) throw new UnsupportedText();
        if(!value.getClass().getName().equals("net.minecraft.network.chat.MutableComponent")
                || value.getStyle().getClickEvent()!=null || value.getStyle().getHoverEvent()!=null) throw new UnsupportedText();
        var contents=value.getContents();
        if(contents instanceof net.minecraft.network.chat.contents.TranslatableContents translated) {
            if(translated.getArgs().length>64) throw new UnsupportedText();
            for(Object argument:translated.getArgs()) {
                if(argument instanceof Component component) plainTree(component,seen,depth+1);
                else if(argument!=null && !(argument instanceof String || argument instanceof Number || argument instanceof Boolean))
                    throw new UnsupportedText();
            }
        } else if(contents!=net.minecraft.network.chat.ComponentContents.EMPTY && !(contents instanceof net.minecraft.network.chat.contents.LiteralContents)
                && !(contents instanceof net.minecraft.network.chat.contents.KeybindContents)) throw new UnsupportedText();
        if(value.getSiblings().size()>64) throw new UnsupportedText();
        for(Component sibling:value.getSiblings()) plainTree(sibling,seen,depth+1);
    }
    private static List<?> list(Object value) throws IOException {
        if(!(value instanceof List<?> list) || list.size()>GameQuestCatalog.MAX_MATCHES) throw new IOException("GAME_QUEST_BOUNDS");
        return list;
    }
    static Class<?> type(String name) throws IOException {
        try { return Class.forName(BASE+name); } catch(ClassNotFoundException | LinkageError failure) { throw unsupported(); }
    }
    private static void exact(Object value,String name) throws IOException {
        if(value==null || !value.getClass().getName().equals(BASE+name)) throw unsupported();
    }
    static Object field(Class<?> type,Object owner,String name) throws IOException {
        try { return type.getField(name).get(owner); } catch(ReflectiveOperationException | SecurityException failure) { throw unsupported(); }
    }
    static Object call(Object owner,String name) throws IOException { return call(owner,name,new Class<?>[0]); }
    static Object call(Object owner,String name,Class<?>[] types,Object... args) throws IOException {
        try { return owner.getClass().getMethod(name,types).invoke(owner,args); }
        catch(ReflectiveOperationException | SecurityException failure) {
            if(failure instanceof java.lang.reflect.InvocationTargetException invocation
                    && invocation.getCause() instanceof java.io.UncheckedIOException io)throw io.getCause();
            throw unsupported();
        }
    }
    static boolean bool(Object value) throws IOException { if(!(value instanceof Boolean flag)) throw unsupported();return flag; }
    static String string(Object value) throws IOException { if(!(value instanceof String text)) throw unsupported();return text; }
    private static IOException unsupported() { return new IOException("GAME_QUEST_SOURCE_UNSUPPORTED"); }
}
