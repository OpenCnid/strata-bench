package io.github.opencnid.strata.client;

import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

/** Synthetic player-quest sources; no FTB runtime or benchmark scoring is mocked as authentic. */
class GameQuestCatalogTest {
    static final String CHAPTER="0000000000000001";
    static class Entry implements GameQuestCatalog.Entry {
        String id=CHAPTER,title="Visible chapter";int progress;boolean visible=true,completed,startable,details;
        public boolean visible() { return visible; }
        public String id() { return id; }
        public String title() { return title; }
        public int progress() { return progress; }
        public boolean completed() { return completed; }
        public boolean startable() { return startable; }
        public boolean detailsVisible() { return details; }
    }
    static class Source implements GameQuestCatalog.Source {
        long generation=1;List<GameQuestCatalog.Entry> entries=new ArrayList<>();
        public long generation() { return generation; }
        public Iterable<? extends GameQuestCatalog.Entry> entries(GameQuestCatalog.Query query) { return entries; }
    }
    static Source fixture(GameQuestCatalog.Query query) throws IOException {
        if(query.chapter()!=null && !query.chapter().equals(CHAPTER)) throw new IOException("TARGET_NOT_OBSERVED");
        var source=new Source();var entry=new Entry();
        if(query.chapter()!=null) { entry.id="0000000000000002";entry.title="Visible quest";entry.progress=25;entry.details=true; }
        source.entries.add(entry);return source;
    }
    @Test void rootAndQuestPagesPreserveOrdinaryProgressAndSeparateDetailAccess() throws Exception {
        for(String chapter:new String[]{null,CHAPTER}) {
            var query=new GameQuestCatalog.Query(chapter,0);
            var page=new GameQuestCatalog(()->0).page(query,fixture(query));
            assertEquals(query.json(),page.get("query"));assertEquals(GameQuestCatalog.POLICY,page.get("policy").getAsString());
            var row=page.getAsJsonArray("entries").get(0).getAsJsonObject();
            assertEquals(7,row.size());assertFalse(row.has("team_id"));assertFalse(row.has("description"));assertFalse(row.has("score"));
            if(chapter==null) assertTrue(row.get("startable").isJsonNull());
            else { assertFalse(row.get("startable").getAsBoolean());assertTrue(row.get("details_visible").getAsBoolean());assertEquals(25,row.get("progress_percent").getAsInt()); }
        }
    }
    @Test void hiddenEntriesNeverReadIdentifiersTitlesOrProgressAndRootNeverReadsQuestFlags() throws Exception {
        var source=new Source();
        source.entries.add(new Entry() {
            public boolean visible() { return false; }
            public String id() { throw new AssertionError("hidden ID"); }
            public String title() { throw new AssertionError("hidden title"); }
            public int progress() { throw new AssertionError("hidden progress"); }
        });
        source.entries.add(new Entry() {
            public boolean startable() { throw new AssertionError("chapter startability"); }
            public boolean detailsVisible() { throw new AssertionError("chapter details"); }
        });
        assertEquals(1,new GameQuestCatalog(()->0).page(new GameQuestCatalog.Query(null,0),source).getAsJsonArray("entries").size());
    }
    @Test void pagesSortAndRevisionsChangeWithSourceFocusVisibilityAndProgress() throws Exception {
        var source=new Source();
        for(int i=69;i>=0;i--) { var entry=new Entry();entry.id=String.format("%016X",i+1);source.entries.add(entry); }
        var catalog=new GameQuestCatalog(()->0);var query=new GameQuestCatalog.Query(null,0);
        var first=catalog.page(query,source);long rev=first.get("revision").getAsLong();
        assertEquals(32,first.getAsJsonArray("entries").size());assertEquals(32,first.get("next_cursor").getAsInt());
        assertEquals(rev,catalog.page(new GameQuestCatalog.Query(null,32),source).get("revision").getAsLong());
        source.generation++;assertEquals(++rev,catalog.page(query,source).get("revision").getAsLong());
        ((Entry)source.entries.get(0)).progress=10;assertEquals(++rev,catalog.page(query,source).get("revision").getAsLong());
        ((Entry)source.entries.get(0)).visible=false;assertEquals(++rev,catalog.page(query,source).get("revision").getAsLong());
        assertEquals(++rev,catalog.page(new GameQuestCatalog.Query(CHAPTER,0),source).get("revision").getAsLong());
    }
    @Test void invalidStatesAndAmbiguousIdsRejectWholePage() throws Exception {
        for(int test=0;test<8;test++) {
            var source=new Source();var entry=new Entry();source.entries.add(entry);
            switch(test) {
                case 0 -> entry.progress=-1;case 1 -> entry.progress=101;case 2 -> entry.completed=true;
                case 3 -> entry.id="private-id";case 4 -> entry.title="x".repeat(1025);
                case 5 -> entry.title="\ud800";case 6 -> source.entries.add(entry);case 7 -> entry.startable=true;
            }
            assertThrows(IOException.class,()->new GameQuestCatalog(()->0).page(new GameQuestCatalog.Query(CHAPTER,0),source));
        }
    }
    @Test void byteBoundHandlesAstralTitlesAndAdvancesWithoutCuttingText() throws Exception {
        var source=new Source();
        for(int i=0;i<32;i++) { var entry=new Entry();entry.id=String.format("%016X",i+1);entry.title="\ud83d\ude00".repeat(1024);source.entries.add(entry); }
        var page=new GameQuestCatalog(()->0).page(new GameQuestCatalog.Query(null,0),source);
        assertTrue(page.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8).length<=32768);
        assertTrue(page.getAsJsonArray("entries").size()<32);
        assertEquals(page.getAsJsonArray("entries").size(),page.get("next_cursor").getAsInt());
    }
    @Test void changedUnavailableOversizeAndTimedOutSourcesReturnNoPartialPage() throws Exception {
        var changed=new Source() {
            public Iterable<? extends GameQuestCatalog.Entry> entries(GameQuestCatalog.Query query) { generation++;return entries; }
        };
        var query=new GameQuestCatalog.Query(null,0);
        assertEquals("GAME_QUEST_CHANGED",assertThrows(IOException.class,()->new GameQuestCatalog(()->0).page(query,changed)).getMessage());
        changed.generation=-1;
        assertEquals("GAME_QUEST_SOURCE_UNAVAILABLE",assertThrows(IOException.class,()->new GameQuestCatalog(()->0).page(query,changed)).getMessage());
        var source=new Source();for(int i=0;i<4097;i++) { var entry=new Entry();entry.visible=false;source.entries.add(entry); }
        assertEquals("GAME_QUEST_BOUNDS",assertThrows(IOException.class,()->new GameQuestCatalog(()->0).page(query,source)).getMessage());
        long[] clock={0};assertEquals("GAME_QUEST_TIMEOUT",assertThrows(IOException.class,
            ()->new GameQuestCatalog(()->clock[0]+=GameQuestCatalog.MAX_NANOS+1).page(query,new Source())).getMessage());
    }
    @Test void queryFieldsIdsAndCursorsAreStrictAndArtifactMismatchesReject() throws Exception {
        var query=new GameQuestCatalog.Query(null,0);assertEquals(query,GameQuestCatalog.Query.read(query.json()));
        for(String field:List.of("source","chapter_id","after")) {
            var value=query.json();value.addProperty(field,"unknown");assertThrows(IOException.class,()->GameQuestCatalog.Query.read(value));
        }
        var value=query.json();value.addProperty("team_id","sibling");assertThrows(IOException.class,()->GameQuestCatalog.Query.read(value));
        for(int after:new int[]{-1,4097}) assertThrows(IllegalArgumentException.class,()->new GameQuestCatalog.Query(null,after));
        assertThrows(IOException.class,()->new GameQuestCatalog(()->0).page(new GameQuestCatalog.Query(null,1),new Source()));
        GameQuestCatalog.requireArtifacts(GameQuestCatalog.ARTIFACTS);
        for(String key:GameQuestCatalog.ARTIFACTS.keySet()) {
            var artifacts=new java.util.HashMap<>(GameQuestCatalog.ARTIFACTS);artifacts.remove(key);
            assertThrows(IOException.class,()->GameQuestCatalog.requireArtifacts(artifacts));
            artifacts.put(key,"0".repeat(64));assertThrows(IOException.class,()->GameQuestCatalog.requireArtifacts(artifacts));
        }
    }
}
