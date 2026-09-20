package io.github.opencnid.strata.client;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import java.io.IOException;
import java.nio.file.Path;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import static org.junit.jupiter.api.Assertions.*;

/** Real projection/motor/journal with synthetic book, visibility and native callbacks. */
class GameQuestNavigationTest {
    static final String CHAPTER="0000000000000001",QUEST="0000000000000002";
    static final class Port implements GameQuestNavigation.Port {
        final GameQuestOpenTest.Port open;final GameQuestScreen tracker=new GameQuestScreen(()->0);
        String chapter,quest;int inputs;boolean forbidden,hidden,refuse,failAfter,mutateSelection;
        String layout="layout";
        Port(){this(new GameQuestOpenTest.Port());open.screen=new Object();open.questScreen=true;}
        Port(GameQuestOpenTest.Port open){this.open=open;}
        public GameQuestScreen.Snapshot read()throws IOException {
            if(forbidden)throw new IOException("TARGET_NOT_OBSERVED");
            return tracker.capture(() -> new GameQuestScreen.Frame(open.generation,open.screen,
                chapter==null?null:chapter.intern(),quest==null?null:quest.intern(),chapter,quest,KeyOptions.sha256(layout)));
        }
        public void selection(GameQuestNavigation.Request request)throws IOException {
            if(request.selection()!=null) {
                var source=GameQuestCatalogTest.fixture(request.selection().query());
                if(hidden)((GameQuestCatalogTest.Entry)source.entries.get(0)).visible=false;
                request.selection().visible(new GameQuestCatalog(()->0).page(request.selection().query(),source),open.generation,request.operation());
            }
            if(mutateSelection)layout="changed";
        }
        public void navigate(GameQuestNavigation.Request request)throws IOException {
            inputs++;if(refuse)return;
            switch(request.operation()) {
                case "chapter" -> {if(!request.selection().id().equals(chapter))quest=null;chapter=request.selection().id();}
                case "quest" -> {chapter=request.selection().query().chapter();quest=request.selection().id();}
                case "back" -> {if(quest!=null)quest=null;else {open.screen=null;open.questScreen=false;chapter=null;}}
                case "close" -> {open.screen=null;open.questScreen=false;chapter=null;quest=null;}
                default -> throw new IOException("MECHANIC_UNSUPPORTED");
            }
            if(failAfter)throw new IOException("INJECTED_AFTER_NAVIGATION");
        }
    }
    static JsonObject action(GameQuestNavigation.Port port,String operation)throws IOException {
        var state=port.read();var value=new JsonObject();value.addProperty("kind","quest_navigate");value.addProperty("operation",operation);
        value.addProperty("source","ftb_quests");value.addProperty("source_generation",state.frame().source());
        value.addProperty("expected_screen_generation",state.generation());value.addProperty("expected_screen_revision",state.revision());
        value.add("selection",com.google.gson.JsonNull.INSTANCE);
        if(operation.equals("chapter") || operation.equals("quest")) {
            var selection=new JsonObject();selection.add("query",new GameQuestCatalog.Query(operation.equals("quest")?CHAPTER:null,0).json());
            selection.addProperty("revision",1);selection.addProperty("entry_id",operation.equals("quest")?QUEST:CHAPTER);value.add("selection",selection);
        }
        return value;
    }
    static GameQuestNavigation.Request request(GameQuestNavigation.Port port,String operation)throws IOException {return GameQuestNavigation.Request.read(action(port,operation));}
    static void run(GameQuestNavigation.Port port,String operation)throws IOException {
        var motor=GameQuestNavigation.start(port,request(port,operation),GameActionLane.Operation::run);
        assertTrue(motor.tick(op -> fail("confirmation cannot emit")));
    }
    @Test void catalogChapterQuestBackThenBackReturnsToGameplay()throws Exception {
        var p=new Port();run(p,"chapter");assertEquals(CHAPTER,p.chapter);assertNull(p.quest);
        run(p,"quest");assertEquals(QUEST,p.quest);run(p,"back");assertNull(p.quest);assertNotNull(p.open.screen);
        run(p,"back");assertNull(p.open.screen);assertEquals("closed",p.read().json().get("kind").getAsString());assertEquals(4,p.inputs);
    }
    @Test void closeFromDetailsAndSameChapterSelectionPreserveOrdinarySemantics()throws Exception {
        var p=new Port();run(p,"quest");run(p,"chapter");assertEquals(QUEST,p.quest);
        run(p,"close");assertNull(p.open.screen);assertNull(p.quest);assertEquals(3,p.inputs);
    }
    @Test void screenProjectionHasStableReadsAndFencesReplacementAndSourceChange()throws Exception {
        var p=new Port();var a=p.read();assertEquals(a.json(),p.read().json());
        p.layout="resize";var b=p.read();assertEquals(a.generation(),b.generation());assertTrue(b.revision()>a.revision());
        p.open.screen=new Object();var c=p.read();assertTrue(c.generation()>b.generation());
        p.open.generation++;assertTrue(p.read().generation()>c.generation());
        assertEquals(java.util.Set.of("policy","source_generation","screen_generation","revision","kind","chapter_id","quest_id"),p.read().json().keySet());
    }
    @Test void invalidPrivateFramesChangedCapturesAndTimeLimitsDoNotPublish()throws Exception {
        Object screen=new Object(),chapter=new Object();
        var good=new GameQuestScreen.Frame(1,screen,chapter,null,CHAPTER,null,KeyOptions.sha256("private-layout"));
        for(var bad:java.util.List.of(
            new GameQuestScreen.Frame(-1,screen,null,null,null,null,good.context()),
            new GameQuestScreen.Frame(1,null,chapter,null,CHAPTER,null,good.context()),
            new GameQuestScreen.Frame(1,screen,null,chapter,null,QUEST,good.context()),
            new GameQuestScreen.Frame(1,screen,chapter,null,"private-canary",null,good.context())))
            assertThrows(IOException.class,() -> new GameQuestScreen().capture(()->bad));
        int[] reads={0};assertThrows(IOException.class,() -> new GameQuestScreen().capture(()->++reads[0]==1?good:
            new GameQuestScreen.Frame(1,new Object(),chapter,null,CHAPTER,null,good.context())));
        long[] clock={0};assertThrows(IOException.class,() -> new GameQuestScreen(()->clock[0]+=100_000_001L).capture(()->good));
    }
    @Test void staleUiOrCatalogHiddenTargetAndPermissionPreventEmission()throws Exception {
        for(int fault=0;fault<7;fault++) {
            var p=new Port();var a=action(p,"quest");
            if(fault==0)p.layout="resize";if(fault==1)p.open.screen=new Object();if(fault==2)p.open.generation++;
            if(fault==3)p.hidden=true;if(fault==4)p.forbidden=true;
            if(fault==5)a.getAsJsonObject("selection").addProperty("revision",2);
            if(fault==6)a.getAsJsonObject("selection").addProperty("entry_id","00000000000000FF");
            assertThrows(IOException.class,() -> GameQuestNavigation.start(p,GameQuestNavigation.Request.read(a),op -> fail("no emission")));
            assertEquals(0,p.inputs);
        }
    }
    @Test void selectionCannotRaceScreenStateAndDispatchRechecksIt()throws Exception {
        var p=new Port();var r=request(p,"quest");p.mutateSelection=true;
        assertThrows(IOException.class,() -> GameQuestNavigation.start(p,r,op -> fail("no emission")));assertEquals(0,p.inputs);
        var stable=new Port();var q=request(stable,"quest");
        assertThrows(IOException.class,() -> GameQuestNavigation.start(stable,q,op -> {stable.layout="race";op.run();}));assertEquals(0,stable.inputs);
    }
    @Test void refusesUnconfirmedAndLaterChangedScreenWithoutRetry()throws Exception {
        var p=new Port();p.refuse=true;
        assertThrows(IOException.class,() -> GameQuestNavigation.start(p,request(p,"close"),GameActionLane.Operation::run));assertEquals(1,p.inputs);
        var q=new Port();var motor=GameQuestNavigation.start(q,request(q,"quest"),GameActionLane.Operation::run);q.open.screen=new Object();
        assertThrows(IOException.class,() -> motor.tick(op -> fail("no retry")));assertEquals(1,q.inputs);
    }
    @Test void selectionRequiresPermittedPageAndDetailAccess()throws Exception {
        var query=new GameQuestCatalog.Query(CHAPTER,0);var source=GameQuestCatalogTest.fixture(query);
        var page=new GameQuestCatalog().page(query,source);var selection=new GameQuestNavigation.Selection(query,1,QUEST);
        selection.visible(page,1,"quest");page.getAsJsonArray("entries").get(0).getAsJsonObject().addProperty("details_visible",false);
        assertThrows(IOException.class,()->selection.visible(page,1,"quest"));
        var after=new GameQuestCatalog.Query(CHAPTER,1);var empty=new GameQuestCatalog().page(after,source);
        assertThrows(IOException.class,()->new GameQuestNavigation.Selection(after,1,QUEST).visible(empty,1,"quest"));
    }
    @Test void switchingCatalogFocusRequiresRefreshingSelectionBeforeNavigation()throws Exception {
        var book=new Port();var catalog=new GameQuestCatalog(()->0);
        GameQuestNavigation.Port port=new GameQuestNavigation.Port() {
            public GameQuestScreen.Snapshot read()throws IOException {return book.read();}
            public void selection(GameQuestNavigation.Request request)throws IOException {
                var selected=request.selection();
                selected.visible(catalog.page(selected.query(),GameQuestCatalogTest.fixture(selected.query())),
                    book.open.generation,request.operation());
            }
            public void navigate(GameQuestNavigation.Request request)throws IOException {book.navigate(request);}
        };
        var root=new GameQuestCatalog.Query(null,0);
        var rootPage=catalog.page(root,GameQuestCatalogTest.fixture(root));
        var stale=action(port,"chapter");
        stale.getAsJsonObject("selection").addProperty("revision",rootPage.get("revision").getAsLong());
        var quests=new GameQuestCatalog.Query(CHAPTER,0);
        catalog.page(quests,GameQuestCatalogTest.fixture(quests));
        var failure=assertThrows(IOException.class,()->GameQuestNavigation.start(port,
            GameQuestNavigation.Request.read(stale),operation->fail("stale selection cannot emit")));
        assertEquals("GAME_QUEST_CHANGED",failure.getMessage());assertEquals(0,book.inputs);
        var current=catalog.page(root,GameQuestCatalogTest.fixture(root));
        assertTrue(current.get("revision").getAsLong()>rootPage.get("revision").getAsLong());
        var fresh=action(port,"chapter");
        fresh.getAsJsonObject("selection").addProperty("revision",current.get("revision").getAsLong());
        var motor=GameQuestNavigation.start(port,GameQuestNavigation.Request.read(fresh),GameActionLane.Operation::run);
        assertTrue(motor.tick(operation->fail("confirmation cannot emit")));
        assertEquals(1,book.inputs);assertEquals(CHAPTER,book.chapter);
    }
    @Test void strictActionRejectsUnknownSelectorsOperationMismatchAndBounds(@TempDir Path root)throws Exception {
        var p=new Port();var f=new GameActionLaneTest.Fixture(root,100);
        for(String patch:new String[]{"{\"operation\":\"claim\"}","{\"operation\":\"back\"}","{\"selection\":null}",
            "{\"source\":\"admin\"}","{\"team_id\":\"private\"}","{\"expected_screen_revision\":true}","{\"expected_screen_generation\":-1}"}) {
            var value=action(p,"quest");JsonParser.parseString(patch).getAsJsonObject().entrySet().forEach(e->value.add(e.getKey(),e.getValue()));
            var b=f.batch(1,"nav",1);b.add("action",value);assertThrows(IOException.class,()->new GameBatch(b));
        }
        var wrong=action(p,"quest");wrong.getAsJsonObject("selection").getAsJsonObject("query").add("chapter_id",com.google.gson.JsonNull.INSTANCE);
        assertThrows(IOException.class,()->GameQuestNavigation.Request.read(wrong));
    }
    @Test void realLaneRetainsChargesEffectsAndDoesNotReplay(@TempDir Path root)throws Exception {
        var f=new GameActionLaneTest.Fixture(root,100);var p=new Port();var action=action(p,"quest");var request=GameQuestNavigation.Request.read(action);
        f.port.customMotor=emit->GameQuestNavigation.start(p,request,emit);var b=f.batch(1,"nav",1);b.add("action",action);
        try(var lane=f.open()) {
            f.arm(lane,1);f.deliver(lane);lane.accept(b);f.start(lane);lane.tick();
            assertEquals("emitted",lane.status("nav").get("status").getAsString());assertEquals(2,lane.status("nav").get("emitted_events").getAsInt());
            lane.accept(b);assertEquals(1,p.inputs);
        }
        try(var lane=f.open()) {assertEquals("emitted",lane.accept(b).get("status").getAsString());assertEquals(1,p.inputs);}
    }
    @Test void cancelBeforeAfterAndFailureAfterEffectPreserveUncertainty(@TempDir Path root)throws Exception {
        for(int mode=0;mode<3;mode++) {
            var f=new GameActionLaneTest.Fixture(java.nio.file.Files.createDirectory(root.resolve("case-"+mode)),100);var p=new Port();p.failAfter=mode==2;
            var a=action(p,"close");var request=GameQuestNavigation.Request.read(a);f.port.customMotor=e->GameQuestNavigation.start(p,request,e);
            try(var lane=f.open()) {
                f.arm(lane,1);f.deliver(lane);var b=f.batch(1,"nav",1);b.add("action",a);lane.accept(b);if(mode>0)f.start(lane);
                if(mode<2)lane.cancel("nav");var receipt=lane.status("nav");
                assertEquals(mode==2?"unknown":"cancelled",receipt.get("status").getAsString());assertTrue(lane.health().get("fenced").getAsBoolean());
                assertEquals(mode==0?0:1,p.inputs);assertEquals(mode==0,p.open.screen!=null);lane.accept(b);assertEquals(mode==0?0:1,p.inputs);
            }
        }
    }
}
