package io.github.opencnid.strata.client;

import com.google.gson.JsonObject;
import java.io.IOException;
import java.nio.channels.FileChannel;
import java.nio.channels.FileLock;
import java.nio.channels.OverlappingFileLockException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.TreeMap;

/** Durable client-thread settings writes. Applied is pending verification, never committed. */
final class SettingsStore implements AutoCloseable {
    record Binding(String translation, String value, boolean mutable) {}
    record Snapshot(long revision, String digest) {}
    record Change(String before, String after) {}
    record Receipt(String id, String phase, long revision, boolean committed) {}

    /** Internal conformance seam; normal stores never activate a fault observer. */
    enum WriteBoundary {
        APPLY_PREPARED, APPLY_RUNTIME_WRITTEN, APPLY_OPTIONS_WRITTEN,
        ROLLBACK_PREPARED, ROLLBACK_RUNTIME_WRITTEN, ROLLBACK_OPTIONS_WRITTEN
    }
    interface WriteObserver { void reached(WriteBoundary boundary) throws IOException; }

    interface RuntimePort {
        void requireClientThread() throws IOException;
        Map<String, Binding> bindings() throws IOException;
        void validateKeys(Map<String, String> changes) throws IOException;
        void setKeys(Map<String, String> changes) throws IOException;
        void releaseInputs() throws IOException;
    }

    private final RuntimePort runtime;
    private final String fingerprint;
    private final Path options;
    private final FileChannel lockChannel;
    private final FileLock profileLock;
    private final SettingsJournal journal;
    private final WriteObserver observer;
    private final Map<String, JsonObject> prepared = new LinkedHashMap<>();
    private final Map<String, String> phases = new LinkedHashMap<>();
    private String active;
    private String observedDigest;
    private boolean closed;

    SettingsStore(Path profile, Path privateDirectory, String fingerprint, RuntimePort runtime) throws IOException {
        this(profile, privateDirectory, fingerprint, runtime, 16777216);
    }

    SettingsStore(Path profile, Path privateDirectory, String fingerprint, RuntimePort runtime, long quota) throws IOException {
        this(profile, privateDirectory, fingerprint, runtime, quota, boundary -> {});
    }

    SettingsStore(Path profile, Path privateDirectory, String fingerprint, RuntimePort runtime,
                  long quota, WriteObserver observer) throws IOException {
        this.runtime = runtime;
        this.fingerprint = fingerprint;
        this.observer = java.util.Objects.requireNonNull(observer);
        runtime.requireClientThread();
        if (!fingerprint.matches("[0-9a-f]{64}") || quota < 4096 || quota > 67108864) {
            throw new IOException("SETTINGS_PROFILE_INVALID");
        }
        profile = SettingsFiles.safeExisting(profile);
        privateDirectory = SettingsFiles.safeExisting(privateDirectory);
        if (!Files.isDirectory(profile) || !Files.isDirectory(privateDirectory)
                || privateDirectory.startsWith(profile) || profile.startsWith(privateDirectory)) {
            throw new IOException("SETTINGS_PRIVATE_ROOT_REQUIRED");
        }
        options = profile.resolve("options.txt");
        Path lockPath = profile.resolve(".strata-client-settings.lock");
        if (Files.exists(lockPath)) SettingsFiles.safeExisting(lockPath);
        lockChannel = FileChannel.open(lockPath, StandardOpenOption.CREATE, StandardOpenOption.WRITE);
        FileLock acquired = null;
        try {
            try { acquired = lockChannel.tryLock(); }
            catch (OverlappingFileLockException error) { throw new IOException("SETTINGS_PROFILE_BUSY", error); }
            if (acquired == null) throw new IOException("SETTINGS_PROFILE_BUSY");
            profileLock = acquired;
            String identity = KeyOptions.sha256(profile + "\n" + fingerprint);
            journal = new SettingsJournal(privateDirectory.resolve("settings-journal.jsonl"), identity, quota);
            for (JsonObject event : journal.entries()) replay(event);
        } catch (IOException | RuntimeException error) {
            if (acquired != null) acquired.release();
            lockChannel.close();
            throw error;
        }
    }

    private void ready() throws IOException {
        runtime.requireClientThread();
        if (closed || !profileLock.isValid()) throw new IOException("SETTINGS_PROFILE_NOT_OWNED");
    }

