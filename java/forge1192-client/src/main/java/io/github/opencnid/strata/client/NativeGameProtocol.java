package io.github.opencnid.strata.client;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import java.io.IOException;

/** Private development seam. Mutations require a separately supplied, durable operator authority. */
final class NativeGameProtocol implements SettingsHttpBridge.Protocol {
    static final String PROFILE = "forge1192-structured-development/1";
    interface RuntimePort {
        void requireClientThread() throws IOException;
        JsonObject observe(String cursor) throws IOException;
        String bodyFingerprint() throws IOException;
        long connectionGeneration();
        default JsonObject recipes(int after) throws IOException { throw new IOException("MECHANIC_UNSUPPORTED"); }
        default JsonObject recipeQuery(GameRecipeQuery.Query query) throws IOException { throw new IOException("MECHANIC_UNSUPPORTED"); }
        default JsonObject quests(GameQuestCatalog.Query query) throws IOException { throw new IOException("MECHANIC_UNSUPPORTED"); }
        default JsonObject questText(GameQuestText.Query query) throws IOException { throw new IOException("MECHANIC_UNSUPPORTED"); }
        default JsonObject questComponents(GameQuestComponents.Query query) throws IOException {throw new IOException("MECHANIC_UNSUPPORTED");}
        default JsonObject questMenu(GameQuestMenu.Query query)throws IOException {throw new IOException("MECHANIC_UNSUPPORTED");}
        default JsonObject questScreen()throws IOException {throw new IOException("MECHANIC_UNSUPPORTED");}
        default JsonObject recipePage()throws IOException {throw new IOException("MECHANIC_UNSUPPORTED");}
    }
    private final RuntimePort runtime;
    private final GameActionLane lane;
    NativeGameProtocol(RuntimePort runtime) { this(runtime, null); }
    NativeGameProtocol(RuntimePort runtime, GameActionLane lane) { this.runtime = runtime; this.lane = lane; }
    public String path() { return "/v1/game"; }
    public String connectionSchema() { return "strata/NativeGameConnection/1"; }
    public JsonObject read(String text) throws IOException { return SettingsJson.readGame(text); }
    public boolean urgent(JsonObject request) {
        return java.util.Set.of("cancel", "stop_all").contains(request.get("operation").getAsString());
    }

    public void validate(JsonObject request, String session, long now) throws IOException {
        SettingsJson.fields(request, "schema", "request_id", "session_id", "deadline_unix_ms", "operation", "args");
        if (!"strata/NativeGameRequest/1".equals(SettingsJson.string(request, "schema"))) throw new IOException("SCHEMA_UNSUPPORTED");
        NativeSettingsProtocol.identifier(SettingsJson.string(request, "request_id"));
        if (!session.equals(SettingsJson.string(request, "session_id"))) throw new IOException("GAME_SESSION_MISMATCH");
        long deadline = SettingsJson.integer(request, "deadline_unix_ms");
        if (deadline <= now || deadline - now > 30000) throw new IOException("GAME_DEADLINE_INVALID");
        if (!request.get("args").isJsonObject()) throw new IOException("GAME_ARGS_INVALID");
        JsonObject args = request.getAsJsonObject("args");
        switch (SettingsJson.string(request, "operation")) {
            case "capabilities", "identity", "quest_screen", "recipe_page" -> SettingsJson.fields(args);
            case "recipes" -> {
                SettingsJson.fields(args, "after");
                if (SettingsJson.integer(args, "after") > 10000) throw new IOException("GAME_RECIPE_BOUNDS");
            }
            case "recipe_query" -> GameRecipeQuery.Query.read(args);
            case "quests" -> GameQuestCatalog.Query.read(args);
            case "quest_text" -> GameQuestText.Query.read(args);
            case "quest_components" -> GameQuestComponents.Query.read(args);
            case "quest_menu" -> GameQuestMenu.Query.read(args);
            case "observe", "observe_bound" -> {
                SettingsJson.fields(args, "cursor");
                if (!args.get("cursor").isJsonNull()) NativeSettingsProtocol.identifier(SettingsJson.string(args, "cursor"));
            }
            default -> {
                if (lane == null) throw new IOException("CAPABILITY_MISSING");
                switch (SettingsJson.string(request, "operation")) {
                    case "lane_status", "stop_all", "authority" -> SettingsJson.fields(args);
                    case "arm", "renew" -> {
                        if (SettingsJson.string(request, "operation").equals("arm")) {
                            SettingsJson.fields(args, "epoch", "lease_id", "lease_until_unix_ms", "expected_fence_token");
                            GameBatch.id(args, "expected_fence_token");
                        } else SettingsJson.fields(args, "epoch", "lease_id", "lease_until_unix_ms");
                        SettingsJson.integer(args, "epoch"); GameBatch.id(args, "lease_id"); SettingsJson.integer(args, "lease_until_unix_ms");
                    }
                    case "deliver" -> {
                        SettingsJson.fields(args, "observation_id", "snapshot_id", "state_revision");
                        GameBatch.id(args, "observation_id"); GameBatch.id(args, "snapshot_id"); SettingsJson.integer(args, "state_revision");
                    }
                    case "act" -> {
                        SettingsJson.fields(args, "batch");
                        if (!args.get("batch").isJsonObject()) throw new IOException("GAME_BATCH_INVALID");
                        new GameBatch(args.getAsJsonObject("batch"));
                    }
                    case "action_status", "cancel" -> { SettingsJson.fields(args, "request_id"); GameBatch.id(args, "request_id"); }
                    default -> throw new IOException("CAPABILITY_MISSING");
                }
            }
        }
    }

