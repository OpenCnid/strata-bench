import io.github.opencnid.strata.vanillaclock.*;
import java.nio.file.*;
import java.util.*;
import java.util.jar.*;
import org.objectweb.asm.*;

public class ClockTest {
    static long now;
    static void require(boolean value) { if (!value) throw new AssertionError(); }
    static void refuses(Runnable call) {
        try { call.run(); } catch (IllegalStateException expected) { return; }
        throw new AssertionError("accepted invalid clock");
    }
    public static void main(String[] args) throws Exception {
        UUID uuid = UUID.fromString("12345678-1234-1234-1234-123456789abc");
        now = Long.MAX_VALUE - 100;
        Ticks ticks = new Ticks(() -> now);
        now += 10; ticks.startTick(); ticks.avatar(uuid);
        now += 200; require(!ticks.endTick()); // nanoTime wrap subtracts correctly.
        String first = ticks.sample(false);
        require(first.contains("\"completed_server_ticks\":1") && first.contains("\"tick_work_ns\":[200]"));
        now += 20; ticks.startTick(); now += 30; ticks.endTick();
        String end = ticks.sample(true);
        require(end.contains("\"window_work_ns\":30") && end.contains("\"observed_tick_work_ns\":230"));
        refuses(ticks::startTick);
        for (int mode = 0; mode < 5; mode++) {
            now = 0; Ticks bad = new Ticks(() -> now);
            switch (mode) {
                case 0 -> refuses(bad::endTick);
                case 1 -> {bad.startTick(); refuses(bad::startTick);}
                case 2 -> {bad.startTick(); bad.avatar(uuid); refuses(() -> bad.avatar(uuid));}
                case 3 -> {bad.startTick(); refuses(() -> bad.sample(true));}
                case 4 -> {now = -1; refuses(bad::startTick);}
            }
            refuses(() -> bad.sample(true)); // Fault is sticky.
        }
        now = 0; Ticks owner = new Ticks(() -> now);
        var threadError = new java.util.concurrent.atomic.AtomicReference<Throwable>();
        Thread wrong = new Thread(() -> {
            try { owner.startTick(); } catch (Throwable error) { threadError.set(error); }
        });
        wrong.start(); wrong.join();
        require(threadError.get() instanceof IllegalStateException);
        refuses(() -> owner.sample(true));
        now = 0; Ticks quota = new Ticks(() -> now); quota.startTick();
        for (int i = 0; i < 64; i++) quota.avatar(new UUID(0, i));
        refuses(() -> quota.avatar(new UUID(0, 64)));
        refuses(() -> quota.sample(true));
        try (JarFile jar = new JarFile(args[0])) {
            for (String name : Agent.PINS.keySet()) {
                byte[] raw = jar.getInputStream(jar.getJarEntry(name + ".class")).readAllBytes();
                byte[] changed = Agent.patch(name, raw);
                List<String> hooks = new ArrayList<>();
                new ClassReader(changed).accept(new ClassVisitor(Opcodes.ASM9) {
                    @Override public MethodVisitor visitMethod(int access, String n, String d, String s, String[] e) {
                        return new MethodVisitor(Opcodes.ASM9) {
                            @Override public void visitMethodInsn(int op, String owner, String method, String desc, boolean itf) {
                                if (owner.equals("io/github/opencnid/strata/vanillaclock/Clock")) hooks.add(method);
                            }
                        };
                    }
                }, 0);
                Collections.sort(hooks);
                require(hooks.equals(name.equals("agh") ? List.of("avatar") : List.of("start", "stop", "tickEnd", "tickStart")));
                raw[raw.length-1] ^= 1;
                try { Agent.patch(name, raw); throw new AssertionError("drift accepted"); }
                catch (java.io.IOException expected) { require(expected.getMessage().equals("VANILLA_CLOCK_CLASS_PIN")); }
            }
        }
        System.out.println("clock-and-patches-pass");
    }
}
