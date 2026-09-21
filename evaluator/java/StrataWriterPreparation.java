// Private operator helper. No gameplay commands, credentials or evaluator logic.
// The controller pins this compiled class and every source before dispatch.
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.nio.channels.FileChannel;
import java.security.MessageDigest;
import java.util.Base64;
import java.util.HexFormat;
import java.util.List;

public final class StrataWriterPreparation {
    private static final long MAX_BYTES = 1L << 30;
    private static String quote(String value) {
        StringBuilder out = new StringBuilder("\"");
        for (char c : value.toCharArray()) {
            if (c == '\\' || c == '"') out.append('\\').append(c);
            else if (c < 32) out.append(String.format("\\u%04x", (int)c));
            else out.append(c);
        }
        return out.append('"').toString();
    }
    private static void publish(Path path, String text) throws Exception {
        Path pending = path.resolveSibling(path.getFileName() + ".pending");
        byte[] bytes = text.getBytes(StandardCharsets.UTF_8);
        try (FileChannel file = FileChannel.open(pending,
                StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE)) {
            java.nio.ByteBuffer buffer = java.nio.ByteBuffer.wrap(bytes);
            while (buffer.hasRemaining()) file.write(buffer);
            file.force(true);
        }
        // Default move rejects an existing target. ATOMIC_MOVE would make
        // replacement semantics implementation-dependent when a target exists.
        Files.move(pending, path);
    }
    private static void waitFor(Path path, String challenge, long deadline) throws Exception {
        while (!Files.exists(path, LinkOption.NOFOLLOW_LINKS)) {
            if (System.nanoTime() >= deadline) throw new Exception("WRITER_GRANT_TIMEOUT");
            Thread.sleep(10);
        }
        if (Files.isSymbolicLink(path) || Files.size(path) > 128
                || !Files.readString(path).equals(challenge))
            throw new Exception("WRITER_GRANT_INVALID");
    }
    private static String decode(String value) {
        return new String(Base64.getDecoder().decode(value), StandardCharsets.UTF_8);
    }
    public static void main(String[] args) throws Exception {
        if (args.length != 3 || !args[2].matches("[0-9a-f]{64}"))
            throw new Exception("WRITER_ARGUMENTS");
        Path requestedRoot = Path.of(args[0]).toAbsolutePath().normalize();
        Path control = Path.of(args[1]).toRealPath();
        String challenge = args[2];
        long deadline = System.nanoTime() + 20_000_000_000L;
        ProcessHandle self = ProcessHandle.current();
        publish(control.resolve("identity.json"), "{\"schema\":\"strata/WriterJavaIdentity/2\","
            + "\"challenge\":" + quote(challenge) + ",\"pid\":" + self.pid()
            + ",\"process_started_unix_ms\":" + self.info().startInstant().orElseThrow().toEpochMilli()
            + ",\"executable\":" + quote(self.info().command().orElseThrow())
            + ",\"requested_root\":" + quote(requestedRoot.toString()) + "}");
        // An unbound Java process must never begin preparation. The controller
        // checks the retained OS handle/job before publishing this one-use gate.
        waitFor(control.resolve("prepare.grant"), challenge, deadline);
        Path root = requestedRoot.toRealPath(); // Controller created the protected root after binding.
        Path manifest = control.resolve("files.tsv");
        if (Files.isSymbolicLink(manifest) || Files.size(manifest) > 8 * 1024 * 1024)
            throw new Exception("WRITER_MANIFEST_QUOTA");
        List<String> lines = Files.readAllLines(manifest, StandardCharsets.UTF_8);
        if (lines.size() < 1 || lines.size() > 12000) throw new Exception("WRITER_FILE_QUOTA");
        long total = 0;
        for (String line : lines) {
            if (System.nanoTime() >= deadline) throw new Exception("WRITER_COPY_TIMEOUT");
            String[] fields = line.split("\t", -1);
            if (fields.length != 4 || !fields[2].matches("[0-9a-f]{64}"))
                throw new Exception("WRITER_MANIFEST_INVALID");
            String relative = decode(fields[0]);
            Path source = Path.of(decode(fields[1]));
            long size = Long.parseLong(fields[3]);
            Path destination = root.resolve(relative).normalize();
            if (size < 0 || size > 512L * 1024 * 1024 || (total += size) > MAX_BYTES
                    || !source.isAbsolute() || Files.isSymbolicLink(source)
                    || !Files.isRegularFile(source, LinkOption.NOFOLLOW_LINKS)
                    || Files.size(source) != size || !destination.startsWith(root)
                    || destination.equals(root) || Path.of(relative).isAbsolute()
                    || relative.contains("\\") || relative.contains(":"))
                throw new Exception("WRITER_FILE_INVALID");
            Files.createDirectories(destination.getParent());
            MessageDigest hash = MessageDigest.getInstance("SHA-256");
            try (var input = Files.newInputStream(source);
                 var output = FileChannel.open(destination, StandardOpenOption.CREATE_NEW,
                                                 StandardOpenOption.WRITE)) {
                byte[] buffer = new byte[65536];
                long copied = 0;
                int count;
                while ((count = input.read(buffer)) != -1) {
                    if ((copied += count) > size || System.nanoTime() >= deadline)
                        throw new Exception("WRITER_COPY_QUOTA");
                    hash.update(buffer, 0, count);
                    var block = java.nio.ByteBuffer.wrap(buffer, 0, count);
                    while (block.hasRemaining()) output.write(block);
                }
                if (copied != size || !HexFormat.of().formatHex(hash.digest()).equals(fields[2]))
                    throw new Exception("WRITER_SOURCE_CHANGED");
                output.force(true);
            }
        }
        publish(control.resolve("copied.json"), "{\"schema\":\"strata/WriterJavaCopied/2\","
            + "\"challenge\":" + quote(challenge) + ",\"files\":" + lines.size()
            + ",\"bytes\":" + total + ",\"root\":" + quote(root.toString()) + "}");
        waitFor(control.resolve("finish.grant"), challenge, deadline);
        System.out.println("strata-writer-preparation-stopped");
    }
}
