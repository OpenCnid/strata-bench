package io.github.opencnid.strata.telemetry;

import com.google.gson.JsonObject;
import com.google.gson.stream.JsonReader;
import com.google.gson.stream.JsonToken;
import com.sun.jna.Memory;
import com.sun.jna.Native;
import com.sun.jna.Pointer;
import com.sun.jna.Structure;
import com.sun.jna.WString;
import com.sun.jna.ptr.IntByReference;
import com.sun.jna.win32.StdCallLibrary;
import java.io.IOException;
import java.io.StringReader;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.HashSet;
import java.util.HexFormat;
import java.util.Set;

/** Windows-only private ingress. No signing key, spool path, retry or reconnect. */
final class PipeTelemetry implements AutoCloseable {
    interface Kernel extends StdCallLibrary {
        Pointer CreateFileW(WString name, int access, int share, Pointer security, int disposition,
                            int flags, Pointer template);
        Pointer CreateEventW(Pointer security, boolean manual, boolean initial, WString name);
        boolean CloseHandle(Pointer handle);
        boolean GetNamedPipeServerProcessId(Pointer pipe, IntByReference pid);
        boolean SetNamedPipeHandleState(Pointer pipe, IntByReference mode, Pointer count, Pointer timeout);
        Pointer OpenProcess(int access, boolean inherit, int pid);
        boolean GetProcessTimes(Pointer process, Pointer created, Pointer exited, Pointer kernel, Pointer user);
        boolean ReadFile(Pointer pipe, Pointer bytes, int length, IntByReference count, Pointer operation);
        boolean WriteFile(Pointer pipe, Pointer bytes, int length, IntByReference count, Pointer operation);
        int WaitForSingleObject(Pointer handle, int timeout);
        boolean GetOverlappedResult(Pointer pipe, Pointer operation, IntByReference count, boolean wait);
        boolean CancelIoEx(Pointer pipe, Pointer operation);
    }
    @Structure.FieldOrder({"internal", "internalHigh", "offset", "offsetHigh", "event"})
    public static class Overlapped extends Structure {
        public Pointer internal, internalHigh;
        public int offset, offsetHigh;
        public Pointer event;
    }
    private final Kernel kernel;
    private Pointer pipe;
    private String settings;
    private long sequence;

    private PipeTelemetry(Kernel kernel, Pointer pipe) { this.kernel = kernel; this.pipe = pipe; }

    static PipeTelemetry open(String descriptor) throws IOException {
        if (!System.getProperty("os.name").startsWith("Windows") || Native.POINTER_SIZE != 8)
            throw new IOException("TELEMETRY_PIPE_PLATFORM");
        String name = null, challenge = null, schema = null;
        long pid = -1, started = -1;
        Set<String> seen = new HashSet<>();
        try (JsonReader reader = new JsonReader(new StringReader(descriptor))) {
            reader.setLenient(false); reader.beginObject();
            while (reader.hasNext()) {
                String field = reader.nextName();
                if (!seen.add(field)) throw new IOException("TELEMETRY_PIPE_DESCRIPTOR");
                switch (field) {
                    case "schema" -> schema = TelemetryConfig.string(reader);
                    case "pipe_name" -> name = TelemetryConfig.string(reader);
                    case "challenge" -> challenge = TelemetryConfig.string(reader);
                    case "controller_pid" -> pid = TelemetryConfig.integer(reader);
                    case "controller_started_unix_ms" -> started = TelemetryConfig.integer(reader);
                    default -> throw new IOException("TELEMETRY_PIPE_DESCRIPTOR");
                }
            }
            reader.endObject();
            if (reader.peek() != JsonToken.END_DOCUMENT) throw new IOException("TELEMETRY_PIPE_DESCRIPTOR");
        }
        String prefix = "\\\\.\\pipe\\strata-telemetry-";
        if (seen.size() != 5 || !"strata/ForgeTelemetryConfig/4".equals(schema)
                || name == null || !name.startsWith(prefix) || !name.substring(prefix.length()).matches("[a-f0-9]{64}")
                || challenge == null || !challenge.matches("[a-f0-9]{64}")
                || pid < 1 || pid > Integer.MAX_VALUE || started < 1)
            throw new IOException("TELEMETRY_PIPE_DESCRIPTOR");
        Kernel kernel = Native.load("kernel32", Kernel.class);
        // Specific rights omit CREATE_PIPE_INSTANCE. Identification SQOS prevents
        // a peer from impersonating this token; the retained server handle is
        // checked independently before any configuration or event exchange.
        Pointer pipe = kernel.CreateFileW(new WString(name), 0x100183, 0, null, 3,
                                          0x40000000 | 0x110000, null);
        if (pipe == null || Pointer.nativeValue(pipe) == -1L) throw new IOException("TELEMETRY_PIPE_CONNECT");
        PipeTelemetry result = new PipeTelemetry(kernel, pipe);
        try {
            if (!kernel.SetNamedPipeHandleState(pipe, new IntByReference(2), null, null))
                throw new IOException("TELEMETRY_PIPE_IO");
            IntByReference actualPid = new IntByReference();
            if (!kernel.GetNamedPipeServerProcessId(pipe, actualPid) || actualPid.getValue() != pid)
                throw new IOException("TELEMETRY_PIPE_CONTROLLER");
            Pointer process = kernel.OpenProcess(0x100000 | 0x1000, false, actualPid.getValue());
            if (process == null) throw new IOException("TELEMETRY_PIPE_CONTROLLER");
            try (Memory created = new Memory(8); Memory exited = new Memory(8);
                 Memory system = new Memory(8); Memory user = new Memory(8)) {
                if (!kernel.GetProcessTimes(process, created, exited, system, user)
                        || created.getLong(0) / 10000 - 11644473600000L != started
                        || kernel.WaitForSingleObject(process, 0) != 258)
                    throw new IOException("TELEMETRY_PIPE_CONTROLLER");
            } finally { kernel.CloseHandle(process); }
            JsonObject hello = new JsonObject();
            hello.addProperty("schema", "strata/TelemetryPipeOpen/1");
            hello.addProperty("challenge", challenge);
            result.settings = result.exchange(hello.toString().getBytes(StandardCharsets.UTF_8), 65536);
            return result;
        } catch (Throwable error) { result.close(); throw error; }
    }

