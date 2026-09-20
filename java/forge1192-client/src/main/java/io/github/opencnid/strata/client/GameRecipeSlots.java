package io.github.opencnid.strata.client;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

/** Copies only actual draw operands; no recipe lookup, alternate-ingredient walk or mutable payloads. */
final class GameRecipeSlots {
    static final int MAX_SLOTS = 128;
    record Rect(int x, int y, int width, int height) {
        void validate() throws IOException {
            if (Math.abs((long)x) > 1048576 || Math.abs((long)y) > 1048576
                    || width < 0 || height < 0 || width > 32768 || height > 32768) throw invalid();
        }
        boolean contains(Rect other) {
            return other.width > 0 && other.height > 0 && other.x >= x && other.y >= y
                && (long)other.x + other.width <= (long)x + width
                && (long)other.y + other.height <= (long)y + height;
        }
        boolean intersects(Rect other) {
            return width > 0 && height > 0 && other.width > 0 && other.height > 0
                && (long)x < (long)other.x + other.width && (long)other.x < (long)x + width
                && (long)y < (long)other.y + other.height && (long)other.y < (long)y + height;
        }
    }
    record Display(String kind, String id, int amount) {
        void validate() throws IOException {
            if (kind == null) throw invalid();
            if (kind.equals("empty") || kind.equals("unsupported")) {
                if (id != null || amount != 0) throw invalid();
            } else if (!(kind.equals("item") || kind.equals("fluid")) || !identifier(id) || amount < 1) throw invalid();
        }
        JsonObject json() throws IOException {
            validate(); var result = new JsonObject(); result.addProperty("kind", kind);
            if (id != null) { result.addProperty("id", id); result.addProperty("amount", amount); }
            return result;
        }
    }
    record Slot(int index, String role, Display display) {
        JsonObject json() throws IOException {
            if (index < 0 || index >= MAX_SLOTS || role == null
                    || !List.of("input", "output", "catalyst", "render_only").contains(role) || display == null) throw invalid();
            var result = new JsonObject(); result.addProperty("index", index); result.addProperty("role", role);
            result.add("display", display.json()); return result;
        }
    }
    record Layout(String category, List<Slot> slots, boolean clipped) {
        Layout { slots = List.copyOf(slots); }
        JsonObject json() throws IOException {
            if (!identifier(category) || slots.size() > MAX_SLOTS) throw invalid();
            var result = new JsonObject(); result.addProperty("category_id", category); result.addProperty("clipped", clipped);
            var values = new JsonArray(); int previous = -1;
            for (Slot slot : slots) {
                if (slot == null || slot.index <= previous || !clipped && slot.index != previous + 1) throw invalid();
                previous = slot.index; values.add(slot.json());
            }
            result.add("slots", values); return result;
        }
    }
    interface Reader<T> { T read() throws IOException; }
    private Object layout, slot, selected;
    private Rect viewport, area;
    private String category, role;
    private List<Object> expected;
    private final ArrayList<Slot> copied = new ArrayList<>();
    private int index;
    private boolean visible, selectionSeen, operand, clipped, invalid;
    private Display display;

    void begin(Object identity, Rect viewport, Rect area, String category, List<?> expected) throws IOException {
        if (layout != null) { invalid = true; throw invalid(); }
        clear();
        if (identity == null || viewport == null || area == null || !identifier(category)
                || expected == null || expected.size() > MAX_SLOTS) throw invalid();
        viewport.validate(); area.validate();
        var identities = new java.util.IdentityHashMap<Object, Boolean>();
        for (Object item : expected) if (item == null || identities.put(item, true) != null) throw invalid();
        this.layout = identity; this.viewport = viewport; this.area = area; this.category = category;
        this.expected = new ArrayList<>(expected);
    }
    void beginSlot(Object identity, Rect relative, Reader<String> role) throws IOException {
        try {
            require(layout != null && !invalid && slot == null && index < expected.size() && expected.get(index) == identity);
            relative.validate();
            var absolute = new Rect(Math.addExact(area.x, relative.x), Math.addExact(area.y, relative.y), relative.width, relative.height);
            absolute.validate();
            slot = identity; visible = viewport.contains(absolute) && area.contains(absolute);
            clipped |= !visible; selectionSeen = false; selected = null; operand = false; display = new Display("empty", null, 0);
            this.role = visible ? role.read() : null;
        } catch (IOException | RuntimeException error) { invalid = true; throw error; }
    }
    void selection(Object identity, Object selected) throws IOException {
        try {
            require(layout != null && !invalid && slot == identity && slot != null && !selectionSeen);
            selectionSeen = true; this.selected = selected;
        } catch (IOException | RuntimeException error) { invalid = true; throw error; }
    }
    boolean activeSlot(Object identity) { return layout != null && !invalid && slot != null && slot == identity; }
    void ingredient(Object identity, Object selected, Reader<Display> copy) throws IOException {
        try {
            require(layout != null && !invalid && slot == identity && slot != null && selectionSeen
                && selected != null && this.selected == selected && !operand);
            operand = true;
            if (visible) { display = copy.read(); require(display != null); display.validate(); }
        } catch (IOException | RuntimeException error) { invalid = true; throw error; }
    }
    void endSlot(Object identity) throws IOException {
        try {
            require(layout != null && !invalid && slot != null && slot == identity && selectionSeen && operand == (selected != null));
            if (visible) { var value = new Slot(index, role, display); value.json(); copied.add(value); }
            index++; slot = null; display = null; role = null;
        } catch (IOException | RuntimeException error) { invalid = true; throw error; }
    }
    Layout finish(Object identity) throws IOException {
        try {
            require(layout == identity && layout != null && !invalid && slot == null && index == expected.size());
            var result = new Layout(category, copied, clipped); result.json(); return result;
        } finally { clear(); }
    }
    void clear() {
        layout = null; slot = null; selected = null; viewport = null; area = null; category = null; role = null;
        expected = null; copied.clear(); index = 0; visible = false; selectionSeen = false; operand = false; clipped = false; invalid = false; display = null;
    }
    private static boolean identifier(String value) { return value != null && value.length() <= 256
        && value.matches("[a-z0-9_.-]+:[a-z0-9_./-]+"); }
    private static void require(boolean value) throws IOException { if (!value) throw invalid(); }
    private static IOException invalid() { return new IOException("GAME_RECIPE_SLOT_CAPTURE_INVALID"); }
}
