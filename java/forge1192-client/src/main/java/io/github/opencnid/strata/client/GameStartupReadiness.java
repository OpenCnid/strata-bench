package io.github.opencnid.strata.client;

/** Client-thread lifecycle barrier; readiness never comes from a render alone. */
final class GameStartupReadiness {
    private Object connection, renderedLevel, renderedPlayer, admittedLevel, admittedPlayer;
    private boolean tags, recipes;

    void connected(Object connection) {
        if (this.connection == connection) return;
        this.connection = connection;
        tags = recipes = false;
        invalidateRender();
    }

    void tagsUpdated(Object connection, Object expectedRegistry, Object eventRegistry) {
        connected(connection);
        if (connection == null || expectedRegistry == null || expectedRegistry != eventRegistry) return;
        tags = true;
        invalidateRender();
    }

    void recipesUpdated(Object connection, Object expectedManager, Object eventManager) {
        connected(connection);
        if (connection == null || expectedManager == null || expectedManager != eventManager) return;
        recipes = true;
        invalidateRender();
    }

    void rendered(Object level, Object player, Object connection, boolean unobstructed) {
        connected(connection);
        boolean complete = tags && recipes && unobstructed && level != null && player != null;
        renderedLevel = complete ? level : null;
        renderedPlayer = complete ? player : null;
    }

    boolean ready(Object level, Object player, Object connection) {
        return tags && recipes && level != null && player != null && connection != null
            && level == renderedLevel && player == renderedPlayer && connection == this.connection;
    }

    void admit(Object level, Object player, Object connection, boolean unobstructed) {
        connected(connection);
        if (level != admittedLevel || player != admittedPlayer) {
            admittedLevel = admittedPlayer = null;
        }
        if (unobstructed && ready(level, player, connection)) {
            admittedLevel = level;
            admittedPlayer = player;
        }
    }

    boolean qualified(Object level, Object player, Object connection) {
        return tags && recipes && level != null && player != null && connection != null
            && level == admittedLevel && player == admittedPlayer && connection == this.connection;
    }

    private void invalidateRender() {
        renderedLevel = renderedPlayer = admittedLevel = admittedPlayer = null;
    }
}
