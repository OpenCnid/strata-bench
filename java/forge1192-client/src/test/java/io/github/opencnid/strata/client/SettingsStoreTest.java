package io.github.opencnid.strata.client;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import static org.junit.jupiter.api.Assertions.*;

/** Real temporary files/locks with a deliberately synthetic client runtime. */
class SettingsStoreTest {
    static final String ID = "fixture:key.mod.action:0", PROTECTED = "minecraft:key.inventory:0";
    static final String BEFORE = "key.keyboard.g", AFTER = "key.keyboard.f13";
    static final String ORIGINAL = "lastServer:private.example\r\nrenderDistance:12\r\n"
        + "key_key.mod.action:" + BEFORE + "\r\nkey_key.inventory:key.keyboard.e\r\ncustom:opaque:日本語";
    static final String FINGERPRINT = "a".repeat(64);

    static class Runtime implements SettingsStore.RuntimePort {
        final Thread owner = Thread.currentThread();
        final Map<String, SettingsStore.Binding> map = new LinkedHashMap<>();
        int writes, releases;
        boolean interruptAfterWrite;
        Runnable afterWrite;
        Runtime() {
            map.put(ID, new SettingsStore.Binding("key.mod.action", BEFORE, true));
            map.put(PROTECTED, new SettingsStore.Binding("key.inventory", "key.keyboard.e", false));
        }
        @Override public void requireClientThread() throws IOException {
            if (owner != Thread.currentThread()) throw new IOException("CLIENT_THREAD_REQUIRED");
        }
        @Override public Map<String, SettingsStore.Binding> bindings() { return Map.copyOf(map); }
        @Override public void validateKeys(Map<String, String> changes) throws IOException {
            if (changes.values().stream().anyMatch(v -> !v.matches("key.keyboard.(?:g|f13|e)"))) {
                throw new IOException("UNSUPPORTED_PHYSICAL_KEY");
            }
        }
        @Override public void setKeys(Map<String, String> changes) throws IOException {
            requireClientThread();
            writes++;
            changes.forEach((id, value) -> {
                var old = map.get(id);
                map.put(id, new SettingsStore.Binding(old.translation(), value, old.mutable()));
            });
            if (afterWrite != null) afterWrite.run();
            if (interruptAfterWrite) throw new IOException("SYNTHETIC_INTERRUPTED_AFTER_RUNTIME_WRITE");
        }
        @Override public void releaseInputs() { releases++; }
        void external(String id, String value) {
            var old = map.get(id);
            map.put(id, new SettingsStore.Binding(old.translation(), value, old.mutable()));
        }
    }

    record Fixture(Path profile, Path journal, Runtime runtime) {
        SettingsStore open() throws IOException { return new SettingsStore(profile, journal, FINGERPRINT, runtime); }
        Path options() { return profile.resolve("options.txt"); }
        String text() throws IOException { return Files.readString(options()); }
    }

    Fixture fixture(Path root) throws IOException {
        Path profile = Files.createDirectory(root.resolve("profile"));
        Path journal = Files.createDirectory(root.resolve("private"));
        Files.writeString(profile.resolve("options.txt"), ORIGINAL);
        return new Fixture(profile, journal, new Runtime());
    }

    Map<String, SettingsStore.Change> change() { return Map.of(ID, new SettingsStore.Change(BEFORE, AFTER)); }

    @Test void appliedIsPendingVerificationDeduplicatedAndRollbackPreservesAllUnownedBytes(@TempDir Path root) throws Exception {
        Fixture f = fixture(root);
        try (SettingsStore store = f.open()) {
            var expected = store.snapshot();
            var receipt = store.apply("tx1", expected, change());
            assertEquals("applied_pending_verification", receipt.phase());
            assertFalse(receipt.committed());
            assertEquals(ORIGINAL.replace("key_key.mod.action:" + BEFORE, "key_key.mod.action:" + AFTER), f.text());
            assertEquals(AFTER, f.runtime.map.get(ID).value());
            assertEquals(receipt, store.apply("tx1", expected, change()));
            assertEquals(1, f.runtime.writes);
            assertThrows(IOException.class, () -> store.apply("tx2", store.snapshot(), change()));
            assertEquals("rolled_back", store.rollback("tx1").phase());
            assertEquals(ORIGINAL, f.text());
            assertEquals(BEFORE, f.runtime.map.get(ID).value());
            int calls = f.runtime.writes;
            assertEquals("rolled_back", store.apply("tx1", expected, change()).phase());
            store.rollback("tx1");
            assertEquals(calls, f.runtime.writes);
            assertTrue(f.runtime.releases >= 4);
        }
    }

