package io.github.opencnid.strata.client;

import com.google.gson.JsonObject;
import java.io.IOException;

/** One ordinary open-book callback. No task/reward selector, automatic navigation or replay. */
final class GameQuestOpen {
    static final String POLICY = "ftb-own-team-open-screen-cas/1";
    record Request(long generation, long revision) {
        static Request read(JsonObject value) throws IOException {
            SettingsJson.fields(value,"kind","operation","source","source_generation","expected_catalog_revision");
            if (!SettingsJson.string(value,"kind").equals("quest_ui")
                    || !SettingsJson.string(value,"operation").equals("open")
                    || !SettingsJson.string(value,"source").equals("ftb_quests")) throw new IOException("MECHANIC_UNSUPPORTED");
            return new Request(SettingsJson.integer(value,"source_generation"),SettingsJson.integer(value,"expected_catalog_revision"));
        }
    }
    record State(long generation, long revision, Object screen, boolean questScreen) { }
    interface Port {
        // Must enforce own team, source identity, non-editing, permission, body and input context.
        State read() throws IOException;
        // Returns the actual new screen identity, never a synthesized success flag.
        Object open() throws IOException;
    }
    static void validate(Port port, Request request) throws IOException {
        var state=port.read();
        if (state.generation<0 || state.generation!=request.generation || state.revision!=request.revision)
            throw new IOException("GAME_QUEST_CHANGED");
        if (state.screen!=null || state.questScreen) throw new IOException("GAME_SCREEN_OPEN");
    }
    private static void opened(Port port, Request request, Object screen) throws IOException {
        var state=port.read();
        if (screen==null || state.screen!=screen || !state.questScreen || state.generation!=request.generation)
            throw new IOException("GAME_QUEST_OPEN_UNCONFIRMED");
    }
    static GameActionLane.Motor start(Port port, Request request, GameActionLane.Emitter emitter) throws IOException {
        validate(port,request);final Object[] screen={null};
        emitter.invoke(() -> {validate(port,request);screen[0]=port.open();});
        opened(port,request,screen[0]);
        return ignored -> {opened(port,request,screen[0]);return true;};
    }
}
