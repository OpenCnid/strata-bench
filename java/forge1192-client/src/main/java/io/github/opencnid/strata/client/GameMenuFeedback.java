package io.github.opencnid.strata.client;

import java.io.IOException;
import java.util.concurrent.atomic.AtomicBoolean;

/** One bounded network-to-client-thread feedback slot; uncertainty survives cancellation. */
final class GameMenuFeedback<M> {
    static final class Ticket<M> {
        final long id; final M menu; final int containerId;
        final AtomicBoolean captured = new AtomicBoolean();
        GameInventory.View response; boolean invalid, cancelled;
        Ticket(long id, M menu, int containerId) { this.id = id; this.menu = menu; this.containerId = containerId; }
    }
    private volatile Ticket<M> pending;
    private boolean uncertain;
    private long sequence;
    void markDirty(M menu, int containerId) { uncertain = true; pending = new Ticket<>(0, menu, containerId); }
    Ticket<M> request(M menu, int containerId) { return pending = new Ticket<>(++sequence, menu, containerId); }
    // Called by the network thread; never reads mutable menu/game state.
    Ticket<M> capture(int containerId) {
        Ticket<M> value = pending;
        return value != null && value.containerId == containerId && value.captured.compareAndSet(false, true) ? value : null;
    }
    boolean current(Ticket<M> ticket, M menu) { return pending == ticket && ticket.menu == menu; }
    void apply(Ticket<M> ticket, M menu, GameInventory.View received, GameInventory.View applied) {
        if (!current(ticket, menu) || ticket.invalid) return;
        if (!received.equals(applied)) { ticket.invalid = true; return; }
        ticket.response = received; uncertain = false;
    }
    void invalid(Ticket<M> ticket) { if (pending == ticket) ticket.invalid = true; }
    GameInventory.View reply(long id, M menu) throws IOException {
        Ticket<M> value = pending;
        if (value == null || value.cancelled || value.id != id || value.menu != menu) throw new IOException("REVISION_CONFLICT");
        if (value.invalid) throw new IOException("GAME_CONTAINER_UNSUPPORTED");
        return value.response;
    }
    boolean uncertain() { return uncertain; }
    void cancel() { if (pending != null) pending.cancelled = true; }
    void close() { pending = null; }
}