    private Map<String, Binding> bindings() throws IOException {
        Map<String, Binding> bindings = new TreeMap<>(runtime.bindings());
        if (bindings.isEmpty() || bindings.size() > 2048) throw new IOException("KEYMAP_INVALID");
        for (var entry : bindings.entrySet()) {
            if (!entry.getKey().matches("[A-Za-z0-9_.:-]{1,128}") || entry.getValue() == null
                    || entry.getValue().translation() == null || entry.getValue().translation().length() > 256
                    || entry.getValue().value() == null || entry.getValue().value().length() > 256) {
                throw new IOException("KEYMAP_INVALID");
            }
        }
        return bindings;
    }

    private static Map<String, String> values(Map<String, Binding> bindings) {
        Map<String, String> result = new TreeMap<>();
        bindings.forEach((id, binding) -> result.put(id, binding.value()));
        return result;
    }

    private static String metadataDigest(Map<String, Binding> bindings) {
        JsonObject value = new JsonObject();
        new TreeMap<>(bindings).forEach((id, binding) -> {
            JsonObject metadata = new JsonObject();
            metadata.addProperty("translation", binding.translation());
            metadata.addProperty("mutable", binding.mutable());
            value.add(id, metadata);
        });
        return KeyOptions.sha256(value.toString());
    }

    private String currentDigest() throws IOException {
        Map<String, Binding> bindings = bindings();
        return KeyOptions.sha256(fingerprint + "\n" + metadataDigest(bindings) + "\n"
            + SettingsJson.strings(values(bindings)) + "\n" + KeyOptions.sha256(SettingsFiles.readOptions(options)));
    }

    Snapshot snapshot() throws IOException {
        ready();
        // Preserve the recovery headroom reserved before the active mutation.
        if (active != null) throw new IOException("SETTINGS_RECOVERY_REQUIRED");
        String digest = currentDigest();
        if (!digest.equals(observedDigest)) {
            JsonObject event = new JsonObject();
            event.addProperty("kind", "observed");
            event.addProperty("digest", digest);
            append(event);
        }
        return new Snapshot(journal.revision(), digest);
    }

    JsonObject inspect() throws IOException {
        ready();
        Snapshot snapshot = active == null ? snapshot() : new Snapshot(journal.revision(), currentDigest());
        JsonObject result = new JsonObject(), entries = new JsonObject();
        result.addProperty("fingerprint", fingerprint);
        result.addProperty("revision", snapshot.revision());
        result.addProperty("digest", snapshot.digest());
        result.addProperty("active_transaction", active);
        result.addProperty("active_phase", active == null ? null : phases.get(active));
        KeyOptions persisted = KeyOptions.parse(SettingsFiles.readOptions(options));
        result.addProperty("options_sha256", persisted.fileDigest());
        for (var entry : bindings().entrySet()) {
            Binding binding = entry.getValue();
            JsonObject value = new JsonObject();
            value.addProperty("translation", binding.translation());
            value.addProperty("runtime_value", binding.value());
            value.addProperty("persisted_value", persisted.values().get(binding.translation()));
            value.addProperty("persisted_ambiguous", persisted.ambiguous().contains(binding.translation()));
            value.addProperty("operator_mutable", binding.mutable());
            entries.add(entry.getKey(), value);
        }
        result.add("bindings", entries);
        // No effect/physical input/OS isolation evidence is established by this protocol.
        result.addProperty("supported", false);
        result.addProperty("operator_development_only", true);
        return result;
    }

    Receipt status(String id) throws IOException {
        ready();
        if (!phases.containsKey(id)) throw new IOException("SETTINGS_TRANSACTION_MISSING");
        return new Receipt(id, phases.get(id), journal.revision(), false);
    }

