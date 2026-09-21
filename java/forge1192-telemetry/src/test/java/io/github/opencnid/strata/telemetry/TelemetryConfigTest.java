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

    @Test void versionedSelectedQueriesRejectDuplicatesPathsAndSchemaMixing() throws Exception {
        Path spool = Files.createDirectory(root.resolve("spool"));
        Path game = Files.createDirectory(root.resolve("game"));
        Path source = root.resolve("config.json");
        JsonObject value = fixture(spool); value.addProperty("schema", "strata/ForgeTelemetryConfig/2");
        JsonArray queries = new JsonArray();
        queries.add(new ConfigQuery("fixture-common.toml", java.util.List.of(java.util.List.of("quoted.key", "items"))).json());
        value.add("config_queries", queries);
        Files.writeString(source, value.toString());
        assertEquals("quoted.key", TelemetryConfig.read(source, game).configQueries().get(0).paths().get(0).get(0));
        String valid = value.toString();
        for (String invalid : new String[] {
            valid.replace("TelemetryConfig/2", "TelemetryConfig/1"),
            valid.replace("fixture-common.toml", "../fixture-common.toml"),
            valid.replace("\"quoted.key\",\"items\"", "\"quoted.key\",null"),
            valid.replace("\"file_name\":", "\"extra\":true,\"file_name\":"),
            valid.replace("\"paths\":", "\"paths\":[],\"paths\":"),
            valid.replace("[[\"quoted.key\",\"items\"]]", "[[],[]]")
        }) {
            Files.writeString(source, invalid);
            assertThrows(Exception.class, () -> TelemetryConfig.read(source, game), invalid);
        }
        queries.add(queries.get(0).deepCopy()); Files.writeString(source, value.toString());
        assertThrows(IOException.class, () -> TelemetryConfig.read(source, game));
        assertThrows(IllegalArgumentException.class, () -> new ConfigQuery("fixture.toml", java.util.List.of(java.util.List.of("k"), java.util.List.of("k"))));
        assertThrows(IllegalArgumentException.class, () -> new ConfigQuery("fixture.toml", java.util.List.of(java.util.Collections.nCopies(17, "k"))));
    }

    @Test void signedVersionRequiresCompletePrivateKeyBinding() throws Exception {
        Path spool = Files.createDirectory(root.resolve("spool"));
        Path game = Files.createDirectory(root.resolve("game"));
        Path source = root.resolve("config.json"), key = root.resolve("key.bin");
        Files.write(key, new byte[32]);
        JsonObject value = fixture(spool); value.addProperty("schema", "strata/ForgeTelemetryConfig/3");
        value.add("config_queries", new JsonArray());
        JsonObject auth = new JsonObject();
        auth.addProperty("challenge", "a".repeat(64)); auth.addProperty("key_file", key.toString());
        auth.addProperty("key_sha256", "b".repeat(64)); auth.addProperty("authority_digest", "c".repeat(64));
        value.add("authentication", auth); Files.writeString(source, value.toString());
        assertEquals(key, TelemetryConfig.read(source, game).authentication().keyFile());
        String valid = value.toString();
        for (String invalid : new String[] {
            valid.replace("TelemetryConfig/3", "TelemetryConfig/2"),
            valid.replace("\"authentication\":", "\"extra\":true,\"authentication\":"),
            valid.replace("\"challenge\":", "\"challenge\":null,\"challenge\":"),
            valid.replace("a".repeat(64), "a".repeat(63)),
            valid.replace("\"authority_digest\":", "\"unknown\":")
        }) {
            Files.writeString(source, invalid);
            assertThrows(Exception.class, () -> TelemetryConfig.read(source, game));
        }
        Path gameKey = game.resolve("secret.bin"); Files.write(gameKey, new byte[32]);
        auth.addProperty("key_file", gameKey.toString()); Files.writeString(source, value.toString());
        assertThrows(IOException.class, () -> TelemetryConfig.read(source, game));
    }
}
