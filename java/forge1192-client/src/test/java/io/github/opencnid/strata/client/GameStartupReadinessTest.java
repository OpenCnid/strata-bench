package io.github.opencnid.strata.client;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class GameStartupReadinessTest {
    private final GameStartupReadiness ready = new GameStartupReadiness();
    private final Object level = new Object(), player = new Object(), connection = new Object();
    private final Object registry = new Object(), recipes = new Object();
    private void tags() { ready.tagsUpdated(connection, registry, registry); }
    private void recipes() { ready.recipesUpdated(connection, recipes, recipes); }
    private void render(boolean clear) { ready.rendered(level, player, connection, clear); }
    private void admit(boolean clear) { ready.admit(level, player, connection, clear); }
    private boolean qualified() { return ready.qualified(level, player, connection); }
    private void join() { tags(); recipes(); render(true); admit(true); assertTrue(qualified()); }

    @Test void worldRenderWithoutPacketsDoesNotQualify() {
        render(true); admit(true);
        assertFalse(qualified());
    }
    @Test void tagsWithoutRecipesDoNotQualify() {
        tags(); render(true); admit(true);
        assertFalse(qualified());
    }
    @Test void recipesWithoutTagsDoNotQualify() {
        recipes(); render(true); admit(true);
        assertFalse(qualified());
    }
    @Test void earlierWorldFrameCannotSurviveLaterSynchronization() {
        tags(); render(true); recipes(); admit(true);
        assertFalse(qualified());
        render(true); admit(true); assertTrue(qualified());
    }
    @Test void reversePacketOrderStillRequiresLaterWorldFrame() {
        recipes(); render(true); tags(); admit(true);
        assertFalse(qualified());
        render(true); admit(true); assertTrue(qualified());
    }
    @Test void sourceObjectMustBelongToCurrentListener() {
        ready.tagsUpdated(connection, registry, new Object());
        recipes(); render(true); admit(true); assertFalse(qualified());
        ready.connected(null);
        tags(); ready.recipesUpdated(connection, recipes, new Object());
        render(true); admit(true); assertFalse(qualified());
        ready.tagsUpdated(connection, null, null);
        ready.recipesUpdated(connection, null, null);
        render(true); admit(true); assertFalse(qualified());
    }
    @Test void screenOverlayAndDisabledRenderingCannotEstablishReadiness() {
        tags(); recipes(); render(false); admit(true); assertFalse(qualified());
        render(true); admit(false); assertFalse(qualified());
        render(false); admit(true); assertFalse(qualified());
        render(true); admit(true); assertTrue(qualified());
    }
    @Test void ordinaryMenusDoNotRevokeAnAlreadyQualifiedBody() {
        join(); render(false); admit(false);
        assertTrue(qualified());
        assertFalse(ready.ready(level, player, connection));
    }
    @Test void reconnectCannotReuseOldConnectionSynchronization() {
        join(); Object next = new Object();
        ready.rendered(level, player, next, true); ready.admit(level, player, next, true);
        assertFalse(ready.qualified(level, player, next));
        assertFalse(qualified());
        ready.tagsUpdated(next, registry, registry); ready.recipesUpdated(next, recipes, recipes);
        ready.rendered(level, player, next, true); ready.admit(level, player, next, true);
        assertTrue(ready.qualified(level, player, next));
    }
    @Test void disconnectEvenWithSameListenerReusedRequiresFreshPackets() {
        join(); ready.connected(null); assertFalse(qualified());
        render(true); admit(true); assertFalse(qualified());
    }
    @Test void replacedBodyNeedsItsOwnWorldFrameButCanRetainConnectionSynchronization() {
        join(); Object nextLevel = new Object(), nextPlayer = new Object();
        assertFalse(ready.qualified(nextLevel, player, connection));
        assertFalse(ready.qualified(level, nextPlayer, connection));
        ready.admit(nextLevel, nextPlayer, connection, true);
        assertFalse(ready.qualified(nextLevel, nextPlayer, connection));
        assertFalse(qualified());
        ready.rendered(nextLevel, nextPlayer, connection, true);
        ready.admit(nextLevel, nextPlayer, connection, true);
        assertTrue(ready.qualified(nextLevel, nextPlayer, connection));
    }
    @Test void furtherTagOrRecipeEventsInvalidateAdmissionUntilAnotherWorldFrame() {
        join(); tags(); assertFalse(qualified()); admit(true); assertFalse(qualified());
        render(true); admit(true); assertTrue(qualified());
        recipes(); assertFalse(qualified()); admit(true); assertFalse(qualified());
        render(true); admit(true); assertTrue(qualified());
    }
    @Test void partialBodyNeverQualifiesEvenAfterPacketsAndRender() {
        for (Object[] tuple : new Object[][]{{null,player,connection},{level,null,connection},
                {level,player,null},{null,null,null}}) {
            tags(); recipes();
            ready.rendered(tuple[0],tuple[1],tuple[2],true);
            ready.admit(tuple[0],tuple[1],tuple[2],true);
            assertFalse(ready.qualified(tuple[0],tuple[1],tuple[2]));
        }
    }
}
