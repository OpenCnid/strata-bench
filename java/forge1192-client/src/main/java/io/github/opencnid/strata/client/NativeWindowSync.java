package io.github.opencnid.strata.client;

import io.netty.channel.ChannelHandlerContext;
import io.netty.channel.ChannelInboundHandlerAdapter;
import it.unimi.dsi.fastutil.ints.Int2ObjectOpenHashMap;
import java.io.IOException;
import net.minecraft.client.Minecraft;
import net.minecraft.network.Connection;
import net.minecraft.network.protocol.game.ClientboundContainerSetContentPacket;
import net.minecraft.network.protocol.game.ServerboundContainerClickPacket;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.inventory.ClickType;

/** Private fixed open-menu refresh. No caller-selectable packet or unopened-window query. */
final class NativeWindowSync {
    private static final String NAME = "strata_open_menu_feedback";
    private final Minecraft client;
    private final Connection connection;
    private final GameMenuFeedback<AbstractContainerMenu> feedback = new GameMenuFeedback<>();
    private volatile boolean ready;
    NativeWindowSync(Minecraft client, Connection connection) throws IOException {
        this.client = client; this.connection = connection;
        var pipeline = connection.channel().pipeline();
        if (pipeline.get("packet_handler") != connection || pipeline.get(NAME) != null) throw new IOException("GAME_MENU_SYNC_UNAVAILABLE");
        pipeline.addBefore("packet_handler", NAME, new ChannelInboundHandlerAdapter() {
            public void handlerAdded(ChannelHandlerContext context) { ready = true; }
            public void handlerRemoved(ChannelHandlerContext context) { ready = false; }
            public void channelRead(ChannelHandlerContext context, Object message) throws Exception {
                ClientboundContainerSetContentPacket contents = message instanceof ClientboundContainerSetContentPacket value ? value : null;
                var requested = contents == null ? null : feedback.capture(contents.getContainerId());
                // Minecraft first enqueues/applies its normal packet handler. Our
                // client-thread callback follows that task in the same queue.
                context.fireChannelRead(message);
                if (requested != null) client.execute(() -> receive(requested, contents));
            }
        });
    }
    void requireReady() throws IOException {
        if (!ready || client.player == null || client.getConnection() == null || client.getConnection().getConnection() != connection) {
            throw new IOException("GAME_MENU_SYNC_UNAVAILABLE");
        }
    }
    boolean uncertain() { return feedback.uncertain(); }
    void markDirty(AbstractContainerMenu menu) throws IOException {
        requireReady();
        // Retain a bounded listener even if the subsequent refresh cannot be
        // emitted. Only real, applied full contents can resolve that uncertainty.
        feedback.markDirty(menu, menu.containerId);
    }
    long request(AbstractContainerMenu menu) throws IOException {
        requireReady();
        if (!client.isSameThread() || client.player == null || client.player.containerMenu != menu || menu.slots.size() > 1024) {
            throw new IOException("REVISION_CONFLICT");
        }
        var request = feedback.request(menu, menu.containerId);
        // Verified against pinned AbstractContainerMenu: PICKUP_ALL with a
        // negative outside slot is a no-op (including with a carried stack).
        // State IDs are 15-bit nonnegative; -1 forces the server's full refresh.
        // This fixed transport primitive has no public packet parameters.
        connection.send(new ServerboundContainerClickPacket(menu.containerId, -1, -999, 0,
            ClickType.PICKUP_ALL, menu.getCarried().copy(), new Int2ObjectOpenHashMap<>()));
        return request.id;
    }
    private void receive(GameMenuFeedback.Ticket<AbstractContainerMenu> request, ClientboundContainerSetContentPacket packet) {
        if (client.player == null || !feedback.current(request, client.player.containerMenu)
                || client.getConnection() == null || client.getConnection().getConnection() != connection) return;
        try {
            if (packet.getItems().size() != request.menu.slots.size() || packet.getItems().size() > 1024) throw new IOException("GAME_CONTAINER_UNSUPPORTED");
            GameInventory.View received = NativeGameRuntime.inventoryView(request.menu, packet.getItems(), packet.getCarriedItem());
            feedback.apply(request, client.player.containerMenu, received, NativeGameRuntime.inventoryView(request.menu));
        } catch (IOException error) { feedback.invalid(request); }
    }
    GameInventory.View reply(long ticket, AbstractContainerMenu menu) throws IOException {
        requireReady();
        if (client.player.containerMenu != menu) throw new IOException("REVISION_CONFLICT");
        return feedback.reply(ticket, menu);
    }
    void cancel() { feedback.cancel(); }
    void close() {
        feedback.close(); ready = false;
        var pipeline = connection.channel().pipeline();
        if (pipeline.get(NAME) != null) pipeline.remove(NAME);
    }
}
