package io.github.opencnid.strata.client;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.nio.file.Files;
import java.time.Instant;

/** Synthetic cross-language fixture only; excluded from the mod JAR. No game, account or desktop. */
public final class GameBridgeFixture {
    private static final class Port implements NativeGameProtocol.RuntimePort, GameActionLane.RuntimePort {
        private final Thread owner = Thread.currentThread();
        private final GamePages pages = new GamePages();
        private final GameQuestOpenTest.Port questOpen = new GameQuestOpenTest.Port();
        private final GameQuestNavigationTest.Port questNavigation = new GameQuestNavigationTest.Port(questOpen);
        private final GameQuestTaskOpenTest.Port questTask = new GameQuestTaskOpenTest.Port(questNavigation);
        private final GameQuestMenuActionTest.Port questMenuAction = new GameQuestMenuActionTest.Port(questTask);
        private final GameQuestRewardOpenTest.Port questReward = new GameQuestRewardOpenTest.Port(questNavigation);
        private final GameQuestChoiceActionTest.Port choiceMenu = new GameQuestChoiceActionTest.Port(questReward);
        private final GameQuestRecipeViewTest.Port recipeView = new GameQuestRecipeViewTest.Port(questTask);
        private final boolean recipeMode = Boolean.getBoolean("strata.fixture.taskRecipes");
        private final java.util.List<GameRecipeControls.Control> recipeControls = GameRecipePageTest.controls();
        private final Object recipeRouter = new Object();
        private final java.util.List<Object> recipeHandlers = java.util.List.of(new Object(),new Object(),new Object(),new Object());
        private final GameRecipeInput.Ownership recipeInput = new GameRecipeInput.Ownership();
        private Object recipeFrame = new Object(); private int recipeNavigations;
        private final java.util.ArrayDeque<Integer> recipeHistory = new java.util.ArrayDeque<>();
        private String active;
        private double x = -1.25;
        private long lastRevision;
        private final boolean hold;
        Port(boolean hold) { this.hold = hold; }
        public String bodyFingerprint() { return "a".repeat(64); }
        public long connectionGeneration() { return 1; }
        public JsonObject recipes(int after) throws IOException {
            requireClientThread();
            return new GameRecipes().page(java.util.List.of(
                GameRecipes.definition("fixture:expert", "minecraft:crafting_shapeless", 0, 0,
                    java.util.List.of(java.util.List.of("fixture:changed_ingredient")), new GameInventory.Stack("fixture:output", 2, "private")),
                GameRecipes.unsupported("fixture:unsupported")), after);
        }
        public JsonObject questComponents(GameQuestComponents.Query query) throws IOException {
            requireClientThread();return new GameQuestComponents().page(query,query.part().equals("rewards")?
                GameQuestRewardOpenTest.rewardSource(true):GameQuestComponentsTest.fixtureSource(query.part()));
        }
        public JsonObject questMenu(GameQuestMenu.Query query)throws IOException {
            requireClientThread();if(questReward.menu!=null)return choiceMenu.page(query);
            if(recipeMode && questTask.menu!=null)throw new IOException("GAME_QUEST_MENU_UNSUPPORTED");
            return questTask.menu!=null?questMenuAction.page(query):new GameQuestMenu().page(query,new GameQuestMenuTest.Source());
        }
        public JsonObject questScreen()throws IOException {requireClientThread();
            if(questReward.menu!=null)throw new IOException("GAME_QUEST_SCREEN_UNSUPPORTED");
            return recipeMode?recipeView.read().json():questTask.book().json();}
        public JsonObject recipePage()throws IOException {
            requireClientThread();if(!recipeMode)throw new IOException("GAME_RECIPE_RENDER_UNAVAILABLE");
            var capture=new GameRecipeRenderCapture();var state=recipeView.read();
            var key=new GameRecipeRenderCapture.Key(state.frame().screen(),recipeView.runtime,recipeView,800,600);
            var headers = new java.util.ArrayList<>(GameRecipePageTest.headers());
            if (recipeNavigations > 0) headers.set(0,new GameRecipeHeaders.Label("category","text","Synthetic category " + recipeNavigations));
            capture.beginFrame(key);capture.headers(headers);capture.controls(recipeControls);capture.beginLayouts(this);
            if (recipeNavigations == 0) { capture.layoutPredicate(this, this, true); capture.drawn(this,GameRecipePageTest.layout()); }
            capture.layoutPredicate(this, this, false); capture.endLayouts(this);capture.finishFrame(key);
            return new GameRecipePage().page(new GameRecipePage.Source() {
                public java.util.List<GameRecipeHeaders.Label> headers() throws IOException {return capture.headers(key);}
                public java.util.List<GameRecipeControls.Control> controls() throws IOException {return capture.controls(key);}
                public GameQuestScreen.Snapshot screen()throws IOException{return recipeView.read();}
                public java.util.List<GameRecipeSlots.Layout> layouts()throws IOException{return capture.copied(key);}
            });
        }
        private GameRecipeNavigation.Port recipeNavigation() {
            return new GameRecipeNavigation.Port() {
                public GameRecipeNavigation.State read() throws IOException {
                    var page=recipePage();return new GameRecipeNavigation.State(recipeView.read(),SettingsJson.string(page,"revision"),recipeFrame,recipeControls);
                }
                public void ready(GameRecipeNavigation.State state)throws IOException {recipeInput.requireIdle();}
                public void checkControl(GameRecipeNavigation.State state,int index)throws IOException {requireClientThread();}
                private void route(GameRecipeNavigation.State state,int index,String mode)throws IOException {
                    var gesture=recipeInput.current();var input=new Object();var screen=state.screen().frame().screen();
                    gesture.prepare(mode);gesture.start(recipeRouter,screen,input,mode);
                    gesture.button(screen,input,recipeHandlers.get(index),recipeHandlers.get(index));
                    gesture.end(recipeRouter,screen,input,true);gesture.finish(true);
                }
                public void preview(GameRecipeNavigation.State state,int index)throws IOException {
                    recipeInput.acquire(new GameRecipeInput.Binding(recipeRouter,recipeControls.stream().map(GameRecipeControls.Control::widget).toList(),
                        recipeHandlers),state.screen().frame().screen(),index);route(state,index,"SIMULATE");
                }
                public void requirePreview()throws IOException {recipeInput.current().requirePreview();}
                public void execute(GameRecipeNavigation.State state,int index)throws IOException {
                    route(state,index,"EXECUTE");recipeHistory.push(recipeNavigations);recipeNavigations++;recipeFrame=null;
                }
                public void checkHistory(GameRecipeNavigation.State state)throws IOException {requireClientThread();recipeInput.requireIdle();}
                public void historyBack(GameRecipeNavigation.State state)throws IOException {
                    checkHistory(state);if(!recipeHistory.isEmpty())recipeNavigations=recipeHistory.pop();recipeFrame=null;
                }
                public GameRecipeNavigation.State after()throws IOException {recipeFrame=new Object();return read();}
            };
        }
        public JsonObject questText(GameQuestText.Query query) throws IOException {
            requireClientThread();return new GameQuestText().page(query,GameQuestTextTest.fixtureSource());
        }
        public JsonObject quests(GameQuestCatalog.Query query) throws IOException {
            return new GameQuestCatalog(()->0).page(query,GameQuestCatalogTest.fixture(query));
        }
        public JsonObject recipeQuery(GameRecipeQuery.Query query) throws IOException {
            requireClientThread();
            var source = new GameRecipeQueryTest.Source();
            if (!query.crafting()) {
                source.entries.add(new GameRecipeQuery.Candidate() {
                    public boolean visible() { return true; }
                    public String id() { return "fixture:machine"; }
                    public boolean bookUnlocked() { throw new AssertionError("machine book authority"); }
                    public JsonObject definition() throws IOException { return GameMachineRecipeTest.fixture(query.category()); }
                });
                return new GameRecipeQuery(() -> 0).query(query, source);
            }
            source.entries.add(GameRecipeQueryTest.candidate("fixture:expert",false,null));
            source.entries.add(GameRecipeQueryTest.candidate("fixture:unsupported",true,"MECHANIC_UNSUPPORTED"));
            return new GameRecipeQuery(() -> 0).query(query,source);
        }
        public void activeRequest(String id) { active = id; }
        public void resetObservations() { pages.reset(); }
        public JsonObject snapshot(String id) throws IOException { return observe(id); }
        public void validate(GameBatch batch, JsonObject snapshot) throws IOException {
            if (batch.revision != lastRevision) throw new IOException("REVISION_CONFLICT");
        }
        public GameActionLane.Motor begin(GameBatch batch, JsonObject snapshot, GameActionLane.Emitter emitter) throws IOException {
            if(batch.kind.equals("quest_ui"))return GameQuestOpen.start(questOpen,GameQuestOpen.Request.read(batch.action),emitter);
            if(batch.kind.equals("quest_navigate"))return GameQuestNavigation.start(recipeMode && questTask.menu!=null?recipeView:questNavigation,GameQuestNavigation.Request.read(batch.action),emitter);
            if(batch.kind.equals("recipe_navigate"))return GameRecipeNavigation.start(recipeNavigation(),GameRecipeNavigation.Request.read(batch.action),emitter);
            if(batch.kind.equals("quest_task"))return GameQuestTaskOpen.start(recipeMode?recipeView:questTask,GameQuestTaskOpen.Request.read(batch.action),emitter);
            if(batch.kind.equals("quest_reward"))return GameQuestRewardOpen.start(questReward,GameQuestRewardOpen.Request.read(batch.action),emitter);
            if(batch.kind.equals("quest_menu"))return GameQuestMenuAction.start(questReward.menu!=null?choiceMenu:questMenuAction,GameQuestMenuAction.Request.read(batch.action),emitter);
            emitter.invoke(() -> x += 1);
            return ignored -> !hold;
        }
        public void releaseInputs() throws IOException {recipeInput.release(router -> {});}
        public void requireClientThread() throws IOException {
            if (Thread.currentThread() != owner) throw new IOException("CLIENT_THREAD_REQUIRED");
        }
        public JsonObject observe(String cursor) throws IOException {
            requireClientThread();
            if (cursor != null) return pages.page(cursor, "minecraft:overworld");
            long captured = pages.beginCapture();
            JsonObject state = JsonParser.parseString("""
                {"dimension":"minecraft:overworld","position":{"x":-1.25,"y":65.0,"z":2.5},
                 "yaw":1.2,"pitch":-0.5,"health":20.0,"food":20.0,"inventory":[],"window":null,
                 "active_request_id":null,"connected":true}
                """).getAsJsonObject();
            state.getAsJsonObject("position").addProperty("x", x);
            state.addProperty("active_request_id", active);
            JsonArray blocks = new JsonArray();
            var eye = new GameVisibility.Point(-1.25, 66.62, 2.5);
            String at = GamePages.utc(Instant.now());
            for (var cell : GameVisibility.capture(eye, (x, y, z) ->
                    new GameVisibility.Cell(x, y, z, y == 64 ? "fixture:floor" : "minecraft:air", y != 64))) {
                JsonObject value = new JsonObject(), position = new JsonObject();
                position.addProperty("x", cell.x()); position.addProperty("y", cell.y()); position.addProperty("z", cell.z());
                value.add("position", position); value.addProperty("block_id", cell.id());
                value.addProperty("observed_at", at); blocks.add(value);
            }
            JsonObject result = pages.capture(state, blocks, new JsonArray(), captured);
            lastRevision = SettingsJson.integer(result, "state_revision"); return result;
        }
    }
    public static void main(String[] args) throws Exception {
        if (args.length < 1 || args.length > 4) throw new IllegalArgumentException("TEST_ARGUMENTS_REQUIRED");
        Port port = new Port(args.length >= 3 && args[2].equals("hold"));
        Path root = args.length >= 2 ? Path.of(args[1]) : null;
        try (var lane = root == null ? null : new GameActionLane(root, "a".repeat(64),
                    GameActionLane.Authority.read(SettingsJson.read(SettingsFiles.readOptions(root.resolve("game-authority.json")))), port)) {
            var protocol = new NativeGameProtocol(port, lane);
            try (var bridge = new SettingsHttpBridge(protocol::execute, protocol)) {
            SettingsFiles.writeNew(Path.of(args[0]), (bridge.descriptor("a".repeat(64)) + "\n").getBytes(StandardCharsets.UTF_8));
                while (System.in.available() == 0) {
                    if (args.length == 4 && Files.exists(Path.of(args[3]))) {
                        Thread.sleep(60000); // Test-only frozen client thread, HTTP thread still responds.
                    }
                    bridge.drain(); if (lane != null) lane.tick(); Thread.sleep(5);
                }
            }
        }
    }
}
