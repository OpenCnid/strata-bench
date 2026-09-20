package io.github.opencnid.strata.client;

import com.google.gson.JsonArray;
import com.google.gson.JsonNull;
import com.google.gson.JsonObject;
import com.mojang.blaze3d.platform.InputConstants;
import java.io.IOException;
import java.util.HashMap;
import java.util.IdentityHashMap;
import java.util.Map;
import net.minecraft.client.KeyMapping;
import net.minecraft.client.Minecraft;
import net.minecraft.client.Options;
import net.minecraft.client.resources.language.I18n;
import net.minecraftforge.client.settings.KeyConflictContext;
import net.minecraftforge.client.settings.KeyModifier;

/** Client-thread discovery only. No inferred mod ownership or claimed input effects. */
final class BindingDiscovery {
    private String previousDigest;
    private long revision;

    JsonObject snapshot(Minecraft client) throws IOException {
        if (!client.isSameThread()) throw new IOException("CLIENT_THREAD_REQUIRED");
        if (client.options == null || client.options.keyMappings.length > 2048) throw new IOException("CLIENT_NOT_READY");
        KeyOptions disk = KeyOptions.read(client.gameDirectory.toPath().resolve("options.txt"));
        Map<KeyMapping, String> vanilla = vanillaFields(client.options);
        Map<String, Integer> total = new HashMap<>(), seen = new HashMap<>();
        for (KeyMapping mapping : client.options.keyMappings) total.merge(mapping.getName(), 1, Integer::sum);
        JsonObject bindings = new JsonObject();
        for (KeyMapping mapping : client.options.keyMappings) {
            String translation = mapping.getName();
            int occurrence = seen.merge(translation, 1, Integer::sum) - 1;
            String owner = vanilla.containsKey(mapping) ? "minecraft" : "unknown";
            String id = KeyOptions.stableId(owner, translation, occurrence);
            JsonObject binding = new JsonObject();
            binding.addProperty("translation_id", translation);
            binding.addProperty("registration_occurrence", occurrence);
            binding.addProperty("label", I18n.get(translation));
            binding.addProperty("category", mapping.getCategory());
            binding.addProperty("owner_mod", owner);
            binding.addProperty("owner_basis", vanilla.getOrDefault(mapping, "unresolved"));
            binding.add("owner_evidence", JsonNull.INSTANCE); // Operator source/registration proof not bound yet.
            binding.addProperty("ambiguous_occurrence", total.get(translation) != 1);
            binding.addProperty("persisted_ambiguous", disk.ambiguous().contains(translation));
            binding.add("persisted_value", disk.values().containsKey(translation)
                ? new com.google.gson.JsonPrimitive(disk.values().get(translation)) : JsonNull.INSTANCE);
            binding.add("key", physical(mapping.getKey(), mapping.getKeyModifier()));
            binding.add("default_key", physical(mapping.getDefaultKey(), mapping.getDefaultKeyModifier()));
            JsonArray contexts = new JsonArray();
            if (mapping.getKeyConflictContext() instanceof KeyConflictContext known) {
                contexts.add(known.name());
                binding.addProperty("context_confidence", "known");
            } else {
                contexts.add("CUSTOM");
                binding.addProperty("context_confidence", "unknown");
            }
            binding.add("contexts", contexts);
            // All vanilla fields are protected, and unresolved mod ownership has
            // no mutation authority. A translation prefix is not owning-mod proof.
            binding.addProperty("protected", true);
            binding.addProperty("consumer_tested", false);
            binding.addProperty("mutation_supported", false);
            bindings.add(id, binding);
        }
        String contentDigest = KeyOptions.sha256(bindings.toString() + "\n" + disk.fileDigest());
        if (!contentDigest.equals(previousDigest)) { revision++; previousDigest = contentDigest; }
        JsonObject result = new JsonObject();
        result.addProperty("schema", "strata/ForgeBindingDiscovery/1");
        result.addProperty("backend", "glfw");
        result.addProperty("module", "strata-forge1192-client/0.1.0");
        result.addProperty("supported", false);
        result.addProperty("discovery_supported", true);
        result.addProperty("atomic_cas", false);
        result.addProperty("restart_tested", false);
        result.addProperty("layout_verified", false);
        result.addProperty("revision", revision);
        result.addProperty("keymap_digest", contentDigest);
        result.addProperty("options_file_sha256", disk.fileDigest());
        result.addProperty("persisted_file_present", disk.fileDigest() != null);
        result.add("bindings", bindings);
        result.add("tested_pool", new JsonArray());
        return result;
    }

    private static Map<KeyMapping, String> vanillaFields(Options options) {
        Map<KeyMapping, String> result = new IdentityHashMap<>();
        // Explicit mapped field access survives reobfuscation. Reflection over
        // all KeyMapping fields could misattribute a mod-injected field to vanilla.
        KeyMapping[] known = {options.keyUp, options.keyLeft, options.keyDown, options.keyRight,
            options.keyJump, options.keyShift, options.keySprint, options.keyInventory,
            options.keySwapOffhand, options.keyDrop, options.keyUse, options.keyAttack,
            options.keyPickItem, options.keyChat, options.keyPlayerList, options.keyCommand,
            options.keySocialInteractions, options.keyScreenshot, options.keyTogglePerspective,
            options.keySmoothCamera, options.keyFullscreen, options.keySpectatorOutlines,
            options.keyAdvancements, options.keySaveHotbarActivator, options.keyLoadHotbarActivator};
        String[] fields = {"keyUp", "keyLeft", "keyDown", "keyRight", "keyJump", "keyShift",
            "keySprint", "keyInventory", "keySwapOffhand", "keyDrop", "keyUse", "keyAttack",
            "keyPickItem", "keyChat", "keyPlayerList", "keyCommand", "keySocialInteractions",
            "keyScreenshot", "keyTogglePerspective", "keySmoothCamera", "keyFullscreen",
            "keySpectatorOutlines", "keyAdvancements", "keySaveHotbarActivator", "keyLoadHotbarActivator"};
        for (int i = 0; i < known.length; i++) result.put(known[i], "minecraft:Options." + fields[i]);
        for (int i = 0; i < options.keyHotbarSlots.length; i++) {
            result.put(options.keyHotbarSlots[i], "minecraft:Options.keyHotbarSlots:" + i);
        }
        return result;
    }

    private static JsonObject physical(InputConstants.Key key, KeyModifier modifier) {
        JsonObject value = new JsonObject();
        value.addProperty("backend", "glfw");
        boolean unbound = key.equals(InputConstants.UNKNOWN);
        value.addProperty("representation", unbound ? "unbound" : switch (key.getType()) {
            case KEYSYM -> "keysym";
            case SCANCODE -> "scancode";
            case MOUSE -> "mouse_button";
        });
        if (unbound) value.add("code", JsonNull.INSTANCE); else value.addProperty("code", key.getValue());
        value.addProperty("name", key.getName());
        JsonArray modifiers = new JsonArray();
        if (!unbound && modifier != KeyModifier.NONE) modifiers.add(modifier.name());
        value.add("modifiers", modifiers);
        value.addProperty("persisted", key.getName() + (modifier == KeyModifier.NONE ? "" : ":" + modifier.name()));
        return value;
    }
}
