// Private pre-start gate. No model, evaluator selector or credential is staged.
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.nio.channels.FileChannel;
import java.util.Base64;
import java.util.List;

public final class StrataWriterLaunch {
    private static String quote(String text) {
        StringBuilder out = new StringBuilder("\"");
        for (char ch : text.toCharArray()) {
            if (ch == '\\' || ch == '"') out.append('\\').append(ch);
            else if (ch < 32) out.append(String.format("\\u%04x", (int) ch));
            else out.append(ch);
        }
        return out.append('"').toString();
    }
    public static void main(String[] args) throws Exception {
        if (args.length != 3 || !args[2].matches("[0-9a-f]{64}"))
            throw new Exception("WRITER_LAUNCH_ARGUMENTS");
        Path root = Path.of(args[0]).toAbsolutePath().normalize();
        Path control = Path.of(args[1]).toRealPath();
        String challenge = args[2];
        ProcessHandle self = ProcessHandle.current();
        String identity = "{\"schema\":\"strata/WriterJavaIdentity/2\",\"challenge\":" + quote(challenge)
            + ",\"pid\":" + self.pid() + ",\"process_started_unix_ms\":"
            + self.info().startInstant().orElseThrow().toEpochMilli() + ",\"executable\":"
            + quote(self.info().command().orElseThrow()) + ",\"requested_root\":" + quote(root.toString()) + "}";
        Path pending = control.resolve("launch-identity.pending");
        try (FileChannel file = FileChannel.open(pending, StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE)) {
            var bytes = java.nio.ByteBuffer.wrap(identity.getBytes(StandardCharsets.UTF_8));
            while (bytes.hasRemaining()) file.write(bytes);
            file.force(true);
        }
        Files.move(pending, control.resolve("launch-identity.json"));
        Path grant = control.resolve("launch.grant");
        long until = System.nanoTime() + 10_000_000_000L;
        while (!Files.exists(grant, LinkOption.NOFOLLOW_LINKS)) {
            if (System.nanoTime() >= until) throw new Exception("WRITER_LAUNCH_GATE_TIMEOUT");
            Thread.sleep(10);
        }
        if (Files.isSymbolicLink(grant) || Files.size(grant) > 128 || !Files.readString(grant).equals(challenge))
            throw new Exception("WRITER_LAUNCH_GATE_INVALID");
        // No world access or child process exists before the held-token grant.
        Path manifest = control.resolve("launch-command.tsv");
        if (Files.isSymbolicLink(manifest) || Files.size(manifest) > 131072)
            throw new Exception("WRITER_LAUNCH_COMMAND");
        List<String> lines = Files.readAllLines(manifest, StandardCharsets.US_ASCII);
        if (lines.size() < 2 || lines.size() > 64) throw new Exception("WRITER_LAUNCH_COMMAND");
        var command = lines.stream().map(line -> new String(Base64.getDecoder().decode(line),
                                                           StandardCharsets.UTF_8)).toList();
        if (!Path.of(command.get(0)).isAbsolute()) throw new Exception("WRITER_LAUNCH_COMMAND");
        Process child = new ProcessBuilder(command).directory(root.toFile()).inheritIO().start();
        System.exit(child.waitFor()); // The controller owns every descendant in the retained Job.
    }
}
