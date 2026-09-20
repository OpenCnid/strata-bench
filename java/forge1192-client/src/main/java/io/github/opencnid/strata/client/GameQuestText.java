package io.github.opencnid.strata.client;

import com.google.gson.JsonArray;
import com.google.gson.JsonNull;
import com.google.gson.JsonObject;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.List;

/** One player-readable quest. Visibility gates precede every content reader. */
final class GameQuestText {
    static final String POLICY="ftb-visible-own-quest-plain-text-pages32/1";
    static final int MAX_LINES=512;
    record Query(String chapter,String quest,int after) {
        Query {
            if(chapter==null || !chapter.matches("[0-9A-F]{16}") || quest==null || !quest.matches("[0-9A-F]{16}")
                    || after<0 || after>MAX_LINES) throw new IllegalArgumentException("GAME_QUEST_QUERY_INVALID");
        }
        JsonObject json() {
            var value=new JsonObject();value.addProperty("source","ftb_quests");value.addProperty("chapter_id",chapter);
            value.addProperty("quest_id",quest);value.addProperty("after",after);return value;
        }
        static Query read(JsonObject value) throws IOException {
            SettingsJson.fields(value,"source","chapter_id","quest_id","after");
            if(!SettingsJson.string(value,"source").equals("ftb_quests")) throw new IOException("MECHANIC_UNSUPPORTED");
            long after=SettingsJson.integer(value,"after");if(after>MAX_LINES) throw new IOException("GAME_QUEST_BOUNDS");
            try { return new Query(SettingsJson.string(value,"chapter_id"),SettingsJson.string(value,"quest_id"),(int)after); }
            catch(IllegalArgumentException failure) { throw new IOException("GAME_QUEST_QUERY_INVALID"); }
        }
    }
    interface Entry extends GameQuestCatalog.Entry {
        String subtitle() throws IOException;
        boolean textVisible() throws IOException;
        List<Line> description() throws IOException;
    }
    record Line(String kind,String text) {
        JsonObject json() throws IOException {
            if(!List.of("text","page_break","unsupported").contains(kind)
                    || kind.equals("text")!=(text!=null)) throw new IOException("GAME_QUEST_SOURCE_UNSUPPORTED");
            if(text!=null) bounded(text,4096);
            var value=new JsonObject();value.addProperty("kind",kind);
            if(text==null) value.add("text",JsonNull.INSTANCE);else value.addProperty("text",text);return value;
        }
    }
    private final java.util.function.LongSupplier clock;
    private long revision=0;
    private String digest;
    GameQuestText() { this(System::nanoTime); }
    GameQuestText(java.util.function.LongSupplier clock) { this.clock=clock; }
    JsonObject page(Query query,GameQuestCatalog.Source source) throws IOException {
        long started=clock.getAsLong(),generation=source.generation();
        if(generation<0 || generation>9007199254740991L) throw new IOException("GAME_QUEST_SOURCE_UNAVAILABLE");
        Entry selected=null;int inspected=0;
        for(var candidate:source.entries(new GameQuestCatalog.Query(query.chapter,0))) {
            checkTime(started);if(++inspected>GameQuestCatalog.MAX_MATCHES) throw new IOException("GAME_QUEST_BOUNDS");
            if(!candidate.visible()) continue;
            if(!query.quest.equals(candidate.id())) continue;
            if(selected!=null) throw new IOException("GAME_QUEST_AMBIGUOUS");
            if(!(candidate instanceof Entry entry)) throw new IOException("GAME_QUEST_SOURCE_UNSUPPORTED");
            selected=entry;
        }
        if(selected==null || !selected.detailsVisible()) throw new IOException("TARGET_NOT_OBSERVED");
        String title=selected.title(),subtitle=selected.subtitle();bounded(title,1024);bounded(subtitle,1024);
        boolean textVisible=selected.textVisible();
        List<Line> lines=textVisible ? selected.description() : List.of();
        if(lines==null || lines.size()>MAX_LINES || query.after>lines.size()) throw new IOException("GAME_QUEST_BOUNDS");
        var all=new JsonArray();int bytes=0;
        for(var line:lines) {
            checkTime(started);if(line==null) throw new IOException("GAME_QUEST_SOURCE_UNSUPPORTED");
            var value=line.json();bytes+=bytes(value);if(bytes>2*1024*1024) throw new IOException("GAME_QUEST_BOUNDS");all.add(value);
        }
        if(!selected.visible() || !selected.detailsVisible() || selected.textVisible()!=textVisible
                || source.generation()!=generation) throw new IOException("GAME_QUEST_CHANGED");
        var value=new JsonObject();value.add("query",query.json());value.addProperty("source_generation",generation);
        value.addProperty("policy",POLICY);value.addProperty("title",title);value.addProperty("subtitle",subtitle);
        value.addProperty("description_visible",textVisible);value.add("lines",all);
        var identity=value.deepCopy();identity.getAsJsonObject("query").addProperty("after",0);
        String nextDigest=KeyOptions.sha256(identity.toString());
        if(!nextDigest.equals(digest)) {digest=nextDigest;revision++;}
        value.addProperty("revision",revision);var page=new JsonArray();value.add("lines",page);value.add("next_cursor",JsonNull.INSTANCE);
        int next=query.after;
        while(next<all.size() && page.size()<32) {
            if(bytes(value)+all.get(next).toString().getBytes(StandardCharsets.UTF_8).length+32>32768) break;
            page.add(all.get(next++));
        }
        if(next<all.size()) {if(next==query.after) throw new IOException("GAME_QUEST_BOUNDS");value.addProperty("next_cursor",next);}
        checkTime(started);return value;
    }
    private void checkTime(long started) throws IOException {if(clock.getAsLong()-started>GameQuestCatalog.MAX_NANOS) throw new IOException("GAME_QUEST_TIMEOUT");}
    private static int bytes(JsonObject value) {return value.toString().getBytes(StandardCharsets.UTF_8).length;}
    static void bounded(String value,int points) throws IOException {
        if(value==null || value.codePoints().anyMatch(cp->cp>=0xD800 && cp<=0xDFFF)
                || value.codePointCount(0,value.length())>points || value.getBytes(StandardCharsets.UTF_8).length>points*4)
            throw new IOException("GAME_QUEST_BOUNDS");
    }
}
