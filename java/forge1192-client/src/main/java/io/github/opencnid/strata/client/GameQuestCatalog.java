package io.github.opencnid.strata.client;

import com.google.gson.JsonArray;
import com.google.gson.JsonNull;
import com.google.gson.JsonObject;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.Map;
import java.util.TreeMap;

/** Player quest UI catalog only. Benchmark predicates and sibling teams have no source route. */
final class GameQuestCatalog {
    static final String POLICY = "ftb-visible-chapters-quests-own-team-pages32/1";
    static final int MAX_MATCHES = 4096;
    static final long MAX_NANOS = 100_000_000L;
    static final Map<String,String> ARTIFACTS = Map.of(
        "ftb-quests-forge-1902.5.10-build.497.jar", "b008de3ad8ed0d331af2853f12369ec560348348fd1e62a21dbbdad6c90e5678",
        "ftb-library-forge-1902.4.1-build.236.jar", "1ba0d7fa626ddb2e3c31e77e20b573ca79eb92e7667cca5b9a3e985fc22d1592",
        "ftb-teams-forge-1902.2.14-build.123.jar", "2233122cfddfccafd5f4840ae63a556edd7088ad15e177fb1288367adef142f7");
    static void requireArtifacts(Map<String,String> artifacts) throws IOException {
        for (var pin:ARTIFACTS.entrySet()) if (!pin.getValue().equals(artifacts.get(pin.getKey())))
            throw new IOException("GAME_QUEST_ARTIFACT_UNSUPPORTED");
    }
    record Query(String chapter, int after) {
        Query {
            if (chapter != null && !chapter.matches("[0-9A-F]{16}") || after < 0 || after > MAX_MATCHES)
                throw new IllegalArgumentException("GAME_QUEST_QUERY_INVALID");
        }
        JsonObject json() {
            var value=new JsonObject();value.addProperty("source","ftb_quests");
            if (chapter==null) value.add("chapter_id",JsonNull.INSTANCE); else value.addProperty("chapter_id",chapter);
            value.addProperty("after",after);return value;
        }
        static Query read(JsonObject value) throws IOException {
            SettingsJson.fields(value,"source","chapter_id","after");
            if (!SettingsJson.string(value,"source").equals("ftb_quests")) throw new IOException("MECHANIC_UNSUPPORTED");
            long after=SettingsJson.integer(value,"after");
            if (after>MAX_MATCHES) throw new IOException("GAME_QUEST_BOUNDS");
            try { return new Query(value.get("chapter_id").isJsonNull() ? null : SettingsJson.string(value,"chapter_id"),(int)after); }
            catch (IllegalArgumentException failure) { throw new IOException("GAME_QUEST_QUERY_INVALID"); }
        }
    }
    interface Entry {
        boolean visible() throws IOException;
        String id() throws IOException;
        String title() throws IOException;
        int progress() throws IOException;
        boolean completed() throws IOException;
        boolean startable() throws IOException;
        boolean detailsVisible() throws IOException;
    }
    interface Source {
        long generation();
        Iterable<? extends Entry> entries(Query query) throws IOException;
    }
    private final java.util.function.LongSupplier clock;
    private long generation=-1,revision=0;
    private String focus,digest;
    GameQuestCatalog() { this(System::nanoTime); }
    GameQuestCatalog(java.util.function.LongSupplier clock) { this.clock=clock; }
    JsonObject page(Query query,Source source) throws IOException {
        long started=clock.getAsLong(), sourceGeneration=source.generation();
        if (sourceGeneration<0 || sourceGeneration>9007199254740991L) throw new IOException("GAME_QUEST_SOURCE_UNAVAILABLE");
        var entries=new TreeMap<String,JsonObject>();int inspected=0,totalBytes=0;
        for (var entry:source.entries(query)) {
            checkTime(started);
            if (++inspected>MAX_MATCHES) throw new IOException("GAME_QUEST_BOUNDS");
            if (!entry.visible()) continue; // Never inspect hidden identifiers/titles/progress.
            String id=entry.id(); if (id==null || !id.matches("[0-9A-F]{16}")) throw new IOException("GAME_QUEST_SOURCE_UNSUPPORTED");
            String title=entry.title();
            if (title==null || title.codePoints().anyMatch(cp->cp>=0xD800 && cp<=0xDFFF)
                    || title.codePointCount(0,title.length())>1024 || title.getBytes(StandardCharsets.UTF_8).length>4096)
                throw new IOException("GAME_QUEST_BOUNDS");
            int progress=entry.progress();boolean completed=entry.completed();
            if (progress<0 || progress>100 || completed && progress!=100) throw new IOException("GAME_QUEST_SOURCE_UNSUPPORTED");
            var value=new JsonObject();value.addProperty("kind",query.chapter==null ? "chapter" : "quest");
            value.addProperty("entry_id",id);value.addProperty("title",title);value.addProperty("progress_percent",progress);
            value.addProperty("completed",completed);
            if(query.chapter==null) { value.add("startable",JsonNull.INSTANCE);value.add("details_visible",JsonNull.INSTANCE); }
            else {
                boolean startable=entry.startable(),details=entry.detailsVisible();
                if(startable && !details) throw new IOException("GAME_QUEST_SOURCE_UNSUPPORTED");
                value.addProperty("startable",startable);value.addProperty("details_visible",details);
            }
            if(entries.put(id,value)!=null) throw new IOException("GAME_QUEST_AMBIGUOUS");
            totalBytes+=bytes(value);if(totalBytes>4*1024*1024) throw new IOException("GAME_QUEST_BOUNDS");
        }
        checkTime(started);if(source.generation()!=sourceGeneration) throw new IOException("GAME_QUEST_CHANGED");
        String nextDigest=KeyOptions.sha256(entries.values().toString());
        if(sourceGeneration!=generation || !java.util.Objects.equals(focus,query.chapter) || !nextDigest.equals(digest)) {
            generation=sourceGeneration;focus=query.chapter;digest=nextDigest;revision++;
        }
        if(query.after>entries.size()) throw new IOException("GAME_QUEST_BOUNDS");
        var value=new JsonObject();value.add("query",query.json());value.addProperty("source_generation",sourceGeneration);
        value.addProperty("policy",POLICY);value.addProperty("revision",revision);var rows=new JsonArray();value.add("entries",rows);
        value.add("next_cursor",JsonNull.INSTANCE);var ordered=java.util.List.copyOf(entries.values());int next=query.after;
        while(next<ordered.size() && rows.size()<32) {
            if(bytes(value)+bytes(ordered.get(next))+32>32768) break;
            rows.add(ordered.get(next++));
        }
        if(next<ordered.size()) { if(next==query.after) throw new IOException("GAME_QUEST_BOUNDS");value.addProperty("next_cursor",next); }
        checkTime(started);return value;
    }
    private void checkTime(long started) throws IOException { if(clock.getAsLong()-started>MAX_NANOS) throw new IOException("GAME_QUEST_TIMEOUT"); }
    private static int bytes(JsonObject value) { return value.toString().getBytes(StandardCharsets.UTF_8).length; }
}
