package io.github.opencnid.strata.telemetry;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.file.Files;
import java.nio.file.Path;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

class LaunchIdentityTest {
    @TempDir Path root;
    @Test void observesThisProcessAndCanonicalPaths() throws Exception {
        Path world = Files.createDirectory(root.resolve("world"));
        Path module = Files.writeString(root.resolve("module.jar"), "abc");
        var identity = LaunchIdentity.observe(root, world.resolve("."), module, true, 25566);
        assertEquals(ProcessHandle.current().pid(), identity.get("pid").getAsLong());
        assertEquals(ProcessHandle.current().info().startInstant().orElseThrow().toEpochMilli(),
            identity.get("process_started_unix_ms").getAsLong());
        assertEquals(world.toRealPath().toString(), identity.get("world_directory").getAsString());
        assertEquals("ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad", identity.get("module_sha256").getAsString());
        assertFalse(identity.has("arguments"));
    }
    @Test void missingArtifactNeverProducesIdentity() throws Exception {
        assertThrows(java.io.IOException.class,
            () -> LaunchIdentity.observe(root, root, root.resolve("missing"), false, 25566));
    }
}
