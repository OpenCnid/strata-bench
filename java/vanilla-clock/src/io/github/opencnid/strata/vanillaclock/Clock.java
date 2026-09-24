package io.github.opencnid.strata.vanillaclock;

import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.channels.FileChannel;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;

/** Bootstrap-visible observer, writing only a fresh operator-owned private file. */
public final class Clock {
    public static final String POLICY = "vanilla1192-method-callback-clock/1";
    private static FileChannel output;
    private static Ticks ticks;
    private static int sequence, bytes;
    private static final Set<String> bound = new HashSet<>();
    private static boolean closed;
    public static synchronized void configure(String options, String module) throws Exception {
        if (output != null || options == null) throw new IOException("VANILLA_CLOCK_CONFIG");
        Path config = Path.of(options);
        if (!config.isAbsolute() || Files.size(config) > 8192 || Files.isSymbolicLink(config))
            throw new IOException("VANILLA_CLOCK_CONFIG");
        Map<String,String> fields = new HashMap<>();
        for (String line : Files.readAllLines(config, StandardCharsets.UTF_8)) {
            int at = line.indexOf('=');
            if (at < 1 || fields.put(line.substring(0, at), line.substring(at + 1)) != null)
                throw new IOException("VANILLA_CLOCK_CONFIG");
        }
        if (!fields.keySet().equals(Set.of("campaign_id", "agent_id", "epoch", "run_id", "output")))
            throw new IOException("VANILLA_CLOCK_CONFIG");
        for (String key : List.of("campaign_id", "agent_id", "run_id"))
            if (!fields.get(key).matches("[A-Za-z0-9_.:-]{1,128}")) throw new IOException("VANILLA_CLOCK_SCOPE");
        if (!fields.get("epoch").matches("[1-9][0-9]{0,8}")) throw new IOException("VANILLA_CLOCK_SCOPE");
        Path path = Path.of(fields.get("output"));
        if (!path.isAbsolute() || !path.normalize().equals(path)) throw new IOException("VANILLA_CLOCK_PATH");
        for (Path parent = path; parent != null; parent = parent.getParent())
            if (Files.isSymbolicLink(parent)) throw new IOException("VANILLA_CLOCK_PATH");
        output = FileChannel.open(path, StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE);
        write("{\"schema\":\"strata/VanillaClockStart/1\",\"policy\":\"" + POLICY
            + "\",\"campaign_id\":\"" + fields.get("campaign_id") + "\",\"agent_id\":\"" + fields.get("agent_id")
            + "\",\"epoch\":" + fields.get("epoch") + ",\"run_id\":\"" + fields.get("run_id")
            + "\",\"module_sha256\":\"" + module + "\",\"pid\":" + ProcessHandle.current().pid()
            + ",\"origin\":\"runServer-entry\",\"terminal\":\"stopServer-return\",\"period_ns\":1000000000}");
    }
    private static void write(String body) throws IOException {
        if (closed || output == null || ++sequence > 2048) throw new IOException("VANILLA_CLOCK_JOURNAL");
        byte[] raw = ("{\"seq\":" + sequence + ",\"body\":" + body + "}\n").getBytes(StandardCharsets.UTF_8);
        bytes = Math.addExact(bytes, raw.length);
        if (raw.length > 131072 || bytes > 4*1024*1024) throw new IOException("VANILLA_CLOCK_QUOTA");
        ByteBuffer buffer = ByteBuffer.wrap(raw);
        while (buffer.hasRemaining()) output.write(buffer);
        output.force(false);
    }
    private interface Callback { void run() throws Exception; }
    private static synchronized void checked(Callback callback) {
        try { callback.run(); }
        catch (Throwable error) { Runtime.getRuntime().halt(126); }
    }
    public static void bound(String name, String before, String after) {
        checked(() -> {
            if (!bound.add(name)) throw new IOException("VANILLA_CLOCK_DUPLICATE_CLASS");
            write("{\"schema\":\"strata/VanillaClockBinding/1\",\"class\":\"" + name
                + "\",\"original_sha256\":\"" + before + "\",\"transformed_sha256\":\"" + after + "\"}");
        });
    }
    public static void start() { checked(() -> {
        if (ticks != null) throw new IOException("VANILLA_CLOCK_DUPLICATE_START");
        ticks = new Ticks(System::nanoTime);
        write("{\"schema\":\"strata/VanillaClockRunning/1\"}");
    }); }
    public static void tickStart() { checked(() -> ticks.startTick()); }
    public static void avatar(UUID uuid) { checked(() -> ticks.avatar(uuid)); }
    public static void tickEnd() { checked(() -> { if (ticks.endTick()) write(ticks.sample(false)); }); }
    public static void stop() { checked(() -> {
        write(ticks.sample(true)); output.close(); closed = true;
    }); }
}
