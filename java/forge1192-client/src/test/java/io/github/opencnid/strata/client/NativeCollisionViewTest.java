package io.github.opencnid.strata.client;

import java.util.HashMap;
import java.util.Map;
import net.minecraft.core.BlockPos;
import net.minecraft.world.level.block.state.BlockState;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

/** Input-boundary tests only. Actual shape checks run in ClientCollisionProbe under Forge. */
class NativeCollisionViewTest {
    final GameObservedMap.Position position = new GameObservedMap.Position(0, 64, 0);
    NativeCollisionView view(String id, BlockState state, long captured, long now) {
        return new NativeCollisionView(Map.of(position,
            new GameObservedMap.Known<>(new GameObservedMap.Cell<>(id, state), captured, 1)), now);
    }
    @Test void absentNullStaleAndFutureCellsCannotResolveGeometry() {
        assertNull(view("minecraft:stone", null, 0, 30_001).at(position));
        assertNull(view("minecraft:stone", null, 2, 1).at(position));
        assertNull(view("minecraft:stone", null, 0, 0).at(position));
        assertNull(view("mod:unknown", null, 0, 0).at(position));
        assertNull(view("minecraft:stone", null, 0, 0).at(new GameObservedMap.Position(1, 64, 0)));
    }
    @Test void copiedMapCannotAcquireNewKnowledgeAndPrivateDependenciesReject() {
        var map = new HashMap<GameObservedMap.Position, GameObservedMap.Known<BlockState>>();
        var nativeView = new NativeCollisionView(map, 0);
        map.put(position, new GameObservedMap.Known<>(new GameObservedMap.Cell<>("minecraft:stone", null), 0, 1));
        assertNull(nativeView.at(position));
        assertThrows(RuntimeException.class, () -> nativeView.getBlockState(new BlockPos(0, 64, 0)));
        assertThrows(RuntimeException.class, () -> nativeView.getBlockEntity(new BlockPos(0, 64, 0)));
        assertThrows(RuntimeException.class, nativeView::getHeight);
        assertThrows(RuntimeException.class, nativeView::getMinBuildHeight);
    }
    @Test void oversizedMapAndInvalidClockRejectBeforeAnyShapeRead() {
        assertThrows(IllegalArgumentException.class, () -> new NativeCollisionView(Map.of(), -1));
        var map = new HashMap<GameObservedMap.Position, GameObservedMap.Known<BlockState>>();
        for (int x = 0; x <= GameObservedMap.MAX_DELIVERED; x++) map.put(new GameObservedMap.Position(x, 64, 0),
            new GameObservedMap.Known<>(new GameObservedMap.Cell<>("minecraft:stone", null), 0, 1));
        assertThrows(IllegalArgumentException.class, () -> new NativeCollisionView(map, 0));
    }
}
