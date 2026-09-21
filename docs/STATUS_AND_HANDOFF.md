# Implementation checkpoint and next-session handoff

Updated September 20, 2026. Operator-only. [SPEC v0.2.71](../SPEC.md)
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
The existing loopback canary failure remains evidence against the original
profile; later restricted-profile results do not erase it. A VM is optional; no user-supplied machine is currently requested.
The [broker report](verification/2026-09-20-restricted-native-tools.md) records implemented source and actual CLI/helper/synthetic-worker evidence, including the retained first-run failure. [Owned adversarial canaries](verification/2026-09-20-native-broker-canaries.md) now pass on the profile with inherited project documents disabled: explicit shell/image/resource/patch denials, exact root/helper catalogs, no marker leakage and no unauthorized loopback visits. Continue from `broker.py`, `broker_stdio.py`, `native_broker_policy.py` and the existing probes. [Participant admission](verification/2026-09-20-native-admission.md) now supplies root stdout identity, exact request/reservation binding, clean helper validation, nested budgets, descendant revocation and terminal sealed closure; 102 focused checks and actual-CLI clean/inherited-context fixtures supply partial evidence. Retain the ephemeral full-fork failure. Continue from `native_admission.py` and its existing probes. [Sealed bootstrap](verification/2026-09-20-native-bootstrap.md) now pins the native/plugin/broker/interpreter/configuration files, holds Windows file leases, rejects unlisted imports/bytecode and uses isolated startup; actual root/helper and changed-profile canary fixtures pass narrowly. Continue from `native_bootstrap.py`, `launch_integrity.py`, `sealed_broker.py` and the existing `--bootstrap` probe. [Authenticated native ingress](verification/2026-09-20-native-ingress.md) now adds native job/profile/header/request binding with persistent revocation, checks before child/per-call reservations and secret-free journals. Source checks and one actual sealed CLI/synthetic-provider root/helper run pass; seven unauthorized HTTP clients are rejected before capture/reservation. Continue from `native_ingress.py` and the existing `--ingress` probe. [Native OAuth transport](verification/2026-09-20-native-oauth-transport.md) now supplies short-lived native bearer/account capture, bounded observed protocol-header preservation, fixed verified HTTPS routing and expiring per-check private qualification requirements, reusing the receipt/accounting path. Two fabricated-cache/native fixtures settle 6 + 7 calls (182 fixture units); the second proves header preservation at the owned upstream. Continue from `native_oauth.py` and the existing `--oauth` fixture. [Gateway and skill-read integration](verification/2026-09-20-native-gateway.md) now connects authenticated HTTP, finite request admission, cancellation and exact closure; real pinned skill bodies reach actual root/helper tool outputs. The [bounded live receipt entrypoint](verification/2026-09-20-native-oauth-conformance.md) is implemented and was executed once. It failed with `RESPONSE_CONTENT_TYPE` and no usage receipt. The request and envelope retain $0.7554 once in the original authority; model admission is blocked by uncertainty. Never rerun `validation-2026-09-18:oauth-first-receipt`, refund its hold or manufacture a settlement. Continue independent M0 scorer setup/team/ingress authority, shutdown/provenance and recovery work. Source fixes now preserve safe private HTTP rejection diagnostics and enforce nonzero failed CLI outcomes; the original lost status/media/body remain unknown. Native catalog pinning has metadata-only evidence; the changed exec profile has not run. Provider-limit exposure is 755400 microUSD per call: concurrent root/helper holds cannot silently exceed the initial ceiling. Implement measured stage admission and fenced helper-envelope lifecycle for the subsequent helper/game/private evidence join. Supporting skill files, learned activation/export and full helper lifecycle/slot reuse remain required. TLS and authenticated read-only metadata were observed, and a real native OAuth token was privately copied/forwarded for the failed request. No authoritative receipt or full transport qualification exists. Keep the separate synthetic adapter guards; do not relabel a fixture as live qualification. The preliminary long-path, root-event ordering and helper-poll failures remain retained. Do not claim that file locks alone authenticate HTTP or isolate arbitrary same-user reads. Do not repeat the passing fixtures without a relevant change or a named evidence gap. If one path is blocked, advance independent authorized M0 work.

## Active independent M0 deliverable

M0.2c.3 implements [private telemetry authentication](verification/2026-09-20-authenticated-telemetry.md), committed as `ec15bbd`: fresh key/challenge grants, durable exclusive boot claims, signed exact-byte chains and full scope/contract verification. Source checks include 136 affected Python tests, 24 final authentication tests, 20 Java tests and the package exclusion check. The cross-language null-serialization failure was fixed and retained.

M0.2c.3a now passes the narrow authentic dedicated reference: distinct protected E9E clone, module 0.3.3/config 3, 13 signed records, 186 sampled ticks, six exact expert-recipe assertions and clean stream termination. Server elapsed 156.203 s, no client/model/shared input, all 18,215 original source files unchanged. Four derived tamper/scope/completeness controls reject. A plain-JVM writer also rejects the consumed authentic grant without changing its claim/spool. Actual evidence and keys remain private. This does not qualify a score, OS process isolation, mechanical parity, the 500-ms guardian or full recovery. Do not repeat this stream trial unchanged.

M0.2c.3b.1 now implements [private fixture seals and the authenticated craft reference join](verification/2026-09-20-craft-reference-seal.md). `craft_reference.py` verifies/preserves complete fixture/supporting bytes, binds the plan into authority v2, reserves one launch and imports a signed complete stream against roster/recipe/tick-window checks. Identical imports are idempotent; changed/missing evidence and reused grants reject. 133 affected Python checks, final 35 reference checks, 20 Java tests, package exclusion and the actual synthetic CLI/JVM flow pass. No protected score, Minecraft/model dispatch or new allowance.

