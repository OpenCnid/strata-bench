package io.github.opencnid.strata.client;

import com.google.gson.JsonObject;
import java.nio.file.Files;
import java.nio.file.Path;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import static org.junit.jupiter.api.Assertions.*;

class GameBootstrapTest {
    @TempDir Path root;
    @Test void publishesExactIdentityBeforeAuthorityAndNeverTreatsPublicationAsAdmission() throws Exception {
        var identity = new JsonObject(); identity.addProperty("artifact", "pinned<&>");
        var bootstrap = new GameBootstrap(root, KeyOptions.sha256(identity.toString()), identity);
        var record = SettingsJson.read(Files.readString(root.resolve("game-bootstrap.json")));
        assertEquals(identity.toString(), record.get("identity_json").getAsString());
        assertEquals(KeyOptions.sha256(record.get("identity_json").getAsString()), record.get("fingerprint").getAsString());
        for (int i=0;i<5;i++) assertFalse(bootstrap.authorityPresent());
        Files.writeString(root.resolve("game-authority.json"), "{}");
        assertTrue(bootstrap.authorityPresent());
        assertThrows(java.io.IOException.class, () -> GameActionLane.Authority.read(SettingsJson.read("{}")));
    }
    @Test void mismatchedIdentityAndOversizedManifestCannotPublish() {
        var identity = new JsonObject(); identity.addProperty("artifact", "pin");
        assertThrows(java.io.IOException.class, () -> new GameBootstrap(root, "0".repeat(64), identity));
        assertFalse(Files.exists(root.resolve("game-bootstrap.json")));
        identity.addProperty("large", "a".repeat(524288));
        assertThrows(java.io.IOException.class, () -> new GameBootstrap(root, KeyOptions.sha256(identity.toString()), identity));
        assertFalse(Files.exists(root.resolve("game-bootstrap.json")));
    }
    @Test void retainedIdentityIsNeverOverwrittenAndDirectoryCannotBeAuthority() throws Exception {
        var identity = new JsonObject(); identity.addProperty("artifact", "pin");
        var bootstrap = new GameBootstrap(root, KeyOptions.sha256(identity.toString()), identity);
        byte[] before = Files.readAllBytes(root.resolve("game-bootstrap.json"));
        assertThrows(java.io.IOException.class, () -> new GameBootstrap(root, KeyOptions.sha256(identity.toString()), identity));
        assertArrayEquals(before, Files.readAllBytes(root.resolve("game-bootstrap.json")));
        Files.createDirectory(root.resolve("game-authority.json"));
        assertThrows(java.io.IOException.class, bootstrap::authorityPresent);
    }
}
