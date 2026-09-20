package io.github.opencnid.strata.client;

import cpw.mods.niofs.union.UnionFileSystem;
import java.io.IOException;
import java.nio.file.FileSystems;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;
import net.minecraftforge.jarjar.nio.pathfs.PathFileSystem;

/** Read-only hashing of paths returned by the pinned Forge mod loader, never caller paths. */
final class ArtifactFiles {
    static final String POLICY = "forge-loaded-file-and-jarjar-bytes/2";
    private static final long MAX_BYTES = 536870912L;

    private static void validate(Path path, int depth) throws IOException {
        if (depth > 8 || path == null) throw new IOException("SETTINGS_ARTIFACT_INVALID");
        if (path.getFileSystem() == FileSystems.getDefault()) {
            SettingsFiles.safeExisting(path);
        } else if (path.getFileSystem() instanceof UnionFileSystem union) {
            // Validate the union's backing artifact without reconstructing a host
            // path from its URI or the entry's basename.
            validate(union.getPrimaryPath(), depth + 1);
        } else if (path.getFileSystem() instanceof PathFileSystem) {
            // Forge JarJar's PathPath.toRealPath() is explicitly unimplemented
            // and returns null; normalize() also has different root semantics.
            // Preserve the loader's path and hash its actual regular entry stream.
            // This exception is only for loader-supplied read-only artifact paths;
            // it is not a general path-safety check or an installation seal.
        } else {
            throw new IOException("SETTINGS_ARTIFACT_FILESYSTEM_UNSUPPORTED");
        }
        if (!Files.isRegularFile(path) || Files.isSymbolicLink(path)
                || Files.size(path) > MAX_BYTES) throw new IOException("SETTINGS_ARTIFACT_INVALID");
    }

    static String hash(Path path) throws IOException {
        validate(path, 0);
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            long count = 0;
            try (var input = Files.newInputStream(path)) {
                byte[] buffer = new byte[65536];
                for (int n; (n = input.read(buffer)) != -1;) {
                    count += n;
                    if (count > MAX_BYTES) throw new IOException("SETTINGS_ARTIFACT_INVALID");
                    digest.update(buffer, 0, n);
                }
            }
            return HexFormat.of().formatHex(digest.digest());
        } catch (NoSuchAlgorithmException error) { throw new IllegalStateException(error); }
    }
}
