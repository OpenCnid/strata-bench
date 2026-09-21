package io.github.opencnid.strata.telemetry;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import java.nio.file.Path;

/** Actual production spool in a plain JVM; synthetic events, no game/server launch. */
public final class AuthenticatedSpoolFixture {
    public static void main(String[] args) throws Exception {
        TelemetryConfig config = TelemetryConfig.read(Path.of(args[0]), Path.of(args[1]));
        try (EventSpool spool = new EventSpool(config)) {
            JsonObject start = new JsonObject();
            start.addProperty("module", "strata-forge1192-telemetry/0.3.3");
            start.addProperty("minecraft", "1.19.2"); start.addProperty("forge", "43.4.23");
            start.addProperty("scoring_provenance_supported", false); start.addProperty("recipe_count", 0);
            start.add("config_queries", new JsonArray());
            start.addProperty("craft_capture_policy", "server-result-pickup-fastbench-bound/2");
            JsonObject support = new JsonObject(); support.addProperty("hook_verified", true);
            support.add("fastbench_sha256", com.google.gson.JsonNull.INSTANCE);
            start.add("craft_capture_support", support);
            spool.publish(0, "server_started", "strata/ServerStarted/4", start, new JsonArray());
            JsonObject health = new JsonObject();
            health.addProperty("interval_wall_ns", 1000000000); health.addProperty("interval_server_ticks", 20);
            health.addProperty("observed_tick_work_ns", 100); health.addProperty("server_average_mspt", 0.1);
            health.addProperty("heap_used_bytes", 1024); health.addProperty("gc_count", 0); health.addProperty("gc_time_ms", 0);
            health.addProperty("durable_event_seq_before_sample", spool.durableSeq());
            health.add("avatar_ticks_since_boot", new JsonObject());
            spool.publish(20, "server_health", "strata/ServerHealth/1", health, new JsonArray());
            spool.publish(20, "server_stopped", "strata/ServerStopped/1", new JsonObject(), new JsonArray());
            System.out.println(spool.bootId());
        }
    }
}