    @Test void changedRequestWithSameIdCannotRedispatch(@TempDir Path root) throws Exception {
        Fixture f = fixture(root);
        try (SettingsStore store = f.open()) {
            var expected = store.snapshot();
            store.apply("tx", expected, change());
            IOException error = assertThrows(IOException.class, () -> store.apply("tx", expected,
                Map.of(ID, new SettingsStore.Change(BEFORE, "key.keyboard.e"))));
            assertEquals("SETTINGS_IDEMPOTENCY_CONFLICT", error.getMessage());
            assertEquals(1, f.runtime.writes);
            store.rollback("tx");
        }
    }

    @Test void staleRevisionAndProtectedBindingsFailBeforeMutation(@TempDir Path root) throws Exception {
        Fixture f = fixture(root);
        try (SettingsStore store = f.open()) {
            var expected = store.snapshot();
            Files.writeString(f.options(), ORIGINAL.replace("renderDistance:12", "renderDistance:8"));
            assertEquals("SETTINGS_REVISION_CONFLICT", assertThrows(IOException.class,
                () -> store.apply("stale", expected, change())).getMessage());
            var fresh = store.snapshot();
            assertEquals("PROTECTED_OR_UNKNOWN_BINDING", assertThrows(IOException.class,
                () -> store.apply("protected", fresh, Map.of(PROTECTED,
                    new SettingsStore.Change("key.keyboard.e", AFTER)))).getMessage());
            assertEquals(0, f.runtime.writes);
            assertTrue(f.text().contains("renderDistance:8"));
        }
    }

    @Test void duplicatePersistedFieldAndUnsupportedKeyCannotMutate(@TempDir Path root) throws Exception {
        Fixture f = fixture(root);
        try (SettingsStore store = f.open()) {
            Files.writeString(f.options(), ORIGINAL + "\nkey_key.mod.action:key.keyboard.g\n");
            assertEquals("OPTIONS_REVISION_CONFLICT", assertThrows(IOException.class,
                () -> store.apply("duplicate", store.snapshot(), change())).getMessage());
            Files.writeString(f.options(), ORIGINAL);
            assertEquals("UNSUPPORTED_PHYSICAL_KEY", assertThrows(IOException.class,
                () -> store.apply("unsupported", store.snapshot(), Map.of(ID,
                    new SettingsStore.Change(BEFORE, "key.keyboard.9999999")))).getMessage());
            assertEquals(0, f.runtime.writes);
            assertEquals(ORIGINAL, f.text());
        }
    }

    @Test void oneProfileLockAppliesEvenWhenOtherCallerChoosesAnotherJournal(@TempDir Path root) throws Exception {
        Fixture f = fixture(root);
        Path other = Files.createDirectory(root.resolve("other-private"));
        try (SettingsStore store = f.open()) {
            assertNotNull(store.snapshot());
            IOException error = assertThrows(IOException.class,
                () -> new SettingsStore(f.profile, other, FINGERPRINT, new Runtime()));
            assertEquals("SETTINGS_PROFILE_BUSY", error.getMessage());
        }
        try (SettingsStore reopened = f.open()) { assertNotNull(reopened.snapshot()); }
    }

