# M0 fresh-session handoff

**Resume M0 and its six G0 outcomes only. M0 is incomplete; G0 fails.**
The September 24 stopping request is to publish the accumulated source and updated
documentation, merge the PR, then continue in a fresh session. The merge does not
close any gate. Preserve M1–M7 and every failed trial.

## Read and establish state

1. Fetch origin/main and verify the PR in the [dated checkpoint](verification/2026-09-24-session-handoff.md).
   Preserve local changes and start a fresh implementation branch from updated main.
2. Read [AGENTS](../AGENTS.md), the [ledger's current position](../MILESTONES.md#current-position),
   and SPEC sections3/16/17/18/19 plus affected contracts. The complete design already exists.
3. Recheck the original authority at
   `C:/Users/Darian/.strata/operator/provisioning/controller.sqlite` with WAL-aware
   read-only SQLite. At the checkpoint all 40 tables match stopped live18;
   exposure is $4.887796 of the original $10. Verify stopped run receipts and
   current owned-process state before selecting any new execution.
4. Use the exact private seals/runtime/PackLock in the dated checkpoint. Do not
   execute old one-use preparation, admission, publication, run or archive scripts.

## Immediate deliverable

Assemble the exact profiles and evidence for all six [G0 outcomes](../SPEC.md#161-first-runnable-vertical-slice-g0),
starting with the changed minor 12 worker's cancellation/reconnect lineage and
remaining child dispositions. The accepted/refused-action/source/worker/pack/
saved-player/cost/clock join now passes independently; do not restart that work.

Selected host/helper, installation and private development scorer outcomes have
named evidence. Selected vanilla and Forge mechanics are retained separately.
Join their profile identities honestly; a source-only correction cannot inherit
an unrelated authentic pass. If an actual G0 gap remains, name it and implement
or test the smallest resolving change. A fresh live trial needs that evidence
gap or a relevant changed implementation/profile; do not rerun a successful or
failed goal merely to seek a better sample.

Audit every applicable child before closing its parent. Broader M0-prefixed gaps
must have an explicit retained disposition. Full T05/keybinding and D14 isolation
qualification belong to G1; full canonical recovery/fault/soak qualification to
G2. Do not convert them into M0 prerequisites or silently mark them passed.

## What just finished

Live18/D19.11 used actual GPT-6 Luna and Mineflayer. Sequence4 was refused without
input; corrected sequence 1 completed a 101.25-degree turn with contiguous receipts.
No walk occurred, so the original goal remains failed (9/14 checks). Independent
combined audit 19/19 proves the refused/accepted outcomes, public observations,
exact source and lock bindings, stopped player, all costs and actual ticks.
Eleven requests cost $0.009696 including one delivered helper. All 54 owned
processes terminated normally; D19.11 is consumed and cannot replay.

Live15 already passed actual turn/walk/helper play 14/14. Live16b/live17 and all
older failures stay under their original identities. We are building the LLM
harness; fixture scripts and fixed motor execution are not model decision-making.

## Continuing decisions

- D14: full gameplay/helper isolation qualification deferred to M1/G1. Label all
  development evidence isolation-unqualified; no scientific/G1 release claim.
- D17: `gpt-6-luna`; older model results retain their original generation.
- D18/D19: necessary bounded M0 runs remain authorized within the original $10,
  with every unresolved amount reserved. Earlier jobs must be terminal/fenced;
  each fresh reservation must fit; new uncertainty stops its own job. No extra
  approval, replay, refund or fresh allowance. General campaign admission is unchanged.
- D13: new Java normal-stop policy is 1,000ms; its 568.994ms sample passes. Historical
  500ms failures remain failed. D05 sign-in/entitlement/EULA approval persists.
- Shared-desktop input remains paused. Raw runs, game installations, credentials,
  private evaluator inputs and this operator checkout stay outside gameplay contexts.

## Source and evidence entry points

- [Native driver](../tools/m0_native_game.py), [public pilot contract](../src/mcbench/native_piloting.py),
  [retention/worker identity](../src/mcbench/native_game_retention.py).
- [Action journal](../backends/mineflayer/src/journal.ts), [lane](../backends/mineflayer/src/actions.ts),
  [private worker measurements](../backends/mineflayer/src/worker_health.ts).
- [Combined private reader](../evaluator/src/strata_evaluator/native_game_measurements.py),
  [action/source/pack reader](../evaluator/src/strata_evaluator/native_game_evidence.py).
- [Dated checkpoint and private pins](verification/2026-09-24-session-handoff.md),
  [latest detailed evidence](verification/2026-09-24-action-refusal-evidence.md),
  [current accounting contract](operations/validation-admission.md).

For merge checks, synchronize this checkout's `.venv` and verify its isolated
`mcbench.forge_guard` import. Python `-I` ignores `PYTHONPATH`; a borrowed worktree's
editable installation caused the retained guard-fixture identity failures at
this checkpoint. The [README](../README.md#local-development) has the commands.

Earlier next actions are retained in [historical handoff](STATUS_AND_HANDOFF_HISTORY_2026-09-24.md)
and the append-only ledger. They are superseded, not instructions to replay a run.
