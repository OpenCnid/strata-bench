package io.github.opencnid.strata.client;

import java.util.Map;
import net.minecraft.core.BlockPos;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.block.AirBlock;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.GrassBlock;
import net.minecraft.world.level.block.SlabBlock;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.material.FluidState;
import net.minecraft.world.phys.shapes.CollisionContext;

/** No Level, Entity, socket or block-entity access. Only copied, delivered BlockStates. */
final class NativeCollisionView implements BlockGetter, GameRoute.View {
    static final String POLICY = "delivered-static-vanilla-shapes-age30s/1";
    private static final Map<String, Class<? extends Block>> IMPLEMENTATIONS = Map.ofEntries(
        Map.entry("minecraft:air", AirBlock.class), Map.entry("minecraft:cave_air", AirBlock.class),
        Map.entry("minecraft:void_air", AirBlock.class), Map.entry("minecraft:stone", Block.class),
        Map.entry("minecraft:cobblestone", Block.class), Map.entry("minecraft:dirt", Block.class),
        Map.entry("minecraft:coarse_dirt", Block.class), Map.entry("minecraft:grass_block", GrassBlock.class),
        Map.entry("minecraft:oak_planks", Block.class), Map.entry("minecraft:spruce_planks", Block.class),
        Map.entry("minecraft:stone_slab", SlabBlock.class), Map.entry("minecraft:oak_slab", SlabBlock.class));
    private final Map<GameObservedMap.Position, GameObservedMap.Known<BlockState>> cells;
    private final long now;
    private static final class Unavailable extends RuntimeException {}

    NativeCollisionView(Map<GameObservedMap.Position, GameObservedMap.Known<BlockState>> cells, long now) {
        if (cells.size() > GameObservedMap.MAX_DELIVERED || now < 0) throw new IllegalArgumentException("NAVIGATION_MAP_INVALID");
        this.cells = Map.copyOf(cells); this.now = now;
    }
    public BlockState getBlockState(BlockPos position) {
        var known = cells.get(new GameObservedMap.Position(position.getX(), position.getY(), position.getZ()));
        if (known == null || known.captured() < 0 || known.captured() > now || now - known.captured() > 30_000) throw new Unavailable();
        BlockState state = known.cell().state();
        Class<? extends Block> expected = IMPLEMENTATIONS.get(known.cell().id());
        if (state == null || expected == null || state.getBlock().getClass() != expected
                || Float.compare(state.getBlock().getFriction(), .6f) != 0
                || Float.compare(state.getBlock().getSpeedFactor(), 1f) != 0
                || Float.compare(state.getBlock().getJumpFactor(), 1f) != 0) throw new Unavailable();
        return state;
    }
    public FluidState getFluidState(BlockPos position) { return getBlockState(position).getFluidState(); }
    public BlockEntity getBlockEntity(BlockPos position) { throw new Unavailable(); }
    public int getHeight() { throw new Unavailable(); }
    public int getMinBuildHeight() { throw new Unavailable(); }

    public GameRoute.Cell at(GameObservedMap.Position position) {
        BlockPos nativePosition = new BlockPos(position.x(), position.y(), position.z());
        try {
            BlockState state = getBlockState(nativePosition);
            if (!state.getFluidState().isEmpty()) return null; // No swimming, waterlogged or fluid-dependent route.
            // These exact classes use state-only geometry. Entity-sensitive/custom classes are not called.
            var shape = state.getCollisionShape(this, nativePosition, CollisionContext.empty());
            return new GameRoute.Cell(shape.toAabbs().stream().map(box ->
                new GameRoute.Box(box.minX, box.minY, box.minZ, box.maxX, box.maxY, box.maxZ)).toList());
        } catch (Unavailable | IllegalArgumentException unavailable) {
            return null;
        }
    }
}
