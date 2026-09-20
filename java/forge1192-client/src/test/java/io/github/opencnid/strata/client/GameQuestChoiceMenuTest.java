package io.github.opencnid.strata.client;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;

/** Synthetic current widgets; no native reward data or claim authority. */
class GameQuestChoiceMenuTest {
    static GameQuestMenuTest.Source source(Object screen) {
        var source=new GameQuestMenuTest.Source();source.screen=screen;
        source.context=new GameQuestMenu.Context("0000000000000001","0000000000000002",null,"0000000000000003","Choose reward");
        source.controls=List.of();source.items=List.of(choice("Visible choice",true));return source;
    }
    static GameQuestMenu.Item choice(String title,boolean visible) {
        return new GameQuestMenu.Item() {
            public boolean visible(){return visible;}
            public GameQuestMenu.ChoiceDisplay display(){assertTrue(visible,"Hidden choice title/tooltip read");
                return new GameQuestMenu.ChoiceDisplay(title,false,List.of(new GameQuestText.Line("text","Visible tooltip")));}
        };
    }
    @Test void visibleWidgetsOnlyWithBoundedChoiceShapeAndNoRawSelectors()throws Exception {
        var source=source(new Object());source.items=List.of(choice("canary",false),choice("Visible",true));
        var page=new GameQuestMenu().page(new GameQuestMenu.Query(0),source);
        assertEquals("reward_choices",page.get("menu_kind").getAsString());
        assertFalse(page.getAsJsonObject("context").has("task_id"));
        assertEquals("0000000000000003",page.getAsJsonObject("context").get("reward_id").getAsString());
        var row=page.getAsJsonArray("entries").get(0).getAsJsonObject();assertEquals(4,row.size());
        assertEquals(0,row.get("index").getAsInt());assertFalse(row.get("enabled").getAsBoolean());
        assertFalse(page.toString().matches(".*(canary|weight|table|packet|command|nbt|screen_identity).*"));
    }
    @Test void choiceOrderPagingAndReplacementBindRevisions()throws Exception {
        var source=source(new Object());source.items=new ArrayList<>();
        for(int n=0;n<40;n++)source.items.add(choice("Choice "+n,true));
        var menu=new GameQuestMenu();var first=menu.page(new GameQuestMenu.Query(0),source);
        var last=menu.page(new GameQuestMenu.Query(32),source);
        assertEquals(32,first.get("next_cursor").getAsInt());assertEquals(first.get("revision"),last.get("revision"));
        assertEquals("Choice 32",last.getAsJsonArray("entries").get(0).getAsJsonObject().get("title").getAsString());
        source.items.set(0,choice("changed",true));assertNotEquals(first.get("revision"),menu.page(new GameQuestMenu.Query(0),source).get("revision"));
        source.screen=new Object();assertNotEquals(first.get("menu_generation"),menu.page(new GameQuestMenu.Query(0),source).get("menu_generation"));
    }
    @Test void mixedKindsControlsPrivateRichPayloadAndBoundsReject() {
        var source=source(new Object());var menu=new GameQuestMenu();
        source.items=List.of(new GameQuestMenuTest.Item());assertThrows(IOException.class,()->menu.page(new GameQuestMenu.Query(0),source));
        source.items=List.of(choice("Visible",true));source.controls=List.of(new GameQuestMenuTest.Control());
        assertThrows(IOException.class,()->menu.page(new GameQuestMenu.Query(0),source));source.controls=List.of();
        source.items=List.of(choice("x".repeat(1025),true));assertThrows(IOException.class,()->menu.page(new GameQuestMenu.Query(0),source));
        source.items=java.util.Collections.nCopies(513,choice("hidden",false));assertThrows(IOException.class,()->menu.page(new GameQuestMenu.Query(0),source));
        source.items=List.of(new GameQuestMenu.Item(){public boolean visible(){return true;}
            public GameQuestMenu.ChoiceDisplay display(){return new GameQuestMenu.ChoiceDisplay("visible",true,List.of(new GameQuestText.Line("unsupported","canary")));}});
        assertThrows(IOException.class,()->menu.page(new GameQuestMenu.Query(0),source));
    }
    @Test void retainedOpeningBindingExpiresOnMenuOrSourceChange()throws Exception {
        var bindings=new NativeQuestChoiceMenu.Bindings();var source=new GameQuestMenuTest.Source();
        GameQuestCatalog.Source quests=new GameQuestCatalog.Source(){public long generation(){return source.generation;}
            public Iterable<? extends GameQuestCatalog.Entry> entries(GameQuestCatalog.Query ignored){throw new AssertionError("No raw reward-table lookup");}};
        var menu=new Object();var parent=new Object();var reward=new Object();
        var bound=new NativeQuestChoiceMenu.Binding(menu,parent,reward,"0000000000000001","0000000000000002","0000000000000003",1,quests,new Object(),new Object());
        bindings.bind(bound);bindings.tick(menu);bindings.bind(bound);
        assertThrows(IOException.class,()->bindings.bind(new NativeQuestChoiceMenu.Binding(new Object(),parent,reward,bound.chapter(),bound.quest(),bound.id(),1,quests,bound.file(),bound.team())));
        bindings.tick(new Object());bindings.bind(bound);source.generation++;
        bindings.tick(menu);var replacement=new NativeQuestChoiceMenu.Binding(new Object(),parent,reward,bound.chapter(),bound.quest(),bound.id(),2,quests,bound.file(),bound.team());
        bindings.bind(replacement);bindings.clear();assertThrows(IOException.class,()->bindings.bind(bound));
        bindings.bind(replacement);
    }
}
