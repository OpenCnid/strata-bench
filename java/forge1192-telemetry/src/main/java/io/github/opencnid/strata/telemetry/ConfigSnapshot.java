package io.github.opencnid.strata.telemetry;

import com.electronwill.nightconfig.core.UnmodifiableConfig;
import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonPrimitive;
import java.nio.charset.StandardCharsets;
import java.util.List;
import net.minecraftforge.common.ForgeConfigSpec;
import net.minecraftforge.fml.config.ConfigTracker;
import net.minecraftforge.fml.config.ModConfig;

/** Reads selected raw backing data; never calls ConfigValue.get, save, correct or reload. */
final class ConfigSnapshot {
    private static final long MAX_INTEGER = 9007199254740991L;

    interface Source {
        Object identity();
        String modId();
        String type();
        Object spec();
        boolean loaded();
        UnmodifiableConfig data();
        boolean declared(List<String> path);
    }

    static JsonObject capture(ConfigQuery query) {
        ModConfig config = ConfigTracker.INSTANCE.fileMap().get(query.fileName());
        Source source = config == null ? null : new Source() {
            public Object identity() { return ConfigTracker.INSTANCE.fileMap().get(query.fileName()); }
            public String modId() { return config.getModId(); }
            public String type() { return config.getType().name(); }
            public Object spec() { return config.getSpec(); }
            public boolean loaded() { return config.getSpec() instanceof ForgeConfigSpec s && s.isLoaded(); }
            public UnmodifiableConfig data() { return config.getConfigData(); }
            public boolean declared(List<String> path) {
                return ((ForgeConfigSpec)config.getSpec()).getSpec().getRaw(path) instanceof ForgeConfigSpec.ValueSpec;
            }
        };
        return capture(query, source, config, config != null && config.getSpec() instanceof ForgeConfigSpec);
    }

    static JsonObject capture(ConfigQuery query, Source source, Object identity, boolean supportedSpec) {
        JsonObject result = new JsonObject(); result.addProperty("file_name", query.fileName());
        if (source == null) return status(result, "unregistered");
        result.addProperty("mod_id", source.modId()); result.addProperty("config_type", source.type());
        if (!supportedSpec) return status(result, "unsupported_spec");
        Object spec = source.spec(); UnmodifiableConfig data = source.data();
        if (!source.loaded() || data == null) return status(result, "unloaded");
        try {
            JsonArray first = rows(query, source, data);
            JsonArray second = rows(query, source, data);
            if (!first.toString().equals(second.toString()) || source.identity() != identity
                    || source.spec() != spec || source.data() != data || !source.loaded()) {
                return status(result, "unstable");
            }
            result.addProperty("consistency", "matching_consecutive_reads");
            result.add("values", second);
            status(result, "snapshot");
            if (result.toString().getBytes(StandardCharsets.UTF_8).length > 65536) {
                result.remove("values"); result.remove("consistency");
                return status(result, "quota_exceeded");
            }
            return result;
        } catch (Rejected error) { return status(result, error.code); }
        catch (RuntimeException error) { return status(result, "read_failed"); }
    }

    private static JsonObject status(JsonObject result, String status) {
        result.addProperty("status", status); return result;
    }

    private static JsonArray rows(ConfigQuery query, Source source, UnmodifiableConfig data) {
        JsonArray rows = new JsonArray(); int[] nodes = {0, 0};
        for (List<String> path : query.paths()) {
            JsonObject row = new JsonObject(); JsonArray keys = new JsonArray(); path.forEach(keys::add);
            row.add("path", keys); row.addProperty("declared", source.declared(path));
            boolean present = data.contains(path); row.addProperty("present", present);
            if (present) row.add("value", copy(data.getRaw(path), 0, nodes));
            rows.add(row);
        }
        return rows;
    }

    private static JsonElement copy(Object value, int depth, int[] nodes) {
        if (++nodes[0] > 4096 || depth > 8) throw new Rejected("quota_exceeded");
        if (value instanceof String s) {
            if (s.getBytes(StandardCharsets.UTF_8).length > 4096) throw new Rejected("quota_exceeded");
            // Do not silently replace malformed UTF-16 when serializing.
            if (!StandardCharsets.UTF_8.newEncoder().canEncode(s)) throw new Rejected("unsupported_value");
            return primitive(new JsonPrimitive(s), nodes);
        }
        if (value instanceof Boolean b) return primitive(new JsonPrimitive(b), nodes);
        if (value instanceof Integer || value instanceof Long) {
            long n = ((Number)value).longValue();
            if (n < -MAX_INTEGER || n > MAX_INTEGER) throw new Rejected("unsupported_value");
            return primitive(new JsonPrimitive(n), nodes);
        }
        if (value instanceof Double d && Double.isFinite(d)) return primitive(new JsonPrimitive(d), nodes);
        if (value instanceof List<?> list) {
            if (list.size() > 4096) throw new Rejected("quota_exceeded");
            JsonArray array = new JsonArray();
            for (Object item : list) array.add(copy(item, depth + 1, nodes));
            return array;
        }
        throw new Rejected("unsupported_value");
    }

    private static JsonPrimitive primitive(JsonPrimitive value, int[] quota) {
        quota[1] += value.toString().getBytes(StandardCharsets.UTF_8).length;
        if (quota[1] > 65536) throw new Rejected("quota_exceeded");
        return value;
    }

    private static final class Rejected extends RuntimeException {
        final String code;
        Rejected(String code) { this.code = code; }
    }
}
