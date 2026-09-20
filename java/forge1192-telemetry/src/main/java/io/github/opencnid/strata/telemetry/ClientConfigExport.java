package io.github.opencnid.strata.telemetry;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.channels.FileChannel;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.UUID;
import net.minecraft.client.Minecraft;
import net.minecraftforge.client.loading.ClientModLoader;
import net.minecraftforge.common.MinecraftForge;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.fml.loading.FMLPaths;

/** Explicit private one-shot export; no commands, channels, input, reload or config getters. */
final class ClientConfigExport {
    private static ClientConfigPlan plan;
    private static boolean attempted;
    private static final String SESSION = UUID.randomUUID().toString();

    static void install() {
        String path = System.getProperty("strata.clientConfigProbePlan");
        if (path == null) return;
        try { plan = ClientConfigPlan.read(Path.of(path), FMLPaths.GAMEDIR.get()); }
        catch (IOException error) { throw new IllegalStateException("STRATA_CLIENT_CONFIG_PLAN_FAILED", error); }
        MinecraftForge.EVENT_BUS.addListener(ClientConfigExport::tick);
    }

    private static void tick(TickEvent.ClientTickEvent event) {
        if (attempted || event.phase != TickEvent.Phase.END || ClientModLoader.isLoading()) return;
        Minecraft client = Minecraft.getInstance();
        if (client.level == null || client.player == null) return;
        attempted = true;
        try {
            plan.unchanged();
            JsonObject value = new JsonObject();
            value.addProperty("schema", "strata/ClientConfigSnapshot/1");
            value.addProperty("module", "strata-forge1192-telemetry/0.3.2");
            value.addProperty("campaign_id", plan.config().campaignId());
            value.addProperty("epoch", plan.config().epoch());
            value.addProperty("plan_sha256", plan.sha256());
            value.addProperty("client_session_id", SESSION);
            value.addProperty("process_id", ProcessHandle.current().pid());
            value.addProperty("captured_unix_ms", System.currentTimeMillis());
            value.addProperty("java_runtime", System.getProperty("java.runtime.version"));
            value.addProperty("phase", "connected_client");
            value.addProperty("actor_uuid", client.player.getUUID().toString());
            value.addProperty("dimension", client.level.dimension().location().toString());
            value.addProperty("operator_development_only", true);
            value.addProperty("scoring_eligible", false);
            JsonArray queries = new JsonArray(), snapshots = new JsonArray();
            for (ConfigQuery query : plan.config().configQueries()) {
                queries.add(query.json()); snapshots.add(ConfigSnapshot.capture(query));
            }
            value.add("config_queries", queries); value.add("config_snapshots", snapshots);
            byte[] bytes = (value + "\n").getBytes(StandardCharsets.UTF_8);
            if (bytes.length > plan.config().maxBytes()) throw new IOException("CLIENT_CONFIG_OUTPUT_QUOTA");
            plan.unchanged();
            Path root = TelemetryConfig.safeExisting(plan.config().spoolDirectory());
            try (FileChannel file = FileChannel.open(root.resolve("client-config-" + SESSION + ".json"),
                    StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE)) {
                ByteBuffer buffer = ByteBuffer.wrap(bytes);
                while (buffer.hasRemaining()) file.write(buffer);
                file.force(true);
            }
        } catch (IOException error) { throw new IllegalStateException("STRATA_CLIENT_CONFIG_EXPORT_FAILED", error); }
    }
}
