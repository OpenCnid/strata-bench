package io.github.opencnid.strata.client;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.function.LongSupplier;

/** Current copied draw operands only. Coverage is explicit; no page/recipe lookup or input authority. */
final class GameRecipePage {
    static final String POLICY = "jei-task-drawn-slot-header-controls-empty-loop/4";
    interface Source {
        GameQuestScreen.Snapshot screen() throws IOException;
        List<GameRecipeSlots.Layout> layouts() throws IOException;
        List<GameRecipeHeaders.Label> headers() throws IOException;
        List<GameRecipeControls.Control> controls() throws IOException;
    }
    private final LongSupplier clock;
    GameRecipePage() { this(System::nanoTime); }
    GameRecipePage(LongSupplier clock) { this.clock = clock; }
    JsonObject page(Source source) throws IOException {
        long start = clock.getAsLong();
        var before = source.screen(); valid(before);
        var raw = source.layouts();
        if (raw == null || raw.size() > 32) throw new IOException("GAME_RECIPE_RENDER_BOUNDS");
        var layouts = new java.util.ArrayList<>(raw);
        var rawHeaders = source.headers();
        if (rawHeaders == null || rawHeaders.size() != 2 || rawHeaders.stream().anyMatch(java.util.Objects::isNull)) throw new IOException("GAME_RECIPE_HEADER_INVALID");
        var headers = List.copyOf(rawHeaders); var labelRows = new JsonArray();
        if (!headers.get(0).kind().equals("category") || !headers.get(1).kind().equals("page")) throw new IOException("GAME_RECIPE_HEADER_INVALID");
        for (var label : headers) labelRows.add(label.json());
        var rawControls = source.controls();
        if (rawControls == null || rawControls.size() != 4 || rawControls.stream().anyMatch(java.util.Objects::isNull)) throw new IOException("GAME_RECIPE_CONTROLS_INVALID");
        var controls = List.copyOf(rawControls); var controlRows = new JsonArray();
        for (int i = 0; i < 4; i++) {
            if (!GameRecipeControls.KINDS.get(i).equals(controls.get(i).kind())) throw new IOException("GAME_RECIPE_CONTROLS_INVALID");
            controlRows.add(controls.get(i).json());
        }
        var rows = new JsonArray();
        for (var layout : layouts) {
            if (layout == null) throw new IOException("GAME_RECIPE_RENDER_UNAVAILABLE");
            rows.add(layout.json());
        }
        var after = source.screen(); valid(after);
        if (!before.frame().same(after.frame()) || before.generation() != after.generation() || before.revision() != after.revision()
                || !layouts.equals(source.layouts()) || !headers.equals(source.headers()) || !controls.equals(source.controls())) throw new IOException("GAME_RECIPE_PAGE_CHANGED");
        var result = new JsonObject();
        result.addProperty("policy", POLICY); result.addProperty("source", "jei");
        result.addProperty("coverage", "slot_header_control_draw_operands"); result.addProperty("complete", false);
        result.addProperty("source_generation", before.frame().source());
        result.addProperty("screen_generation", before.generation()); result.addProperty("screen_revision", before.revision());
        result.addProperty("chapter_id", before.frame().chapter()); result.addProperty("quest_id", before.frame().quest());
        result.add("layouts", rows);
        result.add("headers", labelRows);
        result.add("controls", controlRows);
        result.addProperty("revision", KeyOptions.sha256(canonical(result)));
        if (canonical(result).getBytes(StandardCharsets.UTF_8).length > 32768) throw new IOException("GAME_RECIPE_RENDER_BOUNDS");
        long duration = clock.getAsLong() - start;
        if (duration < 0 || duration > 100_000_000L) throw new IOException("GAME_RECIPE_RENDER_UNAVAILABLE");
        return result;
    }
    private static void valid(GameQuestScreen.Snapshot value) throws IOException {
        if (value == null || value.frame() == null) throw new IOException("GAME_RECIPE_RENDER_UNAVAILABLE");
        value.frame().validate();
        if (!value.frame().kind().equals("task_recipes") || value.generation() < 0 || value.revision() < 0
                || value.generation() > 9007199254740991L || value.revision() > 9007199254740991L)
            throw new IOException("GAME_RECIPE_RENDER_UNAVAILABLE");
    }
    // This response contains only bounded strings, booleans, null and safe integers.
    // Gson's U+2028/U+2029 escaping differs from RFC 8785; serialize strings explicitly.
    private static String canonical(JsonElement value) {
        if (value.isJsonObject()) {
            var result = new java.util.ArrayList<String>();
            value.getAsJsonObject().keySet().stream().sorted().forEach(key -> result.add(quote(key) + ":" + canonical(value.getAsJsonObject().get(key))));
            return "{" + String.join(",", result) + "}";
        }
        if (value.isJsonArray()) { var result = new java.util.ArrayList<String>(); for (var item : value.getAsJsonArray()) result.add(canonical(item)); return "[" + String.join(",", result) + "]"; }
        if (value.isJsonNull()) return "null";
        return value.getAsJsonPrimitive().isString() ? quote(value.getAsString()) : value.toString();
    }
    private static String quote(String text) {
        var result = new StringBuilder("\"");
        for (int i = 0; i < text.length(); i++) {
            char c = text.charAt(i);
            switch (c) {
                case '"' -> result.append("\\\""); case '\\' -> result.append("\\\\");
                case '\b' -> result.append("\\b"); case '\f' -> result.append("\\f");
                case '\n' -> result.append("\\n"); case '\r' -> result.append("\\r"); case '\t' -> result.append("\\t");
                default -> { if (c < 32) result.append(String.format(java.util.Locale.ROOT, "\\u%04x", (int)c)); else result.append(c); }
            }
        }
        return result.append('"').toString();
    }
}