    @Test void wrongProfileOrRuntimeFingerprintCannotUseExistingJournal(@TempDir Path root) throws Exception {
        Fixture f = fixture(root);
        try (SettingsStore store = f.open()) { store.snapshot(); }
        assertEquals("SETTINGS_JOURNAL_PROFILE_MISMATCH", assertThrows(IOException.class,
            () -> new SettingsStore(f.profile, f.journal, "b".repeat(64), f.runtime)).getMessage());
        Path otherProfile = Files.createDirectory(root.resolve("other-profile"));
        Files.writeString(otherProfile.resolve("options.txt"), ORIGINAL);
        assertEquals("SETTINGS_JOURNAL_PROFILE_MISMATCH", assertThrows(IOException.class,
            () -> new SettingsStore(otherProfile, f.journal, FINGERPRINT, f.runtime)).getMessage());
    }

    @Test void interruptionAfterRuntimeMutationDoesNotBlindlyReplayAndRecoversBeforeFileWrite(@TempDir Path root) throws Exception {
        Fixture f = fixture(root);
        SettingsStore.Snapshot original;
        try (SettingsStore store = f.open()) {
            original = store.snapshot();
            f.runtime.interruptAfterWrite = true;
            assertThrows(IOException.class, () -> store.apply("interrupted", original, change()));
            assertEquals("prepared", store.status("interrupted").phase());
            assertEquals(ORIGINAL, f.text());
            assertEquals(AFTER, f.runtime.map.get(ID).value());
        }
        // A fresh client loads old disk values; recovery never re-applies AFTER.
        Runtime restarted = new Runtime();
        try (SettingsStore store = new SettingsStore(f.profile, f.journal, FINGERPRINT, restarted)) {
            assertEquals("prepared", store.apply("interrupted", original, change()).phase());
            assertEquals(0, restarted.writes);
            assertEquals("rolled_back", store.recover().phase());
            assertEquals(BEFORE, restarted.map.get(ID).value());
            assertEquals(ORIGINAL, f.text());
        }
    }

    @Test void appliedButUnverifiedTransactionSurvivesRestartAndRollsBack(@TempDir Path root) throws Exception {
        Fixture f = fixture(root);
        try (SettingsStore store = f.open()) { store.apply("pending", store.snapshot(), change()); }
        Runtime restarted = new Runtime();
        restarted.external(ID, AFTER); // The real client would load the applied options file.
        try (SettingsStore store = new SettingsStore(f.profile, f.journal, FINGERPRINT, restarted)) {
            assertEquals("applied_pending_verification", store.status("pending").phase());
            assertFalse(store.status("pending").committed());
            assertEquals("rolled_back", store.recover().phase());
            assertEquals(ORIGINAL, f.text());
        }
    }

    @Test void unrelatedConcurrentSettingsChangeIsNeverOverwrittenByRollback(@TempDir Path root) throws Exception {
        Fixture f = fixture(root);
        try (SettingsStore store = f.open()) {
            store.apply("pending", store.snapshot(), change());
            String foreign = f.text().replace("renderDistance:12", "renderDistance:7");
            Files.writeString(f.options(), foreign);
            assertEquals("SETTINGS_ROLLBACK_CONFLICT", assertThrows(IOException.class,
                () -> store.rollback("pending")).getMessage());
            assertEquals(foreign, f.text());
            assertEquals(AFTER, f.runtime.map.get(ID).value());
            assertEquals("rollback_conflict", store.status("pending").phase());
            assertEquals("SETTINGS_RECOVERY_REQUIRED", assertThrows(IOException.class,
                () -> store.apply("new", store.snapshot(), change())).getMessage());
        }
    }

    @Test void foreignOwnedValueAndUnrelatedRuntimeChangesFenceRollback(@TempDir Path root) throws Exception {
        Fixture f = fixture(root);
        try (SettingsStore store = f.open()) {
            store.apply("pending", store.snapshot(), change());
            f.runtime.external(ID, "key.keyboard.z");
            String disk = f.text();
            assertThrows(IOException.class, () -> store.rollback("pending"));
            assertEquals(disk, f.text());
            f.runtime.external(ID, AFTER);
            f.runtime.external(PROTECTED, "key.keyboard.i");
            assertThrows(IOException.class, store::recover);
            assertEquals(disk, f.text());
            assertEquals("key.keyboard.i", f.runtime.map.get(PROTECTED).value());
        }
    }

