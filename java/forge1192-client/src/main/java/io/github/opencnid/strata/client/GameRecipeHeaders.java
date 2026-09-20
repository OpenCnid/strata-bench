package io.github.opencnid.strata.client;

import com.google.gson.JsonObject;
import java.io.IOException;
import java.util.List;

/** Actual header draw operands in native order; no stored full title or recipe-count lookup. */
final class GameRecipeHeaders {
    record Label(String kind, String state, String text) {
        JsonObject json() throws IOException {
            if (kind == null || state == null || !List.of("category", "page").contains(kind) || !List.of("text", "clipped", "unsupported").contains(state)
                    || state.equals("text") != (text != null)) throw invalid();
            if (text != null) GameQuestText.bounded(text, 1024);
            var result = new JsonObject(); result.addProperty("kind", kind); result.addProperty("state", state);
            result.addProperty("text", text); return result;
        }
    }
    record Measured(Label label, int width) {}
    static Label clippedCopy(String kind, GameRecipeSlots.Rect viewport, GameRecipeSlots.Rect box,
                             GameRecipeSlots.Reader<Measured> reader) throws IOException {
        viewport.validate(); box.validate();
        if (!viewport.contains(box)) return new Label(kind, "clipped", null);
        var measured = reader.read();
        if (measured == null || measured.label == null || !kind.equals(measured.label.kind)) throw invalid();
        measured.label.json();
        if (!measured.label.state.equals("text")) {
            if (!measured.label.state.equals("unsupported") || measured.width != 0) throw invalid();
            return measured.label;
        }
        if (measured.width < 0 || measured.width > 32768) throw invalid();
        // Exact pinned centering and ordinary shadow extent. Empty text has no glyphs.
        if (measured.label.text.isEmpty()) return measured.label;
        var glyphs = new GameRecipeSlots.Rect(box.x() + Math.round((box.width() - measured.width) / 2.0f),
            box.y() + Math.round((box.height() - 9) / 2.0f), measured.width + 1, 10);
        glyphs.validate();
        return viewport.contains(glyphs) ? measured.label : new Label(kind, "clipped", null);
    }
    private Object screen, category, operand;
    private int stage;
    private Label title, page, drawing;
    void begin(Object screen) throws IOException {
        if (screen == null || stage != 0) throw invalid();
        this.screen = screen; stage = 1;
    }
    void beginCategory(Object category) throws IOException {
        if (stage != 1 || category == null) throw invalid();
        this.category = category; stage = 2;
    }
    boolean observing() { return stage >= 2 && stage <= 6; }
    boolean controlsStage() { return stage == 7; }
    void beginLabel(Object operand, Label label) throws IOException {
        if (operand == null || label == null || !(stage == 2 && label.kind.equals("category") || stage == 5 && label.kind.equals("page"))) throw invalid();
        label.json(); this.operand = operand; drawing = label; stage++;
    }
    void endLabel(Object operand, Label label) throws IOException {
        if (!(stage == 3 || stage == 6) || this.operand != operand || !drawing.equals(label)) throw invalid();
        if (stage == 3) title = drawing; else page = drawing;
        drawing = null; this.operand = null; stage++;
    }
    void endCategory(Object category) throws IOException {
        if (stage != 4 || this.category != category) throw invalid();
        this.category = null; stage = 5;
    }
    List<Label> beforeLayouts() throws IOException {
        if (stage != 7) throw invalid(); stage = 8; return List.of(title, page);
    }
    void end(Object screen) throws IOException {
        if (stage != 8 || this.screen != screen) throw invalid(); stage = 9;
    }
    boolean complete() { return stage == 9; }
    void clear() { screen = null; category = null; operand = null; stage = 0; title = null; page = null; drawing = null; }
    private static IOException invalid() { return new IOException("GAME_RECIPE_HEADER_INVALID"); }
}
