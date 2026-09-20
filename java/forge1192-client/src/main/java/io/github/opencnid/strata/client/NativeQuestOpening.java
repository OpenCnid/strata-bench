package io.github.opencnid.strata.client;

import static io.github.opencnid.strata.client.NativeQuests.*;
import com.google.gson.JsonObject;
import dev.ftb.mods.ftblibrary.ui.ScreenWrapper;
import java.io.IOException;
import net.minecraft.client.Minecraft;

/** Exact public FTB opening API; optional classes are reached only after artifact validation. */
final class NativeQuestOpening {
    interface Catalog { JsonObject read() throws IOException; }
    static GameQuestOpen.Port port(Minecraft client, Catalog catalog, GameActionLane.Operation context) throws IOException {
        final Class<?> fileType=type("client.ClientQuestFile"),screenType=type("gui.quests.QuestScreen");
        final Object file=field(fileType,null,"INSTANCE"),team=field(fileType,file,"self");
        return new GameQuestOpen.Port() {
            private void allowed() throws IOException {
                context.run();FtbQuestDisplays.requireNormalModifiers();
                if (field(fileType,null,"INSTANCE")!=file || field(fileType,file,"self")!=team
                        || bool(call(file,"canEdit"))) throw new IOException("GAME_QUEST_SOURCE_UNAVAILABLE");
                if (bool(field(file.getClass(),file,"disableGui")) || bool(call(team,"isLocked")))
                    throw new IOException("GAME_QUEST_OPEN_FORBIDDEN");
            }
            public GameQuestOpen.State read() throws IOException {
                allowed();var page=catalog.read();allowed();
                boolean matching=false;
                if (client.screen!=null && client.screen.getClass()==ScreenWrapper.class) {
                    var gui=((ScreenWrapper)client.screen).getGui();
                    matching=gui.getClass()==screenType && field(screenType,gui,"file")==file
                        && gui.contextMenu==null && gui.parent==null && gui.getScreen()==client.getWindow();
                }
                return new GameQuestOpen.State(SettingsJson.integer(page,"source_generation"),SettingsJson.integer(page,"revision"),client.screen,matching);
            }
            public Object open() throws IOException {
                allowed();if(client.screen!=null)throw new IOException("GAME_SCREEN_OPEN");
                final Object opened;
                try { opened=fileType.getMethod("openGui").invoke(null); }
                catch (ReflectiveOperationException | SecurityException failure) { throw new IOException("GAME_QUEST_OPEN_UNCONFIRMED"); }
                allowed();
                if (opened==null || opened.getClass()!=screenType || client.screen==null
                        || client.screen.getClass()!=ScreenWrapper.class || ((ScreenWrapper)client.screen).getGui()!=opened)
                    throw new IOException("GAME_QUEST_OPEN_UNCONFIRMED");
                return client.screen;
            }
        };
    }
}
