# Dovetail integration findings

> Architecture update, 2026-09-18 (D01): the user selected Mineflayer as the first control backend, with structured observations/actions. Direct Codex CLI/local commands are the default (D02); MCP and app-server are optional. Full-client-first proposals and prior review conclusions below are historical. Use [SPEC.md](../SPEC.md), [MILESTONES.md](../MILESTONES.md), and the [Mineflayer decision](mineflayer-backend.md) for current contracts and gates; source findings remain supporting evidence.

Research date: 2026-09-17. This is a proposed integration, not an executed compatibility test.

## Confirmed source and verified evidence

- The user explicitly selected **[OpenCnid/dovetail-codex](https://github.com/OpenCnid/dovetail-codex)** and confirmed CurseForge + Forge. The remote repository contains the native Codex plugin, unlike the older local sibling checkout. `git ls-remote` returned `15c306ccfef28eb5f616fadcd5fd8eac0663e361`; the inspected [pinned manifest](https://github.com/OpenCnid/dovetail-codex/blob/15c306ccfef28eb5f616fadcd5fd8eac0663e361/.codex-plugin/plugin.json) declares version `0.4.1` and `skills: "./skills/"`.
- [The Codex self-play skill](https://github.com/OpenCnid/dovetail-codex/blob/15c306ccfef28eb5f616fadcd5fd8eac0663e361/skills/self-play/SKILL.md) separates artifact creation and evaluation, uses clean-context helpers, and distinguishes conversation isolation from filesystem isolation. This differs from adversarial Minecraft matches or weight training.
- [The port's surface map](https://github.com/OpenCnid/dovetail-codex/blob/15c306ccfef28eb5f616fadcd5fd8eac0663e361/docs/codex-surface-map.md) records its earlier Codex CLI validation baseline. Current behavior must be retested against the implementation's pinned binary.
- The local sibling checkout is at `6ac845535065a05a8fce6cde61c8c64ceffdd92e` with untracked calibration material. It was inspected read-only and not updated. Its `2026-09-02-codex/README.md` and `MAP.md` do not describe the current remote plugin distribution.
- The upstream [generic Dovetail](https://github.com/OpenCnid/dovetail) and [DeepSeek port](https://github.com/OpenCnid/deepseek-dovetail) provide lineage and portability context, not substitutes for the user's selected repository.

## Codex host seam

Official [app-server documentation](https://learn.chatgpt.com/docs/app-server) describes stdio transport, initialization, session/turn lifecycle, and generated protocol schemas. [Noninteractive mode](https://learn.chatgpt.com/docs/non-interactive-mode) documents JSONL output for bounded exec jobs. Local read-only checks returned `codex-cli 0.154.0-alpha.6.2`; its app-server help exposes stdio and schema-generation commands and labels the feature experimental. No agent job or game integration was executed.

Use pinned app-server stdio as the campaign integration candidate and exec JSONL for bounded evaluation jobs. Generate/inspect the exact installed protocol before coding against it. Prove native plugin discovery, image observations, scoped MCP tools, helper lifecycle, token accounting, interruption, and restore in an isolated test profile. Do not infer that every tool available in the Desktop application is also present in a headless worker. Missing capabilities must fail preflight or take an explicitly validated alternative path.

## Recommended integration

Treat an experimental agent as `(model, host runtime, Dovetail revision, initial skills, permitted tools, adaptation state, resource budget)`. Model name alone cannot identify the tested system.

Define a host-neutral adapter with proposed operations `start`, `submit_observation`, `poll_events`, `interrupt`, `checkpoint`, `resume`, and `stop`. These are new harness contracts, not claims about existing Dovetail methods. Implement Codex first, after demonstrating the required surfaces. Add other hosts only through explicit ports and conformance tests.

Each embodied agent receives a separate identity, workspace, memory namespace, adaptive skill store, observation/action capability, and budget ledger. Its reasoning helpers are separate from Minecraft player slots. Allow helpers to propose actions or critique plans, but only the avatar's designated executor may submit input. Delegated calls, retries, self-play, research, and practice worlds count toward the owning agent/team budget.

Keep the initial Dovetail source immutable and retain proposed learned skills as versioned overlays. Record additions, revisions, reads, rollbacks, provenance, and retention policy. At provider/host changes, either start a new cohort or label transfer explicitly. A provider alias that changes mid-campaign must not silently masquerade as one fixed model.

Self-play may assess a proposed plan or learned procedure using observations the agent actually obtained. Helpers cannot access hidden benchmark scoring, private test worlds, other experimental arms, or sibling memories unless the communication policy expressly allows them. Physical isolation is required where secrecy matters; a fresh conversation alone does not isolate files, tools, network access, or inherited skill catalogs.

Memory and learned-skill behavior must be measurable rather than assumed from successful skill loading. Preflight should verify that the intended skill body is available and usable in the actual host. Capture neutral session handoffs and compaction policies consistently across experimental arms. Runtime-specific explicit-only workflows need an explicit, documented invocation policy rather than silent host-dependent activation.

## Remaining verification

Repository, initial host family, and installer are settled. Exact Codex build, provider/model support, authentication, plugin installation into isolated worker profiles, child-agent tool parity, and complete usage/checkpoint capture remain Phase 0 validation work. Successful manifest inspection is not proof of working game-agent behavior.
