package io.github.opencnid.strata.client;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;

class GameQuestComponentsTest {
    static final class Entry implements GameQuestComponents.Entry {
        boolean visible=true,change=false,reward=false;String id="0000000000000003";
        GameQuestComponents.Display value;
        public boolean visible(){return visible;}
        public String id(){assertTrue(visible);return id;}
        public GameQuestComponents.Display display(){assertTrue(visible);if(change)visible=false;return value!=null ? value : displayValue(reward);}
    }
    static GameQuestComponents.Display displayValue(boolean reward) {
        return new GameQuestComponents.Display(reward ? "Visible reward" : "Visible task",
            List.of(new GameQuestText.Line("text","Ordinary tooltip")),
            reward ? null : new GameQuestComponents.Task(false,false,"2 / 4"),
            reward ? new GameQuestComponents.Reward("cannot_claim",false) : null);
    }
    static final class Quest extends GameQuestTextTest.Entry implements GameQuestComponents.Quest {
        List<Entry> entries=new ArrayList<>(List.of(new Entry()));
        public Iterable<? extends GameQuestComponents.Entry> components(String part){assertTrue(visible && details);return entries;}
        @Override public List<GameQuestText.Line> description(){throw new AssertionError("No description read by components");}
    }
    static GameQuestComponents.Query query(String part,int after){return new GameQuestComponents.Query(GameQuestTextTest.CHAPTER,GameQuestTextTest.QUEST,part,after);}
    static GameQuestCatalog.Source fixtureSource(String part){var quest=new Quest();quest.entries.get(0).reward=part.equals("rewards");return GameQuestTextTest.source(quest);}
    @Test void tasksAndRewardsHaveSeparateOwnStatusWithoutRawDefinitions()throws Exception {
        for(String part:List.of("tasks","rewards")) {
            var page=new GameQuestComponents().page(query(part,0),fixtureSource(part));var row=page.getAsJsonArray("entries").get(0).getAsJsonObject();
            assertEquals(part.equals("tasks") ? "task" : "reward",row.get("kind").getAsString());
            assertEquals(6,row.size());assertTrue(row.get(part.equals("tasks") ? "reward" : "task").isJsonNull());
            assertFalse(page.toString().contains("team_id"));assertFalse(page.toString().contains("command"));
        }
    }
    @Test void hiddenParentAndRewardsNeverReadIdentifiersOrDefinitions()throws Exception {
        var quest=new Quest();quest.visible=false;var projector=new GameQuestComponents();
        assertThrows(IOException.class,()->projector.page(query("rewards",0),GameQuestTextTest.source(quest)));
        quest.visible=true;quest.details=false;
        assertThrows(IOException.class,()->projector.page(query("rewards",0),GameQuestTextTest.source(quest)));
        quest.details=true;quest.entries.get(0).visible=false;
        assertEquals(0,projector.page(query("rewards",0),GameQuestTextTest.source(quest)).getAsJsonArray("entries").size());
    }
    @Test void sortedPagesAndContentRevisionsAreBounded()throws Exception {
        var quest=new Quest();quest.entries.clear();for(int i=40;i>0;i--){var row=new Entry();row.id=String.format("%016X",i);quest.entries.add(row);}
        var projector=new GameQuestComponents();var first=projector.page(query("tasks",0),GameQuestTextTest.source(quest));
        var second=projector.page(query("tasks",32),GameQuestTextTest.source(quest));
        assertEquals(32,first.get("next_cursor").getAsInt());assertEquals(8,second.getAsJsonArray("entries").size());
        assertEquals(first.get("revision"),second.get("revision"));
        quest.entries.get(0).visible=false;assertNotEquals(first.get("revision"),projector.page(query("tasks",0),GameQuestTextTest.source(quest)).get("revision"));
        quest.entries.add(quest.entries.get(1));assertThrows(IOException.class,()->projector.page(query("tasks",0),GameQuestTextTest.source(quest)));
    }
    @Test void displayKindRichPayloadAndClaimStateReject()throws Exception {
        var quest=new Quest();var entry=quest.entries.get(0);var projector=new GameQuestComponents();
        for(var invalid:List.of(displayValue(true),
            new GameQuestComponents.Display("x",List.of(new GameQuestText.Line("unsupported","private data")),new GameQuestComponents.Task(false,false,null),null),
            new GameQuestComponents.Display("x",List.of(new GameQuestText.Line("page_break",null)),new GameQuestComponents.Task(false,false,null),null),
            new GameQuestComponents.Display("x",List.of(),new GameQuestComponents.Task(false,false,"x".repeat(257)),null))) {
            entry.value=invalid;assertThrows(IOException.class,()->projector.page(query("tasks",0),GameQuestTextTest.source(quest)));
        }
        entry.value=new GameQuestComponents.Display("x",List.of(),null,new GameQuestComponents.Reward("admin_complete",false));
        assertThrows(IOException.class,()->projector.page(query("rewards",0),GameQuestTextTest.source(quest)));
    }
    @Test void entryPageAndCandidateLimitsNeverReturnPartialOverflow()throws Exception {
        var quest=new Quest();var entry=quest.entries.get(0);var projector=new GameQuestComponents();
        entry.value=new GameQuestComponents.Display("x",java.util.Collections.nCopies(65,new GameQuestText.Line("text","x")),new GameQuestComponents.Task(false,false,null),null);
        assertThrows(IOException.class,()->projector.page(query("tasks",0),GameQuestTextTest.source(quest)));
        entry.value=new GameQuestComponents.Display("x",List.of(new GameQuestText.Line("text","\uD83D\uDE00".repeat(4096))),new GameQuestComponents.Task(false,false,null),null);
        assertThrows(IOException.class,()->projector.page(query("tasks",0),GameQuestTextTest.source(quest)));
        entry.value=new GameQuestComponents.Display("x",List.of(new GameQuestText.Line("text","\uD83D\uDE00".repeat(2000))),new GameQuestComponents.Task(false,false,null),null);
        for(int i=4;i<12;i++){var another=new Entry();another.id=String.format("%016X",i);another.value=entry.value;quest.entries.add(another);}
        var page=projector.page(query("tasks",0),GameQuestTextTest.source(quest));assertTrue(page.get("next_cursor").getAsInt()<9);
        assertTrue(page.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8).length<=32768);
        entry.visible=false;quest.entries=java.util.Collections.nCopies(513,entry);
        assertThrows(IOException.class,()->projector.page(query("tasks",0),GameQuestTextTest.source(quest)));
    }
    @Test void changedSourceVisibilityAndTimeoutFailClosed()throws Exception {
        var quest=new Quest();quest.entries.get(0).change=true;
        assertThrows(IOException.class,()->new GameQuestComponents().page(query("tasks",0),GameQuestTextTest.source(quest)));
        quest.entries.get(0).change=false;quest.entries.get(0).visible=true;
        var source=new GameQuestCatalog.Source(){int n;public long generation(){return ++n;}
            public Iterable<? extends GameQuestCatalog.Entry> entries(GameQuestCatalog.Query ignored){return List.of(quest);}};
        assertThrows(IOException.class,()->new GameQuestComponents().page(query("tasks",0),source));
        long[] clock={0};assertThrows(IOException.class,()->new GameQuestComponents(()->clock[0]+=100_000_001L).page(query("tasks",0),GameQuestTextTest.source(quest)));
    }
    static final class Progress implements GameQuestComponents.Progress {
        boolean start=true,hidden=false;long max=10,current=2;int percent=20,formatted=0;
        public boolean startable(){return start;}public long maximum(){assertTrue(start);return max;}
        public long current(){assertTrue(start);return current;}public boolean hiddenNumbers(){return hidden;}
        public int percent(){return percent;}public String maximumLabel(){assertFalse(hidden);formatted++;return "ten";}
        public String currentLabel(long value){assertFalse(hidden);formatted++;return "two";}
    }
    @Test void progressMatchesNormalFormattingWithoutHiddenExactNumbers()throws Exception {
        var p=new Progress();assertEquals("two / ten",GameQuestComponents.progressLabel(p));
        p.max=100;assertEquals("two / ten [20%]",GameQuestComponents.progressLabel(p));
        p.hidden=true;p.formatted=0;assertEquals("[20%]",GameQuestComponents.progressLabel(p));assertEquals(0,p.formatted);
        p.start=false;assertNull(GameQuestComponents.progressLabel(p));p.start=true;p.max=1;assertNull(GameQuestComponents.progressLabel(p));
        p.max=10;p.hidden=false;p.current=20;assertEquals("ten / ten",GameQuestComponents.progressLabel(p));
        p.current=-1;assertThrows(IOException.class,()->GameQuestComponents.progressLabel(p));
        p.current=2;p.hidden=true;p.percent=101;assertThrows(IOException.class,()->GameQuestComponents.progressLabel(p));
    }
    @Test void exactQueryDiscriminantsAndCursorsReject()throws Exception {
        var value=query("tasks",0).json();assertEquals(query("tasks",0),GameQuestComponents.Query.read(value));
        value.addProperty("team_id","sibling");assertThrows(IOException.class,()->GameQuestComponents.Query.read(value));
        assertThrows(IllegalArgumentException.class,()->query("server_commands",0));assertThrows(IllegalArgumentException.class,()->query("tasks",513));
        assertThrows(IllegalArgumentException.class,()->new GameQuestComponents.Query(GameQuestTextTest.CHAPTER,GameQuestTextTest.QUEST+"\n","tasks",0));
    }
}
