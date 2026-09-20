package io.github.opencnid.strata.client;

import com.google.gson.JsonObject;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

/** One selected recipe, filled through ordinary clicks. No recipe or resource planning. */
final class GameRecipeGrid {
    static final String POLICY = "visible-recipe-manual-grid-feedback-search4096/1";
    record Ingredient(int source, int target, GameInventory.Stack item) {}
    static GameActionLane.Motor start(GameCrafting.Port port, JsonObject definition,
            GameActionLane.Emitter emit) throws IOException {
        port.validate(); var before = port.view();
        var plan = plan(port, definition, before);
        return new Motor(port, before, plan, emit);
    }
    static List<Ingredient> plan(GameCrafting.Port port, JsonObject definition, GameInventory.View before) throws IOException {
        int grid = port.gridWidth(), start = port.inventoryStart(), end = port.inventoryEnd();
        if ((grid != 2 && grid != 3) || before.resultSlot() != 0 || before.slots().size() > 1024
                || start <= grid * grid || end > before.slots().size() || end - start != 36
                || !before.cursor().empty()) throw new IOException("PRECONDITION_FAILED");
        for (int i=0;i<=grid*grid;i++) if (!before.slots().get(i).empty()) throw new IOException("PRECONDITION_FAILED");
        String serializer = SettingsJson.string(definition,"serializer");
        boolean shaped = serializer.equals("minecraft:crafting_shaped");
        if (!shaped && !serializer.equals("minecraft:crafting_shapeless")) throw new IOException("MECHANIC_UNSUPPORTED");
        int width = Math.toIntExact(SettingsJson.integer(definition,"width"));
        int height = Math.toIntExact(SettingsJson.integer(definition,"height"));
        var entries = definition.getAsJsonArray("ingredients");
        if (entries == null || entries.isEmpty() || entries.size() > grid * grid
                || (shaped ? width < 1 || width > grid || height < 1 || height > grid || entries.size() != width * height
                           : width != 0 || height != 0)) throw new IOException("PRECONDITION_FAILED");
        var ingredients = new ArrayList<List<String>>();
        for (var entry:entries) {
            if (!entry.isJsonArray() || entry.getAsJsonArray().size() > 64) throw new IOException("MECHANIC_UNSUPPORTED");
            var row = new ArrayList<String>();
            for (var value:entry.getAsJsonArray()) {
                if (!value.isJsonPrimitive() || !value.getAsJsonPrimitive().isString()) throw new IOException("MECHANIC_UNSUPPORTED");
                row.add(GameRecipes.id(value.getAsString()));
            }
            if (!shaped && row.isEmpty()) throw new IOException("MECHANIC_UNSUPPORTED");
            ingredients.add(List.copyOf(row));
        }
        int[] available = new int[end-start], selected = new int[entries.size()], visits = {0};
        java.util.Arrays.fill(selected,-1);
        for (int i=start;i<end;i++) {
            int count = before.slots().get(i).count();
            if (count < 0 || count > 64) throw new IOException("MECHANIC_UNSUPPORTED");
            available[i-start] = count;
        }
        if (!choose(ingredients,before,start,available,selected,visits,0)) throw new IOException("PRECONDITION_FAILED");
        var plan = new ArrayList<Ingredient>();
        for (int i=0;i<selected.length;i++) if (selected[i] >= 0) {
            int target = 1 + (shaped ? (i/width)*grid+i%width : i);
            var item = before.slots().get(selected[i]).withCount(1);
            var source = before.slots().get(selected[i]);
            if (!port.mayPickup(selected[i]) || !port.mayPlace(target,source) || port.capacity(target,source) < 1) {
                throw new IOException("PRECONDITION_FAILED");
            }
            plan.add(new Ingredient(selected[i],target,item));
        }
        if (plan.isEmpty()) throw new IOException("PRECONDITION_FAILED");
        return List.copyOf(plan);
    }
    private static boolean choose(List<List<String>> ingredients, GameInventory.View before, int start,
            int[] available, int[] selected, int[] visits, int index) throws IOException {
        if (++visits[0] > 4096) throw new IOException("GAME_CRAFT_SEARCH_BOUNDS");
        if (index == ingredients.size()) return true;
        if (ingredients.get(index).isEmpty()) return choose(ingredients,before,start,available,selected,visits,index+1);
        for (int slot=0;slot<available.length;slot++) if (available[slot] > 0
                && ingredients.get(index).contains(before.slots().get(start+slot).id())) {
            available[slot]--; selected[index]=start+slot;
            if (choose(ingredients,before,start,available,selected,visits,index+1)) return true;
            available[slot]++;
        }
        selected[index]=-1; return false;
    }
    private static final class Motor implements GameActionLane.Motor {
        enum Phase { PICK, PLACE, RETURN }
        final GameCrafting.Port port; final List<Ingredient> plan;
        int index; Phase phase = Phase.PICK;
        GameInventory.View expected;
        GameActionLane.Motor step;
        Motor(GameCrafting.Port port, GameInventory.View before, List<Ingredient> plan, GameActionLane.Emitter emit) throws IOException {
            this.port=port; this.plan=plan; expected=before; next(emit);
        }
        private void next(GameActionLane.Emitter emit) throws IOException {
            port.validate(); var current=port.view(); check(current);
            var ingredient=plan.get(index); var slots=new ArrayList<>(current.slots());
            GameInventory.Stack cursor; int slot;
            if (phase == Phase.PICK) {
                slot=ingredient.source; cursor=slots.get(slot);
                if (!current.cursor().empty() || !cursor.same(ingredient.item)) throw new IOException("REVISION_CONFLICT");
                slots.set(slot,GameInventory.Stack.EMPTY);
            } else if (phase == Phase.PLACE) {
                slot=ingredient.target;
                if (!slots.get(slot).empty() || !current.cursor().same(ingredient.item)) throw new IOException("REVISION_CONFLICT");
                slots.set(slot,ingredient.item); cursor=current.cursor().withCount(current.cursor().count()-1);
            } else {
                slot=ingredient.source;
                if (!slots.get(slot).empty() || !current.cursor().same(ingredient.item)) throw new IOException("REVISION_CONFLICT");
                slots.set(slot,current.cursor()); cursor=GameInventory.Stack.EMPTY;
            }
            expected=new GameInventory.View(slots,cursor,0);
            step=GameInventory.click(port,slot,phase == Phase.PLACE,false,emit);
        }
        private void check(GameInventory.View current) throws IOException {
            if (current.resultSlot() != 0 || current.slots().size() != expected.slots().size()
                    || !current.cursor().equals(expected.cursor())) throw new IOException("REVISION_CONFLICT");
            // Output is a derived preview and may change while ordinary grid slots fill.
            for (int i=1;i<current.slots().size();i++) if (!current.slots().get(i).equals(expected.slots().get(i))) {
                throw new IOException("REVISION_CONFLICT");
            }
        }
        public boolean tick(GameActionLane.Emitter emit) throws IOException {
            port.validate(); if (!step.tick(emit)) return false;
            var current=port.view(); check(current);
            if (phase == Phase.PICK) phase=Phase.PLACE;
            else if (phase == Phase.PLACE && !current.cursor().empty()) phase=Phase.RETURN;
            else { if (++index == plan.size()) return true; phase=Phase.PICK; }
            next(emit); return false;
        }
    }
}
