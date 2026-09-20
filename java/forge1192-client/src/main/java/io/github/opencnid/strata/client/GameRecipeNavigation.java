package io.github.opencnid.strata.client;

import com.google.gson.JsonObject;
import java.io.IOException;
import java.util.List;

/** One ordinary page/category gesture or Back callback, with copied-page authority and a fresh rendered result. */
final class GameRecipeNavigation {
    static final String POLICY = "jei-current-page-controls-history-fresh-frame200/2";
    static final int MAX_WAIT_TICKS = 200;
    record Request(String control, long source, long generation, long revision, String page) {
        static Request read(JsonObject value) throws IOException {
            SettingsJson.fields(value, "kind", "source", "control", "source_generation",
                "expected_screen_generation", "expected_screen_revision", "expected_page_revision");
            if (!"recipe_navigate".equals(SettingsJson.string(value, "kind"))
                    || !"jei".equals(SettingsJson.string(value, "source"))) throw invalid();
            var control = SettingsJson.string(value, "control");
            if (!GameRecipeControls.KINDS.contains(control) && !"history_back".equals(control)) throw invalid();
            return new Request(control, SettingsJson.integer(value, "source_generation"),
                SettingsJson.integer(value, "expected_screen_generation"), SettingsJson.integer(value, "expected_screen_revision"),
                GameBatch.digest(value, "expected_page_revision"));
        }
        int index() { return GameRecipeControls.KINDS.indexOf(control); }
        boolean history() { return "history_back".equals(control); }
        int minimum() { return history() ? 3 : 4; }
    }
    record State(GameQuestScreen.Snapshot screen, String page, Object frame, List<GameRecipeControls.Control> controls) {
        State { controls = List.copyOf(controls); }
        void validate() throws IOException {
            if (screen == null || screen.frame() == null || frame == null || page == null || !page.matches("[a-f0-9]{64}")
                    || screen.generation() < 0 || screen.revision() < 0 || screen.generation() > 9007199254740991L
                    || screen.revision() > 9007199254740991L || controls.size() != 4) throw invalid();
            screen.frame().validate();
            if (!"task_recipes".equals(screen.frame().kind())) throw changed();
            for (int i = 0; i < 4; i++) {
                var control = controls.get(i); control.json();
                if (!GameRecipeControls.KINDS.get(i).equals(control.kind())) throw invalid();
                for (int j = 0; j < i; j++) if (controls.get(j).widget() == control.widget()) throw invalid();
            }
        }
        boolean sameContext(State other) {
            return other != null && screen.generation() == other.screen.generation()
                && screen.revision() == other.screen.revision() && screen.frame().same(other.screen.frame());
        }
        boolean samePage(State other) { return sameContext(other) && page.equals(other.page) && controls.equals(other.controls); }
    }
    interface Port {
        State read() throws IOException;
        void ready(State state) throws IOException;
        void checkControl(State state, int index) throws IOException;
        void preview(State state, int index) throws IOException;
        void requirePreview() throws IOException;
        void execute(State state, int index) throws IOException;
        default void checkHistory(State state) throws IOException { throw new IOException("GAME_RECIPE_HISTORY_UNSUPPORTED"); }
        default void historyBack(State state) throws IOException { throw new IOException("GAME_RECIPE_HISTORY_UNSUPPORTED"); }
        // Only absence of a complete fresh frame may return null; source/input failures must throw.
        State after() throws IOException;
    }
    static State validate(Port port, Request request) throws IOException {
        var before = port.read(); before.validate();
        int index = request.index();
        if (index < 0 && !request.history() || before.screen.frame().source() != request.source || before.screen.generation() != request.generation
                || before.screen.revision() != request.revision || !before.page.equals(request.page)) throw changed();
        if (request.history()) port.checkHistory(before);
        else {
            if (!"enabled".equals(before.controls.get(index).state())) throw new IOException("GAME_RECIPE_CONTROL_UNAVAILABLE");
            port.checkControl(before, index);
        }
        var after = port.read(); after.validate();
        if (!before.samePage(after)) throw changed();
        return after;
    }
    static GameActionLane.Motor start(Port port, Request request, GameActionLane.Emitter emitter) throws IOException {
        var before = validate(port, request); if (!request.history()) port.ready(before);
        Object[] callbackFrame = {null};
        emitter.invoke(() -> {
            var now = validate(port, request);
            if (!before.samePage(now)) throw changed();
            if (request.history()) { callbackFrame[0] = now.frame; port.historyBack(now); }
            else { port.ready(now); port.preview(now, request.index()); }
        });
        return new GameActionLane.Motor() {
            private int stage = request.history() ? 1 : 0, waited;
            private boolean failed;
            private Object releasedFrame = callbackFrame[0];
            public boolean tick(GameActionLane.Emitter emit) throws IOException {
                if (failed) throw new IOException("GAME_RECIPE_INPUT_UNCONFIRMED");
                if (stage == 2) return true;
                try {
                    if (stage == 0) {
                        emit.invoke(() -> {
                            port.requirePreview(); var now = validate(port, request);
                            if (!before.samePage(now)) throw changed();
                            releasedFrame = now.frame; port.execute(now, request.index());
                        });
                        stage = 1; return false;
                    }
                    if (waited >= MAX_WAIT_TICKS) throw new IOException("GAME_RECIPE_RENDER_TIMEOUT");
                    emit.invoke(() -> {}); waited++;
                    var after = port.after();
                    if (after == null) return false;
                    after.validate();
                    if (!before.sameContext(after)) throw changed();
                    if (after.frame == releasedFrame) return false;
                    // Ordinary dispatch and a fresh frame confirm input, never recipe progress.
                    stage = 2; return true;
                } catch (IOException | RuntimeException error) { failed = true; throw error; }
            }
        };
    }
    private static IOException invalid() { return new IOException("GAME_RECIPE_NAVIGATION_INVALID"); }
    private static IOException changed() { return new IOException("GAME_RECIPE_PAGE_CHANGED"); }
}
