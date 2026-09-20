package io.github.opencnid.strata.client;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.channels.FileChannel;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;
import java.util.function.BooleanSupplier;
import net.minecraft.client.Minecraft;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.SlabBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.SlabType;
import net.minecraftforge.client.loading.ClientModLoader;
import net.minecraftforge.common.MinecraftForge;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.fml.ModList;

/** Opt-in operator-only native shape checks, without a world join, controls or game mutations. */
final class ClientCollisionProbe {
    private static boolean attempted;
    private static final GameObservedMap.Position POSITION = new GameObservedMap.Position(0, 64, 0);
    static void install() { MinecraftForge.EVENT_BUS.addListener(ClientCollisionProbe::tick); }
    private static NativeCollisionView view(String id, BlockState state, long captured, long now) {
        return new NativeCollisionView(Map.of(POSITION,
            new GameObservedMap.Known<>(new GameObservedMap.Cell<>(id, state), captured, 1)), now);
    }
    private static void check(JsonArray checks, String name, BooleanSupplier operation) {
        var item = new JsonObject(); item.addProperty("case", name);
        try { item.addProperty("result", operation.getAsBoolean() ? "pass" : "fail"); }
        catch (RuntimeException error) { item.addProperty("result", "fail"); item.addProperty("exception_type", error.getClass().getName()); }
        checks.add(item);
    }
    private static JsonArray checks() {
        var checks = new JsonArray();
        check(checks, "air_empty", () -> view("minecraft:air", Blocks.AIR.defaultBlockState(), 0, 0).at(POSITION).boxes().isEmpty());
        check(checks, "stone_full", () -> view("minecraft:stone", Blocks.STONE.defaultBlockState(), 0, 0).at(POSITION).boxes()
            .equals(java.util.List.of(new GameRoute.Box(0, 0, 0, 1, 1, 1))));
        for (SlabType type : SlabType.values()) check(checks, "slab_" + type.getSerializedName(), () -> {
            var cell = view("minecraft:stone_slab", Blocks.STONE_SLAB.defaultBlockState().setValue(SlabBlock.TYPE, type), 0, 0).at(POSITION);
            return cell != null && cell.boxes().equals(java.util.List.of(new GameRoute.Box(0, type == SlabType.TOP ? .5 : 0, 0,
                1, type == SlabType.BOTTOM ? .5 : 1, 1)));
        });
        check(checks, "waterlogged_rejected", () -> view("minecraft:stone_slab",
            Blocks.STONE_SLAB.defaultBlockState().setValue(SlabBlock.WATERLOGGED, true), 0, 0).at(POSITION) == null);
        check(checks, "grass_at_age_limit", () -> view("minecraft:grass_block", Blocks.GRASS_BLOCK.defaultBlockState(), 0, 30_000).at(POSITION) != null);
        check(checks, "old_rejected", () -> view("minecraft:stone", Blocks.STONE.defaultBlockState(), 0, 30_001).at(POSITION) == null);
        check(checks, "future_rejected", () -> view("minecraft:stone", Blocks.STONE.defaultBlockState(), 2, 1).at(POSITION) == null);
        check(checks, "wrong_implementation_rejected", () -> view("minecraft:stone", Blocks.CACTUS.defaultBlockState(), 0, 0).at(POSITION) == null);
        check(checks, "unknown_id_rejected", () -> view("mod:unknown", Blocks.STONE.defaultBlockState(), 0, 0).at(POSITION) == null);
        check(checks, "missing_neighbor_rejected", () -> view("minecraft:stone", Blocks.STONE.defaultBlockState(), 0, 0)
            .at(new GameObservedMap.Position(1, 64, 0)) == null);
        check(checks, "native_shapes_level_route", () -> {
            var cells = new HashMap<GameObservedMap.Position, GameObservedMap.Known<BlockState>>();
            for (int x = 0; x <= 3; x++) for (int y = 63; y <= 65; y++) cells.put(new GameObservedMap.Position(x, y, 0),
                new GameObservedMap.Known<>(new GameObservedMap.Cell<>(y == 63 ? "minecraft:stone" : "minecraft:air",
                    (y == 63 ? Blocks.STONE : Blocks.AIR).defaultBlockState()), 0, 1));
            // This fixture tests actual shape conversion, not game motion or planning latency.
            var planner = new GameRoute(new NativeCollisionView(cells, 0), .6, 1.8, () -> 0);
            try {
                var target = new GameVisibility.Point(2.5, 64, .5);
                var route = planner.plan(new GameVisibility.Point(.5, 64, .5), target, .1);
                return !route.isEmpty() && route.get(route.size() - 1).equals(target);
            } catch (IOException error) { return false; }
        });
        return checks;
    }
    private static void tick(TickEvent.ClientTickEvent event) {
        if (attempted || event.phase != TickEvent.Phase.END || ClientModLoader.isLoading()) return;
        String directory = System.getProperty("strata.collisionProbeDirectory");
        if (directory == null) { attempted = true; return; }
        Minecraft client = Minecraft.getInstance();
        if (client.options == null) return;
        attempted = true;
        try {
            Path root = Path.of(directory); SettingsFiles.safeExisting(root);
            if (!Files.isDirectory(root) || root.startsWith(client.gameDirectory.toPath().toAbsolutePath().normalize())) {
                throw new IOException("GAME_PRIVATE_OUTPUT_REQUIRED");
            }
            var result = new JsonObject(); result.addProperty("schema", "StrataNativeCollisionProbe/1");
            result.addProperty("operator_development_only", true); result.addProperty("world_motion_tested", false);
            result.addProperty("native_collision_policy", NativeCollisionView.POLICY); result.addProperty("route_policy", GameRoute.POLICY);
            result.addProperty("recorded_at", java.time.Instant.now().toString());
            result.addProperty("client_jar_sha256", ArtifactFiles.hash(ModList.get().getModFileById("strata_client").getFile().getFilePath()));
            JsonArray checks = checks(); result.add("checks", checks);
            result.addProperty("result", java.util.stream.StreamSupport.stream(checks.spliterator(), false)
                .allMatch(item -> "pass".equals(item.getAsJsonObject().get("result").getAsString())) ? "pass" : "fail");
            byte[] bytes = (result + "\n").getBytes(StandardCharsets.UTF_8);
            if (bytes.length > 16384) throw new IOException("GAME_PROBE_BOUNDS");
            Path output = root.resolve("collision-" + UUID.randomUUID() + ".json");
            try (FileChannel file = FileChannel.open(output, StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE)) {
                ByteBuffer buffer = ByteBuffer.wrap(bytes); while (buffer.hasRemaining()) file.write(buffer); file.force(true);
            }
        } catch (IOException error) { throw new IllegalStateException("STRATA_COLLISION_PROBE_FAILED", error); }
    }
}
