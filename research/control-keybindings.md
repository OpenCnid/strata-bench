# Full-client control and Dovetail keybinding skill design

> Architecture update, 2026-09-18 (D01): the user selected Mineflayer as the first control backend, with structured observations/actions. Direct Codex CLI/local commands are the default (D02); MCP and app-server are optional. Full-client-first proposals and prior review conclusions below are historical. Use [SPEC.md](../SPEC.md), [MILESTONES.md](../MILESTONES.md), and the [Mineflayer decision](mineflayer-backend.md) for current contracts and gates; source findings remain supporting evidence.

Research date: 2026-09-17 (America/Chicago). Scope: evidence and a proposed contract, not an installed controller or finished skill. No client, modpack, keybinding, or world was changed. No runtime compatibility tests were performed.

## Recommendation and evidence status

**Proposal:** Make a real Minecraft client running the exact modpack the execution boundary. Use rendered frames plus keyboard/mouse events as the strict benchmark interface. Establish an OS-input implementation in an isolated display/session as the reference. A small, version-specific client bridge is a promising scaling transport, but admit it only after it passes event/polling/input-context parity tests against that reference. Do not promise that a few `KeyMapping.setDown` calls control arbitrary mods.

Use a separate, pre-episode Dovetail skill, provisionally `minecraft-keybindings`, to discover, resolve, persist, and verify keybindings. Freeze its output for an episode. Gameplay gets physical input primitives; setup gets binding-management privileges. This distinction lets the agent use a modpack fully without silently bypassing its conflicts or granting a semantic “invoke any mod function” API.

**Consolidation decision:** the final BUILD_PLAN and SPEC_PROMPT retain this setup-only policy for the strict reference, but permit agent-requested reconfiguration segments in the declared `pixels-input-settings/v1` primary track. Those segments preserve campaign continuity, version the profile, and charge time/compute/actions. In-play checks use ordinary accessible game state. Private fixture/handler diagnostics remain preflight/evaluator-only. The user confirmed dovetail-codex and CurseForge + Forge; E9E is the proposed first target.

**Facts** below are sourced to official documentation, publisher metadata, or project-owned source. **Inferences** explain implications without claiming runtime proof. **Proposals** are design choices. **Unknowns/gates** must be resolved for each exact client/loader/modpack/platform tuple.

## Verified keyboard constraints

### Unicode is not an unlimited keybinding namespace

