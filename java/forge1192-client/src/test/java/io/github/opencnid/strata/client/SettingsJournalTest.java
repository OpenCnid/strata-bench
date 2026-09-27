package io.github.opencnid.strata.client;

import com.google.gson.JsonObject;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import static org.junit.jupiter.api.Assertions.*;

class SettingsJournalTest {
    @TempDir Path directory;
    private static final String GAME = "strata/NativeGameJournalFrame/1";

    @Test void gameCoordinatesReopenWithIdenticalHashChain() throws Exception {
        Path path = directory.resolve("game.jsonl");
        SettingsJournal journal = new SettingsJournal(path, "profile", 1048576, GAME);
        JsonObject payload = SettingsJson.readGame(
            "{\"kind\":\"reconfiguration_observation\",\"value\":{\"x\":-1.25,\"y\":64.0,\"z\":1.0E-4}}");
        journal.append(payload);
        byte[] original = Files.readAllBytes(path);
        SettingsJournal reopened = new SettingsJournal(path, "profile", 1048576, GAME);
        assertEquals(payload.toString(), reopened.entries().get(1).toString());
        assertArrayEquals(original, Files.readAllBytes(path));
        JsonObject next = new JsonObject();
        next.addProperty("kind", "end");
        reopened.append(next);
        assertEquals(3, new SettingsJournal(path, "profile", 1048576, GAME).revision());
    }

    @Test void settingsJournalStillRejectsFractionalNumbers() throws Exception {
        Path path = directory.resolve("settings.jsonl");
        SettingsJournal journal = new SettingsJournal(path, "profile", 1048576);
        journal.append(SettingsJson.readGame("{\"kind\":\"invalid\",\"revision\":1.5}"));
        assertThrows(IOException.class, () -> new SettingsJournal(path, "profile", 1048576));
    }

    @Test void gameFrameSequenceStillRequiresIntegerLexicalForm() throws Exception {
        for (String sequence : new String[] {"1.0", "1e0", "-1", "1.5"}) {
            Path path = directory.resolve("sequence-" + sequence + ".jsonl");
            new SettingsJournal(path, "profile", 1048576, GAME);
            Files.writeString(path, Files.readString(path).replace("\"seq\":1", "\"seq\":" + sequence));
            assertThrows(IOException.class, () -> new SettingsJournal(path, "profile", 1048576, GAME));
        }
    }

    @Test void changedCoordinateStillFailsHashVerification() throws Exception {
        Path path = directory.resolve("tampered.jsonl");
        SettingsJournal journal = new SettingsJournal(path, "profile", 1048576, GAME);
        journal.append(SettingsJson.readGame("{\"kind\":\"observation\",\"x\":-1.25}"));
        Files.writeString(path, Files.readString(path).replace("-1.25", "-2.25"));
        IOException failure = assertThrows(IOException.class,
            () -> new SettingsJournal(path, "profile", 1048576, GAME));
        assertEquals("SETTINGS_JOURNAL_HASH_MISMATCH", failure.getMessage());
    }
}
