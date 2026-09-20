package io.github.opencnid.strata.client;

import com.google.gson.JsonObject;
import java.io.IOException;
import java.util.Objects;
import java.util.Set;

/** Explicit catalog-selected navigation, or one ordinary Back/Close. Never auto-submit or claim. */
final class GameQuestNavigation {
    record Selection(GameQuestCatalog.Query query,long revision,String id) {
        static Selection read(JsonObject value)throws IOException {
            SettingsJson.fields(value,"query","revision","entry_id");
            if(!value.get("query").isJsonObject())throw invalid();
            String id=SettingsJson.string(value,"entry_id");if(!id.matches("[0-9A-F]{16}"))throw invalid();
            return new Selection(GameQuestCatalog.Query.read(value.getAsJsonObject("query")),SettingsJson.integer(value,"revision"),id);
        }
        void visible(JsonObject page,long generation,String operation)throws IOException {
            if(!query.json().equals(page.get("query")) || SettingsJson.integer(page,"source_generation")!=generation
                    || SettingsJson.integer(page,"revision")!=revision)throw new IOException("GAME_QUEST_CHANGED");
            JsonObject found=null;
            for(var value:page.getAsJsonArray("entries")) {
                var row=value.getAsJsonObject();if(!id.equals(SettingsJson.string(row,"entry_id")))continue;
                if(found!=null)throw new IOException("GAME_QUEST_AMBIGUOUS");found=row;
            }
            if(found==null || !operation.equals(SettingsJson.string(found,"kind")))throw new IOException("TARGET_NOT_OBSERVED");
            if(operation.equals("quest") && !found.get("details_visible").getAsBoolean())throw new IOException("TARGET_NOT_OBSERVED");
        }
    }
    record Request(String operation,long source,long generation,long revision,Selection selection) {
        static Request read(JsonObject value)throws IOException {
            SettingsJson.fields(value,"kind","operation","source","source_generation","expected_screen_generation","expected_screen_revision","selection");
            String operation=SettingsJson.string(value,"operation");
            if(!SettingsJson.string(value,"kind").equals("quest_navigate") || !SettingsJson.string(value,"source").equals("ftb_quests")
                    || !Set.of("chapter","quest","back","close").contains(operation))throw invalid();
            var raw=value.get("selection");Selection selection=null;
            if(!raw.isJsonNull()) {if(!raw.isJsonObject())throw invalid();selection=Selection.read(raw.getAsJsonObject());}
            if(Set.of("chapter","quest").contains(operation)!=(selection!=null)
                    || selection!=null && operation.equals("chapter")!=(selection.query.chapter()==null))throw invalid();
            return new Request(operation,SettingsJson.integer(value,"source_generation"),SettingsJson.integer(value,"expected_screen_generation"),
                SettingsJson.integer(value,"expected_screen_revision"),selection);
        }
    }
    interface Port {
        GameQuestScreen.Snapshot read()throws IOException;
        void selection(Request request)throws IOException;
        void navigate(Request request)throws IOException;
        default void confirmRecipeClose(GameQuestScreen.Snapshot before)throws IOException {
            throw new IOException("GAME_QUEST_SCREEN_UNSUPPORTED");
        }
    }
    static GameQuestScreen.Snapshot validate(Port port,Request request)throws IOException {
        var state=port.read();
        if(state.frame().screen()==null)throw new IOException("GAME_QUEST_SCREEN_UNSUPPORTED");
        if(state.frame().kind().equals("task_recipes") && !request.operation.equals("close"))
            throw new IOException("GAME_QUEST_RECIPE_NAVIGATION_UNSUPPORTED");
        if(state.frame().source()!=request.source || state.generation()!=request.generation || state.revision()!=request.revision)
            throw new IOException("GAME_QUEST_CHANGED");
        port.selection(request);var after=port.read();
        if(after.generation()!=state.generation() || after.revision()!=state.revision() || !after.frame().same(state.frame()))
            throw new IOException("GAME_QUEST_CHANGED");
        return state;
    }
    private static void confirm(Port port,Request request,GameQuestScreen.Snapshot before)throws IOException {
        if(before.frame().kind().equals("task_recipes")){port.confirmRecipeClose(before);return;}
        var now=port.read().frame();var old=before.frame();Object screen=old.screen();String chapter=old.chapter(),quest=old.quest();
        switch(request.operation) {
            case "close" -> {screen=null;chapter=null;quest=null;}
            case "back" -> {if(quest!=null)quest=null;else {screen=null;chapter=null;}}
            case "chapter" -> {if(!request.selection.id.equals(chapter))quest=null;chapter=request.selection.id;}
            case "quest" -> {chapter=request.selection.query.chapter();quest=request.selection.id;}
            default -> throw invalid();
        }
        if(now.source()!=old.source() || now.screen()!=screen || !Objects.equals(now.chapter(),chapter) || !Objects.equals(now.quest(),quest))
            throw new IOException("GAME_QUEST_NAVIGATION_UNCONFIRMED");
    }
    static GameActionLane.Motor start(Port port,Request request,GameActionLane.Emitter emit)throws IOException {
        var before=validate(port,request);
        emit.invoke(() -> {validate(port,request);port.navigate(request);});
        confirm(port,request,before);return ignored -> {confirm(port,request,before);return true;};
    }
    private static IOException invalid(){return new IOException("GAME_QUEST_NAVIGATION_INVALID");}
}
