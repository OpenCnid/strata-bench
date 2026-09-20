# Implementation checkpoint and next-session handoff

Updated September 20, 2026. Operator-only. This is a source checkpoint, not an
MVP or scientific result. [SPEC v0.2.38](../SPEC.md) remains the target;
[MILESTONES.md](../MILESTONES.md) owns detailed status, decisions and history.
The user explicitly resumed implementation beyond the prior commit/merge
stopping point, with a long-horizon goal for every required M0–M6 deliverable
and gate; M7 remains conditional. Continue across intermediate checkpoints.
Older verification reports describe their dated candidates; use this review
and the ledger for current state.

Delivery: [PR #1](https://github.com/OpenCnid/strata-bench/pull/1) is confirmed
merged at `579796da40eeb9e6063196462767f60e9c87eac7` by fresh GitHub metadata
and fetched `origin/main`. The clean current worktree branched from that revision
as `codex/strata-native-dispatch`. The initial source checkpoint checks below
remain historical evidence; the resumed accounting change is described here.

[Draft PR #2](https://github.com/OpenCnid/strata-bench/pull/2) now publishes
`codex/strata-native-dispatch` through `301a2ef`. Last fetched origin/main resolves
to `579796d`. Continue this branch and preserve its unmerged commits; publication
is a partial source checkpoint, not completion or a reason to stop.

## Overall position

| Milestone | Status | What exists / what prevents closure |
|---|---|---|
| M0 — game/host vertical slice | in_progress | Authentic partial vanilla and Forge interactions; exact E9E Mineflayer handshake failed. Native model/plugin/helper integration, aggregate accounting, isolation and full expert mechanics remain open. G0 fail. |
| M1 — contracts/controller/settings | in_progress | Typed records, grants, journals, partial controller and settings workflows. Full T05 effects/persistence, production grants and adversarial isolation remain open. G1 not_run. |
| M2 — durable single-agent operation | in_progress | Budget/clock/checkpoint/recovery components and fault fixtures. Complete game-plus-agent restore, reliable native shutdown and 1/8/24-hour soaks remain open. G2 not_run. |
| M3 — private evaluation | in_progress | Telemetry import, saved-state readers, synthetic scorers/probes, artifact controls and paired analysis. Authoritative live mechanics/quest/team scoring and matched isolated probes remain open. |
| M4 — simultaneous teams | in_progress | Atomic team admission and communication components. Actual N=1/2/4 capacity evidence, accounts and N=2 soak/security remain open. G3 not_run. |
| M5 — research MVP | in_progress | Analysis/reporting source and operations material. Development cost/power pilot, locked protocol and confirmatory execution have not run. G4 not_run. |
| M6 — graduation/transfer/later packs | deferred | Required later milestone: calibrated graduation, anchors, retention/transfer and separately conformant E6E/E2E. G5 not_run. |
| M7 — optional scale/UI | deferred | Activate only on measured need or explicit request; not required merely because source work began. |

The codebase is a substantial foundation with narrow real-game evidence. It is
not yet an integrated long-horizon benchmark. Local test passes do not imply an
aggregate T01–T17 or G0–G5 pass.

## Authentic evidence retained

- Vanilla 1.19.2: authenticated joining, selected look/dig/flat movement,
  cancellation and player-menu checks. Full action/reference/reliability scope is
  incomplete. See the [vanilla menu report](verification/2026-09-19-vanilla-menu.md).
- E9E 1.27.0 / Forge 43.4.23: official dedicated installations, exact server
  startup and partial expert recipe evidence. Mineflayer's FML handshake failed;
  D06's Forge extension has its own identity and cannot pass that original case.
- Forge minor 34: [paired mayapple removal](verification/2026-09-19-outline-target.md),
  [short level walking](verification/2026-09-19-native-movement.md),
  [basic quest navigation](verification/2026-09-19-native-quest-cancel.md), and
  [cancellation before arrival](verification/2026-09-19-native-cancel.md) have
  narrow scoped-API and independent saved-server evidence. The last cancellation
  occurred during route centering, not general route traversal. Prior failures
  remain in the ledger and are not erased by later successes.
- An authentic client renders on a separate Windows desktop without switching
  the operator's active desktop. Private game frames have been decoded and
  inspected. Public capabilities still advertise `screenshots:false`. This
  desktop separation is neither a security sandbox nor full input parity.
- The latest current-policy guardian wait fails at 510.8433 ms against 500 ms;
  T07 is fail, with its remaining cases incomplete. Earlier failures at 501.9950,
  503.5059 and 507.6092 ms and one 451.9577 ms pass remain. CTM startup failure and an earlier frame
  missing terrain also remain in the retained history.

## Checkpoint verification and publication review

Executed on the existing Windows environment with Python 3.12.14, Node 24.19.0,
Temurin 17.0.20.1+1, pinned Forge 1.19.2-43.4.23 and the official external FTB
Library 1902.4.1-build.236 artifact. Commands and JVM opt-ins are in the
[README](../README.md). These are local contracts, synthetic fixtures and real
process/JVM checks, not new authentic game or model runs.

| Check | Actual result |
|---|---|
| `python -m pytest -q`, client/settings JVM opt-ins enabled | 738 passed, zero skipped, 113.77 s; two Typer/Click deprecation warnings |
| `npm test`, client JVM and guard Python opt-ins enabled | TypeScript build passed; 166 passed, zero skipped, 117.39 s |
| Gradle client/telemetry tests and test-classpath generation | Build successful; 440 client + 5 telemetry tests, zero failures/errors/skips |
| `python -m ruff check src evaluator/src tests tools` | All checks passed |
| Installed `mcbench --help` | Exit 0; operator command entry point loads |

The Python suite includes the real compiled gameplay package exclusion check.
The allowlist exports only CLI/error modules, package metadata and the sanitized
keybinding skill; it does not grant a gameplay agent this repository.

Publication review excludes account caches, installations, raw runs, logs and
private evaluator instances. Two compressed local Java logs discovered during
inventory were excluded by adding `logs/` and rotated-log patterns to `.gitignore`;
SQLite sidecars are excluded too. The sole candidate binary is the pinned Gradle
wrapper, whose SHA-256 matches `java/build-inputs.json`. A text scan found no
private keys, recognizable service tokens, JWTs or literal long credential
values; this heuristic is not a complete secret/security audit. The existing
build environment is tested; clean-machine reproducibility and CI are not
qualified. No GitHub Actions workflow is included in this checkpoint.

The staged review covers 462 source/design files and 877 local Markdown links;
all links resolve and all required F/N/M/T/G ledger IDs remain represented.
The only credential-shaped URL match was the explicit synthetic
`user:secret` rejection fixture in `tests/test_provisioning.py`, reviewed as test
data. Source line endings are pinned to LF, with Windows batch files at CRLF,
so a later Windows checkout does not silently alter source fingerprint bytes.

Raw test logs and publication inventories/hashes stay in the operator's external
`C:\Users\Darian\.strata\evidence\2026-09-19-merge-checkpoint-01` directory.
Published reports contain bounded findings, not raw account or run data.

## Current native accounting work

M0.1c.1b now has [eight passing actual-CLI/synthetic-provider cases](verification/2026-09-20-native-dispatch.md)
and 130 passing relevant Python checks. Nested job/helper envelopes consume the
same reservation; distinct requests charge separately; duplicate receipts charge
once; missing usage/lost streams retain holds and block forwarding. Compaction
and two separate native helper/executor jobs reconcile. A fresh supervisor
process refuses replay after an already classified interruption. Exact sealed
inventory closure and native finalization are atomic. Private operator schemas
are regenerated; gameplay records/tools are unchanged.

The final credential-free fixture matrix is external
`C:\Users\Darian\.strata\evidence\2026-09-20-native-dispatch-08`; its manifest
hashes tested code and CLI. Earlier attempts/failures remain in -01 through -07.
All these native processes/listeners are terminal. No paid inference or game
launch occurred. The inspected known roots contain 25 accounting stores, all
newly simulated or prior synthetic tool-only stores, with no live profiles.
Do not interpret the absence of a live ledger as a fresh budget authorization.

M0.1c.1c.1 now adds bounded upstream SSE/JSON parsing and forwarding plus abrupt
supervisor-death recovery. The final nine-case `--wire` matrix passes at private
`2026-09-20-native-dispatch-wire-final-01`: 15 ingress requests, 13 forwarded,
eight settled/five intentionally unresolved and ten CLI jobs. A stream prefix
is flushed before supervisor exit; independent held-job counts go from 13 to
zero before fresh recovery retains the holds and refuses replay. The expanded
165-test Python run and final 30 transport checks pass; see the report's
follow-up for exact source pins, raw evidence and limitations.

Accounting source checkpoint `66baa0f` is committed on the resumed branch.
The [native plugin follow-up](verification/2026-09-20-native-plugin.md) adds
actual discovery and skill-body/tool-loop evidence with a synthetic provider,
including the two explicit-only upstream skills and disabled-plugin controls.
The long-path reader and plugin override key are corrected. Native catalog
policy excludes nested package fixtures without changing the selected source
or dropping any of its eight core skills. All earlier failed samples remain.

Plugin checkpoint `5e3a047` is committed. The [native boundary canaries](verification/2026-09-20-native-boundary.md)
now give concrete failed evidence: unelevated native tools read a dummy operator
file and contact an unapproved loopback endpoint; stricter named read permissions
refuse startup. The prepared elevated sandbox command blocks the file read but
still contacts the endpoint as CodexSandboxOffline. Active firewall rules and
matching account filters were inspected without changing them. No production
qualification is issued. An existing isolated-worker/VM location is requested;
do not repeat that question while pending. Continue independent authorized
game/reliability work while the enforcement blocker remains open.

Continue M0.1c.2b command/helper boundary and canary isolation conformance when
an enforceable execution environment is available. The transport
adapter remains explicitly synthetic-only. Actual OAuth monetary conversion,
finite exposure, complete project spending authority and adversarial isolation
remain unqualified. A request for the account's documented USD-per-credit rate
and non-secret source is pending; do not ask again unless the answer is unclear.
Advance independent credential-free host/plugin/skill/helper work while live
admission remains blocked.

## Native helper lifecycle follow-up

[Authentic native settings](verification/2026-09-20-native-settings.md) now pass
the first Curios configuration apply/readback/rollback and a separate discovery
boot: 253 restored mappings/persisted values, unchanged options digest, intact
transaction journal, both title clients stopped, desktop unchanged and arguments
retired. No world/server/physical input/inference.
[Pending transaction recovery](verification/2026-09-20-native-settings-recovery.md)
now also passes: one apply, forced first-client termination, new-session status
before rollback, six valid journal frames with the original prefix preserved,
253 restored runtime/persisted values and exact original options bytes. Both
processes are terminal and arguments retired. Continue foreign-options/revision
conflicts and precise mid-write faults; physical effects, repair accounting and
complete T05/G1 remain unqualified.

The [authentic current-policy guardian trial](verification/2026-09-20-guardian-live.md)
fails: startup and three public reads pass, but the root wait times out at
510.8433 ms against 500 ms. It produces no complete tree proof or stop receipt.
The server saves normally; zero Java processes, unchanged desktop and retired
arguments are verified. Raw failure/observer/telemetry evidence stays external.
Do not repeat an unchanged trial to obtain a pass. Native title-screen settings
now have the separate narrow evidence above; continue remaining recovery cases and
diagnose guardian cleanup/scheduling while retaining all full acceptance gates.

[Native overlap/limit fixtures](verification/2026-09-20-native-helper-topology.md)
now pass two concurrent children and exact second-child rejection at one slot,
with eight/seven fully settled gateway calls. The required nested profile is
blocked: children omit collaboration even with max depth two; the pinned
bundled Luna catalog reports v1. The first failed nested sample retains its
full 12-call reservation and zero recovery replay. Corrected catalog-first
checks fail cleanly with four settled calls. 113 Python checks/full Ruff pass;
no live inference, game or desktop input in this change. Continue authentic
guardian/mechanic qualification while resolving the explicit nested seam,
production child boundaries and the existing monetary/isolation blockers.

Loaded-config checkpoint `8479e97` is committed. [Native lifecycle/interruption](verification/2026-09-20-native-helper-lifecycle.md) now has a 12-call idle messaging/follow-up case and active child interruption with four settled/one ambiguous request. Fresh recovery replays nothing and retains the full envelope. Exact native results, original helper/restart regressions, 96 Python checks and full Ruff pass. Empty-ack parser failure remains in its original store. Full child admission/permissions/sub-budgets, nested depth/grandchildren, isolation and complete resume remain open; do not treat native cancellation as provider usage settlement. No live inference or game run in this work.

## Exact-pack follow-up

Overlay checkpoint `ce3e465` is committed. [Loaded-config telemetry 0.2.0](verification/2026-09-20-e9e-loaded-config.md) has 51 Python/11 Java checks and an authentic corrected two-boot comparison: 34/32 clean records, same six selected snapshots, both furnace assertions pass. Original placeholder-selector plan failure is retained. Four files are unregistered and current Create/common values persist; all 268 file outcomes/digests remain unchanged, including five failures. The dedicated server now has the pinned 0.2.0 telemetry JAR; old bytes are preserved privately. All three runs stopped normally; no client or inference ran. Next: exact role/consumer disposition and full expert mechanics/reliability with current pins.

Native helper checkpoint `a1fbb0e` is committed. The [overlay review](verification/2026-09-20-e9e-overlay-review.md) adds bounded private mismatch diagnostics while retaining all five failures (263/268 passing stopped-server checks). Exact installed JARs, declared nested mods and original archives indicate client-specific and legacy overlays; no file exclusions, guessed migration or vendor edits were applied. Fifteen local tests and targeted Ruff pass. M0.3.2b now has selected server loaded-config evidence and retains full role/reference/mechanics qualification. The stopped-artifact review itself made no game run or inference.

## Original resumed task and retained acceptance criteria

[Native collaboration](verification/2026-09-20-native-helpers.md) now has actual
v2 spawn/wait/result evidence, extending the earlier two-independent-CLI helper
fixture. Final `native-helper-08`/`-09` pass clean-context/ephemeral and full-history/
private-profile forks. Each meters four requests while root JSONL usage covers
only three; initial parser and ephemeral-thread lookup failures remain. NativeLaunch
now fingerprints session storage and rejects stale qualification on mode changes.
77 relevant Python checks and Ruff/schema/build pass. Native per-helper admission,
budgets/permissions, further lifecycle and complete state resume remain .2c.2 work.
Do not treat fresh contexts or stored rollout files as security isolation.

Independent reliability work after isolation checkpoint `fafd8c3` adds
[owned-job stop proof](verification/2026-09-20-guardian-tree.md). Zero active
accounting was observed before a child handle signaled; that failed sample is
retained. The revised guardian requires complete held/signaled member counts
within the original shared 500 ms wait. 52 Python, five additional inventory
checks and 12 Node checks pass, plus package/Ruff/build checks. The fixed
256-handle development bound, missed-member failures, authentic timing and
production launch/isolation remain unqualified. Next apply the stronger proof
to the synthetic native crash/restart fixture: its historical 13-to-zero counts
are accounting evidence only. That follow-up now passes two actual-CLI crash
cases; final `2026-09-20-native-crash-handles-02` retains all 13 handles and
observes every one signaled before fresh recovery retains the full ambiguous
reservation with zero replays. See the [dispatch report follow-up](verification/2026-09-20-native-dispatch.md).
Guardian checkpoint `0312d53` is committed. Continue independent native helper
conformance and authentic reliability/mechanics with regenerated source pins
while external inputs are pending. Neither partial proof closes live admission.

The user selected **M0.1c.1** first: bounded, zero-inference integration of the
durable dispatch boundary into the actual pinned CLI's local synthetic transport.
The original task criteria below remain traceable; see current work above for
completed synthetic scope and the remaining production boundary.

1. Read this handoff, the ledger's current position, SPEC sections 3, 6, 15–19,
   and the [native budget](verification/2026-09-19-native-budget.md) and
   [dispatch accounting](verification/2026-09-19-inference-dispatch.md) reports.
2. Inspect [inference_dispatch.py](../src/mcbench/inference_dispatch.py),
   [budgets.py](../src/mcbench/budgets.py), [native.py](../src/mcbench/native.py)
   and [dispatch tests](../tests/test_inference_dispatch.py). The module is
   implemented but unverified in production. The new local fixture is a transport
   caller; trusted evidence flags still do not establish real pricing or bounds.
3. Reuse the credential-free native probe under the private
   `2026-09-19-native-budget-01` evidence directory as a reference. It already
   observed one rejected POST and two POSTs for one retry, with identical body
   hashes. Introduce a public synthetic fixture for repeatable integration;
   never copy credentials or raw native journals into tests.
4. Connect each distinct HTTP request/retry to one committed reservation/intent
   before forwarding. Define how whole-job reservations and per-call reservations
   compose without duplicate charges or releasing unresolved cost holds. Exercise
   successful streaming, lost final usage, interrupted streams, compaction,
   helpers and process restart with deterministic local provider fixtures.
5. Preserve fail-closed admission until real OAuth USD conversion, finite
   provider exposure and credential/process/network isolation are qualified.
   The pinned CLI's inspected turn-start schema has no output-token/money cap;
   account limits and goal token budgets are not substitutes for this proof.

Exit evidence for that bounded task: actual CLI requests traverse the durable
boundary, distinct retries charge distinctly, duplicate receipts charge once,
uncertain requests hold their full reservation and prevent further dispatch,
restart never resends an ambiguous request, and root/helper totals reconcile.
Label synthetic evidence explicitly. It advances partial T04/T07/T12 without
claiming full OAuth/native-host conformance. Any change to a public affordance or
budget policy must be recorded in SPEC and the ledger.

## Remaining work after that task

| Priority / owner | Gap and next resolving action |
|---|---|
| Native host — AR/PL/SI | Finish actual Dovetail/plugin/skill/helper invocation, exact model identity, interruption/resume, all-call metering and adversarial isolation. Keep operator/evaluator/account data unreachable. |
| Native reliability — GI/QA | Diagnose repeated 500 ms shutdown timeouts and CTM startup failure without relaxing the bounds or erasing samples; qualify consistent startup/frame/render/stop behavior. |
| Exact pack — GI | Resolve five retained overlay checks: BHMenu, No More World Settings, Inventory Sorter, Sophisticated Core and Create. Complete artifact seals and representative altered recipes/machines; a successful join is insufficient. |
| Affordances/settings — GI/PL | Complete rich/custom JEI content, occupied crafting lifecycle, quest submissions/claims, remaining menus and machine energy/fluid/routing; qualify actual intended/competing physical-key, modifier, polling, pointer-lock and restart/rollback effects for T05. |
| Recovery/resources — PL/QA | Restore game, player/quest/team/machine, agent, artifact, clock and budget state from one clean checkpoint boundary; preserve costs and uncertainty. Run the authorized 1/8/24-hour soaks only when prerequisites pass. |
| Capacity — PL/SI | Obtain a second licensed avatar identity before N=2, measure simultaneous N=1/2 and explicit N=4 disposition, enforce whole-team admission and parent budgets. |
| Scientific qualification — RS | Complete authoritative private scoring and matched probes, cost/power planning, preregistration and confirmation. The present $10 authorization does not establish feasibility for the required study. Keep drift, censoring, retention/transfer and controls. |
| Later compatibility — GI/RS | M6 remains required: independently qualify E6E/E2E and calibrated graduation; M7 stays conditional. |

## Operational handoff

All authentic clients, servers and the two local native probe processes were
terminal before checkpoint testing. Temporary launch arguments were retired;
saved outcomes and costs remain. No checkpoint restore or game restart is
needed merely to inspect the source. The latest dedicated E9E client copy is
`C:\Users\Darian\.strata\clients\e9e-noninput-01`; private servers, credentials
and evidence also live under `.strata`, outside the repository. Inspect only the
specific private metadata needed; do not print auth caches or process command
lines containing credentials.

Existing D01–D10 authorizations persist. D04 selects Codex OAuth / `gpt-5.6-luna`
with **$10 total** across all Strata inference, including helpers/retries; **$0
has been dispatched**. Official installations, account login and EULAs were
already handled. Do not ask the user to repeat those completed steps. A second
Java account remains a separate capacity prerequisite.

Shared-desktop input remains paused; preserve the user's ability to use the
computer. Ordinary gameplay is API-controlled. Separate-desktop launch and
private frame diagnostics are available for bounded checks but do not waive
render/input/security gates. Neither current-user ACLs nor a fresh conversation
provide adversarial isolation.

Continue the current `codex/strata-native-dispatch` worktree without discarding
its unmerged commits. Reconcile the actual remote/working tree and read applicable
instructions before changing code in a later session. Do not rerun broad or paid suites
without a relevant change. Keep all F01–F16/N01–N08, T01–T17, G0–G5 and M0–M7
coverage visible; update the ledger with the next task's actual evidence.
