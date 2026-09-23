package io.github.opencnid.strata.telemetry;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import java.io.IOException;
import java.lang.management.ManagementFactory;
import java.nio.file.Path;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.Container;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.crafting.Ingredient;
import net.minecraft.world.item.crafting.Recipe;
import net.minecraft.world.item.crafting.ShapedRecipe;
import net.minecraftforge.common.MinecraftForge;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.fml.DistExecutor;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.event.CommandEvent;
import net.minecraftforge.event.entity.player.PlayerEvent;
import net.minecraftforge.event.server.ServerStartedEvent;
import net.minecraftforge.event.server.ServerStoppedEvent;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.fml.loading.FMLPaths;
import net.minecraftforge.fml.ModList;
import net.minecraft.world.level.storage.LevelResource;
import net.minecraftforge.registries.ForgeRegistries;

/** No channels, commands, packets, world setters, or fixture definitions. */
@Mod("strata_telemetry")
public final class StrataTelemetry {
    private EventSpool spool;
    private TelemetryConfig config;
    private ServerClock clock;
    private long ticks, lastSample, lastSampleTick, tickStart, workNanos;
    private final Map<UUID, Long> avatarTicks = new HashMap<>();

    public StrataTelemetry() {
        DistExecutor.safeRunWhenOn(Dist.CLIENT, () -> ClientConfigExport::install);
        MinecraftForge.EVENT_BUS.addListener(this::started);
        MinecraftForge.EVENT_BUS.addListener(this::tick);
        MinecraftForge.EVENT_BUS.addListener(this::playerTick);
        MinecraftForge.EVENT_BUS.addListener(this::crafted);
        MinecraftForge.EVENT_BUS.addListener(this::stopped);
        MinecraftForge.EVENT_BUS.addListener(this::command);
    }

    private void command(CommandEvent event) {
        if(event.getParseResults().getContext().getSource().getServer().isDedicatedServer()) {
            SetupCapture.COMMAND_EVENTS.incrementAndGet();
            SetupHistory.command(event.getParseResults().getContext().getSource(),
                event.getParseResults().getReader().getString().equals("stop")
                && !event.getParseResults().getReader().canRead()
                && event.getParseResults().getExceptions().isEmpty());
        }
    }

    private void started(ServerStartedEvent event) {
        // Server telemetry remains dedicated-only; client diagnostics need their explicit private plan.
        if (!event.getServer().isDedicatedServer()) return;
        String path = System.getenv("STRATA_TELEMETRY_CONFIG");
        if (path == null) return;
        clock = new ServerClock();
        try {
            config = TelemetryConfig.read(Path.of(path), FMLPaths.GAMEDIR.get());
            spool = new EventSpool(config);
            SetupHistory.activate();
            JsonObject boot = new JsonObject();
            boot.addProperty("module", "strata-forge1192-telemetry/0.3.11");
            boot.addProperty("clock_policy", ServerClock.POLICY);
            boot.addProperty("minecraft", "1.19.2");
            boot.addProperty("forge", "43.4.23");
            boot.addProperty("scoring_provenance_supported", false);
            boot.addProperty("recipe_count", event.getServer().getRecipeManager().getRecipes().size());
            JsonArray queries = new JsonArray(); config.configQueries().forEach(q -> queries.add(q.json()));
            boot.add("config_queries", queries);
            boot.addProperty("craft_capture_policy",CraftCapture.POLICY);
            boot.add("craft_capture_support",CraftCapture.support());
            boot.add("launch_identity", LaunchIdentity.observe(FMLPaths.GAMEDIR.get(),
                event.getServer().getWorldPath(LevelResource.ROOT),
                ModList.get().getModFileById("strata_telemetry").getFile().getFilePath(),
                event.getServer().usesAuthentication(), event.getServer().getPort()));
            boot.addProperty("setup_capture_policy",SetupCapture.POLICY);
            boot.add("setup_capture_support",SetupCapture.support());
            boot.add("setup_history_support",SetupHistory.support());
            boot.addProperty("telemetry_transport", config.broker() == null ? "private-file/1" : "windows-owned-pipe/1");
            emit("server_started", "strata/ServerStarted/12", boot, new JsonArray());
            for (String id : config.recipeIds()) recipe(event.getServer(), id);
            CraftCapture.activate(this::emit);
            lastSample = System.nanoTime();
        } catch (IOException error) { throw failed(error); }
    }

    private void recipe(MinecraftServer server, String id) {
        JsonObject value = new JsonObject();
        value.addProperty("recipe_id", id);
        Recipe<?> recipe = server.getRecipeManager().byKey(ResourceLocation.tryParse(id)).orElse(null);
        value.addProperty("present", recipe != null);
        if (recipe != null) {
            value.addProperty("serializer", String.valueOf(ForgeRegistries.RECIPE_SERIALIZERS.getKey(recipe.getSerializer())));
            value.add("output", stack(recipe.getResultItem()));
            JsonArray ingredients = new JsonArray();
            for (Ingredient ingredient : recipe.getIngredients()) {
                JsonArray candidates = new JsonArray();
                ItemStack[] items = ingredient.getItems();
                if (items.length > 512) throw failed(new IOException("TELEMETRY_RECIPE_TOO_LARGE"));
                for (ItemStack item : items) candidates.add(stack(item));
                ingredients.add(candidates);
            }
            value.add("ingredients", ingredients);
            if (recipe instanceof ShapedRecipe shaped) {
                value.addProperty("width", shaped.getWidth());
                value.addProperty("height", shaped.getHeight());
            }
        }
        emit("recipe_snapshot", "strata/RecipeSnapshot/1", value, new JsonArray());
    }

