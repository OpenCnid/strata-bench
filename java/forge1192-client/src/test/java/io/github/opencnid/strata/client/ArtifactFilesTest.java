package io.github.opencnid.strata.client;

import cpw.mods.niofs.union.UnionFileSystemProvider;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.RandomAccessFile;
import java.nio.file.FileSystems;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.Map;
import java.util.zip.ZipEntry;
import java.util.zip.ZipOutputStream;
import net.minecraftforge.jarjar.nio.pathfs.PathFileSystemProvider;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import static org.junit.jupiter.api.Assertions.*;

class ArtifactFilesTest {
    @TempDir Path root;
    byte[] zip(String entry, byte[] content) throws IOException {
        var bytes = new ByteArrayOutputStream();
        try (var zip = new ZipOutputStream(bytes)) {
            zip.putNextEntry(new ZipEntry(entry)); zip.write(content); zip.closeEntry();
        }
        return bytes.toByteArray();
    }
    String expected(byte[] bytes) throws Exception {
        return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes));
    }
    @Test void ordinaryFileHashesActualBytes() throws Exception {
        byte[] content = new byte[]{0, 1, 2, (byte)255};
        Path artifact = Files.write(root.resolve("mod.jar"), content);
        assertEquals(expected(content), ArtifactFiles.hash(artifact));
    }
    @Test void forgeNestedJarHashesEntryBytesAndPreservesWriterBoundary() throws Exception {
        byte[] nested = zip("nested-resource", new byte[]{4, 5, 6});
        Path artifact = Files.write(root.resolve("outer.jar"), zip("META-INF/jarjar/inner.jar", nested));
        var provider = new UnionFileSystemProvider();
        try (var union = provider.newFileSystem(null, artifact)) {
            Path entry = union.getPath("/META-INF/jarjar/inner.jar");
            assertEquals(expected(nested), ArtifactFiles.hash(entry));
            assertNotEquals(ArtifactFiles.hash(artifact), ArtifactFiles.hash(entry));
            assertEquals("SETTINGS_UNSAFE_PATH", assertThrows(IOException.class,
                () -> SettingsFiles.safeExisting(entry)).getMessage());
            assertThrows(IOException.class, () -> ArtifactFiles.hash(union.getPath("/")));
            assertThrows(IOException.class, () -> ArtifactFiles.hash(union.getPath("/missing.jar")));
        }
    }
    @Test void nestedUnionBackingAlsoValidatesAndHashes() throws Exception {
        byte[] inner = zip("resource", new byte[]{9, 8, 7});
        byte[] middle = zip("inner.jar", inner);
        Path outer = Files.write(root.resolve("outer.jar"), zip("middle.jar", middle));
        var provider = new UnionFileSystemProvider();
        try (var first = provider.newFileSystem(null, outer);
             var second = provider.newFileSystem(null, first.getPath("/middle.jar"))) {
            assertEquals(expected(inner), ArtifactFiles.hash(second.getPath("/inner.jar")));
        }
    }
    @Test void nonLoaderVirtualFilesystemsCannotBecomeWritableOrHashedArtifacts() throws Exception {
        Path jar = Files.write(root.resolve("other.jar"), zip("entry", new byte[]{1}));
        try (var zip = FileSystems.newFileSystem(jar, Map.of())) {
            assertEquals("SETTINGS_ARTIFACT_FILESYSTEM_UNSUPPORTED", assertThrows(IOException.class,
                () -> ArtifactFiles.hash(zip.getPath("/entry"))).getMessage());
            assertEquals("SETTINGS_UNSAFE_PATH", assertThrows(IOException.class,
                () -> SettingsFiles.safeExisting(zip.getPath("/entry"))).getMessage());
        }
    }
    @Test void actualJarJarNullRealPathStillHashesNestedArchiveBytes() throws Exception {
        byte[] nested = zip("resource", new byte[]{1, 7, 3});
        Path jar = Files.write(root.resolve("jarjar.jar"), zip("libraries/nested.jar", nested));
        try (var zip = FileSystems.newFileSystem(jar, Map.of());
             var jarjar = new PathFileSystemProvider().newFileSystem(zip.getPath("/libraries"))) {
            Path entry = jarjar.getPath("/nested.jar");
            assertNull(entry.toRealPath()); // Reproduces the actual pinned-provider failure.
            assertEquals(expected(nested), ArtifactFiles.hash(entry));
            assertEquals("SETTINGS_UNSAFE_PATH", assertThrows(IOException.class,
                () -> SettingsFiles.safeExisting(entry)).getMessage());
        }
    }
    @Test void missingDirectoryRelativeAndOversizedArtifactsRejectBeforeRead() throws Exception {
        assertThrows(IOException.class, () -> ArtifactFiles.hash(root));
        assertThrows(IOException.class, () -> ArtifactFiles.hash(root.resolve("missing.jar")));
        assertThrows(IOException.class, () -> ArtifactFiles.hash(Path.of("relative.jar")));
        Path large = root.resolve("too-large.jar");
        try (var file = new RandomAccessFile(large.toFile(), "rw")) { file.setLength(536870913L); }
        assertEquals("SETTINGS_ARTIFACT_INVALID", assertThrows(IOException.class,
            () -> ArtifactFiles.hash(large)).getMessage());
    }
}
