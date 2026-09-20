package io.github.opencnid.strata.client;

import com.google.gson.JsonObject;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;

/** Operator-only identity publication before any action lane is constructed. */
final class GameBootstrap {
    private final Path root;
    GameBootstrap(Path root, String fingerprint, JsonObject identity) throws IOException {
        this.root = SettingsFiles.safeExisting(root);
        if (!Files.isDirectory(root) || !KeyOptions.sha256(identity.toString()).equals(fingerprint)) {
            throw new IOException("GAME_BOOTSTRAP_IDENTITY_INVALID");
        }
        var value = new JsonObject();
        value.addProperty("schema", "strata/PrivateGameBootstrap/1");
        value.addProperty("fingerprint", fingerprint);
        // Preserve the exact Gson bytes whose hash forms the native fingerprint.
        value.addProperty("identity_json", identity.toString());
        byte[] bytes = (value + "\n").getBytes(StandardCharsets.UTF_8);
        if (bytes.length > 524288) throw new IOException("GAME_BOOTSTRAP_TOO_LARGE");
        SettingsFiles.writeNew(root.resolve("game-bootstrap.json"), bytes);
    }
    boolean authorityPresent() throws IOException {
        Path authority = root.resolve("game-authority.json");
        if (!Files.exists(authority, java.nio.file.LinkOption.NOFOLLOW_LINKS)) return false;
        SettingsFiles.safeExisting(authority);
        if (!Files.isRegularFile(authority)) throw new IOException("GAME_BOOTSTRAP_AUTHORITY_INVALID");
        return true; // The existing strict authority parser still decides admission.
    }
}