M0.2c.3b.2 now implements the [owned reference launcher](verification/2026-09-20-reference-launch.md). Source/JVM faults pass 104 affected Python + 3 admission checks and 22 Java tests. The actual Forge CLI reference binds native process/world/module identity to retained OS handles, terminates all six members normally and preserves 13 signed records / 207 sampled ticks. All 18,226 original source files remain unchanged; the independent 19-check audit passes. Only .3b.2a's named launch reference is verified, with no scoring or guardian qualification. Preserve the separate private bundle `2026-09-20-reference-launch-live-01`, telemetry 0.3.4 and fresh stopped clone `e9e-owned-reference-01` on loopback 25570; do not reuse its grant or restore it over an earlier instance.

M0.2c.3b.3 now implements [native setup observations](verification/2026-09-20-native-setup.md) and explicit expected FTB teams in `PrivateCraftReferencePlan/2`. Final native Python checks pass 29 cases; Java passes 25. The retained affected run has 156 passes and one rejected-roster test-expectation failure, subsequently fixed. Actual telemetry 0.3.5 startup observes expert flags with zero script errors, survival mode, disabled world commands/command blocks/RCON, no operators and the server-bound FTB manager. The 27-check independent audit compares sealed NBT/properties/ops, verifies all six owned members stopped and preserves 14 records / 206 sampled ticks. All 18,225 original source files remain unchanged. Preserve private bundle `2026-09-20-native-setup-live-01`, fresh stopped clone `e9e-native-setup-01`, loopback 25572 and its consumed grant. This is a server-only startup reference, not actor/team/craft qualification; client diagnostics remain on their earlier pinned 0.3.2 profile.

Next .3b.3b needs an owned sealed version-2 authentic client craft and registered native-team positive/negative controls, using the existing ordinary craft worker and separate-desktop/API facilities. Do not repeat the unchanged startup trial. .3b.2b must exclude concurrent mutable-world/config writers; complete setup/mutation history, instrumentation parity and isolation remain required before scoring. Immutable software leases and native world paths alone do not prove that ownership. The registered benchmark roster is not FTB Teams evidence; supporting bytes are not an automatic setup-validity assertion. Raw/candidate witnesses remain unscorable. The online telemetry API and full recovery remain open. Preserve all original failures and the $0.7554 unknown-usage hold; no model replay/refund or unchanged accounting trial.

## Settled authority and limits

D01–D10 persist; D11 clarifies D04. Use Codex OAuth / `gpt-5.6-luna` under the
original **$10 total estimated experimental usage allowance**, including helpers,
retries and summaries. This means labeled API-price-equivalent subscription
usage, not actual OAuth dollar billing or an exact quota conversion. The user
confirms no outside Strata model experiments; the inspected opening records were
synthetic-only. The first live receipt attempt now has unresolved usage. Zero opening experimental usage does not mean the coding
assistant used no subscription resources.

Recommend at most $1 for the first qualified trial within the same $10 total,
then measure consumption. No allowance increase/reset occurred. Recheck durable
accounting before spending; preserve ambiguous holds. The D11 runtime migration was executed in the existing private project store
`C:/Users/Darian/.strata/operator/provisioning/controller.sqlite`, under the original
`validation-2026-09-18` ID and $10 cap. Fresh inventory found no installed prior
authority and only synthetic model stores; archived D04 was installed then explicitly
migrated with a store/snapshot/inventory/decision audit. Opening experimental usage
was zero. Current exposure is 755400 microUSD with uncertainty, one envelope and one request, zero valuations and admission blocked. Do not create another allowance or use invented qualification flags to admit calls. Finite exposure and actual all-request accounting
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
| Native accounting/plugin/helpers | First authentic OAuth receipt trial fails with unknown usage; $0.7554 held. Actual pinned CLI with credential-free synthetic providers passes bounded dispatch, plugin load/use, helper lifecycle and no-replay recovery cases. Full child admission/permissions/sub-budgets, nested-depth capability, live ingress and complete resume remain unqualified. |
| Game mechanics | Selected vanilla mechanics and separately identified Forge modded block, 3-ingot machine processing/collection and expert furnace craft have independent saved-state/resource evidence. Mineflayer/E9E negotiation remains failed; fallback evidence is never a Mineflayer pass. |
| Cancellation/restart | Forge pair04 passes both public phases, corrected standing-footprint route, immutable authority, full journal staging/verification, receipt deduplication, stale-epoch denial and saved inventory/ender/position continuity. It charges 16 + 4 = 20 primitives without inherited recharge. |
| Shutdown | Pair04 phase1 passes at 339.9197 ms; phase2 fails at 508.2221 ms against 500 ms. Independent observer sees the root alive beyond 509 ms. Overall fail; no unchanged rerun or threshold relaxation. Pair02's two failures and the failed GC/startup diagnostic remain retained. |
| Pack provenance | Selected client/server loaded-config roles are evidenced; five original effective-file failures (263/268 passing) remain. Complete role/consumer disposition, provenance and seals are open. |
| Private scoring | Private signed-spool source now has Java/Python and actual-JVM synthetic evidence; authentic producer/key isolation and scoring still require qualification. Source/epoch/boot binding and semantic receipt-conflict handling fix a reproduced cross-campaign false completion; 112 focused checks passed. Registration is still an operator assertion; authenticated setup/team/ingress, positive/negative controls and nonleakage remain unqualified. |
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
| `C:/Users/Darian/.codex/worktrees/09a0/minecraft-benchmark` | Active `codex/strata-estimated-usage` source worktree from fetched merged main; preserve changes. |
| `C:/Users/Darian/.codex/worktrees/581d/minecraft-benchmark` | Prior native-dispatch worktree and existing Python virtualenv; preserve it. |
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
