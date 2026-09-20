package io.github.opencnid.strata.client;

import com.google.gson.JsonObject;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

/** Copied button draws in the exact pinned header order. Private widgets confer no public input authority. */
final class GameRecipeControls {
    static final List<String> KINDS = List.of("category_next", "category_previous", "page_next", "page_previous");
    record Control(Object widget, String kind, String state, GameRecipeSlots.Rect area) {
        JsonObject json() throws IOException {
            if (widget == null || kind == null || !KINDS.contains(kind) || state == null
                    || !List.of("enabled", "disabled", "clipped").contains(state) || area == null) throw invalid();
            area.validate(); var result = new JsonObject();
            result.addProperty("kind", kind); result.addProperty("state", state); return result;
        }
    }
    private GameRecipeSlots.Rect viewport;
    private final ArrayList<Control> controls = new ArrayList<>();
    private Control drawing;
    private boolean finished;
    void begin(GameRecipeSlots.Rect viewport) throws IOException {
        if (this.viewport != null || viewport == null) throw invalid();
        viewport.validate(); if (viewport.width() < 1 || viewport.height() < 1) throw invalid();
        this.viewport = viewport;
    }
    void beginControl(Object widget, GameRecipeSlots.Rect area, GameRecipeSlots.Reader<Boolean> enabled) throws IOException {
        if (viewport == null || finished || drawing != null || widget == null || controls.size() >= KINDS.size()) throw invalid();
        for (var control : controls) if (control.widget == widget) throw invalid();
        drawing = copy(widget, KINDS.get(controls.size()), area, enabled);
    }
    void endControl(Object widget, GameRecipeSlots.Rect area, GameRecipeSlots.Reader<Boolean> enabled) throws IOException {
        if (drawing == null || drawing.widget != widget) throw invalid();
        var after = copy(widget, drawing.kind, area, enabled);
        if (!drawing.equals(after)) throw invalid();
        controls.add(drawing); drawing = null;
    }
    private Control copy(Object widget, String kind, GameRecipeSlots.Rect area, GameRecipeSlots.Reader<Boolean> enabled) throws IOException {
        if (area == null) throw invalid(); area.validate();
        String state = "clipped";
        if (viewport.contains(area)) {
            var value = enabled.read(); if (value == null) throw invalid(); state = value ? "enabled" : "disabled";
        }
        return new Control(widget, kind, state, area);
    }
    List<Control> finish() throws IOException {
        if (viewport == null || finished || drawing != null || controls.size() != KINDS.size()) throw invalid();
        finished = true; return List.copyOf(controls);
    }
    void clear() { viewport = null; controls.clear(); drawing = null; finished = false; }
    private static IOException invalid() { return new IOException("GAME_RECIPE_CONTROLS_INVALID"); }
}
