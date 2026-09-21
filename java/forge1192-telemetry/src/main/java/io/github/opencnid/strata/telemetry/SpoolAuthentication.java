package io.github.opencnid.strata.telemetry;

import com.google.gson.JsonObject;
import com.google.gson.stream.JsonReader;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.ByteBuffer;
import java.nio.channels.FileChannel;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.security.GeneralSecurityException;
import java.security.MessageDigest;
import java.util.Arrays;
import java.util.Base64;
import java.util.HashSet;
import java.util.HexFormat;
import java.util.Set;
import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;

/** Private launch key and challenge, never supplied through gameplay commands. */
record SpoolAuthentication(String challenge, Path keyFile, String keySha256, String authorityDigest) {
    static final String POLICY = "private-telemetry-hmac-sha256-chain/1";

    static SpoolAuthentication read(JsonReader reader, Path game) throws IOException {
        String challenge = null, key = null, sha = null, authority = null;
        Set<String> seen = new HashSet<>();
        reader.beginObject();
        while (reader.hasNext()) {
            String name = reader.nextName();
            if (!Set.of("challenge", "key_file", "key_sha256", "authority_digest").contains(name) || !seen.add(name))
                throw new IOException("TELEMETRY_AUTH_FIELDS");
            String value = TelemetryConfig.string(reader);
            switch (name) {
                case "challenge" -> challenge = value;
                case "key_file" -> key = value;
                case "key_sha256" -> sha = value;
                case "authority_digest" -> authority = value;
                default -> throw new IOException("TELEMETRY_AUTH_FIELDS");
            }
        }
        reader.endObject();
        if (seen.size() != 4 || !challenge.matches("[a-f0-9]{64}") || !sha.matches("[a-f0-9]{64}")
                || !authority.matches("[a-f0-9]{64}"))
            throw new IOException("TELEMETRY_AUTH_FIELDS");
        Path path = TelemetryConfig.safeExisting(Path.of(key));
        if (!Files.isRegularFile(path) || path.startsWith(game) || Files.size(path) != 32)
            throw new IOException("TELEMETRY_AUTH_KEY");
        return new SpoolAuthentication(challenge, path, sha, authority);
    }

    Signer signer(String boot) throws IOException {
        Path path = TelemetryConfig.safeExisting(keyFile);
        if (Files.size(path) != 32 || !challenge.matches("[a-f0-9]{64}")
                || !keySha256.matches("[a-f0-9]{64}") || !authorityDigest.matches("[a-f0-9]{64}")
                || !boot.matches("[A-Za-z0-9_.:-]{1,128}")) throw new IOException("TELEMETRY_AUTH_KEY");
        byte[] key;
        try (var stream = Files.newInputStream(path)) { key = stream.readNBytes(33); }
        try {
            if (key.length != 32 || !hex(MessageDigest.getInstance("SHA-256").digest(key)).equals(keySha256))
                throw new IOException("TELEMETRY_AUTH_KEY_CHANGED");
            Mac mac = Mac.getInstance("HmacSHA256");
            mac.init(new SecretKeySpec(key, "HmacSHA256"));
            String claimInput = POLICY + "\nclaim\n" + authorityDigest + "\n" + challenge + "\n" + boot + "\n";
            JsonObject claim = new JsonObject();
            claim.addProperty("schema", "strata/TelemetryBootClaim/1");
            claim.addProperty("challenge", challenge);
            claim.addProperty("authority_digest", authorityDigest);
            claim.addProperty("server_boot_id", boot);
            claim.addProperty("mac", hex(mac.doFinal(claimInput.getBytes(StandardCharsets.US_ASCII))));
            // Consume before opening the event stream. Crashes never silently
            // reuse a grant for another boot, even when no event became durable.
            Path claimFile = path.resolveSibling(path.getFileName() + ".claimed");
            try (FileChannel channel = FileChannel.open(claimFile, StandardOpenOption.CREATE_NEW,
                    StandardOpenOption.WRITE)) {
                ByteBuffer bytes = ByteBuffer.wrap((claim + "\n").getBytes(StandardCharsets.UTF_8));
                while (bytes.hasRemaining()) channel.write(bytes);
                channel.force(true);
            }
            return new Signer(challenge, authorityDigest, mac);
        } catch (GeneralSecurityException error) {
            throw new IOException("TELEMETRY_AUTH_UNAVAILABLE", error);
        } finally { Arrays.fill(key, (byte) 0); }
    }

    private static String hex(byte[] bytes) { return HexFormat.of().formatHex(bytes); }

    static final class Signer {
        private final String challenge;
        private final String authority;
        private final Mac mac;
        private String previous = "0".repeat(64);
        private long sequence;

        private Signer(String challenge, String authority, Mac mac) {
            this.challenge = challenge; this.authority = authority; this.mac = mac;
        }

        byte[] wrap(byte[] event, long next) throws IOException {
            if (next != sequence + 1 || event.length == 0 || event.length > 1048576)
                throw new IOException("TELEMETRY_AUTH_SEQUENCE");
            try {
                String hash = hex(MessageDigest.getInstance("SHA-256").digest(event));
                String input = POLICY + "\n" + authority + "\n" + challenge + "\n" + next + "\n" + previous + "\n" + hash + "\n";
                String signature = hex(mac.doFinal(input.getBytes(StandardCharsets.US_ASCII)));
                JsonObject record = new JsonObject();
                record.addProperty("schema", "strata/AuthenticatedTelemetry/1");
                record.addProperty("policy", POLICY);
                record.addProperty("challenge", challenge);
                record.addProperty("authority_digest", authority);
                record.addProperty("sequence", next);
                record.addProperty("previous_mac", previous);
                record.addProperty("event_base64", Base64.getEncoder().encodeToString(event));
                record.addProperty("mac", signature);
                previous = signature; sequence = next;
                return (record + "\n").getBytes(StandardCharsets.UTF_8);
            } catch (GeneralSecurityException error) {
                throw new IOException("TELEMETRY_AUTH_UNAVAILABLE", error);
            }
        }
    }
}
