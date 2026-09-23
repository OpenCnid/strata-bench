// Private operator helper. No gameplay commands, credentials or evaluator logic.
// The controller pins this compiled class and every source before dispatch.
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.nio.channels.FileChannel;
import java.security.MessageDigest;
import java.util.Base64;
import java.util.HexFormat;
import java.util.List;
import java.util.HashSet;

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
        boolean bundled = !lines.isEmpty() && lines.get(0).equals("strata/WriterStagingBundles/1");
        int first = bundled ? 1 : 0;
        int files = lines.size() - first;
        if (files < 1 || files > 12000) throw new Exception("WRITER_FILE_QUOTA");
        long total = 0;
        FileChannel input = null;
        Path currentSource = null;
        HashSet<Path> bundles = new HashSet<>();
        try {
        for (String line : lines.subList(first, lines.size())) {
            if (System.nanoTime() >= deadline) throw new Exception("WRITER_COPY_TIMEOUT");
            String[] fields = line.split("\t", -1);
            if (fields.length != (bundled ? 5 : 4) || !fields[2].matches("[0-9a-f]{64}")
                    || !fields[3].matches("0|[1-9][0-9]{0,9}")
                    || (bundled && !fields[4].matches("0|[1-9][0-9]{0,9}")))
                throw new Exception("WRITER_MANIFEST_INVALID");
            String relative = decode(fields[0]);
            Path source = Path.of(decode(fields[1]));
            long size = Long.parseLong(fields[3]);
            long offset = bundled ? Long.parseLong(fields[4]) : 0;
            Path destination = root.resolve(relative).normalize();
            for (String component : relative.split("/", -1))
                if (component.isEmpty() || component.equals(".") || component.equals(".."))
                    throw new Exception("WRITER_FILE_INVALID");
            if (size < 0 || size > 512L * 1024 * 1024 || (total += size) > MAX_BYTES
                    || !source.isAbsolute() || Files.isSymbolicLink(source)
                    || !Files.isRegularFile(source, LinkOption.NOFOLLOW_LINKS)
                    || !destination.startsWith(root)
                    || destination.equals(root) || Path.of(relative).isAbsolute()
                    || relative.contains("\\") || relative.contains(":"))
                throw new Exception("WRITER_FILE_INVALID");
            if (!bundled || !source.equals(currentSource)) {
                if (input != null) {
                    if (input.position() != input.size()) throw new Exception("WRITER_BUNDLE_RANGE");
                    input.close();
                    input = null;
                }
                if (bundled && (!bundles.add(source) || bundles.size() > 3))
                    throw new Exception("WRITER_BUNDLE_RANGE");
                input = FileChannel.open(source, StandardOpenOption.READ, LinkOption.NOFOLLOW_LINKS);
                currentSource = source;
            }
            long sourceSize = input.size();
            if (sourceSize > 512L * 1024 * 1024 || input.position() != offset
                    || offset > sourceSize || size > sourceSize - offset
                    || (!bundled && sourceSize != size))
                throw new Exception("WRITER_BUNDLE_RANGE");
            Files.createDirectories(destination.getParent());
            MessageDigest hash = MessageDigest.getInstance("SHA-256");
            try (var output = FileChannel.open(destination, StandardOpenOption.CREATE_NEW,
                                                 StandardOpenOption.WRITE)) {
                var buffer = java.nio.ByteBuffer.allocate(65536);
                long copied = 0;
                while (copied < size) {
                    if (System.nanoTime() >= deadline)
                        throw new Exception("WRITER_COPY_QUOTA");
                    buffer.clear();
                    buffer.limit((int)Math.min(buffer.capacity(), size - copied));
                    int count = input.read(buffer);
                    if (count <= 0) throw new Exception("WRITER_SOURCE_CHANGED");
                    copied += count;
                    hash.update(buffer.array(), 0, count);
                    buffer.flip();
                    while (buffer.hasRemaining()) {
                        if (System.nanoTime() >= deadline || output.write(buffer) <= 0)
                            throw new Exception("WRITER_COPY_QUOTA");
                    }
                }
                if (copied != size || !HexFormat.of().formatHex(hash.digest()).equals(fields[2]))
                    throw new Exception("WRITER_SOURCE_CHANGED");
                output.force(true);
            }
        }
        if (input == null || input.position() != input.size()) throw new Exception("WRITER_BUNDLE_RANGE");
        if (System.nanoTime() >= deadline) throw new Exception("WRITER_COPY_TIMEOUT");
        } finally {
            if (input != null) input.close();
        }
        publish(control.resolve("copied.json"), "{\"schema\":\"strata/WriterJavaCopied/2\","
            + "\"challenge\":" + quote(challenge) + ",\"files\":" + files
            + ",\"bytes\":" + total + ",\"root\":" + quote(root.toString()) + "}");
        waitFor(control.resolve("finish.grant"), challenge, deadline);
        System.out.println("strata-writer-preparation-stopped");
    }
}