**Fact:** GLFW separates physical key events (key token, platform scancode, press/release/repeat, modifiers) from Unicode character events used for text. They are not one-to-one. It also keeps a per-window key-state cache for polling. Scancodes are platform-specific; a token and a scancode are different identifiers. [GLFW input guide](https://www.glfw.org/docs/latest/input_guide.html)

**Fact:** Windows `KEYEVENTF_UNICODE` creates a `VK_PACKET` event and ultimately character text for the foreground application. `KEYEVENTF_SCANCODE` instead selects the physical-keystroke path; key-up is explicit. Merely placing a Unicode number in a binding file does not manufacture that physical key. [Microsoft KEYBDINPUT](https://learn.microsoft.com/en-us/windows/win32/api/winuser/ns-winuser-keybdinput)

**Proposal:** Reject Unicode characters as candidates for gameplay bindings. Provide a separate text-input operation for chat, search boxes, and other text fields. Treat any legacy character-derived binding behavior as an unsupported special case until demonstrated with press, hold, release, restart, and mod-consumer tests; this report does not claim every historical Minecraft text fallback is impossible. Never infer a usable input from its display glyph.

### Version and platform differences matter

**Fact:** Mojang's official 1.12.2 manifest lists LWJGL2 libraries (including platform-conditioned 2.9.4-nightly/2.9.2-nightly entries), while 1.20.1 lists LWJGL 3.3.1 and `lwjgl-glfw`. An actual launcher may override these, so discover the running libraries as well as the Minecraft version. [1.12.2 manifest](https://piston-meta.mojang.com/v1/packages/832d95b9f40699d4961394dcf6cf549e65f15dc5/1.12.2.json), [1.20.1 manifest](https://piston-meta.mojang.com/v1/packages/599695fee750ab157846886c6e69583003f22d07/1.20.1.json)

| Stack | Established source facts | Design consequence / gate |
|---|---|---|
| LWJGL2 / legacy Forge | `Keyboard` has a 256-entry physical key-state buffer, separate event character data, and named F13 through F19 constants. [LWJGL2 Keyboard source](https://github.com/LWJGL/lwjgl/blob/master/src/java/org/lwjgl/input/Keyboard.java) | Numeric codes are LWJGL2 codes, not GLFW tokens, Unicode values, Windows virtual-key values, or portable native scancodes. Validate against the actual loaded library. |
| LWJGL2 Windows backend | Its translation switch maps VK_F13/F14/F15, but has no F16–F24 cases; unmatched virtual keys return `KEY_NONE`, despite VK_F16–F24 declarations. [WindowsKeycodes source](https://github.com/LWJGL/lwjgl/blob/master/src/java/org/lwjgl/opengl/WindowsKeycodes.java) | Do not advertise F13–F24 for 1.12.2 Windows. Start discovery with F13–F15 as candidates, not guaranteed keys. Check launcher replacements and bundled source/version before making a final claim. |
| GLFW | Token definitions include F13=302 through F24=313 and F25=314. [GLFW tokens](https://www.glfw.org/docs/latest/group__keys.html) | Token existence alone does not prove the injector/platform can generate it. |
| Windows + GLFW | Windows documents VK_F1 through VK_F24. GLFW 3.3.8's Windows table maps F13–F24 scancodes; it does not map F25 there. [Windows virtual keys](https://learn.microsoft.com/en-us/windows/win32/inputdev/virtual-key-codes), [GLFW 3.3.8 Windows table](https://github.com/glfw/glfw/blob/3.3.8/src/win32_init.c#L264) | F13–F24 are a sensible modern Windows candidate pool. F25 is not a portable Windows escape hatch. Test the particular GLFW binary and injection backend. |

**Proposal:** Resolve each candidate through an explicit translation record:

`logical token -> injector encoding -> OS event -> library token/scancode -> Minecraft binding -> mod handler -> visible effect -> release`.

Store every representation separately. For example, GLFW F13 is 302 while the cited Windows scancode table uses 0x64; a GLFW token must never be copied into a Windows scancode field. Maintain an allowlist of proven candidates per runtime fingerprint. A key is not usable merely because the controls screen accepted or displayed it.

### Forge contexts, modifiers, conflicts, persistence

**Fact:** Forge documents `UNIVERSAL`, `GUI`, and `IN_GAME` contexts, custom `IKeyConflictContext`, and one `KeyModifier` value from CONTROL/SHIFT/ALT/NONE. Its guidance prefers KEYSYM over SCANCODE for keyboard portability. GUI input can use `isActiveAndMatches`; tick-driven bindings can consume clicks. [Forge key mappings documentation](https://docs.minecraftforge.net/en/latest/misc/keymappings/)

**Fact:** Forge's 1.12 branch already has context and modifier extensions. Its conflict logic explicitly treats a no-modifier binding and a modifier binding on the same key as conflicting in overlapping in-game contexts; it also checks when one binding's base key is the other's modifier. A modified chord is therefore not automatically an independent namespace. [Forge 1.12 KeyBinding patch](https://github.com/MinecraftForge/MinecraftForge/blob/1.12.x/patches/minecraft/net/minecraft/client/settings/KeyBinding.java.patch)

**Fact:** The legacy modifier implementation's NONE can remain active in an in-game context even with a modifier held. It represents a single selected modifier, not an arbitrary Ctrl+Alt+Shift combination. [Forge 1.12 KeyModifier](https://github.com/MinecraftForge/MinecraftForge/blob/1.12.x/src/main/java/net/minecraftforge/client/settings/KeyModifier.java)

**Fact:** The examined modern Forge branch distributes key clicks/state to all entries found for a key and checks contexts/modifiers. This makes “only the intended action fires” a testable requirement, not a safe assumption. [Forge 1.20 KeyMapping patch](https://github.com/MinecraftForge/MinecraftForge/blob/1.20.x/patches/minecraft/net/minecraft/client/KeyMapping.java.patch)

**Fact:** Forge 1.12 saves entries as `key_<binding-name>:<integer>` with an optional `:<modifier>` suffix and reads the same format. The examined 1.20 branch instead uses the key's `saveString()` plus optional modifier suffix in `options.txt`. Both contain protections around mod-loading-time saves. [Legacy GameSettings patch](https://github.com/MinecraftForge/MinecraftForge/blob/1.12.x/patches/minecraft/net/minecraft/client/settings/GameSettings.java.patch), [Modern Options patch](https://github.com/MinecraftForge/MinecraftForge/blob/1.20.x/patches/minecraft/net/minecraft/client/Options.java.patch)

**Proposal:** Use the actual loader's binding objects and serialization methods, and record their raw serialized values. Do not implement one regex/file-format assumption for every version. Preserve mod-owned configuration too: mods may register standard mappings, implement custom controls, or poll raw inputs. A registered-key catalog alone is not proof of complete discovery.

Do not change conflict contexts or mod behavior to manufacture conflict freedom. Treat unknown/custom context overlap conservatively, evaluate the runtime conflict relation in both directions, and validate effects in relevant screens. Never “fix” conflicts by unbinding movement, attack/use, escape, inventory, or required mod controls. Do not quietly unbind optional controls either; record any allowed unbinding explicitly in the plan.

## Control transports and existing projects

| Option | Appropriate use | Limits and admission decision |
|---|---|---|
| Full real client, rendered pixels, OS keyboard/mouse injection | Recommended strict reference. Runs the content mods and their actual screens. No per-mod action implementation is inherently needed. | Focus, mouse capture, display freshness, rate/timing, and N-client isolation must be engineered. Compatibility still needs pack tests. |
| Full real client plus narrow bridge | Proposed optimized transport. Frame capture, raw input queue, input receipts, a setup-only binding inventory, and watchdog are the entire intended surface. | Must reproduce downstream events and polled state. Calling only Minecraft keybinding methods can miss raw library polling, custom GUI handlers, or loader hooks. Version-specific integration and regression gates required. |
| Semantic client/server API | Useful separate assisted-control track, development harness, or evaluator instrumentation. | `craft(recipe)`, pathfind-to-position, click-widget-id, trigger-binding-id, scan-world, and select-entity are materially different action/observation contracts. Do not merge their scores into the strict pixels/input track. |
| Protocol bot | Useful vanilla/protocol baseline and some specifically supported server extensions. | Does not load the pack's real Java client code/UI. Handshake support is not an implementation of arbitrary mod GUI, registries, custom channels, item behavior, or physics. |

**Fact:** Mineflayer exposes world/entity knowledge and high-level inventory/crafting/interaction methods. Its ecosystem uses Minecraft protocol, data, physics, windows, recipes, and optional separate viewers. [Mineflayer README](https://github.com/PrismarineJS/mineflayer), [Mineflayer API](https://github.com/PrismarineJS/mineflayer/blob/master/docs/api.md)

**Fact:** The Prismarine Forge protocol plugin describes FML handshake and automatic mod detection/presentation. It does not claim to load the mods' client implementations. **Inference:** successfully joining a Forge server through that plugin is insufficient evidence for modpack playability. [Forge protocol plugin](https://github.com/PrismarineJS/node-minecraft-protocol-forge)

**Fact:** Voyager builds on Mineflayer; its README gives a tested Fabric 1.19 configuration and a creative/peaceful, cheats-enabled setup. **Inference:** it is a useful agent architecture precedent, not a drop-in strict-survival arbitrary-modpack client controller. [Voyager repository](https://github.com/MineDojo/Voyager)

### Leads checked, not adopted

**M1 — Machine One AI Interface. Fact:** its author advertises a real-client localhost text interface for modern loaders/versions, widget descriptions, pathfinding and other semantic commands. The page acknowledges hand-drawn GUI coverage gaps; it also documents one fixed port/client at a time, all-around living-entity perception, and an ARR license. **Inference:** “real client” does not establish pixel-observation or keyboard/mouse parity, and these are material N-player, fairness, compatibility, and reuse gates. [Author's M1 listing and manual](https://modrinth.com/mod/m1-machine-one-ai-interface)

Source spot-check at commit `f85e4597bb2c4295c4af970ba53c9727551d18d1`: `KeyInputAction` directly sets Minecraft movement mappings. `ScreenOps.openpack` searches a mapping name for “backpack”, temporarily rebinds it to an F13–F24 scratch key, clicks it, then restores the original binding; the scratch search falls back to F24 if none is free. **Inference:** this implementation is specifically unsuitable as proof of raw-input parity or a safe generic conflict allocator. It is a useful design lead requiring audit, permission-compatible reuse, and a reduced surface. [M1 KeyInputAction](https://github.com/Kishku7/m1/blob/f85e4597bb2c4295c4af970ba53c9727551d18d1/_codegen/cog_sources/shared/com/kishku7/m1/KeyInputAction.java), [M1 ScreenOps](https://github.com/Kishku7/m1/blob/f85e4597bb2c4295c4af970ba53c9727551d18d1/_codegen/cog_sources/shared/com/kishku7/m1/ScreenOps.java#L1197)

**Gemini Minecraft AI Companion. Fact:** its README targets Fabric 1.21.1 and advertises rich world/inventory/scanning plus command/build-plan execution and screenshot tools. The inspected server source exposes authenticated loopback routes including execute-commands, execute-build-plan, and capture-view. **Inference:** loopback authentication is useful, but this is a semantic assistant/control surface, not established physical-input parity for arbitrary Forge packs. No runtime test was done. [Project README](https://github.com/aaronaalmendarez/gemini-minecraft), [Pinned bridge source](https://github.com/aaronaalmendarez/gemini-minecraft/blob/39b118ff82dea1b72f8367e3d4ae3c12b979650e/src/main/java/com/aaron/gemini/McpBridgeServer.java)

**Steve (YuvDwi/Steve). Fact:** the project documents Forge 1.20.1, custom PathfinderMob-derived agents, structured mining/building/pathfinding actions, and lists crafting as not yet implemented. **Inference:** this is an NPC-agent architecture lead, not a full human-player client-input bridge. Claims about multi-agent behavior and modpack coverage need testing rather than acceptance from the README. [Steve repository](https://github.com/YuvDwi/Steve)

None of these leads establishes support for the user's eventual exact pack, and none was installed. M1's source branch and the Gemini commit were resolved through their public repository APIs; branch names, advertised versions, and licenses should be rechecked before implementation.

## Proposed input parity and information boundary

The strict track's parity target is **the same observable outcome and input-consumer behavior for the same physical input trace**, allowing documented capture/injection latency. It is not merely that a server accepted a movement packet.

The bridge/control adapter must pass presses, holds, releases, modifiers, repeats, mouse buttons, wheel, captured relative motion, and GUI cursor motion through the applicable ordinary input path. Chords press modifier(s), then base key; release base key, then modifiers. Text enters the normal active field at a fixed, declared rate; it must not call arbitrary widget setters. A screenshot comes from the actual client's rendered frame. Mouse-look must remain relative input, rather than a world-space look-at or direct yaw/pitch setter.

**Fact supporting the gate:** LWJGL2 exposes both buffered events and polled state; GLFW also separates callbacks and cached polling state. **Inference:** synthesizing one layer alone can leave another layer inconsistent. [LWJGL2 Keyboard API source](https://github.com/LWJGL/lwjgl/blob/master/src/java/org/lwjgl/input/Keyboard.java), [GLFW input guide](https://www.glfw.org/docs/latest/input_guide.html)

**Proposal: three separated capabilities, enforced by processes/credentials/ACLs, not only prompts:**

1. **Agent runtime:** current client pixels, optional declared audio, own input receipts, public frozen binding manifest, and ordinary allowed player chat. No block/entity scan, inventory NBT, hidden slot contents, world coordinates unless rendered, widget tree, recipe query, private goals, server console, world saves, or evaluator logs. A pixel-derived OCR tool can be a separate declared observation convenience; it must not silently use engine metadata.
2. **Setup/controller:** exact instance/mod/library fingerprints; binding registration/configuration metadata; test fixture access; mapping save/restore. No changes while the scored episode is active. A profile update ends the episode and produces a new profile hash.
3. **Evaluator:** privileged authoritative telemetry and scoring data, with a separate token, endpoint, OS identity/storage, and network policy. Its observations never return through an agent-accessible tool, exception, screenshot overlay, log, or shared working directory. The agent cannot inspect its own server process, attach a debugger, or read save files using a generic shell.

Server-side non-operator permissions and an explicit command allowlist enforce the gameplay contract even if the agent types commands through raw keys. Do not rely on hiding an `execute_command` tool while leaving the same privilege accessible in chat. Agent-authored reusable macros may replay only ordinary input traces under the same timing/observation budget; macros supplied by the environment may not solve semantic tasks on the agent's behalf.

Expose diagnostics such as binding-handler counts only to setup/evaluator during fixtures. Gameplay receipts say what input was delivered, not which hidden entity was hit or whether a private objective succeeded.

## Proposed multi-client isolation and recovery

**Fact:** Windows SendInput writes to the input stream, has no target-window argument, is constrained by integrity levels, and does not reset already-held keys. [SendInput documentation](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-sendinput)

**Proposal:** Do not run N simultaneously active OS-input agents by merely opening N windows on one desktop. Use one independently controlled display/session/VM per reference client, with its own instance directory and input/capture adapter. Container/process separation alone is not input-focus isolation. If a single desktop is used for a development demonstration, serialize exclusive focus leases and release every held input before changing focus; label it as serialized rather than simultaneous N-player control.

For a future per-process bridge, use distinct loopback endpoints or named pipes, unpredictable per-client credentials, explicit `client_id`, process/start identifier, epoch, and a single active controller lease. Bind each frame stream and input queue to the same client identity. Never infer identity from window title or a fixed port. Reject cross-client and stale-epoch messages before queuing them. A local endpoint is still accessible to other local processes unless OS isolation/credentials prevent it.

**Fact:** GLFW emits synthetic key/button releases on focus loss. LWJGL2's Windows keyboard also has release-on-focus-loss logic. These behaviors support recovery but are not substitutes for an independent watchdog. [GLFW window focus reference](https://www.glfw.org/docs/latest/group__window.html), [LWJGL2 WindowsKeyboard](https://github.com/LWJGL/lwjgl/blob/master/src/java/org/lwjgl/opengl/WindowsKeyboard.java#L115)

**Proposal:** Every down event has an expiry lease; a watchdog, independent of the model, tracks all held keys/buttons. Proposed starting limits: 1,000 ms maximum hold lease, renewal before expiry, 250 ms heartbeat, 1,000 ms heartbeat timeout. Tune and publish these numbers after latency tests. Releasing a lease is idempotent. If the model disconnects, the queue stalls, focus is lost, the world changes, the client dies, or the run is cancelled: stop accepting input, cancel queued events, release everything, and require an explicit new epoch before resuming.

Use both an external process watchdog and an in-client expiry check. A hung game thread cannot execute a release immediately; the expiry check must run **before further gameplay input/ticks on resumption**, and the supervisor marks the episode interrupted if the bound cannot be honored. Do not claim a hard in-world release deadline during a total process hang. New client processes start with empty queues and released state; do not replay old held inputs after reconnect. Preserve incident logs for evaluation and never silently rewind world state to erase an agent failure.

Separate gamepad/IME/human input from the benchmark runtime, or detect it and invalidate the episode. Standardize resolution, GUI scale, FOV, sensitivity, raw-mouse setting, frame/tick policy, and accessibility options. Include them in the profile fingerprint because they change action meaning and visual difficulty.

## Proposed Dovetail skill workflow

This is a skill contract for the SPEC writer. Its future implementation needs version adapters, host control tools, and schema validation; the prose alone is not an executable remapper.

### Entry and outputs

Trigger for preparing/troubleshooting controls of a **specific local Minecraft instance**, including conflicting modpack hotkeys. Inputs: instance identity, Minecraft/loader/runtime/modpack hashes, OS/backend/layout, required actions, explicitly protected bindings, reserved host shortcuts, approved optional unbindings, and test fixture identity. Default operation is discover/plan; apply is allowed when the caller has requested remapping/setup and the instance is in setup mode. This research task authorizes no application.

Outputs: discovery manifest, capability test matrix, deterministic binding plan/diff, backup hashes and journal, applied profile, verification report, rollback report when needed, and a short agent-facing control card. Unknown mappings are reported; they are not renamed, guessed from localization text, or invoked to see what happens in a scored world.

### Discover -> plan -> apply -> verify -> rollback

1. **Discover:** resolve the real instance directory and process/library fingerprints. Wait until mod registration finishes. Enumerate bindings with translation key, category, owner evidence, current/default typed key, raw persisted string, modifier, context class/identity, and consumer type if known. Translation strings can collide or omit a mod namespace: identity must include occurrence/owner evidence, and ambiguous records block mutation. Inventory mod-owned hotkey configs and raw input consumers where documented. Snapshot exact options/config bytes and hashes before any modification. Capture the controls UI as corroboration, not the sole source of truth.
2. **Probe candidates:** in a disposable fixture, use the production injector to record press, held-state, repeat behavior, release, context, and visible response. Extended function keys, mouse buttons, and modifiers enter the usable pool only after success. Test the actual host layout and reserve escape/recovery plus host shortcuts; avoid function-key debug combinations and destructive shortcuts. Do not add arbitrary integers or character codes.
3. **Plan:** build a conflict graph from runtime conflict relations plus overlapping raw consumers and observed behavior. Preserve protected controls and minimize changes. Prefer free proven base keys, then proven single-modifier chords on base keys without overlapping unmodified actions. Reuse a key across disjoint contexts only with evidence. Treat unknown contexts as overlapping. Deterministically allocate by stable identity and fixed candidate ordering. If capacity is insufficient, return `UNRESOLVED_CAPACITY` with affected mappings; never reuse an occupied fallback or silently drop actions. Produce before/after diff and required verification cases.
4. **Apply transaction:** assert setup mode, exact precondition hashes, exclusive profile lock, released input state, and no scored episode. Use client mapping setters on the client thread, rebuild lookup structures as required by that version, and persist using its native settings writer; alternatively patch only the specific key entries with the client fully stopped. Do not edit a live options file behind the client's in-memory state. Journal before/after values and owned paths. Do not modify conflict contexts or mod code. Prevent another launcher/profile writer from racing the transaction.
5. **Verify:** read back runtime and persisted records, restart the exact client, reread, and exercise every changed required action through the production raw-input path. Assert intended effect, no unintended co-trigger, complete release, persistence, and basic controls still working. Exercise in-game, inventory/container, chat/search, mod GUI, and relevant custom contexts. Configuration-only success is insufficient. Freeze a verified profile only if all required checks pass; otherwise report partial/failed status accurately.
6. **Rollback:** on a failed apply or verification, release all input and restore the transaction-owned values/files while the writer is stopped or through the same safe adapter. Restore byte-identical backups when no later changes exist. If files changed independently, perform a narrowly owned compare-and-swap restore or stop with `ROLLBACK_CONFLICT`; do not overwrite unrelated new user settings. Reopen/restart and confirm runtime/persistence. An interrupted transaction is discovered from the journal at next startup before accepting gameplay input.

A mapping can be valid without a harmless visible test effect in an empty fixture (for example, an ability requiring equipment). Mark it `unverified_context` and supply the missing equipment/screen prerequisite; do not call it fully verified. Keybinding IDs are setup metadata, not runtime action handles. The agent control card maps a human action description to an explicit frozen physical chord.

### Machine contract (proposed)

All records use UTF-8 JSON. JSON numbers carrying keycodes are namespaced by `kind`; arbitrary non-enumerated keys are rejected. Paths belong to the authorized instance. Unknown schema versions, unsupported adapters, or missing required checks fail closed. Example profile, with illustrative values rather than discovered user settings:

```json
{
  "schema_version": "dovetail.minecraft.controls/v1",
  "profile_id": "example-profile",
  "status": "planned",
  "instance": {
    "instance_id": "client-a",
    "minecraft": "1.20.1",
    "loader": "forge",
    "loader_version": "EXACT_VERSION",
    "modpack_sha256": "REQUIRED_SHA256",
    "runtime_fingerprint": "REQUIRED_SHA256",
    "platform": "windows",
    "keyboard_layout": "DECLARED_LAYOUT",
    "adapter": "os-input-reference/v1"
  },
  "observation_contract": "pixels-input/v1",
  "discovery_sha256": "REQUIRED_SHA256",
  "precondition_files": [
    {"relative_path": "options.txt", "sha256": "REQUIRED_SHA256"}
  ],
  "bindings": [
    {
      "binding_id": "owner:translation-key:0",
      "translation_key": "key.examplemod.open",
      "category": "key.categories.examplemod",
      "owner": {"mod_id": "examplemod", "evidence": "registration-adapter"},
      "context": {"id": "IN_GAME", "class": "VERSION_SPECIFIC_CLASS", "confidence": "known"},
      "consumer": "registered_mapping",
      "protected": false,
      "required": true,
      "before": {"kind": "glfw_keysym", "code": 66, "name": "B", "modifier": "NONE", "persisted": "key.keyboard.b"},
      "after": {"kind": "glfw_keysym", "code": 302, "name": "F13", "modifier": "NONE", "persisted": "key.keyboard.f13"},
      "injector_key": {"kind": "windows_scancode", "code": 100, "extended": false},
      "candidate_evidence_id": "fixture-input-F13",
      "verification": {"status": "not_run", "test_ids": ["open-in-game", "release", "restart"]}
    }
  ],
  "unresolved": [],
  "transaction": {"id": "example-tx", "state": "planned", "backup_manifest_sha256": null},
  "profile_sha256": null
}
```

A concrete JSON Schema for the `before`/`after` key-value records (the adapter additionally checks its observed capability allowlist):

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:dovetail:minecraft:binding-key:v1",
  "type": "object",
  "additionalProperties": false,
  "required": ["kind", "code", "name", "modifier", "persisted"],
  "properties": {
    "kind": {"enum": ["lwjgl2_key", "glfw_keysym", "glfw_scancode", "mouse_button", "unbound"]},
    "code": {"type": ["integer", "null"]},
    "name": {"type": "string", "minLength": 1},
    "modifier": {"enum": ["NONE", "SHIFT", "CONTROL", "ALT"]},
    "persisted": {"type": "string", "minLength": 1}
  },
  "allOf": [
    {
      "if": {"properties": {"kind": {"const": "unbound"}}},
      "then": {"properties": {"code": {"type": "null"}, "modifier": {"const": "NONE"}}},
      "else": {"properties": {"code": {"type": "integer", "minimum": 0}}}
    },
    {
      "if": {"properties": {"kind": {"const": "lwjgl2_key"}}},
      "then": {"properties": {"code": {"minimum": 1, "maximum": 255}}}
    }
  ]
}
```

The normalized `mouse_button` code is a zero-based button index; legacy negative options-file encoding remains in `persisted` and is handled by the adapter. The schema intentionally does not equate integer validity with delivery capability. Define additional adapter key kinds in a new schema version if a later Minecraft release changes its input model.

Normative field rules for the enclosing profile and transaction schemas:

| Record | Required rules |
|---|---|
| Profile | Exact schema version; status enum `discovered / planned / applying / verified / failed / rolled_back / rollback_conflict`; fingerprint fields required before planning. Hashes are actual 64-character SHA-256 strings, not the example placeholders. |
| Binding identity | Nonempty unique `binding_id`; translation key and owner evidence recorded separately; ambiguous owner/duplicate identity blocks apply. |
| Key | Tagged union: `lwjgl2_key`, `glfw_keysym`, `glfw_scancode`, `mouse_button`, or `unbound`; code range validated by adapter's observed capability table, not just schema integer limits. `modifier` is `NONE / SHIFT / CONTROL / ALT` for the examined Forge adapters. An unbound key has null code and explicit plan authorization. |
| Context | `known / custom / unknown`; include adapter-reported identity/class. Runtime overlap is evidence, not derivable from a friendly label alone. |
| Consumer | `registered_mapping / raw_poll / custom_gui / mod_config / unknown`; runtime probe evidence for every changed required consumer. |
| Verification | `not_run / passed / failed / unverified_context / unsupported`; each test has before/after frame IDs, event receipt IDs, expected/actual result, timestamp, adapter/runtime hashes. Privileged handler diagnostics stored outside agent observations. |
| Plan | Deterministic digest of before/after records, precondition hashes, constraints, and evidence IDs; unknown fields rejected for mutation requests. |
| Transaction | `planned / backed_up / mutated / persisted / verified / reverting / rolled_back / rollback_conflict`; crash recovery uses durable transitions and file hashes. |

Operations and access control:

| Operation | Capability | Success result / failure behavior |
|---|---|---|
| `controls.discover(instance)` | Setup read | Full manifest plus completeness/unknowns; never silently assumes raw consumers absent. |
| `controls.plan(discovery_hash, constraints)` | Setup read | Plan hash, diff, unresolved list, required tests. No mutation. |
| `controls.apply(plan_hash, expected_files)` | Setup write | Transaction ID and post-apply records; stale hashes return `STALE_DISCOVERY` without writes. |
| `controls.verify(transaction_id, fixture_id)` | Setup test | Required test matrix and restart evidence; failure initiates configured rollback. |
| `controls.rollback(transaction_id)` | Setup write | Verified restoration or explicit conflict; safe to retry. |
| `controls.export(profile_hash)` | Setup/runtime read | Frozen public physical-control card only. |

Suggested runtime envelope for the eventual controller, independent of the setup skill:

```json
{
  "schema_version": "dovetail.minecraft.input/v1",
  "client_id": "client-a",
  "epoch": "PROCESS_START_NONCE",
  "lease_id": "CONTROLLER_LEASE",
  "seq": 42,
  "profile_sha256": "REQUIRED_SHA256",
  "expires_after_ms": 500,
  "events": [
    {"offset_ms": 0, "type": "key_down", "key": "F13"},
    {"offset_ms": 100, "type": "key_up", "key": "F13"}
  ]
}
```

Allowed event union: `key_down`, `key_up`, `mouse_button_down`, `mouse_button_up`, `mouse_move_relative`, `mouse_move_gui`, `wheel`, `text_input`, `release_all`. Each has a versioned schema with `additionalProperties: false`, finite/range-limited arguments, bounded event counts, and no entity/block/widget/binding targets. Relative motion and GUI positions declare units and frame geometry; GUI actions can carry a frame ID for stale-frame rejection. A profile manifest resolves canonical key tokens to the tested backend encoding. Do not accept user-supplied numeric native codes during gameplay.

The receipt contains client/epoch/sequence, `accepted / applied / released / rejected / interrupted`, monotonic dispatch times, and optional next frame ID. Repeated identical sequence numbers return the prior receipt; a different payload with the same sequence fails. Expired messages never execute. Acknowledging queue acceptance does not claim application or gameplay success. Receipts and captured frames must have explicit causal timestamps; do not label an old frame “after action.”

## Feasibility gates and proposed tests

These are future acceptance tests, not tests performed by this research.

| Gate | Required evidence |
|---|---|
| G0: exact runtime | Minecraft, loader, Java, LWJGL/GLFW/native hashes, pack/mod/config hashes, OS/display/input adapter recorded. No “all Forge versions” claim. |
| G1: physical event delivery | For every allowed key/button: production-injector down/hold/up observed at library event and polling layers, loader input handlers, registered binding, and visible fixture effect. Test repeats and simultaneous chords. Modern F13–F24 and legacy F13–F15 tested independently; unsupported F16+ legacy candidates rejected. |
| G2: full content/UI route | Fixture plus selected real pack cover modded container, custom drawn GUI, search/text field, raw polling consumer, held-use ability, mouse-look, wheel, drag/drop, focus/cursor capture, and GUI scaling. Direct mapping activation is not substituted when raw input fails. |
| G3: conflict correctness | Two bindings on one key, GUI vs IN_GAME, UNIVERSAL, custom overlapping and disjoint contexts, modifier base-key conflicts, unmodified+modified in-game action, duplicate translation keys, and mod-owned config. Verify intended action count and absence of unintended effect. |
| G4: persistence/rollback | Restart preserves approved keys/modifiers. Simulate crash at each transaction state; recover or restore. Edit an unrelated setting concurrently and prove no overwrite. Added/removed/updated mods and modified options invalidate the plan. Running twice produces no new changes. |
| G5: capacity/fallback | Fill the candidate pool; allocator returns unresolved capacity. It must never fall back to an occupied key or unbind required controls. Unknown contexts stay conservative. |
| G6: isolation at N | Concurrent clients press different keys and perform opposite mouse motions; no other client's state/frame changes. Inject wrong client IDs/tokens/epochs; reject. Steal focus and prove the reference adapter stops. Measure frame freshness under GPU/CPU load. |
| G7: stuck-input recovery | Kill model, controller, bridge, socket, and client separately during movement/use/chord; stall game thread; disconnect/rejoin; open GUI; change worlds. Confirm release deadline or explicit interrupted episode, no replay, no stale lease, and new-process empty state. |
| G8: observation secrecy | Place known hidden blocks/containers and private evaluator canaries; inspect every response, log, exception, frame, endpoint, filesystem permission, and generic-tool capability. No metadata or evaluator state crosses into runtime. Audit dependencies for auto-equip/pathfinding/scan behavior. |
| G9: reference equivalence | Feed the same trace through OS reference and candidate bridge on cloned fixtures. Compare downstream input logs, visible transitions, and authoritative outcomes under declared latency tolerances. Demonstrate both success and expected failure cases. |
| G10: human reproducibility | A human can use the exported bindings and reproduce each control through the same input path; extended keys are accessible through the same declared virtual keyboard/device if absent on their hardware. Freeze any allowed macros and rates equally. |

**Unknowns:** No chosen modpack list, concrete controller tool capability set, installed library overrides, display-isolation host topology, or target N was provided to this subtask. GPU/session cost, screenshot throughput, mod raw-input quirks, and human-input equivalence of a client bridge remain measurements. A complete client may run arbitrary content mods, but this does not prove an agent can perceive or solve every task, or that every input hook interoperates. Publish tested tuples and failures.

**Suggested sequence:** select one exact legacy or modern target; build the OS-input reference and a harmless input fixture; validate the capability catalog; prototype the setup skill; validate two simultaneous clients; then evaluate the narrow bridge against the same trace suite. Existing semantic projects remain optional baselines until their contracts and coverage are independently verified.
