package io.github.opencnid.strata.client;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;

final class GameQuestMenuTest {
    static final class Item implements GameQuestMenu.Item {
        boolean visible=true;int reads;GameQuestMenu.ItemDisplay display=new GameQuestMenu.ItemDisplay("minecraft:stone",1,"Stone",List.of(new GameQuestText.Line("text","Stone")));
        public boolean visible(){return visible;}
        public GameQuestMenu.ItemDisplay display(){reads++;if(!visible)fail("off-screen content read");return display;}
    }
    static final class Control implements GameQuestMenu.Control {
        boolean visible=true;int reads;GameQuestMenu.ControlDisplay display=new GameQuestMenu.ControlDisplay("submit","Submit",false,List.of());
        public boolean visible(){return visible;}
        public GameQuestMenu.ControlDisplay display(){reads++;if(!visible)fail("hidden control read");return display;}
    }
    static class Source implements GameQuestMenu.Source {
        Object screen=new Object();long generation=1;String layout="a".repeat(64);boolean available=true;
        GameQuestMenu.Context context=new GameQuestMenu.Context("0000000000000001","0000000000000002","0000000000000003","Valid items");
        List<GameQuestMenu.Item> items=new ArrayList<>(List.of(new Item()));List<GameQuestMenu.Control> controls=new ArrayList<>(List.of(new Control()));
        public void validate()throws IOException{if(!available)throw new IOException("TARGET_NOT_OBSERVED");}
        public long generation(){return generation;}
        public Object screen(){return screen;}
        public String layout(){return layout;}
        public GameQuestMenu.Context context(){if(!available)fail("hidden parent read");return context;}
        public Iterable<? extends GameQuestMenu.Item> items(){return items;}
        public Iterable<? extends GameQuestMenu.Control> controls(){return controls;}
    }
    @Test void visibleOnlyNormalItemAndDisabledSubmit()throws Exception {
        var source=new Source();var hidden=new Item();hidden.visible=false;source.items.add(0,hidden);
        var hiddenControl=new Control();hiddenControl.visible=false;source.controls.add(hiddenControl);
        var value=new GameQuestMenu().page(new GameQuestMenu.Query(0),source);
        assertEquals(1,value.getAsJsonArray("entries").size());assertEquals(0,value.getAsJsonArray("entries").get(0).getAsJsonObject().get("index").getAsInt());
        assertFalse(value.getAsJsonArray("controls").get(0).getAsJsonObject().get("enabled").getAsBoolean());
        assertEquals(0,hidden.reads);assertEquals(0,hiddenControl.reads);
        assertFalse(value.toString().matches(".*(layout|packet|nbt|team_id|screen_identity).*"));
        source.available=false;assertThrows(IOException.class,()->new GameQuestMenu().page(new GameQuestMenu.Query(0),source));
    }
    @Test void pagingKeepsOrderAndScreenSourceLayoutBindRevision()throws Exception {
        var source=new Source();source.items=new ArrayList<>();for(int i=0;i<40;i++)source.items.add(new Item());
        var projector=new GameQuestMenu();var first=projector.page(new GameQuestMenu.Query(0),source);
        var second=projector.page(new GameQuestMenu.Query(32),source);
        assertEquals(32,first.get("next_cursor").getAsInt());assertEquals(8,second.getAsJsonArray("entries").size());
        assertEquals(32,second.getAsJsonArray("entries").get(0).getAsJsonObject().get("index").getAsInt());
        assertEquals(first.get("revision"),second.get("revision"));
        source.layout="b".repeat(64);var moved=projector.page(new GameQuestMenu.Query(0),source);
        assertTrue(moved.get("revision").getAsLong()>first.get("revision").getAsLong());assertEquals(first.get("menu_generation"),moved.get("menu_generation"));
        source.screen=new Object();var reopened=projector.page(new GameQuestMenu.Query(0),source);
        assertTrue(reopened.get("menu_generation").getAsLong()>moved.get("menu_generation").getAsLong());
        source.generation++;assertTrue(projector.page(new GameQuestMenu.Query(0),source).get("menu_generation").getAsLong()>reopened.get("menu_generation").getAsLong());
        assertThrows(IOException.class,()->projector.page(new GameQuestMenu.Query(41),source));
    }
    @Test void viewportIntersectionAndNativeScrollTruncation()throws Exception {
        var clip=new GameQuestMenu.Rect(10,10,100,160);
        assertFalse(clip.intersect(new GameQuestMenu.Rect(10,170,32,32)).nonempty());
        assertTrue(clip.intersect(new GameQuestMenu.Rect(10,169,32,32)).nonempty());
        assertFalse(clip.intersect(new GameQuestMenu.Rect(110,10,32,32)).nonempty());
        assertEquals(-35,GameQuestMenu.scrollOffset(35.9));assertEquals(35,GameQuestMenu.scrollOffset(-35.9));
        assertEquals(0,GameQuestMenu.scrollOffset(.9));
        assertThrows(IOException.class,()->GameQuestMenu.scrollOffset(Double.NaN));
        assertThrows(IOException.class,()->GameQuestMenu.scrollOffset(1048577));
        assertThrows(IllegalArgumentException.class,()->new GameQuestMenu.Rect(Integer.MIN_VALUE,0,1,1));
    }
    @Test void changedContextScreenAndVisibilityReject() {
        for(int mode=0;mode<4;mode++) {
            final int selected=mode;var source=new Source(){int validations;
                public void validate()throws IOException {
                    super.validate();if(++validations==2) {
                        if(selected==0)layout="b".repeat(64);if(selected==1)screen=new Object();
                        if(selected==2)generation++;if(selected==3)context=new GameQuestMenu.Context("0000000000000001","0000000000000002","0000000000000004","Other");
                    }
                }
            };
            assertEquals("GAME_QUEST_CHANGED",assertThrows(IOException.class,()->new GameQuestMenu().page(new GameQuestMenu.Query(0),source)).getMessage());
        }
        var source=new Source();source.items=List.of(new GameQuestMenu.Item(){int reads;public boolean visible(){return reads++==0;}
            public GameQuestMenu.ItemDisplay display(){return new Item().display;}});
        assertThrows(IOException.class,()->new GameQuestMenu().page(new GameQuestMenu.Query(0),source));
    }
    @Test void countCandidateTooltipAndAggregateBoundsReject() {
        var source=new Source();var item=(Item)source.items.get(0);
        for(var bad:List.of(new GameQuestMenu.ItemDisplay("minecraft:stone",0,"Stone",List.of()),
                new GameQuestMenu.ItemDisplay("minecraft:stone\n",1,"Stone",List.of()),
                new GameQuestMenu.ItemDisplay("minecraft:stone",1,"Stone",List.of(new GameQuestText.Line("page_break",null))),
                new GameQuestMenu.ItemDisplay("minecraft:stone",1,"Stone",java.util.Collections.nCopies(65,new GameQuestText.Line("text","x"))),
                new GameQuestMenu.ItemDisplay("minecraft:stone",1,"Stone",List.of(new GameQuestText.Line("text","😀".repeat(4096)))))) {
            item.display=bad;assertThrows(IOException.class,()->new GameQuestMenu().page(new GameQuestMenu.Query(0),source));
        }
        source.items=new ArrayList<>();for(int i=0;i<513;i++){var hidden=new Item();hidden.visible=false;source.items.add(hidden);}
        assertEquals("GAME_QUEST_BOUNDS",assertThrows(IOException.class,()->new GameQuestMenu().page(new GameQuestMenu.Query(0),source)).getMessage());
        source.items=new ArrayList<>();for(int i=0;i<512;i++){var large=new Item();large.display=new GameQuestMenu.ItemDisplay("minecraft:stone",1,"Stone",
            List.of(new GameQuestText.Line("text","x".repeat(4096)),new GameQuestText.Line("text","y".repeat(4096)),new GameQuestText.Line("text","z".repeat(1024))));source.items.add(large);}
        assertThrows(IOException.class,()->new GameQuestMenu().page(new GameQuestMenu.Query(0),source));
    }
    @Test void controlRolesHiddenContentAndTotalBytesReject() {
        var source=new Source();source.controls=List.of(new Control(),new Control());
        assertEquals("GAME_QUEST_AMBIGUOUS",assertThrows(IOException.class,()->new GameQuestMenu().page(new GameQuestMenu.Query(0),source)).getMessage());
        var control=new Control();source.controls=List.of(control);control.display=new GameQuestMenu.ControlDisplay("admin","Hidden",true,List.of());
        assertThrows(IOException.class,()->new GameQuestMenu().page(new GameQuestMenu.Query(0),source));
        control.display=new GameQuestMenu.ControlDisplay("submit","Submit",true,List.of(new GameQuestText.Line("text","x".repeat(4096)),new GameQuestText.Line("text","x".repeat(4096))));
        assertThrows(IOException.class,()->new GameQuestMenu().page(new GameQuestMenu.Query(0),source));
    }
    @Test void bytePagingAndDeadlineAreEnforced()throws Exception {
        var source=new Source();source.items=new ArrayList<>();
        for(int i=0;i<8;i++){var item=new Item();item.display=new GameQuestMenu.ItemDisplay("minecraft:stone",1,"Stone",List.of(new GameQuestText.Line("text","x".repeat(4096))));source.items.add(item);}
        var value=new GameQuestMenu().page(new GameQuestMenu.Query(0),source);
        assertTrue(value.getAsJsonArray("entries").size()<8);assertTrue(value.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8).length<=32768);
        long[] calls={0};assertEquals("GAME_QUEST_TIMEOUT",assertThrows(IOException.class,()->new GameQuestMenu(()->calls[0]++*100000001L).page(new GameQuestMenu.Query(0),new Source())).getMessage());
    }
    @Test void queryAndUnsupportedContextReject()throws Exception {
        var query=new GameQuestMenu.Query(0);assertEquals(query,GameQuestMenu.Query.read(query.json()));
        var extra=query.json();extra.addProperty("task_id","hidden");assertThrows(IOException.class,()->GameQuestMenu.Query.read(extra));
        for(String number:List.of("-1","513","true","1.0","1e0","4294967296")) {
            var value=query.json();value.add("after",com.google.gson.JsonParser.parseString(number));assertThrows(IOException.class,()->GameQuestMenu.Query.read(value));
        }
        var source=new Source();source.context=new GameQuestMenu.Context("0000000000000001\n","0000000000000002","0000000000000003","Title");
        assertThrows(IOException.class,()->new GameQuestMenu().page(query,source));
        source.context=null;assertThrows(IOException.class,()->new GameQuestMenu().page(query,source));
    }
}
