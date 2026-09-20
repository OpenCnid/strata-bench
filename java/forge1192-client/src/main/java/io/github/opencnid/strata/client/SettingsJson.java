package io.github.opencnid.strata.client;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonNull;
import com.google.gson.JsonObject;
import com.google.gson.JsonPrimitive;
import com.google.gson.stream.JsonReader;
import com.google.gson.stream.JsonToken;
import java.io.IOException;
import java.io.StringReader;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;
import java.util.TreeMap;

/** Bounded strict private journal/config parsing; Gson's duplicate-key replacement is forbidden. */
final class SettingsJson {
    static JsonObject read(String text) throws IOException {
        return read(text, false);
    }

    /** Game coordinates admit signed finite numbers; settings/journal integers stay strict. */
    static JsonObject readGame(String text) throws IOException { return read(text, true); }

    private static JsonObject read(String text, boolean gameNumbers) throws IOException {
        if (text.length() > 1048576) throw new IOException("SETTINGS_JSON_TOO_LARGE");
        try (JsonReader reader = new JsonReader(new StringReader(text))) {
            reader.setLenient(false);
            JsonElement result = value(reader, 0, gameNumbers);
            if (!result.isJsonObject() || reader.peek() != JsonToken.END_DOCUMENT) throw new IOException("SETTINGS_JSON_INVALID");
            return result.getAsJsonObject();
        } catch (IllegalStateException | NumberFormatException error) {
            throw new IOException("SETTINGS_JSON_INVALID", error);
        }
    }

    private static JsonElement value(JsonReader reader, int depth, boolean gameNumbers) throws IOException {
        if (depth > 8) throw new IOException("SETTINGS_JSON_TOO_DEEP");
        return switch (reader.peek()) {
            case BEGIN_OBJECT -> {
                reader.beginObject();
                JsonObject object = new JsonObject();
                while (reader.hasNext()) {
                    String name = reader.nextName();
                    if (name.length() > 256 || object.has(name) || object.size() >= 4096) {
                        throw new IOException("SETTINGS_JSON_FIELDS");
                    }
                    object.add(name, value(reader, depth + 1, gameNumbers));
                }
                reader.endObject();
                yield object;
            }
            case BEGIN_ARRAY -> {
                reader.beginArray();
                JsonArray array = new JsonArray();
                while (reader.hasNext()) {
                    if (array.size() >= 4096) throw new IOException("SETTINGS_JSON_TOO_LARGE");
                    array.add(value(reader, depth + 1, gameNumbers));
                }
                reader.endArray();
                yield array;
            }
            case STRING -> {
                String text = reader.nextString();
                if (text.length() > 4096) throw new IOException("SETTINGS_JSON_TOO_LARGE");
                yield new JsonPrimitive(text);
            }
            case NUMBER -> {
                String text = reader.nextString();
                if (gameNumbers) {
                    if (text.length() > 64) throw new IOException("GAME_JSON_NUMBER");
                    double number = Double.parseDouble(text);
                    if (!Double.isFinite(number) || Math.abs(number) > 9007199254740991L) throw new IOException("GAME_JSON_NUMBER");
                    // Preserve integer lexical identity so 1.5/1e0/1.0 cannot become an ID or sequence.
                    yield com.google.gson.JsonParser.parseString(text);
                }
                if (!text.matches("0|[1-9][0-9]{0,15}")) throw new IOException("SETTINGS_JSON_NUMBER");
                long number = Long.parseLong(text);
                if (number > 9007199254740991L) throw new IOException("SETTINGS_JSON_NUMBER");
                yield new JsonPrimitive(number);
            }
            case BOOLEAN -> new JsonPrimitive(reader.nextBoolean());
            case NULL -> { reader.nextNull(); yield JsonNull.INSTANCE; }
            default -> throw new IOException("SETTINGS_JSON_INVALID");
        };
    }

    static void fields(JsonObject value, String... names) throws IOException {
        Set<String> actual = new HashSet<>();
        value.entrySet().forEach(entry -> actual.add(entry.getKey()));
        if (!actual.equals(Set.of(names))) throw new IOException("SETTINGS_JSON_FIELDS");
    }

    static String string(JsonObject object, String key) throws IOException {
        JsonElement value = object.get(key);
        if (value == null || !value.isJsonPrimitive() || !value.getAsJsonPrimitive().isString()) {
            throw new IOException("SETTINGS_JSON_TYPE");
        }
        return value.getAsString();
    }

    static long integer(JsonObject object, String key) throws IOException {
        JsonElement value = object.get(key);
        if (value == null || !value.isJsonPrimitive() || !value.getAsJsonPrimitive().isNumber()) {
            throw new IOException("SETTINGS_JSON_TYPE");
        }
        String text = value.getAsString();
        if (!text.matches("0|[1-9][0-9]{0,15}")) throw new IOException("SETTINGS_JSON_NUMBER");
        long number = Long.parseLong(text);
        if (number > 9007199254740991L) throw new IOException("SETTINGS_JSON_NUMBER");
        return number;
    }

    static JsonObject strings(Map<String, String> values) {
        JsonObject result = new JsonObject();
        new TreeMap<>(values).forEach(result::addProperty);
        return result;
    }

    static Map<String, String> strings(JsonObject parent, String key) throws IOException {
        JsonElement value = parent.get(key);
        if (value == null || !value.isJsonObject()) throw new IOException("SETTINGS_JSON_TYPE");
        Map<String, String> result = new TreeMap<>();
        for (var entry : value.getAsJsonObject().entrySet()) {
            result.put(entry.getKey(), string(value.getAsJsonObject(), entry.getKey()));
        }
        return Map.copyOf(result);
    }
}
