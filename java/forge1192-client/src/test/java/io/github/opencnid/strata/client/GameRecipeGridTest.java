package io.github.opencnid.strata.client;

import com.google.gson.JsonObject;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

/** Independent click/menu simulation; no Minecraft visibility or mechanics claim. */
class GameRecipeGridTest {
    @Test void completedManualGridNeedsFreshServerOutputBeforeTakingAnyResult() throws Exception {
        var port=new Port(1);var motor=GameCrafting.start(port,1,port::emit);
        // A fresh authoritative baseline precedes the first manual grid click.
        assertTrue(port.clicks.isEmpty());
        port.ack();assertFalse(motor.tick(port::emit));
        // Pick, place, then the separate final refresh. No output click yet.
        port.ack();assertFalse(motor.tick(port::emit));
        port.ack();assertFalse(motor.tick(port::emit));
        assertEquals(0,port.takes);assertEquals(4,port.ticket);
        for(int i=0;i<5;i++)assertFalse(motor.tick(port::emit));
        assertEquals(0,port.takes);
        // A stale/wrong authoritative output cannot be replaced by prediction.
        var slots=new ArrayList<>(port.slots);slots.set(0,EMPTY);
        port.reply=new GameInventory.View(slots,port.cursor,0);
        assertFalse(motor.tick(port::emit));assertEquals(0,port.takes);
        // A delayed empty preview permits only a charged read, never a take.
        assertEquals(5,port.ticket);
        slots.set(0,item("wrong",2));
        port.reply=new GameInventory.View(slots,port.cursor,0);
        assertThrows(IOException.class,()->motor.tick(port::emit));assertEquals(0,port.takes);
        var good=new Port(1);var valid=GameCrafting.start(good,1,good::emit);good.finish(valid);
        assertEquals(1,good.takes);assertTrue(good.cursor.empty());
    }
    static final GameInventory.Stack EMPTY=GameInventory.Stack.EMPTY;
    static GameInventory.Stack item(String name,int count) { return new GameInventory.Stack("test:"+name,count,"component-"+name); }
    static class Port implements GameCrafting.Port {
        final List<GameInventory.Stack> slots=new ArrayList<>();
        final List<String> clicks=new ArrayList<>();
        GameInventory.Stack cursor=EMPTY, output=item("result",2), remainder=EMPTY;
        GameInventory.View reply; long ticket; int charges, takes;
        boolean valid=true, permission=true, wrongOutput=false;
        JsonObject definition;
        Port(int count) throws IOException {
            for(int i=0;i<46;i++) slots.add(EMPTY); slots.set(9,item("ingredient",count));
            definition=GameRecipes.definition("test:recipe","minecraft:crafting_shaped",1,1,
                List.of(List.of("test:ingredient")),output);
        }
        public void validate() throws IOException { if(!valid) throw new IOException("GAME_RECIPE_CHANGED"); }
        public int gridWidth() { return 2; }
        public int inventoryStart() { return 9; }
        public int inventoryEnd() { return 45; }
        public GameInventory.Stack output() { return output; }
        public GameInventory.View view() { return new GameInventory.View(slots,cursor,0); }
        public int capacity(int slot,GameInventory.Stack stack) { return 64; }
        public boolean mayPickup(int slot) { return permission; }
        public boolean mayPlace(int slot,GameInventory.Stack stack) { return permission; }
        public void fillRecipe() { throw new AssertionError("book transfer must never execute for manual source"); }
        public GameActionLane.Motor gridMotor(GameActionLane.Emitter emit) throws IOException {
            return GameRecipeGrid.start(this,definition,emit);
        }
        public List<GameInventory.Stack> remainders(GameInventory.View filled) throws IOException {
            if(!filled.slots().get(1).equals(item("ingredient",1))) throw new IOException("PRECONDITION_FAILED");
            return List.of(remainder,EMPTY,EMPTY,EMPTY);
        }
        public void click(int slot,int button,boolean quick) {
            assertFalse(quick); clicks.add(slot+":"+button);
            var target=slots.get(slot);
            if(slot==0) { assertEquals(0,button); takes++; cursor=output; slots.set(1,remainder); }
            else if(button==0) { slots.set(slot,cursor); cursor=target; }
            else {
                assertTrue(target.empty()); assertFalse(cursor.empty());
                slots.set(slot,cursor.withCount(1)); cursor=cursor.withCount(cursor.count()-1);
            }
            slots.set(0,slots.get(1).id().equals("test:ingredient")
                ? wrongOutput ? item("wrong",2) : output : EMPTY);
        }
        public long requestSync() { reply=null; return ++ticket; }
        public GameInventory.View reply(long requested) { assertEquals(ticket,requested); return reply; }
        void ack() { reply=view(); }
        void emit(GameActionLane.Operation op) throws IOException { charges++;op.run(); }
        void finish(GameActionLane.Motor motor) throws IOException {
            for(int i=0;i<200;i++) { ack(); if(motor.tick(this::emit)) return; }
            fail("manual test motor did not terminate");
        }
    }
    @Test void manualFillWaitsForEveryFeedbackAndReturnsUnusedStack() throws Exception {
        var port=new Port(3); var motor=GameRecipeGrid.start(port,port.definition,port::emit);
        assertEquals(List.of("9:0"),port.clicks);
        for(int i=0;i<5;i++) assertFalse(motor.tick(port::emit));
        assertEquals(7,port.charges); assertEquals(List.of("9:0"),port.clicks);
        port.ack(); assertFalse(motor.tick(port::emit)); assertEquals(List.of("9:0","1:1"),port.clicks);
        for(int i=0;i<5;i++) assertFalse(motor.tick(port::emit));
        assertEquals(2,port.clicks.size());port.finish(motor);
        assertEquals(List.of("9:0","1:1","9:0"),port.clicks);
        assertEquals(item("ingredient",1),port.slots.get(1));assertEquals(item("ingredient",2),port.slots.get(9));
        assertTrue(port.cursor.empty());assertEquals(0,port.takes);
    }
    @Test void manualFillFeedsExistingConfirmedOutputAndRemainderMotorAcrossRepetitions() throws Exception {
        var port=new Port(2);port.remainder=item("container",1);
        var motor=GameCrafting.start(port,2,port::emit);port.finish(motor);
        assertEquals(2,port.takes);assertTrue(port.cursor.empty());
        assertEquals(4,port.slots.stream().filter(s->s.id().equals("test:result")).mapToInt(GameInventory.Stack::count).sum());
        assertEquals(2,port.slots.stream().filter(s->s.id().equals("test:container")).mapToInt(GameInventory.Stack::count).sum());
        assertEquals(0,port.slots.stream().filter(s->s.id().equals("test:ingredient")).mapToInt(GameInventory.Stack::count).sum());
        assertTrue(port.slots.subList(0,5).stream().allMatch(GameInventory.Stack::empty));
    }
    @Test void allocationBacktracksForCompetingAlternativesAndKeepsShapedEmptyCells() throws Exception {
        var port=new Port(0);port.slots.set(9,item("a",1));port.slots.set(10,item("b",1));
        var recipe=GameRecipes.definition("test:choice","minecraft:crafting_shaped",2,2,
            List.of(List.of("test:a","test:b"),List.of(),List.of("test:a"),List.of()),port.output);
        var plan=GameRecipeGrid.plan(port,recipe,port.view());
        assertEquals(List.of(10,9),plan.stream().map(GameRecipeGrid.Ingredient::source).toList());
        assertEquals(List.of(1,3),plan.stream().map(GameRecipeGrid.Ingredient::target).toList());
        var motor=GameRecipeGrid.start(port,recipe,port::emit);port.finish(motor);
        assertEquals(item("b",1),port.slots.get(1));assertEquals(item("a",1),port.slots.get(3));
        assertTrue(port.slots.get(2).empty());assertTrue(port.slots.get(4).empty());assertEquals(0,port.takes);
    }
    @Test void threeByThreeMenuFillsAllNineCellsFromItsOwnInventoryRange() throws Exception {
        var port=new Port(0) {
            public int gridWidth() { return 3; }
            public int inventoryStart() { return 10; }
            public int inventoryEnd() { return 46; }
        };
        port.slots.set(10,item("ingredient",9));
        var recipe=GameRecipes.definition("test:nine","minecraft:crafting_shaped",3,3,
            java.util.Collections.nCopies(9,List.of("test:ingredient")),port.output);
        var motor=GameRecipeGrid.start(port,recipe,port::emit);port.finish(motor);
        for(int i=1;i<=9;i++) assertEquals(item("ingredient",1),port.slots.get(i));
        assertTrue(port.slots.get(10).empty());assertTrue(port.cursor.empty());assertEquals(26,port.clicks.size());
        assertEquals(52,port.charges);assertEquals(0,port.takes);
    }
    @Test void shapelessAllocationUsesLinearCellsAndCompetingAlternatives() throws Exception {
        var port=new Port(0);port.slots.set(9,item("a",1));port.slots.set(10,item("b",1));
        var recipe=GameRecipes.definition("test:shapeless","minecraft:crafting_shapeless",0,0,
            List.of(List.of("test:a","test:b"),List.of("test:a")),port.output);
        var motor=GameRecipeGrid.start(port,recipe,port::emit);port.finish(motor);
        assertEquals(item("b",1),port.slots.get(1));assertEquals(item("a",1),port.slots.get(2));
        assertTrue(port.slots.get(3).empty());assertTrue(port.slots.get(4).empty());assertTrue(port.cursor.empty());
        assertEquals(4,port.clicks.size());assertEquals(0,port.takes);
    }
    @Test void insufficientResourcesDirtyGridCursorAndPermissionsRejectBeforeClicks() throws Exception {
        for(int fault=0;fault<4;fault++) {
            var port=new Port(1);
            if(fault==0) port.slots.set(9,EMPTY);
            if(fault==1) port.slots.set(2,item("occupied",1));
            if(fault==2) port.cursor=item("held",1);
            if(fault==3) port.permission=false;
            assertThrows(IOException.class,()->GameRecipeGrid.start(port,port.definition,port::emit));
            assertEquals(0,port.charges);assertTrue(port.clicks.isEmpty());
        }
    }
    @Test void giftComponentChangeOrConservedRearrangementCannotAuthorizeNextClick() throws Exception {
        for(int fault=0;fault<3;fault++) {
            var port=new Port(2);port.slots.set(11,item("unrelated",1));
            var motor=GameRecipeGrid.start(port,port.definition,port::emit);
            if(fault==0) port.slots.set(12,item("gift",1));
            if(fault==1) port.cursor=new GameInventory.Stack(port.cursor.id(),port.cursor.count(),"tampered");
            if(fault==2) {port.slots.set(12,port.slots.get(11));port.slots.set(11,EMPTY);}
            port.ack();assertThrows(IOException.class,()->motor.tick(port::emit));assertEquals(1,port.clicks.size());
        }
    }
    @Test void recipeVisibilityLossCancellationAndExhaustionPreservePartialEffectsWithoutReplay() throws Exception {
        var port=new Port(2);var motor=GameRecipeGrid.start(port,port.definition,port::emit);
        port.ack();port.valid=false;
        assertThrows(IOException.class,()->motor.tick(port::emit));assertEquals(1,port.clicks.size());
        assertEquals(item("ingredient",2),port.cursor);
        var cancelled=new Port(2);var pending=GameRecipeGrid.start(cancelled,cancelled.definition,cancelled::emit);cancelled.ack();
        assertThrows(IOException.class,()->pending.tick(op->{throw new IOException("CANCELLED");}));
        assertEquals(1,cancelled.clicks.size());assertEquals(item("ingredient",2),cancelled.cursor);
        var exhausted=new Port(2);
        assertThrows(IOException.class,()->GameRecipeGrid.start(exhausted,exhausted.definition,op->{
            if(++exhausted.charges==2) throw new IOException("BUDGET_EXHAUSTED");op.run();}));
        assertEquals(1,exhausted.clicks.size());assertEquals(item("ingredient",2),exhausted.cursor);assertEquals(0,exhausted.ticket);
    }
    @Test void wrongDerivedOutputStopsBeforeTakeEvenAfterCorrectManualFill() throws Exception {
        var port=new Port(1);port.wrongOutput=true;var motor=GameCrafting.start(port,1,port::emit);
        assertThrows(IOException.class,()->port.finish(motor));assertEquals(0,port.takes);
        assertEquals(item("ingredient",1),port.slots.get(1));
    }
    @Test void allocationSearchIsBoundedWithoutTakingItems() throws Exception {
        var port=new Port(0);for(int i=9;i<45;i++) port.slots.set(i,item("common",1));
        var recipe=GameRecipes.definition("test:search","minecraft:crafting_shapeless",0,0,
            List.of(List.of("test:common"),List.of("test:common"),List.of("test:common"),List.of("test:missing")),port.output);
        assertEquals("GAME_CRAFT_SEARCH_BOUNDS",assertThrows(IOException.class,
            ()->GameRecipeGrid.start(port,recipe,port::emit)).getMessage());assertTrue(port.clicks.isEmpty());
    }
}
