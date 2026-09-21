package io.github.opencnid.strata.telemetry;

import com.google.gson.JsonArray;
import com.google.gson.JsonNull;
import com.google.gson.JsonObject;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.nio.file.Files;
import java.nio.file.Path;

/** Actual JVM/production spool, synthetic events only, never a game server. */
public final class OwnedLaunchFixture {
    public static void main(String[] args) throws Exception {
        Path game = Path.of(args[1]);
        String mode = args[4];
        Path world = game.resolve(mode.equals("wrong-world") ? "other" : "world");
        Files.createDirectories(world);
        var config = TelemetryConfig.read(Path.of(args[0]), game);
        try (var spool = new EventSpool(config)) {
            var boot = new JsonObject();
            boot.addProperty("module", "strata-forge1192-telemetry/0.3.4");
            boot.addProperty("minecraft", "1.19.2"); boot.addProperty("forge", "43.4.23");
            boot.addProperty("scoring_provenance_supported", false); boot.addProperty("recipe_count", 0);
            boot.add("config_queries", new JsonArray());
            boot.addProperty("craft_capture_policy", "server-result-pickup-fastbench-bound/2");
            var support = new JsonObject(); support.addProperty("hook_verified", true);
            support.add("fastbench_sha256", JsonNull.INSTANCE); boot.add("craft_capture_support", support);
            boot.add("launch_identity", LaunchIdentity.observe(game, world, Path.of(args[2]), true,
                Integer.parseInt(args[3])));
            spool.publish(0, "server_started", "strata/ServerStarted/5", boot, new JsonArray());
            var health = new JsonObject();
            health.addProperty("interval_wall_ns", 1000000000); health.addProperty("interval_server_ticks", 20);
            health.addProperty("observed_tick_work_ns", 100); health.addProperty("server_average_mspt", 0.1);
            health.addProperty("heap_used_bytes", 1024); health.addProperty("gc_count", 0); health.addProperty("gc_time_ms", 0);
            health.addProperty("durable_event_seq_before_sample", 0); health.add("avatar_ticks_since_boot", new JsonObject());
            spool.publish(20, "server_health", "strata/ServerHealth/1", health, new JsonArray());
            System.out.println("Done (0.1s)! For help, type \"help\""); System.out.flush();
            if (mode.equals("early-exit")) return;
            var input = new BufferedReader(new InputStreamReader(System.in));
            while (input.readLine() != null) {
                if (mode.equals("hang")) { Thread.sleep(60000); continue; }
                if (!mode.equals("missing-stop"))
                    spool.publish(20, "server_stopped", "strata/ServerStopped/1", new JsonObject(), new JsonArray());
                break;
            }
        }
    }
}