    JsonObject execute(JsonObject request) throws IOException {
        runtime.requireClientThread();
        JsonObject args = request.getAsJsonObject("args");
        return switch (SettingsJson.string(request, "operation")) {
            case "capabilities" -> capabilities(lane != null);
            case "identity" -> {
                JsonObject value = new JsonObject(); value.addProperty("schema", "strata/NativeGameIdentity/1");
                value.addProperty("body_fingerprint", runtime.bodyFingerprint());
                value.addProperty("connection_generation", runtime.connectionGeneration()); yield value;
            }
            case "recipes" -> {
                var value = runtime.recipes(Math.toIntExact(SettingsJson.integer(args, "after")));
                value.addProperty("schema", "strata/NativeRecipeList/1");
                value.addProperty("body_fingerprint", runtime.bodyFingerprint());
                value.addProperty("connection_generation", runtime.connectionGeneration()); yield value;
            }
            case "recipe_query" -> {
                var value = runtime.recipeQuery(GameRecipeQuery.Query.read(args));
                value.addProperty("schema", "strata/NativeRecipeQuery/1");
                value.addProperty("body_fingerprint", runtime.bodyFingerprint());
                value.addProperty("connection_generation", runtime.connectionGeneration()); yield value;
            }
            case "quest_components" -> {
                var value=runtime.questComponents(GameQuestComponents.Query.read(args));
                value.addProperty("schema","strata/NativeQuestComponents/1");
                value.addProperty("body_fingerprint",runtime.bodyFingerprint());
                value.addProperty("connection_generation",runtime.connectionGeneration());yield value;
            }
            case "quest_menu" -> {
                var value=runtime.questMenu(GameQuestMenu.Query.read(args));
                value.addProperty("schema","strata/NativeQuestMenu/1");
                value.addProperty("body_fingerprint",runtime.bodyFingerprint());
                value.addProperty("connection_generation",runtime.connectionGeneration());yield value;
            }
            case "quest_screen" -> {
                var value=runtime.questScreen();value.addProperty("schema","strata/NativeQuestScreen/1");
                value.addProperty("body_fingerprint",runtime.bodyFingerprint());value.addProperty("connection_generation",runtime.connectionGeneration());yield value;
            }
            case "recipe_page" -> {
                var value=runtime.recipePage();value.addProperty("schema","strata/NativeRecipePage/4");
                value.addProperty("body_fingerprint",runtime.bodyFingerprint());value.addProperty("connection_generation",runtime.connectionGeneration());yield value;
            }
            case "quest_text" -> {
                var value=runtime.questText(GameQuestText.Query.read(args));
                value.addProperty("schema","strata/NativeQuestText/1");
                value.addProperty("body_fingerprint",runtime.bodyFingerprint());
                value.addProperty("connection_generation",runtime.connectionGeneration());yield value;
            }
            case "quests" -> {
                var value=runtime.quests(GameQuestCatalog.Query.read(args));
                value.addProperty("schema","strata/NativeQuestPage/1");
                value.addProperty("body_fingerprint",runtime.bodyFingerprint());
                value.addProperty("connection_generation",runtime.connectionGeneration());yield value;
            }
            case "observe" -> {
                yield runtime.observe(args.get("cursor").isJsonNull() ? null : SettingsJson.string(args, "cursor"));
            }
            case "observe_bound" -> {
                JsonObject snapshot = runtime.observe(args.get("cursor").isJsonNull() ? null : SettingsJson.string(args, "cursor"));
                JsonObject value = new JsonObject(); value.addProperty("schema", "strata/NativeBoundSnapshot/1");
                value.add("snapshot", snapshot); value.addProperty("body_fingerprint", runtime.bodyFingerprint());
                value.addProperty("connection_generation", runtime.connectionGeneration()); yield value;
            }
            default -> {
                if (lane == null) throw new IOException("CAPABILITY_MISSING");
                yield switch (SettingsJson.string(request, "operation")) {
                    case "lane_status" -> lane.health();
                    case "authority" -> lane.authority();
                    case "stop_all" -> lane.stopAll();
                    case "arm" -> lane.arm(SettingsJson.integer(args, "epoch"), GameBatch.id(args, "lease_id"), SettingsJson.integer(args, "lease_until_unix_ms"), GameBatch.id(args, "expected_fence_token"));
                    case "renew" -> lane.renew(SettingsJson.integer(args, "epoch"), GameBatch.id(args, "lease_id"), SettingsJson.integer(args, "lease_until_unix_ms"));
                    case "deliver" -> lane.deliver(GameBatch.id(args, "observation_id"), GameBatch.id(args, "snapshot_id"), SettingsJson.integer(args, "state_revision"));
                    case "act" -> lane.accept(args.getAsJsonObject("batch"));
                    case "action_status" -> lane.status(GameBatch.id(args, "request_id"));
                    case "cancel" -> lane.cancel(GameBatch.id(args, "request_id"));
                    default -> throw new IOException("CAPABILITY_MISSING");
                };
            }
        };
    }