    private static JsonObject request(String id, Snapshot expected, Map<String, Change> changes) throws IOException {
        if (id == null || !id.matches("[A-Za-z0-9_.:-]{1,128}") || expected == null
                || expected.revision() < 1 || expected.digest() == null || !expected.digest().matches("[0-9a-f]{64}")
                || changes == null || changes.isEmpty() || changes.size() > 32) throw new IOException("SETTINGS_PATCH_INVALID");
        JsonObject request = new JsonObject(), edits = new JsonObject();
        request.addProperty("id", id);
        request.addProperty("expected_revision", expected.revision());
        request.addProperty("expected_digest", expected.digest());
        for (var entry : new TreeMap<>(changes).entrySet()) {
            Change change = entry.getValue();
            if (change == null || change.before() == null || change.after() == null
                    || change.before().equals(change.after())) throw new IOException("SETTINGS_PATCH_INVALID");
            JsonObject item = new JsonObject();
            item.addProperty("before", change.before());
            item.addProperty("after", change.after());
            edits.add(entry.getKey(), item);
        }
        request.add("changes", edits);
        return request;
    }

    Receipt apply(String id, Snapshot expected, Map<String, Change> changes) throws IOException {
        ready();
        String requestDigest = KeyOptions.sha256(request(id, expected, changes).toString());
        if (prepared.containsKey(id)) {
            if (!requestDigest.equals(SettingsJson.string(prepared.get(id), "request_digest"))) {
                throw new IOException("SETTINGS_IDEMPOTENCY_CONFLICT");
            }
            return status(id); // An interrupted or terminal transaction is never re-dispatched.
        }
        if (active != null) throw new IOException("SETTINGS_RECOVERY_REQUIRED");
        runtime.releaseInputs();
        try {
            if (!snapshot().equals(expected)) throw new IOException("SETTINGS_REVISION_CONFLICT");
            Map<String, Binding> current = bindings();
            String original = SettingsFiles.readOptions(options);
            Map<String, String> before = new TreeMap<>(), after = new TreeMap<>(), translations = new TreeMap<>();
            for (var entry : changes.entrySet()) {
                Binding binding = current.get(entry.getKey());
                if (binding == null || !binding.mutable() || current.values().stream()
                        .filter(other -> other.translation().equals(binding.translation())).count() != 1) {
                    throw new IOException("PROTECTED_OR_UNKNOWN_BINDING");
                }
                if (!binding.value().equals(entry.getValue().before())) throw new IOException("SETTINGS_REVISION_CONFLICT");
                SettingsFiles.keyField(binding.translation(), binding.value());
                SettingsFiles.keyField(binding.translation(), entry.getValue().after());
                before.put(entry.getKey(), binding.value());
                after.put(entry.getKey(), entry.getValue().after());
                translations.put(entry.getKey(), binding.translation());
            }
            runtime.validateKeys(after);
            Map<String, String> beforeDisk = translate(before, translations), afterDisk = translate(after, translations);
            String replacement = SettingsFiles.patch(original, beforeDisk, afterDisk);
            JsonObject prepare = new JsonObject();
            prepare.addProperty("kind", "prepared");
            prepare.addProperty("id", id);
            prepare.addProperty("request_digest", requestDigest);
            prepare.addProperty("expected_revision", expected.revision());
            prepare.addProperty("expected_digest", expected.digest());
            prepare.addProperty("options_before_digest", KeyOptions.sha256(original));
            prepare.addProperty("non_owned_options_digest", SettingsFiles.nonOwnedDigest(original, beforeDisk));
            prepare.addProperty("runtime_metadata_digest", metadataDigest(current));
            prepare.add("before_runtime", SettingsJson.strings(values(current)));
            prepare.add("translations", SettingsJson.strings(translations));
            prepare.add("before", SettingsJson.strings(before));
            prepare.add("after", SettingsJson.strings(after));
            // Keep space for rollback and its failure/terminal receipts before mutation.
            journal.reserve(prepare.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8).length + 16384L);
            append(prepare);
            observer.reached(WriteBoundary.APPLY_PREPARED);
            runtime.setKeys(after);
            Map<String, String> desiredRuntime = new TreeMap<>(values(current));
            desiredRuntime.putAll(after);
            assertRuntime(desiredRuntime, metadataDigest(current));
            observer.reached(WriteBoundary.APPLY_RUNTIME_WRITTEN);
            SettingsFiles.replaceOwned(options, original, replacement);
            observer.reached(WriteBoundary.APPLY_OPTIONS_WRITTEN);
            runtime.releaseInputs();
            assertRuntime(desiredRuntime, metadataDigest(current));
            phase(id, "applied_pending_verification");
            return status(id);
        } finally { runtime.releaseInputs(); }
    }

    private void assertRuntime(Map<String, String> expected, String metadata) throws IOException {
        Map<String, Binding> current = bindings();
        if (!values(current).equals(expected) || !metadataDigest(current).equals(metadata)) {
            throw new IOException("SETTINGS_RUNTIME_CONFLICT");
        }
    }

    private static Map<String, String> translate(Map<String, String> values, Map<String, String> translations) throws IOException {
        if (!values.keySet().equals(translations.keySet())) throw new IOException("SETTINGS_JOURNAL_INVALID");
        Map<String, String> result = new TreeMap<>();
        for (var entry : values.entrySet()) {
            if (result.put(translations.get(entry.getKey()), entry.getValue()) != null) {
                throw new IOException("SETTINGS_JOURNAL_INVALID");
            }
        }
        return result;
    }

    Receipt rollback(String id) throws IOException {
        ready();
        if (!prepared.containsKey(id)) throw new IOException("SETTINGS_TRANSACTION_MISSING");
        if ("rolled_back".equals(phases.get(id))) return status(id);
        if (!id.equals(active)) throw new IOException("SETTINGS_TRANSACTION_NOT_ACTIVE");
        runtime.releaseInputs();
        try {
            JsonObject transaction = prepared.get(id);
            Map<String, String> before = SettingsJson.strings(transaction, "before");
            Map<String, String> after = SettingsJson.strings(transaction, "after");
            Map<String, String> translations = SettingsJson.strings(transaction, "translations");
            Map<String, String> originalRuntime = SettingsJson.strings(transaction, "before_runtime");
            String metadata = SettingsJson.string(transaction, "runtime_metadata_digest");
            Map<String, Binding> current = bindings();
            if (!metadata.equals(metadataDigest(current)) || !current.keySet().equals(originalRuntime.keySet())) {
                throw new IOException("SETTINGS_ROLLBACK_CONFLICT");
            }
            for (var entry : current.entrySet()) {
                String value = entry.getValue().value();
                if (before.containsKey(entry.getKey()) ? !value.equals(before.get(entry.getKey()))
                        && !value.equals(after.get(entry.getKey())) : !value.equals(originalRuntime.get(entry.getKey()))) {
                    throw new IOException("SETTINGS_ROLLBACK_CONFLICT");
                }
            }
            String diskText = SettingsFiles.readOptions(options);
            KeyOptions disk = KeyOptions.parse(diskText);
            Map<String, String> beforeDisk = translate(before, translations), afterDisk = translate(after, translations);
            if (!SettingsFiles.nonOwnedDigest(diskText, beforeDisk)
                    .equals(SettingsJson.string(transaction, "non_owned_options_digest"))) {
                throw new IOException("SETTINGS_ROLLBACK_CONFLICT");
            }
            Map<String, String> diskCurrent = new TreeMap<>();
            for (var entry : beforeDisk.entrySet()) {
                String value = disk.values().get(entry.getKey());
                if (!entry.getValue().equals(value) && !afterDisk.get(entry.getKey()).equals(value)) {
                    throw new IOException("SETTINGS_ROLLBACK_CONFLICT");
                }
                diskCurrent.put(entry.getKey(), value);
            }
            String restored = SettingsFiles.patch(diskText, diskCurrent, beforeDisk);
            runtime.validateKeys(before);
            journal.reserve(4096);
            phase(id, "rollback_prepared");
            observer.reached(WriteBoundary.ROLLBACK_PREPARED);
            runtime.setKeys(before);
            assertRuntime(originalRuntime, metadata);
            observer.reached(WriteBoundary.ROLLBACK_RUNTIME_WRITTEN);
            if (!restored.equals(diskText)) SettingsFiles.replaceOwned(options, diskText, restored);
            if (!SettingsFiles.readOptions(options).equals(restored)) throw new IOException("SETTINGS_ROLLBACK_UNCONFIRMED");
            observer.reached(WriteBoundary.ROLLBACK_OPTIONS_WRITTEN);
            runtime.releaseInputs();
            assertRuntime(originalRuntime, metadata);
            phase(id, "rolled_back");
            return status(id);
        } catch (IOException | RuntimeException error) {
            try { phase(id, "rollback_conflict"); }
            catch (IOException journalError) { error.addSuppressed(journalError); }
            throw error;
        } finally { runtime.releaseInputs(); }
    }

    Receipt recover() throws IOException {
        ready();
        if (active == null) throw new IOException("SETTINGS_NO_RECOVERY_PENDING");
        return rollback(active);
    }

    private void phase(String id, String phase) throws IOException {
        JsonObject event = new JsonObject();
        event.addProperty("kind", phase);
        event.addProperty("id", id);
        append(event);
    }

    private void append(JsonObject event) throws IOException { journal.append(event); replay(event); }

    private void replay(JsonObject event) throws IOException {
        String kind = SettingsJson.string(event, "kind");
        if (kind.equals("profile")) return;
        if (kind.equals("observed")) {
            SettingsJson.fields(event, "kind", "digest");
            observedDigest = SettingsJson.string(event, "digest");
            if (!observedDigest.matches("[0-9a-f]{64}")) throw new IOException("SETTINGS_JOURNAL_INVALID");
            return;
        }
        String id = SettingsJson.string(event, "id");
        if (!id.matches("[A-Za-z0-9_.:-]{1,128}")) throw new IOException("SETTINGS_JOURNAL_INVALID");
        if (kind.equals("prepared")) {
            SettingsJson.fields(event, "kind", "id", "request_digest", "expected_revision", "expected_digest",
                "options_before_digest", "non_owned_options_digest", "runtime_metadata_digest",
                "before_runtime", "translations", "before", "after");
            if (active != null || prepared.containsKey(id)) throw new IOException("SETTINGS_JOURNAL_INVALID");
            for (String field : java.util.List.of("request_digest", "expected_digest", "options_before_digest",
                    "non_owned_options_digest", "runtime_metadata_digest")) {
                if (!SettingsJson.string(event, field).matches("[0-9a-f]{64}")) {
                    throw new IOException("SETTINGS_JOURNAL_INVALID");
                }
            }
            if (SettingsJson.integer(event, "expected_revision") < 1) throw new IOException("SETTINGS_JOURNAL_INVALID");
            Map<String, String> before = SettingsJson.strings(event, "before");
            Map<String, String> after = SettingsJson.strings(event, "after");
            Map<String, String> translations = SettingsJson.strings(event, "translations");
            Map<String, String> all = SettingsJson.strings(event, "before_runtime");
            if (before.isEmpty() || before.size() > 32 || !before.keySet().equals(after.keySet())
                    || !before.keySet().equals(translations.keySet()) || !all.entrySet().containsAll(before.entrySet())
                    || new HashSet<>(translations.values()).size() != translations.size()) {
                throw new IOException("SETTINGS_JOURNAL_INVALID");
            }
            for (String key : before.keySet()) {
                if (before.get(key).equals(after.get(key))) throw new IOException("SETTINGS_JOURNAL_INVALID");
                SettingsFiles.keyField(translations.get(key), before.get(key));
                SettingsFiles.keyField(translations.get(key), after.get(key));
            }
            prepared.put(id, event.deepCopy());
            phases.put(id, kind);
            active = id;
            return;
        }
        SettingsJson.fields(event, "kind", "id");
        if (!id.equals(active) || !prepared.containsKey(id)) throw new IOException("SETTINGS_JOURNAL_INVALID");
        String previous = phases.get(id);
        if (kind.equals("applied_pending_verification") && !previous.equals("prepared")) throw new IOException("SETTINGS_JOURNAL_INVALID");
        if (kind.equals("rolled_back") && !previous.equals("rollback_prepared")) throw new IOException("SETTINGS_JOURNAL_INVALID");
        if (!java.util.Set.of("applied_pending_verification", "rollback_prepared", "rolled_back", "rollback_conflict").contains(kind)) {
            throw new IOException("SETTINGS_JOURNAL_INVALID");
        }
        phases.put(id, kind);
        if (kind.equals("rolled_back")) active = null;
    }

    @Override public void close() throws IOException {
        if (closed) return;
        runtime.requireClientThread();
        closed = true;
        try { runtime.releaseInputs(); }
        finally { try { profileLock.release(); } finally { lockChannel.close(); } }
    }
}
