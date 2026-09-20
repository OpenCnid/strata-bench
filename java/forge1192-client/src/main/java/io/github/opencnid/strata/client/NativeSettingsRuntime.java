package io.github.opencnid.strata.client;

import com.google.gson.JsonObject;
import com.mojang.blaze3d.platform.InputConstants;
import java.io.IOException;
import java.lang.reflect.Modifier;
import java.nio.file.Path;
import java.util.HashMap;
import java.util.Map;
import java.util.TreeMap;
import net.minecraft.client.KeyMapping;
import net.minecraft.client.Minecraft;
import net.minecraftforge.client.settings.KeyModifier;
import net.minecraftforge.fml.ModList;

/** Development native writer. Ownership is source-bound; physical input is NOT qualified. */
final class NativeSettingsRuntime implements SettingsStore.RuntimePort {
    static final String CURIOS_SHA256 = "1f7742d6c4f6b6cd8d106e54181255c2d264194ba232d42901ef90da6b91e635";
    static final String TARGET = "curios:key.curios.open.desc:0";
    private final Minecraft client;
    private final KeyMapping owned;
    private final String fingerprint;

    NativeSettingsRuntime(Minecraft client) throws IOException {
        this.client = client;
        requireClientThread();
        var mod = ModList.get().getModFileById("curios");
        if (mod == null || !CURIOS_SHA256.equals(fileHash(mod.getFile().getFilePath()))) {
            throw new IOException("SETTINGS_OWNER_ARTIFACT_UNSUPPORTED");
        }
        try {
            Class<?> registration = Class.forName("top.theillusivec4.curios.client.KeyRegistry", false,
                NativeSettingsRuntime.class.getClassLoader());
            var field = registration.getDeclaredField("openCurios");
            if (!Modifier.isPublic(field.getModifiers()) || !Modifier.isStatic(field.getModifiers())
                    || field.getType() != KeyMapping.class) throw new IOException("SETTINGS_OWNER_REGISTRATION_INVALID");
            Object value = field.get(null);
            if (!(value instanceof KeyMapping mapping) || mapping.getClass() != KeyMapping.class
                    || !"key.curios.open.desc".equals(mapping.getName())) {
                throw new IOException("SETTINGS_OWNER_REGISTRATION_INVALID");
            }
            owned = mapping;
        } catch (ReflectiveOperationException error) {
            throw new IOException("SETTINGS_OWNER_REGISTRATION_UNAVAILABLE", error);
        }
        if (!mappings().containsKey(TARGET)) throw new IOException("SETTINGS_OWNER_NOT_REGISTERED");
        JsonObject artifacts = new JsonObject();
        Map<String, String> hashes = new TreeMap<>();
        for (var file : ModList.get().getModFiles()) {
            Path path = file.getFile().getFilePath();
            String name = path.getFileName().toString();
            if (hashes.put(name, fileHash(path)) != null) throw new IOException("SETTINGS_ARTIFACT_AMBIGUOUS");
        }
        artifacts.add("loaded_mod_artifacts", SettingsJson.strings(hashes));
        artifacts.addProperty("artifact_hash_policy", ArtifactFiles.POLICY);
        artifacts.addProperty("java_runtime", System.getProperty("java.runtime.version"));
        artifacts.addProperty("os", System.getProperty("os.name") + ":" + System.getProperty("os.arch"));
        artifacts.addProperty("policy", "strata/native-settings-development/1");
        fingerprint = KeyOptions.sha256(artifacts.toString());
    }

    static String fileHash(Path path) throws IOException {
        return ArtifactFiles.hash(path);
    }

    String fingerprint() { return fingerprint; }

    JsonObject ownershipEvidence() {
        JsonObject result = new JsonObject();
        result.addProperty("mod", "curios");
        result.addProperty("artifact_sha256", CURIOS_SHA256);
        result.addProperty("registration", "top.theillusivec4.curios.client.KeyRegistry.openCurios");
        result.addProperty("registered_object_identity_checked", true);
        result.addProperty("physical_input_tested", false);
        return result;
    }