    static JsonObject capabilities() {
        return capabilities(false);
    }
    static JsonObject capabilities(boolean mutation) {
        JsonObject value = new JsonObject();
        value.addProperty("schema", "strata/NativeGameCapabilities/1");
        value.addProperty("profile", PROFILE);
        value.addProperty("backend", "forge_client");
        value.addProperty("track", "structured-actions/v1");
        value.addProperty("observation_policy", GameVisibility.POLICY);
        value.addProperty("campaign_admission", false);
        value.addProperty("conformance", "unverified");
        value.addProperty("operator_development_only", true);
        JsonArray operations = new JsonArray(); operations.add("capabilities"); operations.add("observe"); operations.add("identity"); operations.add("observe_bound"); operations.add("recipes"); operations.add("recipe_query");
        operations.add("quests"); operations.add("quest_text"); operations.add("quest_components");operations.add("quest_menu");operations.add("quest_screen");operations.add("recipe_page");
        if (mutation) for (String operation : java.util.List.of("arm", "renew", "deliver", "act", "action_status", "cancel", "stop_all", "lane_status", "authority")) operations.add(operation);
        value.add("operations", operations);
        JsonArray actions = new JsonArray();
        if (mutation) GameBatch.ACTIONS.stream().sorted().forEach(actions::add);
        value.add("actions", actions);
        value.addProperty("native_action_policy", "durable-intent-client-thread-nineteen-actions/2");
        value.addProperty("block_target_policy", GameBlockTarget.POLICY);
        value.addProperty("menu_close_policy", GameMenuClose.POLICY);
        value.addProperty("recipe_policy", GameRecipes.POLICY);
        value.addProperty("recipe_query_policy", GameRecipeQuery.POLICY);
        value.addProperty("recipe_page_policy", GameRecipePage.POLICY);
        value.addProperty("recipe_navigation_policy", GameRecipeNavigation.POLICY);
        value.addProperty("quest_policy",GameQuestCatalog.POLICY);
        value.addProperty("quest_text_policy",GameQuestText.POLICY);
        value.addProperty("quest_components_policy",GameQuestComponents.POLICY);
        value.addProperty("quest_menu_policy",GameQuestMenu.POLICY);
        value.addProperty("quest_open_policy",GameQuestOpen.POLICY);
        value.addProperty("quest_navigation_policy",GameQuestScreen.POLICY);
        value.addProperty("quest_reward_policy",GameQuestRewardOpen.POLICY);
        value.addProperty("quest_task_policy",GameQuestTaskOpen.POLICY);
        value.addProperty("quest_menu_action_policy",GameQuestMenuAction.POLICY);
        value.addProperty("crafting_policy", GameCrafting.POLICY);
        value.addProperty("manual_crafting_policy", GameRecipeGrid.POLICY);
        value.addProperty("machine_observation_policy", GameMachineMenu.POLICY);
        value.addProperty("machine_inventory_policy", GameMachineInventory.POLICY);
        value.addProperty("machine_input_policy", GameMachineMenu.INPUT_POLICY);
        value.addProperty("navigation_policy", GameRoute.POLICY);
        value.addProperty("collision_policy", NativeCollisionView.POLICY);
        value.addProperty("movement_policy", GameMovement.POLICY);
        value.addProperty("keybindings", false);
        value.addProperty("screenshots", false);
        return value;
    }

    public JsonObject response(JsonObject request, String session, String status, JsonObject result, String code) {
        JsonObject response = NativeSettingsProtocol.response(request, session, status, result, code);
        response.addProperty("schema", "strata/NativeGameResponse/1");
        return response;
    }
}
