package io.github.opencnid.strata.telemetry;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class CraftCaptureTest {
    @Test void knownNativeSlotNeedsItsExactArtifactAndUnknownSubclassesReject() {
        assertTrue(CraftCapture.supportedSlot("net.minecraft.world.inventory.ResultSlot",false));
        assertTrue(CraftCapture.supportedSlot("shadows.fastbench.util.CraftResultSlotExt",true));
        assertFalse(CraftCapture.supportedSlot("shadows.fastbench.util.CraftResultSlotExt",false));
        assertFalse(CraftCapture.supportedSlot("other.ResultSlot",true));
        assertFalse(CraftCapture.supportedSlot("shadows.fastbench.util.CraftResultSlotExt$Subclass",true));
    }
}
