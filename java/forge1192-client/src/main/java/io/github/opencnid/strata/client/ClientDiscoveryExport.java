package io.github.opencnid.strata.client;

import com.google.gson.JsonObject;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.channels.FileChannel;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.UUID;
import net.minecraft.client.Minecraft;
import net.minecraftforge.client.loading.ClientModLoader;
import net.minecraftforge.common.MinecraftForge;
import net.minecraftforge.event.TickEvent;

/** Optional one-shot operator diagnostic; never exposes a settings mutation endpoint. */
final class ClientDiscoveryExport {
    private static boolean attempted;
    private static final BindingDiscovery DISCOVERY = new BindingDiscovery();

    static void install() {
        MinecraftForge.EVENT_BUS.addListener(ClientDiscoveryExport::tick);
        ClientSettingsProbe.install();
        ClientSettingsBridge.install();
        ClientGameBridge.install();
        ClientCollisionProbe.install();
    }

    private static void tick(TickEvent.ClientTickEvent event) {
        if (attempted || event.phase != TickEvent.Phase.END || ClientModLoader.isLoading()) return;
        String directory = System.getProperty("strata.settingsDiscoveryDirectory",
            System.getenv("STRATA_SETTINGS_DISCOVERY_DIR"));
        if (directory == null) { attempted = true; return; }
        Minecraft client = Minecraft.getInstance();
        if (client.options == null) return;
        attempted = true;
        try {
            Path root = Path.of(directory);
            if (!root.isAbsolute() || !Files.isDirectory(root)
                    || !root.normalize().equals(root.toRealPath())
                    || root.startsWith(client.gameDirectory.toPath().toAbsolutePath().normalize())) {
                throw new IOException("SETTINGS_PRIVATE_OUTPUT_REQUIRED");
            }
            JsonObject value = DISCOVERY.snapshot(client);
            value.addProperty("operator_development_only", true);
            byte[] bytes = (value + "\n").getBytes(StandardCharsets.UTF_8);
            if (bytes.length > 524288) throw new IOException("KEYMAP_TOO_LARGE");
            Path output = root.resolve("bindings-" + UUID.randomUUID() + ".json");
            try (FileChannel file = FileChannel.open(output, StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE)) {
                ByteBuffer buffer = ByteBuffer.wrap(bytes);
                while (buffer.hasRemaining()) file.write(buffer);
                file.force(true);
            }
        } catch (IOException error) {
            throw new IllegalStateException("STRATA_SETTINGS_DISCOVERY_FAILED", error);
        }
    }
}
