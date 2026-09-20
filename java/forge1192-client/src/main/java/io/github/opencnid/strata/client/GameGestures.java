package io.github.opencnid.strata.client;

import com.google.gson.JsonObject;
import java.io.IOException;
import java.util.function.LongSupplier;

/** Bounded gesture sequencing; every callback that can emit input is journaled by the lane. */
final class GameGestures {
    interface UsePort {
        void validate() throws IOException;
        void start(String hand, boolean hold) throws IOException;
        boolean stillUsing(String hand) throws IOException;
        void hold() throws IOException;
    }
    interface EntityPort {
        GameVisibility.Point resolve(String id, String type, boolean attack) throws IOException;
        void look(GameVisibility.Point target) throws IOException;
        void trigger(String id, String type, boolean attack) throws IOException;
    }
    static GameActionLane.Motor use(UsePort port, String hand, long holdMs, LongSupplier clock,
                                   GameActionLane.Emitter emit) throws IOException {
        port.validate();
        long until = clock.getAsLong() + holdMs;
        emit.invoke(() -> port.start(hand, holdMs > 0));
        return next -> {
            port.validate();
            // No implicit second use if an item finishes, is rejected, or changes hands.
            if (holdMs == 0 || clock.getAsLong() >= until || !port.stillUsing(hand)) return true;
            next.invoke(port::hold); // One charged local event per active held-input tick.
            return false;
        };
    }
    static GameActionLane.Motor entity(EntityPort port, JsonObject snapshot, String id, boolean attack,
                                      GameActionLane.Emitter emit) throws IOException {
        String type = deliveredEntity(snapshot, id);
        GameVisibility.Point target = port.resolve(id, type, attack);
        emit.invoke(() -> port.look(target));
        port.resolve(id, type, attack); // Turning/mod callbacks must not make a stale target authoritative.
        emit.invoke(() -> port.trigger(id, type, attack));
        return ignored -> true;
    }
    static String deliveredEntity(JsonObject snapshot, String id) throws IOException {
        String type = null;
        for (var value : snapshot.getAsJsonObject("state").getAsJsonArray("nearby_entities")) {
            JsonObject entity = value.getAsJsonObject();
            if (id.equals(SettingsJson.string(entity, "id"))) {
                if (type != null) throw new IOException("GAME_ENTITY_AMBIGUOUS");
                type = SettingsJson.string(entity, "type");
            }
        }
        if (type == null) throw new IOException("TARGET_NOT_OBSERVED");
        return type;
    }
    static String entityId(int networkId, String uuid, String salt) {
        return networkId + ":" + KeyOptions.sha256(salt + "\n" + uuid);
    }
    static String chat(String text) throws IOException {
        if (text.stripLeading().startsWith("/")) throw new IOException("CHAT_COMMAND_FORBIDDEN");
        // Minecraft's network string bound is UTF-16 units, not Unicode code points.
        if (text.isBlank() || text.length() > 256) throw new IOException("GAME_CHAT_INVALID");
        for (int i = 0; i < text.length(); i++) {
            char c = text.charAt(i);
            if (Character.isISOControl(c) || c == '\u00a7') throw new IOException("GAME_CHAT_INVALID");
            if (Character.isHighSurrogate(c)) {
                if (++i == text.length() || !Character.isLowSurrogate(text.charAt(i))) throw new IOException("GAME_CHAT_INVALID");
            } else if (Character.isLowSurrogate(c)) throw new IOException("GAME_CHAT_INVALID");
        }
        return text;
    }
}
