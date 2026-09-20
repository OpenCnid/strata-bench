package io.github.opencnid.strata.telemetry;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import static org.junit.jupiter.api.Assertions.*;

class TelemetryConfigTest {
    @TempDir Path root;

    private JsonObject fixture(Path spool) {
        JsonObject value = new JsonObject();
        value.addProperty("schema", "strata/ForgeTelemetryConfig/1");
        value.addProperty("campaign_id", "synthetic");
        value.addProperty("epoch", 1);
        value.addProperty("spool_directory", spool.toString());
        value.addProperty("max_bytes", 65536);
        value.addProperty("max_events", 10);
        JsonArray recipes = new JsonArray();
        recipes.add("minecraft:furnace");
        value.add("recipe_ids", recipes);
        return value;
    }

    @Test void requiresPrivateExplicitCompleteConfig() throws Exception {
        Path spool = Files.createDirectory(root.resolve("spool"));
        Path game = Files.createDirectory(root.resolve("game"));
        Path source = root.resolve("config.json");
        Files.writeString(source, fixture(spool).toString());
        assertEquals("minecraft:furnace", TelemetryConfig.read(source, game).recipeIds().get(0));
        Files.writeString(game.resolve("config.json"), fixture(spool).toString());
        assertThrows(IOException.class, () -> TelemetryConfig.read(game.resolve("config.json"), game));
        Files.writeString(source, fixture(game).toString());
        assertThrows(IOException.class, () -> TelemetryConfig.read(source, game));
    }

    @Test void duplicateUnknownCoercedFractionalAndOutOfRangeValuesFail() throws Exception {
        Path spool = Files.createDirectory(root.resolve("spool"));
        Path game = Files.createDirectory(root.resolve("game"));
        Path source = root.resolve("config.json");
        String valid = fixture(spool).toString();
        for (String invalid : new String[] {
            valid.replace("\"epoch\":1", "\"epoch\":1,\"epoch\":2"),
            valid.replace("\"epoch\":1", "\"epoch\":\"1\""),
            valid.replace("\"epoch\":1", "\"epoch\":1.0"),
            valid.replace("\"epoch\":1", "\"epoch\":9007199254740992"),
            valid.replace("\"epoch\":1", "\"epoch\":1,\"extra\":true"),
            valid.replace("\"epoch\":1,", ""),
            valid.replace("65536", "1"),
            valid + "{}"
        }) {
            Files.writeString(source, invalid);
            assertThrows(IOException.class, () -> TelemetryConfig.read(source, game), invalid);
        }
    }
}