    @Test void concurrentFileChangeBetweenRuntimeSetAndPersistenceIsRetained(@TempDir Path root) throws Exception {
        Fixture f = fixture(root);
        f.runtime.afterWrite = () -> {
            try { Files.writeString(f.options(), ORIGINAL + "\nforeign:change\n"); }
            catch (IOException error) { throw new RuntimeException(error); }
        };
        try (SettingsStore store = f.open()) {
            assertEquals("OPTIONS_REVISION_CONFLICT", assertThrows(IOException.class,
                () -> store.apply("race", store.snapshot(), change())).getMessage());
            assertTrue(f.text().endsWith("foreign:change\n"));
            assertEquals("prepared", store.status("race").phase());
            assertThrows(IOException.class, store::recover);
            assertTrue(f.text().endsWith("foreign:change\n"));
        }
    }

    @Test void partialAndCorruptedJournalTailsFailClosed(@TempDir Path root) throws Exception {
        Fixture f = fixture(root);
        try (SettingsStore store = f.open()) { store.snapshot(); }
        Path journal = f.journal.resolve("settings-journal.jsonl");
        String clean = Files.readString(journal);
        Files.writeString(journal, "{\"interrupted\":", StandardOpenOption.APPEND);
        assertEquals("SETTINGS_JOURNAL_PARTIAL_TAIL", assertThrows(IOException.class, f::open).getMessage());
        Files.writeString(journal, clean.replace("\"kind\":\"profile\"", "\"kind\":\"profiLe\""));
        assertEquals("SETTINGS_JOURNAL_HASH_MISMATCH", assertThrows(IOException.class, f::open).getMessage());
        assertEquals(0, f.runtime.writes);
    }

    @Test void quotaMustReserveRollbackSpaceBeforeMutation(@TempDir Path root) throws Exception {
        Fixture f = fixture(root);
        try (SettingsStore store = new SettingsStore(f.profile, f.journal, FINGERPRINT, f.runtime, 4096)) {
            assertEquals("SETTINGS_JOURNAL_EXHAUSTED", assertThrows(IOException.class,
                () -> store.apply("no-room", store.snapshot(), change())).getMessage());
            assertEquals(0, f.runtime.writes);
            assertEquals(ORIGINAL, f.text());
        }
    }

    @Test void blankJournalFramesAndRepeatedProfileHeadersAreRejected(@TempDir Path root) throws Exception {
        Fixture f = fixture(root);
        try (SettingsStore store = f.open()) { store.snapshot(); }
        Path path = f.journal.resolve("settings-journal.jsonl");
        String clean = Files.readString(path);
        for (String corrupted : new String[] {"\n" + clean, clean + "\n", clean.replaceFirst("\n", "\n\n")}) {
            Files.writeString(path, corrupted);
            assertEquals("SETTINGS_JOURNAL_INVALID", assertThrows(IOException.class, f::open).getMessage());
        }
        Files.writeString(path, clean);
        String identity = KeyOptions.sha256(f.profile.toRealPath() + "\n" + FINGERPRINT);
        SettingsJournal journal = new SettingsJournal(path, identity, 16777216);
        var duplicate = new com.google.gson.JsonObject();
        duplicate.addProperty("kind", "profile");
        duplicate.addProperty("identity", identity);
        journal.append(duplicate); // A correctly hash-chained but semantically invalid extra header.
        assertEquals("SETTINGS_JOURNAL_INVALID", assertThrows(IOException.class, f::open).getMessage());
        assertEquals(0, f.runtime.writes);
    }

