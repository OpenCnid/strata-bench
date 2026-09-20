package io.github.opencnid.strata.telemetry;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.Arrays;
import java.util.HexFormat;

/** Reuses exact private selectors; this diagnostic admits one connected-client snapshot only. */
record ClientConfigPlan(Path source, String sha256, TelemetryConfig config) {
    static ClientConfigPlan read(Path source, Path game) throws IOException {
        TelemetryConfig.safeExisting(source);
        if (Files.size(source) > 65536) throw new IOException("CLIENT_CONFIG_PLAN_QUOTA");
        byte[] before = Files.readAllBytes(source);
        TelemetryConfig config = TelemetryConfig.read(source, game);
        if (config.maxEvents() != 1 || config.maxBytes() > 1048576
                || !config.recipeIds().isEmpty() || config.configQueries().isEmpty()) {
            throw new IOException("CLIENT_CONFIG_PLAN_SCOPE");
        }
        if (!Arrays.equals(before, Files.readAllBytes(source))) throw new IOException("CLIENT_CONFIG_PLAN_CHANGED");
        return new ClientConfigPlan(source, hash(before), config);
    }

    void unchanged() throws IOException {
        TelemetryConfig.safeExisting(source);
        if (Files.size(source) > 65536 || !hash(Files.readAllBytes(source)).equals(sha256)) {
            throw new IOException("CLIENT_CONFIG_PLAN_CHANGED");
        }
    }

    private static String hash(byte[] value) {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(value)); }
        catch (NoSuchAlgorithmException error) { throw new AssertionError(error); }
    }
}
