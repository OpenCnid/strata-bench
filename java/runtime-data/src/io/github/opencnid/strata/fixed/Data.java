package io.github.opencnid.strata.fixed;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.security.*;
import java.util.*;

/** Three immutable resource bodies; no URLs are fetched by this class. */
public final class Data {
    public static final Map<String, String> ROUTES = Map.of(
        "stratafixed://raw.githubusercontent.com/Porting-Dead-Mods/Cable-Facades/refs/heads/1.21.1/configs/whitelist.txt", "whitelist.txt",
        "stratafixed://raw.githubusercontent.com/Porting-Dead-Mods/Cable-Facades/refs/heads/1.21.1/configs/blacklist.txt", "blacklist.txt",
        "stratafixed://raw.githubusercontent.com/BluSunrize/ImmersiveEngineering/gh-pages/contributorRevolvers.json", "contributorRevolvers.json");
    private static Map<String, byte[]> bodies;
    private static String identity;

    public static String sha256(byte[] bytes) {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)); }
        catch (NoSuchAlgorithmException e) { throw new AssertionError(e); }
    }

    private static byte[] resource(String name, int maximum) throws IOException {
        try (InputStream input = Data.class.getResourceAsStream("/strata-fixed/" + name)) {
            if (input == null) throw new IOException("FIXED_DATA_MISSING");
            byte[] value = input.readNBytes(maximum + 1);
            if (value.length > maximum) throw new IOException("FIXED_DATA_QUOTA");
            return value;
        }
    }

    public static synchronized void verify() throws IOException {
        if (bodies != null) return;
        byte[] raw = resource("index.txt", 4096);
        String text = new String(raw, StandardCharsets.US_ASCII);
        if (!Arrays.equals(raw, text.getBytes(StandardCharsets.US_ASCII))) throw new IOException("FIXED_DATA_INDEX");
        String[] lines = text.split("\n", -1);
        if (lines.length != 4 || !lines[3].isEmpty()) throw new IOException("FIXED_DATA_INDEX");
        Map<String, byte[]> result = new HashMap<>();
        for (int i = 0; i < 3; i++) {
            String[] fields = lines[i].split(" ", -1);
            if (fields.length != 2 || !fields[0].matches("[0-9a-f]{64}")
                || !ROUTES.containsValue(fields[1]) || result.containsKey(fields[1]))
                throw new IOException("FIXED_DATA_INDEX");
            byte[] value = resource(fields[1], 1048576);
            if (!sha256(value).equals(fields[0])) throw new IOException("FIXED_DATA_HASH");
            result.put(fields[1], value);
        }
        bodies = Map.copyOf(result); identity = sha256(raw);
    }

    public static synchronized String identity() throws IOException { verify(); return identity; }
    public static synchronized byte[] read(String url) throws IOException {
        verify();
        String name = ROUTES.get(url);
        if (name == null) throw new IOException("FIXED_DATA_ROUTE");
        return bodies.get(name).clone();
    }
    private Data() {}
}
