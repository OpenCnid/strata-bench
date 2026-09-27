package io.github.opencnid.strata.livebody;

import java.net.*;
import java.nio.file.*;
import java.util.*;
import java.util.jar.*;

/** Actual private JVM instrumentation with no Minecraft initialization. */
public final class BodyAgentTest {
    public static void main(String[] args) throws Exception {
        if (args[0].equals("forged")) {
            BodyObserver.start(new Object());
            throw new AssertionError("forged callback returned");
        }
        Path server = Path.of(args[1]);
        List<URL> urls = new ArrayList<>();
        urls.add(server.toUri().toURL());
        try (var paths = Files.walk(server.getParent().getParent().getParent().resolve("libraries"))) {
            for (Path path : paths.filter(p -> p.toString().endsWith(".jar")).sorted().toList())
                urls.add(path.toUri().toURL());
        }
        if (urls.size() < 2 || urls.size() > 256) throw new AssertionError("library bounds");
        try (var loader = new URLClassLoader(urls.toArray(URL[]::new), ClassLoader.getPlatformClassLoader()) {
            @Override protected Class<?> findClass(String name) throws ClassNotFoundException {
                if ((!args[0].equals("changed") && !args[0].equals("foreign")) || !name.equals("agh"))
                    return super.findClass(name);
                try (JarFile jar = new JarFile(server.toFile())) {
                    JarEntry entry = jar.getJarEntry("agh.class");
                    byte[] raw = jar.getInputStream(entry).readAllBytes();
                    if (args[0].equals("changed")) raw[raw.length - 1] ^= 1;
                    return defineClass(name, raw, 0, raw.length,
                        new java.security.CodeSource((args[0].equals("foreign") ? server.getParent() : server).toUri().toURL(),
                            entry.getCodeSigners()));
                } catch (Exception error) { throw new ClassNotFoundException(name, error); }
            }
        }) {
            for (String name : List.of("net.minecraft.server.MinecraftServer", "agh", "bbn", "pj", "pt", "ayz")) {
                Class<?> type = Class.forName(name, false, loader);
                if (type.getDeclaredMethods().length == 0) throw new AssertionError("empty methods");
            }
            if (BodyObserver.class.getClassLoader() != null) throw new AssertionError("callback not bootstrap");
            if (args[0].equals("duplicate")) {
                try (var sibling = new URLClassLoader(urls.toArray(URL[]::new), ClassLoader.getPlatformClassLoader())) {
                    Class.forName("agh", false, sibling).getDeclaredMethods();
                    throw new AssertionError("duplicate loader returned");
                }
            }
        }
        System.out.println("actual-instrumented-methods-pass; no game initialization or player capture");
    }
}
