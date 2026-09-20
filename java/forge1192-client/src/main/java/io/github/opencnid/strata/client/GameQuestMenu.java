package io.github.opencnid.strata.client;

import com.google.gson.JsonArray;
import com.google.gson.JsonNull;
import com.google.gson.JsonObject;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;

/** Current visible item/choice UI only. No menu-opening or mutation authority. */
final class GameQuestMenu {
    static final String POLICY="ftb-current-item-choice-clipped-pages32/4";
    static final int MAX_ITEMS=512;
    record Query(int after) {
        Query {if(after<0 || after>MAX_ITEMS)throw new IllegalArgumentException("GAME_QUEST_QUERY_INVALID");}
        JsonObject json(){var value=new JsonObject();value.addProperty("source","ftb_quests");value.addProperty("after",after);return value;}
        static Query read(JsonObject value)throws IOException {
            SettingsJson.fields(value,"source","after");
            if(!SettingsJson.string(value,"source").equals("ftb_quests"))throw new IOException("MECHANIC_UNSUPPORTED");
            long after=SettingsJson.integer(value,"after");if(after>MAX_ITEMS)throw new IOException("GAME_QUEST_BOUNDS");
            return new Query((int)after);
        }
    }
    record Context(String chapter,String quest,String task,String reward,String title) {
        Context(String chapter,String quest,String task,String title){this(chapter,quest,task,null,title);}
        String kind(){return task==null?"reward_choices":"item_alternatives";}
        JsonObject json()throws IOException {
            if((task==null)==(reward==null))throw invalid();
            for(String id:new String[]{chapter,quest,task==null?reward:task})if(id==null || !id.matches("[0-9A-F]{16}"))throw invalid();
            GameQuestText.bounded(title,1024);
            var value=new JsonObject();value.addProperty("chapter_id",chapter);value.addProperty("quest_id",quest);
            value.addProperty(task==null?"reward_id":"task_id",task==null?reward:task);value.addProperty("title",title);return value;
        }
    }
    interface Source {
        void validate()throws IOException;
        long generation()throws IOException;
        Object screen()throws IOException;
        String layout()throws IOException;
        Context context()throws IOException;
        Iterable<? extends Item> items()throws IOException;
        Iterable<? extends Control> controls()throws IOException;
    }
    interface Display {JsonObject json(int index)throws IOException;}
    interface Item {boolean visible()throws IOException; Display display()throws IOException;}
    interface Control {boolean visible()throws IOException; ControlDisplay display()throws IOException;}
    record ItemDisplay(String itemId,int count,String name,List<GameQuestText.Line> tooltip) implements Display {
        public JsonObject json(int index)throws IOException {
            if(itemId==null || itemId.length()>256 || !itemId.matches("[a-z0-9_.-]+:[a-z0-9_./-]+") || count<1)throw invalid();
            GameQuestText.bounded(name,1024);var value=new JsonObject();value.addProperty("index",index);
            value.addProperty("item_id",itemId);value.addProperty("count",count);value.addProperty("name",name);
            value.add("tooltip",lines(tooltip));boundRow(value);return value;
        }
    }
    record ChoiceDisplay(String title,boolean enabled,List<GameQuestText.Line> tooltip) implements Display {
        public JsonObject json(int index)throws IOException {
            GameQuestText.bounded(title,1024);var value=new JsonObject();value.addProperty("index",index);
            value.addProperty("title",title);value.addProperty("enabled",enabled);value.add("tooltip",lines(tooltip));
            boundRow(value);return value;
        }
    }
    record ControlDisplay(String control,String title,boolean enabled,List<GameQuestText.Line> tooltip) {
        JsonObject json()throws IOException {
            if(control==null || !List.of("back","submit").contains(control))throw invalid();
            GameQuestText.bounded(title,1024);var value=new JsonObject();value.addProperty("control",control);
            value.addProperty("title",title);value.addProperty("enabled",enabled);value.add("tooltip",lines(tooltip));
            boundRow(value);return value;
        }
    }
    /** Native panel offsets truncate negated scroll toward zero, rather than rounding/flooring. */
    static int scrollOffset(double value)throws IOException {
        if(!Double.isFinite(value) || Math.abs(value)>1048576)throw new IOException("GAME_QUEST_LAYOUT_UNSUPPORTED");
        return (int)-value;
    }
    record Rect(int x,int y,int width,int height) {
        Rect {if(Math.abs((long)x)>1048576 || Math.abs((long)y)>1048576 || width<0 || height<0
                || width>1048576 || height>1048576)throw new IllegalArgumentException("GAME_QUEST_LAYOUT_UNSUPPORTED");}
        Rect intersect(Rect other) {
            int left=Math.max(x,other.x),top=Math.max(y,other.y);
            return new Rect(left,top,Math.max(0,Math.min(x+width,other.x+other.width)-left),
                Math.max(0,Math.min(y+height,other.y+other.height)-top));
        }
        boolean nonempty(){return width>0 && height>0;}
    }
    private Object lastScreen;
    private long lastSource=-1,menuGeneration,revision;
    private String digest;
    private final java.util.function.LongSupplier clock;
    GameQuestMenu(){this(System::nanoTime);}
    GameQuestMenu(java.util.function.LongSupplier clock){this.clock=clock;}
    JsonObject page(Query query,Source source)throws IOException {
        long started=clock.getAsLong();source.validate();long generation=source.generation();Object screen=source.screen();
        if(generation<0 || generation>9007199254740991L || screen==null)throw new IOException("GAME_QUEST_SOURCE_UNAVAILABLE");
        String layout=source.layout();if(layout==null || !layout.matches("[a-f0-9]{64}"))throw invalid();
        var initialContext=source.context();if(initialContext==null)throw invalid();
        var context=initialContext.json();var entries=new ArrayList<JsonObject>();int inspected=0,totalBytes=0;
        for(var item:source.items()) {
            checkTime(started);if(++inspected>MAX_ITEMS)throw new IOException("GAME_QUEST_BOUNDS");
            if(!item.visible())continue;
            var display=item.display();
            if(initialContext.task()!=null?!(display instanceof ItemDisplay):!(display instanceof ChoiceDisplay))throw invalid();
            var row=display.json(entries.size());
            if(!item.visible())throw changed();entries.add(row);totalBytes+=bytes(row);
            if(totalBytes>4*1024*1024)throw new IOException("GAME_QUEST_BOUNDS");
        }
        var controls=new JsonArray();var roles=new HashSet<String>();inspected=0;
        for(var control:source.controls()) {
            checkTime(started);if(++inspected>2)throw new IOException("GAME_QUEST_BOUNDS");
            if(!control.visible())continue;
            var display=control.display();if(display==null)throw invalid();var row=display.json();
            if(!roles.add(display.control()))throw new IOException("GAME_QUEST_AMBIGUOUS");
            if(!control.visible())throw changed();controls.add(row);
        }
        if(bytes(controls)>8192)throw new IOException("GAME_QUEST_BOUNDS");
        if(initialContext.task()==null && !controls.isEmpty())throw invalid();
        source.validate();
        var finalContext=source.context();if(finalContext==null)throw changed();
        if(source.screen()!=screen || source.generation()!=generation || !layout.equals(source.layout())
                || !context.equals(finalContext.json()))throw changed();
        if(query.after>entries.size())throw new IOException("GAME_QUEST_BOUNDS");
        long nextGeneration=menuGeneration+(screen!=lastScreen || generation!=lastSource ? 1:0);
        var identity=new JsonObject();identity.add("context",context);identity.addProperty("source_generation",generation);
        identity.addProperty("menu_generation",nextGeneration);identity.addProperty("layout",layout);
        identity.addProperty("entries",entries.toString());identity.add("controls",controls);
        String nextDigest=KeyOptions.sha256(identity.toString());long nextRevision=revision+(nextDigest.equals(digest)?0:1);
        var value=new JsonObject();value.add("query",query.json());value.addProperty("source_generation",generation);
        value.addProperty("menu_generation",nextGeneration);value.addProperty("policy",POLICY);value.addProperty("revision",nextRevision);
        value.addProperty("menu_kind",initialContext.kind());value.add("context",context);value.add("controls",controls);
        var rows=new JsonArray();value.add("entries",rows);value.add("next_cursor",JsonNull.INSTANCE);int next=query.after;
        while(next<entries.size() && rows.size()<32) {
            if(bytes(value)+bytes(entries.get(next))+32>32768)break;rows.add(entries.get(next++));
        }
        if(next<entries.size()){if(next==query.after)throw new IOException("GAME_QUEST_BOUNDS");value.addProperty("next_cursor",next);}
        if(bytes(value)>32768)throw new IOException("GAME_QUEST_BOUNDS");checkTime(started);
        lastScreen=screen;lastSource=generation;menuGeneration=nextGeneration;revision=nextRevision;digest=nextDigest;
        return value;
    }
    private static JsonArray lines(List<GameQuestText.Line> lines)throws IOException {
        if(lines==null || lines.size()>64)throw new IOException("GAME_QUEST_BOUNDS");var value=new JsonArray();
        for(var line:lines){if(line==null || line.kind()==null || line.kind().equals("page_break"))throw invalid();value.add(line.json());}return value;
    }
    private static void boundRow(JsonObject value)throws IOException {if(bytes(value)>16384)throw new IOException("GAME_QUEST_BOUNDS");}
    private static int bytes(com.google.gson.JsonElement value){return value.toString().getBytes(StandardCharsets.UTF_8).length;}
    private void checkTime(long started)throws IOException {if(clock.getAsLong()-started>GameQuestCatalog.MAX_NANOS)throw new IOException("GAME_QUEST_TIMEOUT");}
    private static IOException invalid(){return new IOException("GAME_QUEST_SOURCE_UNSUPPORTED");}
    private static IOException changed(){return new IOException("GAME_QUEST_CHANGED");}
}
