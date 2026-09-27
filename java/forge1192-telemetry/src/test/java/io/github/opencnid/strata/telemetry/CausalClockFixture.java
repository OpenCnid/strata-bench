package io.github.opencnid.strata.telemetry;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.nio.file.Files;
import java.nio.file.Path;

/** Production pipe/spool/clock; synthetic callbacks and setup, no Minecraft. */
public final class CausalClockFixture {
    private static void durable(EventSpool spool, long cursor) throws Exception {
        long until = System.nanoTime() + 2_000_000_000L;
        while (spool.durableSeq() < cursor) {
            spool.healthy();
            if (System.nanoTime() >= until) throw new IllegalStateException("FIXTURE_DURABLE_TIMEOUT");
            Thread.sleep(1);
        }
    }

    public static void main(String[] args) throws Exception {
        var input = new BufferedReader(new InputStreamReader(System.in));
        if (!"start".equals(input.readLine())) throw new IllegalStateException("FIXTURE_START");
        var start = JsonParser.parseString(Files.readString(Path.of(args[1]))).getAsJsonObject();
        var expected = start.getAsJsonObject("launch_identity");
        Path game = Path.of(expected.get("game_directory").getAsString());
        start.add("launch_identity", LaunchIdentity.observe(game,
            Path.of(expected.get("world_directory").getAsString()),
            Path.of(expected.get("module_file").getAsString()), true, 25569));
        var config = TelemetryConfig.read(Path.of(args[0]), game);
        var clock = new ServerClock();
        long cursor = 1, ticks = 0, wall = 0, work = 0;
        try (var spool = new EventSpool(config)) {
            spool.publish(0, "server_started", "strata/ServerStarted/20", start, new JsonArray());
            durable(spool, cursor);
            System.out.println("ready");
            for (String command; (command = input.readLine()) != null;) {
                if (command.equals("stop")) {
                    spool.publish(ticks, "server_clock", "strata/ServerClock/1", clock.stop(), new JsonArray());
                    spool.publish(ticks, "server_stopped", "strata/ServerStopped/1", new JsonObject(), new JsonArray());
                    return;
                }
                if (!command.equals("sample") && !command.startsWith("sample ")) throw new IllegalStateException("FIXTURE_COMMAND");
                clock.startTick();
                if (command.startsWith("sample ")) clock.avatarTick(java.util.UUID.fromString(command.substring(7)));
                clock.endTick(); ticks++;
                var now = clock.sample();
                long nextWall = now.get("elapsed_wall_ns").getAsLong();
                long nextWork = now.get("observed_tick_work_ns").getAsLong();
                var health = new JsonObject();
                health.addProperty("interval_wall_ns", nextWall - wall);
                health.addProperty("interval_server_ticks", 1);
                health.addProperty("observed_tick_work_ns", nextWork - work);
                health.addProperty("server_average_mspt", 0);
                health.addProperty("heap_used_bytes", 0);
                health.addProperty("gc_count", 0); health.addProperty("gc_time_ms", 0);
                health.addProperty("durable_event_seq_before_sample", spool.durableSeq());
                health.add("avatar_ticks_since_boot", new JsonObject());
                spool.publish(ticks, "server_health", "strata/ServerHealth/1", health, new JsonArray());
                spool.publish(ticks, "server_clock_sample", "strata/ServerClockSample/1", clock.sample(), new JsonArray());
                cursor += 2; durable(spool, cursor);
                wall = nextWall; work = nextWork;
                System.out.println(cursor);
            }
            throw new IllegalStateException("FIXTURE_UNFINISHED");
        }
    }
}
