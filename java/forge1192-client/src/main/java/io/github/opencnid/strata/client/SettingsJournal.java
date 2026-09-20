package io.github.opencnid.strata.client;

import com.google.gson.JsonObject;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.channels.FileChannel;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.ArrayList;
import java.util.List;

/** Append/force journal. Corrupt or partial tails fence recovery instead of being discarded. */
final class SettingsJournal {
    private final Path path;
    private final long quota;
    private final String frameSchema;
    private final List<JsonObject> entries = new ArrayList<>();
    private String previous = "0".repeat(64);
    private long bytes;
    private boolean poisoned;

    SettingsJournal(Path path, String profileIdentity, long quota) throws IOException {
        this(path, profileIdentity, quota, "strata/SettingsJournalFrame/1");
    }

    SettingsJournal(Path path, String profileIdentity, long quota, String frameSchema) throws IOException {
        this.path = path;
        this.quota = quota;
        if (!java.util.Set.of("strata/SettingsJournalFrame/1", "strata/NativeGameJournalFrame/1").contains(frameSchema)) {
            throw new IOException("SCHEMA_UNSUPPORTED");
        }
        this.frameSchema = frameSchema;
        SettingsFiles.safeExisting(path.getParent());
        if (Files.exists(path)) {
            SettingsFiles.safeExisting(path);
            if (!Files.isRegularFile(path) || Files.size(path) > quota) throw new IOException("SETTINGS_JOURNAL_INVALID");
            byte[] raw;
            try (var input = Files.newInputStream(path)) { raw = input.readNBytes(Math.toIntExact(quota + 1)); }
            if (raw.length > quota) throw new IOException("SETTINGS_JOURNAL_INVALID");
            bytes = raw.length;
            String text = StandardCharsets.UTF_8.newDecoder().decode(ByteBuffer.wrap(raw)).toString();
            if (!text.isEmpty() && !text.endsWith("\n")) throw new IOException("SETTINGS_JOURNAL_PARTIAL_TAIL");
            String[] lines = text.split("\n", -1);
            for (int index = 0; index < lines.length - 1; index++) {
                String line = lines[index];
                if (line.isEmpty()) throw new IOException("SETTINGS_JOURNAL_INVALID");
                JsonObject frame = SettingsJson.read(line);
                SettingsJson.fields(frame, "schema", "seq", "previous", "payload", "sha256");
                if (!frameSchema.equals(SettingsJson.string(frame, "schema"))
                        || SettingsJson.integer(frame, "seq") != entries.size() + 1L
                        || !previous.equals(SettingsJson.string(frame, "previous"))
                        || !frame.get("payload").isJsonObject() || entries.size() >= 10000) {
                    throw new IOException("SETTINGS_JOURNAL_INVALID");
                }
                JsonObject payload = frame.getAsJsonObject("payload");
                if (!entries.isEmpty() && "profile".equals(SettingsJson.string(payload, "kind"))) {
                    throw new IOException("SETTINGS_JOURNAL_INVALID");
                }
                String hash = KeyOptions.sha256(previous + "\n" + payload);
                if (!hash.equals(SettingsJson.string(frame, "sha256"))) throw new IOException("SETTINGS_JOURNAL_HASH_MISMATCH");
                entries.add(payload);
                previous = hash;
            }
        }
        if (entries.isEmpty()) {
            JsonObject header = new JsonObject();
            header.addProperty("kind", "profile");
            header.addProperty("identity", profileIdentity);
            append(header);
        } else {
            SettingsJson.fields(entries.get(0), "kind", "identity");
            if (!"profile".equals(SettingsJson.string(entries.get(0), "kind"))
                    || !profileIdentity.equals(SettingsJson.string(entries.get(0), "identity"))) {
                throw new IOException("SETTINGS_JOURNAL_PROFILE_MISMATCH");
            }
        }
    }

    long revision() { return entries.size(); }
    List<JsonObject> entries() { return entries.stream().map(JsonObject::deepCopy).toList(); }

    void reserve(long additional) throws IOException {
        if (poisoned || additional < 0 || bytes + additional > quota || entries.size() > 9990) {
            throw new IOException("SETTINGS_JOURNAL_EXHAUSTED");
        }
    }

    void append(JsonObject payload) throws IOException {
        String hash = KeyOptions.sha256(previous + "\n" + payload);
        JsonObject frame = new JsonObject();
        frame.addProperty("schema", frameSchema);
        frame.addProperty("seq", entries.size() + 1L);
        frame.addProperty("previous", previous);
        frame.add("payload", payload.deepCopy());
        frame.addProperty("sha256", hash);
        byte[] line = (frame + "\n").getBytes(StandardCharsets.UTF_8);
        if (line.length > 1048576) throw new IOException("SETTINGS_JOURNAL_FRAME_TOO_LARGE");
        reserve(line.length);
        try {
            if (Files.exists(path)) SettingsFiles.safeExisting(path);
            try (FileChannel output = FileChannel.open(path, StandardOpenOption.CREATE,
                    StandardOpenOption.WRITE, StandardOpenOption.APPEND)) {
                if (output.size() != bytes) throw new IOException("SETTINGS_JOURNAL_CONCURRENT_WRITE");
                ByteBuffer buffer = ByteBuffer.wrap(line);
                while (buffer.hasRemaining()) output.write(buffer);
                output.force(true);
            }
        } catch (IOException error) { poisoned = true; throw error; }
        entries.add(payload.deepCopy());
        previous = hash;
        bytes += line.length;
    }
}