    @Override public void requireClientThread() throws IOException {
        if (!client.isSameThread()) throw new IOException("CLIENT_THREAD_REQUIRED");
        if (client.options == null) throw new IOException("CLIENT_NOT_READY");
    }

    private Map<String, KeyMapping> mappings() throws IOException {
        requireClientThread();
        if (client.options.keyMappings.length > 2048) throw new IOException("KEYMAP_TOO_LARGE");
        Map<String, Integer> counts = new HashMap<>(), seen = new HashMap<>();
        for (KeyMapping key : client.options.keyMappings) counts.merge(key.getName(), 1, Integer::sum);
        Map<String, KeyMapping> result = new TreeMap<>();
        int ownCount = 0;
        for (KeyMapping key : client.options.keyMappings) {
            String name = key.getName();
            int occurrence = seen.merge(name, 1, Integer::sum) - 1;
            if (key == owned) {
                ownCount++;
                if (counts.get(name) != 1) throw new IOException("SETTINGS_OWNER_AMBIGUOUS");
            }
            result.put(KeyOptions.stableId(key == owned ? "curios" : "unknown", name, occurrence), key);
        }
        if (ownCount != 1) throw new IOException("SETTINGS_OWNER_NOT_REGISTERED");
        return result;
    }

    private static String persisted(KeyMapping mapping) {
        KeyModifier modifier = mapping.getKeyModifier();
        return mapping.getKey().getName() + (modifier == KeyModifier.NONE ? "" : ":" + modifier.name());
    }

    @Override public Map<String, SettingsStore.Binding> bindings() throws IOException {
        Map<String, SettingsStore.Binding> result = new TreeMap<>();
        mappings().forEach((id, key) -> result.put(id,
            new SettingsStore.Binding(key.getName(), persisted(key), key == owned)));
        return result;
    }

    @Override public void validateKeys(Map<String, String> changes) throws IOException {
        requireClientThread();
        Map<String, KeyMapping> all = mappings();
        if (changes.size() != 1 || !changes.containsKey(TARGET) || all.get(TARGET) != owned) {
            throw new IOException("PROTECTED_OR_UNKNOWN_BINDING");
        }
        String value = changes.get(TARGET);
        // A narrowly scoped configuration-write probe, NOT a tested physical key pool.
        if (!"key.keyboard.unknown".equals(value) && !"key.keyboard.f13".equals(value)) {
            throw new IOException("SETTINGS_DEVELOPMENT_KEY_UNSUPPORTED");
        }
        parse(value);
    }

    private record Parsed(InputConstants.Key key, KeyModifier modifier) {}

    private static Parsed parse(String value) throws IOException {
        try {
            String[] parts = value.split(":", -1);
            if (parts.length > 2) throw new IllegalArgumentException();
            KeyModifier modifier = parts.length == 2 ? KeyModifier.valueOf(parts[1]) : KeyModifier.NONE;
            InputConstants.Key key = InputConstants.getKey(parts[0]);
            if (!key.getName().equals(parts[0])) throw new IllegalArgumentException();
            return new Parsed(key, modifier);
        } catch (IllegalArgumentException error) { throw new IOException("SETTINGS_KEY_ENCODING_UNSUPPORTED", error); }
    }

    @Override public void setKeys(Map<String, String> changes) throws IOException {
        validateKeys(changes);
        Parsed value = parse(changes.get(TARGET));
        owned.setKeyModifierAndCode(value.modifier(), value.key());
        KeyMapping.resetMapping();
    }

    @Override public void releaseInputs() throws IOException {
        requireClientThread();
        KeyMapping.releaseAll();
        for (KeyMapping mapping : client.options.keyMappings) {
            int drained = 0;
            while (mapping.consumeClick()) {
                if (++drained > 2048) throw new IOException("SETTINGS_INPUT_QUEUE_UNBOUNDED");
            }
            if (mapping.isDown()) throw new IOException("SETTINGS_INPUT_RELEASE_UNCONFIRMED");
        }
    }
}
