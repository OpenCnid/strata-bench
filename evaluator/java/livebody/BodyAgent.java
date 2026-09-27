package io.github.opencnid.strata.livebody;

import java.io.*;
import java.lang.instrument.*;
import java.nio.file.*;
import java.security.ProtectionDomain;
import java.util.*;
import java.util.jar.*;
import org.objectweb.asm.*;

/** Distinct private observer; incompatible with additional game transformers. */
public final class BodyAgent implements ClassFileTransformer {
    public static final String SERVER_SHA = "d79def2f9aaf06d6b851e568150762b8e7ee24a898a314cf34b210cbd9ea14b6";
    public static final Map<String,String> TARGETS = Map.of(
        "net/minecraft/server/MinecraftServer", "bb6ab22cbdff49b8f7a76523a21ed54166244b914d63064d1a30f2e1747f802f",
        "agh", "cc6a79060c45ab954bcf80a301b8a21ed48b43fee9eb29ab4a13b28c93b10ad2");
    private static final String OBSERVER = "io/github/opencnid/strata/livebody/BodyObserver";
    private final Path server;
    private final Map<String,String> pins;
    private final Set<String> loaded = new HashSet<>();
    private ClassLoader gameLoader;

    public BodyAgent(Path server) throws Exception {
        this.server = server.toRealPath();
        if (!BodyObserver.hashFile(this.server, 64 * 1024 * 1024).equals(SERVER_SHA))
            throw new IOException("BODY_SERVER_PIN");
        Map<String,String> values = new TreeMap<>();
        try (JarFile jar = new JarFile(this.server.toFile())) {
            for (var entries = jar.entries(); entries.hasMoreElements();) {
                JarEntry entry = entries.nextElement();
                if (!entry.getName().endsWith(".class")) continue;
                try (InputStream input = jar.getInputStream(entry)) {
                    byte[] raw = input.readNBytes(4 * 1024 * 1024 + 1);
                    if (raw.length > 4 * 1024 * 1024 || values.size() >= 16384
                            || values.put(entry.getName().replaceFirst("\\.class$", ""), BodyObserver.sha(raw)) != null)
                        throw new IOException("BODY_CLASS_INVENTORY");
                }
            }
        }
        if (!BodyObserver.hashFile(this.server, 64 * 1024 * 1024).equals(SERVER_SHA)
                || !values.entrySet().containsAll(TARGETS.entrySet())) throw new IOException("BODY_SERVER_PIN");
        pins = Map.copyOf(values);
    }

    public static void premain(String options, Instrumentation instrumentation) throws Exception {
        Path own = Path.of(BodyAgent.class.getProtectionDomain().getCodeSource().getLocation().toURI());
        Path config = Path.of(Objects.requireNonNull(options));
        if (!config.isAbsolute()) throw new IOException("BODY_CONFIG");
        var arguments = java.lang.management.ManagementFactory.getRuntimeMXBean().getInputArguments();
        if (!arguments.contains("-XX:+DisableAttachMechanism")
                || arguments.stream().filter(a -> a.startsWith("-javaagent:")).count() != 1
                || arguments.stream().anyMatch(a -> a.startsWith("-agentlib:") || a.startsWith("-agentpath:")
                    || a.startsWith("-Xbootclasspath"))) throw new IOException("BODY_AGENT_ARGUMENTS");
        Path callbacks = config.resolveSibling("body-observer-callbacks.jar");
        try (JarFile jar = new JarFile(own.toFile());
             var input = jar.getInputStream(jar.getJarEntry("body-observer-callbacks.jar"))) {
            byte[] raw = input.readNBytes(262145);
            if (raw.length > 262144) throw new IOException("BODY_BOOTSTRAP_QUOTA");
            Files.write(callbacks, raw, StandardOpenOption.CREATE_NEW);
        }
        instrumentation.appendToBootstrapClassLoaderSearch(new JarFile(callbacks.toFile()));
        Path server = BodyObserver.configure(config, own);
        BodyAgent agent = new BodyAgent(server);
        for (Class<?> type : instrumentation.getAllLoadedClasses())
            if (agent.pins.containsKey(type.getName().replace('.', '/'))) throw new IOException("BODY_ALREADY_LOADED");
        instrumentation.addTransformer(agent, false);
    }