    String settings() { return settings; }

    private int io(boolean read, Memory data, int length) throws IOException {
        if (pipe == null) throw new IOException("TELEMETRY_PIPE_CLOSED");
        Overlapped operation = new Overlapped();
        operation.event = kernel.CreateEventW(null, true, false, null);
        if (operation.event == null) throw new IOException("TELEMETRY_PIPE_IO");
        // The kernel owns this memory until completion. Passing Structure to a
        // later JNA call would auto-write stale Java fields over its completion
        // status. Initialize once, then pass the same pinned native pointer.
        operation.write();
        Pointer nativeOperation = operation.getPointer();
        try {
            IntByReference count = new IntByReference();
            boolean immediate = read ? kernel.ReadFile(pipe, data, length, count, nativeOperation)
                                     : kernel.WriteFile(pipe, data, length, count, nativeOperation);
            int error = Native.getLastError();
            if (!immediate && error != 997) throw new IOException("TELEMETRY_PIPE_IO");
            if (!immediate && kernel.WaitForSingleObject(operation.event, 2000) != 0) {
                kernel.CancelIoEx(pipe, nativeOperation);
                kernel.GetOverlappedResult(pipe, nativeOperation, count, true);
                throw new IOException("TELEMETRY_PIPE_DEADLINE");
            }
            if (!kernel.GetOverlappedResult(pipe, nativeOperation, count, false))
                throw new IOException("TELEMETRY_PIPE_IO");
            return count.getValue();
        } finally { kernel.CloseHandle(operation.event); }
    }

    private String exchange(byte[] request, int limit) throws IOException {
        try (Memory output = new Memory(request.length); Memory input = new Memory(limit)) {
            output.write(0, request, 0, request.length);
            if (io(false, output, request.length) != request.length) throw new IOException("TELEMETRY_PIPE_IO");
            int read = io(true, input, limit);
            if (read < 1 || read > limit) throw new IOException("TELEMETRY_PIPE_IO");
            return new String(input.getByteArray(0, read), StandardCharsets.UTF_8);
        } catch (IOException error) { close(); throw error; }
    }

    synchronized void append(byte[] event, long next) throws IOException {
        if (next != sequence + 1) throw new IOException("TELEMETRY_PIPE_SEQUENCE");
        try {
            String hash = HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(event));
            verifyReceipt(exchange(event, 512), "strata/TelemetryPipeReceipt/1", next, hash);
            sequence = next;
        } catch (IOException error) { close(); throw error;
        } catch (java.security.GeneralSecurityException | RuntimeException error) {
            close(); throw new IOException("TELEMETRY_PIPE_RECEIPT", error);
        }
    }

    synchronized void finish(long count) throws IOException {
        JsonObject request = new JsonObject();
        request.addProperty("schema", "strata/TelemetryPipeFinish/1"); request.addProperty("sequence", count);
        try {
            if (count != sequence) throw new IOException("TELEMETRY_PIPE_RECEIPT");
            verifyReceipt(exchange(request.toString().getBytes(StandardCharsets.UTF_8), 512),
                          "strata/TelemetryPipeClosed/1", count, null);
        } catch (RuntimeException error) { throw new IOException("TELEMETRY_PIPE_RECEIPT", error); }
        finally { close(); }
    }

    static void verifyReceipt(String text, String expectedSchema, long expectedSequence,
                              String expectedHash) throws IOException {
        Set<String> seen = new HashSet<>();
        String schema = null, hash = null;
        long sequence = -1;
        try (JsonReader reader = new JsonReader(new StringReader(text))) {
            reader.setLenient(false); reader.beginObject();
            while (reader.hasNext()) {
                String field = reader.nextName();
                if (!seen.add(field)) throw new IOException("TELEMETRY_PIPE_RECEIPT");
                switch (field) {
                    case "schema" -> schema = TelemetryConfig.string(reader);
                    case "sequence" -> sequence = TelemetryConfig.integer(reader);
                    case "event_sha256" -> hash = TelemetryConfig.string(reader);
                    default -> throw new IOException("TELEMETRY_PIPE_RECEIPT");
                }
            }
            reader.endObject();
            if (reader.peek() != JsonToken.END_DOCUMENT || !expectedSchema.equals(schema)
                    || sequence != expectedSequence || !java.util.Objects.equals(hash, expectedHash)
                    || !seen.equals(expectedHash == null ? Set.of("schema", "sequence")
                                                        : Set.of("schema", "sequence", "event_sha256")))
                throw new IOException("TELEMETRY_PIPE_RECEIPT");
        }
    }

    @Override public void close() {
        if (pipe != null) { kernel.CloseHandle(pipe); pipe = null; }
    }
}
