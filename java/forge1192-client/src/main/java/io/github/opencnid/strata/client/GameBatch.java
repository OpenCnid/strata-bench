package io.github.opencnid.strata.client;

import com.google.gson.JsonObject;
import java.io.IOException;
import java.time.OffsetDateTime;
import java.time.format.DateTimeParseException;
import java.util.Set;

/** Strict implemented subset of the public ActionBatch; no raw events or unchecked dictionaries. */
final class GameBatch {
    static final Set<String> ACTIONS = Set.of("look_at", "dig", "interact_block", "click_slot",
        "use_item", "attack", "interact_entity", "chat", "place", "equip", "move_to", "craft", "close_window", "quest_ui", "quest_navigate", "quest_task", "quest_menu", "quest_reward", "recipe_navigate");
    final JsonObject json, action;
    final String id, observation, lease, campaign, agent, capability;
    final long epoch, sequence, revision, controlRevision, deadline, duration;
    final String kind;

    GameBatch(JsonObject input) throws IOException {
        SettingsJson.fields(input, "schema", "is_example", "campaign_id", "epoch", "seq", "recorded_at", "agent_id",
            "lease_id", "request_id", "observation_id", "mode", "expected_state_revision", "capability_digest",
            "control_revision", "keymap_digest", "deadline_at", "duration_ms", "action", "events", "release_at_end");
        if (!"mcbench/ActionBatch/1".equals(SettingsJson.string(input, "schema"))) throw new IOException("SCHEMA_UNSUPPORTED");
        bool(input, "is_example", false); bool(input, "release_at_end", true);
        if (!"structured".equals(SettingsJson.string(input, "mode")) || !input.get("keymap_digest").isJsonNull()
                || !input.get("events").isJsonArray() || !input.getAsJsonArray("events").isEmpty()) {
            throw new IOException("CAPABILITY_MISSING");
        }
        json = input.deepCopy();
        id = id(input, "request_id"); observation = id(input, "observation_id"); lease = id(input, "lease_id");
        campaign = id(input, "campaign_id"); agent = id(input, "agent_id");
        capability = digest(input, "capability_digest");
        epoch = SettingsJson.integer(input, "epoch"); sequence = SettingsJson.integer(input, "seq");
        revision = SettingsJson.integer(input, "expected_state_revision"); controlRevision = SettingsJson.integer(input, "control_revision");
        deadline = utc(input, "deadline_at"); utc(input, "recorded_at");
        duration = SettingsJson.integer(input, "duration_ms");
        if (!input.get("action").isJsonObject()) throw new IOException("GAME_ACTION_INVALID");
        action = input.getAsJsonObject("action").deepCopy(); kind = SettingsJson.string(action, "kind");
        if (!ACTIONS.contains(kind)) throw new IOException("MECHANIC_UNSUPPORTED");
        if (duration < 1 || duration > (kind.equals("move_to") ? 30000 : 10000) || json.toString().length() > 4096) {
            throw new IOException("GAME_BATCH_BOUNDS");
        }
        switch (kind) {
            case "quest_ui" -> GameQuestOpen.Request.read(action);
            case "quest_navigate" -> GameQuestNavigation.Request.read(action);
            case "recipe_navigate" -> GameRecipeNavigation.Request.read(action);
            case "quest_reward" -> GameQuestRewardOpen.Request.read(action);
            case "quest_task" -> GameQuestTaskOpen.Request.read(action);
            case "quest_menu" -> GameQuestMenuAction.Request.read(action);
            case "move_to" -> { SettingsJson.fields(action, "kind", "target", "tolerance"); target(action); tolerance(action); }
            case "look_at" -> { SettingsJson.fields(action, "kind", "target"); target(action); }
            case "dig", "interact_block" -> {
                SettingsJson.fields(action, "kind", "target", "expected_block_id"); target(action);
                if (!SettingsJson.string(action, "expected_block_id").matches("[a-z0-9_.-]+:[a-z0-9_./-]+")
                        || SettingsJson.string(action, "expected_block_id").length() > 256) throw new IOException("GAME_BLOCK_ID_INVALID");
            }
            case "click_slot" -> {
                SettingsJson.fields(action, "kind", "window_id", "expected_window_revision", "slot", "button", "mode");
                SettingsJson.integer(action, "window_id"); SettingsJson.integer(action, "expected_window_revision");
                if (SettingsJson.integer(action, "slot") > 1023
                        || !Set.of("left", "right").contains(SettingsJson.string(action, "button"))
                        || !Set.of("pickup", "quick_move").contains(SettingsJson.string(action, "mode"))) throw new IOException("GAME_SLOT_INVALID");
            }
            case "craft" -> {
                var names = new java.util.ArrayList<>(java.util.List.of("kind", "recipe_id", "count", "window_id", "expected_window_revision"));
                if (action.has("recipe_selection")) names.add("recipe_selection");
                SettingsJson.fields(action,names.toArray(String[]::new));
                if (action.has("recipe_selection") && !action.get("recipe_selection").isJsonNull()) {
                    if (!action.get("recipe_selection").isJsonObject()) throw new IOException("GAME_RECIPE_QUERY_INVALID");
                    GameRecipeSelection.read(action.getAsJsonObject("recipe_selection"));
                }
                GameRecipes.id(SettingsJson.string(action, "recipe_id"));
                long count = SettingsJson.integer(action, "count");
                SettingsJson.integer(action, "window_id"); SettingsJson.integer(action, "expected_window_revision");
                if (count < 1 || count > 64) throw new IOException("GAME_CRAFT_BOUNDS");
            }
            case "close_window" -> {
                SettingsJson.fields(action, "kind", "window_id", "expected_window_revision");
                SettingsJson.integer(action, "window_id"); SettingsJson.integer(action, "expected_window_revision");
            }
            case "use_item" -> {
                SettingsJson.fields(action, "kind", "hand", "hold_ms");
                long hold = SettingsJson.integer(action, "hold_ms");
                if (!Set.of("main", "off").contains(SettingsJson.string(action, "hand"))
                        || hold > 2000 || hold > duration) throw new IOException("GAME_USE_INVALID");
            }
            case "attack", "interact_entity" -> { SettingsJson.fields(action, "kind", "entity_id"); id(action, "entity_id"); }
            case "chat" -> { SettingsJson.fields(action, "kind", "text"); GameGestures.chat(SettingsJson.string(action, "text")); }
            case "place" -> {
                SettingsJson.fields(action, "kind", "support", "face", "expected_item_id");
                vector(action, "support"); var face = vector(action, "face");
                if (Math.abs(face.x()) + Math.abs(face.y()) + Math.abs(face.z()) != 1
                        || face.x() != Math.rint(face.x()) || face.y() != Math.rint(face.y()) || face.z() != Math.rint(face.z())) {
                    throw new IOException("GAME_FACE_INVALID");
                }
                itemId(action);
            }
            case "equip" -> {
                SettingsJson.fields(action, "kind", "inventory_slot", "expected_item_id", "destination");
                if (SettingsJson.integer(action, "inventory_slot") > 45
                        || !Set.of("hand", "off_hand", "head", "torso", "legs", "feet").contains(SettingsJson.string(action, "destination"))) {
                    throw new IOException("GAME_SLOT_INVALID");
                }
                itemId(action);
            }
            default -> throw new IOException("MECHANIC_UNSUPPORTED");
        }
    }
    static String id(JsonObject object, String key) throws IOException {
        String value = SettingsJson.string(object, key); NativeSettingsProtocol.identifier(value); return value;
    }
    static String digest(JsonObject object, String key) throws IOException {
        String value = SettingsJson.string(object, key);
        if (!value.matches("[0-9a-f]{64}")) throw new IOException("GAME_DIGEST_INVALID"); return value;
    }
    static void bool(JsonObject object, String key, boolean expected) throws IOException {
        var value = object.get(key);
        if (value == null || !value.isJsonPrimitive() || !value.getAsJsonPrimitive().isBoolean()
                || value.getAsBoolean() != expected) throw new IOException("GAME_BOOLEAN_INVALID");
    }
    static long utc(JsonObject object, String key) throws IOException {
        String value = SettingsJson.string(object, key);
        if (value.startsWith("0000-") || !value.matches("[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\\.[0-9]{1,6})?Z")) {
            throw new IOException("GAME_TIMESTAMP_INVALID");
        }
        try { return OffsetDateTime.parse(value).toInstant().toEpochMilli(); }
        catch (DateTimeParseException | ArithmeticException error) { throw new IOException("GAME_TIMESTAMP_INVALID", error); }
    }
    static GameVisibility.Point target(JsonObject action) throws IOException {
        return vector(action, "target");
    }
    static double tolerance(JsonObject action) throws IOException {
        var value = action.get("tolerance");
        if (value == null || !value.isJsonPrimitive() || !value.getAsJsonPrimitive().isNumber()) throw new IOException("GAME_TARGET_INVALID");
        double tolerance = value.getAsDouble();
        if (!Double.isFinite(tolerance) || tolerance <= 0 || tolerance > 1) throw new IOException("GAME_TARGET_INVALID");
        return tolerance;
    }
    static GameVisibility.Point vector(JsonObject action, String field) throws IOException {
        if (!action.has(field) || !action.get(field).isJsonObject()) throw new IOException("GAME_TARGET_INVALID");
        JsonObject p = action.getAsJsonObject(field); SettingsJson.fields(p, "x", "y", "z");
        return new GameVisibility.Point(coordinate(p, "x", 30000000), coordinate(p, "y", 2048), coordinate(p, "z", 30000000));
    }
    private static void itemId(JsonObject action) throws IOException {
        String id = SettingsJson.string(action, "expected_item_id");
        if (id.length() > 256 || !id.matches("[a-z0-9_.-]+:[a-z0-9_./-]+")) throw new IOException("GAME_ITEM_ID_INVALID");
    }
    private static double coordinate(JsonObject p, String key, double limit) throws IOException {
        var value = p.get(key);
        if (!value.isJsonPrimitive() || !value.getAsJsonPrimitive().isNumber()) throw new IOException("GAME_TARGET_INVALID");
        double number = value.getAsDouble();
        if (!Double.isFinite(number) || Math.abs(number) > limit) throw new IOException("GAME_TARGET_INVALID");
        return number;
    }
}
