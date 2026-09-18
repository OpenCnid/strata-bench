# Mineflayer-first backend decision and supporting research

Date: 2026-09-18. Operator/design material; never mount into gameplay agents. Decision D01 is authorized by the user's request to use Mineflayer for character control and as the first backend. [SPEC.md](../SPEC.md) v0.2.0 is authoritative. This is documentation, not an implemented or tested backend.

D02 follows the user's request to connect directly to Codex CLI: use native command calls and a local JSON/IPC bridge; MCP is optional. [Official noninteractive documentation](https://learn.chatgpt.com/docs/non-interactive-mode) and local `codex exec --help` verify JSONL/resume command availability. Full plugin/helper/isolation conformance is still untested.

## Decision

Use one isolated Node.js/TypeScript Mineflayer worker per avatar, exposed through the scoped local game CLI to the native Dovetail-equipped agent loop. Primary track: `structured-actions/v1`. Structured own-player/inventory/open-container and bounded observed-world data replace mandatory screenshots; fixed local navigation/motor routines execute bounded decisions with event feedback and cancellation. Keep Python for campaign orchestration/research, Java for private Forge telemetry and optional client/settings extensions.

Separate declared gameplay state from private authoritative evaluation. Filter hidden chunk contents, unopened inventories and other players' private state. Navigation uses the same allowed observed map; unknown terrain is conservative. No direct bot object/JS evaluation/socket/admin access, teleportation, free items, recursive crafting planner or built-in progression solver. Model comparisons match backend, plugins, motor behavior, observations and budgets; all local action execution is recorded and charged.

## Existing implementations and reuse

| Primary source | Verified documentation finding | Use / limitation |
|---|---|---|
| [Mineflayer API](https://github.com/PrismarineJS/mineflayer/blob/master/docs/api.md) | Bot properties and methods cover game state, inventory, entities, movement and interactions. | Core control dependency; choose exact versions by conformance, not floating latest. |
| [mineflayer-pathfinder](https://github.com/PrismarineJS/mineflayer-pathfinder) | Local navigation plugin. | Pin and constrain to the declared observed-world/motor policy. No automatic resource collection. |
| [Mindcraft](https://github.com/mindcraft-bots/mindcraft), [MineCollab](https://github.com/mindcraft-bots/mindcraft/blob/develop/minecollab.md) | LLM Mineflayer agents and task/evaluation infrastructure, including cooperative tasks. | Main orchestration/benchmark reference. Preserve our native Dovetail loop and independent private evaluator rather than importing an entire agent loop. |
| [Mindcraft FAQ](https://github.com/mindcraft-bots/mindcraft/blob/develop/FAQ.md) | Mechanics-changing mods are explicitly unsupported. | No E9E compatibility inference. |
| [Voyager](https://github.com/MineDojo/Voyager) | Mineflayer integration, curriculum and persistent executable skills. | Learning-experiment reference; not evidence for expert-pack machine coverage. |
| [Minecraft MCP Server](https://github.com/yuniko-software/minecraft-mcp-server) | Existing MCP facade over Mineflayer. | Concrete wrapper reference; its documented game version differs from E9E. Review code/license and pin before reuse. |
| [Forge protocol plugin](https://github.com/PrismarineJS/node-minecraft-protocol-forge) | Documents Forge/FML negotiation support. | Handshake capability alone does not implement modded registries, custom packets, recipes, containers or machines. |

Source documents were inspected; dependencies were not installed and no code reuse or live compatibility was tested. Their public text may change. Preserve exact commits/licenses before implementation reuse.

## Initial acceptance and unresolved compatibility

1. Pin Mineflayer/Node/TypeScript/protocol/data/pathfinder and the action/observation policy; establish an isolated worker and structured CLI seam.
2. On vanilla, verify state delivery, move/mine/place/equip/use/craft/container actions, bounded cancellation, stop-all, reconnect, partial-effect/ambiguous-ack recovery and observation filtering.
3. Immediately test the pinned E9E distribution: Forge join and required channels, namespaced mod blocks/items/metadata, collision/navigation, an expert-altered recipe, inventory/container synchronization, a real operating modded machine and allowed quest/recipe information.
4. Record each unsupported mechanic by pack/backend version. Extend Mineflayer if feasible or qualify a structured Forge client backend; either way, preserve authentic mechanics. Never silently substitute a fallback or label it Mineflayer support. G0 needs real modded evidence; vanilla alone is partial.
5. Retain the required keybinding skill for a qualified settings extension. Stock Mineflayer advertises no client-mod keybinding capability. Typed rejection is a negative test, not full skill acceptance. T05/G1 still require real repair, competing-effect checks, rollback and persistence.

CurseForge + Forge remains the installation/distribution choice. Mineflayer is a protocol client, not an installation of the Forge client's Java mods. Optional rendered/OS-input reference profiles retain separate affordances and conformance. Every game, host, security, recovery, multi-agent and scientific gate remains not run.
