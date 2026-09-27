package io.github.opencnid.strata.client;

import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.regex.Pattern;
import java.util.stream.Stream;
import org.junit.jupiter.api.DynamicTest;
import org.junit.jupiter.api.TestFactory;
import static org.junit.jupiter.api.Assertions.*;

/** Shared canonical input at the actual Java parser, without a game or model. */
final class GameBatchSharedContractTest {
    private static JsonElement at(JsonElement value, String path) {
        for (String part : path.split("/")) value = value.isJsonArray()
            ? value.getAsJsonArray().get(Integer.parseInt(part)) : value.getAsJsonObject().get(part);
        return value;
    }
    private static void assign(JsonObject body, String path, JsonElement value) {
        int split = path.lastIndexOf('/');
        JsonElement parent = split < 0 ? body : at(body, path.substring(0, split));
        String key = path.substring(split + 1);
        if (parent.isJsonArray()) {
            int index = Integer.parseInt(key);
            if (index == parent.getAsJsonArray().size()) parent.getAsJsonArray().add(value.deepCopy());
            else parent.getAsJsonArray().set(index, value.deepCopy());
        } else parent.getAsJsonObject().add(key, value.deepCopy());
    }
    @TestFactory Stream<DynamicTest> canonicalActionsAndExplicitUnsupportedInput() throws Exception {
        Path root = Path.of("../..");
        JsonObject corpus = JsonParser.parseString(Files.readString(root.resolve(
            "tests/fixtures/public_record_semantics.json"))).getAsJsonObject();
        var matches = Pattern.compile("```json\\s*(.*?)```", Pattern.DOTALL)
            .matcher(Files.readString(root.resolve("SPEC.md")));
        JsonObject example = null;
        while (matches.find()) {
            JsonObject record = JsonParser.parseString(matches.group(1)).getAsJsonObject();
            if (record.get("schema").getAsString().equals("mcbench/ActionBatch/1")) example = record;
        }
        assertNotNull(example);
        var tests = new ArrayList<DynamicTest>();
        for (JsonElement entry : corpus.getAsJsonArray("cases")) {
            JsonObject c = entry.getAsJsonObject();
            JsonObject profile = corpus.getAsJsonObject("profiles").getAsJsonObject(c.get("base").getAsString());
            if (!profile.get("record").getAsString().equals("ActionBatch")) continue;
            JsonObject body = example.deepCopy();
            profile.getAsJsonObject("set").entrySet().forEach(e -> assign(body, e.getKey(), e.getValue()));
            if (c.has("copy")) c.getAsJsonObject("copy").entrySet().forEach(e ->
                assign(body, e.getKey(), at(body, e.getValue().getAsString())));
            c.getAsJsonObject("set").entrySet().forEach(e -> assign(body, e.getKey(), e.getValue()));
            // Canonical examples are documentation. This fixture calls the actual development parser.
            body.addProperty("is_example", false);
            boolean input = c.get("base").getAsString().equals("input");
            tests.add(DynamicTest.dynamicTest(c.get("id").getAsString(), () -> {
                if (input) {
                    // The Forge structured profile refuses the whole input mode; no input parity claim.
                    assertEquals("CAPABILITY_MISSING", assertThrows(IOException.class,
                        () -> new GameBatch(body)).getMessage());
                } else if (c.get("valid").getAsBoolean()) {
                    GameBatch parsed = new GameBatch(body);
                    assertEquals(body, parsed.json);
                    assertNotSame(body, parsed.json);
                } else assertThrows(IOException.class, () -> new GameBatch(body));
            }));
        }
        assertEquals(24, tests.size());
        return tests.stream();
    }
}
