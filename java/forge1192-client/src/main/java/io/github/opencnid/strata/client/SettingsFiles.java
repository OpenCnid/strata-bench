package io.github.opencnid.strata.client;

import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.channels.FileChannel;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.FileSystems;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.nio.file.StandardOpenOption;
import java.util.Map;
import java.util.TreeMap;
import java.util.UUID;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/** Narrow options patches. Call only from the owning client thread under its profile lock. */
final class SettingsFiles {
    static final int MAX_OPTIONS = 1048576;
    private static final Pattern LINES = Pattern.compile("([^\\r\\n]*)(\\r\\n|\\n|\\r|$)");

    static Path safeExisting(Path input) throws IOException {
        // Writable options/journals must never use a loader-owned virtual filesystem.
        if (input.getFileSystem() != FileSystems.getDefault()) throw new IOException("SETTINGS_UNSAFE_PATH");
        Path path = input.toAbsolutePath().normalize();
        if (!input.isAbsolute() || !input.equals(path) || !Files.exists(path, LinkOption.NOFOLLOW_LINKS)) {
            throw new IOException("SETTINGS_UNSAFE_PATH");
        }
        for (Path parent = path; parent != null; parent = parent.getParent()) {
            if (Files.isSymbolicLink(parent) || !parent.toRealPath().equals(parent)) {
                throw new IOException("SETTINGS_UNSAFE_PATH");
            }
        }
        return path;
    }

    static String readOptions(Path path) throws IOException {
        safeExisting(path);
        if (!Files.isRegularFile(path) || Files.size(path) > MAX_OPTIONS) throw new IOException("OPTIONS_UNAVAILABLE");
        try (var stream = Files.newInputStream(path)) {
            byte[] bytes = stream.readNBytes(MAX_OPTIONS + 1);
            if (bytes.length > MAX_OPTIONS) throw new IOException("OPTIONS_UNAVAILABLE");
            return StandardCharsets.UTF_8.newDecoder().decode(ByteBuffer.wrap(bytes)).toString();
        }
    }

    static void keyField(String translation, String value) throws IOException {
        if (!translation.matches("[A-Za-z0-9_.-]{1,256}") || value.isEmpty() || value.length() > 256
                || !value.matches("[a-z0-9_.-]+(?::(?:SHIFT|CONTROL|ALT))?")) {
            throw new IOException("UNSUPPORTED_KEY_FIELD");
        }
    }

    static String patch(String original, Map<String, String> expected, Map<String, String> desired) throws IOException {
        if (expected.isEmpty() || expected.size() > 32 || !expected.keySet().equals(desired.keySet())) {
            throw new IOException("SETTINGS_PATCH_INVALID");
        }
        KeyOptions options = KeyOptions.parse(original);
        for (var entry : expected.entrySet()) {
            keyField(entry.getKey(), entry.getValue());
            keyField(entry.getKey(), desired.get(entry.getKey()));
            if (!entry.getValue().equals(options.values().get(entry.getKey()))) {
                throw new IOException("OPTIONS_REVISION_CONFLICT");
            }
        }
        StringBuilder output = new StringBuilder(original.length());
        Matcher lines = LINES.matcher(original);
        while (lines.find()) {
            String line = lines.group(1);
            int colon = line.indexOf(':');
            String translation = line.startsWith("key_") && colon >= 5 ? line.substring(4, colon) : null;
            if (translation != null && desired.containsKey(translation)) {
                output.append("key_").append(translation).append(':').append(desired.get(translation));
            } else output.append(line);
            output.append(lines.group(2));
        }
        String result = output.toString();
        if (result.getBytes(StandardCharsets.UTF_8).length > MAX_OPTIONS) throw new IOException("OPTIONS_TOO_LARGE");
        return result;
    }

    static String nonOwnedDigest(String original, Map<String, String> owned) throws IOException {
        KeyOptions options = KeyOptions.parse(original);
        Map<String, String> current = new TreeMap<>(), masked = new TreeMap<>();
        for (String translation : owned.keySet()) {
            String value = options.values().get(translation);
            if (value == null) throw new IOException("OPTIONS_REVISION_CONFLICT");
            current.put(translation, value);
            masked.put(translation, "strata.owned.field");
        }
        return KeyOptions.sha256(patch(original, current, masked));
    }

    static void writeNew(Path target, byte[] bytes) throws IOException {
        safeExisting(target.getParent());
        try (FileChannel file = FileChannel.open(target, StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE)) {
            ByteBuffer buffer = ByteBuffer.wrap(bytes);
            while (buffer.hasRemaining()) file.write(buffer);
            file.force(true);
        }
    }

    static void replaceOwned(Path options, String expectedText, String replacement) throws IOException {
        if (!readOptions(options).equals(expectedText)) throw new IOException("OPTIONS_REVISION_CONFLICT");
        Path temporary = options.resolveSibling(".strata-options-" + UUID.randomUUID() + ".tmp");
        try {
            writeNew(temporary, replacement.getBytes(StandardCharsets.UTF_8));
            if (!readOptions(options).equals(expectedText)) throw new IOException("OPTIONS_REVISION_CONFLICT");
            // No non-atomic fallback. The profile lock and client thread exclude
            // cooperating writers; deployment must also exclude foreign writers.
            Files.move(temporary, options, StandardCopyOption.ATOMIC_MOVE, StandardCopyOption.REPLACE_EXISTING);
            if (!readOptions(options).equals(replacement)) throw new IOException("OPTIONS_WRITE_UNCONFIRMED");
        } finally {
            // Only our exact fresh temporary file, never an existing game file.
            Files.deleteIfExists(temporary);
        }
    }
}