    private void tick(TickEvent.ServerTickEvent event) {
        if (spool == null) return;
        try { spool.healthy(); } catch (IOException error) { throw failed(error); }
        if (event.phase == TickEvent.Phase.START) {
            clock.startTick();
            tickStart = System.nanoTime();
            return;
        }
        ticks++;
        // All ServerStarted listeners have returned. This is still a point observation,
        // not a transaction across watcher threads or proof of cached consumer effects.
        if (ticks == 1) {
            emit("setup_snapshot", "strata/NativeSetupSnapshot/1",
                SetupCapture.capture(event.getServer(),null,null,"startup"),new JsonArray());
            for (ConfigQuery query : config.configQueries()) {
                emit("config_snapshot", "strata/ConfigSnapshot/1", ConfigSnapshot.capture(query), new JsonArray());
            }
        }
        long now = System.nanoTime();
        if (tickStart != 0) workNanos += now - tickStart;
        clock.endTick();
        MinecraftServer server = event.getServer();
        for (ServerPlayer player : server.getPlayerList().getPlayers()) {
            avatarTicks.merge(player.getUUID(), 1L, Long::sum);
        }
        if (now - lastSample < 1000000000L) return;
        JsonObject sample = new JsonObject();
        sample.addProperty("interval_wall_ns", now - lastSample);
        sample.addProperty("interval_server_ticks", ticks - lastSampleTick);
        sample.addProperty("observed_tick_work_ns", workNanos);
        sample.addProperty("server_average_mspt", server.getAverageTickTime());
        sample.addProperty("heap_used_bytes", ManagementFactory.getMemoryMXBean().getHeapMemoryUsage().getUsed());
        sample.addProperty("gc_count", ManagementFactory.getGarbageCollectorMXBeans().stream().mapToLong(b -> Math.max(0, b.getCollectionCount())).sum());
        sample.addProperty("gc_time_ms", ManagementFactory.getGarbageCollectorMXBeans().stream().mapToLong(b -> Math.max(0, b.getCollectionTime())).sum());
        sample.addProperty("durable_event_seq_before_sample", spool.durableSeq());
        JsonObject exposures = new JsonObject();
        avatarTicks.entrySet().stream().sorted(Map.Entry.comparingByKey()).forEach(e -> exposures.addProperty(e.getKey().toString(), e.getValue()));
        sample.add("avatar_ticks_since_boot", exposures);
        emit("server_health", "strata/ServerHealth/1", sample, new JsonArray());
        lastSample = now;
        lastSampleTick = ticks;
        workNanos = 0;
    }

    private void playerTick(TickEvent.PlayerTickEvent event) {
        if (spool != null && event.phase == TickEvent.Phase.END && event.player instanceof ServerPlayer player) {
            clock.avatarTick(player.getUUID());
        }
    }

    private void crafted(PlayerEvent.ItemCraftedEvent event) {
        if (spool == null || !(event.getEntity() instanceof ServerPlayer player)) return;
        CraftCapture.callback(player,event.getCrafting(),event.getInventory());
        JsonObject raw = new JsonObject();
        raw.addProperty("score_eligible", false);
        raw.addProperty("reason", "consumption_team_recipe_and_setup_provenance_unverified");
        raw.add("output_at_callback", stack(event.getCrafting()));
        JsonArray matrix = new JsonArray();
        Container inventory = event.getInventory();
        if (inventory.getContainerSize() > 128) throw failed(new IOException("TELEMETRY_CONTAINER_TOO_LARGE"));
        for (int i = 0; i < inventory.getContainerSize(); i++) matrix.add(stack(inventory.getItem(i)));
        raw.add("matrix_at_callback", matrix);
        JsonArray actors = new JsonArray();
        actors.add(player.getUUID().toString());
        emit("craft_callback", "strata/RawCraftCallback/1", raw, actors);
    }

    private static JsonObject stack(ItemStack item) {
        JsonObject value = new JsonObject();
        value.addProperty("item_id", String.valueOf(ForgeRegistries.ITEMS.getKey(item.getItem())));
        value.addProperty("count", item.getCount());
        // NBT omitted intentionally; no false claim that these are complete stack identities.
        value.addProperty("has_nbt", item.hasTag());
        return value;
    }

    private void emit(String kind, String schema, JsonObject payload, JsonArray actors) {
        try {
            if (kind.equals("setup_snapshot")) {
                var transaction = payload.get("transaction_id");
                spool.publish(ticks, "setup_history", "strata/NativeSetupHistory/4",
                    SetupHistory.capture(payload.get("phase").getAsString(),
                        transaction.isJsonNull() ? null : transaction.getAsString()), actors);
            }
            spool.publish(ticks, kind, schema, payload, actors);
        }
        catch (IOException error) { throw failed(error); }
    }

    private void stopped(ServerStoppedEvent event) {
        if (spool == null) return;
        try {
            CraftCapture.close();
            emit("server_clock", "strata/ServerClock/1", clock.stop(), new JsonArray());
            emit("setup_history", "strata/NativeSetupHistory/4", SetupHistory.close(), new JsonArray());
            emit("server_stopped", "strata/ServerStopped/1", new JsonObject(), new JsonArray());
        } finally {
            try { spool.close(); }
            catch (IOException error) { throw failed(error); }
            finally { spool = null; }
        }
    }

    private static IllegalStateException failed(IOException error) {
        return new IllegalStateException("STRATA_TELEMETRY_FAILED: private evidence incomplete", error);
    }
}
