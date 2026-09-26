package io.github.opencnid.strata.livebody;

import java.io.*;
import java.net.*;
import java.nio.file.*;
import java.lang.reflect.InvocationTargetException;
import java.util.*;

/** Synthetic NBT through actual game codecs; never a live-player witness. */
public final class PlayerNbtTest {
    interface Attempt { void run() throws Exception; }
    static void refuses(String code, Attempt attempt) throws Exception {
        try { attempt.run(); } catch (Exception error) {
            Throwable actual = error instanceof InvocationTargetException ? error.getCause() : error;
            if (actual instanceof IOException && code.equals(actual.getMessage())) return;
            throw error;
        }
        throw new AssertionError("expected " + code);
    }
    public static void main(String[] args) throws Exception {
        if (args[0].equals("bounds")) {
            var bytes = new PlayerNbt.BoundedBytes(4);
            bytes.write(new byte[] {1, 2, 3}, 0, 3);
            refuses("PLAYER_NBT_QUOTA", () -> bytes.write(new byte[2], 0, 2));
            bytes.write(4);
            refuses("PLAYER_NBT_QUOTA", () -> bytes.write(5));
            if (!Arrays.equals(bytes.result(), new byte[] {1, 2, 3, 4})) throw new AssertionError();
            byte[] copy = bytes.result();
            copy[0] = 99;
            if (bytes.result()[0] != 1) throw new AssertionError("mutable result");
            System.out.println("bounded-output-pass");
            return;
        }
        Path jar = Path.of(args[1]);
        List<URL> urls = new ArrayList<>();
        urls.add(jar.toUri().toURL());
        try (var paths = Files.walk(jar.getParent().getParent().getParent().resolve("libraries"))) {
            for (Path path : paths.filter(p -> p.toString().endsWith(".jar")).sorted().toList())
                urls.add(path.toUri().toURL());
        }
        if (urls.size() < 2 || urls.size() > 256) throw new AssertionError("library bounds");
        try (var loader = new URLClassLoader(urls.toArray(URL[]::new), PlayerNbtTest.class.getClassLoader())) {
            PlayerNbt codec = new PlayerNbt(loader);
            refuses("PLAYER_NBT_IDENTITY", () -> codec.capture(new Object(), UUID.randomUUID()));
            refuses("PLAYER_NBT_IDENTITY", () -> codec.capture(null, null));
            refuses("PLAYER_NBT_TYPE", () -> codec.encode(new Object()));
            if (args[0].equals("bindings")) {
                System.out.println("actual-descriptors-pass; no game initialization");
                return;
            }
            Object tag;
            try (var input = new DataInputStream(Files.newInputStream(Path.of(args[2])))) {
                tag = Class.forName("pt", true, loader).getMethod("a", DataInput.class).invoke(null, input);
                if (input.read() != -1) throw new AssertionError("trailing input");
            }
            if (args[0].equals("oversize")) {
                refuses("PLAYER_NBT_QUOTA", () -> codec.encode(tag));
                System.out.println("actual-oversize-refused");
            } else {
                Files.write(Path.of(args[3]), codec.encode(tag), StandardOpenOption.CREATE_NEW);
                System.out.println("actual-nbt-roundtrip; synthetic data; no player capture");
            }
        }
    }
}
