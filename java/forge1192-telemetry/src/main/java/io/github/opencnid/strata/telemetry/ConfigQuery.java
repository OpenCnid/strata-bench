package io.github.opencnid.strata.telemetry;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.google.gson.stream.JsonReader;
import java.io.IOException;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

/** Private exact selectors, not file paths, reflection expressions or game commands. */
record ConfigQuery(String fileName, List<List<String>> paths) {
    ConfigQuery {
        if (fileName == null || fileName.length() > 128
                || !fileName.matches("[a-z0-9][a-z0-9_.-]*\\.toml")
                || paths == null || paths.isEmpty() || paths.size() > 32) {
            throw new IllegalArgumentException("TELEMETRY_CONFIG_QUERY");
        }
        paths = paths.stream().map(List::copyOf).toList();
        if (new HashSet<>(paths).size() != paths.size()
                || paths.stream().anyMatch(p -> p.isEmpty() || p.size() > 16
                || p.stream().anyMatch(k -> !k.matches("[ -~]{1,128}")))) {
            throw new IllegalArgumentException("TELEMETRY_CONFIG_QUERY");
        }
    }

    static ConfigQuery read(JsonReader reader) throws IOException {
        String file = null;
        List<List<String>> paths = new ArrayList<>();
        Set<String> seen = new HashSet<>();
        reader.beginObject();
        while (reader.hasNext()) {
            String key = reader.nextName();
            if (!seen.add(key)) throw new IOException("TELEMETRY_CONFIG_QUERY");
            switch (key) {
                case "file_name" -> file = TelemetryConfig.string(reader);
                case "paths" -> {
                    reader.beginArray();
                    while (reader.hasNext()) {
                        if (paths.size() >= 32) throw new IOException("TELEMETRY_CONFIG_QUERY");
                        List<String> path = new ArrayList<>();
                        reader.beginArray();
                        while (reader.hasNext()) {
                            if (path.size() >= 16) throw new IOException("TELEMETRY_CONFIG_QUERY");
                            path.add(TelemetryConfig.string(reader));
                        }
                        reader.endArray(); paths.add(path);
                    }
                    reader.endArray();
                }
                default -> throw new IOException("TELEMETRY_CONFIG_QUERY");
            }
        }
        reader.endObject();
        if (!seen.equals(Set.of("file_name", "paths"))) throw new IOException("TELEMETRY_CONFIG_QUERY");
        try { return new ConfigQuery(file, paths); }
        catch (IllegalArgumentException error) { throw new IOException("TELEMETRY_CONFIG_QUERY", error); }
    }

    JsonObject json() {
        JsonObject result = new JsonObject(); result.addProperty("file_name", fileName);
        JsonArray values = new JsonArray();
        for (List<String> path : paths) {
            JsonArray keys = new JsonArray(); path.forEach(keys::add); values.add(keys);
        }
        result.add("paths", values); return result;
    }
}
