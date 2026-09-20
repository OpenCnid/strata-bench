package io.github.opencnid.strata.client;

import com.google.gson.JsonObject;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Map;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.screens.TitleScreen;
import net.minecraftforge.client.loading.ClientModLoader;
import net.minecraftforge.common.MinecraftForge;
import net.minecraftforge.event.TickEvent;

/** Explicit operator-only title-screen round trip. No gameplay endpoint or capability claim. */
final class ClientSettingsProbe {
    private static boolean attempted;

    static void install() { MinecraftForge.EVENT_BUS.addListener(ClientSettingsProbe::tick); }

    private static void tick(TickEvent.ClientTickEvent event) {
        if (attempted || event.phase != TickEvent.Phase.END || ClientModLoader.isLoading()) return;
        String directory = System.getProperty("strata.settingsTransactionDirectory");
        if (directory == null) { attempted = true; return; }
        if (System.getProperty("strata.settingsBridgeDirectory") != null) {
            attempted = true;
            throw new IllegalStateException("SETTINGS_DIAGNOSTICS_CONFLICT");
        }
        Minecraft client = Minecraft.getInstance();
        if (!(client.screen instanceof TitleScreen) || client.player != null || client.level != null) return;
        attempted = true;
        try { run(client, Path.of(directory)); }
        catch (IOException error) { throw new IllegalStateException("STRATA_SETTINGS_PROBE_FAILED", error); }
    }

    private static JsonObject state(NativeSettingsRuntime runtime, Path options) throws IOException {
        JsonObject result = new JsonObject();
        Map<String, String> values = new java.util.TreeMap<>();
        runtime.bindings().forEach((id, binding) -> values.put(id, binding.value()));
        result.add("runtime", SettingsJson.strings(values));
        result.addProperty("options_sha256", KeyOptions.sha256(SettingsFiles.readOptions(options)));
        return result;
    }

    private static void run(Minecraft client, Path directory) throws IOException {
        Path profile = SettingsFiles.safeExisting(client.gameDirectory.toPath().toAbsolutePath().normalize());
        directory = SettingsFiles.safeExisting(directory);
        if (!Files.isDirectory(directory) || directory.startsWith(profile) || profile.startsWith(directory)) {
            throw new IOException("SETTINGS_PRIVATE_ROOT_REQUIRED");
        }
        // Refuse repeat execution. A pending journal requires a distinct recovery procedure.
        if (Files.exists(directory.resolve("settings-journal.jsonl"))) throw new IOException("SETTINGS_PROBE_ALREADY_STARTED");
        NativeSettingsRuntime runtime = new NativeSettingsRuntime(client);
        Path options = profile.resolve("options.txt");
        JsonObject report = new JsonObject();
        report.addProperty("schema", "strata/NativeSettingsRoundTrip/1");
        report.addProperty("operator_development_only", true);
        report.addProperty("gameplay_capability_qualified", false);
        report.addProperty("gate_result", "not_run");
        report.addProperty("fingerprint", runtime.fingerprint());
        report.add("ownership", runtime.ownershipEvidence());
        report.add("before", state(runtime, options));
        SettingsFiles.writeNew(directory.resolve("options-before.txt"),
            SettingsFiles.readOptions(options).getBytes(StandardCharsets.UTF_8));
        try (SettingsStore store = new SettingsStore(profile, directory, runtime.fingerprint(), runtime)) {
            String before = runtime.bindings().get(NativeSettingsRuntime.TARGET).value();
            if (!before.equals("key.keyboard.unknown")) throw new IOException("SETTINGS_PROBE_REQUIRES_INITIAL_UNBOUND_KEY");
            Throwable primaryFailure = null;
            try {
                SettingsStore.Receipt receipt = store.apply("operator-roundtrip-1", store.snapshot(),
                    Map.of(NativeSettingsRuntime.TARGET, new SettingsStore.Change(before, "key.keyboard.f13")));
                report.addProperty("apply_phase", receipt.phase());
                report.addProperty("committed", receipt.committed());
                report.add("applied", state(runtime, options));
                SettingsFiles.writeNew(directory.resolve("options-applied.txt"),
                    SettingsFiles.readOptions(options).getBytes(StandardCharsets.UTF_8));
            } catch (IOException | RuntimeException error) {
                primaryFailure = error;
                throw error;
            } finally {
                // This conformance probe is never committed, even after successful readback.
                try { report.addProperty("rollback_phase", store.rollback("operator-roundtrip-1").phase()); }
                catch (IOException rollbackError) {
                    if (primaryFailure == null) throw rollbackError;
                    if (!"SETTINGS_TRANSACTION_MISSING".equals(rollbackError.getMessage())) {
                        primaryFailure.addSuppressed(rollbackError);
                    }
                }
                finally { runtime.releaseInputs(); }
            }
            report.add("restored", state(runtime, options));
        }
        if (!report.get("before").equals(report.get("restored"))) throw new IOException("SETTINGS_PROBE_RESTORE_MISMATCH");
        SettingsFiles.writeNew(directory.resolve("roundtrip.json"), (report + "\n").getBytes(StandardCharsets.UTF_8));
    }
}
