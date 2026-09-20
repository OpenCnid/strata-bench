package io.github.opencnid.strata.client;

import com.google.gson.JsonObject;
import java.io.IOException;
import java.util.Objects;

/** One visible choice-reward button, bound to a returned reward page and current book. */
final class GameQuestRewardOpen {
    static final String POLICY="ftb-visible-choice-reward-menu-open/1";
    record Selection(GameQuestComponents.Query query,long revision,String id) {
        static Selection read(JsonObject value)throws IOException {
            SettingsJson.fields(value,"query","revision","entry_id");
            if(!value.get("query").isJsonObject())throw invalid();
            var query=GameQuestComponents.Query.read(value.getAsJsonObject("query"));
            String id=SettingsJson.string(value,"entry_id");
            if(!query.part().equals("rewards") || !id.matches("[0-9A-F]{16}"))throw invalid();
            return new Selection(query,SettingsJson.integer(value,"revision"),id);
        }
        void visible(JsonObject page,long source)throws IOException {
            if(!query.json().equals(page.get("query")) || SettingsJson.integer(page,"revision")!=revision
                    || SettingsJson.integer(page,"source_generation")!=source)throw changed();
            int found=0;
            for(var entry:page.getAsJsonArray("entries")) {
                var row=entry.getAsJsonObject();
                if(id.equals(SettingsJson.string(row,"entry_id")) && "reward".equals(SettingsJson.string(row,"kind"))) {
                    if(!"can_claim".equals(SettingsJson.string(row.getAsJsonObject("reward"),"claim_state")))throw new IOException("GAME_QUEST_OPEN_FORBIDDEN");
                    found++;
                }
            }
            if(found!=1)throw new IOException(found==0?"TARGET_NOT_OBSERVED":"GAME_QUEST_AMBIGUOUS");
        }
    }
    record Request(long source,long generation,long revision,Selection selection) {
        static Request read(JsonObject value)throws IOException {
            SettingsJson.fields(value,"kind","operation","source","source_generation","expected_screen_generation","expected_screen_revision","selection");
            if(!SettingsJson.string(value,"kind").equals("quest_reward") || !SettingsJson.string(value,"operation").equals("open")
                    || !SettingsJson.string(value,"source").equals("ftb_quests") || !value.get("selection").isJsonObject())throw invalid();
            return new Request(SettingsJson.integer(value,"source_generation"),SettingsJson.integer(value,"expected_screen_generation"),
                SettingsJson.integer(value,"expected_screen_revision"),Selection.read(value.getAsJsonObject("selection")));
        }
    }
    record Target(Object reward,Object button,String context) {
        void validate()throws IOException {
            if(reward==null || button==null || context==null || !context.matches("[a-f0-9]{64}"))throw invalid();
        }
        boolean same(Target other){return reward==other.reward && button==other.button && context.equals(other.context);}
    }
    interface Port {
        GameQuestScreen.Snapshot book()throws IOException;
        Target selection(Request request)throws IOException;
        Object open(Target target)throws IOException;
        void confirm(Request request,Target target,Object book,Object menu)throws IOException;
    }
    record Prepared(GameQuestScreen.Snapshot book,Target target) { }
    static Prepared validate(Port port,Request request)throws IOException {
        var before=port.book();var frame=before.frame();var query=request.selection.query;
        if(!frame.kind().equals("quest_book") || !Objects.equals(frame.chapter(),query.chapter()) || !Objects.equals(frame.quest(),query.quest()))
            throw new IOException("TARGET_NOT_OBSERVED");
        if(frame.source()!=request.source || before.generation()!=request.generation || before.revision()!=request.revision)throw changed();
        var target=port.selection(request);if(target==null)throw invalid();target.validate();
        var after=port.book();
        if(!before.frame().same(after.frame()) || before.generation()!=after.generation() || before.revision()!=after.revision())throw changed();
        return new Prepared(before,target);
    }
    static GameActionLane.Motor start(Port port,Request request,GameActionLane.Emitter emit)throws IOException {
        var prepared=validate(port,request);Object[] menu={null};
        emit.invoke(() -> {
            var now=validate(port,request);
            if(!prepared.book.frame().same(now.book.frame()) || !prepared.target.same(now.target))throw changed();
            menu[0]=port.open(prepared.target);
        });
        if(menu[0]==null || menu[0]==prepared.book.frame().screen())throw new IOException("GAME_QUEST_REWARD_OPEN_UNCONFIRMED");
        port.confirm(request,prepared.target,prepared.book.frame().screen(),menu[0]);
        return ignored -> {port.confirm(request,prepared.target,prepared.book.frame().screen(),menu[0]);return true;};
    }
    private static IOException changed(){return new IOException("GAME_QUEST_CHANGED");}
    private static IOException invalid(){return new IOException("GAME_QUEST_REWARD_OPEN_INVALID");}
}
