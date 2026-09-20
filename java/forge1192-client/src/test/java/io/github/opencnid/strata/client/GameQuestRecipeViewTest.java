package io.github.opencnid.strata.client;

import static org.junit.jupiter.api.Assertions.*;
import com.google.gson.JsonObject;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

/** Real provenance/projection/open/close/lane, synthetic XMod/JEI/native screen authority. */
class GameQuestRecipeViewTest {
    static final class Port implements GameQuestTaskOpen.Port,GameQuestNavigation.Port {
        final GameQuestTaskOpenTest.Port opening;final GameQuestRecipeView.Bindings bindings=new GameQuestRecipeView.Bindings();
        GameQuestRecipeView.Binding binding;GameQuestScreen.Frame parent;Object runtime=new Object();
        boolean available=true,refuseClose,failAfterClose;String layout="recipe-layout";int closes;
        Port(){this(new GameQuestTaskOpenTest.Port());}
        Port(GameQuestTaskOpenTest.Port opening){this.opening=opening;}
        private void valid()throws IOException {if(!available)throw new IOException("GAME_QUEST_RECIPE_SOURCE_UNAVAILABLE");}
        public GameQuestScreen.Snapshot book()throws IOException {valid();return opening.book();}
        public GameQuestTaskOpen.Target selection(GameQuestTaskOpen.Request request)throws IOException {valid();return opening.selection(request);}
        public Object open(GameQuestTaskOpen.Target target)throws IOException {
            valid();parent=book().frame();return opening.open(target);
        }
        public void confirm(GameQuestTaskOpen.Request request,GameQuestTaskOpen.Target target,Object book,Object menu)throws IOException {
            valid();opening.confirm(request,target,book,menu);Object captured=runtime;
            var next=new GameQuestRecipeView.Binding(menu,parent,target.task(),runtime,()->{
                valid();if(runtime!=captured || opening.navigation.open.generation!=parent.source())throw new IOException("GAME_QUEST_CHANGED");
            });
            bindings.bind(next);binding=next;
        }
        public GameQuestScreen.Snapshot read()throws IOException {
            valid();if(opening.menu==null)return opening.navigation.read();
            var current=bindings.current(opening.navigation.open.screen);
            return opening.navigation.tracker.capture(()->GameQuestRecipeView.frame(current,parent,KeyOptions.sha256(layout)));
        }
        public void selection(GameQuestNavigation.Request request)throws IOException {
            valid();if(!request.operation().equals("close") || opening.menu==null)throw new IOException("GAME_QUEST_RECIPE_NAVIGATION_UNSUPPORTED");
        }
        public void navigate(GameQuestNavigation.Request request)throws IOException {
            selection(request);closes++;if(refuseClose)return;
            opening.navigation.open.screen=parent.screen();opening.menu=null;bindings.clear();
            if(failAfterClose)throw new IOException("INJECTED_AFTER_CLOSE");
        }
        public void confirmRecipeClose(GameQuestScreen.Snapshot before)throws IOException {
            if(before.frame().screen()!=binding.screen())throw new IOException("GAME_QUEST_CHANGED");
            GameQuestRecipeView.confirmReturn(binding,read().frame());
        }
        void openRecipe()throws IOException {
            var motor=GameQuestTaskOpen.start(this,GameQuestTaskOpen.Request.read(GameQuestTaskOpenTest.action(this)),GameActionLane.Operation::run);
            assertTrue(motor.tick(op->fail("No further opening input")));
        }
    }
    @Test void exactPinsRequireAllFiveArtifacts()throws Exception {
        var pins=new java.util.HashMap<>(GameQuestCatalog.ARTIFACTS);pins.putAll(GameQuestRecipeView.ARTIFACTS);
        GameQuestRecipeView.requireArtifacts(pins);
        for(var key:pins.keySet()) {
            var missing=new java.util.HashMap<>(pins);missing.remove(key);
            assertThrows(IOException.class,()->GameQuestRecipeView.requireArtifacts(missing));
            missing.put(key,"0".repeat(64));assertThrows(IOException.class,()->GameQuestRecipeView.requireArtifacts(missing));
        }
    }
    @Test void opensDistinctRecipeStateAndClosesToExactOriginWithoutPrivateContents()throws Exception {
        var p=new Port();Object book=p.book().frame().screen();p.openRecipe();var read=p.read();
        assertEquals("task_recipes",read.json().get("kind").getAsString());
        assertEquals(GameQuestNavigationTest.QUEST,read.json().get("quest_id").getAsString());
        assertEquals(java.util.Set.of("policy","source_generation","screen_generation","revision","kind","chapter_id","quest_id"),read.json().keySet());
        assertEquals(read.json(),p.read().json());
        GameQuestNavigationTest.run(p,"close");assertSame(book,p.read().frame().screen());assertEquals("quest_book",p.read().frame().kind());
        assertEquals(1,p.opening.inputs);assertEquals(1,p.closes);
    }
    @Test void historyBackChapterAndQuestAreNotRecipeClose()throws Exception {
        var p=new Port();p.openRecipe();
        for(String operation:new String[]{"back","quest","chapter"}) {
            var request=GameQuestNavigationTest.request(p,operation);
            assertEquals("GAME_QUEST_RECIPE_NAVIGATION_UNSUPPORTED",assertThrows(IOException.class,
                ()->GameQuestNavigation.start(p,request,op->fail("No input"))).getMessage());
        }
        assertEquals(0,p.closes);
    }
    @Test void runtimeSourceScreenAndLayoutChangesRejectOldClose()throws Exception {
        for(int mode=0;mode<4;mode++) {
            var p=new Port();p.openRecipe();var request=GameQuestNavigationTest.request(p,"close");
            switch(mode){case 0->p.runtime=new Object();case 1->p.opening.navigation.open.generation++;
                case 2->p.opening.navigation.open.screen=new Object();case 3->p.layout="resized";}
            assertThrows(IOException.class,()->GameQuestNavigation.start(p,request,op->fail("No input")));assertEquals(0,p.closes);
        }
    }
    @Test void ordinaryNoOpenAndUnavailableRuntimeCannotBecomeOpenedSuccess()throws Exception {
        var p=new Port();p.opening.refuse=true;var request=GameQuestTaskOpen.Request.read(GameQuestTaskOpenTest.action(p));
        assertEquals("GAME_QUEST_TASK_OPEN_UNCONFIRMED",assertThrows(IOException.class,
            ()->GameQuestTaskOpen.start(p,request,GameActionLane.Operation::run)).getMessage());assertEquals(1,p.opening.inputs);
        var q=new Port();var second=GameQuestTaskOpen.Request.read(GameQuestTaskOpenTest.action(q));q.available=false;
        assertThrows(IOException.class,()->GameQuestTaskOpen.start(q,second,op->fail("No input")));assertEquals(0,q.opening.inputs);
    }
    @Test void bindCannotInventParentOrReplaceLiveOpeningAndExpiresOnChanges()throws Exception {
        var p=new Port();p.openRecipe();var b=p.binding;assertSame(b,p.bindings.current(b.screen()));
        assertThrows(IOException.class,()->p.bindings.bind(new GameQuestRecipeView.Binding(new Object(),b.parent(),b.task(),b.runtime(),b.validity())));
        assertThrows(IOException.class,()->p.bindings.bind(new GameQuestRecipeView.Binding(b.parent().screen(),b.parent(),b.task(),b.runtime(),b.validity())));
        p.bindings.tick(new Object());assertThrows(IOException.class,()->p.bindings.current(b.screen()));
        p.bindings.bind(b);p.available=false;p.bindings.tick(b.screen());p.available=true;
        assertThrows(IOException.class,()->p.bindings.current(b.screen()));
    }
    @Test void recipeFramesCannotMasqueradeAsBookOrLackOrigin()throws Exception {
        var p=new Port();p.openRecipe();var b=p.binding;
        for(String kind:new String[]{"closed","unknown"})assertThrows(IOException.class,
            ()->new GameQuestScreen.Frame(1,b.screen(),b.parent().chapterObject(),b.parent().questObject(),b.parent().chapter(),b.parent().quest(),b.parent().context(),kind).validate());
        assertThrows(IOException.class,()->new GameQuestScreen.Frame(1,b.screen(),null,null,null,null,b.parent().context(),"task_recipes").validate());
        var wrong=new GameQuestScreen.Frame(1,new Object(),b.parent().chapterObject(),b.parent().questObject(),b.parent().chapter(),b.parent().quest(),b.parent().context());
        assertThrows(IOException.class,()->GameQuestRecipeView.frame(b,wrong,KeyOptions.sha256("layout")));
        assertThrows(IOException.class,()->GameQuestRecipeView.confirmReturn(b,wrong));
        var noQuest=new GameQuestScreen.Frame(1,b.parent().screen(),b.parent().chapterObject(),null,b.parent().chapter(),null,b.parent().context());
        assertFalse(GameQuestRecipeView.sameOrigin(b.parent(),noQuest));
        assertThrows(IOException.class,()->GameQuestRecipeView.frame(b,noQuest,KeyOptions.sha256("layout")));
        GameQuestTaskOpen.Port impostor=new GameQuestTaskOpen.Port(){public GameQuestScreen.Snapshot book()throws IOException{return p.read();}
            public GameQuestTaskOpen.Target selection(GameQuestTaskOpen.Request r){throw new AssertionError("Not a book");}
            public Object open(GameQuestTaskOpen.Target t){throw new AssertionError("No input");}
            public void confirm(GameQuestTaskOpen.Request r,GameQuestTaskOpen.Target t,Object book,Object menu){throw new AssertionError();}};
        var request=GameQuestTaskOpen.Request.read(GameQuestTaskOpenTest.action(impostor));
        assertThrows(IOException.class,()->GameQuestTaskOpen.start(impostor,request,op->fail("No input")));
    }
    @Test void refusedOrWrongParentAndNextTickChangesNeverReplay()throws Exception {
        var p=new Port();p.openRecipe();p.refuseClose=true;
        assertThrows(IOException.class,()->GameQuestNavigationTest.run(p,"close"));assertEquals(1,p.closes);
        var q=new Port();q.openRecipe();var r=GameQuestNavigationTest.request(q,"close");
        var motor=GameQuestNavigation.start(q,r,GameActionLane.Operation::run);q.opening.navigation.quest=null;
        assertThrows(IOException.class,()->motor.tick(op->fail("No replay")));assertEquals(1,q.closes);
    }
    @Test void durableCloseChargesAndDeduplicatesAcrossReopen(@TempDir Path root)throws Exception {
        var f=new GameActionLaneTest.Fixture(root,100);var p=new Port();p.openRecipe();
        var a=GameQuestNavigationTest.action(p,"close");var r=GameQuestNavigation.Request.read(a);
        f.port.customMotor=e->GameQuestNavigation.start(p,r,e);var batch=f.batch(1,"recipe-close",1);batch.add("action",a);
        try(var lane=f.open()) {
            f.arm(lane,1);f.deliver(lane);lane.accept(batch);f.start(lane);lane.tick();
            assertEquals("emitted",lane.status("recipe-close").get("status").getAsString());
            assertEquals(2,lane.status("recipe-close").get("emitted_events").getAsInt());lane.accept(batch);assertEquals(1,p.closes);
        }
        try(var lane=f.open()){assertEquals("emitted",lane.accept(batch).get("status").getAsString());assertEquals(1,p.closes);}
    }
    @Test void cancelledAndUncertainClosePreserveParentStateAndAllAttemptedCosts(@TempDir Path root)throws Exception {
        for(int mode=0;mode<3;mode++) {
            var f=new GameActionLaneTest.Fixture(Files.createDirectory(root.resolve("case-"+mode)),100);var p=new Port();p.openRecipe();p.failAfterClose=mode==2;
            var a=GameQuestNavigationTest.action(p,"close");var r=GameQuestNavigation.Request.read(a);f.port.customMotor=e->GameQuestNavigation.start(p,r,e);
            try(var lane=f.open()) {
                f.arm(lane,1);f.deliver(lane);var b=f.batch(1,"recipe-close",1);b.add("action",a);lane.accept(b);
                if(mode>0)f.start(lane);if(mode<2)lane.cancel("recipe-close");var status=lane.status("recipe-close");
                assertEquals(mode==2?"unknown":"cancelled",status.get("status").getAsString());
                assertEquals(mode==0?1:2,status.get("attempted_events").getAsInt());
                if(mode==2)assertTrue(status.get("emitted_events").isJsonNull());else assertEquals(mode==0?1:2,status.get("emitted_events").getAsInt());
                assertTrue(lane.health().get("fenced").getAsBoolean());assertEquals(mode==0?"task_recipes":"quest_book",p.read().frame().kind());
                lane.accept(b);assertEquals(mode==0?0:1,p.closes);
            }
        }
    }
}
