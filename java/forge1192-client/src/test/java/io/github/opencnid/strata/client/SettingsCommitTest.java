package io.github.opencnid.strata.client;

import com.google.gson.JsonObject;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import static org.junit.jupiter.api.Assertions.*;

class SettingsCommitTest {
    static SettingsCommitDecision decision(SettingsStore.Snapshot head) throws Exception {
        return new SettingsCommitDecision(SettingsJson.read("""
            {"schema":"strata/NativeSettingsCommitDecision/1","transaction_id":"tx","plan_digest":"%s",
             "expected_revision":%d,"expected_digest":"%s","verification_ref":"cas:sha256:%s"}
            """.formatted("b".repeat(64), head.revision(), head.digest(), "c".repeat(64))));
    }
    @Test void commitIsDurableIdempotentAndDoesNotWriteOrResumeInput(@TempDir Path root) throws Exception {
        var helper = new SettingsStoreTest(); var f = helper.fixture(root);
        SettingsCommitDecision decision;
        try (var store = f.open()) {
            store.apply("tx", store.snapshot(), helper.change());
            decision = decision(store.verificationHead("tx"));
            int writes = f.runtime().writes;
            JsonObject result = store.commit(decision);
            assertTrue(result.get("committed").getAsBoolean());
            assertFalse(result.get("input_resumed").getAsBoolean());
            assertFalse(result.get("effects_verified_by_native").getAsBoolean());
            assertEquals(writes, f.runtime().writes);
            assertEquals(result, store.commit(decision));
            assertEquals(decision.expected.revision() + 1, store.snapshot().revision());
            assertTrue(store.inspect().get("active_transaction").isJsonNull());
            var changed = decision.value.deepCopy(); changed.addProperty("verification_ref", "cas:sha256:" + "d".repeat(64));
            assertThrows(IOException.class, () -> store.commit(new SettingsCommitDecision(changed)));
        }
        try (var reopened = f.open()) {
            assertEquals("committed", reopened.commitStatus("tx").get("phase").getAsString());
            assertEquals(decision.value, reopened.commitStatus("tx").getAsJsonObject("decision"));
            assertEquals("rolled_back", reopened.rollback("tx").phase());
            assertFalse(reopened.commitStatus("tx").get("committed").getAsBoolean());
            assertEquals(SettingsStoreTest.ORIGINAL, f.text());
            assertEquals("rolled_back", reopened.commit(decision).get("phase").getAsString());
        }
    }
    @Test void staleHeadAndConcurrentUnownedChangesNeverCommit(@TempDir Path root) throws Exception {
        var helper = new SettingsStoreTest(); var f = helper.fixture(root);
        try (var store = f.open()) {
            store.apply("tx", store.snapshot(), helper.change()); var head = store.verificationHead("tx");
            assertThrows(IOException.class, () -> store.commit(decision(new SettingsStore.Snapshot(head.revision() - 1, head.digest()))));
            Files.writeString(f.options(), f.text().replace("renderDistance:12", "renderDistance:13"));
            assertThrows(IOException.class, () -> store.commit(decision(head)));
            assertEquals("applied_pending_verification", store.status("tx").phase());
            assertThrows(IOException.class, () -> store.commitStatus("tx"));
        }
    }
    @Test void laterTransactionCannotBeOverwrittenByEarlierCommittedRollback(@TempDir Path root) throws Exception {
        var helper = new SettingsStoreTest(); var f = helper.fixture(root);
        try (var store = f.open()) {
            store.apply("tx", store.snapshot(), helper.change()); store.commit(decision(store.verificationHead("tx")));
            store.apply("later", store.snapshot(), Map.of(SettingsStoreTest.ID,
                new SettingsStore.Change(SettingsStoreTest.AFTER, "key.keyboard.e")));
            assertThrows(IOException.class, () -> store.rollback("tx"));
            assertEquals("key.keyboard.e", f.runtime().map.get(SettingsStoreTest.ID).value());
            assertEquals("applied_pending_verification", store.status("later").phase());
        }
    }
    @Test void validHashButWrongCommitRevisionIsRejectedOnReopen(@TempDir Path root) throws Exception {
        var helper = new SettingsStoreTest(); var f = helper.fixture(root); SettingsStore.Snapshot head;
        try (var store = f.open()) { store.apply("tx", store.snapshot(), helper.change()); head = store.verificationHead("tx"); }
        String identity = KeyOptions.sha256(f.profile().toAbsolutePath().normalize() + "\n" + SettingsStoreTest.FINGERPRINT);
        var journal = new SettingsJournal(f.journal().resolve("settings-journal.jsonl"), identity, 16777216);
        JsonObject event = new JsonObject(); event.addProperty("kind", "committed"); event.addProperty("id", "tx");
        event.add("decision", decision(new SettingsStore.Snapshot(head.revision() + 1, head.digest())).value);
        journal.append(event);
        assertEquals("SETTINGS_JOURNAL_INVALID", assertThrows(IOException.class, f::open).getMessage());
    }
    @Test void uncertainJournalWriteDoesNotProduceAnInMemoryCommit(@TempDir Path root) throws Exception {
        var helper = new SettingsStoreTest(); var f = helper.fixture(root);
        try (var store = f.open()) {
            store.apply("tx", store.snapshot(), helper.change()); var decision = decision(store.verificationHead("tx"));
            Files.writeString(f.journal().resolve("settings-journal.jsonl"), "partial", java.nio.file.StandardOpenOption.APPEND);
            assertThrows(IOException.class, () -> store.commit(decision));
            assertEquals("applied_pending_verification", store.status("tx").phase());
            assertThrows(IOException.class, () -> store.commitStatus("tx"));
        }
        assertThrows(IOException.class, f::open);
    }
    @Test void commitModeRequiresExplicitEffectsAndRepairOwnership() {
        var properties = new java.util.Properties();
        properties.setProperty(NativeSettingsEffects.COMMIT_PROPERTY, "true");
        assertThrows(IllegalStateException.class, () -> NativeSettingsEffects.validateModes(properties, Map.of()));
        properties.setProperty(NativeSettingsEffects.REPAIR_PROPERTY, "true");
        assertThrows(IllegalStateException.class, () -> NativeSettingsEffects.validateModes(properties, Map.of()));
        properties.setProperty(NativeSettingsEffects.PROPERTY, "true");
        properties.setProperty("strata.gameBridgeDirectory", "private");
        assertDoesNotThrow(() -> NativeSettingsEffects.validateModes(properties, Map.of()));
        properties.setProperty(NativeSettingsEffects.COMMIT_PROPERTY, "yes");
        assertThrows(IllegalStateException.class, () -> NativeSettingsEffects.validateModes(properties, Map.of()));
    }
}
