# M1/G1 fresh-session handoff

The user requested a checkpoint PR merged to main, then continuation in a fresh
session. **This is a handoff, not M1/G1 completion.** The current session should
stop implementation after publishing the checkpoint. M0 is verified; G0 passes
only its named D14 development slice. M1 is `in_progress`; G1 and every complete
T01/T04/T05/T06/T10/T11 suite remain `not_run`.

## Resume in this order

1. Read [AGENTS](../AGENTS.md), [STATUS](STATUS.md), this handoff,
   [the dated checkpoint](verification/2026-09-27-session-handoff.md),
   [MILESTONES](../MILESTONES.md) and applicable [SPEC](../SPEC.md) contracts,
   especially sections 3, 8, 11, 15–19. Follow the
   [opening profile audit](verification/2026-09-24-g1-coverage-audit.md) and
   [G0 assembly](verification/2026-09-24-g0-assembly.md) /
   [child dispositions](verification/2026-09-24-g0-child-dispositions.md) as needed.
2. Fetch origin, verify the actual checkpoint PR is merged and its implementation
   is present on main, preserve existing changes and branch from updated main.
   Do not assume a local branch name or this document proves remote state.
3. Recheck the durable authority database with WAL-aware read-only access,
   unresolved telemetry holds, installed hashes and actual process inventory.
   Historical locks/files do not establish that a process is live.
4. Continue the connected repair/accounting workflow below, then complete every
   remaining G1 suite. Keep unrelated M2–M7 work untouched. Do not restart G0,
   repeat unchanged suites or run another authentic trial for a lucky result.

## Next implementation work

The visible target is ordinary play → conflict diagnosis → owned pause → repair
→ same-server client restart → intended/competing and essential-control checks →
complete accounting → commit or verified restoration → resumed gameplay.

Current focus is **M1.1c.3.4**. Finish active/reserved wall and disconnected-time
allocation, complete the consumption/settlement join, and restore the original
worker lease/history through the controller. Generic `Reconfigurations.finish`
correctly refuses worker-backed repairs; do not bypass it with a fabricated ready
receipt or silently mint a different native lease. Restored rollback requires
its own actual effect verification. Repeated repair chains and capability/skill
qualification remain unfinished.

Relevant implementation:

| Component | What is present; what it cannot prove |
|---|---|
| `src/mcbench/reconfiguration.py`, `native_repair_flow.py`, `native_repair_restart.py` | Owned repair request/pause/admission and replacement integration; generic completion cannot certify native resume. |
| `src/mcbench/native_repair_resume.py`, `repair_inference.py` | Frozen settled inference prerequisite; original decisions/status-only reconciliation; measured primitive floors and stored publication evidence. Full settlement and campaign permission remain false. |
| `src/mcbench/worker_publication.py`; `backends/mineflayer/src/journal.ts`, `forge_lane.ts` | Worker/6 keeps the public hold through native resume, records the publication boundary and exposes historical accounting privately. An arbitrary settlement reference is not certified by the worker. |
| `evaluator/src/strata_evaluator/body_ticks.py` | Continuous full-roster tick reservations and pre-request/post-publication coverage. No exact per-repair tick split, wall/disconnected time, terminal tail or full-accounting claim. |
| `evaluator/src/strata_evaluator/bound_clocks.py`, `repair_clocks.py`, `live_clocks.py` | Held authenticated source/roster, causal sample barriers and partial repair marks. These do not replace complete time coverage or qualified isolation. |

Latest implementation commits and retained evidence:

- `b483f4d`: [inference-gated resume](verification/2026-09-27-m1-resume-inference.md).
- `c1d3055`: [immutable publication retrieval](verification/2026-09-27-m1-publication-receipt.md).
- `07737f3`: [continuous body-tick allocation](verification/2026-09-27-m1-body-tick-window.md).

The most recent focused checks were 51 Python cases plus one actual JVM/private
pipe case. The latter uses synthetic game/setup/roster/token qualification and
does not prove pre-request repair coverage. Earlier source and process failures
are retained in their reports. Read the dated checkpoint for merge-wide results.

## Authentic game evidence and blocking failure

The narrow [Curios E/F13 cycle](verification/2026-09-27-m1-settings-cycle-plan.md)
passed conflict/effects, same-server restart, repeated checks and exact rollback
restoration: 13 effects, eight frames, 355 primitives. It does not close T05 or
qualify the current complete Worker/6 workflow.

The later [essential-controls native04](verification/2026-09-27-m1-essential-native.md)
failed after admission during its first overlap effect. It retained six primitive
charges and only 1/20 required released observations; no patch or restart ran.
Guardian failure was `PROCESS_NATIVE_HEALTH_TIMEOUT` under the unchanged 750-ms
policy; diagnostic elapsed time was 1,438 ms. The concurrent status read was
469/500 ms, and the precise client-thread-delay cause is unproven. Tree termination
was 668.7582 ms within D13's 1,000-ms bound; normal-stop acceptance still failed.
Do not confuse termination success with successful gameplay or normal shutdown.

