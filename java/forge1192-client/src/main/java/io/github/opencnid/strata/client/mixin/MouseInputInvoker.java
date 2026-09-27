package io.github.opencnid.strata.client.mixin;

import net.minecraft.client.MouseHandler;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.gen.Invoker;

/** Exact 1.19.2 ordinary callback, invoked only by the owned private input session. */
@Mixin(MouseHandler.class)
public interface MouseInputInvoker {
    @Invoker(value = "m_91530_", remap = false)
    void strata$button(long window, int button, int action, int modifiers);
}
