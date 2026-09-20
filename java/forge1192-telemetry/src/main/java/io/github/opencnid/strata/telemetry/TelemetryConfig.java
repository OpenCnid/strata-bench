package io.github.opencnid.strata.telemetry;

import com.google.gson.stream.JsonReader;
import com.google.gson.stream.JsonToken;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

/** Private operator configuration. Never read from a player packet or game command. */
record TelemetryConfig(String campaignId, long epoch, Path spoolDirectory,
                       long maxBytes, long maxEvents, List<String> recipeIds,
                       List<ConfigQuery> configQueries) {
    private static final Set<String> FIELDS = Set.of("schema", "campaign_id", "epoch",
        "spool_directory", "max_bytes", "max_events", "recipe_ids");
    private static final Set<String> FIELDS_V2 = Set.of("schema", "campaign_id", "epoch",
        "spool_directory", "max_bytes", "max_events", "recipe_ids", "config_queries");

    static Path safeExisting(Path input) throws IOException {
        Path absolute = input.toAbsolutePath().normalize();
        if (!input.isAbsolute() || !input.equals(absolute)
                || !Files.exists(absolute, LinkOption.NOFOLLOW_LINKS)) {
            throw new IOException("TELEMETRY_UNSAFE_PATH");
        }
        for (Path p = absolute; p != null; p = p.getParent()) {
            if (Files.isSymbolicLink(p) || !p.toRealPath().equals(p)) {
                throw new IOException("TELEMETRY_UNSAFE_PATH");
            }
        }
        return absolute;
    }

    static TelemetryConfig read(Path path, Path gameDirectory) throws IOException {
        Path source = safeExisting(path);
        Path game = gameDirectory.toAbsolutePath().normalize();
        if (source.startsWith(game) || Files.size(source) > 65536) {
            throw new IOException("TELEMETRY_CONFIG_PRIVATE_ROOT_REQUIRED");
        }
        String schema = null, campaign = null, spool = null;
        List<ConfigQuery> queries = new ArrayList<>();
        long epoch = -1, maxBytes = -1, maxEvents = -1;
        List<String> recipes = new ArrayList<>();
        Set<String> seen = new HashSet<>();
        try (JsonReader reader = new JsonReader(Files.newBufferedReader(source, StandardCharsets.UTF_8))) {
            reader.setLenient(false);
            reader.beginObject();
            while (reader.hasNext()) {
                String key = reader.nextName();
                if (!FIELDS_V2.contains(key) || !seen.add(key)) {
                    throw new IOException("TELEMETRY_CONFIG_FIELDS");
                }
                switch (key) {
                    case "schema" -> schema = string(reader);
                    case "campaign_id" -> campaign = string(reader);
                    case "spool_directory" -> spool = string(reader);
                    case "epoch" -> epoch = integer(reader);
                    case "max_bytes" -> maxBytes = integer(reader);
                    case "max_events" -> maxEvents = integer(reader);
                    case "recipe_ids" -> {
                        reader.beginArray();
                        while (reader.hasNext()) {
                            String id = string(reader);
                            if (!id.matches("[a-z0-9_.-]+:[a-z0-9_./-]+") || id.length() > 256
                                    || recipes.size() >= 64 || recipes.contains(id)) {
                                throw new IOException("TELEMETRY_RECIPE_IDS");
                            }
                            recipes.add(id);
                        }
                        reader.endArray();
                    }
                    case "config_queries" -> {
                        reader.beginArray();
                        while (reader.hasNext()) {
                            if (queries.size() >= 16) throw new IOException("TELEMETRY_CONFIG_QUERY");
                            ConfigQuery query = ConfigQuery.read(reader);
                            if (queries.stream().anyMatch(q -> q.fileName().equals(query.fileName()))) {
                                throw new IOException("TELEMETRY_CONFIG_QUERY");
                            }
                            queries.add(query);
                        }
                        reader.endArray();
                    }
                    default -> throw new IOException("TELEMETRY_CONFIG_FIELDS");
                }
            }
            reader.endObject();
            if (reader.peek() != JsonToken.END_DOCUMENT) throw new IOException("TELEMETRY_CONFIG_TRAILING");
        }
        boolean validVersion = "strata/ForgeTelemetryConfig/1".equals(schema) && seen.equals(FIELDS)
            || "strata/ForgeTelemetryConfig/2".equals(schema) && seen.equals(FIELDS_V2);
        if (!validVersion
                || campaign == null || !campaign.matches("[A-Za-z0-9_.:-]{1,128}")
                || epoch < 1 || epoch > 9007199254740991L || maxBytes < 65536
                || maxBytes > 1073741824L || maxEvents < 1 || maxEvents > 1000000) {
            throw new IOException("TELEMETRY_CONFIG_RANGE");
        }
        Path directory = safeExisting(Path.of(spool));
        if (!Files.isDirectory(directory) || directory.startsWith(game) || game.startsWith(directory)) {
            throw new IOException("TELEMETRY_PRIVATE_ROOT_REQUIRED");
        }
        return new TelemetryConfig(campaign, epoch, directory, maxBytes, maxEvents,
            List.copyOf(recipes), List.copyOf(queries));
    }

    static String string(JsonReader reader) throws IOException {
        if (reader.peek() != JsonToken.STRING) throw new IOException("TELEMETRY_CONFIG_TYPE");
        return reader.nextString();
    }

    private static long integer(JsonReader reader) throws IOException {
        if (reader.peek() != JsonToken.NUMBER) throw new IOException("TELEMETRY_CONFIG_TYPE");
        String text = reader.nextString();
        if (!text.matches("0|[1-9][0-9]{0,15}")) throw new IOException("TELEMETRY_CONFIG_TYPE");
        return Long.parseLong(text);
    }
}
