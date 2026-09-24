package io.github.opencnid.strata.telemetry;

import com.google.gson.JsonNull;
import com.google.gson.JsonObject;
import java.util.Map;
import java.util.TreeMap;

/** Bounded sticky observations, with no game-state writes or raw command data. */
public final class SetupHistory {
    public static final String POLICY = "native-e9e-setup-mutation-watch/6";
    static final String[] ROUTES = {"command_attempt", "actor_mode_change", "operator_add",
        "operator_remove", "operator_reload", "allow_cheats", "world_mode", "world_difficulty",
        "team_deserialize", "party_change", "team_create", "team_reload", "native_stop_command", "global_mode_write", "team_map_write", "team_script_field_write", "script_reflection_overflow", "script_handle_unresolved"};
    private static Monitor monitor;
    private static boolean used;

    // The holder remains private. No reset/resume method is exposed to hooks.
    static synchronized void activate() {
        if (used) throw new IllegalStateException("SETUP_HISTORY_ALREADY_USED");
        used = true; monitor = new Monitor(Thread.currentThread(), 1_000_000);
    }
    public static synchronized void attempt(String route) {
        if (monitor != null) monitor.attempt(route, Thread.currentThread());
    }
    static synchronized void command(Object source, boolean exactStop) {
        if (monitor != null) monitor.command(source, exactStop, Thread.currentThread());
    }
    public static synchronized void stopping(Object source) {
        if (monitor != null) monitor.stopping(source, Thread.currentThread());
    }
    static synchronized JsonObject capture(String phase, String transaction) {
        if (monitor == null) throw new IllegalStateException("SETUP_HISTORY_INACTIVE");
        return monitor.capture(phase, transaction);
    }
    static synchronized JsonObject close() {
        JsonObject result = capture("stop", null); monitor = null; return result;
    }
    static JsonObject support() {
        var result = new JsonObject(); result.addProperty("policy", POLICY);
        result.addProperty("vanilla_hooks_verified", marked(
            "net.minecraft.server.level.ServerPlayerGameMode", "net.minecraft.server.players.StoredUserList",
            "net.minecraft.server.players.PlayerList", "net.minecraft.world.level.storage.PrimaryLevelData",
            "net.minecraft.server.commands.StopCommand"));
        result.addProperty("team_hooks_verified", marked("dev.ftb.mods.ftbteams.data.Team",
            "dev.ftb.mods.ftbteams.data.PartyTeam", "dev.ftb.mods.ftbteams.data.TeamManager"));
        boolean global=false;
        try {
            global=Class.forName("dev.latvian.mods.kubejs.BuiltinKubeJSPlugin").getField("GLOBAL").get(null)
                instanceof ObservedGlobalMap;
        } catch(ReflectiveOperationException ignored) {}
        result.addProperty("global_map_hooks_verified", global);
        result.addProperty("team_map_hooks_verified", TeamMapSupport.verified());
        result.addProperty("script_field_hooks_verified", marked("dev.latvian.mods.rhino.JavaMembers",
            "dev.latvian.mods.rhino.MemberBox"));
        // Native/mod writes, native handle calls and pre-activation history remain unqualified.
        result.addProperty("all_mutation_routes_covered", false); return result;
    }
    private static boolean marked(String... names) {
        try {
            for (String name : names)
                if (!java.util.Arrays.asList(Class.forName(name, false, SetupHistory.class.getClassLoader())
                    .getInterfaces()).contains(SetupHistoryMarker.class)) return false;
            return true;
        } catch (ClassNotFoundException error) { return false; }
    }
    static final class Monitor {
        private final Thread owner;
        private final long limit;
        private final Map<String, Long> attempts = new TreeMap<>();
        private long offThread;
        private boolean overflowed;
        private Object pendingStopSource;
        Monitor(Thread owner, long limit) {
            if (limit < 1) throw new IllegalArgumentException("SETUP_HISTORY_LIMIT");
            this.owner = owner; this.limit = limit;
            for (String route : ROUTES) attempts.put(route, 0L);
        }
        synchronized void attempt(String route, Thread thread) {
            Long count = attempts.get(route);
            if (count == null) throw new IllegalArgumentException("SETUP_HISTORY_ROUTE");
            if (count == limit) { overflowed = true; return; }
            attempts.put(route, count + 1);
            if (thread != owner) offThread++;
        }
        synchronized void command(Object source, boolean exactStop, Thread thread) {
            attempt("command_attempt", thread);
            pendingStopSource = exactStop && thread == owner ? source : null;
        }
        synchronized void stopping(Object source, Thread thread) {
            if (source != null && source == pendingStopSource && thread == owner)
                attempt("native_stop_command", thread);
            pendingStopSource = null;
        }
        synchronized JsonObject capture(String phase, String transaction) {
            var result = new JsonObject(); result.addProperty("policy", POLICY);
            result.addProperty("phase", phase);
            if (transaction == null) result.add("transaction_id", JsonNull.INSTANCE);
            else result.addProperty("transaction_id", transaction);
            var counts = new JsonObject(); attempts.forEach(counts::addProperty);
            result.add("attempts", counts); result.addProperty("off_thread_attempts", offThread);
            result.addProperty("overflowed", overflowed); return result;
        }
    }
    private SetupHistory() {}
}
