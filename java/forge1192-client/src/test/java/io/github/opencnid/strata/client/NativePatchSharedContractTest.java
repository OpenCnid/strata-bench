package io.github.opencnid.strata.client;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.stream.Stream;
import org.junit.jupiter.api.DynamicTest;
import org.junit.jupiter.api.TestFactory;
import static org.junit.jupiter.api.Assertions.*;

/** Actual private request validator with shared Python fixtures; no game runtime. */
final class NativePatchSharedContractTest {
    @TestFactory Stream<DynamicTest> sharedPatchValidation() throws Exception {
        JsonObject corpus = JsonParser.parseString(Files.readString(Path.of(
            "../../tests/fixtures/native_patch_semantics.json"))).getAsJsonObject();
        var tests = new ArrayList<DynamicTest>();
        for (var entry : corpus.getAsJsonArray("cases")) {
            JsonObject c = entry.getAsJsonObject(), body = corpus.getAsJsonObject("base").deepCopy();
            for (var change : c.getAsJsonObject("set").entrySet()) {
                String[] parts = change.getKey().split("/");
                JsonObject parent = body;
                for (int i = 0; i < parts.length - 1; i++) parent = parent.getAsJsonObject(parts[i]);
                parent.add(parts[parts.length - 1], change.getValue().deepCopy());
            }
            JsonObject request = new JsonObject();
            request.addProperty("schema", NativeSettingsProtocol.REQUEST_SCHEMA);
            request.addProperty("request_id", "r"); request.addProperty("session_id", "s");
            request.addProperty("deadline_unix_ms", 1001); request.addProperty("operation", "apply");
            request.add("args", body);
            tests.add(DynamicTest.dynamicTest(c.get("id").getAsString(), () -> {
                JsonObject before = request.deepCopy();
                if (c.get("valid").getAsBoolean()) NativeSettingsProtocol.validate(request, "s", 1000);
                else assertThrows(IOException.class, () -> NativeSettingsProtocol.validate(request, "s", 1000));
                assertEquals(before, request);
            }));
        }
        return tests.stream();
    }
}
