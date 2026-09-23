package io.github.opencnid.strata.telemetry;

import com.google.gson.JsonArray;
import com.google.gson.JsonNull;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import java.io.BufferedReader;
import java.io.DataOutputStream;
import java.io.InputStreamReader;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.zip.GZIPOutputStream;

/** Real owned JVM and signing code, fabricated setup/world/commands. Never Minecraft. */
public final class SetupControlFixture {
    private static JsonObject point() {
        return JsonParser.parseString("""
            {"policy":"native-e9e-setup-observation/1","phase":"startup","transaction_id":null,
             "actor":null,"team":{"status":"manager_ready"},
             "pack":{"status":"observed","mode":"expert","is_expert":true,"is_normal":false,
                     "startup_errors":0,"server_errors":0},
             "server":{"default_game_mode":"survival","world_game_mode":"survival","difficulty":"normal",
                       "hardcore":false,"world_allows_commands":false,"command_blocks_enabled":false,
                       "rcon_enabled":false,"operator_levels":[],"command_events_seen":0}}
            """).getAsJsonObject();
    }
    private static void save(Path file, int mode) throws Exception {
        try (var out = new DataOutputStream(new GZIPOutputStream(Files.newOutputStream(file)))) {
            out.writeByte(10); out.writeUTF(""); out.writeByte(10); out.writeUTF("Data");
            out.writeByte(3); out.writeUTF("GameType"); out.writeInt(mode); out.writeByte(0); out.writeByte(0);
        }
    }
    public static void main(String[] args) throws Exception {
        var game = Path.of(args[1]); var world = game.resolve("world");
        var config = TelemetryConfig.read(Path.of(args[0]), game);
        var monitor = new SetupHistory.Monitor(Thread.currentThread(), 100);
        Object source = new Object();
        boolean clockMode = args[4].equals("clock");
        var clockTime = new java.util.concurrent.atomic.AtomicLong();
        var clock = new ServerClock(clockTime::get);
        try (var spool = new EventSpool(config)) {
            var boot = new JsonObject(); boot.addProperty("module", "strata-forge1192-telemetry/0.3.7");
            if (clockMode) {
                boot.addProperty("module", "strata-forge1192-telemetry/0.3.8");
                boot.addProperty("clock_policy", ServerClock.POLICY);
            }
            boot.addProperty("minecraft", "1.19.2"); boot.addProperty("forge", "43.4.23");
            boot.addProperty("scoring_provenance_supported", false); boot.addProperty("recipe_count", 0);
            boot.add("config_queries", new JsonArray());
            boot.addProperty("craft_capture_policy", "server-result-pickup-fastbench-bound/2");
            var craft = new JsonObject(); craft.addProperty("hook_verified", true);
            craft.add("fastbench_sha256", JsonNull.INSTANCE); boot.add("craft_capture_support", craft);
            boot.add("launch_identity", LaunchIdentity.observe(game, world, Path.of(args[2]), true, Integer.parseInt(args[3])));
            boot.addProperty("setup_capture_policy", SetupCapture.POLICY);
            var support = new JsonObject(); support.addProperty("status", "supported");
            var pins = new JsonObject(); SetupCapture.PINS.forEach(pins::addProperty); support.add("artifacts", pins);
            boot.add("setup_capture_support", support); boot.addProperty("telemetry_transport", "private-file/1");
            var history = new JsonObject(); history.addProperty("policy", SetupHistory.POLICY);
            history.addProperty("vanilla_hooks_verified", true); history.addProperty("team_hooks_verified", true);
            history.addProperty("all_mutation_routes_covered", false); boot.add("setup_history_support", history);
            spool.publish(0, "server_started", clockMode ? "strata/ServerStarted/9" : "strata/ServerStarted/8", boot, new JsonArray());
            spool.publish(1, "setup_history", "strata/NativeSetupHistory/1", monitor.capture("startup", null), new JsonArray());
            spool.publish(1, "setup_snapshot", "strata/NativeSetupSnapshot/1", point(), new JsonArray());
            var health = new JsonObject(); health.addProperty("interval_wall_ns", 1000000000);
            health.addProperty("interval_server_ticks", 20); health.addProperty("observed_tick_work_ns", 100);
            health.addProperty("server_average_mspt", 0.1); health.addProperty("heap_used_bytes", 1024);
            health.addProperty("gc_count", 0); health.addProperty("gc_time_ms", 0);
            health.addProperty("durable_event_seq_before_sample", 0); health.add("avatar_ticks_since_boot", new JsonObject());
            spool.publish(20, "server_health", "strata/ServerHealth/1", health, new JsonArray());
            if (clockMode) {
                for (int i = 0; i < 22; i++) {
                    clockTime.set(i * 50_000_000L); clock.startTick();
                    if (i >= 20) clock.avatarTick(java.util.UUID.fromString("11111111-1111-1111-1111-111111111111"));
                    clockTime.addAndGet(10); clock.endTick();
                }
                clockTime.set(1_200_000_000L);
            }
            System.out.println("Done (0.1s)! For help, type \"help\""); System.out.flush();
            var input = new BufferedReader(new InputStreamReader(System.in)); String line;
            while ((line = input.readLine()) != null) {
                monitor.command(source, line.equals("stop"), Thread.currentThread());
                if (line.equals("stop")) {
                    monitor.stopping(source, Thread.currentThread());
                    if (clockMode) spool.publish(22, "server_clock", "strata/ServerClock/1", clock.stop(), new JsonArray());
                    spool.publish(clockMode ? 22 : 20, "setup_history", "strata/NativeSetupHistory/1", monitor.capture("stop", null), new JsonArray());
                    spool.publish(clockMode ? 22 : 20, "server_stopped", "strata/ServerStopped/1", new JsonObject(), new JsonArray());
                    break;
                }
                if (line.equals("save-all flush")) {
                    System.out.println("Saved the game"); System.out.flush(); continue;
                }
                if (args[4].startsWith("operator-")) {
                    boolean grant = line.equals("op FixtureActor");
                    if (!grant && !line.equals("deop FixtureActor"))
                        throw new IllegalStateException("UNEXPECTED_SYNTHETIC_OPERATOR_COMMAND");
                    monitor.attempt(grant ? "operator_add" : "operator_remove", Thread.currentThread());
                    boolean keep = !args[4].equals("operator-no-effect")
                        && (grant || args[4].equals("operator-wrong-restore"));
                    Files.writeString(game.resolve("ops.json"), keep
                        ? "[{\"uuid\":\"11111111-1111-1111-1111-111111111111\",\"name\":\"FixtureActor\",\"level\":4,\"bypassesPlayerLimit\":false}]"
                        : "[]");
                    System.out.println("Made FixtureActor " + (grant ? "a server operator" : "no longer a server operator"));
                    System.out.flush(); continue;
                }
                if (!line.equals("defaultgamemode creative") && !line.equals("defaultgamemode survival"))
                    throw new IllegalStateException("UNEXPECTED_SYNTHETIC_COMMAND");
                if (!args[4].equals("no-effect")) monitor.attempt("world_mode", Thread.currentThread());
                boolean creative = line.endsWith("creative");
                save(world.resolve("level.dat"), !args[4].equals("no-effect")
                    && (creative || args[4].equals("wrong-restore")) ? 1 : 0);
                System.out.println("The default game mode is now " + (creative ? "Creative Mode" : "Survival Mode"));
                System.out.flush();
            }
        }
    }
    private SetupControlFixture() {}
}
