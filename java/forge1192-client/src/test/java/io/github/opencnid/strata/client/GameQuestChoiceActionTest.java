package io.github.opencnid.strata.client;

import static org.junit.jupiter.api.Assertions.*;
import static io.github.opencnid.strata.client.GameQuestMenuActionTest.action;
import static io.github.opencnid.strata.client.GameQuestMenuActionTest.run;
import com.google.gson.JsonObject;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

/** Real motor/lane/projector, synthetic opening-bound native menu and scrollbar. */
class GameQuestChoiceActionTest {
    static final class Port implements GameQuestMenuAction.Port {
        final GameQuestRewardOpenTest.Port opening;final GameQuestMenu pages=new GameQuestMenu();
        final GameQuestMenuTest.Source source=GameQuestChoiceMenuTest.source(new Object());
        double value,y,step=20;int height=160,contentHeight=320,inputs;String shape="choice";
        boolean refuse,failAfter,movePanelOnly,wheelEnabled=true;
        Port()throws IOException {
            this(new GameQuestRewardOpenTest.Port());opening.open(null);
        }
        Port(GameQuestRewardOpenTest.Port opening){this.opening=opening;}
        JsonObject page(GameQuestMenu.Query query)throws IOException {
            if(opening.menu==null || opening.menu!=opening.navigation.open.screen)throw new IOException("GAME_QUEST_MENU_UNSUPPORTED");
            source.screen=opening.menu;source.generation=opening.navigation.open.generation;
            source.layout=KeyOptions.sha256(shape+"/"+scroll()+"/"+wheelEnabled);return pages.page(query,source);
        }
        GameQuestMenuAction.Scroll scroll() {
            return new GameQuestMenuAction.Scroll(0,y,step,144,height,144,contentHeight,
                new GameQuestMenuAction.Wheel(value,0,contentHeight-height));
        }
        public GameQuestMenuAction.State read()throws IOException {
            var p=page(new GameQuestMenu.Query(0));
            return new GameQuestMenuAction.State(source.generation,p.get("menu_generation").getAsLong(),p.get("revision").getAsLong(),
                opening.menu,opening.parent,opening.reward,KeyOptions.sha256(shape),scroll(),true,wheelEnabled);
        }
        public void wheel(GameQuestMenuAction.State before,String direction)throws IOException {
            inputs++;if(refuse)return;
            double attempted=value+step*(direction.equals("up")?-1:1),maximum=contentHeight-height;
            double updated=attempted<0?0:attempted>maximum?maximum:attempted;
            if(!movePanelOnly)value=updated;y=maximum<=0?0:updated;
            if(failAfter)throw new IOException("INJECTED_AFTER_SCROLL");
        }
        public void back(GameQuestMenuAction.State before)throws IOException {
            inputs++;if(refuse)return;opening.navigation.open.screen=opening.parent;opening.menu=null;
            if(failAfter)throw new IOException("INJECTED_AFTER_BACK");
        }
        public void confirmBack(GameQuestMenuAction.State before)throws IOException {
            if(opening.menu!=null || opening.navigation.open.screen!=before.parent()
                    || opening.navigation.open.generation!=before.source())throw new IOException("GAME_QUEST_CHANGED");
        }
    }
    @Test void positiveRangeFractionalStepsAndBoundsMatchPinnedWheelTrace()throws Exception {
        var p=new Port();p.step=20.25;run(p,"scroll","down");assertEquals(20.25,p.value);assertEquals(20.25,p.y);
        run(p,"scroll","up");assertEquals(0,p.value);run(p,"scroll","up");assertEquals(0,p.value);
        p.value=p.y=159;run(p,"scroll","down");assertEquals(160,p.value);
        run(p,"scroll","down");assertEquals(160,p.value);assertEquals(5,p.inputs);
    }
    @Test void fittingContentPreservesNegativeScrollbarMaximumWithoutMovingPanel()throws Exception {
        var p=new Port();p.contentHeight=30;var before=p.page(new GameQuestMenu.Query(0));
        run(p,"scroll","down");assertEquals(-130,p.value);assertEquals(0,p.y);
        assertNotEquals(before.get("revision"),p.page(new GameQuestMenu.Query(0)).get("revision"));
        run(p,"scroll","down");assertEquals(0,p.value);assertEquals(0,p.y);
        run(p,"scroll","up");assertEquals(0,p.value);run(p,"scroll","down");assertEquals(-130,p.value);
        run(p,"scroll","up");assertEquals(0,p.value);assertEquals(0,p.y);
        p.contentHeight=p.height;run(p,"scroll","down");assertEquals(0,p.value);assertEquals(0,p.y);
    }
    @Test void unchangedPanelDoesNotHideRefusedScrollbarMutation()throws Exception {
        var p=new Port();p.contentHeight=30;p.movePanelOnly=true;
        var request=GameQuestMenuAction.Request.read(action(p,"scroll","down"));
        assertEquals("GAME_QUEST_SCROLL_UNCONFIRMED",assertThrows(IOException.class,
            ()->GameQuestMenuAction.start(p,request,GameActionLane.Operation::run)).getMessage());assertEquals(1,p.inputs);
    }
    @Test void independentValueRangeStepLayoutSourceAndScreenChangesRejectBeforeEmission()throws Exception {
        for(int mode=0;mode<7;mode++) {
            var p=new Port();p.contentHeight=30;var request=GameQuestMenuAction.Request.read(action(p,"scroll","down"));
            switch(mode) {
                case 0 -> p.value=-130;
                case 1 -> p.contentHeight=40;
                case 2 -> p.step=16;
                case 3 -> p.shape="resized";
                case 4 -> p.opening.navigation.open.generation++;
                case 5 -> p.opening.navigation.open.screen=new Object();
                case 6 -> p.wheelEnabled=false;
            }
            assertThrows(IOException.class,()->GameQuestMenuAction.start(p,request,op->fail("No emission")));assertEquals(0,p.inputs);
        }
    }
    @Test void dispatchAndNextTickFenceChangedRewardParentAndScrollbar()throws Exception {
        for(int mode=0;mode<2;mode++) {
            var p=new Port();var request=GameQuestMenuAction.Request.read(action(p,"scroll","down"));final int selected=mode;
            assertThrows(IOException.class,()->GameQuestMenuAction.start(p,request,op->{
                if(selected==0)p.opening.reward=new Object();else p.opening.parent=new Object();op.run();
            }));assertEquals(0,p.inputs);
        }
        var p=new Port();p.contentHeight=30;
        var motor=GameQuestMenuAction.start(p,GameQuestMenuAction.Request.read(action(p,"scroll","down")),GameActionLane.Operation::run);
        p.value=0;assertThrows(IOException.class,()->motor.tick(op->fail("No replay")));assertEquals(1,p.inputs);
    }
    @Test void invalidOrDesynchronizedScrollbarStateRejects() {
        for(double[] v:new double[][]{{Double.NaN,0,160,0},{0,1,160,0},{161,0,160,161},
                {20,0,160,0},{0,0,159,0},{-1,0,160,0},{Double.POSITIVE_INFINITY,0,160,0}}) {
            var scroll=new GameQuestMenuAction.Scroll(0,v[3],20,144,160,144,320,new GameQuestMenuAction.Wheel(v[0],v[1],v[2]));
            assertThrows(IOException.class,scroll::validate);
        }
        assertThrows(IOException.class,()->new GameQuestMenuAction.Scroll(1,0,20,144,160,145,320,
            new GameQuestMenuAction.Wheel(0,0,160)).validate());
        assertThrows(IOException.class,()->new GameQuestMenuAction.Scroll(0,0,20,144,160,144,30,
            new GameQuestMenuAction.Wheel(-131,0,-130)).validate());
    }
    @Test void normalBackReturnsParentWithoutChoiceOrClaimCallback()throws Exception {
        var p=new Port();assertTrue(p.page(new GameQuestMenu.Query(0)).getAsJsonArray("controls").isEmpty());
        Object parent=p.opening.parent;run(p,"back",null);assertNull(p.opening.menu);
        assertSame(parent,p.opening.navigation.read().frame().screen());assertEquals(1,p.inputs);
        assertThrows(IOException.class,()->p.page(new GameQuestMenu.Query(0)));
    }
    @Test void cancelledAndUncertainWheelRetainStateChargesAndNeverReplay(@TempDir Path root)throws Exception {
        for(int mode=0;mode<3;mode++) {
            var f=new GameActionLaneTest.Fixture(Files.createDirectory(root.resolve("case-"+mode)),100);
            var p=new Port();p.contentHeight=30;p.failAfter=mode==2;var a=action(p,"scroll","down");
            var r=GameQuestMenuAction.Request.read(a);f.port.customMotor=e->GameQuestMenuAction.start(p,r,e);
            try(var lane=f.open()) {
                f.arm(lane,1);f.deliver(lane);var b=f.batch(1,"choice-wheel",1);b.add("action",a);lane.accept(b);
                if(mode>0)f.start(lane);if(mode<2)lane.cancel("choice-wheel");
                var status=lane.status("choice-wheel");assertEquals(mode==2?"unknown":"cancelled",status.get("status").getAsString());
                assertEquals(mode==0?1:2,status.get("attempted_events").getAsInt());
                if(mode==2)assertTrue(status.get("emitted_events").isJsonNull());
                else assertEquals(mode==0?1:2,status.get("emitted_events").getAsInt());
                assertTrue(lane.health().get("fenced").getAsBoolean());
                assertEquals(mode==0?0:-130,p.value);assertEquals(0,p.y);lane.accept(b);assertEquals(mode==0?0:1,p.inputs);
            }
        }
    }
    @Test void durableBackDeduplicatesAfterJournalReopen(@TempDir Path root)throws Exception {
        var f=new GameActionLaneTest.Fixture(root,100);var p=new Port();var a=action(p,"back",null);
        var r=GameQuestMenuAction.Request.read(a);f.port.customMotor=e->GameQuestMenuAction.start(p,r,e);
        var batch=f.batch(1,"choice-back",1);batch.add("action",a);
        try(var lane=f.open()) {
            f.arm(lane,1);f.deliver(lane);lane.accept(batch);f.start(lane);lane.tick();
            assertEquals("emitted",lane.status("choice-back").get("status").getAsString());
            assertEquals(2,lane.status("choice-back").get("emitted_events").getAsInt());lane.accept(batch);assertEquals(1,p.inputs);
        }
        try(var lane=f.open()){assertEquals("emitted",lane.accept(batch).get("status").getAsString());assertEquals(1,p.inputs);}
    }
}
