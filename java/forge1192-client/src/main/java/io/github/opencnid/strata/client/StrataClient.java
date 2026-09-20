package io.github.opencnid.strata.client;

import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.fml.DistExecutor;
import net.minecraftforge.fml.common.Mod;

@Mod("strata_client")
public final class StrataClient {
    public StrataClient() {
        DistExecutor.safeRunWhenOn(Dist.CLIENT, () -> ClientDiscoveryExport::install);
    }
}