Diagnose the retained source/journals before selecting changed verification.
Do not relax the health bound, clear uncertainty, reuse consumed decisions or
repeat the unchanged attempt. All client/server processes were terminal at that
checkpoint; check current state afresh.

## Other required G1 work

[STATUS](STATUS.md) lists every remaining suite. In particular, do not let repair
work obscure final root/helper isolation, native selected-skill integration,
protected scorer controls and matched probe disposal/reset. Useful evidence:

- [Native boundary](verification/2026-09-24-m1-native-boundary.md),
  [native handoff](verification/2026-09-25-m1-native-handoff.md),
  [helper-disabled control](verification/2026-09-25-m1-no-self-play-native.md).
- [Scorer coverage](verification/2026-09-26-m1-scorer-coverage.md) and
  [authentic low-energy control](verification/2026-09-26-m1-low-energy-native.md).
- [Matched retention](verification/2026-09-25-m1-matched-retention.md) and
  [probe custody](verification/2026-09-25-m1-probe-custody.md).

These are named partial scopes, not interchangeable exact-profile certificates.

## Durable authority and private state

D20 authorizes complete M1/G1 implementation/scripted conformance; no new scope
approval is needed for that work. D17 selects `gpt-6-luna`. D18/D19 remain M0-only:
**no M1 paid-inference allowance exists**. Ask only for genuinely missing bounded
paid authority when the proposed verification is concrete and ready. Continue
independent authorized work in the meantime.

Read-only authority database:
`C:/Users/Darian/.strata/operator/provisioning/controller.sqlite`.
Last verified exposure: 4,887,796 microUSD, including the old 755,400 hold and four
full 1,000,000 failed-job envelopes. Forty authority tables were unchanged through
`07737f3`. D12 and all used pilots, including D19.11, stay consumed. Do not replay,
refund, rearm, duplicate child charges or interpret this as an exact OAuth bill.

Eight distinct telemetry reservations remain `RESERVED`, each 268,435,456 bytes,
with `actual_bytes` unknown. Their private evidence scopes are:

- `2026-09-26-m1-furnace-operation-10`
- `2026-09-27-m1-furnace-operation-15`
- `2026-09-27-m1-furnace-operation-16`
- `2026-09-27-m1-settings-cycle-native-02`
- `2026-09-27-m1-settings-cycle-native-03`
- `2026-09-27-m1-essential-native-01`
- `2026-09-27-m1-essential-native-03`
- `2026-09-27-m1-essential-native-04`

Each lives under `C:/Users/Darian/.strata/evidence/<scope>/reference.sqlite`.
The private `audit-state.py` in the latest sealed evidence roots compares the
authority, holds and installed hashes. Use a fresh output directory; never edit
sealed roots. Do not instantiate live budget services just to inspect authority.

## Installed versus built profiles

Installed development client: `C:/Users/Darian/.strata/clients/e9e-noninput-01`.
Client JAR SHA-256:
`e2c718506b078f529e92fd25e31068af7377b079e1b591b2488bf98f9797c41d`.
Options SHA-256:
`b967ff8fa4e6f1e179d17a9a03b53a1372955ef6fde31d144259249a1648e271`.
The installed native-input /6 profile has the retained essential-controls failure.
Built telemetry 0.3.19 / ServerStarted20 has source/JVM clock evidence, not changed
Minecraft-profile qualification. Building source does not install or qualify it.

Use this checkout's Python 3.12 environment, Node 24.19.0 and pinned Java
17.0.20.1+1. The isolated Python guardian must import this checkout, not another
worktree's editable install. The existing local `CodexSandboxUsers` group is the
writer fixture input; Builtin Users was previously refused. Build/test commands
and opt-in scope are in [README](../README.md). Run focused checks for changes;
no reason exists to repeat unchanged authentic or paid suites.

Operator source/docs, private evaluator inputs, account caches and raw evidence
must remain outside gameplay/root/helper contexts. Shared-desktop OS input is
paused. Fresh conversations, separate folders and separate desktops are not
filesystem/process/network qualification.

## History and next-session prompt

The complete previous rolling handoff remains in
[the archived handoff](archive/2026-09-27-m1-handoff-history.md); all ledger IDs,
failures and historical profiles remain in [MILESTONES](../MILESTONES.md).

Suggested continuation:

> Continue Strata M1/G1 from the merged September 27 checkpoint. Read AGENTS.md,
> docs/STATUS.md, docs/STATUS_AND_HANDOFF.md, the dated checkpoint, MILESTONES.md
> and applicable SPEC contracts. Verify the merged remote state and durable
> accounting/process state, preserve existing work and branch from updated main.
> Continue complete repair/accounting/controller integration and all remaining
> G1 contracts, native/keybinding, isolation, scorer and probe requirements. D20
> authority persists; D18/D19 remain M0-only. Preserve failures, profiles, holds
> and consumed decisions. Close M1/G1 only on complete applicable evidence.