    @Test void pendingSnapshotCannotConsumeRecoveryHeadroom(@TempDir Path root) throws Exception {
        Fixture f = fixture(root);
        try (SettingsStore store = f.open()) {
            store.apply("pending", store.snapshot(), change());
            Path journal = f.journal.resolve("settings-journal.jsonl");
            String original = Files.readString(journal);
            f.runtime.external(PROTECTED, "key.keyboard.i");
            assertEquals("SETTINGS_RECOVERY_REQUIRED", assertThrows(IOException.class, store::snapshot).getMessage());
            assertEquals(original, Files.readString(journal));
            f.runtime.external(PROTECTED, "key.keyboard.e");
            assertEquals("rolled_back", store.recover().phase());
        }
    }

    @Test void rolledBackTransactionsAllowNewRevisionAndRetainOldIdempotency(@TempDir Path root) throws Exception {
        Fixture f = fixture(root);
        SettingsStore.Snapshot first;
        try (SettingsStore store = f.open()) {
            first = store.snapshot();
            store.apply("first", first, change());
            store.rollback("first");
            var second = store.snapshot();
            assertTrue(second.revision() > first.revision());
            assertEquals(first.digest(), second.digest());
            store.apply("second", second, change());
        }
        Runtime restarted = new Runtime();
        restarted.external(ID, AFTER);
        try (SettingsStore store = new SettingsStore(f.profile, f.journal, FINGERPRINT, restarted)) {
            assertEquals("rolled_back", store.apply("first", first, change()).phase());
            assertEquals(0, restarted.writes);
            assertEquals("rolled_back", store.recover().phase());
            assertEquals(ORIGINAL, f.text());
        }
    }

    @Test void missingOptionsAndUnsafeRootsFailBeforeAnyRuntimeWrite(@TempDir Path root) throws Exception {
        Fixture f = fixture(root);
        assertThrows(IOException.class, () -> new SettingsStore(f.profile, f.profile, FINGERPRINT, f.runtime));
        assertThrows(IOException.class, () -> SettingsFiles.safeExisting(Path.of("relative")));
        Files.move(f.options(), f.profile.resolve("retained-options.txt"));
        try (SettingsStore store = f.open()) { assertThrows(IOException.class, store::snapshot); }
        assertEquals(0, f.runtime.writes);
    }

    @Test void unicodeLineSeparatorsCannotHideBytesInsideAnOwnedField(@TempDir Path root) throws Exception {
        Fixture f = fixture(root);
        for (String separator : new String[] {"\u000b", "\f", "\u0085", "\u2028", "\u2029"}) {
            String text = ORIGINAL.replace("key_key.mod.action:" + BEFORE,
                "key_key.mod.action:" + BEFORE + separator + "foreign:must-survive");
            Files.writeString(f.options(), text);
            try (SettingsStore store = f.open()) {
                assertThrows(IOException.class, () -> store.apply("invalid-line", store.snapshot(), change()));
                assertEquals(text, f.text());
            }
        }
        assertEquals(0, f.runtime.writes);
    }

    @Test void closedOrNonClientThreadCannotReadOrMutate(@TempDir Path root) throws Exception {
        Fixture f = fixture(root);
        SettingsStore store = f.open();
        AtomicReference<Throwable> failure = new AtomicReference<>();
        Thread foreign = new Thread(() -> {
            try { store.snapshot(); }
            catch (Throwable error) { failure.set(error); }
        });
        foreign.start();
        foreign.join();
        assertEquals("CLIENT_THREAD_REQUIRED", failure.get().getMessage());
        store.close();
        assertEquals("SETTINGS_PROFILE_NOT_OWNED", assertThrows(IOException.class, store::snapshot).getMessage());
    }

    @Test void strictPrivateJsonRejectsDuplicateKeysCoercionAndTrailingValues() throws Exception {
        assertThrows(IOException.class, () -> SettingsJson.read("{\"a\":1,\"a\":2}"));
        assertThrows(IOException.class, () -> SettingsJson.read("{\"a\":1.0}"));
        assertThrows(IOException.class, () -> SettingsJson.read("{} {}"));
        assertThrows(IOException.class, () -> SettingsJson.string(SettingsJson.read("{\"a\":2}"), "a"));
        assertThrows(IOException.class, () -> SettingsJson.read("{\"a\":".repeat(10) + "1" + "}".repeat(10)));
    }
}
