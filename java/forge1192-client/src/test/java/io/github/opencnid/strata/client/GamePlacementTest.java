package io.github.opencnid.strata.client;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import java.io.IOException;
import java.nio.file.Path;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import static org.junit.jupiter.api.Assertions.*;

class GamePlacementTest {
    JsonObject action() throws IOException {
        return SettingsJson.readGame("""
            {"kind":"place","support":{"x":-1.2,"y":64,"z":0},"face":{"x":0,"y":1,"z":0},"expected_item_id":"minecraft:stone"}
            """);
    }
    JsonObject snapshot(String destination) throws IOException {
        var snapshot = SettingsJson.readGame("""
            {"state":{"nearby_blocks":[{"position":{"x":-2,"y":64,"z":0},"block_id":"minecraft:stone"},
             {"position":{"x":-2,"y":65,"z":0},"block_id":"minecraft:air"}]}}
            """);
        snapshot.getAsJsonObject("state").getAsJsonArray("nearby_blocks").get(1).getAsJsonObject().addProperty("block_id", destination);
        return snapshot;
    }
    @Test void placementUsesDeliveredSupportAndAdjacentAirWithNegativeCoordinateFlooring() throws Exception {
        var target = GamePlacement.observed(snapshot("minecraft:air"), action());
        assertEquals(-2, target.x()); assertEquals(64, target.y()); assertEquals(1, target.dy());
        assertEquals("minecraft:stone", target.supportId()); assertEquals("minecraft:air", target.destinationId());
    }
    @Test void unseenOccupiedOrAmbiguousDestinationAndAirSupportReject() throws Exception {
        for (String blocked : new String[]{"minecraft:stone", "pack:unknown_air_like_block"}) {
            assertThrows(IOException.class, () -> GamePlacement.observed(snapshot(blocked), action()));
        }
        for (int missing : new int[]{0, 1}) {
            var snapshot = snapshot("minecraft:air"); snapshot.getAsJsonObject("state").getAsJsonArray("nearby_blocks").remove(missing);
            assertThrows(IOException.class, () -> GamePlacement.observed(snapshot, action()));
        }
        var snapshot = snapshot("minecraft:air"); JsonArray blocks = snapshot.getAsJsonObject("state").getAsJsonArray("nearby_blocks");
        blocks.add(blocks.get(0).deepCopy());
        assertThrows(IOException.class, () -> GamePlacement.observed(snapshot, action()));
        blocks.remove(2); blocks.get(0).getAsJsonObject().addProperty("block_id", "minecraft:air");
        assertThrows(IOException.class, () -> GamePlacement.observed(snapshot, action()));
    }
    @Test void allAxisFacesParseButDiagonalsFractionsAndUnknownFieldsReject(@TempDir Path root) throws Exception {
        var f = new GameActionLaneTest.Fixture(root, 100); var batch = f.batch(1, "place", 1);
        var action = action(); batch.add("action", action);
        for (String axis : new String[]{"x", "y", "z"}) for (int sign : new int[]{-1, 1}) {
            var face = action.getAsJsonObject("face"); face.addProperty("x", 0); face.addProperty("y", 0); face.addProperty("z", 0);
            face.addProperty(axis, sign); new GameBatch(batch);
        }
        var face = action.getAsJsonObject("face"); face.addProperty("z", 0); face.addProperty("x", .5); face.addProperty("y", .5);
        assertThrows(IOException.class, () -> new GameBatch(batch));
        face.addProperty("x", 1); face.addProperty("y", 1); assertThrows(IOException.class, () -> new GameBatch(batch));
        face.addProperty("y", 0); action.addProperty("give_item", true); assertThrows(IOException.class, () -> new GameBatch(batch));
    }
    @Test void equipmentEnvelopePreservesExactSlotItemAndDestinationBounds(@TempDir Path root) throws Exception {
        var f = new GameActionLaneTest.Fixture(root, 100); var batch = f.batch(1, "equip", 1);
        var action = SettingsJson.readGame("{\"kind\":\"equip\",\"inventory_slot\":10,\"expected_item_id\":\"minecraft:stone\",\"destination\":\"hand\"}");
        batch.add("action", action); new GameBatch(batch);
        action.addProperty("inventory_slot", 46); assertThrows(IOException.class, () -> new GameBatch(batch));
        action.addProperty("inventory_slot", 10.5); assertThrows(IOException.class, () -> new GameBatch(batch));
        action.addProperty("inventory_slot", 10); action.addProperty("destination", "auto_best"); assertThrows(IOException.class, () -> new GameBatch(batch));
        action.addProperty("destination", "head"); action.addProperty("expected_item_id", "unqualified"); assertThrows(IOException.class, () -> new GameBatch(batch));
    }
}
