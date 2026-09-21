package io.github.opencnid.strata.telemetry;

import com.google.gson.JsonObject;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;

/** Native observations, never copied from an expected launcher identity. */
final class LaunchIdentity {
    static JsonObject observe(Path game, Path world, Path module, boolean online, int port) throws IOException {
        var process = ProcessHandle.current();
        var info = process.info();
        var result = new JsonObject();
        result.addProperty("policy", "native-server-launch-observation/1");
        result.addProperty("pid", process.pid());
        result.addProperty("process_started_unix_ms", info.startInstant().orElseThrow(
            () -> new IOException("TELEMETRY_PROCESS_IDENTITY")).toEpochMilli());
        result.addProperty("executable", Path.of(info.command().orElseThrow(
            () -> new IOException("TELEMETRY_PROCESS_IDENTITY"))).toRealPath().toString());
        result.addProperty("game_directory", game.toRealPath().toString());
        result.addProperty("world_directory", world.toRealPath().toString());
        result.addProperty("module_file", module.toRealPath().toString());
        result.addProperty("module_sha256", sha256(module));
        result.addProperty("online_mode", online);
        result.addProperty("server_port", port);
        return result;
    }

    private static String sha256(Path path) throws IOException {
        try (var stream = Files.newInputStream(path)) {
            var hash = MessageDigest.getInstance("SHA-256");
            byte[] bytes = new byte[65536];
            int read;
            while ((read = stream.read(bytes)) != -1) hash.update(bytes, 0, read);
            return HexFormat.of().formatHex(hash.digest());
        } catch (NoSuchAlgorithmException error) { throw new IOException("TELEMETRY_DIGEST", error); }
    }
}
