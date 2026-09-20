package io.github.opencnid.strata.client;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;

class GameQuestTextTest {
    static final String CHAPTER="0000000000000001",QUEST="0000000000000002";
    static class Entry implements GameQuestText.Entry {
        boolean visible=true,details=true,text=true;int reads=0;
        String id=QUEST,title="Visible quest",subtitle="Ordinary subtitle";
        List<GameQuestText.Line> lines=new ArrayList<>(List.of(new GameQuestText.Line("text","Visible description")));
        public boolean visible() {return visible;}
        public String id() {assertTrue(visible);return id;}
        public String title() {assertTrue(visible && details);return title;}
        public int progress() {throw new AssertionError("Text does not need progress");}
        public boolean completed() {throw new AssertionError("Source decides text visibility");}
        public boolean startable() {throw new AssertionError("Source decides details visibility");}
        public boolean detailsVisible() {return details;}
        public String subtitle() {assertTrue(visible && details);return subtitle;}
        public boolean textVisible() {return text;}
        public List<GameQuestText.Line> description() {assertTrue(visible && details && text);reads++;return lines;}
    }
    static GameQuestCatalog.Source source(Entry entry) {
        return new GameQuestCatalog.Source() {
            public long generation() {return 1;}
            public Iterable<? extends GameQuestCatalog.Entry> entries(GameQuestCatalog.Query query) throws IOException {
                if(!CHAPTER.equals(query.chapter())) throw new IOException("TARGET_NOT_OBSERVED");return List.of(entry);
            }
        };
    }
    static GameQuestCatalog.Source fixtureSource() {return source(new Entry());}
    static GameQuestText.Query query(int after) {return new GameQuestText.Query(CHAPTER,QUEST,after);}
    @Test void plainTextAndExplicitRichDispositionHaveNoRawFields() throws Exception {
        var entry=new Entry();entry.lines.add(new GameQuestText.Line("page_break",null));
        entry.lines.add(new GameQuestText.Line("unsupported",null));
        var page=new GameQuestText().page(query(0),source(entry));
        assertEquals("Visible description",page.getAsJsonArray("lines").get(0).getAsJsonObject().get("text").getAsString());
        assertEquals(3,page.getAsJsonArray("lines").size());assertEquals(1,entry.reads);
        assertFalse(page.toString().contains("team_id"));assertFalse(page.toString().contains("reward"));
    }
    @Test void HiddenQuestDetailsAndTextNeverInvokeForbiddenReaders() throws Exception {
        var entry=new Entry();entry.visible=false;
        assertThrows(IOException.class,()->new GameQuestText().page(query(0),source(entry)));
        entry.visible=true;entry.details=false;
        assertThrows(IOException.class,()->new GameQuestText().page(query(0),source(entry)));
        entry.details=true;entry.text=false;
        var page=new GameQuestText().page(query(0),source(entry));
        assertEquals("Ordinary subtitle",page.get("subtitle").getAsString());
        assertFalse(page.get("description_visible").getAsBoolean());assertEquals(0,page.getAsJsonArray("lines").size());
        assertEquals(0,entry.reads);assertThrows(IOException.class,()->new GameQuestText().page(query(1),source(entry)));
    }
    @Test void pagesAndRevisionsPreserveLineOrderAndSource() throws Exception {
        var entry=new Entry();entry.lines.clear();for(int i=0;i<40;i++) entry.lines.add(new GameQuestText.Line("text","line "+i));
        var text=new GameQuestText();var first=text.page(query(0),source(entry));var second=text.page(query(32),source(entry));
        assertEquals(32,first.get("next_cursor").getAsInt());assertEquals(8,second.getAsJsonArray("lines").size());
        assertEquals(first.get("revision"),second.get("revision"));assertEquals("line 32",second.getAsJsonArray("lines").get(0).getAsJsonObject().get("text").getAsString());
        entry.subtitle="Changed";assertNotEquals(first.get("revision"),text.page(query(0),source(entry)).get("revision"));
        var changed=new GameQuestCatalog.Source() {
            int calls=0;public long generation(){return ++calls;}
            public Iterable<? extends GameQuestCatalog.Entry> entries(GameQuestCatalog.Query ignored){return List.of(entry);}
        };
        assertThrows(IOException.class,()->text.page(query(0),changed));
    }
    @Test void invalidLinesBoundsAndUnicodeRejectWholeResponse() throws Exception {
        var entry=new Entry();var text=new GameQuestText();
        for(var bad:List.of(new GameQuestText.Line("raw",null),new GameQuestText.Line("text",null),
                new GameQuestText.Line("unsupported","hidden"),new GameQuestText.Line("text","\uD800"),
                new GameQuestText.Line("text","x".repeat(4097)))) {
            entry.lines=List.of(bad);assertThrows(IOException.class,()->text.page(query(0),source(entry)));
        }
        entry.lines=java.util.Collections.nCopies(513,new GameQuestText.Line("text","x"));
        assertThrows(IOException.class,()->text.page(query(0),source(entry)));
        entry.lines=java.util.Collections.nCopies(512,new GameQuestText.Line("text","x".repeat(4096)));
        assertThrows(IOException.class,()->text.page(query(0),source(entry)));
        entry.lines=List.of();entry.subtitle="x".repeat(1025);
        assertThrows(IOException.class,()->text.page(query(0),source(entry)));
    }
    @Test void utf8PageBudgetAndTimeoutAreBounded() throws Exception {
        var entry=new Entry();entry.lines=java.util.Collections.nCopies(8,new GameQuestText.Line("text","\uD83D\uDE00".repeat(4096)));
        var page=new GameQuestText().page(query(0),source(entry));
        assertEquals(1,page.getAsJsonArray("lines").size());assertEquals(1,page.get("next_cursor").getAsInt());
        assertTrue(page.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8).length<=32768);
        long[] ticks={0};assertThrows(IOException.class,()->new GameQuestText(()->ticks[0]+=100_000_001L).page(query(0),source(entry)));
    }
    @Test void strictQueriesAndAmbiguousSelectionReject() throws Exception {
        var value=query(0).json();assertEquals(query(0),GameQuestText.Query.read(value));value.addProperty("team_id","sibling");
        assertThrows(IOException.class,()->GameQuestText.Query.read(value));
        assertThrows(IllegalArgumentException.class,()->new GameQuestText.Query(CHAPTER,QUEST+"\n",0));
        assertThrows(IllegalArgumentException.class,()->query(513));
        var duplicate=new GameQuestCatalog.Source() {
            public long generation(){return 1;}
            public Iterable<? extends GameQuestCatalog.Entry> entries(GameQuestCatalog.Query ignored){return List.of(new Entry(),new Entry());}
        };
        assertThrows(IOException.class,()->new GameQuestText().page(query(0),duplicate));
    }
}
