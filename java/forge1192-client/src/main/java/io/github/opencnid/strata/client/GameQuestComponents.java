package io.github.opencnid.strata.client;

import com.google.gson.JsonArray;
import com.google.gson.JsonNull;
import com.google.gson.JsonObject;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.TreeMap;

/** Visible task/reward display pages, never raw definitions or mutation authority. */
final class GameQuestComponents {
    static final String POLICY="ftb-visible-own-quest-task-reward-tooltips-pages32/1";
    static final int MAX_ENTRIES=512;
    record Query(String chapter,String quest,String part,int after) {
        Query {
            new GameQuestText.Query(chapter,quest,after);
            if(part==null || !List.of("tasks","rewards").contains(part)) throw new IllegalArgumentException("GAME_QUEST_QUERY_INVALID");
        }
        JsonObject json() {
            var value=new GameQuestText.Query(chapter,quest,after).json();value.addProperty("part",part);return value;
        }
        static Query read(JsonObject value) throws IOException {
            SettingsJson.fields(value,"source","chapter_id","quest_id","part","after");
            var text=value.deepCopy();text.remove("part");var query=GameQuestText.Query.read(text);
            try{return new Query(query.chapter(),query.quest(),SettingsJson.string(value,"part"),query.after());}
            catch(IllegalArgumentException failure){throw new IOException("GAME_QUEST_QUERY_INVALID");}
        }
    }
    interface Quest extends GameQuestText.Entry { Iterable<? extends Entry> components(String part) throws IOException; }
    interface Entry {
        boolean visible() throws IOException;
        String id() throws IOException;
        Display display() throws IOException;
    }
    record Display(String title,List<GameQuestText.Line> tooltip,Task task,Reward reward) {
        JsonObject json(String id,String part) throws IOException {
            GameQuestText.bounded(title,1024);
            if(tooltip==null || tooltip.size()>64 || (task!=null)!=part.equals("tasks")
                    || (reward!=null)!=part.equals("rewards")) throw new IOException("GAME_QUEST_SOURCE_UNSUPPORTED");
            var value=new JsonObject();value.addProperty("entry_id",id);value.addProperty("kind",part.equals("tasks") ? "task" : "reward");
            value.addProperty("title",title);var lines=new JsonArray();value.add("tooltip",lines);
            for(var line:tooltip) {
                if(line==null || line.kind().equals("page_break")) throw new IOException("GAME_QUEST_SOURCE_UNSUPPORTED");
                lines.add(line.json());
            }
            value.add("task",task==null ? JsonNull.INSTANCE : task.json());
            value.add("reward",reward==null ? JsonNull.INSTANCE : reward.json());
            if(bytes(value)>16384) throw new IOException("GAME_QUEST_BOUNDS");return value;
        }
    }
    interface Progress {
        boolean startable() throws IOException;
        long maximum() throws IOException;
        long current() throws IOException;
        boolean hiddenNumbers() throws IOException;
        int percent() throws IOException;
        String maximumLabel() throws IOException;
        String currentLabel(long current) throws IOException;
    }
    static String progressLabel(Progress source) throws IOException {
        if(!source.startable())return null;
        long maximum=source.maximum(),current=source.current();
        if(maximum<0 || current<0)throw new IOException("GAME_QUEST_SOURCE_UNSUPPORTED");
        if(maximum<=1)return null;
        String label;
        if(source.hiddenNumbers())label="["+checkedPercent(source.percent())+"%]";
        else {
            String max=source.maximumLabel(),amount=current>maximum ? max : source.currentLabel(current);
            GameQuestText.bounded(max,256);GameQuestText.bounded(amount,256);
            label=amount+" / "+max+(maximum>=100 ? " ["+checkedPercent(source.percent())+"%]" : "");
        }
        GameQuestText.bounded(label,256);return label;
    }
    private static int checkedPercent(int value) throws IOException {
        if(value<0 || value>100)throw new IOException("GAME_QUEST_SOURCE_UNSUPPORTED");return value;
    }
    record Task(boolean completed,boolean optional,String progressLabel) {
        JsonObject json() throws IOException {
            if(progressLabel!=null) GameQuestText.bounded(progressLabel,256);
            var value=new JsonObject();value.addProperty("completed",completed);value.addProperty("optional",optional);
            if(progressLabel==null)value.add("progress_label",JsonNull.INSTANCE);else value.addProperty("progress_label",progressLabel);return value;
        }
    }
    record Reward(String claimState,boolean teamReward) {
        JsonObject json() throws IOException {
            if(!List.of("can_claim","cannot_claim","claimed").contains(claimState)) throw new IOException("GAME_QUEST_SOURCE_UNSUPPORTED");
            var value=new JsonObject();value.addProperty("claim_state",claimState);value.addProperty("team_reward",teamReward);return value;
        }
    }
    private final java.util.function.LongSupplier clock;
    private String digest;
    private long revision;
    GameQuestComponents(){this(System::nanoTime);}
    GameQuestComponents(java.util.function.LongSupplier clock){this.clock=clock;}
    JsonObject page(Query query,GameQuestCatalog.Source source) throws IOException {
        long started=clock.getAsLong(),generation=source.generation();
        if(generation<0 || generation>9007199254740991L)throw new IOException("GAME_QUEST_SOURCE_UNAVAILABLE");
        Quest selected=null;int inspected=0;
        for(var entry:source.entries(new GameQuestCatalog.Query(query.chapter,0))) {
            checkTime(started);if(++inspected>GameQuestCatalog.MAX_MATCHES)throw new IOException("GAME_QUEST_BOUNDS");
            if(!entry.visible() || !query.quest.equals(entry.id()))continue;
            if(selected!=null)throw new IOException("GAME_QUEST_AMBIGUOUS");
            if(!(entry instanceof Quest quest))throw new IOException("GAME_QUEST_SOURCE_UNSUPPORTED");selected=quest;
        }
        if(selected==null || !selected.detailsVisible())throw new IOException("TARGET_NOT_OBSERVED");
        var entries=new TreeMap<String,JsonObject>();int totalBytes=0;inspected=0;
        for(var entry:selected.components(query.part)) {
            checkTime(started);if(++inspected>MAX_ENTRIES)throw new IOException("GAME_QUEST_BOUNDS");
            if(!entry.visible())continue; // Hidden rewards have no ID/title/definition reader.
            String id=entry.id();if(id==null || !id.matches("[0-9A-F]{16}"))throw new IOException("GAME_QUEST_SOURCE_UNSUPPORTED");
            var display=entry.display();if(display==null)throw new IOException("GAME_QUEST_SOURCE_UNSUPPORTED");
            var value=display.json(id,query.part);
            if(!entry.visible())throw new IOException("GAME_QUEST_CHANGED");
            if(entries.put(id,value)!=null)throw new IOException("GAME_QUEST_AMBIGUOUS");
            totalBytes+=bytes(value);if(totalBytes>4*1024*1024)throw new IOException("GAME_QUEST_BOUNDS");
        }
        if(!selected.visible() || !selected.detailsVisible() || source.generation()!=generation)throw new IOException("GAME_QUEST_CHANGED");
        if(query.after>entries.size())throw new IOException("GAME_QUEST_BOUNDS");
        var identity=new JsonObject();var focus=query.json();focus.addProperty("after",0);identity.add("query",focus);
        identity.addProperty("generation",generation);identity.addProperty("entries",entries.values().toString());
        String nextDigest=KeyOptions.sha256(identity.toString());if(!nextDigest.equals(digest)){digest=nextDigest;revision++;}
        var value=new JsonObject();value.add("query",query.json());value.addProperty("source_generation",generation);
        value.addProperty("policy",POLICY);value.addProperty("revision",revision);var rows=new JsonArray();value.add("entries",rows);
        value.add("next_cursor",JsonNull.INSTANCE);var ordered=List.copyOf(entries.values());int next=query.after;
        while(next<ordered.size() && rows.size()<32) {
            if(bytes(value)+bytes(ordered.get(next))+32>32768)break;rows.add(ordered.get(next++));
        }
        if(next<ordered.size()){if(next==query.after)throw new IOException("GAME_QUEST_BOUNDS");value.addProperty("next_cursor",next);}
        checkTime(started);return value;
    }
    private void checkTime(long started)throws IOException {if(clock.getAsLong()-started>GameQuestCatalog.MAX_NANOS)throw new IOException("GAME_QUEST_TIMEOUT");}
    private static int bytes(JsonObject value){return value.toString().getBytes(StandardCharsets.UTF_8).length;}
}
