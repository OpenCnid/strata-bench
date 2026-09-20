package io.github.opencnid.strata.client;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import java.io.IOException;
import java.nio.file.Path;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import static org.junit.jupiter.api.Assertions.*;

/** Real menu projection/motor/lane; native UI and wheel callback remain synthetic. */
class GameQuestMenuActionTest {
    static final class Port implements GameQuestMenuAction.Port {
        final GameQuestMenuTest.Source source=new GameQuestMenuTest.Source();final GameQuestMenu pages=new GameQuestMenu();
        final GameQuestTaskOpenTest.Port opening;Object parent=new Object(),task=new Object();
        String shape="shape";double y;int inputs;boolean closed,backEnabled=true,wheelEnabled=true,refuse,failAfter;
        Port(){this(null);}
        Port(GameQuestTaskOpenTest.Port opening){this.opening=opening;}
        JsonObject page(GameQuestMenu.Query query)throws IOException {
            if(opening!=null) {
                if(opening.menu==null)throw new IOException("GAME_QUEST_MENU_UNSUPPORTED");
                source.screen=opening.menu;source.generation=opening.navigation.open.generation;parent=opening.parent;task=opening.task;
            }
            if(closed)throw new IOException("GAME_QUEST_MENU_UNSUPPORTED");
            var back=new GameQuestMenuTest.Control();back.display=new GameQuestMenu.ControlDisplay("back","Back",backEnabled,java.util.List.of());
            source.controls=java.util.List.of(back,new GameQuestMenuTest.Control());source.layout=KeyOptions.sha256(shape+"/"+y);
            return pages.page(query,source);
        }
        public GameQuestMenuAction.State read()throws IOException {
            var p=page(new GameQuestMenu.Query(0));
            return new GameQuestMenuAction.State(source.generation,p.get("menu_generation").getAsLong(),p.get("revision").getAsLong(),
                source.screen,parent,task,KeyOptions.sha256(shape),new GameQuestMenuAction.Scroll(0,y,16,144,160,144,320),backEnabled,wheelEnabled);
        }
        public void back(GameQuestMenuAction.State before)throws IOException {
            inputs++;if(refuse)return;closed=true;
            if(opening!=null){opening.navigation.open.screen=parent;opening.menu=null;}
            if(failAfter)throw new IOException("INJECTED_AFTER_BACK");
        }
        public void wheel(GameQuestMenuAction.State before,String direction)throws IOException {
            inputs++;if(refuse)return;y=Math.max(0,Math.min(160,y+(direction.equals("up")?-16:16)));
            if(failAfter)throw new IOException("INJECTED_AFTER_SCROLL");
        }
        public void confirmBack(GameQuestMenuAction.State before)throws IOException {
            if(!closed || source.generation!=before.source() || parent!=before.parent())throw new IOException("GAME_QUEST_CHANGED");
        }
    }
    static JsonObject action(GameQuestMenuAction.Port port,String operation,String direction)throws IOException {
        var state=port.read();var value=new JsonObject();value.addProperty("kind","quest_menu");value.addProperty("operation",operation);
        value.addProperty("direction",direction);value.addProperty("source","ftb_quests");value.addProperty("source_generation",state.source());
        value.addProperty("expected_menu_generation",state.generation());value.addProperty("expected_menu_revision",state.revision());return value;
    }
    static void run(GameQuestMenuAction.Port port,String operation,String direction)throws IOException {
        var motor=GameQuestMenuAction.start(port,GameQuestMenuAction.Request.read(action(port,operation,direction)),GameActionLane.Operation::run);
        assertTrue(motor.tick(op->fail("confirmation does not emit")));
    }
    @Test void oneWheelStepClampsAndBackReturnsToParent()throws Exception {
        var p=new Port();run(p,"scroll","down");assertEquals(16,p.y);run(p,"scroll","up");assertEquals(0,p.y);
        run(p,"scroll","up");assertEquals(0,p.y);p.y=155;run(p,"scroll","down");assertEquals(160,p.y);
        run(p,"scroll","down");assertEquals(160,p.y);run(p,"back",null);assertTrue(p.closed);assertEquals(6,p.inputs);
    }
    @Test void scrollPredictionPreservesFractionalStepsAndRejectsInvalidBounds()throws Exception {
        var fractional=new GameQuestMenuAction.Scroll(0,15.5,16.25,144,160,144,320);
        assertEquals(31.75,fractional.nextY("down"));assertEquals(0,fractional.nextY("up"));
        assertEquals(0,new GameQuestMenuAction.Scroll(0,0,16,144,160,144,30).nextY("down"));
        for(double value:new double[]{Double.NaN,Double.POSITIVE_INFINITY,-1,161})
            assertThrows(IOException.class,()->new GameQuestMenuAction.Scroll(0,value,16,144,160,144,320).validate());
        assertThrows(IOException.class,()->new GameQuestMenuAction.Scroll(0,0,0,144,160,144,320).validate());
    }
    @Test void staleSourceScreenLayoutAndHiddenControlsPreventInput()throws Exception {
        for(int failure=0;failure<6;failure++) {
            var p=new Port();var a=action(p,"back",null);
            if(failure==0)p.source.generation++;if(failure==1)p.source.screen=new Object();if(failure==2)p.shape="resize";
            if(failure==3)p.backEnabled=false;if(failure==4)p.y=16;if(failure==5)p.source.available=false;
            assertThrows(IOException.class,()->GameQuestMenuAction.start(p,GameQuestMenuAction.Request.read(a),op->fail("no emission")));assertEquals(0,p.inputs);
        }
        var p=new Port();var a=action(p,"scroll","down");p.wheelEnabled=false;
        assertThrows(IOException.class,()->GameQuestMenuAction.start(p,GameQuestMenuAction.Request.read(a),op->fail("no emission")));
    }
    @Test void finalDispatchFencesReplacedParentTaskAndNativeShape()throws Exception {
        for(int mode=0;mode<3;mode++) {
            var p=new Port();var r=GameQuestMenuAction.Request.read(action(p,"scroll","down"));final int failure=mode;
            assertThrows(IOException.class,()->GameQuestMenuAction.start(p,r,op->{
                if(failure==0)p.parent=new Object();if(failure==1)p.task=new Object();if(failure==2)p.shape="changed";op.run();
            }));assertEquals(0,p.inputs);
        }
    }
    @Test void unconfirmedOrLaterChangedScrollNeverRetries()throws Exception {
        var p=new Port();p.refuse=true;var r=GameQuestMenuAction.Request.read(action(p,"scroll","down"));
        assertThrows(IOException.class,()->GameQuestMenuAction.start(p,r,GameActionLane.Operation::run));assertEquals(1,p.inputs);
        var q=new Port();var motor=GameQuestMenuAction.start(q,GameQuestMenuAction.Request.read(action(q,"scroll","down")),GameActionLane.Operation::run);
        q.y=32;assertThrows(IOException.class,()->motor.tick(op->fail("no replay")));assertEquals(1,q.inputs);
    }
    @Test void strictActionCannotSubmitOrInventScrollMagnitude(@TempDir Path root)throws Exception {
        var f=new GameActionLaneTest.Fixture(root,100);var p=new Port();
        for(String patch:new String[]{"{\"operation\":\"submit\"}","{\"direction\":null}","{\"direction\":1}","{\"direction\":\"left\"}",
                "{\"operation\":\"back\"}","{\"team_id\":\"private\"}","{\"expected_menu_revision\":true}","{\"expected_menu_generation\":-1}"}) {
            var a=action(p,"scroll","down");JsonParser.parseString(patch).getAsJsonObject().entrySet().forEach(e->a.add(e.getKey(),e.getValue()));
            var batch=f.batch(1,"menu",1);batch.add("action",a);assertThrows(IOException.class,()->new GameBatch(batch));
        }
    }
    @Test void durableLaneDeduplicatesScrollAndReopen(@TempDir Path root)throws Exception {
        var f=new GameActionLaneTest.Fixture(root,100);var p=new Port();var a=action(p,"scroll","down");var r=GameQuestMenuAction.Request.read(a);
        f.port.customMotor=e->GameQuestMenuAction.start(p,r,e);var batch=f.batch(1,"menu",1);batch.add("action",a);
        try(var lane=f.open()) {
            f.arm(lane,1);f.deliver(lane);lane.accept(batch);f.start(lane);lane.tick();
            assertEquals("emitted",lane.status("menu").get("status").getAsString());assertEquals(2,lane.status("menu").get("emitted_events").getAsInt());
            lane.accept(batch);assertEquals(16,p.y);assertEquals(1,p.inputs);
        }
        try(var lane=f.open()){assertEquals("emitted",lane.accept(batch).get("status").getAsString());assertEquals(1,p.inputs);}
    }
    @Test void cancellationAndFailurePreservePartialScrollAndCharge(@TempDir Path root)throws Exception {
        for(int mode=0;mode<3;mode++) {
            var f=new GameActionLaneTest.Fixture(java.nio.file.Files.createDirectory(root.resolve("case-"+mode)),100);var p=new Port();p.failAfter=mode==2;
            var a=action(p,"scroll","down");var r=GameQuestMenuAction.Request.read(a);f.port.customMotor=e->GameQuestMenuAction.start(p,r,e);
            try(var lane=f.open()) {
                f.arm(lane,1);f.deliver(lane);var b=f.batch(1,"menu",1);b.add("action",a);lane.accept(b);if(mode>0)f.start(lane);if(mode<2)lane.cancel("menu");
                assertEquals(mode==2?"unknown":"cancelled",lane.status("menu").get("status").getAsString());
                assertTrue(lane.health().get("fenced").getAsBoolean());assertEquals(mode==0?0:16,p.y);lane.accept(b);assertEquals(mode==0?0:1,p.inputs);
            }
        }
    }
    @Test void budgetAndDeadlineDoNotRefundOrRepeatGesture(@TempDir Path root)throws Exception {
        var p=new Port();var a=action(p,"back",null);var r=GameQuestMenuAction.Request.read(a);
        var limited=new GameActionLaneTest.Fixture(java.nio.file.Files.createDirectory(root.resolve("budget")),2);
        limited.port.customMotor=e->GameQuestMenuAction.start(p,r,e);
        try(var lane=limited.open()) {
            limited.arm(lane,1);limited.deliver(lane);var b=limited.batch(1,"menu",1);b.add("action",a);
            assertEquals("BUDGET_EXHAUSTED",assertThrows(IOException.class,()->lane.accept(b)).getMessage());assertEquals(0,p.inputs);
        }
        var f=new GameActionLaneTest.Fixture(java.nio.file.Files.createDirectory(root.resolve("deadline")),100);f.port.customMotor=e->GameQuestMenuAction.start(p,r,e);
        try(var lane=f.open()) {
            f.arm(lane,1);f.deliver(lane);var b=f.batch(1,"menu",1);b.add("action",a);lane.accept(b);f.start(lane);f.time.advance(5000);lane.tick();
            assertEquals("cancelled",lane.status("menu").get("status").getAsString());assertTrue(p.closed);
            assertEquals(2,lane.status("menu").get("emitted_events").getAsInt());lane.accept(b);assertEquals(1,p.inputs);
        }
    }
}
