# Implementation checkpoint and next-session handoff

Updated September 20, 2026. Operator-only. [SPEC v0.2.61](../SPEC.md)
defines the target; [MILESTONES.md](../MILESTONES.md) owns detailed progress,
decisions and history. [STATUS.md](STATUS.md) is the short evidence index.

## Start here

Implementation resumed from the merged documentation checkpoint. The active
long-horizon goal preserves the user's objective:

> Complete Strata according to SPEC.md and AGENTS.md through every required
> M0–M6 deliverable and acceptance gate. Preserve M7 and other conditional
> extensions with their activation conditions. Completion requires authoritative
> evidence for the full specification, not merely passing local tests.

Resume implementation in dependency order, prioritizing M0/G0. Continue across
intermediate checkpoints without asking whether to continue. The old session's
goal was marked blocked before D11 clarified the supposed missing inputs;
that historical label is not a current request for a VM or billing evidence.
Verify the new session's goal state instead of declaring completion.

1. Read AGENTS.md, the ledger's current position/G0 checklist, and SPEC sections
   3, 4.1, 6, 15–19 plus affected contracts. On first implementation review,
   read the full specification. Do not read the entire old conversation merely
   to discover the next action.
2. Fetch origin and inspect local changes/worktrees and
   [PR #2](https://github.com/OpenCnid/strata-bench/pull/2). PR #1 merged at
   `579796da40eeb9e6063196462767f60e9c87eac7`; PR #2 carries this continuation.
   PR #2 was verified merged at `542a77ac760fb305b26941085e33447f392f8ba8`;
   current worktree `09a0` uses fresh branch `codex/strata-estimated-usage`. Preserve it.
   Preserve uncommitted implementation before any subsequent branch transition.
3. Verify current private process/accounting/profile state using only necessary
   metadata. No game needs to launch just to inspect this checkpoint. Preserve
   existing work and raw evidence; never print auth caches or secret-bearing
   command lines.
4. State the bounded deliverable and exit evidence below, then implement it.
   Maintain the ledger alongside source changes. A test result alone cannot
   close the complete M0 gate.

## Delivered accounting and next implementation

**M0.1c.1c.2a: D11 versioned estimate implementation and migration delivered.**
Use [validation admission](operations/validation-admission.md) as the precise
continuation contract; do not restart the completed accounting implementation. Inspect `src/mcbench/authorization.py`, `budgets.py`,
`inference_dispatch.py`, `inference_transport.py`, `native.py`, their tests and
`configs/operator/live-validation.json`.

The durable actual-CLI/local-synthetic-provider dispatch task originally called
M0.1c.1c.1 already has streaming, retries, compaction, helpers and restart evidence.
Do not start it from scratch. The versioned estimate semantics, finite exposure records, settlement valuations
and explicit migration are implemented with focused synthetic verification and
one actual pinned-CLI/local-wire estimate fixture. See the [D11 report](verification/2026-09-20-estimated-accounting.md).
Real native/OAuth ingress and boundary qualification remain required.

Exit evidence: pinned price/usage basis; original allowance/store lineage
preserved; root/helper/retry/summary aggregation without envelope double counting;
distinct requests charged separately; duplicate receipts deduplicated; unknown
usage/streams/restart retain holds and never replay; incompatible migration
rejected; justified finite exposure before dispatch. Run focused affected tests
and only the affected pinned-CLI fixture. Mark synthetic/source checks
separately from authentic OAuth/game qualification.

**Current next deliverable M0.1c.2b.2:** complete qualification of the native tool/helper
boundary on available hardware. The agent needs scoped game access, its own
notes/skills and allowed docs; evaluator/holdout/admin/credential/sibling access
must be denied. Inspect host-supported restricted tools and protected brokerage,
preserving the selected native Dovetail loop and declaring capability changes.
The existing loopback canary failure remains evidence against the current
profile. A VM is optional; no user-supplied machine is currently requested.
The [broker report](verification/2026-09-20-restricted-native-tools.md) records implemented source and actual CLI/helper/synthetic-worker evidence, including the retained first-run failure. [Owned adversarial canaries](verification/2026-09-20-native-broker-canaries.md) now pass on the profile with inherited project documents disabled: explicit shell/image/resource/patch denials, exact root/helper catalogs, no marker leakage and no unauthorized loopback visits. Continue from `broker.py`, `broker_stdio.py`, `native_broker_policy.py` and the existing probes. Next: protected bootstrap/config/source identity and budget-linked live child enrollment, clean-fork/descendant enforcement, actual Dovetail body projection/learned-artifact activation/export, then OAuth/game qualification. Do not repeat the passing fixtures without a relevant change or a named evidence gap. If one path is blocked, advance independent authorized M0 work.

## Settled authority and limits

D01–D10 persist; D11 clarifies D04. Use Codex OAuth / `gpt-5.6-luna` under the
original **$10 total estimated experimental usage allowance**, including helpers,
retries and summaries. This means labeled API-price-equivalent subscription
usage, not actual OAuth dollar billing or an exact quota conversion. The user
confirms no outside Strata model experiments; inspected experimental records are
synthetic-only. Zero opening experimental usage does not mean the coding
assistant used no subscription resources.

Recommend at most $1 for the first qualified trial within the same $10 total,
then measure consumption. No allowance increase/reset occurred. Recheck durable
accounting before spending; preserve ambiguous holds. The D11 runtime migration was executed in the existing private project store
`C:/Users/Darian/.strata/operator/provisioning/controller.sqlite`, under the original
`validation-2026-09-18` ID and $10 cap. Fresh inventory found no installed prior
authority and only synthetic model stores; archived D04 was installed then explicitly
migrated with a store/snapshot/inventory/decision audit. Opening experimental usage
is zero. Do not create another allowance or use invented qualification flags to admit calls. Finite exposure and actual all-request accounting
remain required.

Isolation is needed for benchmark validity and private-state protection. It is
our implementation responsibility and does not block unrelated source work.
Shared-desktop input stays paused; API control and prepared separate-desktop
facilities are authorized within documented limits. A separate desktop does not
isolate files/processes/network. Official acquisition, EULAs and the existing
account login were already handled; do not ask to repeat them. N=2 still needs
a second licensed player identity.

## Current evidence and remaining gates

M0 is `in_progress`, G0 is `fail`, G1–G5 are `not_run`. M1–M5 contain partial
foundation implementations; M6 remains required and M7 remains conditional.
All F01–F16/N01–N08, T01–T17 and prose/contract coverage remain in the ledger.

| M0 area | Retained result and next gap |
|---|---|
| Native accounting/plugin/helpers | Actual pinned CLI with credential-free synthetic providers passes bounded dispatch, plugin load/use, helper lifecycle and no-replay recovery cases. Full child admission/permissions/sub-budgets, nested-depth capability, live ingress and complete resume remain unqualified. |
| Game mechanics | Selected vanilla mechanics and separately identified Forge modded block, 3-ingot machine processing/collection and expert furnace craft have independent saved-state/resource evidence. Mineflayer/E9E negotiation remains failed; fallback evidence is never a Mineflayer pass. |
| Cancellation/restart | Forge pair04 passes both public phases, corrected standing-footprint route, immutable authority, full journal staging/verification, receipt deduplication, stale-epoch denial and saved inventory/ender/position continuity. It charges 16 + 4 = 20 primitives without inherited recharge. |
| Shutdown | Pair04 phase1 passes at 339.9197 ms; phase2 fails at 508.2221 ms against 500 ms. Independent observer sees the root alive beyond 509 ms. Overall fail; no unchanged rerun or threshold relaxation. Pair02's two failures and the failed GC/startup diagnostic remain retained. |
| Pack provenance | Selected client/server loaded-config roles are evidenced; five original effective-file failures (263/268 passing) remain. Complete role/consumer disposition, provenance and seals are open. |
| Private scoring | Source/epoch/boot binding and semantic receipt-conflict handling fix a reproduced cross-campaign false completion; 112 focused checks passed. Registration is still an operator assertion; authenticated setup/team/ingress, positive/negative controls and nonleakage remain unqualified. |
| Complete integration | Join native host/helper usage, game actions/time and private milestone evidence under qualified locks/boundaries. Narrow journal continuity is not a full game+agent checkpoint. |

Linked completed Forge references total 766 primitives / 10233.723 s, plus
witness setups 266.907 s and interphase gaps 15.760 s and 3.899 s retained
separately. Other historical scopes remain separate; this is not a complete
project clock total.

After these M0 gaps, continue the specified contracts/keybinding T05, complete
recovery, 1/8/24-hour soaks, simultaneous capacity, matched probes and scientific
pilot/confirmation in dependency order. M1 settings expansion is paused while
M0 is the priority. Later E6E/E2E compatibility and graduation remain mandatory
M6 work; optional adapters/dashboard/distributed work retain activation conditions.

## Local operational map

| Location | Purpose / handling |
|---|---|
| `C:/Users/Darian/Desktop/codex/minecraft-benchmark` | Main checkout; check for changes before fast-forwarding or branching. |
| `C:/Users/Darian/.codex/worktrees/581d/minecraft-benchmark` | This session's `codex/strata-native-dispatch` source worktree; preserve it. |
| `C:/Users/Darian/.strata/evidence/` | Private raw evidence and launch/audit scripts; never copy into public source or gameplay access. |
| `C:/Users/Darian/.strata/evidence/2026-09-20-budget-clarification-01/operator-statement.json` | D11 user statement; non-executable, no runtime migration/dispatch qualification. |
| `C:/Users/Darian/.strata/evidence/2026-09-20-forge-reconnect-04` | Terminal failed pair04, staging receipt, independent audits and shutdown crosscheck. |
| `C:/Users/Darian/.strata/servers/e9e-1.27.0` | Original reference server; retain current saved bytes. |
| `C:/Users/Darian/.strata/clients/e9e-noninput-01` | Dedicated separate-desktop client; no shared-desktop input. |

Last authentic pair used client minor43, client telemetry 0.3.2 and original
server telemetry 0.2.0, with client config probing disabled. The 3-GiB resource
profile failed shutdown; it is not capacity-certified. Resolve exact artifact
hashes and source/profile pins from the [pair report](verification/2026-09-20-forge-reconnect.md)
and private manifest before any new launch. Do not restore saved state, renew
expired authority or launch a game as part of merely resuming the source.

Development toolchains: Python 3.12.14, Node 24.19.0, Windows x64 Temurin
17.0.20.1+1. Read [README](../README.md) and Forge runbooks for exact build inputs.
[Session checkpoint verification](verification/2026-09-20-session-handoff.md)
records actual merge checks, retained failures and publication review. It is
not clean-machine, production or scientific qualification.

For details use the [status index](STATUS.md), dated verification reports and
append-only milestone history. Earlier “pending VM/billing input,” “no live
corrected case yet,” and “next run pair04” statements describe superseded states.
Preserve their historical evidence without executing stale next actions.
