package io.github.opencnid.strata.telemetry;

import com.electronwill.nightconfig.core.Config;
import com.electronwill.nightconfig.core.UnmodifiableConfig;
import com.google.gson.JsonObject;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Set;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class ConfigSnapshotTest {
    private static final List<String> PATH = List.of("quoted.key", "items");
    private static final ConfigQuery QUERY = new ConfigQuery("fixture-common.toml", List.of(PATH, List.of("absent")));

    static class Fixture implements ConfigSnapshot.Source {
        final Object identity = new Object(), spec = new Object();
        Config data = Config.inMemory();
        boolean loaded = true;
        Set<List<String>> declared = Set.of(PATH);
        public Object identity() { return identity; }
        public String modId() { return "fixture"; }
        public String type() { return "COMMON"; }
        public Object spec() { return spec; }
        public boolean loaded() { return loaded; }
        public UnmodifiableConfig data() { return data; }
        public boolean declared(List<String> path) { return declared.contains(path); }
        JsonObject capture() { return ConfigSnapshot.capture(QUERY, this, identity, true); }
    }

    @Test void preservesTypedSelectedRawDataAndOmittedKeysWithoutMutatingSource() {
        Fixture fixture = new Fixture();
        List<Object> items = new ArrayList<>(List.of(true, 1, 1.0, "text"));
        fixture.data.set(PATH, items); fixture.data.set("private_unselected", new Object());
        JsonObject result = fixture.capture();
        assertEquals("snapshot", result.get("status").getAsString());
        assertEquals("[true,1,1.0,\"text\"]", result.getAsJsonArray("values").get(0).getAsJsonObject().get("value").toString());
        JsonObject missing = result.getAsJsonArray("values").get(1).getAsJsonObject();
        assertFalse(missing.get("present").getAsBoolean()); assertFalse(missing.has("value"));
        assertFalse(missing.get("declared").getAsBoolean());
        assertSame(items, fixture.data.getRaw(PATH));
        items.add("later"); assertFalse(result.toString().contains("later"));
        assertFalse(result.toString().contains("private_unselected"));
    }

    @Test void distinguishesAbsentUnloadedUnknownAndUndeclaredPresent() {
        assertEquals("unregistered", ConfigSnapshot.capture(QUERY, null, null, false).get("status").getAsString());
        Fixture f = new Fixture(); f.loaded = false;
        assertEquals("unloaded", f.capture().get("status").getAsString());
        assertEquals("unsupported_spec", ConfigSnapshot.capture(QUERY, f, f.identity, false).get("status").getAsString());
        f.loaded = true; f.data.set(PATH, 3); f.declared = Set.of();
        JsonObject row = f.capture().getAsJsonArray("values").get(0).getAsJsonObject();
        assertFalse(row.get("declared").getAsBoolean()); assertTrue(row.get("present").getAsBoolean());
    }

    @Test void changingDataIdentitySpecAndRegistrationNeverEmitPartialSnapshot() {
        for (int mode = 0; mode < 5; mode++) {
            final int selected = mode;
            Fixture f = new Fixture() {
                int reads;
                public boolean declared(List<String> path) {
                    if (path.equals(PATH) && ++reads == 2) {
                        if (selected == 0) data.set(PATH, 2);
                        if (selected == 1) data = Config.copy(data);
                        if (selected == 4) loaded = false;
                    }
                    return super.declared(path);
                }
                public Object identity() { return selected == 2 ? new Object() : identity; }
                public Object spec() { return selected == 3 ? new Object() : spec; }
            };
            f.data.set(PATH, 1); JsonObject result = f.capture();
            assertEquals("unstable", result.get("status").getAsString());
            assertFalse(result.has("values")); assertFalse(result.has("consistency"));
        }
    }

    @Test void unsupportedValuesAndReadFailuresRemainExplicitWithoutCoercion() {
        for (Object value : List.of(Double.NaN, Double.POSITIVE_INFINITY, 9007199254740992L,
                new Object(), 1.0f, Config.inMemory(), "\ud800")) {
            Fixture f = new Fixture(); f.data.set(PATH, value); JsonObject result = f.capture();
            assertEquals("unsupported_value", result.get("status").getAsString());
            assertFalse(result.has("values"));
        }
        Fixture failed = new Fixture() {
            public boolean declared(List<String> path) { throw new IllegalStateException("private error"); }
        };
        JsonObject result = failed.capture();
        assertEquals("read_failed", result.get("status").getAsString());
        assertFalse(result.toString().contains("private error"));
    }

    @Test void boundsNodesDepthStringsAndWholePayloadWithoutTruncation() {
        Object nested = "x"; for (int i = 0; i < 9; i++) nested = List.of(nested);
        for (Object value : List.of(nested, "x".repeat(4097), Collections.nCopies(4096, 1),
                Collections.nCopies(17, "x".repeat(4096)))) {
            Fixture f = new Fixture(); f.data.set(PATH, value); JsonObject result = f.capture();
            assertEquals("quota_exceeded", result.get("status").getAsString()); assertFalse(result.has("values"));
        }
    }
}
