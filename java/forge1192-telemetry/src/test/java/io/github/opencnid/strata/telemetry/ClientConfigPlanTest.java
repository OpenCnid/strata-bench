package io.github.opencnid.strata.telemetry;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import static org.junit.jupiter.api.Assertions.*;

class ClientConfigPlanTest {
    @TempDir Path root;

    private JsonObject value(Path output) {
        JsonObject v = new JsonObject();
        v.addProperty("schema", "strata/ForgeTelemetryConfig/2");
        v.addProperty("campaign_id", "synthetic"); v.addProperty("epoch", 1);
        v.addProperty("spool_directory", output.toString());
        v.addProperty("max_bytes", 65536); v.addProperty("max_events", 1);
        v.add("recipe_ids", new JsonArray()); JsonArray q = new JsonArray();
        q.add(new ConfigQuery("fixture-client.toml", List.of(List.of("key"))).json());
        v.add("config_queries", q); return v;
    }

    @Test void fixedPrivatePlanDetectsChangesBeforeCapture() throws Exception {
        Path game = Files.createDirectory(root.resolve("game"));
        Path out = Files.createDirectory(root.resolve("out"));
        Path source = root.resolve("plan.json");
        Files.writeString(source, value(out).toString());
        ClientConfigPlan plan = ClientConfigPlan.read(source, game);
        plan.unchanged(); assertEquals(64, plan.sha256().length());
        Files.writeString(source, value(out) + "\n");
        assertThrows(IOException.class, plan::unchanged);
        Files.writeString(game.resolve("plan.json"), value(out).toString());
        assertThrows(IOException.class, () -> ClientConfigPlan.read(game.resolve("plan.json"), game));
        Files.writeString(source, value(game).toString());
        assertThrows(IOException.class, () -> ClientConfigPlan.read(source, game));
    }

    @Test void serverOrUnboundedPlansCannotActivateClientProbe() throws Exception {
        Path game = Files.createDirectory(root.resolve("game"));
        Path out = Files.createDirectory(root.resolve("out"));
        Path source = root.resolve("plan.json");
        String original = value(out).toString();
        for (String bad : new String[] {
            original.replace("\"max_events\":1", "\"max_events\":2"),
            original.replace("65536", "1048577"),
            original.replace("\"recipe_ids\":[]", "\"recipe_ids\":[\"minecraft:furnace\"]"),
            original.replace(value(out).get("config_queries").toString(), "[]")
        }) {
            Files.writeString(source, bad);
            assertThrows(IOException.class, () -> ClientConfigPlan.read(source, game));
        }
    }
}