    @Override public synchronized byte[] transform(ClassLoader loader, String name, Class<?> redefined,
                                                    ProtectionDomain domain, byte[] raw) {
        if (!pins.containsKey(name)) return null;
        try {
            if (redefined != null || loader == null || domain == null || domain.getCodeSource() == null
                    || !Path.of(domain.getCodeSource().getLocation().toURI()).toRealPath().equals(server)
                    || !pins.get(name).equals(BodyObserver.sha(raw)) || !loaded.add(name))
                throw new IOException("BODY_LOADED_CLASS_PIN");
            if (gameLoader == null) gameLoader = loader;
            if (gameLoader != loader) throw new IOException("BODY_LOADER_CHANGED");
            byte[] changed = TARGETS.containsKey(name) ? patch(name, raw) : null;
            BodyObserver.bound(loader, name, pins.get(name), changed == null ? pins.get(name) : BodyObserver.sha(changed));
            return changed;
        } catch (Throwable error) {
            Runtime.getRuntime().halt(126);
            throw new AssertionError("unreachable");
        }
    }

    public static byte[] patch(String name, byte[] raw) throws Exception {
        if (!TARGETS.containsKey(name) || !TARGETS.get(name).equals(BodyObserver.sha(raw)))
            throw new IOException("BODY_CLASS_PIN");
        ClassReader reader = new ClassReader(raw);
        ClassWriter writer = new ClassWriter(reader, ClassWriter.COMPUTE_MAXS);
        int[] count = {0};
        reader.accept(new ClassVisitor(Opcodes.ASM9, writer) {
            @Override public MethodVisitor visitMethod(int access, String method, String desc,
                                                        String signature, String[] exceptions) {
                MethodVisitor original = super.visitMethod(access, method, desc, signature, exceptions);
                String start = null, end = null;
                if (name.equals("agh")) {
                    if (method.equals("l") && desc.equals("()V")) end = "avatar";
                } else {
                    if (method.equals("v") && desc.equals("()V")) start = "start";
                    if (method.equals("a") && desc.equals("(Ljava/util/function/BooleanSupplier;)V")) {
                        start = "tickStart"; end = "tickEnd";
                    }
                    if (method.equals("s") && desc.equals("()V")) end = "stop";
                }
                if (start == null && end == null) return original;
                count[0]++;
                final String entry = start, exit = end;
                return new MethodVisitor(Opcodes.ASM9, original) {
                    void callback(String call) {
                        super.visitVarInsn(Opcodes.ALOAD, 0);
                        super.visitMethodInsn(Opcodes.INVOKESTATIC, OBSERVER, call, "(Ljava/lang/Object;)V", false);
                    }
                    @Override public void visitCode() { super.visitCode(); if (entry != null) callback(entry); }
                    @Override public void visitInsn(int opcode) {
                        if (opcode == Opcodes.RETURN && exit != null) callback(exit);
                        super.visitInsn(opcode);
                    }
                    @Override public void visitVarInsn(int opcode, int local) {
                        if (local == 0 && opcode != Opcodes.ALOAD) throw new IllegalArgumentException("BODY_RECEIVER_CHANGED");
                        super.visitVarInsn(opcode, local);
                    }
                    @Override public void visitIincInsn(int local, int increment) {
                        if (local == 0) throw new IllegalArgumentException("BODY_RECEIVER_CHANGED");
                        super.visitIincInsn(local, increment);
                    }
                    @Override public void visitFrame(int type, int locals, Object[] values, int stack, Object[] stackValues) {
                        if (type != Opcodes.F_NEW || (locals > 0 && !name.equals(values[0]) && !Opcodes.TOP.equals(values[0])))
                            throw new IllegalArgumentException("BODY_RECEIVER_FRAME");
                        Object[] retained = locals == 0 ? new Object[] {name} : Arrays.copyOf(values, locals);
                        retained[0] = name;
                        super.visitFrame(type, retained.length, retained, stack, stackValues);
                    }
                };
            }
        }, ClassReader.EXPAND_FRAMES);
        if (count[0] != (name.equals("agh") ? 1 : 3)) throw new IOException("BODY_METHOD_PIN");
        return writer.toByteArray();
    }
}
