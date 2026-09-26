package io.github.opencnid.strata.livebody;

import java.io.*;
import java.nio.ByteBuffer;
import java.nio.channels.FileChannel;
import java.nio.charset.StandardCharsets;
import java.nio.charset.CodingErrorAction;
import java.nio.file.*;
import java.security.MessageDigest;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicReference;

/** Bootstrap-visible private callbacks. All failures halt the owned JVM. */
public final class BodyObserver {
    public static final String POLICY = "vanilla1192-private-roster-nbt/1";
    private static final AtomicReference<ClassLoader> loader = new AtomicReference<>();
    private static final Map<String,String> bindings = new ConcurrentHashMap<>();
    private static final StackWalker WALKER = StackWalker.getInstance(Set.of(
        StackWalker.Option.RETAIN_CLASS_REFERENCE, StackWalker.Option.SHOW_REFLECT_FRAMES,
        StackWalker.Option.SHOW_HIDDEN_FRAMES));
    private static Path output;
    private static FileChannel journal;
    private static List<UUID> expected;
    private static Object server;
    private static RosterCapture roster;
    private static PlayerNbt codec;
    private static long origin, sequence, written;
    private static volatile boolean closed;
    private static boolean bindingsClosed;

    public static String sha(byte[] bytes) throws Exception {
        return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes));
    }
    public static String hashFile(Path path, int maximum) throws Exception {
        if (Files.size(path) > maximum) throw new IOException("BODY_FILE_QUOTA");
        try (var input = Files.newInputStream(path)) {
            MessageDigest hash = MessageDigest.getInstance("SHA-256");
            byte[] buffer = new byte[65536];
            int total = 0, count;
            while ((count = input.read(buffer)) != -1) {
                total = Math.addExact(total, count);
                if (total > maximum) throw new IOException("BODY_FILE_QUOTA");
                hash.update(buffer, 0, count);
            }
            return HexFormat.of().formatHex(hash.digest());
        }
    }
    public static synchronized Path configure(Path config, Path module) throws Exception {
        if (journal != null || !config.isAbsolute() || Files.size(config) > 16384)
            throw new IOException("BODY_CONFIG");
        byte[] configBytes;
        try (InputStream input = Files.newInputStream(config)) { configBytes = input.readNBytes(16385); }
        if (configBytes.length > 16384) throw new IOException("BODY_CONFIG");
        String textConfig = StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT)
            .onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(configBytes)).toString();
        Map<String,String> fields = new HashMap<>();
        for (String line : textConfig.lines().toList()) {
            int at = line.indexOf('=');
            if (at < 1 || fields.put(line.substring(0, at), line.substring(at + 1)) != null)
                throw new IOException("BODY_CONFIG");
        }
        if (!fields.keySet().equals(Set.of("campaign_id", "epoch", "run_id", "roster", "server_jar", "output")))
            throw new IOException("BODY_CONFIG");
        for (String key : List.of("campaign_id", "run_id"))
            if (!fields.get(key).matches("[A-Za-z0-9_.:-]{1,128}")) throw new IOException("BODY_SCOPE");
        if (!fields.get("epoch").matches("[1-9][0-9]{0,8}")) throw new IOException("BODY_SCOPE");
        List<UUID> ids = new ArrayList<>();
        for (String text : fields.get("roster").split(",", -1)) {
            UUID uuid;
            try { uuid = UUID.fromString(text); }
            catch (IllegalArgumentException error) { throw new IOException("BODY_ROSTER", error); }
            if (!uuid.toString().equals(text) || ids.contains(uuid) || ids.size() == 64)
                throw new IOException("BODY_ROSTER");
            ids.add(uuid);
        }
        expected = List.copyOf(ids);
        Path serverJar = Path.of(fields.get("server_jar"));
        output = Path.of(fields.get("output"));
        for (Path path : List.of(config, serverJar, output, module)) {
            if (!path.isAbsolute() || !path.normalize().equals(path)) throw new IOException("BODY_PATH");
            for (Path parent = path; parent != null; parent = parent.getParent())
                if (Files.isSymbolicLink(parent)) throw new IOException("BODY_PATH");
        }
        String serverHash = hashFile(serverJar, 64 * 1024 * 1024);
        if (!serverHash.equals("d79def2f9aaf06d6b851e568150762b8e7ee24a898a314cf34b210cbd9ea14b6"))
            throw new IOException("BODY_SERVER_PIN");
        String moduleHash = hashFile(module, 8 * 1024 * 1024);
        Files.createDirectory(output);
        journal = FileChannel.open(output.resolve("events.jsonl"), StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE);
        origin = System.nanoTime();
        write("{\"schema\":\"strata/PrivateBodyStart/1\",\"policy\":\"" + POLICY
            + "\",\"campaign_id\":\"" + fields.get("campaign_id") + "\",\"run_id\":\"" + fields.get("run_id")
            + "\",\"epoch\":" + fields.get("epoch") + ",\"pid\":" + ProcessHandle.current().pid()
            + ",\"config_sha256\":\"" + sha(configBytes) + "\""
            + ",\"module_sha256\":\"" + moduleHash + "\",\"server_sha256\":\"" + serverHash
            + "\",\"roster\":[\"" + String.join("\",\"", expected.stream().map(UUID::toString).toList()) + "\"]}");
        return serverJar;
    }
    // No callback lock here: class loading can occur while a callback is active.
    public static void bound(ClassLoader actual, String name, String before, String after) throws IOException {
        synchronized (bindings) {
            loader.compareAndSet(null, actual);
            if (bindingsClosed || actual == null || loader.get() != actual || bindings.size() >= 16384
                    || bindings.putIfAbsent(name, before + ":" + after) != null) throw new IOException("BODY_BINDING");
        }
    }
    private static void write(String body) throws IOException {
        if (closed || journal == null || ++sequence > 128) throw new IOException("BODY_JOURNAL");
        long elapsed = System.nanoTime() - origin;
        if (elapsed < 0 || elapsed > 9_007_199_254_740_991L) throw new IOException("BODY_TIME");
        byte[] bytes = ("{\"seq\":" + sequence + ",\"elapsed_ns\":" + elapsed + ",\"body\":" + body + "}\n")
            .getBytes(StandardCharsets.UTF_8);
        written = Math.addExact(written, bytes.length);
        if (written > 1024 * 1024) throw new IOException("BODY_JOURNAL_QUOTA");
        ByteBuffer buffer = ByteBuffer.wrap(bytes);
        while (buffer.hasRemaining()) journal.write(buffer);
        journal.force(false);
    }
    private interface Callback { void run() throws Exception; }
    private static synchronized void checked(String name, String method, String desc, Object receiver, Callback callback) {
        try {
            StackWalker.StackFrame caller = WALKER.walk(frames -> frames
                .filter(f -> f.getDeclaringClass() != BodyObserver.class).findFirst().orElseThrow());
            if (caller.getDeclaringClass().getClassLoader() != loader.get() || !caller.getClassName().equals(name)
                    || !caller.getMethodName().equals(method) || !caller.getDescriptor().equals(desc)
                    || !caller.getDeclaringClass().isInstance(receiver) || closed || journal == null)
                throw new IOException("BODY_CALLBACK_ORIGIN");
            callback.run();
        } catch (Throwable error) { Runtime.getRuntime().halt(126); }
    }
    public static void start(Object actual) {
        checked("net.minecraft.server.MinecraftServer", "v", "()V", actual, () -> {
            if (roster != null) throw new IOException("BODY_DUPLICATE_START");
            server = actual; roster = new RosterCapture(actual, expected);
            write("{\"schema\":\"strata/PrivateBodyRunning/1\"}");
        });
    }
    public static void tickStart(Object actual) {
        checked("net.minecraft.server.MinecraftServer", "a", "(Ljava/util/function/BooleanSupplier;)V", actual,
            () -> roster.start(actual));
    }
    public static void avatar(Object player) {
        checked("agh", "l", "()V", player, () -> {
            if (player.getClass() != Class.forName("agh", false, loader.get())
                    || player.getClass().getMethod("cD").invoke(player) != server)
                throw new IOException("BODY_PLAYER_SERVER");
            UUID id = (UUID)player.getClass().getMethod("co").invoke(player);
            roster.avatar(server, id, player);
        });
    }
    public static void tickEnd(Object actual) {
        checked("net.minecraft.server.MinecraftServer", "a", "(Ljava/util/function/BooleanSupplier;)V", actual, () -> {
            Map<UUID,Object> complete = roster.end(actual);
            if (complete.isEmpty()) return;
            long began = System.nanoTime() - origin;
            codec = new PlayerNbt(loader.get());
            if (!bindings.keySet().containsAll(Set.of("net/minecraft/server/MinecraftServer", "agh", "bbn", "pj", "pt", "ayz")))
                throw new IOException("BODY_INCOMPLETE_BINDINGS");
            long total = 0;
            StringJoiner bodies = new StringJoiner(",");
            for (UUID id : expected) {
                byte[] bytes = codec.capture(complete.get(id), id);
                total += bytes.length;
                if (total > 64 * 1024 * 1024) throw new IOException("BODY_AGGREGATE_QUOTA");
                try (FileChannel file = FileChannel.open(output.resolve(id + ".nbt"),
                        StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE)) {
                    ByteBuffer buffer = ByteBuffer.wrap(bytes);
                    while (buffer.hasRemaining()) file.write(buffer);
                    file.force(true);
                }
                bodies.add("{\"uuid\":\"" + id + "\",\"bytes\":" + bytes.length + ",\"sha256\":\"" + sha(bytes) + "\"}");
            }
            write("{\"schema\":\"strata/PrivateBodyCapture/1\",\"tick\":" + roster.tick()
                + ",\"begin_ns\":" + began + ",\"bodies\":[" + bodies + "]}");
            roster.committed(actual);
        });
    }
    public static void stop(Object actual) {
        checked("net.minecraft.server.MinecraftServer", "s", "()V", actual, () -> {
            roster.stop(actual);
            Map<String,String> finalBindings;
            synchronized (bindings) {
                bindingsClosed = true;
                finalBindings = new TreeMap<>(bindings);
            }
            StringJoiner entries = new StringJoiner("\n");
            finalBindings.forEach((key, value) -> entries.add(key + "=" + value));
            byte[] raw = entries.toString().getBytes(StandardCharsets.UTF_8);
            try (FileChannel file = FileChannel.open(output.resolve("loaded-classes.txt"),
                    StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE)) {
                ByteBuffer buffer = ByteBuffer.wrap(raw);
                while (buffer.hasRemaining()) file.write(buffer);
                file.force(true);
            }
            write("{\"schema\":\"strata/PrivateBodyStop/1\",\"tick\":" + roster.tick()
                + ",\"loaded_classes\":" + finalBindings.size() + ",\"bindings_sha256\":\"" + sha(raw) + "\"}");
            journal.close(); closed = true;
        });
    }
}
