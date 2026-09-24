package io.github.opencnid.strata.vanillaclock;

import java.io.IOException;
import java.lang.instrument.ClassFileTransformer;
import java.lang.instrument.Instrumentation;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.security.MessageDigest;
import java.security.ProtectionDomain;
import java.util.HexFormat;
import java.util.Map;
import java.util.jar.JarFile;
import org.objectweb.asm.*;

/** Exact official 1.19.2 methods only; no game-state queries or gameplay API. */
public final class Agent implements ClassFileTransformer {
    public static final Map<String,String> PINS = Map.of(
        "net/minecraft/server/MinecraftServer", "bb6ab22cbdff49b8f7a76523a21ed54166244b914d63064d1a30f2e1747f802f",
        "agh", "cc6a79060c45ab954bcf80a301b8a21ed48b43fee9eb29ab4a13b28c93b10ad2");
    private static final String CLOCK = "io/github/opencnid/strata/vanillaclock/Clock";

    public static String sha(byte[] value) throws Exception {
        return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(value));
    }
    public static void premain(String options, Instrumentation instrumentation) throws Exception {
        Path own = Path.of(Agent.class.getProtectionDomain().getCodeSource().getLocation().toURI());
        // Mojang's game loader has the platform loader as parent. Expose only
        // callbacks in bootstrap: exposing Agent's anonymous classes there too
        // would split its runtime package across app/bootstrap loaders.
        if (options == null) throw new IOException("VANILLA_CLOCK_CONFIG");
        Path config = Path.of(options);
        if (!config.isAbsolute()) throw new IOException("VANILLA_CLOCK_CONFIG");
        Path callbacks = config.resolveSibling("vanilla-clock-callbacks.jar");
        try (JarFile jar = new JarFile(own.toFile());
             var stream = jar.getInputStream(jar.getJarEntry("strata-clock-callbacks.jar"))) {
            byte[] data = stream.readNBytes(262145);
            if (data.length > 262144) throw new IOException("VANILLA_CLOCK_BOOTSTRAP_QUOTA");
            Files.write(callbacks, data, StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE);
        }
        instrumentation.appendToBootstrapClassLoaderSearch(new JarFile(callbacks.toFile()));
        Clock.configure(options, sha(Files.readAllBytes(own)));
        for (Class<?> loaded : instrumentation.getAllLoadedClasses())
            if (PINS.containsKey(loaded.getName().replace('.', '/')))
                throw new IOException("VANILLA_CLOCK_ALREADY_LOADED");
        instrumentation.addTransformer(new Agent(), false);
    }
    @Override public byte[] transform(ClassLoader loader, String name, Class<?> redefined,
                                      ProtectionDomain domain, byte[] input) {
        if (!PINS.containsKey(name)) return null;
        try {
            if (redefined != null) throw new IOException("VANILLA_CLOCK_REDEFINITION");
            byte[] result = patch(name, input);
            Clock.bound(name, sha(input), sha(result));
            return result;
        } catch (Throwable error) {
            // Transformer exceptions alone would silently run unmeasured code.
            Runtime.getRuntime().halt(126);
            throw new AssertionError("unreachable");
        }
    }
    public static byte[] patch(String name, byte[] input) throws Exception {
        if (!PINS.containsKey(name) || !PINS.get(name).equals(sha(input)))
            throw new IOException("VANILLA_CLOCK_CLASS_PIN");
        ClassReader reader = new ClassReader(input);
        ClassWriter writer = new ClassWriter(reader, ClassWriter.COMPUTE_MAXS);
        int[] methods = {0};
        reader.accept(new ClassVisitor(Opcodes.ASM9, writer) {
            @Override public MethodVisitor visitMethod(int access, String method, String desc,
                                                        String signature, String[] exceptions) {
                MethodVisitor original = super.visitMethod(access, method, desc, signature, exceptions);
                String entry = null, end = null;
                if (name.equals("net/minecraft/server/MinecraftServer")) {
                    if (method.equals("v") && desc.equals("()V")) entry = "start";
                    if (method.equals("a") && desc.equals("(Ljava/util/function/BooleanSupplier;)V")) {
                        entry = "tickStart"; end = "tickEnd";
                    }
                    if (method.equals("s") && desc.equals("()V")) end = "stop";
                } else if (method.equals("l") && desc.equals("()V")) end = "avatar";
                if (entry == null && end == null) return original;
                methods[0]++;
                final String onEntry = entry, onEnd = end;
                return new MethodVisitor(Opcodes.ASM9, original) {
                    @Override public void visitVarInsn(int opcode, int variable) {
                        // The exact doTick body never reassigns its receiver.
                        // Check this before retaining slot zero in dead-local
                        // frames for the added normal-return UUID read.
                        if ("avatar".equals(onEnd) && variable == 0 && opcode != Opcodes.ALOAD)
                            throw new IllegalArgumentException("VANILLA_CLOCK_RECEIVER_CHANGED");
                        super.visitVarInsn(opcode, variable);
                    }
                    @Override public void visitIincInsn(int variable, int increment) {
                        if ("avatar".equals(onEnd) && variable == 0)
                            throw new IllegalArgumentException("VANILLA_CLOCK_RECEIVER_CHANGED");
                        super.visitIincInsn(variable, increment);
                    }
                    @Override public void visitFrame(int type, int nLocal, Object[] local,
                                                      int nStack, Object[] stack) {
                        if ("avatar".equals(onEnd)) {
                            if (type != Opcodes.F_NEW || (nLocal > 0 &&
                                !name.equals(local[0]) && !Opcodes.TOP.equals(local[0])))
                                throw new IllegalArgumentException("VANILLA_CLOCK_RECEIVER_FRAME");
                            // Mojang's final return frame drops all locals.
                            // Loading this at that return makes slot zero live.
                            Object[] retained = nLocal == 0 ? new Object[] {name}
                                : java.util.Arrays.copyOf(local, nLocal);
                            retained[0] = name;
                            super.visitFrame(type, retained.length, retained, nStack, stack);
                        } else super.visitFrame(type, nLocal, local, nStack, stack);
                    }
                    @Override public void visitCode() {
                        super.visitCode();
                        if (onEntry != null) super.visitMethodInsn(Opcodes.INVOKESTATIC, CLOCK, onEntry, "()V", false);
                    }
                    @Override public void visitInsn(int opcode) {
                        if (opcode == Opcodes.RETURN && onEnd != null) {
                            if (onEnd.equals("avatar")) {
                                super.visitVarInsn(Opcodes.ALOAD, 0);
                                super.visitMethodInsn(Opcodes.INVOKEVIRTUAL, "agh", "co", "()Ljava/util/UUID;", false);
                                super.visitMethodInsn(Opcodes.INVOKESTATIC, CLOCK, onEnd, "(Ljava/util/UUID;)V", false);
                            } else super.visitMethodInsn(Opcodes.INVOKESTATIC, CLOCK, onEnd, "()V", false);
                        }
                        super.visitInsn(opcode);
                    }
                };
            }
        }, ClassReader.EXPAND_FRAMES);
        if (methods[0] != (name.equals("agh") ? 1 : 3)) throw new IOException("VANILLA_CLOCK_METHOD_PIN");
        return writer.toByteArray();
    }
}
