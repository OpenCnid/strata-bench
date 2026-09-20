package io.github.opencnid.strata.client;

import com.mojang.blaze3d.platform.GlStateManager;
import com.mojang.blaze3d.systems.RenderSystem;
import java.io.IOException;
import java.nio.file.Path;
import net.minecraft.client.Minecraft;
import net.minecraft.client.Screenshot;
import net.minecraftforge.client.loading.ClientModLoader;
import net.minecraftforge.fml.ModList;
import org.lwjgl.opengl.GL11;
import org.lwjgl.opengl.GL21;

/** Private operator evidence from this client's own render target, never OS capture. */
public final class ClientFrameProbe {
    private static PrivateFrames store;
    private static boolean disabled;
    private static long frame, lastPoll = Long.MIN_VALUE;
    private ClientFrameProbe() {}

    public static void beforeDisplay() {
        if (disabled) return;
        String directory = System.getProperty("strata.privateFrameDirectory");
        if (directory == null) { disabled = true; return; }
        if (ClientModLoader.isLoading()) return;
        long now = System.nanoTime(); frame++;
        if (lastPoll != Long.MIN_VALUE && now - lastPoll < 250_000_000L) return;
        lastPoll = now;
        try {
            RenderSystem.assertOnRenderThread();
            Minecraft client = Minecraft.getInstance();
            if (store == null) store = new PrivateFrames(Path.of(directory),
                client.gameDirectory.toPath().toAbsolutePath().normalize(),
                ArtifactFiles.hash(ModList.get().getModFileById("strata_client").getFile().getFilePath()),
                System::nanoTime, System::currentTimeMillis);
            var target = client.getMainRenderTarget();
            String screen = client.screen == null ? "" : client.screen.getClass().getName();
            store.capture(screen, client.player != null && client.level != null,
                target.width, target.height, frame, () -> read(client));
        } catch (IOException | RuntimeException error) {
            disabled = true;
            if (store != null) store.fail(error.getMessage());
            com.mojang.logging.LogUtils.getLogger().error("STRATA_PRIVATE_FRAME_CAPTURE_FAILED");
        }
    }

    private static byte[] read(Minecraft client) throws IOException {
        if (client.noRender) throw new IOException("FRAME_NOT_RENDERED");
        var target = client.getMainRenderTarget();
        // A PBO or non-default row layout would reinterpret NativeImage's pointer.
        if (GL11.glGetInteger(GL21.GL_PIXEL_PACK_BUFFER_BINDING) != 0
                || GL11.glGetInteger(GL11.GL_PACK_ROW_LENGTH) != 0
                || GL11.glGetInteger(GL11.GL_PACK_SKIP_ROWS) != 0
                || GL11.glGetInteger(GL11.GL_PACK_SKIP_PIXELS) != 0)
            throw new IOException("FRAME_PACK_STATE_UNSUPPORTED");
        int texture = GL11.glGetInteger(GL11.GL_TEXTURE_BINDING_2D);
        int alignment = GL11.glGetInteger(GL11.GL_PACK_ALIGNMENT);
        try {
            RenderSystem.bindTexture(target.getColorTextureId());
            if (GL11.glGetTexLevelParameteri(GL11.GL_TEXTURE_2D, 0, GL11.GL_TEXTURE_WIDTH) != target.width
                    || GL11.glGetTexLevelParameteri(GL11.GL_TEXTURE_2D, 0, GL11.GL_TEXTURE_HEIGHT) != target.height)
                throw new IOException("FRAME_TEXTURE_MISMATCH");
            try (var image = Screenshot.takeScreenshot(target)) { return image.asByteArray(); }
        } finally {
            RenderSystem.bindTexture(texture);
            GlStateManager._pixelStore(GL11.GL_PACK_ALIGNMENT, alignment);
        }
    }
}
