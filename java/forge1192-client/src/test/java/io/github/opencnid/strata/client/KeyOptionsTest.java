package io.github.opencnid.strata.client;

import java.io.IOException;
import java.nio.file.Path;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import static org.junit.jupiter.api.Assertions.*;

class KeyOptionsTest {
    @Test void firstLaunchWithoutOptionsDoesNotInventPersistedValues(@TempDir Path root) throws Exception {
        KeyOptions options = KeyOptions.read(root.resolve("options.txt"));
        assertNull(options.fileDigest());
        assertTrue(options.values().isEmpty());
    }

    @Test void extractsOnlyPhysicalKeyFieldsAndRetainsModifierEncoding() throws Exception {
        KeyOptions options = KeyOptions.parse("lastServer:private.example\nrenderDistance:12\n"
            + "key_key.inventory:key.keyboard.e\nkey_mod.test:key.keyboard.f13:SHIFT\n");
        assertEquals(2, options.values().size());
        assertEquals("key.keyboard.f13:SHIFT", options.values().get("mod.test"));
        assertFalse(options.values().containsKey("lastServer"));
        assertEquals(64, options.fileDigest().length());
        assertThrows(UnsupportedOperationException.class, () -> options.values().put("new", "bad"));
    }

    @Test void duplicatePersistedFieldsHaveNoUnambiguousValue() throws Exception {
        KeyOptions options = KeyOptions.parse("key_mod.test:key.keyboard.a\nkey_mod.test:key.keyboard.b\n");
        assertTrue(options.ambiguous().contains("mod.test"));
        assertFalse(options.values().containsKey("mod.test"));
        assertThrows(IOException.class, () -> KeyOptions.parse("key_missingSeparator\n"));
        assertThrows(IOException.class, () -> KeyOptions.parse("key_test:\0\n"));
    }

    @Test void identifiersPreserveRegistrationOccurrenceAndBoundUnusualTranslations() {
        assertEquals("owner:key.mod.action:2", KeyOptions.stableId("owner", "key.mod.action", 2));
        String unusual = KeyOptions.stableId("unknown", "Unicode 控制:".repeat(100), 0);
        assertTrue(unusual.matches("[A-Za-z0-9_.:-]{1,128}"));
        assertEquals(unusual, KeyOptions.stableId("unknown", "Unicode 控制:".repeat(100), 0));
        assertNotEquals(unusual, KeyOptions.stableId("unknown", "Unicode 控制:".repeat(100), 1));
        assertThrows(IllegalArgumentException.class, () -> KeyOptions.stableId("bad/name", "x", 0));
    }
}
