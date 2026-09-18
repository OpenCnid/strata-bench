# Strata

**A Minecraft benchmark for long-horizon agent adaptation.**

Strata studies how agents learn from experience during extended Minecraft playthroughs, progressing toward increasingly complex modpacks. Each agent uses Dovetail, with Mineflayer as the first character-control backend.

Repository: [OpenCnid/strata-bench](https://github.com/OpenCnid/strata-bench). **Status: specification and research; implementation has not started.**

Research baseline 2026-09-17; architecture updated 2026-09-18. Default integration: **Codex CLI → local mcgame command/IPC → persistent Mineflayer worker**; MCP is optional. Confirmed choices: **Mineflayer as the first character-control backend**, **CurseForge + Forge** and **[OpenCnid/dovetail-codex](https://github.com/OpenCnid/dovetail-codex)**.

- [Specification](SPEC.md): authoritative v0.2.0 contract; structured observations/actions through Mineflayer first, with exact Forge-modpack compatibility gates.
- [Milestones](MILESTONES.md): requirements, feature coverage and remaining implementation/tests.
- [Project instructions](AGENTS.md): work process and scope-preservation rules.
- [Build plan](BUILD_PLAN.md): recommended architecture, measurement protocol, stack, compatibility strategy, hotkey skill, and staged acceptance gates.
- [Fresh-session specification prompt](SPEC_PROMPT.md): copy the marked prompt into a new design session to produce an implementation-ready `SPEC.md` without needing the original conversation.

Supporting investigations:

| Report | Focus |
|---|---|
| [Mineflayer backend decision](research/mineflayer-backend.md) | Current architecture, reuse candidates, Forge risks and initial acceptance tests |
| [Benchmark design](research/benchmark-design.md) | Prior work, adaptation metrics, controls, transfer, team fairness, graduation |
| [Modpack runtime](research/modpack-runtime.md) | Released artifacts, installation, expert mode, identities, multi-client resources, recovery |
| [Control and keybindings](research/control-keybindings.md) | Full-client input, existing modded interfaces, keycode limitations, proposed skill and test contracts |
| [Dovetail integration](research/dovetail-integration.md) | Confirmed Codex plugin, inspected revision, host adapter, isolated state |
| [Handoff review](research/handoff-review.md) | Independent case review and revision disposition |

SPEC.md is authoritative; the build plan and prompt reflect user decision D01. Earlier research reports retain historical proposals, with explicit supersession notices. Mineflayer is selected, not implemented: all runtime/pack gates remain open. All implementation and compatibility claims remain gated by real tests. No game was installed, no scored agent playthrough was run, and no runtime benchmark result is claimed.

These are public **operator/design documents**. Public availability does not make them permitted gameplay-agent input: exclude this repository from gameplay-agent workspaces and retrieval sources because it describes the measurement objective and evaluation design. Live credentials, run data, private evaluator material and sealed fixtures must remain outside the public repository.
