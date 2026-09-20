package io.github.opencnid.strata.client;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.Collections;
import java.util.HexFormat;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.Map;
import java.util.Set;

/** Reads only persisted key fields; never exposes server addresses or other options. */
record KeyOptions(String fileDigest, Map<String, String> values, Set<String> ambiguous) {
    static KeyOptions read(Path path) throws IOException {
        if (!Files.exists(path, java.nio.file.LinkOption.NOFOLLOW_LINKS)) {
            return new KeyOptions(null, Map.of(), Set.of());
        }
        if (!Files.isRegularFile(path) || Files.isSymbolicLink(path)
                || !path.toAbsolutePath().normalize().equals(path.toRealPath())
                || Files.size(path) > 1048576) throw new IOException("OPTIONS_UNAVAILABLE");
        return parse(Files.readString(path));
    }

    static KeyOptions parse(String text) throws IOException {
        if (text.length() > 1048576 || text.indexOf('\0') >= 0) throw new IOException("OPTIONS_INVALID");
        Map<String, String> values = new LinkedHashMap<>();
        Set<String> ambiguous = new LinkedHashSet<>();
        // Match BufferedReader/readLine and the owned-field patcher. Unicode
        // separators inside a value must not masquerade as new options fields.
        for (String line : text.split("\\r\\n|\\r|\\n", -1)) {
            if (!line.startsWith("key_")) continue;
            int colon = line.indexOf(':');
            if (colon < 5 || line.length() > 2048) throw new IOException("OPTIONS_INVALID");
            String name = line.substring(4, colon);
            String value = line.substring(colon + 1);
            if (values.putIfAbsent(name, value) != null) ambiguous.add(name);
            if (values.size() > 2048) throw new IOException("KEYMAP_TOO_LARGE");
        }
        for (String name : ambiguous) values.remove(name);
        return new KeyOptions(sha256(text), Collections.unmodifiableMap(values), Set.copyOf(ambiguous));
    }

    static String sha256(String value) {
        try {
            return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256")
                .digest(value.getBytes(java.nio.charset.StandardCharsets.UTF_8)));
        } catch (NoSuchAlgorithmException error) { throw new IllegalStateException(error); }
    }

    static String stableId(String owner, String translation, int occurrence) {
        if (!owner.matches("[a-z0-9_.-]{1,64}") || occurrence < 0) throw new IllegalArgumentException("BINDING_ID_INVALID");
        String key = translation.matches("[A-Za-z0-9_.:-]{1,48}") ? translation : "sha256-" + sha256(translation).substring(0, 32);
        return owner + ":" + key + ":" + occurrence;
    }
}
