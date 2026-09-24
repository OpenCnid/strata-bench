package io.github.opencnid.strata.fixed;

import java.io.*;
import java.net.*;
import java.nio.file.*;
import java.security.Permission;
import java.util.*;

public final class RuntimeDataFixture {
    @SuppressWarnings("removal")
    public static void main(String[] args) throws Exception {
        System.setSecurityManager(new SecurityManager() {
            @Override public void checkPermission(Permission permission) {}
            @Override public void checkConnect(String host, int port) { throw new SecurityException("NETWORK_FORBIDDEN"); }
        });
        if (args.length > 0 && args[0].equals("patch")) {
            Files.write(Path.of(args[3]), Agent.patch(args[1], Files.readAllBytes(Path.of(args[2]))));
            return;
        }
        if (args.length > 0 && args[0].equals("drift")) {
            new Agent().transform(null, "com/portingdeadmods/cable_facades/CFConfig", null, null, new byte[10]);
            throw new AssertionError("did not halt");
        }
        int checked = 0;
        for (String url : new TreeSet<>(Data.ROUTES.keySet())) {
            HttpURLConnection connection = (HttpURLConnection)new URL(url).openConnection();
            connection.setRequestMethod("GET");
            if (connection.getResponseCode() != 200 || connection.usingProxy()) throw new AssertionError();
            byte[] first = connection.getInputStream().readAllBytes();
            byte[] second = new URL(url).openStream().readAllBytes();
            if (!Arrays.equals(first, second) || !Arrays.equals(first, Data.read(url))) throw new AssertionError();
            if (connection.getContentLengthLong() != first.length) throw new AssertionError();
            System.out.println(Data.ROUTES.get(url) + " " + Data.sha256(first)); checked++;
            for (String changed : List.of(url + "?changed", url + "#fragment", url.replace(".com/", ".com:443/"),
                    url.replace("raw.githubusercontent.com", "other.invalid"))) {
                try { new URL(changed).openStream(); throw new AssertionError("route accepted"); }
                catch (IOException expected) { checked++; }
            }
            HttpURLConnection post = (HttpURLConnection)new URL(url).openConnection();
            post.setRequestMethod("POST");
            try { post.getInputStream(); throw new AssertionError("method accepted"); }
            catch (IOException expected) { checked++; }
        }
        if (checked != 18) throw new AssertionError();
        System.out.println("FIXED_DATA_FIXTURE_PASS " + checked);
    }
}
