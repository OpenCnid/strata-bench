import io.github.opencnid.strata.vanillaclock.Agent;
import java.net.*;
import java.nio.file.*;
import java.util.*;
import java.util.jar.*;

/** Verify real method bodies without initializing game classes or starting a server. */
public class ActualClassVerifyTest {
    public static void main(String[] args) throws Exception {
        Path server = Path.of(args[0]);
        List<URL> urls = new ArrayList<>();
        urls.add(server.toUri().toURL());
        Path libraries = server.getParent().getParent().getParent().resolve("libraries");
        try (var paths = Files.walk(libraries)) {
            for (Path jar : paths.filter(p -> p.toString().endsWith(".jar")).sorted().toList())
                urls.add(jar.toUri().toURL());
        }
        if (urls.size() < 2 || urls.size() > 256) throw new AssertionError("library fixture bounds");
        try (URLClassLoader loader = new URLClassLoader(urls.toArray(URL[]::new), ActualClassVerifyTest.class.getClassLoader()) {
            @Override protected Class<?> findClass(String name) throws ClassNotFoundException {
                String internal = name.replace('.', '/');
                if (!Agent.PINS.containsKey(internal)) return super.findClass(name);
                try (JarFile jar = new JarFile(server.toFile())) {
                    JarEntry entry = jar.getJarEntry(internal + ".class");
                    byte[] input = jar.getInputStream(entry).readAllBytes();
                    byte[] patched = Agent.patch(internal, input);
                    // Instrumentation preserves the original protection domain.
                    return defineClass(name, patched, 0, patched.length,
                        new java.security.CodeSource(server.toUri().toURL(), entry.getCodeSigners()));
                } catch (Exception error) { throw new ClassNotFoundException(name, error); }
            }
        }) {
            for (String internal : new TreeSet<>(Agent.PINS.keySet())) {
                Class<?> type = Class.forName(internal.replace('/', '.'), false, loader);
                // Merely loading the byte array may defer method verification.
                // Reflection forces verification, without class initialization.
                if (type.getDeclaredMethods().length == 0) throw new AssertionError("missing methods");
            }
        }
        System.out.println("actual-class-method-verification-pass; no game initialization");
    }
}
