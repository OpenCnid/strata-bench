# Strata implementation milestones and coverage ledger

Updated: 2026-09-21. Authority: [SPEC.md](SPEC.md) v0.2.76; maintenance rules: [AGENTS.md](AGENTS.md).

**Operator-only. Never expose this ledger or its linked private evidence to gameplay agents or their helpers.**

## Current position

Read [STATUS.md](docs/STATUS.md) for the compact evidence index and [the handoff](docs/STATUS_AND_HANDOFF.md) for the next session. Dated reports and the append-only log preserve historical states; their superseded next actions are not current instructions.

- **User clarification D11:** no outside Strata model experiments occurred; the inspected synthetic-only records plus this statement establish a zero opening experimental-model usage baseline. The original $10 is a rough model-price estimate of subscription usage, not an account-billing proof request or a fresh allowance. Versioned API-equivalent estimate accounting and explicit original-authority migration now have source/synthetic evidence; [D11 report](docs/verification/2026-09-20-estimated-accounting.md). Isolation remains our engineering responsibility; an externally supplied VM is not a prerequisite in itself. Keep the actual game/evaluator/admin boundary and existing failed samples. No live dispatch or gate qualification is implied.
- **Current live accounting:** the first receipt-only OAuth trial failed (`RESPONSE_CONTENT_TYPE`) without authoritative usage. Original schema-2 authority/cap and one migration remain; one envelope plus one request reserve $0.7554 once, zero valuations. Gateway closed, native stopped, admission blocked by uncertainty. No replay/refund. [Failed trial and fixes](docs/verification/2026-09-20-native-oauth-conformance.md).
- **Implemented M0 behavior:** durable actual-CLI/synthetic-provider accounting handles distinct retries, helper calls, streaming failures, compaction and restart without double charging or replaying unknowns. Native game journals now reconcile and stage complete history across epochs, with unchanged authority and a separately verified publication receipt. [Native dispatch](docs/verification/2026-09-20-native-dispatch.md), [cost reconciliation](docs/verification/2026-09-20-run-costs.md).
- **Authentic evidence:** selected vanilla and separately identified Forge mechanics, private native expert-craft consumption, and selected cancellation/reconnect cases have independent saved-state evidence. The previous Forge pair preserves receipts/counters and charges 27 + 4 = 31, but both shutdowns fail 500 ms. Client config-role observations pass narrowly; all five original effective-file failures remain. [Craft witness](docs/verification/2026-09-20-craft-witness.md), [restart](docs/verification/2026-09-20-forge-reconnect.md), [client roles](docs/verification/2026-09-20-client-config-role.md).
- **Retained failures and costs:** pair04 is terminal overall fail. Corrected cancellation, reusable staging/verification, restarted receipts/state and 16 + 4 = 20 accounting all pass; phase1 guardian passes 339.9197 ms, phase2 fails at 508.2221/500 ms. No unchanged repeat. Completed linked references retain 766 primitives/10233.723 s, plus witness setups 266.907 s and separately retained interphase gaps 15.760 s and 3.899 s; other scopes remain separate. [Restart evidence](docs/verification/2026-09-20-forge-reconnect.md).
- **Current independent M0 work:** M0.2c.3b.3 now implements native mode/admin/team point observations and a version-2 expected-team reference plan. [Native setup evidence](docs/verification/2026-09-20-native-setup.md): final 29 native Python checks and 25 Java tests pass; the retained affected run has 156 passes and one subsequently fixed test-expectation failure. One actual Forge reference observes loaded expert flags, native survival/admin settings and server-bound FTB manager readiness; 27 audit checks pass, all six members terminate, 14 records / 206 sampled ticks are retained and all 18,225 original files remain unchanged. Actor-specific team/craft observations, joint controls, full setup history and isolation remain open. The subsequent client references remain failed/uncertain; current abort/outer-monitor work is detailed below. No unchanged startup repeat or scoring credit. .3b.2b and all M0/G0 gaps remain.
- **Remaining engineering/gates:** qualify actual OAuth all-request ingress on the implemented D11 estimate basis; enforce the selected native runtime/helper boundary around private evaluator, credentials and server-admin access. The prior-spend question is resolved and no VM procurement request remains pending. Reliable shutdown, complete role/config provenance and seals, scorer controls/nonleakage and full host/game evidence join remain required. Exact Mineflayer/E9E negotiation remains failed; Forge is separately identified.
- **Release status:** M0 remains in_progress, G0 fail, G1–G5 not_run. All F01–F16/N01–N08, T01–T17 and required M0–M6 work remain represented below; M7 stays conditional. N=2 needs a second licensed identity; required capacity tests, soaks and scientific execution remain unrun.
- **Authority and publication:** D01–D10 persist with D11 clarifying the original $10 TOTAL API-equivalent estimated-usage allowance, OAuth/Luna selection and zero opening experimental usage. Runtime policy migrated with the original authority/cap preserved; no new allowance. One live receipt request is now unresolved with its hold retained. Shared-desktop input stays paused. [PR #2](https://github.com/OpenCnid/strata-bench/pull/2) contains the continuation and this session-transition checkpoint; PR #2 was verified merged at `542a77ac760fb305b26941085e33447f392f8ba8`; work continues on fresh branch `codex/strata-estimated-usage`. [Merge verification](docs/verification/2026-09-20-session-handoff.md) records actual checks. This checkpoint does not close M0 or cancel the M0–M6 objective.

Current candidate: [restricted native tools and broker](docs/verification/2026-09-20-restricted-native-tools.md) now has source and actual-CLI/synthetic-worker evidence; [owned adversarial canaries](docs/verification/2026-09-20-native-broker-canaries.md) pass narrowly on the changed profile. [Native participant admission](docs/verification/2026-09-20-native-admission.md) now binds root/helper requests, nested budgets and broker grants to the running native job; clean helpers pass and inherited history is rejected in actual-CLI/synthetic-provider fixtures. [Sealed bootstrap](docs/verification/2026-09-20-native-bootstrap.md) now pins private software/configuration, enforces isolated source imports and holds Windows file leases; native root/helper and changed-profile canaries pass narrowly. [Authenticated native ingress](docs/verification/2026-09-20-native-ingress.md) now binds transport credentials and exact request digests before child-budget/dispatch admission; source and actual-CLI synthetic root/helper/negative-client checks pass. [Native OAuth transport](docs/verification/2026-09-20-native-oauth-transport.md) now has fixed HTTPS/qualification source and actual-native fabricated-cache/header-preservation evidence, using the existing accounting path. [Gateway and skill-body integration](docs/verification/2026-09-20-native-gateway.md) now has source and actual pinned-CLI/synthetic-provider evidence: finite per-request admission, cancellation, port ownership until native termination, exact closure and immutable real Dovetail body reads for root/helper. The bounded first-receipt conformance entrypoint is implemented and its one authentic request failed without usage; $0.7554 remains held. Safe rejected-response diagnostics and sealed native startup catalog pinning are now implemented, with focused source checks and metadata-only CLI evidence. Do not replay or loosen unknown-metering admission. Continue independent M0 private-scorer authority, shutdown/provenance and recovery implementation while preserving the unresolved receipt. Full native/game/private join, measured helper lifecycle, supporting skill files and learned activation/export remain required; no unrelated M1 expansion.

Statuses: `not_started`, `in_progress`, `implemented_unverified`, `verified`, `blocked`, `deferred`. Test/gate results: `not_run`, `pass`, `fail`, `blocked`. A dash in implementation/evidence means none yet, not not-applicable. Owner roles are defined in SPEC section 3; assign an actual owner when work starts.

**Active M0 client reference:** the [changed authentic reference](docs/verification/2026-09-21-native-craft-points.md) completed the expert furnace craft with matching signed native actor/team/mode and saved-resource evidence; 74 primitives reconcile without unknown requests. The pair remains UNCERTAIN after `PROCESS_MEMBER_INVENTORY_UNAVAILABLE`; its 27/29-check audit fails and import is denied despite normal server stop and complete eventual terminal handles. Preserve both earlier failed references and consumed grants. Bounded process-inventory diagnostics now record exact API/predicate stages and immediate Win32 errors before abort/cleanup; 109 affected checks pass (17 initially skipped), then 37 guard/package checks pass including those 17. One owned Python churn case did not reproduce the authentic failure. No unchanged game rerun. Next diagnose the named inventory failure with changed diagnostic pins and finite exposure; continue independent M0 ownership/scorer/provenance/recovery work. Original $0.7554 hold and all acceptance failures remain.

## M0 closure checklist — SPEC 16.1

These are the six required G0 outcomes. Child evidence below does not close a row by itself.

| G0 item | Current evidence | Remaining closure work |
|---|---|---|
| 1 — native host and isolated helper | Actual pinned CLI/Dovetail with synthetic provider; durable retry/helper accounting; first authentic OAuth receipt trial failed with $0.7554 retained | Live scoped game action, qualified OAuth exposure/receipts and enforced helper/worker isolation; D11 source/synthetic accounting delivered |
| 2 — authentic locked installations | Official vanilla/E9E boots; vanilla join; failed Mineflayer E9E negotiation retained | Complete role/config provenance, five failed effective files, sealed locks and fallback conformance |
| 3 — ordinary game mechanics | Vanilla mine/walk/chest/player/table craft with saved references; separate Forge server-confirmed 3-ingot processing/collection, modded mayapple and expert furnace craft with exact saved resources | Selected G0 mechanics evidenced; retain failed samples and complete profile/reference qualification under other rows |
| 4 — cancel/reconnect without duplicate mutation | Selected vanilla and Forge cancellation/restart, immutable authority, exact receipt/state/cost continuity pass; reusable staging now exercised authentically | Reliable stop remains failed: pair04 phase2 exceeds 500 ms despite phase1 pass; complete applicable fault cases and profile qualification remain |
| 5 — private server-verified milestone | Private telemetry/resource witness; source registration/conflict detection; signed-spool source/Java/Python controls and authentic signed craft/team/mode points with saved-resource corroboration; outer pair remains uncertain | Authentic score provenance, setup/team/ingress authority, full positive/negative controls and enforced nonleakage |
| 6 — complete costs, time and evidence | Durable native dispatch/action journals, resource deltas and clocks | Join the host/game/private evidence under qualified locks and full root/helper accounting |

G0 remains incomplete. Item 3 has selected authentic mechanics evidence; items 4/6 have authentic cumulative restart evidence; pair02's two shutdown failures and pair04's phase2 shutdown failure remain retained. Advance independent M0 implementation; do not rerun unchanged live profiles to seek a passing sample.

## Milestone plan

| ID | Owner | Dependencies | Required deliverables / exit | Status | Implementation / evidence | Next action |
|---|---|---|---|---|---|---|
| M0 | GI; AR owns host seam | Execution prerequisites | Mineflayer/host vanilla slice followed immediately by exact E9E API/recipe/machine conformance, cancel/reconnect, private milestone and complete charges; G0 | in_progress | [M0 foundation evidence](docs/verification/2026-09-18-m0-foundation.md), child items below | Complete local gaps and resolve actual acquisition/auth/isolation prerequisites; execute real vanilla/E9E/host tests. |
| M1 | PL | M0 | Typed Python/TypeScript/conditional Java contracts, scoped local CLI, durable controller, capability isolation; full keybinding skill/extension T05; G1 | in_progress | [Core services](docs/verification/2026-09-18-controller-evaluator.md), M1.1–M1.4; contracts/storage/grants/settings workflow implemented partially. Actual isolation and Forge adapter remain open. | Complete child integrations and preserve the named exit gate; no milestone closure. |
| M2 | QA | M1 | Durable single-agent play, input fencing/watchdog, complete snapshots, recovery, budgets/clocks and operational report; G2 | in_progress | [Budgets](src/mcbench/budgets.py), [clocks](src/mcbench/clocks.py), [checkpoints](src/mcbench/checkpoints.py); synthetic fault/recovery tests pass, full supervisor and real soaks open. | Complete child integrations and preserve the named exit gate; no milestone closure. |
| M3 | RS | M1 | Private fixtures/scorers/probes, artifact projections, ablations, pairing/analysis and canary tests; T10/T11/T13 | in_progress | [Private evaluator](evaluator/src/strata_evaluator/), artifact projections and scorer/analysis controls; live telemetry/probe runner/isolation open. | Complete child integrations and preserve the named exit gate; no milestone closure. |
| M4 | PL | M2 | Team communication, simultaneous capacity, atomic N-body admission, distinct accounts/routing; G3 | in_progress | [Admission](src/mcbench/controller.py), [messages](src/mcbench/communication.py); whole-team synthetic cases pass, measured simultaneous capacity and actual accounts open. | Complete child integrations and preserve the named exit gate; no milestone closure. |
| M5 | RS | M3, M4 | Development cost/power pilot, locked preregistration, confirmatory execution, report/export and operations handbook; G4 | in_progress | [Offline report builder](evaluator/src/strata_evaluator/cli.py), paired analysis and planning heuristic; no pilot, powered plan or confirmatory execution. | Complete child integrations and preserve the named exit gate; no milestone closure. |
| M6 | GI; RS owns calibration | M5 | Calibrated tasks/graduation/anchors, retention/transfer and separately conformant E6E/E2E modules; G5 | deferred | — | Required later release work; preserve all compatibility gates. |
| M7 | PL | Stable M5 workload and demonstrated need | Distributed workers/storage/scheduling and optional dashboard, with unchanged integrity/conformance guarantees | deferred | — | Activate individual extensions only on measured need or user request. |

Dependencies govern milestone closure. Shared foundation work can advance before an entire prerequisite milestone closes when its own inputs are available; this does not waive gates. M1's G1 includes probe-isolation evidence also developed in M3: start that minimal evidence in M1, then extend it in M3, avoiding a circular dependency. MVP is M0–M5; later mandatory work and conditional extensions remain separate.

### D01 child work items

| ID | Owner | Scope / affected coverage | Status | Evidence / next action |
|---|---|---|---|---|
| M0.1 | GI/AR | Pin Mineflayer/Node/TypeScript/plugins; worker/GameBackend/CLI; Dovetail structured delivery. F01/F03/F06/F16, C03/C06/C09, T01/T03/T04 | in_progress | [Worker](backends/mineflayer/src/worker.ts), [CLI](backends/mineflayer/src/cli.ts), [host inspection](src/mcbench/runtime.py); actual native Dovetail integration open. |
| M0.2 | GI/QA | Vanilla move/mine/craft/container state, filtering, local cancellation, stale/ambiguous actions and reconnect. F06/F09/N02/N03, C09/C15/C18, T03/T07 | in_progress | [Adapter](backends/mineflayer/src/adapter.ts), [inventory motor](backends/mineflayer/src/inventory_motor.ts), [pagination](backends/mineflayer/src/pagination.ts), children M0.2d–f. All action kinds now have development dispatch; use/attack/entity/chat explicitly report input-only `emitted`. Game postconditions/reference evidence, broader navigation/containers, reconnect and all real integration remain open. |
| M0.3 | GI | Exact E9E handshake/channels/registries, expert recipe, container and operating machine. F01/F05/F06, C04/C09, T02/T03/T10, G0 | in_progress | Mineflayer path remains blocked by the actual Forge rejection; D06's separately identified Forge candidate now has a read-only API foundation. This parent advances through M0.3b without resolving M0.3.3 or claiming a game pass. All ten mechanic children retained; [live evidence](docs/verification/2026-09-18-long-horizon.md), [fallback development evidence](docs/verification/2026-09-18-forge-game-api.md). |
| M1.1 | GI | Required keybinding skill plus capable Forge settings extension: repair/effect/persistence tests; stock Mineflayer rejects unsupported operations. F06, C10/C11, T05, G1 | in_progress | [Settings transaction engine](src/mcbench/controls.py), [sanitized skill](gameplay/skills/minecraft-keybindings/SKILL.md), synthetic repair/rollback/context tests; actual Forge extension and full T05 remain open. |

### M0 implementation children and exact-pack cases

The narrow `vanilla-development/1` profile is a development restriction, not an amendment to `structured-actions/v1` or a waiver of any required action. Owner roles below are accountable for the next task; all work in the 2026-09-18 foundation change was performed locally by Codex without gameplay subagents.

| ID | Owner | Deliverable / negative cases | Status | Evidence / remaining work |
|---|---|---|---|---|
| M0.1a | PL/GI | Three game records, local request, Python schemas/TypeScript generation; unknown fields/types/bounds | in_progress | [Contracts](src/mcbench/contracts.py), [remaining records](src/mcbench/records.py), all 13 example/schema checks in Python and TypeScript; full reference/integration/migration coverage remains open. |
| M0.1b | GI | Persistent worker, authenticated own-avatar transport, CLI, dependency/policy fingerprints | in_progress | [Worker/client](backends/mineflayer/src/), [allowlisted client packager](src/mcbench/packaging.py), actual packaged CLI/subprocess tests; OS isolation and live server routing unverified. |
| M0.1c | AR | Pinned native Codex/Dovetail execution, helpers, interrupts/resume and all-call accounting | in_progress | [Native runner](src/mcbench/native.py), [plugin evidence](docs/verification/2026-09-20-native-plugin.md), [helper lifecycle](docs/verification/2026-09-20-native-helper-lifecycle.md): actual CLI/plugin/tool/helper execution against synthetic providers. D11 estimate source/migration is delivered; OAuth all-request ingress, child admission/isolation and complete resume remain unqualified. |
| M0.1c.1 | AR/PL/SI | D04/D11 estimated usage, finite per-dispatch exposure and complete native call/retry/helper metering | in_progress | [Native dispatch evidence](docs/verification/2026-09-20-native-dispatch.md) covers local synthetic streaming/compaction/helper/restart paths. Identical request digests are distinct dispatches. Versioned API-equivalent estimates now have source/synthetic evidence. Next: actual OAuth all-call ingress, finite exposure and enforced boundaries under [validation admission](docs/operations/validation-admission.md). Exact OAuth billing conversion is not required for this initial estimate allowance; no production qualification issued. |
| M0.1c.1a | AR/PL | Durable reservation and dispatch-intent boundary; F03/F11/F16, N01/N03/N04/N06, C06/C20, partial T01/T04/T07/T12 | implemented_unverified | [Accounting implementation](docs/verification/2026-09-19-inference-dispatch.md) and [actual CLI synthetic integration](docs/verification/2026-09-20-native-dispatch.md) cover atomic reserve/intent, nested envelopes, receipt deduplication, distinct retries and retained unknowns without replay. Production accounting qualification remains under M0.1c.1c.2; do not restart the completed synthetic integration. |
| M0.1c.1b | AR/PL | Actual pinned CLI/local synthetic provider dispatch, job/request/helper reservation composition, streaming/compaction/retry/interruption/restart evidence | implemented_unverified | [Eight-case native fixture / 130 Python checks](docs/verification/2026-09-20-native-dispatch.md) pass; explicit envelopes, deduplicated receipts, retained unknowns and sealed atomic closure. Restart reopens an already classified interruption. Provider fixtures are deterministic; production OAuth transport, price/exposure and isolation are not qualified. |
| M0.1c.1c | AR/PL/SI | Bounded upstream parsing/forwarding, supervisor-loss no-replay, original project allowance and qualified production ingress/receipts | in_progress | Child .1c.1 supplies actual-CLI/synthetic-wire evidence. D11 resolves the outside-experiment question: zero opening experimental usage, original $10 API-equivalent estimate allowance. Child .1c.2 owns versioned migration, real ingress, finite exposure and boundary qualification. No exact OAuth-dollar conversion or supplied-VM input is pending. |
| M0.1c.1c.1 | AR/PL/QA | Synthetic upstream wire-usage parsing/forwarding, strict finite transport and abrupt supervisor-loss no-replay | implemented_unverified | [Wire/crash follow-up](docs/verification/2026-09-20-native-dispatch.md): nine actual-CLI cases pass; 15 ingress requests, 13 forwarded, eight settled/five unresolved, ten CLI jobs. Actual stream prefix precedes supervisor exit; independent held-job accounting goes 13-to-zero before fresh recovery. 165 relevant Python / final 30 transport checks pass. Synthetic-only; no OAuth proxy/price/bound or adversarial isolation qualification. |
| M0.1c.1c.2 | AR/PL/SI | Durable project spending authority and qualified live ingress, price basis, finite exposure, all-request/descendant receipts and isolation | in_progress | Child .2a implements D11 estimate semantics/migration with focused synthetic and pinned-CLI evidence. Actual OAuth ingress/exposure and helper isolation remain required under .2b and M0.1c.2b.2. |
| M0.1c.1c.2a | AR/PL | Versioned estimate basis, explicit preserved-authority migration, per-request valuations and finite exposure admission; F03/F11/F16, N01/N02/N04/N06, C06/C12/C20, partial T01/T04/T07/T12 | implemented_unverified | [Implementation and verification](docs/verification/2026-09-20-estimated-accounting.md): pinned standard Luna rates, conservative cache writes, typed evidence, migration snapshot preservation, root/helper/retry/summary aggregation and no replay. Actual CLI/local-wire estimate fixture passes; 114 affected Python checks passed before final additional guards. Durable original authority migrated at zero opening experimental usage without resetting historical fixture holds. Authentic OAuth qualification remains under .2b; no release gate closes. |
| M0.1c.1c.2b | AR/PL/SI | Actual OAuth all-request ingress and verified exposure, staged <=$1 trial within the original $10, root/helper/game/private evidence join | in_progress | Depends on enforceable M0.1c.2b.2 boundary. Arithmetic or operator evidence flags alone cannot qualify real ingress. Recheck the durable project account before any live call. |
| M0.1c.1c.2b.1 | AR/PL/SI | Bounded authentic first-receipt admission, independent prechecks and durable no-replay/unknown holds | implemented_unverified | [Failed live trial and source fixes](docs/verification/2026-09-20-native-oauth-conformance.md): 9-call/38-check native synthetic preflight; one real request fails without usage; $0.7554 held once, original $10 unchanged. Focused final conformance/transport/gateway suite: 88 pass. Actual OAuth receipt and production qualification remain failed/unresolved. |
| M0.1c.1c.2b.2 | AR/SI | Pin native model startup metadata in the private sealed launch without changing provider fields | implemented_unverified | [Catalog evidence](docs/verification/2026-09-20-native-oauth-conformance.md): 23 catalog/integrity checks; actual CLI metadata-only loading passes narrowly with no inference/model-catalog HTTP; denied background plugin lookup and initial audit race retained. Changed native exec profile still requires conformance; no receipt reconciliation. |
| M0.1c.2 | AR/SI | Actual pinned Dovetail/native skills, tools, helpers and enforceable inherited-context boundaries | in_progress | Children preserve native discovery, invocation and helper/isolation contracts separately. F03/F07/F11/F16, N01/N03/N04/N06, C06/C18/C20; partial T01/T04/T07/T12. Synthetic native plumbing does not qualify live reasoning or security. |
| M0.1c.2a | AR/QA | Native six-skill implicit catalog, two explicit-only skill injections, real skill-file/tool response, disabled-plugin and nested-fixture negatives | implemented_unverified | [Native plugin probe](tools/native_plugin_probe.py) and [evidence](docs/verification/2026-09-20-native-plugin.md). Pinned real CLI/plugin and synthetic provider; long-path Git inventory and inline TOML configuration tests pass. Preserve prior failures and source hashes. No production qualification. |
| M0.1c.2b | AR/SI | Scoped native command/helper seam, clean contexts and denied file/process/network/operator/fixture access; immutable initial skills and admitted learned overlays | in_progress | [Actual canary failures](docs/verification/2026-09-20-native-boundary.md) retain unauthorized file/loopback results; elevated enrollment denies the file read but loopback still succeeds. Next: enforce the smallest native capability/process boundary on available hardware, then recheck permitted access and all affected negatives. Native/helper production isolation remains unqualified. |
| M0.1c.2b.1 | AR/SI | Actual native Windows file/network canaries with permitted-workspace controls | implemented_unverified | [Five retained samples](docs/verification/2026-09-20-native-boundary.md): narrow file controls pass in the prepared elevated sandbox command, but the unapproved loopback endpoint is reachable. Unelevated named-read restrictions refuse startup. Probe implemented; required qualification result fail. Process/helper/alternate-path/IPC/egress matrix remains open. |
| M0.1c.2b.2 | AR/SI | Enforceable native boundary and exact agent/helper profile bootstrap | in_progress | Existing arbitrary-loopback canary failure is retained. Resolve access to private evaluator, credentials, raw game/admin interfaces and sibling state through the smallest enforceable capability/process boundary. A VM is one implementation option, not a resource the user must supply before engineering can continue. Preserve the full selected native-runtime/helper contract and T06; no qualification or isolation waiver. |
| M0.1c.2b.2a | AR/SI | Supported native tool restrictions and root/helper protected-broker identity seam | in_progress | [Restricted-tools report](docs/verification/2026-09-20-restricted-native-tools.md): actual CLI/Dovetail, synthetic provider, shell absent and owned outside-workspace patch denied. Implemented broker projections, helper result permissions and executor worker forwarding pass an actual-CLI/synthetic-worker fixture. Complete read/network/process negatives, actual skill integration and live admission remain unqualified. |
| M0.1c.2b.2b | AR/SI | Candidate root/helper inherited-instruction, file/resource, disabled-tool and loopback canaries | implemented_unverified | [Actual pinned native-tool evidence](docs/verification/2026-09-20-native-broker-canaries.md): changed profile, owned targets and synthetic provider/worker; positive controls and explicit negative outputs pass. This does not supply complete protected-bootstrap/live enrollment, Dovetail artifact or production isolation qualification. |
| M0.1c.2b.2c | AR/PL/SI | Native stdout-bound participant identity, clean initial helper context, nested request budgets, broker lifecycle and sealed closure | implemented_unverified | [Admission evidence](docs/verification/2026-09-20-native-admission.md): 102 focused checks pass; actual CLI clean helper passes six calls/84 fixture units; inherited-context request denied before forwarding/reservation in separately declared private-profile sample, four root calls/56 units. Retain failed ephemeral full-fork sample. Protected launch/ingress, live qualification and full helper lifecycle remain open. |
| M0.1c.2b.2d | AR/SI | Sealed native/broker/plugin/import configuration, isolated bootstrap, immutable file leases and active mutation/import negatives | implemented_unverified | [Bootstrap evidence](docs/verification/2026-09-20-native-bootstrap.md): 104 affected checks, then 14 final focused checks; native sealed root/helper fixture seven calls/98 fixture units and changed-profile canaries nine calls/126 units pass. Live write-open denial and final dependency/scope checks pass. Three failed preliminary samples retained. Authenticated ingress, OAuth credentials, complete OS/resource/lifecycle and actual skill/artifact integration remain unqualified. |
| M0.1c.2b.2e | AR/PL/SI | Authenticated native job/profile/request ingress, persistent revocation, header separation and admission before child/request reservations | implemented_unverified | [Ingress evidence](docs/verification/2026-09-20-native-ingress.md): 99 affected checks, then 27 final ingress checks pass; actual sealed CLI root/helper fixture seven settled calls/98 synthetic units, seven unauthorized clients rejected before capture/reservation, secret absent from context/journal. Upstream OAuth credentials/transport, complete isolation and live qualification remain open. |
| M0.1c.2b.2f | AR/PL/SI | Native-owned OAuth header capture, bounded protocol-header preservation, fixed HTTPS upstream and private qualification gate; shared receipt accounting | implemented_unverified | [OAuth transport evidence](docs/verification/2026-09-20-native-oauth-transport.md): 106 affected checks and final 19 OAuth tests pass. Two actual-CLI/fabricated-cache samples settle 6 + 7 requests to 84 + 98 fixture units; final owned-upstream header parity and all 21 checks pass. Production gateway/lifetime, actual TLS/account/receipts/exposure, cache renewal and full boundary remain unqualified. |
| M0.1c.2b.2g | AR/PL/SI | Profile-bound finite gateway admission, bounded HTTP handlers, transport cancellation, listener ownership and exact native closure | implemented_unverified | [Gateway evidence](docs/verification/2026-09-20-native-gateway.md): 58 gateway/transport and 102 affected native tests pass; actual pinned CLI six root/helper calls settle to 42 microUSD estimates on synthetic token counts, 22 checks pass. Unknown usage holds survive shutdown; no real OAuth qualification or allowance consumption. |
| M0.1c.2b.2h | AR/SI | Immutable exact Dovetail bodies through the restricted broker, native invocation policy and declared capability limits | implemented_unverified | [Skill-read evidence](docs/verification/2026-09-20-native-gateway.md): final 16 skill/gateway tests pass; changed actual native profile six calls/42 synthetic-token estimate microUSD and all 24 checks pass. Eight bodies per participant; exact body returned to root/helper. Supporting files, scripts, learned activation/export and full helper lifecycle remain required. |
| M0.2a | GI | Bounded player/window projection, ray occlusion, filtered-map planning, ordinary mutation subset | in_progress | Filtered player/window observations, opaque fixed-capture spatial pages, bounded public signals, player-unlocked recipes and fixed crafting slot motor; placement and furnace/table opening implemented but authentic behavior unverified. Remaining action/movement/reconnect gaps persist. |
| M0.2b | GI/QA | Journal, one executor/lane, ID/sequence/epoch fencing, stop/cancel and retained partial effects | in_progress | [Journal](backends/mineflayer/src/journal.ts), [lane](backends/mineflayer/src/actions.ts), fault fixtures pass; real interruption timings, corruption/disk faults, supervised termination and automatic resync open. |
| M0.2c | GI/AR/RS | Real vanilla server, host action/helper, private milestone and full clocks/costs | in_progress | Actual official server, authenticated worker, scoped CLI, look/dig/flat movement and cancellation evidence in [long-horizon report](docs/verification/2026-09-18-long-horizon.md). Native model/helper, private authoritative milestone and complete clocks/costs still blocked; no gate pass. |
| M0.2c.1 | QA/RS | Reusable private native/worker/server cost and clock reconciliation; F09/F11/F13/F16, N01/N03/N04/N06/N08, partial T07/T12/T13 and G0 item 6 | in_progress | [Cost join](docs/verification/2026-09-20-run-costs.md) implements the read-only hash-pinned join; 14 focused synthetic cases and retained actual control-04 reconciliation pass. Preserve ambiguous outcomes; qualified host/helper costs, isolation and full timing/role locks remain separate gates. |
| M0.2c.1a | QA/RS | Complete stopped native/public journal continuity and costs across increasing epochs under one authority | verified | [Restart cost join](docs/verification/2026-09-20-run-costs.md): focused synthetic failure cases and authentic Forge pair pass full prefixes, retained receipts/counters, immutable authority/fingerprint, distinct boots and incremental charges (27 + 4 = 31). Both shutdown audits fail; this narrow join does not qualify shutdown, complete checkpoints or project accounting. |
| M0.2c.2 | RS/SI | Explicit private scorer instance/campaign/source binding and semantic receipt conflicts; F04/F09/F10/F13/F16, N01/N02/N04/N06/N08, C18/C24, partial T01/T06/T07/T10/T13 and G0 item 5 | implemented_unverified | [Source/receipt binding](docs/verification/2026-09-20-scorer-scope.md), [operator API](docs/operations/private-scoring.md): reproduced cross-campaign false completion, then 112 focused cases pass in 1.70 s; targeted Ruff passes. Authentic source admission/setup/team authority, isolation and full controls remain unqualified. All output remains explicitly unqualified. |
| M0.2c.3 | GI/RS/SI | Private producer-key/boot/source authentication before telemetry inspection; unchanged raw-score exclusion and complete setup/team/control gates | implemented_unverified | [Signed telemetry implementation and evidence](docs/verification/2026-09-20-authenticated-telemetry.md): module 0.3.3/config 3, fresh operator key/challenge, consumed boot claim, exact bytes/sequence/chain/scope and quota checks. 136 Python and 20 Java tests plus actual-JVM/synthetic CLI control pass. Fixed explicit-null omission found by cross-language execution. Selected actual dedicated stream now passes narrowly in M0.2c.3a; process/key isolation, setup/team authority, online ingress, controls/parity and recovery remain required. |
| M0.2c.3a | GI/QA | Exact changed-module dedicated E9E signed-stream, scope/recipe/termination and source-preservation reference | verified | [Authentic reference](docs/verification/2026-09-20-authenticated-telemetry.md#authentic-dedicated-reference): source ec15bbd/module 0.3.3, private clone and fresh grant, 13 signed records/186 sampled ticks, six recipe assertions, four derived negative controls and unchanged 18,215 original files. Server 156.203 s, normal stop, no client/model. Actual writer rejects the consumed authentic grant in a plain JVM without altering evidence. Narrow stream verification only; no scoring, OS isolation, guardian or full recovery pass. |
| M0.2c.3b | GI/RS/SI | Bind authenticated source to sealed setup/team/recipe/resource authority and private positive/negative scoring controls | in_progress | M0.2c.3b.1 now verifies/preserves actual fixture/evidence bytes and joins the setup-bound signed source to registered roster/resource candidates. Signature and operator registration alone cannot establish fixture validity or a score. Continue from the implemented stream importer and retained authentic craft witness; preserve raw-score exclusion until complete provenance/control evidence exists. |
| M0.2c.3b.1 | GI/RS/SI | Complete private fixture/evidence byte seal, setup-bound authority v2, durable single launch reservation and replay-safe native resource/roster/recipe/window join | implemented_unverified | [Source/synthetic evidence](docs/verification/2026-09-20-craft-reference-seal.md): 133 affected Python, final 35 reference, 20 Java and package checks pass. Actual operator CLI plus production JVM writer joins one synthetic resource candidate and replays identically; consumed grant re-admission rejects. No scorer state or qualified score; actual protected launch/setup/team controls remain open. |
| M0.2c.3b.2 | GI/SI/PL | Bind sealed one-use reservation to owned launcher, exact game directory/configuration/artifacts and actual server process without replay | in_progress | [Owned launch implementation and authentic evidence](docs/verification/2026-09-20-reference-launch.md): one-use durable dispatch, reviewed non-restarting bootstrap, immutable file leases and signed native identity joined to retained Job handles. Source/JVM fault checks and one authentic Forge reference pass narrowly. .2a is verified; .2b and complete setup/launch authority remain open. |
| M0.2c.3b.2a | GI/SI/PL | Bind signed native boot PID/start/executable/world/module to retained owned-process handles; retain terminal/uncertain evidence and reject reuse | verified | [Exact profile and audit](docs/verification/2026-09-20-reference-launch.md#authentic-changed-profile-reference): actual CLI/E9E/telemetry 0.3.4, 13 records, 207 sampled ticks, six retained/signaled members, no forced stop; all 18,226 original files unchanged. JVM wrong-world/hang/missing-stop/early-exit and input/identity negatives reject. This is the named launch-binding reference only, not scoring, mutable-file isolation or guardian qualification. |
| M0.2c.3b.2b | GI/SI/PL | Exclude concurrent mutable-world/config writers across sealed preflight and native boot; join full protected setup authority | not_started | Immutable software/key leases and native world paths do not protect mutable world/config bytes against concurrent same-user writers. Implement and qualify that ownership seam on available hardware alongside the existing native tool/broker boundary; no VM prerequisite or scoring admission is implied. |
| M0.2c.3b.3 | GI/RS/SI | Native setup/admin/mode/pack-team facts and authentic joint craft positive/negative controls before protected scoring | in_progress | [Native observation implementation and startup evidence](docs/verification/2026-09-20-native-setup.md) adds pinned read-only point capture, strict signed adjacency and registered native team mapping in reference-plan v2. Real startup facts agree with sealed NBT/properties/ops; the [changed craft reference](docs/verification/2026-09-21-native-craft-points.md) adds matching actor/team/mode points and saved consumption, but an uncertain outer monitor blocks import. Complete joint controls, mutation history, isolation and parity remain open. |
| M0.2c.3b.3a | GI/SI/RS | Native mode/admin/FTB point capture, strict source/sequence binding and versioned expected-team reference joining | implemented_unverified | [Source/startup evidence](docs/verification/2026-09-20-native-setup.md), plus [authentic craft points](docs/verification/2026-09-21-native-craft-points.md): actor/team/mode points and resource-consuming craft agree. Derived negative point controls reject, but are not separate authentic trajectories. Continuous setup authority, joint controls and score qualification remain open. |
| M0.2c.3b.3b | GI/RS/QA | Owned sealed version-2 authentic client craft, registered native team and required joint positive/negative controls before scoring | in_progress | [Changed authentic reference](docs/verification/2026-09-21-native-craft-points.md) produces the expert craft, matching native actor/team/mode and saved resources; 74 primitives reconcile. Pair remains UNCERTAIN on process inventory; 27/29 audit checks pass, score import denied. Prior body/exposure/abrupt-stop failures retained. Resolve monitor fault and history/isolation/parity/ownership/joint controls. |
| M0.2c.3b.3b.1 | GI/PL/QA | Versioned native-bound readiness and finite external participant window, exact terminal-report retention and uncertain-import/replay denial | implemented_unverified | [Source/JVM evidence](docs/verification/2026-09-20-reference-participant.md), [changed authentic reference](docs/verification/2026-09-21-native-craft-points.md): full worker exposure admitted, exact completed receipt and normal server stop retained. Outer uncertainty still denies qualification/import. Historical failed receipts and all thresholds retained. |
| M0.2c.3b.3b.2 | GI/PL/QA | Strict preregistered endpoint/body/team/fixture/module/exposure binding enforced before production participant dispatch | implemented_unverified | [Binding source/first failure](docs/verification/2026-09-20-reference-client-binding.md), [CLI correction](docs/verification/2026-09-20-native-craft-reference.md), [new authentic body/team agreement and full worker admission](docs/verification/2026-09-21-native-craft-points.md). Complete participant qualification remains denied by the outer monitor fault. No historical failure erased. |
| M0.2c.3b.3b.3 | GI/PL/QA | Typed outer-monitor errors, bounded abort/report/cleanup coordination and honest interrupted-reference recovery | in_progress | [Abort component](docs/verification/2026-09-20-reference-abort.md) and [durable outer pair](docs/verification/2026-09-20-reference-pair.md) implemented with source/owned-process evidence. Actual changed Forge pair remains unqualified. Preserve the abrupt reference, missing reports and unrecorded historical Fault cause. |
| M0.2c.3b.3b.3a | GI/PL/QA | Scope-bound typed aborts, server cleanup coordination, independent participant process guard and negative controls | implemented_unverified | [Private abort module](evaluator/src/strata_evaluator/reference_abort.py), [launcher](evaluator/src/strata_evaluator/reference_launch.py), [tests](tests/test_reference_abort.py). 97 affected checks pass; actual module CLI v2/v3 and package exclusion pass. Windows/Python/pure-JVM fixtures, not Minecraft or actual outer pair integration. No score/guardian qualification. |
| M0.2c.3b.3b.3b | GI/PL/QA | Durable outer pair monitor/client-driver integration, finite hard fallback and interrupted-run terminal reconciliation | implemented_unverified | [Pair source/fixtures](docs/verification/2026-09-20-reference-pair.md), [authentic integration and diagnostic correction](docs/verification/2026-09-21-native-craft-points.md): late inventory fault remains uncertain despite completed client, normal server stop and 112/11/6 complete terminal histories. Exact API stage now retained before cleanup; 109 affected and 37 overlapping guard/package checks pass after resolving explicit fixture skips. One owned churn case does not reproduce the failure. No retry, history waiver or threshold change. |
| M0.2d | GI | Captured-region pagination, opaque expiry, delivery-only map promotion and stale/hidden/dimension negatives | implemented_unverified | [Pagination tests](backends/mineflayer/tests/pagination.test.ts), actual local CLI/gateway with synthetic geometry; authentic LOS/cache/fresh-probe conformance remains unrun. |
| M0.2e | GI | Carried-stack projection, left/right pickup/quick-move and explicit equipment with authoritative resync | implemented_unverified | [Inventory tests](backends/mineflayer/tests/inventory.test.ts), eight synthetic cursor/resource/rejection/interruption cases; D07 explicit close is tracked across both backends under M0.3b.1b.2b.1c. Real server validation and additional window serializers remain open. |
| M0.2f | GI/QA | Bounded item use/release, observed-identity attack/entity interaction and ordinary chat | in_progress | [Gesture tests](backends/mineflayer/tests/gestures.test.ts); normal input dispatch returns `emitted`, without asserting gameplay success. Local cancellation and charged release fixtures pass; real effects, timings and action-specific server evidence remain open. |
| M0.2g | GI/SI | Operator Microsoft device sign-in, protected per-account cache, identity binding and cancelled-login fencing | in_progress | [Authentication seam](backends/mineflayer/src/authentication.ts), [operator command](backends/mineflayer/src/operator_auth.ts), [native ACL helper](backends/mineflayer/tools/auth_cache_acl.py); Windows ACL/cache tests and synthetic provider tests pass. Java-owning account authenticated and joined vanilla; old non-entitled account remains separately bound. Same-user gameplay isolation and credential expiry integration remain open. |
| M0.2g.1 | GI/SI/QA | Native startup session lifetime reservation, near-expiry refresh and immediate prelaunch recheck | implemented_unverified | [Session lifetime](backends/mineflayer/src/session_lifetime.ts) and [worker trials](docs/verification/2026-09-19-desktop-worker.md): optional provider cache-view filter preserves Microsoft/Xbox caches and rechecks returned expiry. Fourteen targeted tests and one package check pass. Retain the expired-token failure; two fresh-session prelaunch bounds and authenticated joins pass narrowly. Forced near-expiry refresh has pinned-provider synthetic evidence; production launch integration and full credential-recovery/isolation remain open. |
| M0.2h | GI/AR | Scoped CLI observation/action freshness in real play; keep strict CAS and no blind mutation replay | in_progress | [Earlier CLI failure](docs/verification/2026-09-19-vanilla-menu.md) retained. The unconditional heartbeat defect is now fixed; [authentic CLI smoke](docs/verification/2026-09-19-body-revision.md) passes idle/turn/age/menu cases. Complete native host/state-transition/coalescing qualification stays .2; the individual prior conflict was not conclusively attributed. |
| M0.2h.1 | GI/QA | Distinguish pinned Mineflayer idle position heartbeats from actual body changes; exact pose/motion/ground/dimension/body identity and freshness negatives | implemented_unverified | [Body tracker and evidence](docs/verification/2026-09-19-body-revision.md): exact body samples, capability minor 7, 112 Node/1 packaging test pass. Authentic CLI idle heartbeat acceptance, actual-turn revision rejection and unchanged two-second age rejection pass; cursor/grid returns and final saved seed verified narrowly. Real knockback/dimension/death/full movement transitions remain unqualified; no aggregate pass. |
| M0.2h.2 | AR/GI | Full native model/CLI freshness, state transitions, coalescing, deadlines and ordinary gameplay qualification | not_started | Local heartbeat repair and manual API checks cannot qualify native Codex/Dovetail command use or the full observation/action contract. |
| M0.2i | GI/QA | Vanilla crafting binds its selected recipe across unrelated unlocks; authentic navigation/mining/container/player/table craft and saved reconciliation | in_progress | Source review found that any recipe-book revision interrupts a partial craft, including normal unlocks caused by its output. Implement selected definition/authorization binding; preserve revocation/regrant/reset/redeclaration fencing. Build and nine focused recipe checks pass, including strict fresh-tool metadata. Authentic mining/walking/chest/player crafting now have saved references; epoch 5 table pickaxe and exact stopped-server metadata audit pass. [Narrow evidence and failures](docs/verification/2026-09-20-vanilla-mechanics.md); full T03 remains incomplete. |
| M0.2j | GI/QA | Terminal authentication/connection failure before first spawn fences startup with a sanitized reason | in_progress | Adapter/ActionLane now distinguish failed startup from pending connection. Actual pinned backend with a synthetic held auth lock plus three connection/fencing checks pass; real epoch 3 authenticated and joined after reviewed retirement of a dead owner's lock. No cache lock is automatically removed. F06/F09/F16, N02/N03, T03/T07/G0; full reconnect remains open. |
| M0.2k | GI/QA | Authentic in-flight cancel, disconnect, fresh-epoch resynchronization and durable known-receipt deduplication | in_progress | Selected vanilla result is .1; broader fault/restore and other profile coverage remain required. |
| M0.2k.2 | GI/QA | Authentic Forge cancellation, complete native/public journal restart, fresh epoch, known-receipt deduplication and saved-player continuity | in_progress | [Pair04](docs/verification/2026-09-20-forge-reconnect.md) passes corrected public cancellation, reusable staging/verification, full saved state and cumulative cost continuity (16 + 4 = 20). Phase1 full guardian proof passes 339.9197 ms; phase2 wait fails 508.2221/500 ms. Overall fail. Historical pair02/03 failures retained; no unchanged repeat or authority renewal. |
| M0.2k.2a | GI/QA | Reusable stopped native/public journal staging, immutable authority, retained unknowns/costs and interruption-safe publication | verified | [Staging](docs/verification/2026-09-20-journal-staging.md) has 22 unique focused cases exercised across implementation revisions, authentic expired-authority rejection, and successful actual pair04 staging plus pre-client byte verification and subsequent journal/cost audit. Narrow operator-attested journal continuity only; phase2 shutdown fails, complete checkpoints/admission/isolation remain unqualified. |
| M0.2k.2b | GI/QA | Public reference footprint proof for centered/edge/corner starts, with unchanged bounded cancellation route | verified | [Footprint correction](docs/verification/2026-09-20-reference-footprint.md): ten geometry cases and retained public reconstruction pass; actual pair04 cancellation succeeds from the two-support-cell off-center footprint and independent saved-state audit passes. Narrow reference selector only; no general geometry, full recovery, shutdown or isolation claim. |
| M0.2k.1 | GI/QA | Vanilla minor-10 N=1 move/cancel/fence, fresh epoch, historical receipt dedup, stale epoch denial and one new action | verified | [Independent saved-player/journal audit](docs/verification/2026-09-20-vanilla-reconnect.md) passes across retained fail/fail/fail/pass raw checker reports. Third checker incorrectly rejected documented resync-required cancellation; its failure remains. Fourth public sequence passes. All inventory NBT, prior receipts/event prefixes and costs preserved; 24 new primitives, total journal 61, 297.156 s. Full T07/G0 remain incomplete. |

| M0.3.1 | GI | Official E9E archives and exact bootstrap | in_progress | D05: actual exact client/server archives acquired and hashed; manifest confirms 1.19.2 / Forge 43.4.23. Both dedicated profiles and reviewed install-only bootstrap/JVM are prepared; exact mod inventories and a complete bootstrap-tree hash scan are recorded. Full role provenance, cold game restart and sealed PackLock remain open; [evidence](docs/verification/2026-09-18-long-horizon.md). |
| M0.3.1a | GI/QA | Reject wrapper-success masking server crashes/save failures; preserve raw logs and unqualified-stop distinction | implemented_unverified | [Server lifecycle repair](docs/verification/2026-09-20-server-save-integrity.md): bounded signature inspector and runner return failure for crash/save signals even when wrapper exits zero. Operation-05 produces 9 recognized signals. Absence is not complete clean-save proof; authentic replacement setup finishes stopped_unqualified in 199.422 s, with independent saved resource/orientation evidence; complete campaign/save provenance remains open. |
| M0.3.2 | GI | Cold-start expert config, recipe and quest assertions | in_progress | [Mode inspector](src/mcbench/pack_modes.py): 263/268 effective-file checks pass unchanged across cold restart; five findings retained. [Private runtime inspector](evaluator/src/strata_evaluator/telemetry.py) confirms expert furnace ingredients/output and vanilla-recipe absence in actual instrumented E9E boots. Quest/team, player crafting, independent reference and full mode acceptance remain open. |
| M0.3.2a | GI/QA | Exact-file mismatch diagnostics and source-backed review of all five overlay findings; F01/F05/F10/F16, N01/N04/N06/N08, C03/C04/C24, partial T01/T02/T10/T13 | implemented_unverified | [Review](docs/verification/2026-09-20-e9e-overlay-review.md): 15 local checks pass, unchanged 263/268 stopped-server result. Exact JAR/disassembly/nested-mod/original-archive evidence clarifies client/legacy settings without exclusions or config edits. Loaded behavior remains unqualified. |
| M0.3.2b | GI/QA | Private loaded config registration/spec/data, role applicability and cold-restart/reference equivalence | in_progress | Follow .2a with bounded read-only native evidence. Preserve all five file failures pending exact role/consumer disposition; no guessed migrations or relaxed threshold. Full expert recipe/quest/mechanics and instrumentation parity remain required. |
| M0.3.2b.1 | GI/QA | Bounded native config registration/spec/raw-value observations, versioned selector plan and strict private ingestion; F01/F05/F10/F16, N01/N03/N04/N06/N08, C03/C04/C18/C24, partial T01/T02/T10/T13 | implemented_unverified | [Telemetry 0.2.0 evidence](docs/verification/2026-09-20-e9e-loaded-config.md): 51 Python/11 Java checks pass, targeted Ruff/build pass. Corrected exact-selector boots have 34/32 clean records and identical six snapshots; four files unregistered, common list 145 entries exact, current Create values 8/400/10, three legacy keys undeclared/absent. Original placeholder-plan failure retained. No exclusions or full mode/consumer/client-role/mechanics/isolation qualification. |
| M0.3.2b.2 | GI/QA | Complete loaded client/server role applicability, source-backed legacy-consumer disposition, independent player/reference and mode/recipe/quest/mechanic assertions | in_progress | Server selected-config evidence alone cannot resolve all five file failures or certify mod caches/effects. Continue exact role/provenance and consumer review with the bounded evidence; unchanged file threshold and G0 fail. |
| M0.3.2b.3 | GI/QA | Private connected-client registration/spec/raw-data snapshots for the five unresolved file findings, bound to exact operator selectors | verified | [Authentic trial 01](docs/verification/2026-09-20-client-config-role.md) passes 18 independent process/artifact/plan/role/value/resource/cost checks. Two CLIENT files loaded; two legacy files unregistered; COMMON/Create snapshots equal dedicated server. Two safety releases/404.063 s, guardian 367.8943/500 ms. Narrow observation contract only; all five historical file failures and broader consumer/cold-restart/lock/isolation gaps remain. |
| M0.3.3 | GI | Exact Forge handshake and required channels | blocked | Actual case result **fail**: vanilla-style handshake rejected. [FML3 offer decoder](backends/mineflayer/src/forge_handshake.ts) decoded 233 mods / 111 channels / 39 registries / 2 custom datapack registries, with Quark's separate login message unsupported. No mod-channel claims/acknowledgments or game join; locked implementations and full handshake remain required. |
| M0.3.4 | GI | Namespaced modded registry/metadata | not_started | No modded decoder conformance. |
| M0.3.5 | GI | Exact-pack collision and navigation | not_started | Synthetic vanilla geometry cannot pass this case. |
| M0.3.6 | GI | Expert-altered recipe | not_started | No vanilla recipe substitution. |
| M0.3.7 | GI | Modded container transaction | not_started | Vanilla quick-move prototype cannot pass this case. |
| M0.3.8 | GI | Operating machine, energy and fluid | not_started | Actual operation with server evidence required. |
| M0.3.9 | GI | Player-accessible recipe and quest surface | not_started | No hidden global dependency dump. |
| M0.3.10 | GI/RS | Private authoritative evidence and authentic reference parity | in_progress | Existing raw telemetry remains score-ineligible; .1 adds paired native resource evidence. Isolation, setup/team authority and full controls remain required. |
| M0.3.10.1 | GI/RS | Read-only exact server result-click resource witness and private qualification | in_progress | [Source and authentic control 05](docs/verification/2026-09-20-craft-witness.md): exact selected witness and saved resource audit pass, prior failures/gift control retained. Full setup/team authority, scoring controls, ingress/isolation and instrumentation parity remain unqualified. |
| M0.3.10.1a | GI/QA | Authentic selected expert furnace native click bracket, exact resources/callback/recipe and independent saved-state corroboration | verified | [Control 05](docs/verification/2026-09-20-craft-witness.md): minor 43/telemetry 0.3.1, resource witness passes at server tick 4297, one furnace from 5 andesite + 3 polished andesite. All other saved resources unchanged, no drops, 69 primitives/428.688 s. Guardian 373.5694/500 ms passes this run. Broader parent qualification remains open. |
| M0.3b | GI | D06 separate structured Forge client fallback for exact E9E, without changing the failed Mineflayer result | in_progress | Source-backed channel/registry assessment selects the existing SPEC 8.1/16.1 fallback. Candidate `forge1192-structured-development/1`; no campaign support or conformance claim. |
| M0.3b.1 | GI/SI | Native filtered observations, ordinary player action motor and private bounded API; hidden state and unsupported operations rejected | in_progress | Split into .1a read-only projection/transport and .1b motor. Registered object IDs and conservative visibility implemented; no raw packet/admin or desktop-input facade. [Runbook](docs/operations/forge-game-api.md). |
| M0.3b.1a | GI/SI | Filtered native state, bounded frozen pages, private HTTP and typed operator client; hidden/raw data, stale cursors and cross-protocol requests rejected | implemented_unverified | [Native runtime](java/forge1192-client/src/main/java/io/github/opencnid/strata/client/NativeGameRuntime.java), [Python client](src/mcbench/native_game.py); synthetic revision/transport checks retained. [Authentic title-screen API and transport checks](docs/verification/2026-09-19-forge-live-api.md) now pass after fixing loaded JarJar path hashing. [Connected E9E evidence](docs/verification/2026-09-19-forge-connected.md) adds real paged-state/schema/age/body checks; full visibility/reference/serializer/latency/isolation qualification remains open. |
| M0.3b.1a.1 | GI/QA | Loaded host/Union/JarJar artifact bytes and fingerprint policy; bounded reads, unsupported provider and writable-path rejection | implemented_unverified | [ArtifactFiles](java/forge1192-client/src/main/java/io/github/opencnid/strata/client/ArtifactFiles.java), six provider regression tests within 91 Java passes, actual corrected E9E boot. Hashing is not a sealed installation or malicious-mod/process boundary. Shared settings fingerprint changes remain unqualified for real repair. |
| M0.3b.1a.2 | GI/SI/QA | Actual read-only native API, connected paged snapshots, state/identity/age/cursor and visibility/isolation conformance | in_progress | [Connected E9E evidence](docs/verification/2026-09-19-forge-connected.md): 2,745 connected assertions over 20 pages/2,489 block rows, 6 pre-join plus 6 post-stop disconnected checks and 10 transport negatives pass through the private operator client. Complete visibility/reference/unsupported-serializer/isolation and scoped-worker qualification remain required. |
| M0.3b.1b | GI | Ordinary player action motor, filtered-map movement and bounded inventory/recipe operations after M0.3b.2 fencing | in_progress | Split into .1b.1 implemented subset and .1b.2 remaining actions. No authentic action completion or campaign support claim. |
| M0.3b.1b.1 | GI | Native `look_at`, `dig`, `interact_block`, `click_slot`; current state/delivered target/reach/menu checks and ordinary player calls | implemented_unverified | [Native motor](java/forge1192-client/src/main/java/io/github/opencnid/strata/client/NativeGameRuntime.java) compiles against pinned Forge; click-slot now uses .2b.1a's server-feedback/conservation path. Receipts report input-only `emitted`; synthetic motor/transport tests do not verify actual Minecraft effects. |
| M0.3b.1b.2 | GI | Remaining `move_to`, `place`, `equip`, `use_item`, `attack`, `interact_entity`, `craft`, `chat`, with filtered-map/bounded motor policies | in_progress | Split into .2a gestures and .2b navigation/inventory/recipes below. Preserve complete public action contract and authentic modded conformance. |
| M0.3b.1b.2a | GI/QA | Native bounded item use, observed-identity attack/entity interaction and ordinary chat; cancellation, ID reuse, occlusion/reach, commands and repeat prevention | implemented_unverified | [Native gestures](java/forge1192-client/src/main/java/io/github/opencnid/strata/client/GameGestures.java), pinned native runtime calls and cross-language policy updates; [67 Java / 96 Node plus final 17 Python checks](docs/verification/2026-09-18-forge-gestures.md). Actual Minecraft effects, mod input hooks, item-hold/polling and target/ray/reach behavior remain unverified. |
| M0.3b.1b.2b | GI/QA | Native `move_to`, `place`, `equip`, `craft`; filtered-map execution, resources, collision, menu revisions and server feedback | in_progress | Split placement/equipment/server feedback, navigation and crafting into .2b.1–3 below. Actual expert recipes/machines and M0.3b.3 stay required independently. |
| M0.3b.1b.2b.1 | GI/QA | Ordinary observed-face placement and explicit equipment; authoritative open-menu refresh, fixed slot motor, prediction rejection, conservation and cancellation | in_progress | .1a implements equipment/menu feedback; .1b implements initial placement with remaining mechanics explicit. [85 Java / 21 Node / 34 Python checks](docs/verification/2026-09-19-forge-inventory-placement.md). No authentic qualification. |
| M0.3b.1b.2b.1a | GI/QA | Explicit equipment and server-confirmed slot/cursor/conservation checks; bounded current-menu feedback, stale/replaced/late responses and uncertain cancellation | implemented_unverified | [Inventory motor](java/forge1192-client/src/main/java/io/github/opencnid/strata/client/GameInventory.java), [feedback fence](java/forge1192-client/src/main/java/io/github/opencnid/strata/client/GameMenuFeedback.java), private native refresh and synthetic faults. Actual native ordering/no-op/resource/recovery behavior remains unverified; custom menu serializers remain unsupported. |
| M0.3b.1b.2b.1b | GI/QA | Complete ordinary placement at an observed target, with requested face/item/reach and normal player constraints | in_progress | Initial delivered-support/adjacent-air `BlockItem` route compiles and projection/bounds tests pass. Qualified replaceable states, interactive-support/crouching behavior and exact-pack placement/resource effects remain required; no successful-placement claim from `emitted`. |
| M0.3b.1b.2b.1c | GI/PL/QA | D07 explicit close-window lifecycle across Forge/Mineflayer; window/revision/resource/capacity checks, ordinary close, confirmed own inventory, cancellation and no replay | in_progress | Split candidate (.1) from authentic qualification (.2); D07 fills the omitted close operation without implicit movement side effects or a requirement waiver. |
| M0.3b.1b.2b.1c.1 | GI/PL/QA | Typed close envelope, native and Mineflayer fixed motors, owned-resource/capacity/feedback fences, charges and cancellation | implemented_unverified | [Menu-close evidence](docs/verification/2026-09-19-menu-close.md): 153 Java / 107 Node / 95 selected Python pass. Strict current-window revision, cursor/grid return, offhand semantics, loss/gift/component/armor negatives and no-replay checks use synthetic game effects. Schema/capability versions updated; native candidate uninstalled. |
| M0.3b.1b.2b.1c.2 | GI/QA | Authentic vanilla/E9E menu close, cursor/grid return, full inventory, loaded mod hooks, interrupted/replaced menus and reference evidence | in_progress | [Authentic vanilla player-menu smoke](docs/verification/2026-09-19-vanilla-menu.md) passes empty/cursor/grid close, duplicate receipt and final saved seed count; six final actions/18 primitives. Full external menus, resource components/capacity, interruption/reference and all Forge cases remain unrun. CLI freshness sensitivity is retained as M0.2h. |
| M0.3b.1b.2b.2 | GI/QA | Native `move_to` using only delivered map cells, bounded local movement, collision/obstruction and cancellation | in_progress | Delivered authority (.2a), collision/planning (.2b), and ordinary movement (.2c) now connect for the level-walking development candidate. [126 Java / 21 Node / 28 Python evidence](docs/verification/2026-09-19-forge-movement.md). Full geometry and authentic effects remain open; no raw chunk route or implicit digging/placing. |
| M0.3b.1b.2b.2a | GI/SI/QA | Bounded immutable captured states, durable delivery-only map promotion, newer-state ordering, reset/eviction and hidden-page negatives | implemented_unverified | [Native map](java/forge1192-client/src/main/java/io/github/opencnid/strata/client/GameObservedMap.java) is wired to filtered captures and the forced delivery journal; four captured scenes and 1,024 delivered cells are bounded separately. [103 Java / 21 Node / 27 Python checks](docs/verification/2026-09-19-forge-delivered-map.md), including 12 new authority/reset/eviction/failure cases. New build not installed; authentic delivery and movement conformance remain open. |
| M0.3b.1b.2b.2b | GI/QA | Fixed bounded planner and collision queries through delivered states only; unknown cells/state dependencies reject, no implicit block edits or resource planning | in_progress | Split into initial candidate (.1) and geometry qualification/extension (.2). [115 Java checks](docs/verification/2026-09-19-forge-route-planning.md); an initial flat route cannot satisfy the full item. |
| M0.3b.1b.2b.2b.1 | GI/SI/QA | Level-walking search, native copied-state shape adapter, continuous support/clearance, clock/knowledge bounds and unknown-dependency negatives | implemented_unverified | [GameRoute](java/forge1192-client/src/main/java/io/github/opencnid/strata/client/GameRoute.java) and [NativeCollisionView](java/forge1192-client/src/main/java/io/github/opencnid/strata/client/NativeCollisionView.java) connect through NativeGameRuntime.planMove; 12 initial unit tests pass. All 13 [loaded native shape cases](docs/verification/2026-09-19-native-collision.md) now pass on minor34; original plain-JVM bootstrap failure retained. Native movement integration is recorded under .2c. |
| M0.3b.1b.2b.2b.2 | GI/QA | Qualify loaded-pack shapes and observation-only routes; extend level candidate to required representative geometry and modded collision | in_progress | All 13 native collision cases pass on exact E9E/Forge/minor34 using a non-input desktop, no world join/control; 20 read-only API checks and cleanup pass. [Native probe evidence](docs/verification/2026-09-19-native-collision.md). Then authentic observed routes and M0.3b.3 modded collision cases. Steps/jumps/vertical transitions and other block implementations currently reject; retain them as limitations until qualified. |
| M0.3b.1b.2b.2c | GI/QA | Ordinary bounded movement input, damage/obstruction/state-change interruption, charged active ticks, deadline/cancel/release and actual route effects | in_progress | Split candidate integration (.1) from authentic qualification (.2). Ordinary forward input, neutral/settling policy, local rechecks, charged ticks and release are connected. One authentic level walk and independent saved position now pass under .2; remaining movement cases stay open. |
| M0.3b.1b.2b.2c.1 | GI/PL/QA | Native forward motor, settings/input preconditions, per-tick charges, interruption and cross-language movement envelope/policy identity | implemented_unverified | [GameMovement](java/forge1192-client/src/main/java/io/github/opencnid/strata/client/GameMovement.java), NativeGameRuntime, GameBatch, worker/native capability minor 9 and Python client. [126 Java / 21 Node / 28 Python checks](docs/verification/2026-09-19-forge-movement.md); 11 new Java tests and movement envelopes reach actual JVM fixtures with synthetic bodies. Deployed in minor34; [one authentic level walk](docs/verification/2026-09-19-native-movement.md) now passes. Complete loaded-mod/input qualification remains open. |
| M0.3b.1b.2b.2c.2 | GI/QA | Authentic observed routes, loaded-mod input/physics, precision, interruption/release timing and server evidence | in_progress | Loaded native shape probe passes 13 cases. [Fresh observed level walk](docs/verification/2026-09-19-native-movement.md) passes public behavior, 15 private checks and six saved-player checks; one intent/24 primitives reconcile. Its shutdown and first terrain frame fail. [Earlier cancellation](docs/verification/2026-09-19-native-quest-cancel.md) stops inside target tolerance and remains failed. [Fresh bent-route cancellation](docs/verification/2026-09-19-native-cancel.md) passes 13 public calls/eight saved-player/thirteen reference checks during initial centering, one intent/20 primitives, and one 451.9577 ms guardian wait. Complete route traversal, interruption timing, geometry and loaded-mod cases stay open; no broader reliability claim. |
| M0.3b.1b.2b.3 | GI/QA | Native player-accessible recipe discovery and one-recipe bounded `craft`, including server feedback and exact expert recipe evidence | in_progress | Split discovery (.1), fixed recipe-book/grid/output/remainder motor (.2), and authentic expert qualification (.3). No global solution dump or guessed vanilla recipe substitution. |
| M0.3b.1b.2b.3.1 | GI/SI | Player-unlocked recipe-book projection, bounded pages, native serializer/ingredient validation and recipe-change fencing | implemented_unverified | [NativeRecipes/GameRecipes and scoped transport](docs/verification/2026-09-19-forge-crafting.md): actual-book adapter compiled, known-first resolution, bounded sorted pages, revision and exact-class/serializer checks. 144 Java / 23 Node / 38 selected Python synthetic checks pass; authentic book semantics/custom serializers remain .3.3. |
| M0.3b.1b.2b.3.2 | GI/QA | One requested recipe, ordinary grid fill/output/remaining-item transfers, menu/resource checks and charged/cancellable server feedback | implemented_unverified | [GameCrafting/native port](docs/verification/2026-09-19-forge-crafting.md): ordinary book fill, exact confirmed grid/output/remaining items, empty-slot capacity reservation, charged waits/clicks/refresh and durable cancellation/deadline/exhaustion tests. Partial grid/cursor effects preserved; new build uninstalled and authentic server-feedback ordering/effects remain .3.3. |
| M0.3b.1b.2b.3.3 | GI/QA | Authentic known-recipe source, expert ingredients/results/remainders, stale/menu/cancel/resource negatives and custom serializer adapters | not_started | Exact E9E proof and any JEI/custom recipe extension remain required under M0.3b.3; synthetic fixtures and native compilation cannot satisfy this item. |
| M0.3b.1b.4 | GI/QA | Cross-action authentic server references, resource/reach/mechanics and negative controls | in_progress | Makes the previously referenced but missing .1b.4 ledger entry explicit. Existing saved-player pose checks and narrow action receipts remain partial; [saved block references](docs/verification/2026-09-19-saved-block-reference.md) at .2c.3c.2b.2c.1 match 128 persisted IDs. All causal action, resource, reach, custom mechanic and failure cases remain required. |
| M0.3b.1b.4.1 | GI/QA | Fixed observed-outline targeting, thin/multipart geometry/reach/occlusion negatives, private native rejection diagnostics and authentic mayapple retry under fresh scope | in_progress | [Paired trial/repair](docs/verification/2026-09-19-paired-block-reference.md) retains ACTION_UNKNOWN, unchanged saved target and no native dig input. Minor 34 candidate: 439 Java / 42 Node Forge / 41 Python pass. [Fresh authentic trial](docs/verification/2026-09-19-outline-target.md) passes startup/identity, scoped mayapple dig and independent saved mayapple-to-air transition, 256/256 delivered IDs matched. Full geometry/reach/occlusion, diagnostic failure, resource/scoring and shutdown qualification remain required. |
| M0.3b.1b.4.1a | GI/QA | Preserve sanitized private native failures through mutation-unknown transport wrapping; actual HTTP negative paths, fencing/release, no replay/leaks, authentic observed-air rejection | verified | [Diagnostic repair](docs/verification/2026-09-19-native-diagnostics.md). Original worker-startup trial retains UNCLASSIFIED_NATIVE_FAILURE and failed offline diagnostic check. Build, 12 selected HTTP/JVM cases, package exclusion and 13 real E9E negative-audit checks pass. One action/no native intent, two safety releases, no private CLI leakage, saved 256/256 IDs agree. Parent geometry/resources/isolation and overall guardian stop remain unqualified. Public unknown/resync semantics and native code unchanged. |
| M0.3b.2 | GI/QA | Scoped game CLI/worker integration, durable action IDs, deadlines/leases/cancellation/reconnect and native action receipts | in_progress | .2a native safety foundation and .2b development worker/public routing implemented with synthetic evidence; .2c controller/aggregate accounting/external watchdog and authentic conformance remain open. [Evidence](docs/verification/2026-09-18-forge-worker.md). |
| M0.3b.2a | GI/QA | Process ownership, durable intent/delivery/primitive/terminal evidence, lease/epoch/sequence/deadline fencing, urgent cancellation and unknown recovery | implemented_unverified | [Native lane](java/forge1192-client/src/main/java/io/github/opencnid/strata/client/GameActionLane.java), 16 direct lane cases and six actual game JVM/HTTP cases with synthetic runtime. Killed JVM recovery and no-replay pass; real client watchdog/release/timing and game-state continuity unrun. |
| M0.3b.2b | GI/PL | Public scoped worker/CLI backend routing, actor grants, typed observation delivery, capability/source/body binding and asynchronous confirmed stop/release | in_progress | .2b.1/.2b.2 now provide an explicit Forge development route with scoped public grants and synthetic conformance; campaign controller grants and authentic qualification remain open with .2c. No automatic backend substitution. |
| M0.3b.2b.1 | GI/QA | Asynchronous stop confirmation, pending mutation exclusion, cancellation/stop-all fencing, bounded failure and journal-safe shutdown | implemented_unverified | [Worker lane](backends/mineflayer/src/actions.ts), gateway and worker shutdown changed; final 29 synthetic action/HTTP/CLI cases pass after a prior 74-test full Node run. [Evidence](docs/verification/2026-09-18-worker-release.md). Authentic backend release/latency remains unverified. |
| M0.3b.2b.2 | GI/PL | Native transport, asynchronous observation delivery, full batch/actor/body/capability binding, backend selection and public receipt mapping | implemented_unverified | [Forge broker](backends/mineflayer/src/forge_lane.ts), [transport](backends/mineflayer/src/native_game.ts), explicit worker factory/config and atomic native identity projection. Same CLI reaches the synthetic JVM, with scope/owner/replay/stop negatives. [90 Node / 58 Java / 21 Python evidence](docs/verification/2026-09-18-forge-worker.md). Authentic integration and controller grant/repair remain open. |
| M0.3b.2c | GI/PL/QA | Native primitive/clock reconciliation into aggregate budgets, repair/supervisor authority, external hung-client termination, archival/resource limits and actual isolation | in_progress | Split local broker primitives/observation clock mapping from aggregate/controller and external process/archival/isolation qualification below. |
| M0.3b.2c.1 | GI/PL | Native attempted-primitive high-water reconciliation, retained observation clock domains and conservative page capture bounds in the development broker | implemented_unverified | [Broker](backends/mineflayer/src/forge_lane.ts) retains native safety-release charges across epochs without refund or duplicate charge; raw source clocks and transport bounds remain private evidence. Synthetic JVM/page/restart tests pass; full clock/performance and aggregate ledger qualification remain .2c.2. |
| M0.3b.2c.2 | PL/QA | Controller input generations/repair holds, aggregate BudgetLedger settlement, ticks/performance/clock uncertainty and readiness receipts | not_started | Replace manual-conformance-only broker authority with the existing controller's qualified production flow; no OAuth/paid campaign dispatch before isolation/accounting gates. |
| M0.3b.2c.3 | GI/SI/QA | Independent hung-client process identity/fencing/termination, durable evidence resource/archival bounds and OS/process/network isolation | in_progress | Split process attachment/lease foundation from worker/bridge integration and deployment qualification below. A client-thread watchdog and honest unknown receipts do not stop a hung JVM. |
| M0.3b.2c.3a | GI/QA | Exact held Windows process identity, dedicated Java lifetime grant, independent challenge lease and kernel kill-on-guard-exit | implemented_unverified | [Process guard](src/mcbench/process_guard.py), [24 selected Python checks](docs/verification/2026-09-18-process-guard.md), including 17 guard cases. Disposable JVM identity/lease/crash/descendant/sibling tests pass; no production route is protected by this foundation yet. |
| M0.3b.2c.3b | GI/PL | Bind native bridge session/listener and worker to guarded process before arming; independent native-thread health, startup fencing and durable stop evidence | implemented_unverified | [Native process guard](src/mcbench/forge_guard.py), [worker supervisor](backends/mineflayer/src/forge_guard.ts), required version 2 worker config and pre-arm descriptor/generation checks. [95 Node / 51 Python plus final 20 Forge checks](docs/verification/2026-09-18-forge-guard-integration.md) cover actual synthetic listener/process-chain faults. Authentic behavior and production controller authority/launch containment remain .2c.2/.3c qualification work. |
| M0.3b.2c.3c | SI/QA | Durable evidence resource/archival bounds, complete process-tree launch containment, OS/process/network isolation and authentic interruption timing | in_progress | Split non-input-desktop launch/lifetime (.1) from remaining production isolation/resource/native qualification (.2). Private grant files, desktop separation and Job Objects do not establish a gameplay sandbox. |
| M0.3b.2c.3c.1 | SI/GI/QA | Operator-owned Windows non-input-desktop launch, suspended-before-job assignment, bounded lifetime and cleanup without shared-desktop input | implemented_unverified | [Launch evidence](docs/verification/2026-09-19-desktop-launch.md): twelve real disposable Windows launch/lifetime cases, six existing process cases and corrected package check pass. Actual hidden OpenGL 3.2 context/readback succeeds without changing input desktop. No Minecraft, input injection or desktop switch. Production native/guardian/security qualification remains .2. |
| M0.3b.2c.3c.2 | SI/GI/QA | Production client/guardian/launch integration, private visual evidence, resource bounds, OS/process/network/credential isolation and authentic timing | in_progress | Split bounded operator Java/guardian launch (.a) from private frames/full production qualification (.b). Desktop placement is not a security boundary or physical-input certificate. |
| M0.3b.2c.3c.2a | SI/GI/QA | Connect bounded non-input desktop Java launch to the independent challenge guardian; reviewed official installed startup, startup/stop evidence and failure cleanup | implemented_unverified | [Actual startup/lifetime evidence](docs/verification/2026-09-19-desktop-client.md): four disposable JVM fault/lifetime cases and package check pass; exact private-copy E9E title bridge plus twenty API checks pass, input desktop unchanged, guardian stop confirmed. Full production launch/identity/resource/fault integration remains .2b; no clean-checkpoint or gameplay claim. |
| M0.3b.2c.3c.2a.1 | GI/QA | Diagnose exact CTM startup cache concurrency and qualify an explicit pinned compatibility remedy | in_progress | B10 repeats during the [first native settings crash trial](docs/verification/2026-09-20-settings-crash-startup.md). Exact installed bytecode has unsynchronized HashMap get/put/clear and null negative entries; upstream issue agrees with the signature. Preserve failed samples; inspect loader/executor semantics before selecting a remedy. No silent mod removal/replacement or threshold change. |
| M0.3b.2c.3c.2b | SI/GI/QA | Private game-only frames, full Forge guardian/worker integration, resource enforcement, OS/process/network/credential isolation and native timing/input | in_progress | Split private bounded frame evidence (.1) from complete native/worker/resource/isolation qualification (.2). |
| M0.3b.2c.3c.2b.1 | GI/QA | Explicit operator request, private main-render-target PNG before display, graphics-state restoration, bounded lifetime/size/count, no replay or public image affordance | implemented_unverified | [Evidence](docs/verification/2026-09-19-private-frames.md): ten final Java tests; two actual decoded/inspected E9E title frames, wrong-screen/no-retry negatives, API continuity and guardian stop. Complete world/GUI/reference/GL-fault/overhead and production resource/isolation qualification remain open. |
| M0.3b.2c.3c.2b.2 | SI/GI/QA | Full Forge-aware guardian/worker, world/reference/input/focus/pointer parity, resources, security principals and archival integration | in_progress | Children below preserve world startup separately from authentic actions, full physical input and production isolation. |
| M0.3b.2c.3c.2b.2a | GI/QA | Native startup connection, connected bridge readiness, private world frames and independent server join/save evidence | implemented_unverified | [World startup evidence](docs/verification/2026-09-19-desktop-world.md): completed same-body unobstructed render gates startup; missing saved-server metadata uses the actual resolved TCP peer. Final 424 Java tests pass; fourth authentic run passes 2,745/10/6 assertions, ten 500 ms identity reads, two decoded/inspected world frames and 453 ms base-guardian stop. Three failed attempts retained; full production/failure-path qualification and first guardian failure remain open. |
| M0.3b.2c.3c.2b.2b | GI/QA | Full Forge-aware guardian, scoped worker/CLI, actions and native release/cancel under non-input desktop | in_progress | Operator trial prepared at private evidence root `2026-09-19-forge-worker-live-01`; 111 Node tests pass / 25 explicitly skipped, then all 37 Forge tests pass with the pinned JVM/Python fixtures enabled. These are contract/fixture checks, not authentic game evidence. Connect bounded fenced desktop startup to the worker-owned Forge guardian without conflicting exclusive owners; require actual authority/body/epoch, client-thread health, scoped action and cancellation evidence. |
| M0.3b.2c.3c.2b.2b.1 | GI/QA | Same-connection initial tag/recipe synchronization before native readiness; stale/replaced connection and incomplete initialization negatives | implemented_unverified | [Readiness repair](docs/verification/2026-09-19-forge-readiness.md): pinned handler/event audit and current-source synchronization plus later world frame. 433 Java tests pass, including 13 lifecycle cases. Candidate 06f29980… passes one authentic read-only world/transport/disconnection/frame/stop trial; full repeated timing, title-join/respawn/reload negatives and worker qualification remain open. Retain all prior failures. |
| M0.3b.2c.3c.2b.2b.2 | GI/QA | Authentic worker-owned guardian and public CLI look/dig/use/cancel/dedup/fencing, plus server reference and owned shutdown | in_progress | [Worker readiness report](docs/verification/2026-09-19-forge-readiness.md) and [external stop diagnostics](docs/verification/2026-09-19-stop-latency.md) retain earlier failures. [Direct timing](docs/verification/2026-09-19-stop-boundaries.md) adds 33 Python/10 Node checks and a narrow normal-stop pass. [Minor-34 trial](docs/verification/2026-09-19-outline-target.md) adds successful saved mayapple effect / 12 primitive charges, signaled but 503.6561 ms observed wait, and a separate startup lease-expiry failure before any action. Child .2.1 tracks startup; full actions/resources/shutdown qualification remains. All processes stopped; failures retained. |
| M0.3b.2c.3c.2b.2b.2.1 | GI/QA | Bounded child bootstrap/initialization liveness before public gateway readiness; actual event-loop health, phase evidence and hung/late/crashed startup negatives | in_progress | Retain [Worker-02 failure](docs/verification/2026-09-19-outline-target.md), whose exact slow phase is unproven. [Startup repair](docs/verification/2026-09-19-worker-startup.md): bounded post-import handshake, real child pulses, fixed initialization limit, strict IPC/early exit evidence and explicit backend imports. Initial 58-test run had 56 pass/two exit-evidence failures; corrected 13 process tests pass, final three early-failure repeats pass, package check pass. Authentic startup/phase order passes; rejection diagnostic and process-stop checks fail separately. Full production launch/identity/timing and failure qualification remain open. |
| M0.3b.2c.3c.2b.2b.2.1a | GI/QA | Build-time public schema validators with runtime byte binding, preserved semantics and fixed startup bounds | implemented_unverified | [Schema startup report](docs/verification/2026-09-20-worker-schema-startup.md): actual machine -03 bootstrap failure retained. 128 Node checks pass, 43 initially skipped; separate pinned Java/Windows run passes all 55 cases, including those 43. 2,467 differential cases, four stale-schema rejections, reproducible output and capability pinning pass; Python 63 and package exclusion one pass. Five idle-host real-child samples improve from 396–424 to 158–181 ms; loaded-game timing remains unverified. No deadlines or guardian thresholds changed. |
| M0.3b.2c.3c.2b.2c | SI/GI/QA | Full world/menu/machine reference, focus/pointer/physical-key parity, resource/archival and distinct security principals | in_progress | Split private saved-block references (.1) from remaining reference/input/resource/security qualification (.2). Preserve .1b.4 and T03/T05/T06/T07/T08/T09/T13 cases; screenshots, desktop separation and same-user ACLs cannot close these contracts. |
| M0.3b.2c.3c.2b.2c.1 | GI/RS/QA | Bounded exact-1.19.2 saved-block reference reader, malformed/version/coordinate/packing negatives, independent authenticated save/source binding and action-effect comparisons | in_progress | [Reader](docs/verification/2026-09-19-saved-block-reference.md): 79 synthetic parser tests and one package check pass. Retain the [failed paired trial](docs/verification/2026-09-19-paired-block-reference.md). [Minor-34 trial](docs/verification/2026-09-19-outline-target.md): five independently copied files at each stopped boundary, six comparison checks pass, 256/256 delivered IDs match; only selected mayapple becomes air and support stays unchanged. Saved arrow count falls 64 to 63 during use/cancel. Authenticated snapshot consistency and full causal/resource/scoring provenance remain required. |
| M0.3b.2c.3c.2b.2c.2 | SI/GI/QA | Remaining world/menu/machine/resource references, focus/pointer/physical-key parity, archival and distinct security-principal qualification | not_started | Retain the parent's complete scope and all T03/T05/T06/T07/T08/T09/T13 cases. A saved-block parser cannot satisfy menu/machine semantics, live reach/visibility, resource provenance, input parity or isolation. |
| M0.3b.3 | GI/RS | Modded metadata/collision, expert recipe/container/machine/quest operations and private reference evidence | in_progress | All M0.3.4–10 mechanic cases still required for this profile; native client loading alone is insufficient. The exact JEI query candidate is implemented_unverified under .3.1a/b; its authentic discovery/execution, custom machine/category/quest and full reference cases remain required. |
| M0.3b.3.1 | GI/SI/QA | Exact installed JEI player-visible recipe discovery through bounded focused queries, scoped CLI and strict source/visibility/body fencing | in_progress | [D08 query candidate](docs/verification/2026-09-19-jei-query.md) implemented across native/transport layers (.1a/b), with distinct discovery/book status and exact API/policy pins. Authentic qualification (.1c) and visible-but-locked execution (.1d) remain; no game support claim. |
| M0.3b.3.1a | GI/SI | Native JEI runtime lifecycle, exact API pin, bounded visible focused crafting projection and hidden/changed/unavailable negatives | implemented_unverified | [Query evidence](docs/verification/2026-09-19-jei-query.md): native plugin compiled against JEI 11.8.1.1034, mapped API hash pinned; 512-match/32-entry/32-KiB and cooperative timing limits, hidden-first filtering and lifecycle revisions. Seven new synthetic projection tests; complete 160 Java pass. Loaded runtime/UI/missing-version behavior remains .1c. |
| M0.3b.3.1b | GI/PL | Typed JEI query, Java/TypeScript/Python validation, scoped worker/CLI routing and source/body/capability binding | implemented_unverified | [Query evidence](docs/verification/2026-09-19-jei-query.md): strict recipes.query/recipe-query transport, private body binding stripped before public delivery, source journal, method/scope/extra-field negatives and Mineflayer unsupported rejection. 114 Node/76 Python pass, including actual CLI/HTTP/JVM with a synthetic recipe source. Forge minor 12; live integration remains .1c. |
| M0.3b.3.1c | GI/QA | Authentic JEI/UI visibility parity, hidden entries, reload/disconnect, expert definition and ordinary recipe execution | not_started | The containing minor-34 client now loads in the dedicated separate-desktop copy; this suite has not run. Compilation, startup and synthetic filtering do not qualify JEI visibility, plugin lifecycle or expert execution; manual execution candidate is .1d.1/.2 and authentic .1d.3. |
| M0.3b.3.1d | GI/QA | Ordinary single-recipe grid execution for player-visible JEI recipes absent from the unlocked book; source/recipe/menu/resource/remainder/cancel fences | in_progress | Split bounded manual grid motor (.1), explicit source selection/native transport (.2), and authentic qualification (.3). Existing unlocked-book and discovery checks cannot satisfy this item. |
| M0.3b.3.1d.1 | GI/QA | Exact one-recipe ingredient allocation, ordinary pickup/place-one/return with feedback at every step, resource/component/interruption negatives | implemented_unverified | [Manual craft evidence](docs/verification/2026-09-19-manual-craft.md): 36 own main/hotbar slots, 4,096 allocation visits, 2x2/3x3 shaped and shapeless fill; every click awaits feedback and exact non-result state. Existing output/remainder motor integrated. Ten new synthetic grid cases; native game effects remain .3. |
| M0.3b.3.1d.2 | GI/PL/SI | Explicit JEI selection in craft contract; visible focused source revision/generation and recipe revalidation; native and cross-language fail-closed routing | implemented_unverified | [Manual craft evidence](docs/verification/2026-09-19-manual-craft.md): recipe_selection carries query/source generation/initial revision; source visibility is checked before definition lookup and throughout input. Omitted/null retains book route; Mineflayer rejects before input. Strict schemas, source negatives and actual JVM transport over synthetic game effects pass. Full authentic binding/source/cancellation remains .3. |
| M0.3b.3.1d.3 | GI/QA | Authentic E9E manual expert craft, consumption/remainders, interruption and reference comparison | not_started | Requires candidate deployment, cleared operator security prompt and live guarded player tests. Synthetic clicks cannot close this item. |
| M0.3b.3.2 | GI/RS | Remaining custom recipe/category/ingredient, modded container/machine/energy/fluid, quest and reference adapters | in_progress | Split into scoped menu observation (.1), machine transactions (.2), additional discovery (.3), and authentic/reference qualification (.4). All required scope retained. |
| M0.3b.3.2.1 | GI/SI | Exact Thermal furnace/crucible current-menu projection: visible base/player slots and GUI energy/fluid; version/class/layout/hidden-context negatives | implemented_unverified | [Thermal menu evidence](docs/verification/2026-09-19-thermal-menu.md): installed bytecode/metadata inspection, three exact JAR hashes, fixed public getters and strict cross-language schema. 182 Java / 116 Node / 114 selected Python pass; final focused rerun 30 pass. Runtime versions omit build suffixes; corrected guards also require bytes. Augment-panel contents and machine mutation remain excluded; native GUI parity/version/layout failure paths still require .4. F01/F06/F16/N01/N04/N06, C09, T01/T03/T06. |
| M0.3b.3.2.2 | GI/QA | Ordinary modded menu/machine transactions, energy/fluid operation, processing races, server feedback and cancellation | in_progress | Split ordinary visible-slot transfers (.a), remaining routing/controls (.b), and energy/fluid operation (.c). Current inspection confirms native player-to-machine quick-move may enter hidden augment slots; that route cannot be silently enabled. |
| M0.3b.3.2.2a | GI/QA | Ordinary Thermal pickup/placement and machine-to-player quick-move; exact owned inventory/cursor feedback despite processing, no prediction-only confirmation/replay | implemented_unverified | [Transaction evidence](docs/verification/2026-09-19-thermal-transactions.md): conserved/scoped native prediction, actual full applied server feedback, exact owned slots/cursor, hidden-slot masking, D10 display-independent input fence, and unknown/fenced failures without replay. 200 Java / 116 Node / 114 Python pass, including 18 new Java cases. Native GUI/slot/feedback/mod-hook semantics remain unqualified under .4; full routing and energy/fluid effects stay .2b/.2c. |
| M0.3b.3.2.2b | GI/QA | Full required modded transfer/control coverage, including player-to-machine quick-move, augment-panel visibility/interaction and loaded mod hook semantics | not_started | Exact CoFH quick-move targets `invSize()`, including augments. Qualify a visible panel/control route before supporting that branch; ordinary pickup remains the initial explicit insertion route. |
| M0.3b.3.2.2c | GI/QA | Ordinary energy/fluid supply/extraction and operating-machine effects with material conservation and cancellation | not_started | Requires typed ordinary player interactions and .4's actual server/reference evidence; observing a tank or accepting a slot action cannot pass. |
| M0.3b.3.2.3 | GI/RS | Remaining custom recipe/category/ingredient and player-accessible quest adapters | in_progress | Split focused Thermal discovery (.a), other required custom categories/ingredients (.b), and player-visible quests (.c); no scope removed. |
| M0.3b.3.2.3a | GI/SI/QA | Focused exact Thermal furnace/crucible JEI recipes, item/fluid amounts, displayed energy/chance, visibility and strict query transport | implemented_unverified | [Thermal discovery evidence](docs/verification/2026-09-19-thermal-recipes.md): bounded non-hidden JEI layout projection, four exact artifact hashes, class/type/visibility guards, item/fluid focus and strict cross-language transport. Machine rows remain discovery-only and cannot enter craft selection. 207 Java / 117 Node / 131 Python pass; native game/JEI effects are synthetic. Authentic UI/reference/timing parity stays .4. F01/F06/F16/N01/N04/N06, C09, T01/T03/T06, G0.  [Connected E9E evidence](docs/verification/2026-09-19-forge-connected.md) adds bounded authentic reads; full UI/hidden/team/reference/action qualification remains open. |
| M0.3b.3.2.3b | GI/QA | Remaining required custom recipe categories and ingredient components/semantics | not_started | Retain unsupported tagged ingredients and other mod categories as explicit gaps; qualify each actual source and visibility policy. |
| M0.3b.3.2.3c | GI/RS/SI | Player-accessible quest discovery and progress with private evaluator separation | in_progress | Split visible chapter/quest catalog (.1), readable details/task/reward surfaces (.2), and ordinary quest interactions (.3); authentic qualification remains .4. No scope removed. |
| M0.3b.3.2.3c.1 | GI/SI/QA | Exact FTB visible chapter/quest catalog, own-team progress and detail-access flags, bounded scoped CLI/native transport | implemented_unverified | [Quest catalog evidence](docs/verification/2026-09-19-quest-catalog.md): three exact artifact hashes, fixed public client APIs, editing/membership/source guards, hidden-entry reader rejection, bounded projection and strict native/scoped transport. 214 Java / 118 Node / 148 Python pass; loaded FTB/UI/team/timing/isolation remain unverified under .4. F01/F06/F16/N01/N04/N06, C09, T01/T03/T06.  [Connected E9E evidence](docs/verification/2026-09-19-forge-connected.md) adds bounded authentic reads; full UI/hidden/team/reference/action qualification remains open. |
| M0.3b.3.2.3c.2 | GI/SI/QA | Player-readable quest descriptions, tasks, rewards and dependencies with all native hiding rules | in_progress | Split bounded readable text (.1), task/reward definitions (.2), and visible dependency/link surfaces (.3). Catalog visibility is insufficient for detail access; all authentic qualification remains .4. |
| M0.3b.3.2.3c.2.1 | GI/SI/QA | One visible quest's subtitle and paged readable plain description, with detail/text hiding and strict source bounds | implemented_unverified | [Quest text evidence](docs/verification/2026-09-19-quest-text.md): native visibility/detail/text gates, own-team/context pins, explicit page breaks/unsupported rich lines, bounded component/text projection and scoped CLI. 220 Java / 119 Node / 167 Python pass after correcting a CLI allowlist failure. Native parser/localization/UI/team/timing/isolation qualification remains .4; full rich content remains .2.3.  [Connected E9E evidence](docs/verification/2026-09-19-forge-connected.md) adds bounded authentic reads; full UI/hidden/team/reference/action qualification remains open. |
| M0.3b.3.2.3c.2.2 | GI/SI/QA | Visible task/reward definitions and own-team status with native reward blocking and invisible auto-claim gates | in_progress | Split bounded normal-tooltip/status pages (.a) from remaining player-opened item-alternative/choice/extension displays (.b). Ordinary interactions remain .c.3 and full rich representation .2.3; no hidden server commands or completion/claim bypass. |
| M0.3b.3.2.3c.2.2a | GI/SI/QA | Bounded normal task/reward tooltips, formatted progress and own-player claim state, with visibility/source/modifier fences | implemented_unverified | [Task/reward evidence](docs/verification/2026-09-19-quest-components.md): public FTB display APIs, blocked/invisible filtering before IDs/display, no raw counts/commands/NBT, strict query/role/bounds and scoped native/CLI transport. 228 Java / 120 Node / 187 Python pass with synthetic game effects. Exact external Library compile-only pin rejects missing/wrong bytes; candidate contains no FTB classes. Native callbacks/UI/team/modifier/timing/isolation remain .4; no aggregate gate changes.  [Connected E9E evidence](docs/verification/2026-09-19-forge-connected.md) adds bounded authentic reads; full UI/hidden/team/reference/action qualification remains open. |
| M0.3b.3.2.3c.2.2b | GI/SI/QA | Remaining player-opened item alternatives, choice reward details and extension task/reward displays | in_progress | [Installed-menu audit](docs/verification/2026-09-19-quest-menu-audit.md) informs item-menu candidate .1; choice/extension coverage remains .2. Ordinary fenced interactions stay .c.3 and full rich content .2.3. Submit callback and private choice-parent constraints remain binding. |
| M0.3b.3.2.3c.2.2b.1 | GI/SI/QA | Current item-alternatives menu, visible item tooltips and ordinary control state, with viewport/source/screen fencing | implemented_unverified | [Item-menu evidence](docs/verification/2026-09-19-quest-item-menu.md): exact public layout, own-team/task/detail guards, native scroll truncation/clipping before stack readers, bounded normal displays, source/screen/layout revisions and strict scoped CLI/native transport. 236 Java / 121 Node / 212 Python pass; 2 Node/1 Python final focused checks pass. No opening/scroll/submission/recipe navigation. Actual callbacks/viewport/UI/options/timing/isolation remain .4. |
| M0.3b.3.2.3c.2.2b.2 | GI/SI/QA | Choice reward menus and remaining extension task/reward surfaces | in_progress | Split exact choice opening-bound projection (.a) and remaining extension displays (.b). Do not read private fields or use raw tables to bypass menu access. |
| M0.3b.3.2.3c.2.2b.2a | GI/SI/QA | Exact choice reward menu, ordinary eligible opening and retained parent/source identity, bounded visible titles/tooltips | implemented_unverified | [Choice report](docs/verification/2026-09-19-quest-choice.md): current page/book/widget/eligibility fences, ordinary opening, ephemeral private parent binding and clipped public widget display; 285 Java / 130 Node / 254 Python pass, synthetic game authority. No raw table/claim route; native callback/viewport/reference/isolation qualification stays .4. |
| M0.3b.3.2.3c.2.2b.2b | GI/SI/QA | Other extension task/reward display surfaces | not_started | Individually qualify public native display callbacks and hiding/eligibility semantics; exact choice support cannot cover arbitrary extensions. |
| M0.3b.3.2.3c.2.3 | GI/SI/QA | Player-readable dependency/link surfaces and guide/rich content | not_started | Preserve visibility and UI affordances; no hidden graph solver, unbounded graph enumeration or automatic external fetch. |
| M0.3b.3.2.3c.3 | GI/QA | Ordinary bounded quest UI/submission/claim interactions, confirmation, cancellation and resource effects | in_progress | Split into .3.1–.3.3 below; no direct progress writes, administrative completion, or automatic hidden-answer exposure. Authentic mechanics/reference evidence remains required. |
| M0.3b.3.2.3c.3.1 | GI/QA | Open ordinary own-team quest book from gameplay, source/catalog/screen guards, charged one-shot dispatch and cancellation | implemented_unverified | [Opening report](docs/verification/2026-09-19-quest-open.md): pinned ordinary callback, exact local screen checks, strict ActionBatch, native/CLI transport, ten motor/journal tests. 246 Java / 123 Node / 214 Python pass; actual FTB/game effects and isolation unqualified. |
| M0.3b.3.2.3c.3.2 | GI/QA | Chapter/quest/task navigation, back and scrolling with visible control and screen binding | in_progress | Split current book state/basic chapter/quest/back/close (.a) from task/menu/scroll and other GUI contexts (.b). |
| M0.3b.3.2.3c.3.2a | GI/QA | Current own-team book state, catalog-bound chapter/quest navigation and ordinary back/close, with source/screen guards and retained effects | implemented_unverified | [Navigation report](docs/verification/2026-09-19-quest-navigation.md): exact public callbacks, bounded state, catalog-page/selected-object fences, charged one-shot navigation, retained effects and no replay. 257 Java / 126 Node / 230 Python pass, synthetic game authority; loaded UI/server/reference/isolation qualification remains .4. |
| M0.3b.3.2.3c.3.2b | GI/QA | Task opening, item/choice/menu back, scrolling and remaining normal GUI contexts | in_progress | Split visible item-task menu opening (.1), menu back/scroll (.2), other task/choice/recipe and UI contexts (.3), and occupied crafting-state resource lifecycle (.4). No scope removed. |
| M0.3b.3.2.3c.3.2b.1 | GI/QA | Open an ordinary item-task menu from the current visible quest detail, component-page selection and native widget/context fencing | implemented_unverified | [Task-opening report](docs/verification/2026-09-19-quest-task-open.md): exact public TaskButton callback, task-page/current-book/visible-widget fences, new-menu/parent confirmation, retained effects and charges. 264 Java / 128 Node / 232 Python pass, synthetic UI; initial CLI rejection retained as unresolved timing. Native viewport/callback/server/reference/isolation remains .4. |
| M0.3b.3.2.3c.3.2b.2 | GI/QA | Ordinary item/choice menu back and visible panel scrolling with parent/layout identity | in_progress | Split current exact item-menu controls (.a) from choice/other menu lifecycle (.b). Preserve clipping, parent identity, native wheel semantics and charged cancellation; no raw scroll-state write or submit bypass. |
| M0.3b.3.2.3c.3.2b.2a | GI/QA | Exact current item-menu Back and one bounded wheel gesture, source/menu/parent/layout fences | implemented_unverified | [Menu-action report](docs/verification/2026-09-19-quest-menu-action.md): pinned native callbacks, restored logical hover, local scroll/parent confirmation, retained effects/costs and no replay; 273 Java / 129 Node / 235 Python pass, synthetic UI authority. Initial fixture lease expiry retained and renewal lifecycle corrected. Authentic UI/resource/reference qualification remains .4. |
| M0.3b.3.2.3c.3.2b.2b | GI/QA | Choice/extension/other menu back and scrolling | in_progress | Split exact opening-bound choice controls (.1) from extension/other controls (.2); item-menu support does not cover them. |
| M0.3b.3.2.3c.3.2b.2b.1 | GI/QA | Exact opening-bound choice menu Back and attached-scrollbar wheel semantics | implemented_unverified | [Choice controls](docs/verification/2026-09-19-quest-choice-controls.md): ordinary Back, parent/reward/source/layout fences, native scrollbar/panel confirmation including negative maximum, retained cancellation/uncertain charges and no replay. 294 Java / 130 Node / 255 Python pass with synthetic UI authority. Native callback/drag/polling/pointer/viewport/resource/reference qualification stays .4; no claim path. |
| M0.3b.3.2.3c.3.2b.2b.2 | GI/QA | Other extension menu lifecycle and scrolling | not_started | Requires separately qualified visible menu/parent projections and native input semantics; no generic arbitrary-callback fallback. |
| M0.3b.3.2.3c.3.2b.3 | GI/QA | Other task/choice/recipe opening routes and normal GUI contexts | in_progress | Split exact choice opening (.a) from other required routes/contexts (.b); no scope removed. |
| M0.3b.3.2.3c.3.2b.3a | GI/QA | Ordinary eligible choice-reward opening and retained menu parent binding | implemented_unverified | [Choice report](docs/verification/2026-09-19-quest-choice.md), jointly implemented with .c.2.2b.2a. One charged exact callback, immediate/next-tick local confirmation, deduplication, cancellation and unknown-outcome fencing. Claims and real qualification remain open. |
| M0.3b.3.2.3c.3.2b.3b | GI/QA | Other task/recipe opening routes and normal GUI contexts | in_progress | Split exact non-consuming single-item recipe route (.1) from other task/UI contexts (.2). Native callback, resulting screen, parent return and readable affordances need separate qualification. |
| M0.3b.3.2.3c.3.2b.3b.1 | GI/QA | Exact non-consuming single-item task to JEI recipe screen and ordinary return lifecycle | in_progress | [Installed-route audit](docs/verification/2026-09-19-quest-jei-route-audit.md) and [lifecycle candidate](docs/verification/2026-09-19-quest-jei-lifecycle.md): .a opening/origin/close implemented but unverified; .b readable current-page and further navigation remain. No private parent/focus/page getter invented or raw graph exposed. |
| M0.3b.3.2.3c.3.2b.3b.1a | GI/QA | Task-to-JEI ordinary opening, explicit origin-bound recipe-screen state, and close to the retained quest book | implemented_unverified | [Lifecycle evidence](docs/verification/2026-09-19-quest-jei-lifecycle.md): exact runtime/helper/five-artifact pins, page/widget/source CAS, actual distinct screen, retained origin state and normal close; no replay or cost refunds. 304 Java / 131 Node / 262 Python pass with synthetic UI authority. Current recipe-page contents stay .b and authentic native/reference/resource/isolation qualification stays .4. |
| M0.3b.3.2.3c.3.2b.3b.1b | GI/SI/QA | Current JEI recipe-page projection, history/category/page navigation and full native parity for the task route | in_progress | Split actual-render provenance (.1), filtered copied page/public transport (.2), ordinary further navigation (.3) and authentic qualification (.4). Focused recipe lookup alone does not satisfy rendered-page parity. Preserve custom categories/ingredients under .c.3.2.3b. |
| M0.3b.3.2.3c.3.2b.3b.1b.1 | GI/SI/QA | Task-bound actual-render provenance with bounded complete-frame lifecycle and no graph read | implemented_unverified | [Render capture](docs/verification/2026-09-19-jei-render-capture.md): pinned optional draw-call hook, whole-screen Pre/Post, 32 private identities, runtime/origin/dimension/timeout fences. 314 Java cases pass including ten new synthetic renderer cases. Actual Mixin application, callbacks and frame semantics remain .4; opaque mutable layouts are not public observations. |
| M0.3b.3.2.3c.3.2b.3b.1b.2 | GI/SI/QA | Copied visible recipe-page content, labels, slot/ingredient clipping and typed public observation transport | in_progress | Split immutable actual slot draw operands (.a), remaining displayed labels/rich/custom/overlay semantics (.b), and complete source/body/schema/public transport (.c). Raw mutable layouts remain forbidden as observations. |
| M0.3b.3.2.3c.3.2b.3b.1b.2a | GI/SI/QA | Actual slot selection/draw operand pairing, geometry-before-content filtering, immutable bounded primitives | implemented_unverified | [Slot-copy report](docs/verification/2026-09-19-jei-slot-copies.md): exact native callbacks and 128-slot/32-layout/32-KiB bounds; clipped/unsupported data never read as ordinary item/fluid payload. Synthetic cases/native compilation are evidence only; .2c adds public transport and authentic .1b.4 remains. |
| M0.3b.3.2.3c.3.2b.3b.1b.2b | GI/SI/QA | Displayed category/page labels, rich/tagged/custom ingredients, decorators/overlays and remaining page content | in_progress | Split ordinary category/page header operands (.1) from rich/custom/overlay and remaining display semantics (.2); full native visibility qualification stays .1b.4. |
| M0.3b.3.2.3c.3.2b.3b.1b.2b.1 | GI/SI/QA | Actual category/page header draw operands, complete-frame binding, bounded text and typed transport | implemented_unverified | [Header evidence](docs/verification/2026-09-19-jei-page-headers.md): actual helper operands, ordered screen/category/helper/layout lifecycle, bounded Unicode, geometry-before-content and canonical cross-language transport; 342 Java / 293 Python / 134 Node pass with synthetic game authority. Native hook/Font/pose/viewport/reference qualification remains .1b.4. |
| M0.3b.3.2.3c.3.2b.3b.1b.2b.2 | GI/SI/QA | Rich/tagged/custom ingredients, category annotations, decorators/overlays, empty-layout pages and remaining displayed content | in_progress | Split empty-loop provenance and transport (.a) from remaining rich/custom/overlay content (.b). Preserve unsupported cases and full native visibility/input/reference qualification under .1b.4. |
| M0.3b.3.2.3c.3.2b.3b.1b.2b.2a | GI/SI/QA | Empty rendered layout list distinguished from missing/aborted draw hooks; bounded source/frame/digest transport and navigation confirmation | implemented_unverified | [Empty-page evidence](docs/verification/2026-09-19-jei-empty-page.md): ordinary predicate/draw/end witness, exact identity/freshness, headers/controls and zero-to-32 layout transport. 405 Java / 330 Python / 136 Node pass with synthetic renders. Compiled wrapper preserves one native predicate call; actual transformation, empty native pages and full UI/reference/isolation remain .1b.4. |
| M0.3b.3.2.3c.3.2b.3b.1b.2b.2b | GI/SI/QA | Remaining rich/tagged/custom ingredients, category annotations, decorators/overlays and full displayed content | not_started | Header/slot draw operands and empty-list handling do not establish full-page parity. Preserve all required representations and final overlay visibility checks. |
| M0.3b.3.2.3c.3.2b.3b.1b.2c | GI/PL/SI/QA | Typed public current-page observation, native/scoped CLI transport and source/body/lease/content fencing | implemented_unverified | [Transport evidence](docs/verification/2026-09-19-jei-page-transport.md): no-argument recipe-page/recipes.page and native recipe_page, explicit incomplete slot_draw_operands, strict digest/bytes/source/body/lease fences. 333 Java / 285 Python / 134 Node pass with synthetic game authority; final strict-role targeted check passed. Labels/custom/overlay scope stays .2b and authentic .1b.4 remains. |
| M0.3b.3.2.3c.3.2b.3b.1b.3 | GI/QA | Ordinary recipe-history, category and page navigation with exact displayed control authority | in_progress | Split current rendered controls (.a), native preview/execute motor (.b), history route (.c) and authentic qualification (.1b.4). Preserve source/page CAS, at-most-once input, cancellation and no replay. |
| M0.3b.3.2.3c.3.2b.3b.1b.3a | GI/SI/QA | Actual four navigation-button draw operands, clipped enabled-state projection and source/frame transport | implemented_unverified | [Control observation evidence](docs/verification/2026-09-19-jei-page-controls.md): 350 Java / 301 Python / 134 Node pass with synthetic render authority. Exact native draw-order/flags/geometry capture, immutable frame copies and strict scoped projection; no input authority until .b. Authentic hooks/render/reference/isolation remain .1b.4. |
| M0.3b.3.2.3c.3.2b.3b.1b.3b | GI/QA | Bounded native page/category preview and execute gesture, fresh-page selection, charged waits, cancellation/release and no replay | implemented_unverified | [Navigation motor evidence](docs/verification/2026-09-19-jei-navigation-motor.md): .1/.2 connected through the real lane/HTTP/scoped CLI with synthetic screen/input authority. Actual hook/input/cancel/render/reference/isolation qualification remains .1b.4; no game-effect or gate pass. |
| M0.3b.3.2.3c.3.2b.3b.1b.3b.1 | GI/QA | Bounded native constructor/button/router provenance, two-phase confirmation, cancellation ownership and failed-reset/no-replay behavior | implemented_unverified | [Input provenance report](docs/verification/2026-09-19-jei-input-provenance.md): 368 Java pass at that phase, eighteen new synthetic cases; five artifact pins and compiled/native selectors audited. Three optional hooks now connect to .2's action-lane motor. Containing minor-34 client loads in the dedicated copy; actual transformation, native cleanup and isolation remain .1b.4. |
| M0.3b.3.2.3c.3.2b.3b.1b.3b.2 | GI/PL/QA | Strict typed page/category action, source/page/control CAS, ordinary preview/execute, fresh-frame wait, per-tick charges, deadlines and integrated safety release | implemented_unverified | [Motor report](docs/verification/2026-09-19-jei-navigation-motor.md): SPEC v0.2.23, Forge minor 31/nineteen actions; four-unit admission, 200-tick/ten-second limits and integrated non-executing cleanup. 383 Java / 328 Python / 135 Node plus final targeted checks; synthetic effects, no installed/native qualification. |
| M0.3b.3.2.3c.3.2b.3b.1b.3c | GI/QA | Ordinary recipe-history Back with valid current-screen/input authority and confirmed local result | implemented_unverified | [History evidence](docs/verification/2026-09-19-jei-history.md): exact concrete public callback, source/screen/page guards, fresh-frame confirmation, three-unit admission, empty-history no-op and no replay. 395 Java / 329 Python / 136 Node pass with synthetic history; no private stack access or physical-key claim. Actual populated/empty Back, hooks, timing/reference/isolation remain .1b.4; Close-to-quest stays separate. |
| M0.3b.3.2.3c.3.2b.3b.1b.4 | GI/SI/QA | Authentic hook loading, visible-page/input parity, overhead/mechanics and isolation | in_progress | Six-hook read-only candidate deployed and actual JEI runtime registered; unbound recipe-page request rejected. [Connected E9E evidence](docs/verification/2026-09-19-forge-connected.md) does not prove hook application, complete native frames, visible-page/input/overlay parity, overhead, mechanics or isolation. Containing minor-34 candidate now loads in the dedicated copy; nine-hook application remains unproven, with no rendered-page or input pass. |
| M0.3b.3.2.3c.3.2b.3b.2 | GI/QA | Other extension task callbacks and previous-screen/context-menu/hidden-panel contexts | not_started | Qualify each native route and its visibility, input, parent and resource effects independently. |
| M0.3b.3.2.3c.3.2b.4 | GI/QA | Occupied crafting-state handling across quest GUI lifecycle | not_started | Native book/menu close closes the player container; integrate owned-resource conservation and authoritative returns without implicit loss or duplicate effects. |
| M0.3b.3.2.3c.3.3 | GI/QA | Ordinary submission and reward/choice claims, resource effects, server feedback and ambiguous-outcome recovery | not_started | Client display or successful callback is not authoritative completion or a resource-effect pass. |
| M0.3b.3.2.4 | GI/RS/QA | Authentic connected menu/UI parity, machine operation and independent server/reference evidence | in_progress | Split basic quest lifecycle (.a) from the remaining menu/machine/reference qualification (.b). Read-only E9E discovery and guarded action foundation exist; actual complete mechanics/parity remain open. Metadata, compilation and synthetic fixtures cannot pass T03/G0. |
| M0.3b.3.2.4a | GI/QA | Authentic quest book open, chapter/detail, text, back/close, dedup and retained resource effects | in_progress | [Third authentic trial](docs/verification/2026-09-19-native-quest-cancel.md) passes all five quest mutations, readable text and dedup through scoped CLI. Six total intents/39 primitives including cancelled walk reconcile; 256 saved IDs, settled pose and selected inventory agree. Prior CTM startup crash and stale-catalog harness failure retained; corrected refresh and 19 focused Java checks pass. Full rendered UI, resource/failure-path and isolation evidence remain open; overall run fails cancellation-before-arrival and guardian shutdown. |
| M0.3b.3.2.4b | GI/RS/QA | Remaining authentic quest/task/choice/JEI/custom menus, occupied crafting, machine/resource mechanics, rendered parity, private server references and isolation | in_progress | Private persisted machine reference (.1) implemented; authentic prepared-copy operation (.2) follows. Preserve all .3.2 contracts and required failure cases. Basic quest navigation cannot substitute for submissions/claims, custom content, modded crafting/energy/fluid transactions or independent causal/resource verification. |
| M0.3b.3.2.4b.1 | GI/QA | Independent private selected Thermal furnace save projection, source hashes and malformed/resource/orientation negatives | implemented_unverified | [Version 2 reader and crash evidence](docs/verification/2026-09-20-server-save-integrity.md) now requires saved Facing to match horizontal block facing and six valid side values. The previous v1 baseline checked resource fields but missed invalid orientation; superseded for fixture admission. Final focused Python 136 pass and full Ruff pass; authentic replacement and operating reconciliation pending. |
| M0.3b.3.2.4b.2 | GI/QA | Authentic furnace input/processing/output/close plus independent machine/player resource reconciliation | in_progress | [Trials 01–05](docs/verification/2026-09-20-native-machine.md) retained. -05 startup passes (215.441-ms bootstrap, 261.0195-ms initialization) but malformed fixture crashes activation/save: 3 intents, 11 primitives, deposit unknown, 370.828 s retained. Player loses 3 dust, machine tile missing, output unproven. Never replay this request. Continue .2a with a distinct fixture. |
| M0.3b.3.2.4b.2a | GI/QA | Native-initialized replacement fixture, actual furnace operation and expert furnace crafting; no crashed-world repair/replay | in_progress | Prior fixture quarantined. New explicit setup resources: 20,000 RF, 3 dust, 5 andesite and 3 polished andesite. [Actual saved evidence](docs/verification/2026-09-20-machine-crafting.md) confirms 3 ingots and 8,000 RF remaining, but deposit receipt is unknown. Preserve 8 intents/27 primitives/521.719 s. Collection and crafting pending; guardian fails 500.5117/500 ms. No gate pass. |
| M0.3b.3.2.4b.2b | GI/QA | Bound exact pre-click echo reacquisition without accepting prediction, repeating input or ignoring unexpected owned changes | implemented_unverified | Machine policy v2 / Forge minor 35 adds at most one charged fixed refresh within existing deadline/budget; a fresh exact server/current owned-state match remains mandatory. Possible stale full-packet association is source-backed, not yet proven as this run's cause. [Focused checks pass](docs/verification/2026-09-20-machine-feedback.md); authentic output collection passed, but the causal echo hypothesis remains unproven. |
| M0.3b.3.2.4b.2c | GI/AR | Bind rebuilt native identity before issuing static action authority in the same bounded launch | implemented_unverified | Opt-in private bootstrap publishes exact loaded-runtime fingerprint bytes and waits without transport/action lane for strict operator authority. Existing source/artifact checks and lifetime limits remain. Bounded record, mismatch, no-overwrite and missing/invalid-authority cases pass focused checks; rebuilt candidate bound its actual native identity before authority and completed three charged API actions. [Evidence](docs/verification/2026-09-20-machine-feedback.md). |
| M0.3b.3.2.4b.2d | GI/QA | Exact EMI crafting discovery and execution selection for the actual E9E pack | in_progress | Actual JEI furnace query is empty. Installed EMI PluginCallerMixin skips jei:minecraft recipe registration. Add explicit source=emi with exact artifact, public focus, reload/index/hidden fencing, standard display/native definition equality and existing execution guards. No hidden manager enumeration, implicit fallback or game qualification claim. |
| M0.3b.3.2.4b.2e | GI/QA | Preserve changing derived previews during ordinary grid assembly; fresh authoritative final-output barrier | in_progress | Actual EMI discovery passed; partial craft failed REVISION_CONFLICT after three andesite populated the first row and a slab preview appeared. Unknown craft retained; all five andesite persisted as dropped items at the avatar. Implement exact owned-slot equality for non-result transfer, plus a charged final full server refresh before output take. No replay or resource refill. |
| M0.3b.3.2.4b.2f | GI/QA | One fixed read after exact current pre-state rollback; exact unaffected owned slots and bounded mismatch diagnostics | in_progress | Operation 05 locates the failure at GameInventory.Steps.tick current/reply comparison; exact mismatch shape was not captured. Minor 38 narrows recovery to verified full post-state reply plus exact pre-state current view, one charged resync, no click replay/deadline extension. Java 34 focused checks, build and Node capability check pass; authentic case unqualified. |
| M0.3b.3.2.4b.2g | GI/QA | Exact authoritative restoration after untouched client metadata drift; persistent/component/server-change negatives | in_progress | Operation 07 identifies backpack contentsUuid addition only in the client. Minor 39 allows one shared charged refresh while retaining original full component equality and exact resource checks. No field normalization, mutation replay or extended bounds. Java 35 focused checks/build and Node capability check pass; operation 08 recovered two drifts before failing the final fill barrier; minor 40 extends the same strict restoration to fill/take barriers, with 11 focused crafting checks/build passing. Operation 09 fails policy admission; corrected operation 10 fails final feedback; operation 11 completes selected craft and independent resource audit (.2h). Cause of operation 10's final mismatch remains unproven. [Evidence](docs/verification/2026-09-20-emi-crafting.md). |
| M0.3b.3.2.4b.2h | GI/QA | Selected E9E minor-40 expert furnace craft, public close and exact saved full-stack resource reconciliation | verified | [Operation 11](docs/verification/2026-09-20-emi-crafting.md) public sequence and independent audit pass: 5 andesite + 3 polished andesite -> 1 furnace; all other stack NBT, 3 ingots and 8000 RF retained. Three terminal actions/70 primitives/393.234 s. All prior failed samples preserved; full policy reliability/T03/G0 and private scoring remain open. |
| M0.3b.3.2.4b.2i | GI/QA | Server-confirmed inventory baseline before each recipe, bounded read and unchanged exact resource gates | implemented_unverified | [Witness control failure and repair](docs/verification/2026-09-20-craft-witness.md): minor 41 adds actual initial feedback before fill, preserving local dirty-state rejection and all budgets. Twelve focused Java checks/build, TypeScript build, two actual Node/JVM and two Python/JVM checks pass. Authentic control 02 public craft and full saved-resource audit pass; guardian and missing-witness checks fail separately. Final mismatch cause in the prior run remains unproven; no replay/refill. |


Native collaboration continuation children:

| ID | Owner | Scope / affected coverage | Status | Evidence / next action |
|---|---|---|---|---|
| M0.1c.2c | AR/PL/SI | Actual native collaboration discovery, context forks, lineage, lifecycle, bounded nested accounting and enforced child permissions | in_progress | Children .1/.2; retain M0.1c.2b boundary failure and all self-play requirements. |
| M0.1c.2c.1 | AR/QA | Observed pinned v2 tool schemas, native spawn/wait/result, clean/full context and declared session storage; F03/F07/F09/F11/F16, N01/N03/N04/N06/N08, C06/C14/C18/C20, partial T01/T04/T07/T12 | implemented_unverified | [Actual CLI/synthetic provider evidence](docs/verification/2026-09-20-native-helpers.md): two final invocation cases pass, four all-call receipts each, unchanged plugin bytes; 77 relevant Python checks pass. Preserve absent legacy surface, ephemeral-fork and parser failures. No production helper/isolation qualification. |
| M0.1c.2c.2 | AR/PL/SI | Trusted native child admission/lineage, child permission principals, nested/grandchild sub-budgets, full messaging/follow-up/interruption/restart and complete admitted session state | in_progress | M0.1c.2b.2c implements job/lineage/clean-context admission, finite nested envelopes, descendant revocation and exact sealed closure with [source/native synthetic evidence](docs/verification/2026-09-20-native-admission.md). Protected live ingress and complete messaging/follow-up/interruption/slot reuse remain open. Session files are not complete checkpoint/restore evidence. |
| M0.1c.2c.2a | AR/QA | Actual native idle messaging, follow-up, idle/active interruption/list lifecycle and unknown child usage through restart | implemented_unverified | [Evidence](docs/verification/2026-09-20-native-helper-lifecycle.md): final lifecycle 12 settled calls, active interruption four settled/one ambiguous with full held envelope and zero fresh-process replay. Exact native result shapes, dedup, unchanged plugin and original helper/restart regressions pass; 96 Python checks/full Ruff pass. Empty-ack parser failure retained. Fixture cap 16 applies only to declared idle case; old cap eight/live $10 unchanged. No trusted child budgets/permissions qualification. |
| M0.1c.2c.2b | AR/QA | Actual native concurrent helper admission and over-limit rejection, overlapping streaming and complete gateway charges | implemented_unverified | [Topology evidence](docs/verification/2026-09-20-native-helper-topology.md): two/one slot cases pass eight/seven calls, exact running/final agent sets, denial, dedup and settled envelopes; 113 local Python checks/full Ruff pass. Initial denial-shape discovery fail retained. This is not production child admission, per-child permission/sub-budget enforcement or N-body capacity. |
| M0.1c.2c.2c | AR/PL/SI | Actual child/grandchild capability, recursive registered lineage/charges and enforced depth-two bound | blocked | [Pinned nested failure](docs/verification/2026-09-20-native-helper-topology.md): native child omits collaboration tools even with max depth two. Final four-call capability-failure samples are settled; initial unsupported-call sample retains four settled/one unknown and full hold, with zero recovery replay. Pinned bundled Luna metadata is v1; forced root v2 is not a verified nested profile. Qualify a supported configuration or separate validated native-job helper seam; do not change model or treat an absent tool as the required positive pass. |

Guardian continuation child:

| ID | Owner | Scope / affected coverage | Status | Evidence / next action |
|---|---|---|---|---|
| M0.3b.2c.3c.2b.2b.2.2 | GI/QA | Owned-job accounting plus complete held-member exit proof within the existing 500 ms bound; F09/F16, N01/N03/N04/N05/N06/N08, C14/C15/C18, partial T01/T07/T12/T13 | implemented_unverified | [Code, failed samples and fixture checks](docs/verification/2026-09-20-guardian-tree.md): membership-verified observation handles, cumulative completeness and strict Node evidence. Actual JVM cases pass after zero-count-only proof failed. Authentic timing, inventory completeness/quota suitability and production launch/isolation remain open; do not reinterpret historical policy-1 records as current proof. |
| M0.3b.2c.3c.2b.2b.2.2a | GI/QA | Authentic E9E separate-desktop/current guardian proof after ordinary worker expiry; exact member completeness and unchanged 500 ms stop bound | in_progress | [Actual current-policy failure](docs/verification/2026-09-20-guardian-live.md): root wait times out at 510.8433 ms, no tree proof/receipt, supervisor exits one. Startup/read-only checks and clean server/telemetry stop pass; zero Java and argument retirement verified. Fresh source/capability pins, unchanged client, telemetry 0.2.0 and all failures retained. Diagnose cleanup/scheduling without changing bounds; full soaks, isolation and launch containment remain open. |

### Independent core implementation children

These children advance authorized software work while real M0 dependencies remain unavailable. They do not bypass milestone dependencies or integration gates.

| ID | Owner | Deliverable / negative cases | Status | Evidence / remaining work |
|---|---|---|---|---|
| M0.3a | GI/PL | Durable official acquisition receipts, role inventories, immutable templates and fresh instances | in_progress | [Provider and filesystem tests](tests/test_provisioning.py), [evidence](docs/verification/2026-09-18-long-horizon.md); 20 provisioning tests and actual official archive import/install-only bootstrap pass their limited checks; exact reviewed vendor bookmark survives immutable materialization. Cold game restart, full role provenance and supervised gameplay launch remain open. |
| M1.2 | PL | All 13 models, partitioned schemas, generated bindings and semantic checks | in_progress | [Records](src/mcbench/records.py), [tests](tests/test_records.py); full reference fixtures/migrations/conditional Java open. |
| M1.3 | SI/PL | Private CAS/outbox, safe paths, grants/epochs and production prerequisite checks | in_progress | [Storage/controller tests](tests/test_storage_controller.py); actual OS/process/network/helper boundary open. |
| M1.4 | AR/PL | Artifact revisions, immutable initial state, episode retention, message policies | in_progress | [Artifact tests](tests/test_checkpoints_artifacts.py); native runtime/session/tool integration open. |
| M2.1 | QA/PL | Complete clean-stop checkpoint commit, fresh materialization and recovery plans | in_progress | [Checkpoint tests](tests/test_checkpoints_artifacts.py); actual persistence inventory and stop/restore assertions open. |
| M2.2 | PL | Nested budget accounts/receipts, reservation races, measured clock intervals | in_progress | [Budget/clock tests](tests/test_budget_clocks.py); real metering/dispatch/exhaustion and unknown reconciliation open. |
| M3.1 | RS/GI | Registered private craft/machine predicates, positive/negative/duplicate controls | in_progress | [Evaluator tests](tests/test_evaluator.py); authoritative game telemetry/reachability/parity open. |
| M3.1a | GI/RS | Exact Forge read-only tick/player/recipe evidence producer, bounded durable private spool and gap detection | in_progress | [Module](java/forge1192-telemetry), [runbook](docs/operations/forge-telemetry.md): five Java tests and fourteen Python telemetry tests; real clean-stop streams and six runtime furnace assertions pass. Authenticated ingestion, supervisor fault integration, overhead, player-tick parity and mechanics parity remain open. Raw observations cannot earn scored craft/machine predicates. M0.3.2b.1 adds [0.2.0 bounded selected config evidence](docs/verification/2026-09-20-e9e-loaded-config.md), 51 Python/11 Java checks and a corrected two-boot private persistence check; full gates remain open. |
| M3.1b | GI/RS | Source-backed craft consumption and machine/energy/fluid provenance adapters | not_started | Requires authentic runtime traces, alternate strategies and all T10 negative controls; possession or raw craft callbacks alone cannot pass. |
| M1.1a | GI | Exact Forge client binding discovery, stable IDs and narrow client-thread settings transactions | in_progress | Children M1.1a.1/a.2 distinguish read-only discovery from transactional mutation; no settings capability advertised. |
| M1.1a.1 | GI | Runtime/default/persisted binding discovery, stable occurrences, explicit ownership basis and conservative contexts | implemented_unverified | [Client module](java/forge1192-client), [operator audit](src/mcbench/client_discovery.py), [actual evidence](docs/verification/2026-09-18-long-horizon.md): two exact client boots export 253 stable bindings (34 vanilla references, 219 unknown owners), with sampled Controls UI correspondence. Native options save/cold restart yielded all 253 persisted/runtime matches. Four Java tests and 13 synthetic Python audit cases pass. Mod ownership, complete runtime/layout fingerprint and broader discovery failure cases remain open; all mutation/input/restart capability flags remain false. Desktop stop signal cleared after supported session reset; no physical Escape attributed to the user. |
| M1.1a.2 | GI | Native client-thread CAS writer, exclusive profile/journal/backup, owned-field rollback and crash recovery | in_progress | Children M1.1a.2.1–2.3 separate durable writer, native authority/adapter and real transaction recovery. Integrate with the Python transaction engine only after source-bound ownership and the native writer are qualified. |
| M1.1a.2.1 | GI/QA | Profile-exclusive durable transaction journal, bounded owned-field file patch, revision fencing and conservative recovery | implemented_unverified | [Java core](java/forge1192-client/src/main/java/io/github/opencnid/strata/client/SettingsStore.java), [tests](java/forge1192-client/src/test/java/io/github/opencnid/strata/client/SettingsStoreTest.java): 20 synthetic-runtime cases pass with real Windows temporary files/locks, plus four parser cases. Recovery never replays the forward write or assumes commit. Actual Minecraft recovery, foreign-writer exclusion, power-loss durability and full exhaustion qualification remain open. |
| M1.1a.2.2 | GI | Source-bound native KeyMapping authority, client-thread setters and release/readback | in_progress | [Native adapter](java/forge1192-client/src/main/java/io/github/opencnid/strata/client/NativeSettingsRuntime.java): exact Curios JAR plus public registration-object identity; all other keys protected. [Authentic encoding round trip](docs/verification/2026-09-20-native-settings.md) now passes. General ownership, physical pool/context/consumer effects and full runtime qualification remain open. |
| M1.1a.2.3 | GI/QA | Actual native apply/rollback and interrupted transaction recovery with private evidence | in_progress | Split .2.3a title-screen round trip, .2.3b cold restart/readback and .2.3c interrupted recovery. Existing authorized separate-desktop/API route; synthetic checks do not satisfy these real cases. Complete effects/input/isolation remain M1.1b. |
| M1.1a.2.3a | GI/QA | Actual source-bound Curios native/persisted apply/readback/rollback; all unrelated mapping/options preservation | implemented_unverified | [Actual positive case](docs/verification/2026-09-20-native-settings.md): native pending apply/rollback, exact owned-file change, all 253 mappings restored, six-frame journal and title-client stop pass. No commit/physical F13, general conflict/foreign-writer or full T05 qualification. Failure-path integration remains .2.3c/M1.1b. |
| M1.1a.2.3b | GI/QA | Fresh client restart reads the rolled-back runtime and persisted keymap; no forward transaction replay | implemented_unverified | [Independent read-only boot](docs/verification/2026-09-20-native-settings.md) passes 253 runtime/persisted matches and unchanged options digest; strict discovery audit passes format only. No forward transaction property/replay. Repaired-key physical-effect persistence, complete restore/isolation and full T05 remain open. |
| M1.1a.2.3c | GI/QA | Actual interrupted native settings transaction, preserved journal/owned-field recovery and foreign-change conflict negatives | in_progress | Split .2.3c.1 applied-pending process interruption, .2.3c.2 mid-write faults and .2.3c.3 foreign-change conflicts. Existing private bridge, exact identity and bounded conservative recovery; no blind apply replay. Synthetic SettingsStore cases remain supporting evidence only. |
| M1.1a.2.3c.1 | GI/QA | Authentic process termination after applied_pending_verification, new-session status and owned rollback from the same journal, no second apply | implemented_unverified | [Authentic two-client case](docs/verification/2026-09-20-native-settings-recovery.md) passes one total apply/zero recovery applies, preserved hash-linked journal prefix, 253 restored runtime/persisted bindings and exact original options bytes. Both processes terminal/arguments retired. Full partial-write, ambiguous-response and foreign-change cases remain .2.3c.2/.3; no physical-key/effect or full T05 claim. |
| M1.1a.2.3c.2 | GI/QA | Actual interruption within prepared/native-write/file-write/rollback phases and retained uncertain outcome recovery | in_progress | Split .2.3c.2a precise operator-only boundary fixture and .2.3c.2b authentic exact-artifact qualification. A completed pending apply followed by termination cannot stand in for partial-write cases; power-loss durability remains separate. |
| M1.1a.2.3c.2a | GI/QA | Inert-by-default fault boundaries and bounded title-only crash probe; abrupt-JVM synthetic recovery checks | implemented_unverified | [Candidate and checks](docs/verification/2026-09-20-settings-crash-fixture.md): six explicit boundaries, real abrupt JVM/synthetic binding recovery, 448 Java/33 Python checks pass; protected fresh plan and exact state captures, no bridge/input/replay. Authentic native qualification remains .2b; no gameplay capability. |
| M1.1a.2.3c.2b | GI/QA | Exact new-artifact authentic crash at each boundary, new-session status and conservative rollback | in_progress | Pinned candidate installed after zero-Java/old-artifact backup checks. Six independent fresh broker/evidence pairs are prepared; .2b.1–.6 retain each result separately. Synthetic JVM faults do not pass these children. |
| M1.1a.2.3c.2b.1 | GI/QA | Authentic apply_runtime_written crash and fresh status/rollback | in_progress | Original profile remains blocked by retained CTM startup failure (.1a). Separately pinned diagnostic pair (.1b) passes; this is not default-profile reliability. |
| M1.1a.2.3c.2b.1a | GI/QA | Original configured profile apply-runtime fault attempt | blocked | [Native -01 sample](docs/verification/2026-09-20-settings-crash-startup.md) fails in CTM startup before journal/armed state; no recovery or native fault occurs. Preserve it under B10; later different-profile evidence cannot erase this failure. |
| M1.1a.2.3c.2b.1b | GI/QA | Profile ctm-startup-bg1-diagnostic/1 apply-runtime fault and conservative recovery | verified | [Authentic diagnostic evidence](docs/verification/2026-09-20-settings-crash-recovery.md): exact runtime-written boundary exits 86; fresh status/rollback, five journal frames, one forward transaction, zero recovery apply, all 253 mappings and original options restored. Both processes terminal/arguments retired; profile ctm-startup-bg1-diagnostic/1 only. No power-loss, physical effect or CTM reliability claim. |
| M1.1a.2.3c.2b.2 | GI/QA | Authentic apply_prepared crash and fresh status/rollback | verified | [Authentic diagnostic evidence](docs/verification/2026-09-20-settings-crash-recovery.md): exact prepared/original-runtime/original-disk state, exit 86, new-session status/rollback and 253-value restoration; no replay. Scoped to ctm-startup-bg1-diagnostic/1; default-profile and full T05 acceptance remain open. |
| M1.1a.2.3c.2b.3 | GI/QA | Authentic apply_options_written crash and fresh status/rollback | not_started | Expected prepared journal with changed runtime/disk, no pending receipt; separate sample required. |
| M1.1a.2.3c.2b.4 | GI/QA | Authentic rollback_prepared crash and fresh status/rollback | not_started | Expected rollback_prepared journal with changed runtime/disk; separate sample required. |
| M1.1a.2.3c.2b.5 | GI/QA | Authentic rollback_runtime_written crash and fresh status/rollback | not_started | Expected rollback_prepared journal with restored runtime/changed disk; separate sample required. |
| M1.1a.2.3c.2b.6 | GI/QA | Authentic rollback_options_written crash and fresh status/rollback | not_started | Expected rollback_prepared journal with restored runtime/disk, no terminal receipt; separate sample required. |
| M1.1a.2.3c.3 | GI/QA | Actual foreign runtime/options revision conflicts, no overwrite of unrelated changes and explicit owned-intervention cleanup | in_progress | [Authentic disk cases](docs/verification/2026-09-20-native-settings-conflicts.md) pass stale apply plus unrelated/owned-third-value rollback conflicts and two forward fences; one prepared transaction, exact known-injection removal, 253 runtime/persisted mappings and original bytes restored. In-memory foreign changes and OS-writer exclusion remain unrun. Cooperating profile locks/operator byte comparisons do not qualify isolation/CAS. |
| M1.1a.2.4 | GI/PL | Transaction-aware private native transport and Python adapter; strict schema, session/deadline fencing, uncertain-response recovery | implemented_unverified | [Java bridge](java/forge1192-client/src/main/java/io/github/opencnid/strata/client/SettingsHttpBridge.java), [Python client](src/mcbench/native_settings.py): five Java transport tests, 15 Python validation tests and four actual JVM/HTTP cases with synthetic runtime pass, including lost acknowledgement, process restart, duplicate transaction and foreign-edit recovery fencing. Native Minecraft, OS isolation, qualified Controls projection/verified commit, lifecycle/accounting and gameplay CLI integration remain open. Capability stays disabled. |
| M1.1b | GI/QA | Ordinary-input effects, competing consumers, restart/persistence, rollback and isolation | not_started | Required before advertising keybinding support; byte comparisons and source inspection alone are insufficient. |
| M1.1c | GI/PL | Host workflow profile ownership, durable phase fencing, rollback-conflict holds, qualification drift and verification coverage | in_progress | [Workflow](src/mcbench/controls.py), [contract](docs/operations/settings-workflow.md); c.1–c.3 distinguish implemented host checks from missing authentic provider/supervisor integration. |
| M1.1c.1 | PL/QA | Profile/avatar recovery holds, cross-process operation lock, phase/idempotency/metadata/revision fencing and legacy-plan rejection | implemented_unverified | [Fencing tests](tests/test_controls_fencing.py), actual Windows lock exclusion and normal/crash release; persistent failed holds survive database reopening. Native profile lock and full supervisor/action-lane coupling remain separate requirements. |
| M1.1c.2 | GI/PL | Transaction/plan/binding/context/restart evidence matrix, bounded hashed proof/source reads and simulation separation | implemented_unverified | [Controls tests](tests/test_controls.py) and [evidence tests](tests/test_controls_fencing.py); actual private CAS integration with synthetic proofs passes. No authentic effect producer/provenance, physical input or verified native commit yet. |
| M1.1c.3 | GI/PL | Qualified native adapter/commit, per-avatar RECONFIGURING, action-lease fencing, worker restart, charged continuity and public patch/CLI projection | in_progress | Children c.3.1–c.3.3 retain the complete integration scope; the development bridge is unqualified and has no commit operation. |
| M1.1c.3.1 | PL/QA | Durable per-avatar repair holds, scoped grant revocation, stop/fresh-observation receipts, recovery fencing and clock attribution | implemented_unverified | [Coordinator](src/mcbench/reconfiguration.py), [32 synthetic cases](tests/test_reconfiguration.py); partial controller/settings/budget/clock integration with private CAS proofs. Actual worker transport, receipt provenance and complete measured charges remain unqualified. |
| M1.1c.3.2 | GI/PL | Qualified native adapter/commit, worker action-lease transport, restart/rejoin and authentic effect evidence | not_started | Preserve T05/G1 qualification; controller-side state alone cannot fence a separately running worker. |
| M1.1c.3.3 | PL/GI | Full repair budget/telemetry settlement, public KeybindingPatch/control card and scoped gameplay CLI | not_started | Retain nested charging, fresh-probe repair policy and complete public/private projections. |
| M3.2 | RS/SI | Matched fresh clone plans, artifact controls and drift quarantine decisions | in_progress | [Probe planner](evaluator/src/strata_evaluator/probes.py); actual isolated clone execution/disposal and supervisor drift handling open. |
| M3.3 | RS | Paired lineage analysis, absolute competence, uncertainty/attrition and common support | in_progress | [Analysis](evaluator/src/strata_evaluator/analysis.py); full survival/hierarchical/power/confirmatory workflow open. |
| M4.1 | PL | Whole-team resource/account admission, scoped grants and bounded communication | in_progress | [Controller/message tests](tests/test_storage_controller.py); actual simultaneous N=1/2/4 certificates remain required. |
| M5.1 | RS/PL | Offline report reconstruction/publication and operator commands/runbook | in_progress | [Command/report tests](tests/test_operator_commands.py); no pilot or confirmation, complete evidence audit/report still open. |

## Requirement coverage

September 20 loaded-config delta: M0.3.2b.1/M3.1a advances partial F01/F05/F10/F16 and N01/N03/N04/N06/N08 through bounded native queries, strict private payloads, scorer rejection and authentic selected-server persistence. C03/C04/C18/C24 and partial T01/T02/T10/T13 are linked in the [report](docs/verification/2026-09-20-e9e-loaded-config.md). Source/loaded-role/consumer and full expert-mode/isolation/mechanics gates remain open; no requirement or original file failure was removed.

September 20 native-helper delta — F03/F07/F09/F11/F16 and
N01/N03/N04/N06/N08: [native collaboration and storage](docs/verification/2026-09-20-native-helpers.md)
advances M0.1c.2c.1 through actual pinned tools, clean/full context markers and
four-call aggregate accounting. Root terminal usage excludes the child. Native
child admission/budgets, permissions, further lifecycle and complete resume stay
open under .2c.2; no aggregate requirement is promoted.

September 20 owned-job delta — F09/F16, N01/N03/N04/N05/N06/N08:
[guardian proof](docs/verification/2026-09-20-guardian-tree.md) advances child
M0.3b.2c.3c.2b.2b.2.2. Root exit or zero active accounting alone is insufficient;
the final candidate reconciles cumulative totals with held, signaled member
handles under the existing bound. Fixture evidence passes; authentic behavior,
inventory completeness and all aggregate requirement statuses remain open.

Checkpoint accounting addendum: M0.1c.1a advances partial F03/F11/F16 and N01/N03/N04/N06 through [durable private dispatch accounting](docs/verification/2026-09-19-inference-dispatch.md). Synthetic reservation/receipt/recovery tests pass; production host, clocks, monetary semantics and isolation remain unqualified. No parent status or release gate is promoted.

September 19 paired-reference/outline delta — F01/F06/F09/F10/F13/F16,
N01/N02/N03/N04/N05/N06/N08: [authentic failed case and repair candidate](docs/verification/2026-09-19-paired-block-reference.md).
Independent saves resolve unchanged block state, not a successful action. New
motor identity and post-fence private diagnostics have fixture evidence only;
the installed client and historical results retain their prior identity.

September 19 saved-reference delta — F01/F06/F10/F13/F16 and
N01/N04/N06/N08: [private reader/evidence](docs/verification/2026-09-19-saved-block-reference.md)
adds bounded saved-state inspection and source hashes, not live observation
authority or scoring eligibility. 128 authentic persisted ID comparisons match;
all aggregate requirement statuses and remaining acceptance cases stay open.

Latest direct-timing delta: [guardian call boundaries](docs/verification/2026-09-19-stop-boundaries.md)
advances M0.3b.2c.3c.2b.2b.2 under F01/F06/F09/F16 and
N01/N02/N03/N04/N05/N06/N08, C09/C14/C15/C18, T01/T03/T06/T07/T12/T13.
Private diagnostics distinguish job and wait outcomes and queue after owned
handle cleanup. The base wire contract and all gameplay/stop limits remain.
Fixture checks and one authentic scoped-worker/API/normal-stop procedure pass.
Direct measurement gives a 489.8473 ms wait under the unchanged 500 ms bound;
prior failures and small margin leave reliable termination and all aggregate
requirements open.

Latest stop-diagnostic delta: [private intent and latency evidence](docs/verification/2026-09-19-stop-latency.md)
advances M0.3b.2c.3c.2b.2b.2 for F01/F06/F09/F16 and
N01/N02/N03/N04/N05/N06/N08, C09/C14/C15/C18, T01/T03/T06/T07/T12/T13.
Six guarded fixture integrations and five disposable heap/render stops pass;
the authentic observer trial reproduces the 500 ms failure despite its CLI subset
pass. Real timing qualification remains open. Explicit clock resolution and observation
delay prevent interpreting intent/receipt times as kernel-call times. No public
capability, budget, isolation or release claim changes.

Latest readiness delta: [initial synchronization barrier](docs/verification/2026-09-19-forge-readiness.md)
advances .2c.3c.2b.2b.1 for F01/F06/F09/F16 and N01/N02/N03/N04/N05/N06/N08,
with C02/C09/C15/C18 and T01/T03/T06/T07/T12/T13 mappings. Current-connection
source identity and a later world frame gate native body qualification; public
actions, screenshot capability, budgets and watchdog bounds are unchanged.
433 Java tests pass; authentic readiness/worker testing remains incomplete.
No aggregate requirement, test or gate becomes verified by this local evidence.

Latest session-lifetime delta: [native worker trial and authentication repair](docs/verification/2026-09-19-desktop-worker.md)
advances M0.2g.1 and .2c.3c.2b.2b for F01/F06/F09/F16 and
N01/N02/N03/N04/N05/N06/N08. Minimum session lifetime is an operator preflight,
not new gameplay authority. The first attempt failed before login; two refreshed
sessions joined but native reads remained unavailable. A sampled tag/block-cache
initialization path is now explicit under .2b.2b.1; authentic scoped actions and
guardian remain unverified. All requirement statuses stay open.

Latest private-frame delta: [actual game imagery](docs/verification/2026-09-19-private-frames.md)
advances F01/F06/F09/F16 and N01/N02/N03/N04/N05/N06/N08 through .2c.3c.2b.1.
New operator-only session/request/intent/frame/failure records do not alter the
13 primary record types or public screenshots:false. Full image/reference and
security qualification remains open; no requirement status becomes verified.

Latest actual launch delta: [guarded E9E startup](docs/verification/2026-09-19-desktop-client.md)
advances F01/F05/F06/F09/F16 and N01/N02/N03/N04/N05/N06/N08 through .2c.3c.2a.
Exact installed artifacts, a private client copy, independent guardian and actual
title-screen API evidence do not establish gameplay, frames or production isolation.

Earlier launch delta: [non-input-desktop foundation](docs/verification/2026-09-19-desktop-launch.md)
advances F06/F09/F16 and N01/N02/N03/N04/N05/N06/N08 through .2c.3c.1.
Actual disposable kernel process/desktop tests and synthetic graphics on the real
GPU do not establish authentic Minecraft behavior or same-user security isolation.

Latest candidate delta: [witnessed empty JEI pages](docs/verification/2026-09-19-jei-empty-page.md)
advances F01/F06/F09/F11/F16 and N01/N02/N03/N04/N05/N06 through the explicit
M0.3b.3.2.3c.3.2b.3b.1b.2b.2a child and preceding navigation children. Public schema, motor, budget, cancellation
and source/privacy checks have synthetic evidence; none establishes authentic
effects, measured native timing or process isolation.

Latest task-opening cross-reference: M0.3b.3.2.3c.3.2b.1 extends F01/F06/F09/F16/N01/N02/N04/N05/N06, C09/C15 and partial T01/T03/T06/T07/T12 through the [visible task motor](docs/verification/2026-09-19-quest-task-open.md). Page/current-book/native-button identity, clipped visibility, charged one-shot callback and durable uncertainty/cancellation have synthetic evidence. Actual JVM/HTTP/scoped CLI exercise the pure motor; native UI/resource/isolation remain unverified. All aggregate statuses stay unchanged.

Latest navigation cross-reference: M0.3b.3.2.3c.3.2a extends F01/F06/F09/F16/N01/N02/N04/N05/N06, C09/C15 and partial T01/T03/T06/T07/T12 through the [current book observer and motor](docs/verification/2026-09-19-quest-navigation.md). Catalog-page, source/screen/body and selected-object fencing, one-shot charged dispatch, cancellation and deduplication have synthetic evidence. Complete open/chapter/quest/back/close runs through actual JVM/HTTP/scoped CLI with synthetic UI authority. Native callback/UI/resource/isolation qualification remains open; no aggregate status changes.

Latest opening cross-reference: M0.3b.3.2.3c.3.1 extends F01/F06/F09/F16/N01/N02/N04/N05/N06, C09/C15 and partial T01/T03/T06/T07/T12 through the [ordinary opening motor](docs/verification/2026-09-19-quest-open.md). Bound source/catalog/permission/screen checks, charged one-shot dispatch and durable cancellation/deduplication have synthetic evidence. No server effect or full quest interaction is claimed; corresponding aggregate statuses remain unchanged.

Latest item-menu cross-reference: M0.3b.3.2.3c.2.2b.1 extends F01/F06/F16/N01/N04/N06, C09 and partial T01/T03/T06 through the [current clipped menu observer](docs/verification/2026-09-19-quest-item-menu.md). Source/task/menu/layout and body/lease checks bound visible item/control projection; off-screen content and raw metadata are excluded. No mutation authority. Native UI/scroll/mod-hook/options/timing/isolation remain unverified; aggregate statuses are unchanged.

Latest task/reward cross-reference: M0.3b.3.2.3c.2.2a extends F01/F06/F16/N01/N04/N06, C09 and partial T01/T03/T06 through the [normal-tooltip/status adapter](docs/verification/2026-09-19-quest-components.md). Visible parent/detail and reward blocking gates precede identifiers/display; exact dependency pins, typed roles and private body binding retain source boundaries. Game callbacks/UI/claim/team/modifier/timing and isolation are unverified; corresponding requirement, feature and aggregate test statuses are unchanged.

Latest quest-text cross-reference: M0.3b.3.2.3c.2.1 extends F01/F06/F16/N01/N04/N06, C09 and partial T01/T03/T06 through the [one-quest text adapter](docs/verification/2026-09-19-quest-text.md). Detail/text visibility precedes readers; strict transport rejects hidden payloads and unsupported raw content. Actual FTB/parser/UI and isolation gates remain unverified; aggregate statuses are unchanged.

Latest quest cross-reference: M0.3b.3.2.3c.1 advances F01/F06/F16/N01/N04/N06, C09 and partial T01/T03/T06 through the [visible own-team catalog](docs/verification/2026-09-19-quest-catalog.md). Exact artifact/source guards, bounded visibility-filtered rows, body/revision checks and strict schema/CLI cases have synthetic evidence. Corresponding requirement, feature and aggregate test statuses stay unchanged; loaded API/UI/team isolation remains unverified.

Latest discovery cross-reference: M0.3b.3.2.3a advances F01/F06/F16/N01/N04/N06 and C09 through [focused Thermal queries](docs/verification/2026-09-19-thermal-recipes.md), with exact source guards, bounded player-visible data, source/body/revision binding, machine execution rejection and strict generated public contracts. All corresponding requirement statuses remain in progress; actual visibility/isolation/mechanics conformance is unverified.

Latest cross-reference: M0.3b.3.2.2a adds [Thermal transfers/input fences](docs/verification/2026-09-19-thermal-transactions.md) under F01/F06/F09/F16/N01/N02/N03/N04/N05/N06, extending .1's exact GUI projection. Ordinary mechanics, owned transfer checks, hidden-slot masking, charges/unknown/cancel and D10 revision policy have implementation/synthetic evidence. Authentic mechanics and isolation coverage remain incomplete; requirement statuses below are unchanged.

Status refers to complete requirement coverage, not the first related prototype. In-progress rows link the actual partial work; no local synthetic test closes an entire requirement.

September 20 accounting cross-reference: M0.1c.1b advances partial F03/F11/F16,
N01/N03/N04/N06, C06/C20, T01/T04/T07/T12 through the
[native synthetic dispatch report](docs/verification/2026-09-20-native-dispatch.md).
The operator-only NativeLaunch accounting mode is regenerated in JSON/TypeScript;
all thirteen canonical records, gameplay affordances and aggregate statuses remain.

| ID | Required behavior | Owner | Milestones | Tests | Status | Implementation / evidence / gap |
|---|---|---|---|---|---|---|
| F01 | Authentic vanilla/E9E servers; Mineflayer first, exact modded API conformance | GI | M0, M2 | T02, T03 | in_progress | M0.2c partial authenticated vanilla action/cancellation evidence; exact E9E boot/cold restart and instrumented runtime recipe assertions. Mineflayer/E9E handshake failed. Complete locks, full body/host/private-scoring and modded mechanics conformance remain open. [Authentic vanilla menu evidence](docs/verification/2026-09-19-vanilla-menu.md) adds player-menu cursor/grid returns, duplicate handling, retained pre-acceptance schema/revision rejections, 24 total charged primitives and final saved inventory; complete profile/reference/accounting gates remain open. [Body-revision evidence](docs/verification/2026-09-19-body-revision.md) fixes idle heartbeat invalidation and adds authentic scoped CLI acceptance/actual-turn/age negatives; full native host and body-transition conformance stay open. D08 [JEI query evidence](docs/verification/2026-09-19-jei-query.md) adds bounded focused discovery, strict scoped/body-bound transport and exact dependency/policy pins; native effects/isolation remain unverified, with no gate change. D09 [manual-craft evidence](docs/verification/2026-09-19-manual-craft.md) adds explicit source selection, ordinary confirmed grid filling and retained partial-effect charges; synthetic checks pass, authentic scope remains open. |
| F02 | Positive configurable N and whole-team simultaneous admission | PL | M1, M4 | T01, T09 | in_progress | M4.1: [controller](src/mcbench/controller.py) atomically reserves all bodies/resources/accounts and queues/rejects the team; real simultaneous N=1/2/4 certification open. |
| F03 | Native selected Dovetail for each body; helpers/self-play accounted | AR | M0, M1 | T04, T12 | in_progress | M0.1c: [native host adapter](src/mcbench/native.py), [process fencing](src/mcbench/processes.py) and observed-usage reader; synthetic native streams and real process lifecycle tested. Actual pinned CLI/Dovetail skill and native-helper execution now have synthetic-provider evidence; live root/helper admission, all-call coverage and isolation remain open. [Body-revision evidence](docs/verification/2026-09-19-body-revision.md) fixes idle heartbeat invalidation and adds authentic scoped CLI acceptance/actual-turn/age negatives; full native host and body-transition conformance stay open. M0.1c.2b.2c adds [native participant/budget admission](docs/verification/2026-09-20-native-admission.md), with clean-helper and inherited-context native synthetic evidence; protected live ingress and complete lifecycle remain unqualified.  M0.1c.2b.2e adds [authenticated native request admission](docs/verification/2026-09-20-native-ingress.md), with source/native synthetic evidence; OAuth transport and complete isolation remain unqualified.  M0.1c.2b.2f adds [native OAuth transport candidate evidence](docs/verification/2026-09-20-native-oauth-transport.md); fabricated authentication does not qualify live TLS/account/usage.  [First OAuth trial/diagnostic/catalog evidence](docs/verification/2026-09-20-native-oauth-conformance.md): one unresolved request, $0.7554 hold; source checks and native metadata evidence do not close this row. |
| F04 | Enforced hidden objective/criteria/holdout isolation | SI | M0, M1, M3 | T06 | in_progress | M1.3: [CAS authorization](src/mcbench/storage.py), scoped grants and separate evaluator package; synthetic canaries pass, real filesystem/process/network/helper boundaries open. D08 [JEI query evidence](docs/verification/2026-09-19-jei-query.md) adds bounded focused discovery, strict scoped/body-bound transport and exact dependency/policy pins; native effects/isolation remain unverified, with no gate change. D09 [manual-craft evidence](docs/verification/2026-09-19-manual-craft.md) adds explicit source selection, ordinary confirmed grid filling and retained partial-effect charges; synthetic checks pass, authentic scope remains open.  M0.1c.2b.2a: [native broker source/synthetic integration](docs/verification/2026-09-20-restricted-native-tools.md) enforces explicit projections, helper result writes and executor-only game transport. Full native isolation/live admission remains open. M0.1c.2b.2d adds [sealed bootstrap/source integrity evidence](docs/verification/2026-09-20-native-bootstrap.md), including native root/helper canaries; aggregate qualification remains incomplete.  M0.1c.2b.2e adds [authenticated native request admission](docs/verification/2026-09-20-native-ingress.md), with source/native synthetic evidence; OAuth transport and complete isolation remain unqualified.  M0.1c.2b.2f adds [native OAuth transport candidate evidence](docs/verification/2026-09-20-native-oauth-transport.md); fabricated authentication does not qualify live TLS/account/usage.  [First OAuth trial/diagnostic/catalog evidence](docs/verification/2026-09-20-native-oauth-conformance.md): one unresolved request, $0.7554 hold; source checks and native metadata evidence do not close this row.  M0.2c.3 [private telemetry authentication](docs/verification/2026-09-20-authenticated-telemetry.md) adds source/synthetic byte/boot binding; no authentic score or aggregate gate pass.  M0.2c.3b.1 [sealed craft-reference source/synthetic evidence](docs/verification/2026-09-20-craft-reference-seal.md) verifies preserved bytes and the registered source/resource join; no protected score or aggregate gate pass. |
| F05 | Official CurseForge/Forge acquisition, provenance and blocked states | GI | M0 | T02 | in_progress | [Pack provider](src/mcbench/provisioning.py) and [commands](src/mcbench/pack_commands.py): receipts, complete role inventories, seal and fresh materialization implemented; actual official workflow/bootstrap/expert evidence remains open. |
| F06 | Bounded structured state/actions and capability-gated verified keybinding skill | GI | M0, M1, M2 | T03, T05 | in_progress | Mineflayer actions/settings transactions and real 253-binding Forge discovery retained. The Forge route exposes thirteen development motors, including [level walking](docs/verification/2026-09-19-forge-movement.md), [equipment/initial placement](docs/verification/2026-09-19-forge-inventory-placement.md) and [known-recipe crafting](docs/verification/2026-09-19-forge-crafting.md). Full geometry/custom serializers/placement, settings effects/physical pool/restart and authentic conformance stay open. D07 [menu-close evidence](docs/verification/2026-09-19-menu-close.md) adds explicit resource-preserving close to both backends; authentic menu effects remain open. [Authentic vanilla menu evidence](docs/verification/2026-09-19-vanilla-menu.md) adds player-menu cursor/grid returns, duplicate handling, retained pre-acceptance schema/revision rejections, 24 total charged primitives and final saved inventory; complete profile/reference/accounting gates remain open. [Body-revision evidence](docs/verification/2026-09-19-body-revision.md) fixes idle heartbeat invalidation and adds authentic scoped CLI acceptance/actual-turn/age negatives; full native host and body-transition conformance stay open. D08 [JEI query evidence](docs/verification/2026-09-19-jei-query.md) adds bounded focused discovery, strict scoped/body-bound transport and exact dependency/policy pins; native effects/isolation remain unverified, with no gate change. D09 [manual-craft evidence](docs/verification/2026-09-19-manual-craft.md) adds explicit source selection, ordinary confirmed grid filling and retained partial-effect charges; synthetic checks pass, authentic scope remains open.  Latest [vanilla mechanics](docs/verification/2026-09-20-vanilla-mechanics.md) and [EMI discovery/craft evidence](docs/verification/2026-09-20-emi-crafting.md) distinguish saved-server outcomes from unqualified implementations.  Latest [vanilla cancel/reconnect](docs/verification/2026-09-20-vanilla-reconnect.md) has a passing narrow independent audit with all raw checker failures retained; complete profile/gate coverage remains open. |
| F07 | Information, communication, learned-artifact and context policies | AR | M1, M3, M4 | T04, T06, T11 | in_progress | M1.4: [artifacts](src/mcbench/artifacts.py), [messages](src/mcbench/communication.py), exact episode projections; native context/helper enforcement and executable policy integration open.  M0.1c.2b.2a: [native broker source/synthetic integration](docs/verification/2026-09-20-restricted-native-tools.md) enforces explicit projections, helper result writes and executor-only game transport. Full native isolation/live admission remains open. M0.1c.2b.2c adds [native participant/budget admission](docs/verification/2026-09-20-native-admission.md), with clean-helper and inherited-context native synthetic evidence; protected live ingress and complete lifecycle remain unqualified.  M0.1c.2b.2e adds [authenticated native request admission](docs/verification/2026-09-20-native-ingress.md), with source/native synthetic evidence; OAuth transport and complete isolation remain unqualified.  M0.1c.2b.2f adds [native OAuth transport candidate evidence](docs/verification/2026-09-20-native-oauth-transport.md); fabricated authentication does not qualify live TLS/account/usage.  [First OAuth trial/diagnostic/catalog evidence](docs/verification/2026-09-20-native-oauth-conformance.md): one unresolved request, $0.7554 hold; source checks and native metadata evidence do not close this row. |
| F08 | Persistent campaigns separated from matched one-way probes | RS | M1, M3, M5 | T11 | in_progress | M3.2: [matched clone planner](evaluator/src/strata_evaluator/probes.py), probe-origin import rejection; actual disposable clones and sealed execution open. |
| F09 | Durable lifecycle, leases, fenced input, consistent recovery | PL | M1, M2 | T07, T08 | in_progress | Controller/repair/checkpoint services, native lane and [scoped Forge broker](docs/verification/2026-09-18-forge-worker.md). [Integrated independent guard](docs/verification/2026-09-18-forge-guard-integration.md) adds actual synthetic listener/native-thread/worker/parent fault stopping and bounded private lifecycle evidence. Production controller authority, launch/isolation, authentic release and complete game/agent restoration remain open. [Authentic vanilla menu evidence](docs/verification/2026-09-19-vanilla-menu.md) adds player-menu cursor/grid returns, duplicate handling, retained pre-acceptance schema/revision rejections, 24 total charged primitives and final saved inventory; complete profile/reference/accounting gates remain open. [Body-revision evidence](docs/verification/2026-09-19-body-revision.md) fixes idle heartbeat invalidation and adds authentic scoped CLI acceptance/actual-turn/age negatives; full native host and body-transition conformance stay open. D09 [manual-craft evidence](docs/verification/2026-09-19-manual-craft.md) adds explicit source selection, ordinary confirmed grid filling and retained partial-effect charges; synthetic checks pass, authentic scope remains open.  Latest [vanilla cancel/reconnect](docs/verification/2026-09-20-vanilla-reconnect.md) has a passing narrow independent audit with all raw checker failures retained; complete profile/gate coverage remains open.  [First OAuth trial/diagnostic/catalog evidence](docs/verification/2026-09-20-native-oauth-conformance.md): one unresolved request, $0.7554 hold; source checks and native metadata evidence do not close this row.  M0.2c.3 [private telemetry authentication](docs/verification/2026-09-20-authenticated-telemetry.md) adds source/synthetic byte/boot binding; no authentic score or aggregate gate pass.  M0.2c.3b.1 [sealed craft-reference source/synthetic evidence](docs/verification/2026-09-20-craft-reference-seal.md) verifies preserved bytes and the registered source/resource join; no protected score or aggregate gate pass. |
| F10 | Authoritative scorer and positive/negative controls | RS | M0, M3 | T10, T13 | in_progress | M3.1: [private craft/machine predicates](evaluator/src/strata_evaluator/scorer.py), synthetic alternate/negative/duplicate controls; real read-only tick/recipe evidence producer. Source-backed craft/machine provenance, transport identity, authentic reachability and mechanics parity remain open.  M0.2c.3 [private telemetry authentication](docs/verification/2026-09-20-authenticated-telemetry.md) adds source/synthetic byte/boot binding; no authentic score or aggregate gate pass.  M0.2c.3b.1 [sealed craft-reference source/synthetic evidence](docs/verification/2026-09-20-craft-reference-seal.md) verifies preserved bytes and the registered source/resource join; no protected score or aggregate gate pass. |
| F11 | All nested usage and team/agent/evaluation budget enforcement | PL | M0, M1, M2, M4 | T12 | in_progress | M2.2 hierarchical reserves/settles/adjustments and unknown blocking. M0.3b.2c.1 reconciles native attempts/safety releases into local worker counters across epochs; [movement](docs/verification/2026-09-19-forge-movement.md) also charges neutral/coasting/walking ticks. .2c.2 must post actual/uncertain aggregate usage without refunds. Provider all-call reconciliation/dispatch remains open. September 19 [crafting evidence](docs/verification/2026-09-19-forge-crafting.md) adds charged book fills, confirmed output/remainder transfers and feedback waits; no model inference or aggregate qualification. D07 [menu-close evidence](docs/verification/2026-09-19-menu-close.md) charges close, refresh and feedback waits; native release remains reserved, while aggregate settlement stays unqualified. [Authentic vanilla menu evidence](docs/verification/2026-09-19-vanilla-menu.md) adds player-menu cursor/grid returns, duplicate handling, retained pre-acceptance schema/revision rejections, 24 total charged primitives and final saved inventory; complete profile/reference/accounting gates remain open. D09 [manual-craft evidence](docs/verification/2026-09-19-manual-craft.md) adds explicit source selection, ordinary confirmed grid filling and retained partial-effect charges; synthetic checks pass, authentic scope remains open.  M0.1c.2b.2e adds [authenticated native request admission](docs/verification/2026-09-20-native-ingress.md), with source/native synthetic evidence; OAuth transport and complete isolation remain unqualified.  M0.1c.2b.2f adds [native OAuth transport candidate evidence](docs/verification/2026-09-20-native-oauth-transport.md); fabricated authentication does not qualify live TLS/account/usage.  [First OAuth trial/diagnostic/catalog evidence](docs/verification/2026-09-20-native-oauth-conformance.md): one unresolved request, $0.7554 hold; source checks and native metadata evidence do not close this row. |
| F12 | Fixed-system cohorts, model-generation/drift quarantine | RS | M1, M5 | T14 | in_progress | M3.2: [identity decisions](evaluator/src/strata_evaluator/probes.py) classify drift/unverifiable identity and quarantine boundary; actual supervisor revocation/cohort/anchor workflow open. |
| F13 | Reproducible evidence, uncertainty, censoring and interventions | RS | M2, M3, M5 | T13, T15 | in_progress | M3.3/M5.1: [paired analysis](evaluator/src/strata_evaluator/analysis.py), bounds/replay/private publication; full survival/power analysis, evidence inventory and real study open.  M0.2c.3 [private telemetry authentication](docs/verification/2026-09-20-authenticated-telemetry.md) adds source/synthetic byte/boot binding; no authentic score or aggregate gate pass.  M0.2c.3b.1 [sealed craft-reference source/synthetic evidence](docs/verification/2026-09-20-craft-reference-seal.md) verifies preserved bytes and the registered source/resource join; no protected score or aggregate gate pass. |
| F14 | Calibrated graduation/retention and frozen historical anchors | RS | M6 | T16 | deferred | Required in M6 before promotion claims. |
| F15 | Each later pack/version separately conformant; fresh-world transfer | GI | M6 | T17 | deferred | Required E6E/E2E work in M6. |
| F16 | Typed lifecycle/acquisition/capability/game/settings/telemetry/communication/artifact/evaluation contracts | PL | M1 | T01 | in_progress | All 13 records, partitioned schemas and domain services; M0.3b.2b.2 adds typed native authority/body-bound observations and a shared public gateway contract. Full service/controller integration and remaining API domains stay open. September 19 [crafting evidence](docs/verification/2026-09-19-forge-crafting.md) adds strict body-bound recipe pages, a craft envelope and twelve-action capability minor 10 across Java/TypeScript/Python. D07 [menu-close evidence](docs/verification/2026-09-19-menu-close.md) adds strict close_window, regenerated schemas and thirteen-action negotiation (Forge minor 11 / Mineflayer minor 6). [Authentic vanilla menu evidence](docs/verification/2026-09-19-vanilla-menu.md) adds player-menu cursor/grid returns, duplicate handling, retained pre-acceptance schema/revision rejections, 24 total charged primitives and final saved inventory; complete profile/reference/accounting gates remain open. [Body-revision evidence](docs/verification/2026-09-19-body-revision.md) fixes idle heartbeat invalidation and adds authentic scoped CLI acceptance/actual-turn/age negatives; full native host and body-transition conformance stay open. D08 [JEI query evidence](docs/verification/2026-09-19-jei-query.md) adds bounded focused discovery, strict scoped/body-bound transport and exact dependency/policy pins; native effects/isolation remain unverified, with no gate change. D09 [manual-craft evidence](docs/verification/2026-09-19-manual-craft.md) adds explicit source selection, ordinary confirmed grid filling and retained partial-effect charges; synthetic checks pass, authentic scope remains open.  M0.1c.2b.2e adds [authenticated native request admission](docs/verification/2026-09-20-native-ingress.md), with source/native synthetic evidence; OAuth transport and complete isolation remain unqualified.  M0.1c.2b.2f adds [native OAuth transport candidate evidence](docs/verification/2026-09-20-native-oauth-transport.md); fabricated authentication does not qualify live TLS/account/usage.  [First OAuth trial/diagnostic/catalog evidence](docs/verification/2026-09-20-native-oauth-conformance.md): one unresolved request, $0.7554 hold; source checks and native metadata evidence do not close this row.  M0.2c.3 [private telemetry authentication](docs/verification/2026-09-20-authenticated-telemetry.md) adds source/synthetic byte/boot binding; no authentic score or aggregate gate pass.  M0.2c.3b.1 [sealed craft-reference source/synthetic evidence](docs/verification/2026-09-20-craft-reference-seal.md) verifies preserved bytes and the registered source/resource join; no protected score or aggregate gate pass. |
| N01 | Fail closed on unsupported schema/capability/lock/isolation/accounting | PL | M0, M1 | T01, T04, T06 | in_progress | Schema, scope, epoch, quota, pack/admission and unknown-metering denials exercised synthetically; complete real environment admission remains open. [Body-revision evidence](docs/verification/2026-09-19-body-revision.md) fixes idle heartbeat invalidation and adds authentic scoped CLI acceptance/actual-turn/age negatives; full native host and body-transition conformance stay open. D08 [JEI query evidence](docs/verification/2026-09-19-jei-query.md) adds bounded focused discovery, strict scoped/body-bound transport and exact dependency/policy pins; native effects/isolation remain unverified, with no gate change. D09 [manual-craft evidence](docs/verification/2026-09-19-manual-craft.md) adds explicit source selection, ordinary confirmed grid filling and retained partial-effect charges; synthetic checks pass, authentic scope remains open.  M0.1c.2b.2e adds [authenticated native request admission](docs/verification/2026-09-20-native-ingress.md), with source/native synthetic evidence; OAuth transport and complete isolation remain unqualified.  M0.1c.2b.2f adds [native OAuth transport candidate evidence](docs/verification/2026-09-20-native-oauth-transport.md); fabricated authentication does not qualify live TLS/account/usage.  [First OAuth trial/diagnostic/catalog evidence](docs/verification/2026-09-20-native-oauth-conformance.md): one unresolved request, $0.7554 hold; source checks and native metadata evidence do not close this row.  M0.2c.3 [private telemetry authentication](docs/verification/2026-09-20-authenticated-telemetry.md) adds source/synthetic byte/boot binding; no authentic score or aggregate gate pass.  M0.2c.3b.1 [sealed craft-reference source/synthetic evidence](docs/verification/2026-09-20-craft-reference-seal.md) verifies preserved bytes and the registered source/resource join; no protected score or aggregate gate pass. |
| N02 | One executor; deduplicated dispatch; ambiguous-ack resync | GI | M1, M2 | T07 | in_progress | Durable native/public intent, single lock/lane and cancellation fencing. M0.3b.2b.2 tests second-broker rejection, lost reply/no replay, actual synthetic JVM kill and higher-epoch retained consumption through the public worker. Authentic Minecraft ambiguity/recovery remains open. September 19 [crafting evidence](docs/verification/2026-09-19-forge-crafting.md) cancels the real crafting motor over synthetic menus without replay; partial grid/cursor effects remain. D07 [menu-close evidence](docs/verification/2026-09-19-menu-close.md) retains ambiguous close effects without reopening or replaying the operation. [Authentic vanilla menu evidence](docs/verification/2026-09-19-vanilla-menu.md) adds player-menu cursor/grid returns, duplicate handling, retained pre-acceptance schema/revision rejections, 24 total charged primitives and final saved inventory; complete profile/reference/accounting gates remain open. [Body-revision evidence](docs/verification/2026-09-19-body-revision.md) fixes idle heartbeat invalidation and adds authentic scoped CLI acceptance/actual-turn/age negatives; full native host and body-transition conformance stay open. D09 [manual-craft evidence](docs/verification/2026-09-19-manual-craft.md) adds explicit source selection, ordinary confirmed grid filling and retained partial-effect charges; synthetic checks pass, authentic scope remains open.  Latest [vanilla cancel/reconnect](docs/verification/2026-09-20-vanilla-reconnect.md) has a passing narrow independent audit with all raw checker failures retained; complete profile/gate coverage remains open.  M0.2c.3 [private telemetry authentication](docs/verification/2026-09-20-authenticated-telemetry.md) adds source/synthetic byte/boot binding; no authentic score or aggregate gate pass.  M0.2c.3b.1 [sealed craft-reference source/synthetic evidence](docs/verification/2026-09-20-craft-reference-seal.md) verifies preserved bytes and the registered source/resource join; no protected score or aggregate gate pass. |
| N03 | Real-time clocks, ticks, latency and performance accounting | QA | M1, M2, M4 | T08, T09, T12 | in_progress | [Measured interval ledger](src/mcbench/clocks.py) separates active/elapsed/ticks/reserved-body exposure, with rollback-safe deduplication and repair-hold attribution without double charging. Exact boundary coverage, actual telemetry and performance reconciliation remain open. [Authentic vanilla menu evidence](docs/verification/2026-09-19-vanilla-menu.md) adds player-menu cursor/grid returns, duplicate handling, retained pre-acceptance schema/revision rejections, 24 total charged primitives and final saved inventory; complete profile/reference/accounting gates remain open. [Body-revision evidence](docs/verification/2026-09-19-body-revision.md) fixes idle heartbeat invalidation and adds authentic scoped CLI acceptance/actual-turn/age negatives; full native host and body-transition conformance stay open.  M0.1c.2b.2e adds [authenticated native request admission](docs/verification/2026-09-20-native-ingress.md), with source/native synthetic evidence; OAuth transport and complete isolation remain unqualified.  M0.1c.2b.2f adds [native OAuth transport candidate evidence](docs/verification/2026-09-20-native-oauth-transport.md); fabricated authentication does not qualify live TLS/account/usage.  [First OAuth trial/diagnostic/catalog evidence](docs/verification/2026-09-20-native-oauth-conformance.md): one unresolved request, $0.7554 hold; source checks and native metadata evidence do not close this row. |
| N04 | Secrets/private records/initial artifacts protected from agent code | SI | M1 | T06 | in_progress | [Namespaced CAS](src/mcbench/storage.py), immutable initial-artifact policy and explicit private report projection; actual credential/process/network isolation open. D08 [JEI query evidence](docs/verification/2026-09-19-jei-query.md) adds bounded focused discovery, strict scoped/body-bound transport and exact dependency/policy pins; native effects/isolation remain unverified, with no gate change. D09 [manual-craft evidence](docs/verification/2026-09-19-manual-craft.md) adds explicit source selection, ordinary confirmed grid filling and retained partial-effect charges; synthetic checks pass, authentic scope remains open.  M0.1c.2b.2e adds [authenticated native request admission](docs/verification/2026-09-20-native-ingress.md), with source/native synthetic evidence; OAuth transport and complete isolation remain unqualified.  M0.1c.2b.2f adds [native OAuth transport candidate evidence](docs/verification/2026-09-20-native-oauth-transport.md); fabricated authentication does not qualify live TLS/account/usage.  [First OAuth trial/diagnostic/catalog evidence](docs/verification/2026-09-20-native-oauth-conformance.md): one unresolved request, $0.7554 hold; source checks and native metadata evidence do not close this row.  M0.2c.3 [private telemetry authentication](docs/verification/2026-09-20-authenticated-telemetry.md) adds source/synthetic byte/boot binding; no authentic score or aggregate gate pass.  M0.2c.3b.1 [sealed craft-reference source/synthetic evidence](docs/verification/2026-09-20-craft-reference-seal.md) verifies preserved bytes and the registered source/resource join; no protected score or aggregate gate pass. |
| N05 | Safe exhaustion handling; costs retained; gameplay failures preserved | QA | M2 | T07, T08, T12 | in_progress | Local/native action limits, native release reserve and evidence-failure fencing plus hierarchical blocking/overruns and confirmatory rollback rejection. Synthetic exhaustion evidence does not qualify actual whole-process/team coordinated stopping. September 19 [movement exhaustion tests](docs/verification/2026-09-19-forge-movement.md) retain charged neutral/walking/coasting events and release a synthetic active walk without refund. September 19 [crafting evidence](docs/verification/2026-09-19-forge-crafting.md) preserves partial crafting effects and consumed budget through deadline/exhaustion with release. D07 [menu-close evidence](docs/verification/2026-09-19-menu-close.md) rejects unsafe return capacity before close and preserves consumed budget/partial effects on interrupted feedback. [Authentic vanilla menu evidence](docs/verification/2026-09-19-vanilla-menu.md) adds player-menu cursor/grid returns, duplicate handling, retained pre-acceptance schema/revision rejections, 24 total charged primitives and final saved inventory; complete profile/reference/accounting gates remain open. |
| N06 | Pinned dependencies/protocols and report replay | PL | M1, M2, M5 | T01, T13 | in_progress | Pinned packages, 13 generated contracts, immutable artifact/report digests and journal/report reconstruction. Broker identity hashes all compiled modules, schemas, package lock and native fingerprint; .2c.3b adds the guardian policy/Python version/eight source hashes and explicit Forge worker config v2. Complete installed dependency/environment pins and release reproducibility remain open. [Authentic vanilla menu evidence](docs/verification/2026-09-19-vanilla-menu.md) adds player-menu cursor/grid returns, duplicate handling, retained pre-acceptance schema/revision rejections, 24 total charged primitives and final saved inventory; complete profile/reference/accounting gates remain open. [Body-revision evidence](docs/verification/2026-09-19-body-revision.md) fixes idle heartbeat invalidation and adds authentic scoped CLI acceptance/actual-turn/age negatives; full native host and body-transition conformance stay open. D08 [JEI query evidence](docs/verification/2026-09-19-jei-query.md) adds bounded focused discovery, strict scoped/body-bound transport and exact dependency/policy pins; native effects/isolation remain unverified, with no gate change. D09 [manual-craft evidence](docs/verification/2026-09-19-manual-craft.md) adds explicit source selection, ordinary confirmed grid filling and retained partial-effect charges; synthetic checks pass, authentic scope remains open.  M0.1c.2b.2e adds [authenticated native request admission](docs/verification/2026-09-20-native-ingress.md), with source/native synthetic evidence; OAuth transport and complete isolation remain unqualified.  M0.1c.2b.2f adds [native OAuth transport candidate evidence](docs/verification/2026-09-20-native-oauth-transport.md); fabricated authentication does not qualify live TLS/account/usage.  [First OAuth trial/diagnostic/catalog evidence](docs/verification/2026-09-20-native-oauth-conformance.md): one unresolved request, $0.7554 hold; source checks and native metadata evidence do not close this row.  M0.2c.3 [private telemetry authentication](docs/verification/2026-09-20-authenticated-telemetry.md) adds source/synthetic byte/boot binding; no authentic score or aggregate gate pass.  M0.2c.3b.1 [sealed craft-reference source/synthetic evidence](docs/verification/2026-09-20-craft-reference-seal.md) verifies preserved bytes and the registered source/resource join; no protected score or aggregate gate pass. |
| N07 | Measured operating envelope before confirmation | QA | M2, M4 | T08, T09 | not_started | — |
| N08 | Durable bounded private storage; no silent evidence deletion | PL | M1, M2 | T07, T13 | in_progress | [Private CAS/outbox](src/mcbench/storage.py), quota-before-write/checkpoint commits and M0.3b.2a forced native intent/delivery/event journal. Native development ceiling fences instead of discarding evidence; archival/rotation, complete disk exhaustion/retention and deployment controls remain open. [Authentic vanilla menu evidence](docs/verification/2026-09-19-vanilla-menu.md) adds player-menu cursor/grid returns, duplicate handling, retained pre-acceptance schema/revision rejections, 24 total charged primitives and final saved inventory; complete profile/reference/accounting gates remain open.  M0.2c.3 [private telemetry authentication](docs/verification/2026-09-20-authenticated-telemetry.md) adds source/synthetic byte/boot binding; no authentic score or aggregate gate pass.  M0.2c.3b.1 [sealed craft-reference source/synthetic evidence](docs/verification/2026-09-20-craft-reference-seal.md) verifies preserved bytes and the registered source/resource join; no protected score or aggregate gate pass. |

## Feature coverage beyond requirement titles

September 20 C06/C14/C18/C20 delta: [native helper/context evidence](docs/verification/2026-09-20-native-helpers.md)
adds fingerprinted ephemeral/private-profile storage and observed v2 tools.
Root and child requests retain distinct native thread metadata and one root
turn; private rollout persistence does not prove isolation or checkpoint scope.
All later/self-play behavior and trusted per-helper budget/capability gates remain.

September 20 C14/C15/C18 delta: [complete owned-member stop evidence](docs/verification/2026-09-20-guardian-tree.md)
adds bounded read-only handles and strict private proof. Missing members, late
proof, unsignaled children and query failures never yield confirmed termination.
No clean checkpoint, input release, refunded cost or new gameplay capability is
implied. Pre-attachment and adversarial launch containment remain separate.

C09/C14/C15/C18/C19: [paired modded block failure and candidate repair](docs/verification/2026-09-19-paired-block-reference.md)
add independent boundary saves, retained uncertainty, actual stop timing and
explicit bounded outline policy. Raw exceptions remain private/omitted and
diagnostics cannot precede release. No schema affordance, model budget, physical
input, scored success, full checkpoint or security-isolation pass is inferred.

C09/C19 and private evaluation gain the [saved-block reference utility](docs/verification/2026-09-19-saved-block-reference.md).
It is evaluator-only; all 13 public records, action affordances, clocks, budget
limits and scientific comparisons are unchanged. No before-state, full-world
checkpoint, causal effect, registry validity or same-user isolation is inferred.

C02/C09/C15/C18: the [worker trial](docs/verification/2026-09-19-desktop-worker.md)
composes bounded fenced desktop startup with the existing worker-owned guardian;
no competing guardian, native/admin mutation token in scoped checks or OS input route. Startup
session lifetime and post-provider expiry checks preserve credential/account
boundaries; same-user ACLs still do not establish adversarial isolation.

[Private-frame evidence](docs/verification/2026-09-19-private-frames.md) advances
C02/C09/C15/C18: exact pre-display hook/native readback, strict private requests,
durable intent, bounded count/size/clocks, retained failures, no replay and actual
PNG/visual verification. OS/compositor/cursor and drawing outside the main target
are not captured; full native/physical-reference parity remains .2b.2/.1b.4/M1.1.

[Guarded client startup](docs/verification/2026-09-19-desktop-client.md) advances
C02/C04/C09/C15/C18 through reviewed installed bootstrap, distinct private-copy
identity, process lifetime and bounded evidence. Native world/frame/input and
full security/resource qualification remain explicit under .2b/.1b.4.

[Launch evidence](docs/verification/2026-09-19-desktop-launch.md) advances
C02/C09/C15/C18: separate non-input desktop, pre-execution job assignment,
bounded watchdog/cleanup and hidden-render prerequisite. Production isolation,
game-only frame evidence and native input remain .2c.3c.2/.1b.4/M1.1.

[Empty-loop evidence](docs/verification/2026-09-19-jei-empty-page.md) extends
C09/C15/C18: distinguish a witnessed empty draw loop from missing hooks, preserve
source/frame/digest checks and allow navigation confirmation on a fresh empty
page. Synthetic transport/motor checks do not qualify actual rendering.

The [history Back extension](docs/verification/2026-09-19-jei-history.md) advances
C09/C15/C18 through .1b.3c: fixed ordinary callback, bounded fresh-frame result,
strict source/page authority and durable charges/cancellation/no replay. This is
synthetic implementation evidence; full page content, physical-key behavior and
authentic mechanics/isolation remain open.

Task-to-JEI child M0.3b.3.2.3c.3.2b.3b.1a adds [partial lifecycle evidence](docs/verification/2026-09-19-quest-jei-lifecycle.md) for F01/F06/F09/F16, N01/N02/N04/N05/N06 and C09/C15. SPEC 8.1 minor 27 distinguishes origin-bound recipe-screen state and ordinary close from current rendered contents/history. All required page/navigation/native/reference/isolation work remains explicit; no aggregate closes.

Choice-control child M0.3b.3.2.3c.3.2b.2b.1 adds [partial implementation evidence](docs/verification/2026-09-19-quest-choice-controls.md) for F01/F06/F09/F16, N01/N02/N04/N05/N06 and C09/C15. Normal Back and wheel preserve source/parent/reward identity, stale-state fencing, charges and no replay; loaded native behavior and private isolation remain unverified. SPEC 8.1's minor 26 policies retain empty choice controls and no claims. No requirement or feature aggregate is closed.

C09/C15/C18 exact-pack container/machine and input-reliability work includes .3.2.1's Thermal GUI adapter and .3.2.2a's [initial transfer/fence candidate](docs/verification/2026-09-19-thermal-transactions.md) (SPEC 8.1/9.1/10.3). Its evidence does not satisfy full .2b routing/controls, .2c energy/fluid operation, .3 discovery or .4 actual UI/server/reference cases.

This inventory preserves important prose obligations. Full details and edge cases remain in the cited SPEC sections. Each row must acquire implementation/evidence links or child items as work proceeds; a broad row cannot close while an applicable child behavior is absent.

| ID | Feature scope | SPEC | Milestone / requirements | Status | Implementation / evidence / next detail |
|---|---|---|---|---|---|
| C01 | Definitions of system/cohort/lineage/campaign/episode/probe; body/helper/replica separation | 1, 13 | M1, M3; F02/F03/F08 | in_progress | Typed roster/cohort/lineage records and lineage-level paired analysis; full runtime separation of bodies/helpers/replicas still open. |
| C02 | Prior-art/source provenance, factual/proposed/unverified labels; bounded compatibility claims | 2, 7, 18 | M0, M5; F01/F05/N06 | in_progress | [Dated evidence](docs/verification/2026-09-18-m0-foundation.md) distinguishes source, synthetic and real gates; no pack support claimed. |
| C03 | Package layout, stack/toolchain locks, deployment profiles; single-controller SQLite/journal/CAS | 4–5 | M1; F16/N06/N08 | in_progress | Pinned Python/Node, separate evaluator package, SQLite WAL/FULL, outbox/CAS and generated schema partitions; qualified deployment integration open. D08 [JEI query evidence](docs/verification/2026-09-19-jei-query.md) adds bounded focused discovery, strict scoped/body-bound transport and exact dependency/policy pins; native effects/isolation remain unverified, with no gate change. |
| C04 | Official acquisition, role inventories, exact bootstrap/client/server/JVM bytes, expert recipe/quest assertions | 7 | M0; F01/F05 | in_progress | [Provider](src/mcbench/provisioning.py) imports exact receipts, streams and verifies role inventories, binds seal checks and materializes fresh copies. Authentic acquisition/bootstrap/cold restart/expert assertions remain open. |
| C05 | Supported authentication, distinct simultaneous player identities, clean templates/materialization and missing-artifact states | 7, 15 | M0, M4; F02/F05/N04 | in_progress | M0.2g actual protected Microsoft authentication and one Java-owning account joined vanilla; M0.3a synthetic template/materialization checks. Distinct simultaneous licensed accounts and full authentic clean templates remain open. |
| C06 | Native Codex CLI loop/plugin load, JSONL/command-bridge negotiation, exec-job conformance, explicit invocation and host capability failures | 6 | M0, M1; F03/F16/N01 | in_progress | [Native runner and exact plugin install evidence](docs/verification/2026-09-18-long-horizon.md); durable bounded jobs, private raw streams, actual pinned installation and real process fixtures. Model-side Dovetail invocation/helpers/all-call accounting/restore and isolation remain open. M0.1c.1a adds [private durable dispatch accounting](docs/verification/2026-09-19-inference-dispatch.md), with synthetic evidence only and live transport integration open.  M0.1c.2b.2a: [native broker source/synthetic integration](docs/verification/2026-09-20-restricted-native-tools.md) enforces explicit projections, helper result writes and executor-only game transport. Full native isolation/live admission remains open. M0.1c.2b.2c adds [native participant/budget admission](docs/verification/2026-09-20-native-admission.md), with clean-helper and inherited-context native synthetic evidence; protected live ingress and complete lifecycle remain unqualified. M0.1c.2b.2d adds [sealed bootstrap/source integrity evidence](docs/verification/2026-09-20-native-bootstrap.md), including native root/helper canaries; aggregate qualification remains incomplete.  M0.1c.2b.2e adds [authenticated native request admission](docs/verification/2026-09-20-native-ingress.md), with source/native synthetic evidence; OAuth transport and complete isolation remain unqualified.  M0.1c.2b.2f adds [native OAuth transport candidate evidence](docs/verification/2026-09-20-native-oauth-transport.md); fabricated authentication does not qualify live TLS/account/usage.  [First OAuth trial/diagnostic/catalog evidence](docs/verification/2026-09-20-native-oauth-conformance.md): one unresolved request, $0.7554 hold; source checks and native metadata evidence do not close this row. |
| C07 | Immutable initial skills, learned revisions, executable macro restrictions, notes/handoffs/compaction/resume and artifact quotas | 6, 9, 13 | M1, M3; F03/F07/F08 | in_progress | [Artifact activation/episode projections](src/mcbench/artifacts.py), provenance/quota/initial/probe rules; actual runtime export/import, compaction and macro enforcement open. |
| C08 | Helper/self-play clean context AND file/tool isolation, depth/concurrency, ancestry, returned evidence and parent budget | 6, 15 | M0, M1; F03/F04/F11 | in_progress | [Native helper checks](tests/test_native.py): separate profile/workspace, parent account/job, depth/concurrency, no executor game grant, descendant shutdown. Actual model helpers, filesystem/network/tool isolation and returned evidence policy remain open. |
| C09 | Mineflayer structured state/actions, observed-map filtering, pinned local navigation and exact modded API suite; optional pixel/input parity separately | 8 | M0, M1; F01/F06 | in_progress | Mineflayer recipes/crafting, signal waits, bounded placement and confirmed release retained. D06 [Forge API](docs/operations/forge-game-api.md) routes filtered observations/thirteen motors and known recipes through the scoped worker/CLI, including level walking, identity/selection/recipe fences and server-menu feedback. Full geometry/custom recipe adapters/placement and both profiles' complete authentic conformance stay open. D07 [menu-close evidence](docs/verification/2026-09-19-menu-close.md) supplies explicit close with own-inventory resource checks on both backends. [Authentic vanilla menu evidence](docs/verification/2026-09-19-vanilla-menu.md) adds player-menu cursor/grid returns, duplicate handling, retained pre-acceptance schema/revision rejections, 24 total charged primitives and final saved inventory; complete profile/reference/accounting gates remain open. [Body-revision evidence](docs/verification/2026-09-19-body-revision.md) fixes idle heartbeat invalidation and adds authentic scoped CLI acceptance/actual-turn/age negatives; full native host and body-transition conformance stay open. D08 [JEI query evidence](docs/verification/2026-09-19-jei-query.md) adds bounded focused discovery, strict scoped/body-bound transport and exact dependency/policy pins; native effects/isolation remain unverified, with no gate change. D09 [manual-craft evidence](docs/verification/2026-09-19-manual-craft.md) adds explicit source selection, ordinary confirmed grid filling and retained partial-effect charges; synthetic checks pass, authentic scope remains open. |
| C10 | Capability-gated keybinding discover/diagnose/tested-pool allocation, contexts/backend/Unicode distinctions, protected controls, transactional patch and rollback | 8–10 | M1.1; F06/N02 | in_progress | [Transaction engine](src/mcbench/controls.py), [skill](gameplay/skills/minecraft-keybindings/SKILL.md), [bounded operator audit](src/mcbench/client_discovery.py), real Forge discovery/UI sample and [Java transaction core](java/forge1192-client). Source-bound Curios adapter built; mutation/recovery has synthetic-runtime tests only. Real qualification and tested input remain open. |
| C11 | Actual intended/competing key effects, persistence/restart, cross-client isolation; charged in-play repairs and matched probe keymaps | 8, 13 | M1.1, M2, M3; F06/F08/N03 | in_progress | Synthetic effect/restart, per-avatar repair holds, cognitive-probe repair prohibition and budget/clock integration tested. Actual native save plus operator cold restart retained all 253 runtime bindings and matched persistence. No actual changed-binding transaction, worker restart, game effects, in-play charges or cross-client isolation evidence yet. |
| C12 | Worker/game/runtime/evaluator process and host boundaries, credential brokerage, filesystem/network/capability enforcement and leak attempts | 4–6, 10, 13 | M1; F04/N04 | in_progress | Scoped method grants/CAS namespace checks and evaluator packaging implemented; no OS/process/network/helper isolation claim. D08 [JEI query evidence](docs/verification/2026-09-19-jei-query.md) adds bounded focused discovery, strict scoped/body-bound transport and exact dependency/policy pins; native effects/isolation remain unverified, with no gate change.  M0.1c.2b.2e adds [authenticated native request admission](docs/verification/2026-09-20-native-ingress.md), with source/native synthetic evidence; OAuth transport and complete isolation remain unqualified.  M0.1c.2b.2f adds [native OAuth transport candidate evidence](docs/verification/2026-09-20-native-oauth-transport.md); fabricated authentication does not qualify live TLS/account/usage.  [First OAuth trial/diagnostic/catalog evidence](docs/verification/2026-09-20-native-oauth-conformance.md): one unresolved request, $0.7554 hold; source checks and native metadata evidence do not close this row.  M0.2c.3 [private telemetry authentication](docs/verification/2026-09-20-authenticated-telemetry.md) adds source/synthetic byte/boot binding; no authentic score or aggregate gate pass.  M0.2c.3b.1 [sealed craft-reference source/synthetic evidence](docs/verification/2026-09-20-craft-reference-seal.md) verifies preserved bytes and the registered source/resource join; no protected score or aggregate gate pass. |
| C13 | Pinned allowed docs, player-accessible recipe/quest projections, sanitized goals/control cards, declared messages and no implicit shared memory | 4, 6, 8, 10, 13 | M1, M4; F04/F07 | in_progress | Sanitized skill, declared team messages and server-unlocked vanilla recipe projections implemented; pinned docs, quest surface and exact expert serializers open. |
| C14 | Campaign/worker/agent states, ownership, deadlines, durable revisions, sequence/epoch fencing and health leases | 10–11 | M1, M2; F09/F16/N01 | in_progress | [Controller](src/mcbench/controller.py) durable lifecycle, owned transitions, epochs, readiness and cleanup-held reservations; worker/runtime supervisor integration open. |
| C15 | Action deduplication, ambiguous emission recovery, cancel/stop-all watchdog, hung-client termination and late-tool rejection | 8, 10–12 | M2; F09/N02/N05 | in_progress | Native/Mineflayer cancellation/ack/release tests plus synthetic JVM kill and queue fencing. [Integrated independent guard](docs/verification/2026-09-18-forge-guard-integration.md) binds listener/session/body generation and stops native-thread/worker/parent faults without replay. Authentic timings, production controller recovery, complete launch containment, disk-full and full game/agent restoration remain open. September 19 [crafting evidence](docs/verification/2026-09-19-forge-crafting.md) extends synthetic lane cancellation/deadline/exhaustion to recipe fill and output pickup. D07 [menu-close evidence](docs/verification/2026-09-19-menu-close.md) tests close cancellation/deadline/exhaustion and retains uncertain post-close state without replay. [Authentic vanilla menu evidence](docs/verification/2026-09-19-vanilla-menu.md) adds player-menu cursor/grid returns, duplicate handling, retained pre-acceptance schema/revision rejections, 24 total charged primitives and final saved inventory; complete profile/reference/accounting gates remain open. [Body-revision evidence](docs/verification/2026-09-19-body-revision.md) fixes idle heartbeat invalidation and adds authentic scoped CLI acceptance/actual-turn/age negatives; full native host and body-transition conformance stay open. D09 [manual-craft evidence](docs/verification/2026-09-19-manual-craft.md) adds explicit source selection, ordinary confirmed grid filling and retained partial-effect charges; synthetic checks pass, authentic scope remains open. |
| C16 | Complete clean-stop world/player/quest/team/machine/client/runtime/skill snapshots, atomic commit, same-boundary restore | 11–12 | M2; F09/N06/N08 | in_progress | [Checkpoint service](src/mcbench/checkpoints.py) validates complete rosters/path inventories and clean-stop attestations, commits immutable sets and materializes fresh worlds; real stop/restore open. |
| C17 | Crash/rate-limit/credential/disk/resource/stall incidents, interventions; no gameplay undo, cost refund or future-knowledge retention | 12 | M2; F09/N05 | in_progress | Confirmatory rollback rejection, development lost-interval plan, retained budget costs and crash-safe intent tested synthetically; full incident classifier/recovery supervisor open. |
| C18 | Active/elapsed/server/avatar clocks, checkpoint timing/drain overrun, state/action/model lag, event-loop lag/TPS/MSPT and conditional FPS | 11–12, 15 | M2, M4; N03/N07 | in_progress | [Clock ledger](src/mcbench/clocks.py), [Forge telemetry](java/forge1192-telemetry): actual E9E server ticks, sampled wall intervals, rolling MSPT and GC/heap evidence. Avatar tick parity, full supervisor/model/worker reconciliation, overhead and envelope calibration remain open.  [First OAuth trial/diagnostic/catalog evidence](docs/verification/2026-09-20-native-oauth-conformance.md): one unresolved request, $0.7554 hold; source checks and native metadata evidence do not close this row.  M0.2c.3 [private telemetry authentication](docs/verification/2026-09-20-authenticated-telemetry.md) adds source/synthetic byte/boot binding; no authentic score or aggregate gate pass.  M0.2c.3b.1 [sealed craft-reference source/synthetic evidence](docs/verification/2026-09-20-craft-reference-seal.md) verifies preserved bytes and the registered source/resource join; no protected score or aggregate gate pass. |
| C19 | Durable raw evidence, delivered structured state/signals and optional images/video, retention/tombstones, private export/redaction and report replay | 5, 12 | M2, M5; F13/N06/N08 | in_progress | CAS/outbox and deterministic report/journal exports, private-ID publication allowlist; full retention/tombstones, complete raw-reference replay and live evidence open. D08 [JEI query evidence](docs/verification/2026-09-19-jei-query.md) adds bounded focused discovery, strict scoped/body-bound transport and exact dependency/policy pins; native effects/isolation remain unverified, with no gate change. |
| C20 | Team/agent budget reservations/settlement/reconciliation, descendant/retry/practice/probe charges and unknown metering | 9–10, 15 | M1, M2; F11/N01 | in_progress | [Budgets](src/mcbench/budgets.py) support nested accounts/reservations/settles/reconciliation, retries and unknown blocking; provider/host metering and unknown reconciliation completion open. D09 [manual-craft evidence](docs/verification/2026-09-19-manual-craft.md) adds explicit source selection, ordinary confirmed grid filling and retained partial-effect charges; synthetic checks pass, authentic scope remains open. M0.1c.1a adds [private durable dispatch accounting](docs/verification/2026-09-19-inference-dispatch.md), with synthetic evidence only and live transport integration open.  M0.1c.2b.2e adds [authenticated native request admission](docs/verification/2026-09-20-native-ingress.md), with source/native synthetic evidence; OAuth transport and complete isolation remain unqualified.  M0.1c.2b.2f adds [native OAuth transport candidate evidence](docs/verification/2026-09-20-native-oauth-transport.md); fabricated authentication does not qualify live TLS/account/usage.  [First OAuth trial/diagnostic/catalog evidence](docs/verification/2026-09-20-native-oauth-conformance.md): one unresolved request, $0.7554 hold; source checks and native metadata evidence do not close this row. |
| C21 | Measured backend hardware/accounts/provider capacity (displays only when used), N=1/2/4, atomic team queue/reject, no time-sharing/substitution | 11, 15–16 | M4; F02/N07 | in_progress | Atomic team capacity/account reservations, queue/reject and expiry-cleanup tests; no measured certificate or authentic simultaneous N test. |
| C22 | Persistent natural play, one-way disposable probes, matched fresh contexts/world/equipment/keymap, sealed instances and no tuning feedback | 13 | M1, M3; F08 | in_progress | [Matched clone manifests](evaluator/src/strata_evaluator/probes.py) and artifact taint rejection; actual fresh clone execution/disposal and canary isolation open. |
| C23 | Full/frozen-persistence/frozen-skills/no-self-play policies; exact reset surfaces and budget-dependent experimental arms | 13.2 | M3, M5; F07/F08/F11 | in_progress | All four episode artifact projections implemented and tested; no campaign arm has run and native session reset enforcement remains open. |
| C24 | Server-verified milestones, alternate strategies, sustained automation and positive/negative controls | 13, 16 | M0, M3; F10 | in_progress | [Private development predicates](evaluator/src/strata_evaluator/scorer.py), craft alternatives and sustained machine/negative controls; server telemetry/reachability/parity open.  M0.2c.3 [private telemetry authentication](docs/verification/2026-09-20-authenticated-telemetry.md) adds source/synthetic byte/boot binding; no authentic score or aggregate gate pass.  M0.2c.3b.1 [sealed craft-reference source/synthetic evidence](docs/verification/2026-09-20-craft-reference-seal.md) verifies preserved bytes and the registered source/resource join; no protected score or aggregate gate pass. |
| C25 | AG/absolute success/AULC/AUG, independent paired samples, clustering, CI/multiplicity, censoring/attrition bounds and power plan | 13 | M3, M5; F13 | in_progress | Paired family-weighted AG/absolute success, block bootstrap, common-support areas, Holm and attrition bounds implemented; survival/hierarchical generalization/power simulation and confirmation open. |
| C26 | Retention and fresh-world target-pack transfer, source cost, fixed-system versus new-generation cohorts and drift quarantine | 13 | M3, M5, M6; F08/F12/F14/F15 | in_progress | Fixed-system drift/quarantine decision logic implemented; real cohort/anchor lifecycle, retention and fresh-pack transfer remain open/deferred to M6 where applicable. |
| C27 | Fixed aggregate versus fixed-per-agent N comparisons; summed ticks/reserved body time, repeated-call costs and concurrency reporting | 13, 15 | M3, M4; F02/F11/N03 | in_progress | Hierarchical caps and reserved-body versus actual-tick accounting tested; resource-plan derivation and real fixed-team/per-agent comparisons remain open. |
| C28 | Task DAG/calibration, promotion/retention thresholds, repeated-look control, independent confirmation, ceiling/prerequisite outcomes and historical anchors | 14 | M6; F14 | deferred | Required in M6; not replaced by pack-number ordering. |
| C29 | E6E and E2E version-specific Java/loader/input/GUI/quest/save modules and conformance | 7, 14, 16 | M6; F15 | deferred | Required later support, each exact profile separately gated. |
| C30 | Operator CLI/services, typed errors, status/stop/abort, handbook, static reports, versioned reproducible release | 10, 17 | M1, M2, M5; F13/F16 | in_progress | [Operator commands](src/mcbench/commands.py), [offline report CLI](evaluator/src/strata_evaluator/cli.py), runbooks; full live lifecycle commands and release remain open. |
| C31 | Optional pixel/OS, expanded semantic assistance and open-web conditions with distinct affordance/information/score identities | 4, 8, 13 | Later explicit condition; F06/F07/F13 | deferred | D01 makes structured control primary; these expanded/alternative conditions remain optional. |
| C32 | Budgeted practice worlds and optional mechanic-intervention diagnostics, reachability and no holdout contamination | 6, 13, 15 | Later explicit condition; F03/F08/F11 | deferred | Optional; practice quota remains zero by default. |
| C33 | Additional packs, provider extensions and broader platform/input modules | 5, 7, 17 | M6 / later scope; F05/F15 | deferred | Preserve boundaries; add each target by explicit lock and conformance. |
| C34 | Remote workers/mTLS, distributed scheduling, PostgreSQL/object storage and interactive dashboard | 4–5, 17 | M7; F02/F13/F16/N04/N08 | deferred | Needs-driven and optional; retain individual activation decisions. |
| C35 | Full test suite, staged gates, risk ownership, requirement traceability and no unjustified completion claims | 3, 16–19 | M0–M7; all requirements | in_progress | [115 Python / 26 Node checks](docs/verification/2026-09-18-controller-evaluator.md), separate binding checks and wheel builds; original IDs/features and later/optional work retained. Aggregate suites/gates not run. |
| C36 | Optional MCP game facade and app-server lifecycle adapter, sharing the same scoped contracts and independent conformance | 4, 6, 10 | Demonstrated native boundary need; F03/F16/N01 | in_progress | M0.1c.2b.2a activates a candidate native stdio broker for tool/helper enforcement after shell-boundary failures; same scoped game contract, explicit profile, [source/synthetic evidence](docs/verification/2026-09-20-restricted-native-tools.md). Full conformance remains open; app-server remains deferred until a demonstrated lifecycle need. Neither adapter is independently mandatory. M0.1c.2b.2c adds [native participant/budget admission](docs/verification/2026-09-20-native-admission.md), with clean-helper and inherited-context native synthetic evidence; protected live ingress and complete lifecycle remain unqualified. M0.1c.2b.2d adds [sealed bootstrap/source integrity evidence](docs/verification/2026-09-20-native-bootstrap.md), including native root/helper canaries; aggregate qualification remains incomplete.  M0.1c.2b.2e adds [authenticated native request admission](docs/verification/2026-09-20-native-ingress.md), with source/native synthetic evidence; OAuth transport and complete isolation remain unqualified.  M0.1c.2b.2f adds [native OAuth transport candidate evidence](docs/verification/2026-09-20-native-oauth-transport.md); fabricated authentication does not qualify live TLS/account/usage.  [First OAuth trial/diagnostic/catalog evidence](docs/verification/2026-09-20-native-oauth-conformance.md): one unresolved request, $0.7554 hold; source checks and native metadata evidence do not close this row. |

### Schema inventory

SPEC section 9 defines these typed contracts. All 13 have strict models, exported schemas and generated TypeScript, with synthetic example/negative tests. Cross-record and real integration coverage is partial; aggregate T01 remains `not_run`. Own them under M1, with domain owners as in SPEC.

| Record | Owner | Required integration | Status | Implementation / evidence |
|---|---|---|---|---|
| PackLock | GI | Candidate/sealed invariants, provenance and installed inventory | in_progress | [Model](src/mcbench/records.py), [provider](src/mcbench/provisioning.py) and bound seal/materialization tests; no authentic installed lock yet. |
| CampaignConfig | PL | Roster, profiles, budgets, schedule, admission and recovery | in_progress | [Model](src/mcbench/records.py), roster/schedule checks and controller; live profile/reference completeness open. |
| AgentConfig | AR | Runtime/model/plugin/skills/credentials references and helper policy | in_progress | [Model](src/mcbench/records.py), model assurance/account uniqueness checks; native runtime/helper conformance open. |
| Observation | GI | Scoped structured state/signals, observation age/revisions/capability digest; optional image/keymap | in_progress | [Pydantic/schema](src/mcbench/contracts.py), generated binding, bounded signals and timeout/disconnected age tests; spatial pagination, optional pixel conformance and live evidence open. |
| ActionBatch | GI | Lease/epoch/sequence/preconditions, one typed bounded action, conditional raw events | in_progress | [Pydantic](src/mcbench/contracts.py), [public schema](schemas/v1/public/ActionBatch.json), durable lane; full input semantics/action set and live evidence open. |
| ActionAck | GI | Accepted/executing/completed/failed/cancelled/unknown, partial effects and resync | in_progress | [Pydantic](src/mcbench/contracts.py), [public schema](schemas/v1/public/ActionAck.json), synthetic lifecycle/recovery tests; actual postconditions/uncertainty tests open. |
| GameEvent | GI | Private authoritative payloads, event identity and validation | in_progress | [Record](src/mcbench/records.py) and registered evaluator payload validation/deduplication; actual telemetry producer open. |
| SkillRevision | AR | Provenance, ancestry, activation and forbidden probe imports | in_progress | [Model](src/mcbench/records.py), [activation service](src/mcbench/artifacts.py), provenance and probe-import tests; runtime activation integration open. |
| KeybindingPatch | GI | Stable IDs/owner/backend/contexts/modifiers/CAS/restart evidence | in_progress | [Model](src/mcbench/records.py), [transaction logic](src/mcbench/controls.py); wire-adapter connection and actual Forge evidence open. |
| CheckpointManifest | PL | Consistent full set including backend cache/state and conditional keymap; exposure/cursors | in_progress | [Model](src/mcbench/records.py) and [complete-set service](src/mcbench/checkpoints.py); actual clean-stop/restore evidence open. |
| BudgetLedger | PL | Reserves/settles/adjustments, actual calls and unknown metering | in_progress | [Model](src/mcbench/records.py) and [hierarchical ledger](src/mcbench/budgets.py); provider reconciliation/unknown resolution and dispatch integration open. |
| EvaluationProtocol | RS | Private sealed definitions, budgets, samples and analysis | in_progress | [Model](src/mcbench/records.py), schedule/weight checks; actual sealing/preregistration/cross-record validation open. |
| EvaluationResult | RS | Private paired results, evidence, censoring and validity | in_progress | [Model](src/mcbench/records.py), outcome checks and paired analysis; live probe/scorer persistence pipeline open. |

### API inventory

Each domain inherits SPEC section 10's authentication/authorization, version negotiation, IDs, deadlines, errors, persistence and idempotency rules. Track implementation under M1/F16, tested by T01 plus domain cases.

| Domain | Contract scope | Status | Implementation / evidence |
|---|---|---|---|
| Lifecycle | Campaign create/status/start/checkpoint/stop/abort; worker register/heartbeat/reserve/release | in_progress | [Controller](src/mcbench/controller.py) and draft/status/preflight CLI; actual process supervisor and live endpoints open. |
| Pack acquisition | Resolve/acquire/verify/seal/materialize; operator/artifact waits | in_progress | [Private provider/CLI](src/mcbench/pack_commands.py): durable resolve/acquire/import/verify/seal/materialize; actual official acquisition and supervisor launch remain open. |
| Capabilities | Required/optional negotiation and fail-closed profile fingerprints | in_progress | [Development manifest](backends/mineflayer/src/capabilities.ts) and scoped checks; [D08 Forge minor 12](docs/verification/2026-09-19-jei-query.md) declares exact JEI version/source/bounds and policy. Complete signed negotiation and real conformance still open. |
| Observation/actions | Observe/wait-events/act/typed wrappers/status/cancel/stop-all; bounded recipe discovery; conditional input; stale/ambiguous-action handling | in_progress | [Gateway/CLI](backends/mineflayer/src/) supports both development routes; the separate Forge candidate has thirteen motors, player-book recipes and [focused JEI queries](docs/verification/2026-09-19-jei-query.md). Java/TypeScript/Python query contracts reject hidden fields and source/body mismatches before scoped delivery. Authentic effects, custom mechanics, native host, aggregate clock/charge/stop integration and full isolation remain open. D09 [manual craft](docs/verification/2026-09-19-manual-craft.md) adds explicit JEI selection and ordinary grid fill; authentic effects remain unverified. |
| Keybindings | List/capabilities/plan/apply/status/rollback; serialized verification | in_progress | [Settings engine](src/mcbench/controls.py), [private native transport](src/mcbench/native_settings.py), [controller repair coordination](src/mcbench/reconfiguration.py) and sanitized skill. Native snapshot remains correctly unqualified. Actual worker-authority transport, qualified projection/effects/commit, complete accounting and gameplay CLI remain open. |
| Telemetry | Private authenticated authoritative event stream and durable cursors | in_progress | Registered private development event payloads and scorer deduplication; authenticated authoritative server producer open. |
| Communication | Scoped team send/receive, ordering, rate/size/TTL and cost | in_progress | [Team service](src/mcbench/communication.py) tested for scope/order/rate/size/TTL; live scoped transport integration open. |
| Artifacts | Authorized content storage, safe paths, quotas and skill publication | in_progress | [CAS](src/mcbench/storage.py) and [revision service](src/mcbench/artifacts.py); actual isolated workspace/runtime integration open. |
| Evaluation | Private schedule/score/export, sealed access and one-way clones | in_progress | [Separate evaluator](evaluator/src/strata_evaluator/) implements predicates, clone plans and offline reports; live sealed scheduling/probe execution open. |
| Agent runtime | Inspect/start/deliver/events/interrupt/export/resume/helpers/stop | in_progress | [Read-only inspection/turn-usage reader](src/mcbench/runtime.py); start/deliver/helper/isolation/interrupt/resume adapter not implemented. |

## Test suites and release gates

September 20 selected-config delta: 51 Python/11 Java checks and a corrected actual E9E two-boot comparison pass narrowly. Original placeholder-selector plan fails source qualification and remains retained. Four unregistered files/three undeclared Create keys explain the unchanged five file failures; 263/268 pass with all check/result/code/success digests identical before/after. All aggregate suite/gate results below remain unchanged.

September 20 native-helper delta: partial T01/T04/T07/T12. Final actual-CLI
clean-context and persistent full-history cases pass, four settled/deduplicated
synthetic calls each. Retain absent legacy tools, ephemeral parent lookup failure
and the initial native event-parser failure with unresolved reservations. 77
relevant Python checks pass, zero skips, plus full Ruff/schema/build/diff checks.
[Report](docs/verification/2026-09-20-native-helpers.md). No aggregate T/G result changes.

September 20 guardian delta: partial T01/T07/T12/T13 only. Initial runs retain
46 pass/two fixture failures and 47 pass/one count-only false-confirmation failure.
The revised candidate passes 52 Python checks, five subsequently added inventory
checks, 12 Node checks, one gameplay-package check and Ruff. Offline fixture
compilation/TypeScript build pass. [Exact evidence and limits](docs/verification/2026-09-20-guardian-tree.md).
G0 remains fail; G1–G5 remain not_run; no full test suite is promoted.

September 19 source checkpoint: [review and environment](docs/STATUS_AND_HANDOFF.md), 738 Python / 166 Node / 445 Java tests, no skips, Ruff pass. The [dispatch child](docs/verification/2026-09-19-inference-dispatch.md) covers local positive/negative reservation, scope, concurrency, unknown-cost and crash cases for partial T01/T04/T07/T12. Complete integration suites and G0–G5 retain their existing results.

September 19 movement addendum: [authentic level walk](docs/verification/2026-09-19-native-movement.md) passes its public checks, 15 private input/save checks and six saved-player checks. Partial T03/T07/T12/T13 evidence only. T07 guardian wait still fails; initial captured terrain is missing, retaining native-render qualification. No aggregate result changes.

September 19 diagnostic addendum: [M0.3b.1b.4.1a](docs/verification/2026-09-19-native-diagnostics.md) passes 12 selected HTTP/JVM cases, package exclusion and 13 authentic E9E private rejection checks. This supplies partial T01/T03/T06/T07/T13 evidence. The same run fails T07 guardian stop timing; aggregate results below remain unchanged.

Latest exact-profile addition: [minor-34 E9E outline trial](docs/verification/2026-09-19-outline-target.md)
adds partial T01/T03/T06/T07/T12/T13 evidence for the separate Forge candidate:
actual startup identity, 2,750/10/6 read-only checks, scoped look/dig/use-cancel/
dedup/fencing, 256 matching before/after saved IDs and reconciled 12 primitives.
The stop protocol passes, but its 503.6561 ms measured wait does not certify a
strict 500 ms wall bound. No aggregate test/gate status changes; full authentic
mechanics, input/privacy, resources/scoring and reliability remain open.

September 19 paired case: authentic mayapple action **fails** with ACTION_UNKNOWN;
128 saved states stay unchanged, while the separate 436.8138 ms stop wait passes.
Repair candidate checks: 439 Java / 42 Node Forge / 41 Python pass; no skips.
[Evidence and limits](docs/verification/2026-09-19-paired-block-reference.md) retain
partial T01/T03/T06/T07/T10/T12/T13 and every aggregate G0–G5 requirement.

September 19 reference delta: [79 synthetic save checks and one compiled-package check](docs/verification/2026-09-19-saved-block-reference.md)
pass; a separate authentic offline comparison matches 128/128 persisted block
IDs. Partial T01/T03/T06/T10/T13 support only; complete authentic scorer controls,
reach/resources/visibility, causal effects and isolation remain open. No aggregate
suite or G0–G5 status changes.

Latest [direct timing checks](docs/verification/2026-09-19-stop-boundaries.md):
33 Python guardian tests pass (30.01 s), including six new failure/timing cases;
Node build and ten selected Node tests pass (36.902 s), zero failures/skips.
Five owned-event kernel waits return timeout after 500.1985–515.3868 ms.
One authentic bounded procedure passes: readiness 209.906 s, CLI subset pass,
normal confirmed stop with 1.2930 ms job call and 489.8473 ms wait, plus saved
pose and PNG decoding. Previous failed stops remain; this is not a repair or
reliability certificate. T01/T03/T06/T07/T12/T13 remain partial; no aggregate gate changes.

Latest [stop diagnostics](docs/verification/2026-09-19-stop-latency.md): Node build
and six actual-process/synthetic-game guarded integrations pass (36.827 s,
zero skips/failures). Five independent disposable resource cases pass the
existing 500 ms wait; their Python monotonic reporting is coarse (15.625 ms
resolution). The authentic QPC observer trial passes its narrow CLI checks,
saved pose and image checks but fails the unchanged 500 ms stop wait. Eventual
exit is separately observed; all prior failures remain fail. Partial
T01/T03/T06/T07/T12/T13 only, no aggregate gate changes.

Latest [readiness checks](docs/verification/2026-09-19-forge-readiness.md): 433 Java
tests and one package-exclusion test pass. On candidate 06f29980… and official
E9E 1.27.0 / Forge 43.4.23 / Java 17.0.20.1, the read-only trial passes
2,745 world / 10 transport / 6 disconnected assertions, ten 500 ms identity
reads, two independently decoded/inspected world images and 359 ms base-guardian
termination. Two authentic worker trials now attach/arm; corrected worker-02 passes its narrow CLI subset but fails timely guardian stop. Eight targeted Node tests and two Python failure-evidence tests also pass.
Partial T01/T03/T06/T07/T12/T13 evidence only; all aggregate results stay open.

Latest [session-lifetime checks](docs/verification/2026-09-19-desktop-worker.md):
14 targeted authentication/dependency tests and one gameplay-package check pass.
Earlier worker baseline: 111 Node pass / 25 skipped; with JVM/Python enabled all
37 Forge fixture tests pass (12 overlap). The first authentic worker attempt
fails before login because its session expires during server setup; two refreshed
sessions join but fail native-read checks. The diagnostic retry retains six
timeouts, 456 accepted HTTP responses and one JVM stack sample. No authentic
action/guardian pass. Partial T01/T03/T06/T07/T12/T13 only; aggregates unchanged.

Latest [private-frame checks](docs/verification/2026-09-19-private-frames.md):
full Java test/build pass, final focused ten tests pass without failures/skips.
Two actual E9E title PNGs pass CRC/zlib/scanline/hash and visual checks; live wrong
screen, no retry, API continuity and guardian stop pass. Initial request mismatch
retained. Partial T01/T03/T06/T07/T12/T13 only; all aggregate gates remain open.

Latest [actual unattended startup](docs/verification/2026-09-19-desktop-client.md):
four disposable JVM tests and package exclusion pass; twenty actual title-screen
API checks pass, with confirmed guardian termination and unchanged input desktop.
Partial T01/T02/T03/T06/T07/T12 only. No frame/world/input/isolation or gate pass.

Latest [launch checks](docs/verification/2026-09-19-desktop-launch.md): twelve
new launch tests and six existing process tests pass; corrected package check
passes its focused rerun. Two 20-frame hidden OpenGL prerequisite probes pass.
Partial T01/T06/T07/T12 only; no authentic body, isolation or aggregate gate pass.

Latest [empty-page checks](docs/verification/2026-09-19-jei-empty-page.md): 405
Java / 330 selected Python / 136 Node pass. Additional partial T01/T03/T06/T07/T12
evidence includes missing-loop negatives and scoped empty-page/Back transitions;
all authentic and aggregate results remain unchanged.

Latest [history checks](docs/verification/2026-09-19-jei-history.md): 395 Java,
329 selected Python and 136 Node pass. These add partial T01/T03/T06/T07/T12
coverage with synthetic game state, real JVM/HTTP/scoped CLI and journals.
Neither T05 physical-key parity nor any aggregate suite/gate is passed.

[JEI navigation evidence](docs/verification/2026-09-19-jei-navigation-motor.md)
adds partial T01/T03/T06/T07/T12 coverage: strict selectors, scoped transport,
page/control authority, bounded charges, cancellation and ambiguous-effect
handling. Final 383 Java tests, 328 selected Python and 135 Node baseline tests
plus documented final targeted checks pass with synthetic game authority.
Aggregate statuses below remain unchanged; all native and release prerequisites
retain their original scope.

September 19 quest opening adds partial T01/T03/T06/T07/T12 evidence: [246 Java / 123 Node / 214 Python pass](docs/verification/2026-09-19-quest-open.md), no final failures/skips. Actual JVM/HTTP/scoped CLI transport uses the real pure motor with synthetic FTB/GUI authority. Exact loaded-pack behavior remains unverified. T03/G0 retain the failed Mineflayer/E9E result; no aggregate status changes.

September 19 Thermal discovery adds partial T01/T03/T06 evidence: 207 Java, 117 Node and 131 Python tests pass, no skips; actual JVM/CLI transport is exercised over synthetic game/JEI effects. [Exact procedures and limits](docs/verification/2026-09-19-thermal-recipes.md). Aggregate T01/T06 remain not_run and T03/G0 retain the actual Mineflayer/E9E failure; the separate Forge profile is still unqualified.

Latest partial T01/T03/T06/T07/T12 checks: [Thermal transaction report](docs/verification/2026-09-19-thermal-transactions.md), 200 Java / 116 Node / 114 Python pass with no skips. One retained intermediate fixture-directory failure was repaired without weakening the path guard. Exact installed bytecode inspection and synthetic journal/transport checks are not real API operation. Aggregate results below remain unchanged, including failed Mineflayer/E9E T03/G0.

September 19 choice controls add partial T01/T03/T06/T07/T12 evidence: [294 Java / 130 Node / 255 Python pass](docs/verification/2026-09-19-quest-choice-controls.md), no final failures/skips. Initial new-test accounting expectation failed and was corrected to preserve the existing charged safety release and uncertain emitted count. JVM/HTTP and scoped CLI exercise choice Back/wheel over synthetic UI authority. Authentic qualification and every aggregate gate remain open.

September 19 task-to-JEI lifecycle adds partial T01/T03/T06/T07/T12 evidence: [304 Java / 131 Node / 262 Python pass](docs/verification/2026-09-19-quest-jei-lifecycle.md), no failures/skips. Actual JVM/HTTP/scoped CLI transports use synthetic game/UI authority. Native compilation and all checks pass; loaded JEI/current-page/reference/isolation gates remain unrun. No aggregate status changes.

September 19 JEI render provenance adds partial T01/T03/T06/T07 evidence: [314 Java pass](docs/verification/2026-09-19-jei-render-capture.md), zero failures/errors/skips, including ten synthetic renderer cases. Installed bytecode and packaged hooks are audited; actual Mixin application/rendering and public page contents remain unrun/unimplemented. Public contract unchanged, so previous Python/Node evidence is retained without rerun. No aggregate status changes.

September 19 header operands add partial T01/T03/T06/T07 evidence: [342 Java / 293 Python / 134 Node pass](docs/verification/2026-09-19-jei-page-headers.md), zero failures/skips. Complete ordered header callbacks, wrong/missing/changed/expired evidence, clipping-before-reader, Unicode bounds/digests and strict scoped transport are exercised with synthetic rendering. Native hooks/Font/viewport/overlays/reference/isolation remain unrun. No aggregate status changes.

September 19 copied-page transport adds partial T01/T03/T06/T07 evidence: [333 Java / 285 Python / 134 Node pass](docs/verification/2026-09-19-jei-page-transport.md), plus the final strict-role targeted transport check. Actual JVM/scoped CLI with synthetic game/render authority; malformed schemas/content, raw fields, bounds, body replacement, stop and unsupported stock-backend cases reject. Authentic page visibility/input/reference/isolation gates remain unrun; no aggregate status changes.

September 19 immutable slot copies add partial T01/T03/T06/T07 evidence: [326 Java pass](docs/verification/2026-09-19-jei-slot-copies.md), zero failures/errors/skips. Twelve new synthetic draw/copy/geometry/completeness cases; native hooks compiled and exact installed bytecode audited. Actual Mixin/renderer/visibility/overhead and public current-page transport remain unqualified/unimplemented. Public contract unchanged; prior Python/Node results retained. No aggregate status changes.

Record each test attempt in the progress log or linked report with its exact profile, procedure, date, raw evidence and limitations. Partial execution does not pass the aggregate suite. Keep different N/pack/backend/model profiles separate; a successful synthetic test does not pass its real-game equivalent.

| Test | Owner | Scope (full acceptance is SPEC section 16) | Result | Profile / evidence / outstanding work |
|---|---|---|---|---|
| T01 | PL | Strict contracts, schemas, config, auth, paths and negative cases | not_run | All 13 canonical examples/schema checks pass in Python/TypeScript with negative cases; full cross-record references, migrations and runtime bindings remain incomplete. [Core evidence](docs/verification/2026-09-18-controller-evaluator.md). September 19 [live native read-only/auth/session/schema negatives and provider regression](docs/verification/2026-09-19-forge-live-api.md) add partial evidence only. September 19 [movement contracts](docs/verification/2026-09-19-forge-movement.md) add strict 30-second envelopes, finite tolerance and identical eleven-action policy negotiation across Java/TypeScript/Python; full suite remains incomplete. September 19 [crafting evidence](docs/verification/2026-09-19-forge-crafting.md): twelve-action/recipe policy negotiation and strict bounded recipe pages pass synthetic Java/Node/Python checks; original aggregate result unchanged. D07 [menu-close evidence](docs/verification/2026-09-19-menu-close.md) adds strict close-window schema/field/duration checks and thirteen-action capability negotiation; 153 Java / 107 Node / 95 selected Python pass with synthetic game effects. [Body-revision evidence](docs/verification/2026-09-19-body-revision.md) fixes idle heartbeat invalidation and adds authentic scoped CLI acceptance/actual-turn/age negatives; full native host and body-transition conformance stay open. D08 [JEI query evidence](docs/verification/2026-09-19-jei-query.md) adds bounded focused discovery, strict scoped/body-bound transport and exact dependency/policy pins; native effects/isolation remain unverified, with no gate change. D09 [manual-craft evidence](docs/verification/2026-09-19-manual-craft.md) adds explicit source selection, ordinary confirmed grid filling and retained partial-effect charges; synthetic checks pass, authentic scope remains open.  [Connected E9E evidence](docs/verification/2026-09-19-forge-connected.md) adds exact-pack read-only decoding and transport negatives; no complete contract or OS-isolation pass.  M0.1c.2b.2e adds [authenticated native request admission](docs/verification/2026-09-20-native-ingress.md), with source/native synthetic evidence; OAuth transport and complete isolation remain unqualified.  M0.1c.2b.2f adds [native OAuth transport candidate evidence](docs/verification/2026-09-20-native-oauth-transport.md); fabricated authentication does not qualify live TLS/account/usage.  [First OAuth trial/diagnostic/catalog evidence](docs/verification/2026-09-20-native-oauth-conformance.md): one unresolved request, $0.7554 hold; source checks and native metadata evidence do not close this row.  M0.2c.3 [private telemetry authentication](docs/verification/2026-09-20-authenticated-telemetry.md) adds source/synthetic byte/boot binding; no authentic score or aggregate gate pass.  M0.2c.3b.1 [sealed craft-reference source/synthetic evidence](docs/verification/2026-09-20-craft-reference-seal.md) verifies preserved bytes and the registered source/resource join; no protected score or aggregate gate pass. |
| T02 | GI | Official clean provisioning, locked inventory, expert mode and blocked acquisition | not_run | Official profiles/bootstrap, vanilla boot/stop, E9E cold restart and instrumented runtime expert furnace assertions have partial evidence. Five effective-file findings, transitive provenance, sealed role inventory, quest/team/player/reference assertions remain unresolved. [Earlier evidence](docs/verification/2026-09-18-long-horizon.md); [selected loaded-config follow-up](docs/verification/2026-09-20-e9e-loaded-config.md) adds a two-boot point-observation comparison while retaining all five file failures. |
| T03 | GI | Structured vanilla and exact Forge/registry/recipe/machine actions; optional input parity separately | fail | [Vanilla mechanics](docs/verification/2026-09-20-vanilla-mechanics.md) now pass narrowly with saved mining, walking, chest, planks/sticks and Damage=0 pickaxe deltas. Preserve earlier [vanilla menu](docs/verification/2026-09-19-vanilla-menu.md) and [body revision](docs/verification/2026-09-19-body-revision.md) cases. Exact E9E Mineflayer handshake still fails. The separate D06 Forge backend has partial [connected](docs/verification/2026-09-19-forge-connected.md), movement/cancellation/quest and [machine processing/collection](docs/verification/2026-09-20-machine-crafting.md) evidence; [Earlier EMI/craft failures](docs/verification/2026-09-20-emi-crafting.md) remain retained; the selected expert furnace craft now has [authentic consumption/resource evidence](docs/verification/2026-09-20-craft-witness.md). Full geometry, metadata/custom serializers, placement/equipment/use, reliable recovery, broader machine/container/quest operations, filtering/isolation and optional rendered parity remain incomplete. Selected [Forge cancellation/restart](docs/verification/2026-09-20-forge-reconnect.md) preserves state/receipts/costs but fails shutdown. All original negative cases and failures remain in their reports/child rows.  Latest [vanilla cancel/reconnect](docs/verification/2026-09-20-vanilla-reconnect.md) has a passing narrow independent audit with all raw checker failures retained; complete profile/gate coverage remains open. |
| T04 | AR | Native host/plugin/structured tools/helpers/accounting/interruption/resume; optional images | not_run | Actual pinned native Dovetail installation and Windows process-tree fixtures; durable runner/raw-usage/helper/interrupt tests use synthetic model streams. Model invocation, actual helpers/isolation/all-call accounting remain open. [Latest evidence](docs/verification/2026-09-18-long-horizon.md). [Body-revision evidence](docs/verification/2026-09-19-body-revision.md) fixes idle heartbeat invalidation and adds authentic scoped CLI acceptance/actual-turn/age negatives; full native host and body-transition conformance stay open. M0.1c.2b.2d adds [sealed bootstrap/source integrity evidence](docs/verification/2026-09-20-native-bootstrap.md), including native root/helper canaries; aggregate qualification remains incomplete.  M0.1c.2b.2e adds [authenticated native request admission](docs/verification/2026-09-20-native-ingress.md), with source/native synthetic evidence; OAuth transport and complete isolation remain unqualified.  M0.1c.2b.2f adds [native OAuth transport candidate evidence](docs/verification/2026-09-20-native-oauth-transport.md); fabricated authentication does not qualify live TLS/account/usage.  [First OAuth trial/diagnostic/catalog evidence](docs/verification/2026-09-20-native-oauth-conformance.md): one unresolved request, $0.7554 hold; source checks and native metadata evidence do not close this row. |
| T05 | GI | Stock-Mineflayer rejection plus full real keybinding-extension effects/restart/rollback/isolation cases | not_run | Exact client exported 253 bindings with sampled Controls UI correspondence. Prior JVM/HTTP transport/restart/lost-ack tests use synthetic runtime. September 20 [authentic encoding round trip/cold readback](docs/verification/2026-09-20-native-settings.md) and [pending transaction termination/recovery](docs/verification/2026-09-20-native-settings-recovery.md) now pass narrowly: source-bound Curios, preserved unrelated bytes, all 253 restored mappings, status before rollback and zero replay. [Authentic disk-conflict negatives](docs/verification/2026-09-20-native-settings-conflicts.md) also pass with one prepared transaction and exact restoration. Intended/competing effects, mid-write/in-memory-foreign cases, qualified CAS/isolation, physical pool and gameplay repair/accounting remain open. Controls invalid-scancode GL finding retained; shared input remains paused. [Original discovery](docs/verification/2026-09-18-long-horizon.md), [shared artifact-path fix](docs/verification/2026-09-19-forge-live-api.md). |
| T06 | SI | Private/cross-agent/helper/filesystem/process/network/tool/holdout leaks | not_run | Synthetic scoped grants/CAS canaries/paths/probe-origin/messages and allowlisted client package checks pass. September 19 live bridge rejects unauthorized/browser-origin/foreign-host requests; these [limited transport checks](docs/verification/2026-09-19-forge-live-api.md) do not prove OS/process/network/helper or sealed-probe isolation, which remains unrun. [Core evidence](docs/verification/2026-09-18-controller-evaluator.md). September 19 [crafting evidence](docs/verification/2026-09-19-forge-crafting.md) rejects private/extra recipe response fields and body-generation drift in synthetic transport; actual book filtering and OS boundaries remain unverified. D08 [JEI query evidence](docs/verification/2026-09-19-jei-query.md) adds bounded focused discovery, strict scoped/body-bound transport and exact dependency/policy pins; native effects/isolation remain unverified, with no gate change. D09 [manual-craft evidence](docs/verification/2026-09-19-manual-craft.md) adds explicit source selection, ordinary confirmed grid filling and retained partial-effect charges; synthetic checks pass, authentic scope remains open.  [Connected E9E evidence](docs/verification/2026-09-19-forge-connected.md) adds exact-pack read-only decoding and transport negatives; no complete contract or OS-isolation pass. M0.1c.2b.2d adds [sealed bootstrap/source integrity evidence](docs/verification/2026-09-20-native-bootstrap.md), including native root/helper canaries; aggregate qualification remains incomplete.  M0.1c.2b.2e adds [authenticated native request admission](docs/verification/2026-09-20-native-ingress.md), with source/native synthetic evidence; OAuth transport and complete isolation remain unqualified.  M0.1c.2b.2f adds [native OAuth transport candidate evidence](docs/verification/2026-09-20-native-oauth-transport.md); fabricated authentication does not qualify live TLS/account/usage.  [First OAuth trial/diagnostic/catalog evidence](docs/verification/2026-09-20-native-oauth-conformance.md): one unresolved request, $0.7554 hold; source checks and native metadata evidence do not close this row.  M0.2c.3 [private telemetry authentication](docs/verification/2026-09-20-authenticated-telemetry.md) adds source/synthetic byte/boot binding; no authentic score or aggregate gate pass.  M0.2c.3b.1 [sealed craft-reference source/synthetic evidence](docs/verification/2026-09-20-craft-reference-seal.md) verifies preserved bytes and the registered source/resource join; no protected score or aggregate gate pass. |
| T07 | QA | Ack/lease/process/server/controller/disk/credential/snapshot faults and recovery | fail | Prior repair/vanilla cancellation (20.7 ms), native journal, release and guard foundation evidence retained. .2c.3b: **95 Node / 51 Python**, then final **20 Forge** checks pass; synthetic native freeze/worker kill/worker hang/parent kill stop the JVM in **1466/45/1922/31 ms**, with one native intent/no replay. Wrong grants/owners reject and normal shutdown retains hashed private evidence. Actual Minecraft timings/restore, controller authority, coordinated exhaustion/recovery and isolation remain open. [Prior](docs/verification/2026-09-18-long-horizon.md), [native](docs/verification/2026-09-18-forge-game-actions.md), [release](docs/verification/2026-09-18-worker-release.md), [routing](docs/verification/2026-09-18-forge-worker.md), [guard foundation](docs/verification/2026-09-18-process-guard.md), [guard integration](docs/verification/2026-09-18-forge-guard-integration.md). September 19 [movement lane evidence](docs/verification/2026-09-19-forge-movement.md) adds charged cancellation/deadline/damage/exhaustion on a synthetic walking body; latest 21 Forge tests retain guarded JVM fault stops at 492/42/1738/25 ms. These are not Minecraft timing results. September 19 [crafting evidence](docs/verification/2026-09-19-forge-crafting.md) adds crafting partial-effect/no-replay cases; 23 Forge tests pass, with disposable JVM stop times 511/45/1741/24 ms. Authentic timing/recovery remains open. D07 [menu-close evidence](docs/verification/2026-09-19-menu-close.md) adds menu-close cancellation/deadline/exhaustion without replay; disposable JVM freeze/worker-kill/worker-hang/parent-kill stops were 505/42/1731/24 ms. These are not Minecraft timing results. [Authentic vanilla menu evidence](docs/verification/2026-09-19-vanilla-menu.md) adds player-menu cursor/grid returns, duplicate handling, retained pre-acceptance schema/revision rejections, 24 total charged primitives and final saved inventory; complete profile/reference/accounting gates remain open. [Body-revision evidence](docs/verification/2026-09-19-body-revision.md) fixes idle heartbeat invalidation and adds authentic scoped CLI acceptance/actual-turn/age negatives; full native host and body-transition conformance stay open. D09 [manual-craft evidence](docs/verification/2026-09-19-manual-craft.md) adds explicit source selection, ordinary confirmed grid filling and retained partial-effect charges; synthetic checks pass, authentic scope remains open. Latest current-policy [authentic guardian trial](docs/verification/2026-09-20-guardian-live.md) fails its 500 ms root wait at 510.8433 ms; no tree proof or stop receipt. Remaining T07 cases are still incomplete; this explicit failed required case changes the aggregate from not_run to fail.  M0.1c.2b.2e adds [authenticated native request admission](docs/verification/2026-09-20-native-ingress.md), with source/native synthetic evidence; OAuth transport and complete isolation remain unqualified.  M0.1c.2b.2f adds [native OAuth transport candidate evidence](docs/verification/2026-09-20-native-oauth-transport.md); fabricated authentication does not qualify live TLS/account/usage.  [First OAuth trial/diagnostic/catalog evidence](docs/verification/2026-09-20-native-oauth-conformance.md): one unresolved request, $0.7554 hold; source checks and native metadata evidence do not close this row.  M0.2c.3 [private telemetry authentication](docs/verification/2026-09-20-authenticated-telemetry.md) adds source/synthetic byte/boot binding; no authentic score or aggregate gate pass.  M0.2c.3b.1 [sealed craft-reference source/synthetic evidence](docs/verification/2026-09-20-craft-reference-seal.md) verifies preserved bytes and the registered source/resource join; no protected score or aggregate gate pass. |
| T08 | QA | Ordered 1-hour, 8-hour, 24-hour operating-envelope soaks | not_run | — |
| T09 | PL | N=1/2/4 simultaneous capacity, whole-team rejection, shared and independent topology | not_run | Synthetic atomic N=2/4 capacity/account tests and N=10,000 whole-team queue without body allocation pass. No measured simultaneous N=1/2/4 certificate. [Core evidence](docs/verification/2026-09-18-controller-evaluator.md). |
| T10 | RS | Reachability, scorer positive/negative controls and alternative strategies | not_run | Synthetic registered craft/machine positive/negative/alternate/duplicate/sustained-window cases pass. Raw Forge recipe/tick evidence cannot score; authoritative consumption/machine provenance, identity, reference reachability and mechanics parity remain open. [Latest evidence](docs/verification/2026-09-18-long-horizon.md).  M0.2c.3 [private telemetry authentication](docs/verification/2026-09-20-authenticated-telemetry.md) adds source/synthetic byte/boot binding; no authentic score or aggregate gate pass.  M0.2c.3b.1 [sealed craft-reference source/synthetic evidence](docs/verification/2026-09-20-craft-reference-seal.md) verifies preserved bytes and the registered source/resource join; no protected score or aggregate gate pass. |
| T11 | RS | Matched clones, probe disposal/non-feedback, exact ablation state | not_run | Synthetic clone-manifest equality, exact episode projections and probe-origin import rejection pass. Actual fresh process/world clones, disposal and canary feedback tests open. [Core evidence](docs/verification/2026-09-18-controller-evaluator.md). |
| T12 | PL | All nested usage, dedup/retries/reservations and reconciled clocks/caps | not_run | Synthetic hierarchical reserves/settles, ancestry/retries/races/unknown/overrun and repair interval tests pass. .2c.1 adds native attempted-event/safety-release reconciliation across broker epochs and preserved page capture age; these are local counters, not complete BudgetLedger settlement or clock qualification. Provider all-call and measured real-time reconciliation remain open. [Core evidence](docs/verification/2026-09-18-controller-evaluator.md), [repair evidence](docs/verification/2026-09-18-long-horizon.md), [broker evidence](docs/verification/2026-09-18-forge-worker.md). September 19 [movement accounting](docs/verification/2026-09-19-forge-movement.md) charges active neutral/coasting/walking decisions and final release, including exhaustion with retained usage; aggregate/model/clock qualification is unchanged. September 19 [crafting evidence](docs/verification/2026-09-19-forge-crafting.md) charges recipe fills, refreshes, waits and output/remainder clicks; synthetic lane exhaustion preserves consumption and partial state. D07 [menu-close evidence](docs/verification/2026-09-19-menu-close.md) verifies charged close/refresh/active waits and preserved partial effects, without qualifying complete aggregate or provider accounting. [Authentic vanilla menu evidence](docs/verification/2026-09-19-vanilla-menu.md) adds player-menu cursor/grid returns, duplicate handling, retained pre-acceptance schema/revision rejections, 24 total charged primitives and final saved inventory; complete profile/reference/accounting gates remain open.  M0.1c.2b.2e adds [authenticated native request admission](docs/verification/2026-09-20-native-ingress.md), with source/native synthetic evidence; OAuth transport and complete isolation remain unqualified.  M0.1c.2b.2f adds [native OAuth transport candidate evidence](docs/verification/2026-09-20-native-oauth-transport.md); fabricated authentication does not qualify live TLS/account/usage.  [First OAuth trial/diagnostic/catalog evidence](docs/verification/2026-09-20-native-oauth-conformance.md): one unresolved request, $0.7554 hold; source checks and native metadata evidence do not close this row. |
| T13 | RS | Deterministic report/accounting reconstruction, retention and safe export | not_run | Synthetic deterministic outbox/report replay, CAS hashes, safe report/client export and cross-language canonical hashing pass. Complete evidence reconstruction, retention/tombstones and live replay open. [Core evidence](docs/verification/2026-09-18-controller-evaluator.md).  M0.2c.3 [private telemetry authentication](docs/verification/2026-09-20-authenticated-telemetry.md) adds source/synthetic byte/boot binding; no authentic score or aggregate gate pass.  M0.2c.3b.1 [sealed craft-reference source/synthetic evidence](docs/verification/2026-09-20-craft-reference-seal.md) verifies preserved bytes and the registered source/resource join; no protected score or aggregate gate pass. |
| T14 | RS | Model/reroute/runtime drift, quarantine and unavailable identity | not_run | Synthetic identity/drift boundary decisions and unverified-identity report qualification pass; actual supervisor stop/grant revocation/fresh cohort/anchor integration open. [Core evidence](docs/verification/2026-09-18-controller-evaluator.md). |
| T15 | RS | Preregistered confirmatory pilot, all assignments/attrition and honest inference | not_run | — |
| T16 | RS | Calibration/graduation/history/retention/ceiling/prerequisite decisions | not_run | Deferred to M6; no promotion claims. |
| T17 | GI | Each later pack/backend/quest/save module separately conformant | not_run | Deferred to M6; no legacy support claims. |

| Gate | Required milestone/evidence | Result | Profile / evidence / remaining condition |
|---|---|---|---|
| G0 | M0; all six SPEC 16.1 vertical-slice items together | fail | Selected vanilla and separate Forge mechanics, expert furnace resource witness and restart/journal continuity have authentic evidence. Reliable shutdown still fails (pair04 phase2 508.2221/500 ms); D11 live ingress/isolation, complete locks/config roles, authoritative scorer controls and joined costs remain open. Mineflayer/E9E negotiation and earlier craft failures remain retained. [Craft witness](docs/verification/2026-09-20-craft-witness.md), [restart](docs/verification/2026-09-20-forge-reconnect.md), [six-item checklist](#m0-closure-checklist--spec-161).  [First OAuth trial/diagnostic/catalog evidence](docs/verification/2026-09-20-native-oauth-conformance.md): one unresolved request, $0.7554 hold; source checks and native metadata evidence do not close this row.  M0.2c.3 [private telemetry authentication](docs/verification/2026-09-20-authenticated-telemetry.md) adds source/synthetic byte/boot binding; no authentic score or aggregate gate pass. |
| G1 | G0; complete T01/T04/T05/T06/T10/T11 including settings extension | not_run | Partial synthetic contract and actual client-discovery evidence exist. Complete native-host, settings-effect, isolation, scorer and probe gates remain open. |
| G2 | G1; T07/T08/T12/T13 at N=1 | not_run | No durable single-agent/24-hour proof. |
| G3 | G2; T09, actual N=2, explicit N=4 disposition, N=2 soak/security | not_run | No simultaneous capacity certificate. |
| G4 | G3; development cost/power pilot, T14, locked protocol and T15 | not_run | No research MVP or scientific result. |
| G5 | G4; T16/T17 per new target | not_run | Later packs and graduation unverified. |

September 19 quest/cancel addendum: [three authentic attempts](docs/verification/2026-09-19-native-quest-cancel.md) retain the CTM startup crash and stale-catalog harness failure. Nineteen focused Java tests pass; corrected trial passes basic quest lifecycle and public cancellation/fencing, with six intents/39 primitives and 256 independent saved IDs reconciled. The stopped-position cancellation predicate fails because the body is already within target tolerance; guardian shutdown also fails at the unchanged 500 ms bound. This is partial T01/T03/T06/T07/T12/T13 evidence, not a complete suite or gate pass. No runtime/affordance, budget, isolation or scientific-comparison policy changed.

September 19 route-cancel addendum: [fresh bounded trial](docs/verification/2026-09-19-native-cancel.md) passes cancellation before arrival during initial centering, eight saved-player/thirteen reference checks and 256 IDs, with one intent/20 primitives reconciled. Guardian wait signals at 451.9577 ms; previous failures remain. The 359 ms CLI timing does not certify the separate 250 ms worker target. First unavailable-target and second unexecuted cases are retained. Partial T01/T03/T07/T12/T13 only; aggregate suites and G0–G5 remain open.

September 19 native-budget addendum: [exact CLI/schema and two local provider probes](docs/verification/2026-09-19-native-budget.md) cover synthetic rejection/retry transport with no paid model or credentials. Turn-start and actual requests lack an output-token bound; no authenticated monetary/call-exposure proof exists. T04/T12 remain incomplete; no all-call gateway qualification or live host admission.

## Blockers, open decisions, and change history

**Private participant coordination, 2026-09-20:** GI/PL/QA own .3b.3b.1. SPEC v0.2.72 declares `PrivateReferenceLaunch/2` with a finite 1–420-second external-client window inside the existing 600-second server exposure. SPEC v0.2.73 requires explicit `PrivateReferenceClientBinding/1` for production E9E participant admission after the actual stale-body failure. Scope/endpoint/team/module/fixture/exposure consistency and held-pin rechecks are source-verified; historical records remain readable without retroactive upgrade. These are integration facilities, not allowance increases, guardian relaxations, authenticated successful client execution or scorer authorization. Failed completion remains uncertain and unreplayed; full setup ownership and authentic craft controls remain open. [Evidence](docs/verification/2026-09-20-reference-client-binding.md).

**Private abort coordination, 2026-09-20:** SPEC v0.2.74 adds explicit `PrivateReferenceLaunch/3` operator control; v1/v2 histories, participant registration, 600-second server/120-second graceful-stop limits and 500-ms guardian remain unchanged. The 500–15000-ms cooperative abort interval is bounded by existing deadlines and never converts uncertainty into qualification. Component .3b.3b.3a has source/owned-process evidence; durable outer integration .3b remains required. No gameplay capability, experiment allowance or acceptance threshold changed. [Evidence](docs/verification/2026-09-20-reference-abort.md).

**Durable private pair monitoring, 2026-09-21:** SPEC v0.2.75 declares `PrivateReferencePair/1`, held declared pins, one-use durable outer intent, exact recorded readiness and independent finite outer deadlines. Nonterminal/uncertain pairs now prevent craft import even if the inner server stopped. This adds operator coordination without gameplay capability, budget or threshold changes. [Implementation and bounded evidence](docs/verification/2026-09-20-reference-pair.md); authentic Forge integration remains open.

**D11 — initial validation budget clarified, 2026-09-20:** the user confirms no outside Strata model experiments and explains that $10 means a rough model-price estimate of subscription usage. Preserve D04's original aggregate allowance and selected OAuth/Luna identity; no increase/reset. Stop requiring a complete external OAuth-dollar billing proof as the meaning of this initial allowance. Record actual tokens and clearly labeled API-equivalent estimates, conservatively reserving unresolved exposure. The explicit versioned migration is now recorded in the [D11 implementation report](docs/verification/2026-09-20-estimated-accounting.md); live ingress/boundary qualification remains required. Official sources fetched today give Luna standard short-context rates $0.20/M input, $0.02/M cached input and $1.20/M output, with separate cache-write, long-context and service-tier rates. Sources: [model](https://developers.openai.com/api/docs/models/gpt-5.6-luna), [API prices](https://developers.openai.com/api/docs/pricing), [subscription credit semantics](https://learn.chatgpt.com/docs/pricing). A $1 estimated first trial within the $10 total is the engineering recommendation, not an additional allowance. The user's isolation question is not a waiver of F04/N04/T06. The agent owns designing/testing the minimum enforceable boundary; a user-provided VM is not an independent acceptance requirement.

**Native collaboration/storage, 2026-09-20:** AR/PL/SI own M0.1c.2c.
Observed v2 tools support actual clean/full forks, but the pinned ephemeral
parent cannot support full-history lookup. SPEC v0.2.37 declares storage mode
as part of runtime identity and preserves the default; a changed mode invalidates
old qualification. All-call aggregation now has native child evidence, whereas
child-specific budgets/permissions and full lifecycle remain unqualified. Native
metadata is not an authenticated admission channel. No D04 allowance, live
dispatch, shared-desktop input or model policy changes are authorized by this
implementation; the existing monetary/isolation blockers remain.

**Owned-member proof, 2026-09-20:** GI/QA own child
M0.3b.2c.3c.2b.2b.2.2. A real fixture disproves zero-job-accounting as complete
process exit proof. SPEC v0.2.36 requires complete signaled member handles plus
zero active accounting at the unchanged 500 ms bound. The bounded implementation
passes fixtures but must fail on incomplete observation or more than 256 lifetime
members; real workload suitability remains unqualified. Previous native crash
13-to-zero counts retain their narrow accounting meaning. Next strengthen that
fixture's recovery fence, then qualify authentic guardian behavior; all previous
stop failures remain. This implementation choice grants no new live/model/input
authorization and removes no acceptance requirement.

**Native accounting continuation, 2026-09-20:** AR/PL/SI own M0.1c.1c.
The user explicitly resumed the full M0–M6 objective beyond merged PR #1;
the former checkpoint stopping point is superseded, not a scope reduction.
SPEC v0.2.34 records nested reservation composition within the existing D04
ceiling, with no new budget or authentication authorization. A read-only audit
of known external roots found no live inference accounting profile; the $0
handoff report is retained but is not silently converted into a fresh allowance.
Actual account USD-per-credit evidence was requested asynchronously; live
OAuth dispatch remains blocked by monetary conversion, finite exposure,
complete spending authority and credential/process/network isolation.
Independent credential-free implementation continues. Eight native synthetic
cases do not close these blockers or the full T04/T07/T12/G0/G1 gates.

**Rendered-client stop confirmation, 2026-09-19:** GI/QA own the open
`PROCESS_STOP_UNCONFIRMED` gate under M0.3b.2c.3c.2b.2b.2, F09/N05,
T07/T08/G2. Corrected worker-02 passes the bounded CLI subset and drains its
executor normally, but the independent guardian cannot confirm Java exit within
the unchanged 500 ms wait. It later exits and is confirmed absent; that is not a
timely-stop pass. The previous worker's unconfirmed stop has no retained inner
cause. [Evidence](docs/verification/2026-09-19-forge-readiness.md) retains both
failures and full charges. Next: instrument the owned stop/exit path to distinguish
OS/job/render-thread teardown latency, preserve limits, and rerun appropriate
normal/hung-client cases. Same-user desktop separation does not close isolation.
Other mechanic/reference work remains independently authorized; no new approval
or inference spend is implied.

Diagnostic continuation: five disposable heap/render stop cases pass at the
unchanged bound. Their one-sample-per-condition resource trend does not identify
the real failure cause. A private stop-intent marker and read-only QPC observer
show resource release and eventual exit in a fresh authentic failure;
[diagnostic evidence](docs/verification/2026-09-19-stop-latency.md) retains clock
resolution, process identity and observation limitations. Next: precise timing
at the existing job-call/wait boundaries. GI/QA still own repeated normal/hung-client
qualification before admission.

Direct-boundary continuation: [instrumented trial](docs/verification/2026-09-19-stop-boundaries.md)
now passes its bounded worker/API/normal-stop procedure, with job call 1.2930 ms
and process wait 489.8473 ms under the unchanged 500 ms bound. This one passing
sample does not repair the earlier failures or qualify reliable stop. The
resource/OS cause and representative normal/hung-client timing remain open;
GI/QA own direct failure capture and independent mechanic/reference work.

**Initial synchronization readiness, 2026-09-19:** two refreshed-session worker
trials reach authenticated E9E, but their native identity reads do not complete.
In the diagnostic run, six five-second probes receive 456 accepted HTTP replies;
one stack sample finds block-cache rebuilding inside server tag-update handling.
The first-render barrier is insufficient for admitting the worker before that
initialization. GI/QA own source/event-order audit and .2b.2b.1 readiness repair,
then .2b.2b.2 live actions. Keep deadlines, failures, resource accounting and
all authenticity gates. Earlier successful world imagery remains narrow evidence,
not a full startup/worker qualification.

**Native startup session lifetime, 2026-09-19:** SPEC v0.2.29 records sufficient
session lifetime for setup/run and immediate prelaunch recheck. The first worker
trial prepared a token with 88.480 seconds remaining; it expired 50.928 seconds
before the client launched. Profile-key failures and later HTTP 401 are retained.
M0.2g.1 adds an optional cache-view filter/returned-expiry check without deleting
Microsoft/Xbox caches or changing ordinary vanilla authentication. GI/SI/QA own
the fresh-session authentic check and remaining credential-recovery/isolation
gates. D05/D06 and existing account authorization apply; no new login, gameplay
affordance, paid inference or relaxed acceptance threshold is implied.

**Private frame evidence, 2026-09-19:** SPEC v0.2.28 records the optional
operator-only capture policy and versioned private files. This is implementation
of the already-authorized unattended verification path, not a new gameplay image
affordance or physical-key waiver. E9E PackMenu's exact ExtendedMenuScreen class
is source-verified; an initial vanilla-class mismatch remains a failed attempt.
Full GUI/world/reference/GL-state-failure/overhead/security work remains .2b.2,
owned by GI/SI/QA. [Evidence](docs/verification/2026-09-19-private-frames.md).

**Guarded installed bootstrap, 2026-09-19:** SPEC v0.2.27 records the direct
operator JVM startup from exact installed official metadata/artifacts, separately
labeled from the official launcher UI. D05 and the user's desktop-availability
constraint authorize this dedicated-copy test; no replacement acquisition or
gameplay affordance. Real title startup/lifetime passes under .2c.3c.2a. Full
frames/worker/security remain .2b, owned by SI/GI/QA. A base vanilla-client JAR
digest mismatch was found and preserved; the Forge profile's matching official
client JAR was used. Resolve the base-file provenance before its client lock can
seal. [Evidence](docs/verification/2026-09-19-desktop-client.md).

**Unattended launch foundation, 2026-09-19:** SPEC v0.2.26 records
windows-noninput-desktop-suspended-job/1, a same-account operator launch primitive
with no desktop switching/input injection. Actual disposable process/graphics
evidence shows feasibility on this machine, not adversarial isolation, physical
key parity or Minecraft conformance. Production integration remains .2c.3c.2,
owned by SI/GI/QA. No new gameplay affordance, account authority, campaign
admission or gate waiver. [Evidence](docs/verification/2026-09-19-desktop-launch.md).

**Shared-desktop availability, 2026-09-19:** the user cannot use their computer
during lengthy computer-use sessions. Keep desktop input paused and prioritize
API/state/server-evidence verification. Long graphical/physical-input tests need
an isolated graphical session; short shared-desktop checks require an arranged
window. Current native capabilities advertise screenshots:false; no qualified
private framebuffer capture or unattended launch/render/input path exists yet.
Native menu callbacks retain pointer-restoration behavior, so background safety
must be demonstrated, not inferred from an API call. GI/SI/QA own .2c.3c/.1b.4
and M1.1 resolution. This changes the work process, not required T03/T05 gates.

**D06 empty-loop page evidence, 2026-09-19:** SPEC v0.2.25 / Forge minor 33 /
NativeRecipePage/4 / jei-task-drawn-slot-header-controls-empty-loop/4 permit zero
copied layouts only with an observed complete ordinary loop and headers/controls.
Every predicate invokes the original once; each positive result pairs with one
completed draw, followed by false and normal return. No private list reads or
extra iteration. Action count/charges and all rich/custom/native gates remain.
GI/SI/QA own authentic qualification. [Evidence](docs/verification/2026-09-19-jei-empty-page.md).

**D06 ordinary history Back, 2026-09-19:** SPEC v0.2.24 / Forge minor 32 extend
recipe_navigate with history_back under jei-current-page-controls-history-fresh-frame200/2.
The audited concrete RecipesGui.back public callback is used directly; it is not
an IRecipesGui method or simulated keypress. Empty history keeps the screen open.
Current-page/origin guards, three-unit admission, charged fresh-frame waits and
uncertain-effect/no-replay handling preserve the existing contract. Physical
hotkey, rich/custom/empty-page and native qualification remain required; no scope
or gate waiver. GI/QA own exact-pack qualification. [Evidence](docs/verification/2026-09-19-jei-history.md).

**D06 bounded JEI navigation, 2026-09-19:** SPEC v0.2.23 / Forge minor 31 add recipe_navigate and jei-current-page-preview-execute-fresh-frame200/1 within the already required ordinary page/category controls. Native nineteen-action identity supersedes the earlier eighteen-action candidate; prior deployed/client evidence remains separate. Strict source/screen/page/control authority, observed ordinary router/button provenance, two input phases, fresh frames, four-unit admission, charged waits and non-executing cleanup are implemented but unverified in-game. No private logic, changed threshold, campaign admission or waiver; history/rich/custom/native/isolation gates remain. GI/PL/QA own exact-pack qualification. [Evidence](docs/verification/2026-09-19-jei-navigation-motor.md).

**D06 navigation-control observation, 2026-09-19:** SPEC v0.2.22 / Forge minor 30 / NativeRecipePage/3 / jei-task-drawn-slot-header-controls/3 add four actual ordered button draw states to the same incomplete page. Viewport filtering precedes flag reads, copied objects/geometry remain private, and strict frame/source/body/digest/lease checks remain. No new action kind or navigation authority. Installed ordinary input uses SIMULATE on mouse-down and EXECUTE on mouse-up; the motor and history routes remain .3b/.3c. GI/SI/QA own native qualification. [Evidence](docs/verification/2026-09-19-jei-page-controls.md).

**Desktop handoff resolved, 2026-09-19:** the user reports completing and allowing the Windows Security prompt; a fresh E9E capture confirms its absence. Existing desktop authorization applies. The previous read-only client was closed, its JAR backed up and the tested minor-30 candidate deployed for live testing. No security-dialog automation, action authority or inference was enabled. Prior prompt observations below remain historical.

**D06 header-draw extension, 2026-09-19:** SPEC v0.2.21 / Forge minor 29 / native NativeRecipePage/2 / jei-task-drawn-slot-and-header-copies/2 supersede the slot-only page identity. Two actual bounded header operands, category then page, share complete-frame/source/body/digest/lease checks; clipped/unsupported markers have null text. No full-title/private-field/count/graph lookup. Keep explicit incomplete coverage, eighteen actions and all rich/custom/overlay/control/native gates. GI/SI/QA own qualification. [Evidence](docs/verification/2026-09-19-jei-page-headers.md).

**D06 copied-page transport, 2026-09-19:** SPEC v0.2.20 / Forge minor 28 adds no-argument recipes.page/native recipe_page under jei-task-drawn-slot-copies/1, explicitly incomplete slot_draw_operands coverage. Canonical digest, full-envelope bounds, origin/source/body/lease checks and private-metadata stripping are implemented with synthetic evidence. This supersedes the prior absence of public transport without claiming complete page content or authentic conformance. Eighteen actions unchanged; GI/PL/SI/QA retain remaining content/input/isolation work. [Evidence](docs/verification/2026-09-19-jei-page-transport.md).

**D06 immutable slot-copy foundation, 2026-09-19:** SPEC v0.2.19 records ordinary slot-selection/draw-operand hooks, private immutable records and 128-slot/32-layout/32-KiB bounds. Distinguish observed empty slots from missing instrumentation, filter geometry before content, and never inspect alternatives/raw components. Exact native wrappers, tagged/custom representations, final overlay visibility and actual hook semantics remain qualification concerns; unsupported markers do not waive their scope. Public Forge minor 27 and eighteen actions unchanged; page transport remains required .1b.2c. GI/SI/QA own remaining visibility/native/isolation work. [Evidence](docs/verification/2026-09-19-jei-slot-copies.md).

**D06 render-provenance foundation, 2026-09-19:** SPEC v0.2.18 records the optional exact-JEI draw-call hook and complete-frame source. The native call's receiver/arguments/exception remain unchanged; no private JEI fields or raw graph lookup. Five-artifact task-origin binding, 32-layout limit, complete-frame/identity/dimension/time fences precede any future filtered projection. Private mutable layouts grant no public observation/input authority; Forge minor 27 remains. GI/SI/QA own actual hook-loading, rendering/overhead/mechanics and isolation qualification. [Evidence](docs/verification/2026-09-19-jei-render-capture.md). All original requirements and gates retained.

**D06 task-to-JEI lifecycle, 2026-09-19:** SPEC v0.2.17 / Forge minor 27 pins task policy `ftb-visible-item-task-menu-or-jei-open/2` and screen policy `ftb-own-team-book-and-task-recipes-state/2`. Exact non-consuming single-item route uses the ordinary callback, all five FTB/XMod/JEI hashes and common runtime identity. Origin-bound `task_recipes` and `quest_navigate/close` are implemented but unverified; JEI Back/history and current-page data remain .1b. Parent provenance is retained from opening, not recovered through private fields. Eighteen action kinds unchanged; no scope/gate/budget reduction. GI/QA/SI own native/resource/reference/isolation qualification. [Evidence](docs/verification/2026-09-19-quest-jei-lifecycle.md).

**D06 choice-menu controls, 2026-09-19:** SPEC v0.2.16 / Forge minor 26 adds `ftb-current-item-choice-menu-back-wheel/2`, preserving item controls and supporting exact opening-bound choice Back/scroll. Menu observation `/4` binds wheel state in revisions; no private scrollbar fields or claim route. Exact ordinary Back can restore the native pointer; earlier no-pointer wording applies specifically to wheel targeting. Native eighteen-action count unchanged. GI/QA own authentic callback/drag/polling/reference qualification; other extension/context/resource gates remain required. [Evidence](docs/verification/2026-09-19-quest-choice-controls.md).

**D06 choice-menu implementation, 2026-09-19:** SPEC v0.2.15 / Forge minor 25 adds `ftb-visible-choice-reward-menu-open/1`, native eighteen-action policy and menu observation `/3` with a distinct visible choice shape. Parent authority is retained from eligible ordinary opening, never private-field reflection or raw-table recovery. Only a pre-opening count limit is checked; no entries are read/exported before the native menu opens. Existing item rows and item-only Back/wheel remain. Claims, choice Back/scroll, other extensions and all authentic gates remain required. GI/SI/QA own qualification. [Evidence](docs/verification/2026-09-19-quest-choice.md).

**D06 item-menu control implementation, 2026-09-19:** SPEC v0.2.14 / Forge minor 24 pins `ftb-current-item-menu-back-wheel/1`, native seventeen-action policy and item-menu observation policy `/2` (wheel-sensitive revision; unchanged response fields). Exact item-menu Back/one wheel gesture is implemented but unverified. Choice/other menus, occupied crafting state, submissions/claims and all authentic qualification remain required. GI/QA own these cases; operator handling of Windows Security remains pending. No feature or gate is waived. [Evidence](docs/verification/2026-09-19-quest-menu-action.md).

**D06 item-task opening implementation, 2026-09-19:** SPEC v0.2.13 / Forge minor 23 pins `ftb-visible-item-task-menu-open/1` and native sixteen-action policy. Initial exact ItemTask menu opening is implemented but unverified; non-consuming single-item JEI/empty-toast/extension routes, back/scroll, occupied crafting state and submissions/claims retain required children. No gate or required feature is waived. GI/QA own native viewport/callback/reference qualification and the unresolved initial Node timing finding. [Evidence](docs/verification/2026-09-19-quest-task-open.md).

**D06 quest navigation implementation, 2026-09-19:** SPEC v0.2.12 / Forge minor 22 adds `ftb-own-team-book-state-navigation/1` and native fifteen-action policy. Exact own-team book state and catalog-bound chapter/quest/back/close are implemented but unverified; current opening/navigation require empty carried/crafting/result slots because native close also closes the player container. Occupied-grid resource handling, other UI contexts, tasks/menus/scrolling and submissions/claims retain required children. No feature or gate is waived. GI/QA own loaded-pack qualification; the operator owns the existing Windows Security handoff. [Evidence](docs/verification/2026-09-19-quest-navigation.md).

**D06 quest opening implementation, 2026-09-19:** SPEC v0.2.11 / Forge minor 21 pins `ftb-own-team-open-screen-cas/1` for the existing required quest UI. Only ordinary opening is implemented; navigation/close/back/scroll and submission/claim effects are explicit .3.2/.3.3 children. Native policy now lists fourteen actions; stock Mineflayer still rejects this new action. No campaign identity, study arm, required feature or release threshold is changed. GI/QA own exact-pack qualification; the operator owns the existing Windows Security handoff. [Evidence](docs/verification/2026-09-19-quest-open.md).

**D10, 2026-09-19:** implementation policy for the already required ordinary
machine transfers. One native click must have a conserved, scoped immediate
prediction and exact server-confirmed owned player/cursor result; machine storage
may advance independently without being credited as production. Hidden augment
slots are excluded from motor and feedback reads. Exact CoFH code routes
player-to-machine quick-move through augment slots, so that branch remains a
named implementation gap (.3.2.2b), not a removed requirement. Passive energy/tank
display values no longer invalidate the window input fence, so normal close and
slot actions can operate while a machine runs. Slot/cursor/body/control/age and
latest-observation fences remain intact. SPEC v0.2.5 and Forge minor 15 identify
this explicit correction to v0.2.4; no existing run or cohort is relabeled and no
gate is waived. Implementation is within D06's authorized structured API scope.

**D06 current item-menu implementation, 2026-09-19:** SPEC v0.2.10 / Forge minor 20 adds `ftb-current-item-alternatives-clipped-pages32/1`. Scoped `quests.menu` reads only the exact active item-alternatives screen after own-team/task/detail and screen/layout guards. Preserve clipped viewport and normal tooltip semantics; displayed enabled state grants no input authority. GI/SI/QA own loaded UI/source/privacy qualification. Choice/extension/rich surfaces and ordinary actions remain required. [Evidence](docs/verification/2026-09-19-quest-item-menu.md).

**D06 task/reward implementation, 2026-09-19:** SPEC v0.2.9 / Forge minor 19 adds `ftb-visible-own-quest-task-reward-tooltips-pages32/1` for already-required ordinary quest displays. Only normal bounded tooltips/formatted progress/claim state are implemented; item alternatives, choice/extension displays, rich content and actions remain named children. Official exact FTB Maven requests returned 403; already-authorized installed Library bytes supply a hash-checked external compile-only prerequisite, with no bundled FTB classes or alternate dependency. GI/SI/QA own loaded callback/UI/privacy qualification; no study arm, feature or gate is waived. [Evidence](docs/verification/2026-09-19-quest-components.md).

**D06 quest text implementation, 2026-09-19:** SPEC v0.2.8 / Forge minor 18 adds `ftb-visible-own-quest-plain-text-pages32/1` within the required player-accessible source. One visible/detail-accessible quest supplies bounded plain subtitle/description lines with independent text hiding, native page breaks and explicit unsupported rich content. Task/reward/link/guide/interaction work remains named, and no native integration or campaign claim changes. GI/SI/QA own native parser/UI/privacy qualification. [Evidence](docs/verification/2026-09-19-quest-text.md).

**D06 quest catalog implementation, 2026-09-19:** SPEC v0.2.7 / Forge minor 17 pins `ftb-visible-chapters-quests-own-team-pages32/1` for the already required player-accessible quest surface. Only the visible chapter/quest catalog and own-team progress/flags are implemented; details/tasks/rewards/interactions retain named child items. No required feature, study arm or gate is removed. GI/SI own native source/privacy qualification; the operator owns the pending Windows Security dialog. [Evidence](docs/verification/2026-09-19-quest-catalog.md).

**D08 extension, 2026-09-19:** the already authorized player-accessible recipe scope now has a two-category Thermal implementation under `jei-visible-crafting-thermal-item-fluid-focus-pages32/2`, SPEC v0.2.6 / Forge minor 16. One item or fluid focus returns bounded visible layout data under four exact artifact hashes; source/category/kind/revision identities remain explicit. Machine definitions are discovery-only and cannot be selected by the crafting motor. This supersedes the initial crafting-only query policy for the new uninstalled candidate without changing any admitted run, removing required categories/quests, granting automatic machine operation or waiving authentic gates. GI owns implementation; QA/SI own actual source/visibility/timing qualification. [Evidence](docs/verification/2026-09-19-thermal-recipes.md).

September 19 Thermal continuation: GI owns processing-aware transactions and live conformance (M0.3b.3.2.2/.4). The operator owns the still-displayed Windows Security/OpenJDK prompt; a fresh read-only capture confirmed it and no input was sent. The existing user handoff remains pending because the computer-use skill's guidance forbids acting on security permission requests. After that response, resume candidate deployment and actual GUI/server checks. Independent implementation continues. Inspection also corrected filename-versus-runtime version handling: the adapter now checks shortened mod metadata plus three exact loaded JAR hashes; no client failure was claimed from that predeployment correction.

These are unresolved prerequisites, not proof that future implementation cannot proceed. Convert a specific active work item to `blocked` only when its progress actually depends on the missing input. Keep unrelated work moving.

| ID | Owner | Affected work | Open condition | Default / next resolving action | Evidence or decision reference |
|---|---|---|---|---|---|
| B01 | GI | M0, F01/F05, T02 | Official vanilla workflow and exact E9E distribution/JVM/expert mode | Acquisition, user account/EULA, vanilla boot and E9E expert cold restart have actual evidence. Finish sealed inventories/provenance, resolve five effective-file findings and verify recipe/quest/reference assertions. | SPEC 7/D05, risks R02/R03/R06; [actual acquisition and game evidence](docs/verification/2026-09-18-long-horizon.md). |
| B02 | AR | M0, F03/N01, T04 | Exact CLI/plugin/helper/command/accounting/resume capability | Actual pinned CLI/plugin/helper synthetic conformance exists. Complete D11 estimate source/migration is delivered; OAuth all-request ingress, child admission/isolation, nested-depth capability and full restore. | SPEC 6/15, R04/R15; [native dispatch](docs/verification/2026-09-20-native-dispatch.md), [admission contract](docs/operations/validation-admission.md). |
| B03 | GI | M0/M1.1, F01/F06, T03/T05 | Mineflayer exact Forge/registry/recipe/machine compatibility; separate keybinding-capable extension | Actual Forge rejection and FML3 offer expose 111 channels/39 registries; source confirms real implementations and snapshot installation are required. D06 selects the already-permitted native Forge API fallback with separate identity/tests; its read-only foundation cannot resolve the mechanic gate. | SPEC 8/16, D01/D06, R01/R07/R10; [failed handshake evidence](docs/verification/2026-09-18-long-horizon.md), [fallback evidence](docs/verification/2026-09-18-forge-game-api.md). |
| B04 | PL | M0/M4/M5, F02/F11 | Hardware/provider capabilities and metered experimental budgets | D04/D11 authorize OAuth, Luna and the original $10 aggregate estimated-usage allowance; user confirms no outside experiments. Estimate-basis source and explicit migration are delivered. Qualify real ingress and minimum enforceable native access boundaries on available hardware. N=2 still needs a second licensed game identity; no partial team. | SPEC 15/D04/D11. Game acquisition/account steps have their own recorded outcomes; prior-spend input is resolved, and no exact OAuth billing conversion or supplied VM is requested for this allowance. |
| B09 | SI/GI | M0/M1, F01/N04/N06, T03/T06 | Historical six moderate npm audit findings in pinned authentication dependency chain | Resolved dependency advisory via exact uuid 11.1.1 override, preserving protocol 1.68.0. Full authenticated qualification/T06 remain independent. | [Remediation evidence](docs/verification/2026-09-18-long-horizon.md): npm audit zero findings, actual CJS consumers and buffer rejection tests pass. |
| B05 | SI | M1, F04/N04, T06 | Credential/process/filesystem/network separation and leak resistance | Implement actual boundaries and adversarial canary cases. | SPEC 4.1/13.5, R05/R11/R17. |
| B06 | QA | M2/M4, F09/N07 | Complete pack persistence, recovery and long-run capacity envelope | Inventory all mutable state; staged faults/soaks and capacity certificates. | SPEC 12/16, R08/R09/R16. |
| B07 | RS | M3/M5/M6, F10/F12/F13/F14 | Scorer reachability, identity assurance, costs, samples and calibrated thresholds | Develop controls; pilot first, then freeze powered/qualified protocol and untouched tests. | SPEC 13–14, R12/R13/R14. |
| B08 | PL | M7, C31–C34 | Whether conditional extensions are needed | Retain all extensions visibly; record need and scope before activating each. | SPEC 4/17; no activation decision. |
| B10 | GI/QA | M0/M1/M2, F01/F05/F06/F09, N01/N06/N07, T02/T03/T05/T07/T08/T09 | Exact CTM 1.19.2-1.1.6+8 client startup metadata-cache ClassCastException | Preserve both pre-world failed samples, including the September 20 settings-crash startup. Exact bytecode confirms unsynchronized null-valued HashMap operations. Qualify an explicit pinned repair/profile disposition; a separately recorded max.bg.threads=1 diagnostic is planned under unchanged deadlines, not a cache-correctness claim. A later successful startup cannot establish reliability or erase this crash; no silent mod removal/replacement. | [Authentic startup failure](docs/verification/2026-09-19-native-quest-cancel.md), D05/D06; fresh bounded diagnostic startup is authorized, with unchanged runtime and limits. |

Baseline history: the initial ledger recorded no authorized scope changes. **D01, 2026-09-18:** the user explicitly requested Mineflayer for controlling characters and as the first backend. SPEC v0.2.0 supersedes pixel-first A01, updates F01/F06 and related contracts/gates, and moves required real keybinding-extension evidence from G0 to G1. Original requirement/test/milestone IDs remain. Modded play, CurseForge + Forge, Dovetail, N, adaptation controls and the hotkey skill remain required. Optional physical-input profiles remain visible; no runtime capability or gate was passed.

**D02, 2026-09-18:** user steering questioned the need for MCP and proposed direct Codex CLI integration. The design defaults to native command calls through `mcgame`/scoped IPC and a persistent bot worker. CLI exec JSONL is the initial host adapter; MCP/app-server remain optional. A04, M0.1, C06/C09/C12, F03/F06/F16 and T01/T04/T06 are affected. Read-only CLI help/official docs support feasibility; real integration remains not run.

**D06, 2026-09-18:** implementation selection under the existing SPEC 8.1/16.1 fallback, following the actual Mineflayer/E9E failure and source inspection. Candidate `forge1192-structured-development/1` uses the real Forge client's mod implementations with a separate scoped structured API. The user reaffirmed API-driven gameplay; this is not authorization to resume desktop control or a new scope waiver. Mineflayer remains first/vanilla, its E9E failure stays recorded, and the fallback needs its own full conformance. Read-only development support cannot admit campaigns or promote any gate.

**D07, 2026-09-19:** implementation clarification under the authorized complete
Strata task: add an explicit `close_window` action to SPEC 8/9. Opening a container
without an available close operation prevents continued structured gameplay. This
adds ordinary menu lifecycle control with window/revision/capacity/resource checks,
server feedback and existing fencing/accounting, rather than silently closing menus
inside unrelated actions. Update both backend capability minors and schemas; keep
authentic close/return/cancellation conformance open. No scope removal or gate waiver.

**D08, 2026-09-19:** declared source-policy implementation under the authorized
full scope and SPEC 8.1/13.5, not a new authorization request or reduced scope.
Add exact JEI 11.8.1.1034 focused visible crafting input/output discovery with
explicit source/role/item/cursor, bounds, revision/generation and separate book
membership. SPEC v0.2.2 and Forge capability minor 12 record the changed affordance;
campaign admission stays disabled until authentic conformance and matched policy
are qualified. No hidden lookup, global dependency dump, cheat/transfer hook or
new crafting authority is introduced. Manual-grid execution for visible but
book-locked recipes is required .3.1d; custom categories/machines/quests remain .3.2.

**D09, 2026-09-19:** implementation completion of the already required visible
recipe execution path under the user's full-scope authorization. SPEC v0.2.3 adds
optional `recipe_selection` to `craft`: explicit JEI query/generation/initial
revision, current visible-definition revalidation and fixed manual grid fill.
Omitted/null selection retains book behavior; stock Mineflayer rejects JEI input.
Forge minor 13 declares the added motor/policy and unchanged deadline/accounting.
No gathering, recipe chain, automatic transfer, hidden-source access or gate waiver.
Authentic effects and matching scientific conditions remain required.

## Progress log (append-only)

### 2026-09-18 — Documentation and tracking baseline

- Added AGENTS.md and MILESTONES.md for the user's request to prevent feature omissions and require progress tracking. No implementation scope was activated.
- Tracked M0–M7, F01–F16/N01–N08, T01–T17, G0–G5, 35 feature groups, 13 record types and 10 API domains against SPEC.md. Later required and optional work retain explicit dispositions.
- Document checks: reconciled ID coverage and inventories against SPEC.md; confirmed implementation entries begin `not_started` or explicitly `deferred`, and every execution test/gate remains `not_run`. These are document checks, not T01 or runtime acceptance.
- Remaining work: all implementation and real-world gates. Next handoff action: use the current-position entry and M0 plan when implementation is requested; update this ledger in the same change as each implemented behavior and its evidence.

### 2026-09-18 — D01 Mineflayer first; D02 direct Codex CLI

- Updated SPEC.md to v0.2.0, BUILD_PLAN.md, SPEC_PROMPT.md, README.md and AGENTS.md; added [Mineflayer backend research/decision](research/mineflayer-backend.md). Earlier research reports now identify their superseded architectural proposals explicitly.
- Preserved F01–F16/N01–N08, M0–M7, T01–T17, G0–G5, all 35 original feature rows, all 13 record types and all 10 API domains. Added M0.1–M0.3, M1.1 and optional C36. Changed F01/F06/A01/A04 and cross-cutting observation/action/state/capability, lifecycle, resource and secrecy contracts. Full hotkey-extension acceptance remains required at T05/G1; no unsupported feature is marked passed.
- Default path: native Codex CLI/Dovetail -> local mcgame command + scoped IPC -> persistent Node.js/TypeScript Mineflayer worker -> authentic game server. Structured state/actions replace mandatory screenshots. MCP and app-server are optional; Forge compatibility still requires actual modded recipes and machine operations, not just a handshake.
- Actual checks: read-only `codex --help` and `codex exec --help`; official CLI/noninteractive documentation and primary Mineflayer sources; a temporary Node.js document checker. The document checker passed: 12 changed documents checked, 13 JSON examples parsed and matched to their documented top-level types, example observation/action/backend references consistent, 24 requirement IDs / 17 test IDs / 6 gate IDs / 8 milestone IDs and all original feature rows retained, local file links resolved, fences balanced. Manual review reconciled transport defaults, diagrams, optional capabilities and fallback identity. These checks are not generated-schema or runtime conformance.
- Remaining: all implementation and real-game/host/security/accounting/soak/research tests. Every T/G result remains `not_run`. Next handoff: implement M0.1/M0.2, then resolve M0.3 before claiming expert-pack support or expanding the harness.

### 2026-09-18 — D03 Strata naming and public repository preparation

- User selected **Strata** as the project name and **strata-bench** as the repository name, and explicitly authorized public GitHub creation/publication. Target owner is the authenticated **OpenCnid** account.
- Updated README, specification, build plan, fresh-session prompt and standing instructions. Added repository ignore rules for credentials, private evaluation/run data, installed games and generated build artifacts; removed a workstation-specific temporary path from this log for publication.
- Scope: naming and repository setup only (C02/C30/C35). All implementation milestones and T/G execution results remain unchanged. Publication verification is recorded below after the remote exists and files have been pushed.

### 2026-09-18 — Public repository publication verified

- Created [OpenCnid/strata-bench](https://github.com/OpenCnid/strata-bench) as a **public** repository with default branch `main`, connected local `origin`, and pushed the 14-file specification/research baseline in [commit 526a4db](https://github.com/OpenCnid/strata-bench/commit/526a4dbdcdcd21aa2575a612233e833f917e9ead).
- Verification: `gh repo view` reported `PUBLIC` and `main`; the GitHub commit API and local `git rev-parse HEAD` matched the initial commit exactly. The working tree was clean after the initial push. Document checks and `git diff --cached --check` passed; the staged credential-pattern scan had no matches. Ignore checks excluded example credential/run/fixture/dependency paths while allowing `.env.example`.
- Repository setup is complete. No game, backend, model, compatibility, reliability or benchmark execution result is implied; M0–M7 and T01–T17/G0–G5 retain their prior statuses. Next implementation work remains M0.1/M0.2 followed by the exact-pack M0.3 gate.

### 2026-09-18 — Implementation activated; partial M0 worker and contract foundation

- Authorization: user requested “Implement Strata according to the SPEC.md.” Implemented the bounded initial M0 slice under AGENTS.md; no feature, release threshold, backend choice or experimental requirement was removed. No game installation/terms acceptance, account login, inference spending or experiment was performed.
- Added pinned Python 3.12.14/uv and Node 24.19.0/npm packages; strict Observation/ActionBatch/ActionAck and local request models; exported JSON Schema and generated TypeScript. These are partial canonical-contract coverage, not full T01 or M1 completion.
- Added one persistent development Mineflayer worker with scoped authenticated loopback transport, `mcgame` reads/full-envelope actions and move/look wrappers; observed voxel projection, actual pinned pathfinder behind a filtered planning facade, bounded level walking/look/dig/hotbar/container quick-move subset. Container completion requests native server resync instead of trusting local predicted slots. Settings/unsupported mechanics reject explicitly. All actual Mineflayer mechanics remain implemented but unverified.
- Added SQLite WAL/FULL acceptance/action/observation evidence; single executor lock and mutation lane; request-digest deduplication, sequence/epoch/revision/lease/deadline checks; watchdog/cancel and conservative disconnect fencing; unresolved old actions recover as unknown without replay; primitive intent counter retained across epochs. Whole-system controller/recovery, full budgets/clocks and OS isolation remain open.
- Added read-only `mcbench doctor`, game-record validation, documented JSONL turn-usage inspection, and vanilla/E9E acquisition/conformance preflight. The exact E9E candidate and all ten compact cases remain visible and blocked/not_run. CLI help/source inspection does not prove native Dovetail or nested metering; no custom reasoning loop or substitute plugin was introduced.
- IDs advanced: M0/M0.1/M0.2 and children M0.1a–c/M0.2a–c; M0.3 now records a concrete prerequisite blocker, with M0.3.1–10 retained. Partial F01/F03/F05/F06/F09/F11/F16, N01–N03/N05/N06/N08 and C02–C04/C06/C09/C14/C15/C18–C20/C30/C35. Full keybindings, later packs and optional extensions remain in their original rows.
- Actual checks: 31 Python tests and 17 Node tests passed, Python lint passed, TypeScript strict/unused checks passed, schemas regenerated and validated across both languages. Native CLI fingerprint/help matched candidate; doctor and E9E preflight returned blocked (exit 2) as designed. Initial SQLite cleanup failure and vec3 type mismatch were fixed and retested. See [dated report](docs/verification/2026-09-18-m0-foundation.md) and [operations](docs/operations/development-worker.md). A subsequent final source/ledger reconciliation is recorded below.
- Remaining: official vanilla/E9E installation and identity, actual native Dovetail execution/helper/isolation/accounting proof, remaining vanilla actions/signals/pagination/reconnect, exact-pack mechanics, private scorer and real cancellation/clock/cost evidence. All aggregate T01–T17/G0–G5 remain `not_run`; M0 is not complete. Next handoff: resolve B01–B05/B09 and finish the M0 action/host gaps before authentic vanilla then immediate E9E conformance; do not expand scale or claim G0 from fixtures.

### 2026-09-18 — Final foundation reconciliation

- Rechecked source/contracts against observation privacy, mutation preconditions, ambiguous acknowledgements, control release, clocks and cost limits. Added pre-emission target rechecks after looking and a local dig/click cooldown; real mechanics remain unverified. Python now rejects numeric `release_at_end=1` consistently with the exported JSON Schema/TypeScript validator.
- Final local evidence: 31 Python tests, 17 Node tests, strict TypeScript compilation and Python lint/format checks pass. Generated schemas/bindings regenerated. Coverage checker retained exactly 24 requirement rows, 36 feature rows, 13 records, M0–M7, T01–T17 and G0–G5; every aggregate T/G row remains `not_run`. Changed Markdown links/fences and npm transitive integrity pins validated; `git diff --check` passed.
- No real game, native model job, compatibility pass, publication, milestone completion or scientific result is implied. Blocking prerequisites and the next handoff remain as above.

### 2026-09-18 — Continued controller, contracts and evaluator implementation

- User instructed “Okay, continue” after rejecting an early stop at the initial foundation, then confirmed exact game installations are currently unavailable. Continued independent authorized code work; no installation, terms acceptance, paid inference, experiment or scope reduction occurred.
- Advanced M1.1–M1.4, M2.1–M2.2, M3.1–M3.3, M4.1 and M5.1 with the models, private storage/controller, budget/clock/checkpoint services, artifact/team policies, settings workflow and separate evaluator described in [dated evidence](docs/verification/2026-09-18-controller-evaluator.md). Requirement/feature/schema/API rows now link partial implementations while retaining their integration gaps.
- Executed: schema export and TypeScript generation; Python lint; **107 Python tests passed**; TypeScript compilation and **18 Node tests passed**; operator CLI help and command/report tests. Fixtures are synthetic. An initial Typer option/argument mismatch was caught and corrected. Quota-before-write, private CAS canaries, budget races, incomplete snapshots, scorer negative controls and deterministic report replay are regression checked.
- Remaining: all real game/host/isolation/settings/telemetry/probe execution, full usage/recovery/retention integration, staged soaks/capacity/pilot/confirmation and mandatory later-pack work. Aggregate T01–T17 and G0–G5 remain `not_run`. Next action is the current-position implementation work; external dependencies do not close or erase independent gaps.

### 2026-09-18 — Continued vanilla body surface, client packaging and hash interoperability

- Advanced M0.1b/M0.2a, M1.2/M1.3 and M3.3: ordered bounded public signals/event waits; server-unlocked shaped/shapeless recipe projections; fixed craft slot motor with server resync and consumption/output checks; bounded placement; corrected generic furnace/table opening; allowlisted client-only package. No raw server recipes, worker internals or evaluator material enter the gameplay bundle.
- Added explicit RFC 8785 canonical hashing to SPEC section 9 and pinned rfc8785 0.1.4. This resolves the canonical-encoding implementation choice without changing features/affordances/budgets or gate thresholds. Actual Python/Node comparison covers number formatting and Unicode key ordering. Added `recipes.list` as a backward-compatible local-request operation under advertised capability minor 1; implementation/policy/schema hashes change accordingly.
- Latest executed checks: **115 Python tests passed; 26 Node tests passed**; Python lint; worker build; separate operator/evaluator TypeScript bindings; `uv build --wheel` and `uv build evaluator --wheel --out-dir dist/evaluator`. Public bundle runs its real compiled CLI outside the repository and rejects missing grants. Recipe/craft fixtures deliberately distinguish predicted from server-resynchronized state. Tests caught and resolved TypeScript nullable-slot/ES-library declarations; no remaining test failure. Evidence: [continued report](docs/verification/2026-09-18-controller-evaluator.md).
- Authentic Mineflayer operations remain implemented but unverified. Use/attack/entity/chat, richer equip/slot/navigation, spatial pagination, automatic reconnect, native Dovetail runner, isolated supervisors, official provisioning, actual Forge/telemetry/settings adapters, live probes and full research/reliability gates remain open. No milestone/MVP/release completion is claimed. User-confirmed missing installations remain B01/B04 prerequisites, not a reason to discard independent implementation work.
- Final reconciliation: coverage checker retained 24 F/N requirements, 36 feature rows, all 13 record rows, M0–M7, T01–T17 and G0–G5; aggregate tests/gates remain `not_run`. Changed documentation links and code fences passed; `git diff --check` passed. Inspected the two built wheels: operator wheel excludes evaluator code; both exclude tests and operator specification/instruction documents. Recompiled the worker and separately checked generated operator/evaluator TypeScript after the advertised minor-capability addition. No credentials, installations or live run data were added.


### 2026-09-18 — Long-horizon goal activated; provisioning implementation

- User explicitly requested a long-horizon task to complete the milestones. Started the native goal for required M0–M6, retaining conditional M7. Independent implementation continues rather than ending at this batch. No game installation, terms acceptance, account login, paid inference or experiment has occurred.
- Added M0.3a: durable exact-target resolution/acquisition waits, private receipt/evidence import, complete role inventories, archive/path/privacy checks, streamed quota-bound immutable asset storage, digest-bound provisioning checks, sealed PackLocks and independent fresh materialization. Advanced F05/F16/N01/N04/N06/N08, C04, PackLock and pack-acquisition API coverage.
- Actual checks: 18 provisioning tests passed; combined provisioning/storage/controller/operator-command suite **40 passed**; lint passed. Follow-up verification and limitations are recorded in [long-horizon evidence](docs/verification/2026-09-18-long-horizon.md). Synthetic game assets remain explicitly examples; aggregate T/G rows remain `not_run`.
- Rechecked official sources: CurseForge documents vanilla profiles and retains the exact selected E9E client/server pages. This resolves the documented workflow question only; real feasibility/acquisition and expert assertions remain B01.
- Next ongoing work: supervised native-runtime processes, game-access revocation and complete metering/restore integration; then real isolated host and game checks once concrete execution prerequisites are supplied.


### 2026-09-18 — Native supervision and D04 execution authorization

- Added native exec adapter, trusted process bootstrap and Windows kill-on-close Job Object fencing. Dispatch intent precedes process creation; one executor, parent-linked helper slots/depth, bounded raw output, timeout/interrupt, descendant shutdown and fenced recovery are durable. A fresh-handoff state references admitted artifacts and excludes session/cache carryover; complete checkpoint materialization remains integration work.
- Actual Windows process tests verify argument/stdin/environment boundaries, killed grandchildren, no delayed mutation and cleanup after parent exit. Native JSONL producers are synthetic and invoke no model. Tests cover malformed/truncated output, disk failure, revocation failure, helper scope, crash/duplicate intent, settlement and fresh epochs. A Windows fixture initially decoded UTF-8 using its default codepage; fixed the fixture to decode the native UTF-8 byte contract explicitly.
- Executed full Python suite: **152 passed**; lint and `git diff --check` passed. After D04 policy implementation, authorization/native/operator subset: **19 passed**, lint passed. Node code unchanged from prior 26-test baseline. All aggregate T/G gates remain `not_run`.
- **D04:** user explicitly chose Codex OAuth, initially `gpt-5.6-luna`, and **$10 total inference**. Added [operator authorization](configs/operator/live-validation.json), durable shared-root cap and model/auth checks; installed it into a private external operator store with zero model dispatch/spend. Reinstalling the policy does not reset the cap; development/training/evaluation/helpers share it. More expensive models are not enabled yet. Updated SPEC section 15; no scientific threshold or required scope changed.
- Read-only `codex login status` confirms ChatGPT authentication. Official docs distinguish OAuth subscription/credits from API pricing; native turn summaries and account-wide quota percentages do not certify exact job dollar costs. Verified monetary conversion, finite all-call limits and credential separation remain required. No credential cache was copied or published and no live model call ran.
- Began actual native plugin installation in a separate empty inspection profile, without inference or inherited user configuration. First remote checkout hit a Windows path-length error; a short profile and child-scoped Git long-path setting resolved it. Native installer reported Dovetail 0.4.1. Inspection found the upstream marketplace plugin source names `main` even when the marketplace itself is pinned; verifying installed bytes and implementing an exact-source installer before any runtime qualification. This is installation inspection, not T04 skill invocation.

### 2026-09-18 — Exact plugin source, private schemas and spatial pagination

- Implemented and actually ran an exact-source local marketplace installer through the pinned native CLI in an empty external profile. Native config, clean Git HEAD, actual installed bytes and eight skills match the selected Dovetail revision; digests are in [long-horizon evidence](docs/verification/2026-09-18-long-horizon.md). No credential import or model invocation; this does not close T04.
- Exported seven additional operator-only API models (native launch, authorization and provisioning) without changing the 13 canonical identities or exposing them through the gameplay package.
- Added minor-2 opaque spatial pagination through the scoped CLI/gateway. Fixed region/time/revision, 128 entries per kind/page, 30-second expiry, four-region cache, dimension/worker separation and journal-before-planner admission. Pending pages never read new world state; old pages cannot overwrite newer memory. Known limitations and negative cases remain visible.
- Advanced M0.1c/M0.2a/M1.2 and partial F03/F06/F11/F16, N01/N02/N04/N06, C06/C08/C09. Actual checks: **164 Python tests / 31 Node tests**, lint, generated schemas and strict worker/operator/evaluator TypeScript checks passed; `git diff --check` passed. Game geometry and model streams are synthetic. All aggregate T/G results remain `not_run`.

### 2026-09-18 — Explicit inventory motor and carried-stack projection

- Extended M0.2a / F06/F16 / C09 / T01/T03 with left/right pickup and quick-move, player window 0, fixed explicit equip sequences for main/off hand and armor, per-click server resync and item/NBT conservation. No implicit drops or equipment search. Crafting output still requires the explicit recipe action; unqualified window serializers remain unsupported.
- Added the optional public `window.cursor_item` field to the SPEC/schema (development minor 3), containing only the ordinary carried item ID/count and the same empty component allowlist. This is necessary visible state for slot control, not privileged data. No existing cohort exists; the changed profile/schema/policy fingerprint distinguishes the surface. Added normal server cursor-only packet decoding because the pinned upstream ignores window -1; such updates advance window revision before another click.
- Actual checks: **39 Node tests passed**, including eight inventory/cursor cases against pinned library predictions and a separate synthetic server state; **55 Python contract/record tests passed**, lint passed. Fixtures reject predicted-only success, server-created extras, changed carried metadata, cancellation and window replacement. Published upstream TypeScript declarations needed narrow fixture casts for nullable slots/click fields; build now passes. The added direct `prismarine-item` 1.18.0 pin resolves the already-installed version; npm retains the six moderate B09 findings.
- Real-game acceptance, remaining use/attack/entity/chat actions, general navigation, reconnect and all host/isolation/telemetry/probe/soak gates remain open. Continue the active long-horizon goal; no milestone/release closure.

### 2026-09-18 — Bounded gestures and safe qualification bootstrap

- Implemented M0.2f input dispatch through normal Mineflayer methods: bounded main/off-hand use; one attack or main-hand entity interaction only on an actually projected, still-visible identity within three blocks; ordinary single Unicode chat without commands/control characters or implicit splitting. The new development capability minor 4 declares `emitted_input_only`; packet dispatch is not promoted to a gameplay postcondition or benchmark success.
- Local held-input ownership is independent of upstream `usingHeldItem` resets. Cancellation releases once, charges the release even after abort, then closes the connection; admission leaves room for both activation and release. Failed release evidence causes a connection fence. A failed backend stop produces `unknown`, `release_confirmed=false` and resync instead of claiming a successful stop. Required real watchdog timing remains open.
- Actual checks: **48 Node tests and 165 Python tests passed**, lint and strict operator/evaluator TypeScript passed. Gesture/identity/hidden/reuse/range/Unicode/cancellation/release/duplicate/failure fixtures are synthetic; no account/game/model call was made. Updated [long-horizon evidence](docs/verification/2026-09-18-long-horizon.md).
- Fixed the native qualification bootstrap dependency: explicit `purpose=conformance` jobs may test plugin invocation/host behavior after essential isolation, credential protection and complete bounded billing proofs, using the development account only. `purpose=campaign` still requires every original proof. Purpose is fingerprinted and inherited by helpers, so conformance evidence cannot admit a campaign. Actual targeted native/record tests: **44 passed**, lint/schema generation passed. Essential proofs remain unavailable; this does not dispatch a model or relax T04/G0/G1.
- Asked the user to prepare the unavailable official game installations and complete account/legal steps while source work continues. D04 OAuth/Luna/$10 remains authorized; no repeated budget/model approval was requested. Next work: supervised reconnect/recovery, complete artifact restoration, authoritative telemetry and live-run qualification.


### 2026-09-18 — D05 acquisition and checkpoint snapshot binding

- Recorded the user's explicit request for Codex to create dedicated vanilla 1.19.2 / E9E 1.27.0 CurseForge profiles and acquire the official server files. Installed the official winget CurseForge package (older 0.220.1-9343 build); downloaded exact official client/server archives, the vendor bootstrap installer and ServerStarter 2.4.0 into private external storage. Real hashes and distributed bootstrap inspection are in [long-horizon evidence](docs/verification/2026-09-18-long-horizon.md). Advanced M0.3.1 / F01/F05 / C04, without passing T02.
- Automatic approval blocked app launch with only “blocked by policy”; a reduced download-only command succeeded. The user opened CurseForge, then native computer use reported a physical Escape stop. Stopped native UI work; profiles and updater completion are unverified. No Java/game/bootstrap/EULA/account/model work executed. Both authentic archives expose eight JEI configuration members matching the broad world-state exclusion; preserve and inspect them before a scoped import-policy correction.
- Bound complete checkpoint references and identity in CleanStop/2, rejected legacy/mixed sets, streamed large-save verification/copy and rejected secret/colliding paths. Native artifact export/resume requires exact campaign/agent namespaces. Advanced M2.1 / F09 / N03/N04/N06 / T08 negative coverage. Actual targeted checkpoint/native suite: **32 passed**; lint passed. Corrupt-copy fixtures preserve the previous independent restore and publish no partial target. Complete authentic game-and-agent restoration remains open.
- Long-horizon goal stays active; next action is to resume profile preparation when computer use is available, resolve actual archive classification, provision Java and the inspected bootstrap, and continue supervisor/reconnect/telemetry implementation. All aggregate T/G gates remain not_run.

### 2026-09-18 — Dedicated profiles, exact bootstrap and vendor configuration policy

- User explicitly resumed desktop interaction. Created official CurseForge-managed `Strata Vanilla 1.19.2` and imported exact official E9E 1.27.0, named `Strata E9E 1.27.0` through the UI; no replacement launcher or modified pack. Installed Temurin 17.0.20.1+1 JRE and ran the pinned, source-reviewed ServerStarter 2.4.0 install-only path with a bounded Windows process tree. It exited 0 after Forge 43.4.23 installed. EULA was not accepted and no world started.
- Actual evidence: 232/232 client mods, 226/226 server mods after the distribution's six applicable client exclusions, zero missing/extra mods and zero shared-file hash differences. Bootstrap tree hashes cover 18,121 files / 572,768,937 bytes. Official vanilla client/server SHA-1 match Mojang metadata. Private inventory/logs under `C:/Users/Darian/.strata/evidence/2026-09-18-provisioning/`; [provisioning evidence](docs/verification/2026-09-18-long-horizon.md).
- Fixed the actual archive import rejection without deleting vendor content: `pack_policies.py` permits only the eight exact initial JEI world-config paths, with kind checks and the 52-byte bookmark's exact SHA-256. Changed bookmarks, unlisted runtime state and all credential/private paths still reject. Applied the policy to archive inspection, installed verification and fresh materialization. Actual official receipt imported as ACQUIRED, not sealed.
- Checks: `uv run --frozen pytest -q`: **176 passed**, two existing Typer deprecation warnings; provisioning subset **20 passed**, Python lint passed. Fixtures cover default-deny, changed content, wrong kind, private siblings and immutable materialization. Authentic acquisition/bootstrap evidence is distinct from synthetic guard fixtures.
- Coverage: M0.3.1/M0.3a, F01/F05, N04/N06, C04, partial T02 advanced. All aggregate T01–T17/G0–G5 remain `not_run`. Next: account/EULA handoff, complete role provenance and expert cold-start checks, while continuing independent required implementation.

### 2026-09-18 — Authentication cache, dependency remediation and user sign-in handoff

- Resolved B09's six moderate audit entries using the exact patched uuid 11.1.1 CommonJS-compatible override; inspected both real consumers (`@azure/msal-node` and `yggdrasil`) and retained protocol 1.68.0. Actual module loading/v4 calls and v3/v5/v6 truncated-buffer rejection pass; npm audit now reports zero findings.
- M0.2g adds an operator-only bounded Microsoft device-auth initializer, protected per-account cache, immutable account-label/profile binding, signed-chat certificate prerequisite and a worker callback that rejects login prompts and late post-cancellation connections. The strict cache factory removes upstream directory fallback, rejects corrupt/shared-linked files and writes atomically. Token/provider error bodies never enter public responses. Initializer modules remain absent from the allowlisted gameplay bundle.
- Actual Windows directory/child ACL tests pass, including deliberate weakened-permission rejection. An initial PowerShell-file helper was blocked by local script policy; it was removed and replaced by native Windows security APIs through the pinned Python runtime. No execution/security policy was changed. Synthetic gesture fixtures needed the new authentication cancellation controller; no gameplay behavior was weakened to make tests pass.
- Checks: **58 Node tests passed**, npm audit **0 vulnerabilities**, Python gameplay bundle test **1 passed**, Python/helper lint and `git diff --check` passed. Prior full Python result remains **176 passed**. Synthetic Microsoft responses are labeled; these tests do not certify authenticated gameplay or T06.
- User reports launcher sign-in complete. Both prepared server EULA files remain false. A real worker device-auth request is awaiting the operator at the private protected prompt file; no Minecraft connection/model/inference spend occurred. Native Computer Use reported another physical Escape stop and is paused pending user resumption; code work continued.
- Coverage: M0.1b/M0.2g/M1.3, F01/F04/F06, N04/N06, C04/C09 and partial T03/T06/T07. All aggregate T/G gates remain open. Next: complete account/EULA handoff and authentic vanilla/E9E attempts while continuing supervisor/recovery and private telemetry.


### 2026-09-18 — Exact E9E mode-file inspection

- Advanced M0.3.2 / F01/F05 / C04 / partial T02 preparation with `pack_modes.py`
  and the operator `pack inspect-expert-mode` command. Six exact release files and
  the complete 260-file ConfigSwapper expert overlay tree are hash-bound. Setup
  permits absent mode state while identifying it; effective checks require expert
  mode and the explicitly selected world, compare TOML leaves/types and replacement
  bytes, and reject altered/missing/unsafe content. No game/config mutation occurs.
- Actual server and client setup inspections each passed eight file checks. Private
  reports: `.strata/evidence/2026-09-18-provisioning/e9e-{server,client}-mode-setup.json`.
  Source-backed startup/config/recipe/quest expectations and remaining runtime steps
  are in `docs/operations/e9e-mode.md`. These checks do not pass aggregate T02/G0.
- `uv run --frozen pytest tests/test_pack_modes.py -q`: **12 passed**; initial fixture
  snapshot incorrectly used the software-template scanner on a synthetic world and
  was corrected to compare fixture bytes without weakening production restrictions.
- The separate Microsoft worker device request expired with `AUTHENTICATION_TIMEOUT`.
  No retry or game connection occurred. Both server EULA files remain false. User
  Escape stopped native UI; desktop control remains paused. Continue independent
  implementation; a fresh device request needs a coordinated user-ready window.


### 2026-09-18 — First authenticated vanilla run and exact E9E startup

- User completed the Java-owning Microsoft account flow and explicitly accepted
  the Minecraft EULA, authorizing both prepared `eula.txt` edits to true. Recorded
  D05 follow-up in SPEC. The earlier account returned profile HTTP 404 and zero
  entitlements; a separate protected cache holds the correct account. No secret
  or account cache entered the repository. Native UI remains paused after Escape.
- Fixed prismarine-auth 3.1.1 declaration/runtime disagreement: signing expiry is
  a Date in `profileKeys.expiresOn`, not at the certificate root. The regression
  exercises the actual pinned certificate decoder with a synthetic response/keypair.
  Real Java profile and certificate authentication subsequently succeeded.
- Added bounded interactive operator-console input to the existing Job Object
  process owner and `tools/development_server.py`: reviewed private plan, executable
  hash, preaccepted EULA, online authentication, localhost binding, complete private
  logs, clean stop and hard lifetime. A real fixture found CPython finalization
  racing a blocked console-reader thread; bootstrap now exits after child completion
  without that finalization race. Native/process regression suite: **22 passed**.
- Official vanilla 1.19.2 server booted and accepted the authenticated Mineflayer
  connection. Scoped CLI observations, look and dig produced live receipts. Two
  pre-emission navigation failures exposed the missing public `game.minY` on the
  filtered pathfinder facade; fixed and tested uneven terrain without raw world access.
  After proven process/connection fencing, a fresh worker epoch completed movement
  with 18 charged motor events. A 150 ms in-flight return movement was cancelled
  in approximately 20.7 ms measured round trip; 3 events retained, socket closed,
  resync required, duplicate request returned cancelled without dispatch. Earlier
  failed receipts and a rejected revision race remain in evidence.
- Idle disconnect now fences the epoch; a same-epoch reconnect cannot regain action
  authority. Initial connecting state is distinguished from a ready avatar. Worker
  output separates gateway readiness, connected avatar and fenced status. Three
  lifecycle regression cases passed, including reentrant disconnect callbacks.
- Vanilla clean stop exited 0 with all dimension-save messages, no forced termination
  and complete logs after 484.97 s. Private evidence: `.strata/evidence/2026-09-18-vanilla-boot-01/`.
  This is partial T02/T03/T07 evidence, not native-model, full resource/mechanics,
  authoritative private scoring, timing qualification, automatic recovery or a soak.
- Immediately began the exact E9E bootstrap with expert `mode.json` established
  before any world; the source-supported root mode file is also set in the dedicated
  client. Disabled only bootstrap automatic crash restart and pinned its changed YAML,
  localhost properties and Java environment in private evidence. Original YAML is
  retained. No content mods/recipes changed. Startup remains in progress.
- Full verification: **190 Python tests passed** (two existing Typer deprecations),
  **63 Node tests passed**, strict worker compilation, Python lint and diff whitespace
  checks passed. M0.2a/b/c/g, M0.3.2, M2.1 and F01/F05/F06/F09/N02/N03 advanced;
  full T02/T03/T07 and all aggregate gates remain open. No model inference/spend.


### 2026-09-18 — Exact E9E cold restart and failed Forge handshake

- Exact E9E 1.27.0 / Forge 43.4.23 booted twice with expert mode established before
  world creation. Both clean stops exited 0, no forced stop, complete logs; 259.469 s
  and 359.203 s. All dimension-save messages retained. No scored baseline, reference
  client gameplay, model call or inference charge occurred.
- Effective-file inspection after each stopped boot: **263 pass / 5 fail**, with
  identical results and hashes across cold restart. Missing targets: bhmenu-client,
  nomoreworldsettings-client, inventorysorter-server and sophisticatedcore-server;
  Create overlay references three absent legacy keys. These are retained findings,
  not deleted configs or automatic exceptions. Primary expert recipe/quest/team and
  independent client verification remain open; T02 stays not_run.
- The unextended authenticated Mineflayer client was explicitly rejected for lacking
  Forge. A source-backed, bounded FML3 metadata decoder now inspects wrappers/mod-data/
  mod-list offers, rejects malformed/oversized/duplicate/truncated input, and advertises
  no Forge support. Four synthetic parser tests pass. Exact sources JAR SHA-256 is
  663e58cdde75ce06f4713cfcedea4414c39d17adcfddcfa81c6da5adcd59102f.
- Separate operator diagnostics retained the initial unsupported Quark login packet,
  then passively received unacknowledged offers: 233 mod IDs, 111 channels, 39 synced
  registries, two custom datapack registries. The probe deliberately disconnected
  before join; it did not echo unsupported channel claims or complete a handshake.
  All raw packets/offers are private live evidence, never repository fixtures or
  gameplay tools. The allowlisted gameplay package test still passes.
- M0.3.3 stays blocked; T03 and G0 are now **fail**, recording the authentic compatibility
  failure rather than leaving the attempted requirement not_run. Most other compact
  cases remain unrun. Next: locked actual channel/registry implementations, expert
  reference/assertions, plus continuing independent native isolation/accounting work.
  Private evidence: `.strata/evidence/2026-09-18-e9e-boot-{01,02}/`. All game/worker
  processes were confirmed stopped. Desktop UI remains paused after the user's Escape.


### 2026-09-18 — Read-only Forge telemetry and runtime expert recipe evidence

- Added `java/forge1192-telemetry` and the private Python spool inspector. Exact
  Forge 43.4.23 / official 1.19.2 mappings build with Temurin JDK 17.0.20.1+1,
  ForgeGradle 6.0.42 and hash-pinned Gradle 8.8. Installed the matching JDK under
  existing dependency/provisioning authorization. Wrapper, compiler, eight
  Forge-managed inputs, dependency versions and Maven verification hashes are
  pinned; the final JAR hash is
  `745d47d2fdad6d6b426c31b2d9b9e3494bfe9a86e12b77541a4f97ca7817c26d`.
- The module has no commands, client channels or state setters. It writes bounded
  evaluator-only boot/tick/recipe/raw-craft records through a durable single writer.
  Raw callbacks explicitly cannot score. Private inspection rejects sequence/scope/
  boot/clock corruption, partial tails and missing clean stop. Same-user filesystem
  checks are not a qualified isolation boundary or authenticated transport.
- Actual instrumented E9E runs 01/02/03 all reached readiness and exited 0 after
  clean stops, with complete logs and no forced termination: 184.422 / 184.454 /
  184.391 seconds. Run 01 exposed missing resource metadata; added `pack.mcmeta`
  and retained the original JAR/logs. Runs 02/03 used identical final JAR bytes:
  67/63 records, 1296/1228 observed server ticks, distinct boot IDs and identical
  runtime recipe snapshots. Their six exact furnace assertions pass: expert
  shaped 3x3 recipe, one furnace output, five andesite plus three polished andesite,
  empty center, and no vanilla furnace recipe. No player joined these runs.
- These are M0.3.2/M3.1a partial runtime checks, not player crafting, quest/team
  verification, private predicate provenance, reference parity, overhead, a soak
  or a G0/T02/T03/T10 pass. The instrumented installation has a separate identity;
  no vendor content mod or recipe was removed/replaced. Added instrumentation is
  retained in the development server and private evidence, not in a sealed pack.
- Source review of exact Forge key handling exposed an earlier planner error:
  UNIVERSAL/custom contexts and different modifier lists were treated as disjoint.
  Corrected conservative physical/context conflicts, including modifier-key
  activation and unknown keysym/scancode aliases. Five regression cases pass;
  actual client effect/restart T05 remains open (M1.1/C10/C11).
- Verification: `uv run pytest -q` **209 passed**, two existing Typer deprecations;
  `uv run ruff check src evaluator tests tools` passed; exact Gradle build passed,
  **5 Java tests passed**; `git diff --check` passed with line-ending notices.
  SPEC section 16 now points to this ledger rather than its stale initial
  documentation-only execution statement. No acceptance case was removed.
- Evidence: `C:/Users/Darian/.strata/evidence/2026-09-18-e9e-telemetry-{01,02,03}/`,
  private spool under `.strata/telemetry/e9e-development-{01,02,03}/`, and
  [runbook](docs/operations/forge-telemetry.md). Affected F01/F05/F06/F10/F16,
  N01/N03/N06/N08, C04/C10/C11/C18/C24. All server processes stopped; no model
  inference/spend. Next: actual Forge settings extension, provenance adapters,
  telemetry identity/supervisor integration and the retained compatibility gates.


### 2026-09-18 — Forge client binding discovery foundation

- Added the separately identified `java/forge1192-client` module and
  [runbook](docs/operations/forge-client-settings.md), splitting M1.1a into
  discovery (a.1, implemented_unverified) and native transactions (a.2, not_started).
  Actual effects/restart/isolation remain M1.1b. No keybinding capability is advertised.
- Discovery executes on the client thread after mod loading and emits one bounded
  optional operator snapshot: runtime/default keys, modifiers, native/custom
  contexts, labels, stable owner/translation/occurrence IDs, persisted key fields
  and ambiguity. Explicit mapped vanilla Options references survive reobfuscation;
  arbitrary reflection/translation prefixes do not establish mod ownership.
  Unknown owners, all mutations, tested keys and restart claims remain disabled.
- Missing first-launch options files yield explicit unknown persistence without
  creating/editing options. Four synthetic Java options/identity tests passed;
  exact Forge reobfuscated build succeeded under existing locked dependencies.
  Client JAR SHA-256: `6947930421e1c4d5b52481517e3197fe861658e9d2951cce2a567a1be787851f`.
- Confirmed no Java client was running, added only this instrumentation JAR to the
  dedicated E9E development profile, and retained the binary plus preparation
  receipt under `.strata/evidence/2026-09-18-e9e-client-discovery-01/`. No vendor mod
  changed. The profile is now instrumented; this is not a sealed baseline or a
  live settings pass. Native desktop control remains paused after the user's
  Escape; an explicit resume question is pending. No UI operation or client launch
  occurred during this work. Continue native transaction/evidence work while waiting.
- F06/F16/N01/N06 and C10/C11 advanced partially. T05/G1 remain not_run. The latest
  Python full run remains 209 passes; telemetry Java 5 plus client Java 4 passed
  separately. All game processes are stopped, inference spend remains zero.


### 2026-09-18 — Desktop resume attempt

- User explicitly answered “Resume desktop interaction” for the prepared E9E
  client/settings check. Recorded authorization; do not ask for the same approval
  again merely because the helper failed to resume.
- Re-read native Computer Use recovery/API guidance, initialized the supported
  `@oai/sky` entry point, and attempted `sky.list_apps()`. The tool immediately
  returned “Computer Use was stopped by the user with the physical Escape key”
  and required ending desktop interaction for this turn. No app input or client
  launch occurred. Whether this is a new physical stop or retained helper state
  has not been established; do not claim the client check ran.
- Java-owning authentication remains successful. All game processes remain stopped.
  Native goal remains active; no milestone or release gate closes. Next useful
  implementation is M1.1a.2 native settings transactions and telemetry/scoring
  integration while desktop helper recovery is unresolved. Four client and five
  telemetry Java tests passed separately; latest Python suite is 209 passes.


### 2026-09-18 — Persistent desktop-tool stop signal

- User clarified that they did not press Escape. Their explicit desktop-resume
  authorization remains valid; do not describe this as a newly requested stop.
- Reset the supported Node REPL session (`js_reset`), imported `@oai/sky` afresh,
  and retried only `sky.list_apps()`. The identical physical-Escape stop error
  returned immediately. No app input or launch occurred. Stopped further native
  desktop calls. This is a persistent tool stop-state blocker with unknown cause,
  not missing user permission or a failed Minecraft integration test.
- Continue independent M1/M3 implementation under the active goal. The prepared
  client JAR/private output directory and all successful server/auth evidence
  remain intact. No extra approval, model charge or release claim was introduced.

### 2026-09-18 — Desktop access recovered

- User explicitly requested repair/resumption and repeated that no Escape key was
  pressed. A fresh supported `js_reset`, `@oai/sky` initialization and `list_apps`
  succeeded. Subsequent CurseForge and Minecraft Launcher state capture and UI
  input succeeded. The cause of the earlier stop signal remains unknown; do not
  attribute it to user action or claim a permanent helper repair.
- Resumed M1.1a.1 real-client preparation through the dedicated CurseForge profile.
  Launcher selected E9E 1.27.0 / Forge 43.4.23 and displayed Java Edition PLAY.
  Set the installation-specific pinned Temurin Java 17 `javaw.exe` and appended
  the private discovery output property, preserving the existing JVM flags.
  Confirmed saved fields by read-only inspection; launched the selected profile.
- Private launch receipt: `.strata/evidence/2026-09-18-e9e-client-discovery-01/launch-configuration.json`.
  `javaw.exe` SHA-256: `326c477cf91039f50f4ffb507801972882ea09546bd9e2c9f36e9d32a5aa7a97`.
  Client JAR remains `6947930421e1c4d5b52481517e3197fe861658e9d2951cce2a567a1be787851f`.
  Actual loading/export results are pending; no T05/G1 pass or inference charge.

### 2026-09-18 — Actual client discovery, UI sample and cold restart

- M1.1a.1 / F06/F16/N01/N06 / C10/C11 / partial T05: exact E9E 1.27.0,
  Minecraft 1.19.2, Forge 43.4.23 and the unchanged client JAR ran twice through
  the official CurseForge-managed Launcher with matched pinned JRE/arguments.
  The UI reported 240 loaded mods. Both reached the title screen and exited
  through ordinary Quit; game and Crash Assistant monitor processes were absent
  before final logs were copied. No world was entered, no key binding was changed,
  and no model inference occurred.
- First live export: 253 bindings, 34 explicit vanilla owners and 219 unresolved
  mod owners, 31 custom/unknown contexts, no duplicate occurrence/persistence flags.
  The first options file existed but had zero key lines, so all 253 persisted
  values correctly remained unknown. The UI sample matched movement, modifiers,
  mouse attack/use and unbound Curios. Ordinary Controls/Options Done saved 253
  key fields; the second boot retained every runtime/default/owner/context field,
  stable identifier and all 253 persisted/runtime matches. Six bounded comparison
  assertions passed; this is not a worker-managed repair/restart or effect pass.
- Added [bounded audit](src/mcbench/client_discovery.py) and
  [synthetic negative cases](tests/test_client_discovery.py): duplicate/unknown
  JSON fields, bounds, mixed backend, forged IDs/occurrences/owner basis, unsupported
  authority claims and concurrent options-file changes. Reports exclude unrelated
  options values and explicitly leave producer authentication, effects and the
  gate unverified. `uv run --frozen pytest tests/test_client_discovery.py tests/test_controls.py tests/test_gameplay_package.py -q`:
  **28 passed** (13 new audit cases); targeted Ruff and `git diff --check` passed.
- Private evidence: `.strata/evidence/2026-09-18-e9e-client-discovery-01/` contains
  two raw exports/audits, native-saved options, launch comparisons, screenshots,
  final logs, ordinary-stop receipts and hashes. Export SHA-256 values are
  `368bba2f9de2e81241b7ed478a2f92e6eb5357b07164792dc53f5a4515fc4262`
  and `9f72f6d7e7ebe7f35505d652f7cd41ee31943b6d7e2d67d9d4b1b80883b575fa`.
- Findings retained: Controls emitted GL `65540: Invalid scancode -1`; cause and
  uninstrumented reference parity remain unresolved. CurseForge regenerates the
  launcher's Java path/arguments on each Play, so both were reapplied through UI
  and compared before the second launch. Directly opening the launcher executable
  used a different/default profile directory and showed a login screen; it was
  closed without authentication input and the managed CurseForge route was used.
- Desktop recovery used only the supported helper session reset, fresh import and
  returned window handles. It remained usable throughout; the earlier stop-signal
  cause is unknown, not evidence of an actual user Escape. T05/G1 remain `not_run`,
  M1.1a.1 remains `implemented_unverified`, and native CAS/effect/input/isolation
  work remains M1.1a.2/M1.1b. Continue those under the active long-horizon goal.

### 2026-09-18 — Native settings transactions; user pauses desktop

- Advanced M1.1a.2.1/2.2, F06/F09/F16/N01/N02/N06/N08 and C10/C11/C15:
  [Java store](java/forge1192-client/src/main/java/io/github/opencnid/strata/client/SettingsStore.java)
  now holds a profile lock, journals backups and transitions before mutation,
  fences revisions, patches owned key fields and conservatively rolls back.
  Repeated requests never replay a forward write; applied does not mean committed.
  Foreign values, truncated/corrupt journals and insufficient recovery space fail
  closed. Unicode separators cannot hide unrelated bytes in an owned key field.
- Added [native adapter](java/forge1192-client/src/main/java/io/github/opencnid/strata/client/NativeSettingsRuntime.java)
  with exact Curios artifact/registration-object checks, client-thread setters,
  key lookup rebuild and native release/readback. Its developer-only unbound/F13
  encoding probe does not qualify physical input, effects or settings capability.
  [Title-screen probe](java/forge1192-client/src/main/java/io/github/opencnid/strata/client/ClientSettingsProbe.java)
  is built but not run. All general discovery capability flags remain false.
- Executed pinned `:forge1192-client:test :forge1192-client:build`: **24 tests
  passed**, zero failures/errors (20 transaction cases with synthetic runtime and
  real Windows files/locks; four parser tests). Reobfuscation/build succeeded.
  `git diff --check` passed with existing line-ending warnings. Final JAR hash:
  `b4001b77c3a54fb754b4c21af255008550287d7960b9e885f4eb2c45e388cb8b`.
  Private log/XML/JAR/hash archive: `.strata/evidence/2026-09-18-native-settings-unit-01/`.
- Desktop helper responded again; CurseForge opened the managed Launcher. The
  user then explicitly paused desktop control while using the computer. No app
  input/capture followed that message; the new JAR was not installed or launched.
  Background implementation/tests continued. This is a current user-requested
  pause, not evidence for the earlier physical-Escape attribution.
- M1.1a.2.1 is `implemented_unverified`; 2.2 is `in_progress`; actual game case
  2.3 remains `not_started`. T05/G1 remain `not_run`, T03/G0 remain `fail` for
  Mineflayer/E9E. Native recovery/effects/physical pool/restart/isolation and
  foreign-writer/power-loss guarantees remain open. No inference spend. Continue
  independent code work; desktop probe waits for the user's resume.

### 2026-09-18 — Private native settings bridge and cross-language recovery

- Previous goal turn was progress: native writer implementation and 24 passing
  Java tests. This continuation adds M1.1a.2.4 under F06/F09/F16/N01/N02/N04/N08,
  C10/C11/C12/C15, with partial T01/T05/T06/T07 evidence. Desktop pause remains
  binding; no native desktop tools, game launch or account/inference use occurred.
- [Private Java bridge](java/forge1192-client/src/main/java/io/github/opencnid/strata/client/SettingsHttpBridge.java)
  and [protocol](java/forge1192-client/src/main/java/io/github/opencnid/strata/client/NativeSettingsProtocol.java)
  carry explicit durable transaction IDs. Loopback-only, random per-boot bearer
  and session, exact host/Origin checks, bounded requests/queue/cache, monotonic
  pre-dispatch deadlines and client-thread dispatch fence the development seam.
  It supports snapshot/apply/status/rollback/native release, not commit. Client
  integration is title-screen-only; diagnostics conflict before mutation.
- [Python client/CLI](src/mcbench/native_settings.py) validates connection and
  response schemas, binds result IDs/fingerprint, sends a mutation once and polls
  read-only request status. Uncertain responses never trigger forward replay.
  Connection descriptors are credentials, excluded from source/evidence/gameplay
  packaging. The public Controls planner rejects native `supported=false`.
- Executed pinned Java build/test/reobfuscation: **29 passed**, zero failures or
  errors. Selected Python native-settings/JVM/controls/discovery/packaging suite:
  **47 passed in 6.04s**. Four Python cases launch the actual Java store/HTTP bridge
  with synthetic keys; verify deduplication, explicit status/rollback, forced JVM
  restart, a lost POST acknowledgment and foreign-edit conflict preservation.
  Five Java HTTP tests cover queue/deadline/auth/session/schema/replay/shutdown
  paths; 15 Python cases cover bounds/identity/uncertainty/secret redaction.
- Targeted Ruff passed. Pinned JRE lists `jdk.httpserver@17.0.20.1`; production
  JAR contains no synthetic fixture/test classes. JAR SHA-256:
  `2ce213d9a0866fb9ba83d1957d33965bea63dab9f31d0c3be16f8528b6d96cc5`.
  Private archive: `.strata/evidence/2026-09-18-native-settings-bridge-01/`;
  JUnit XML, build JAR, verification summary, available synthetic journals and
  hashes only, with no connection credential files. The installed client remains
  the earlier discovery-only JAR.
- Follow-up review also sanitized connection-file validation at the Python
  library boundary, preventing exceptions from echoing credential-bearing input.
  The 15 native-client tests were rerun and passed; targeted Ruff and diff checks
  passed. The full 47-test selection was not repeated for this narrow change.
- M1.1a.2.4 is `implemented_unverified`. Authentic native effects/transactions,
  worker restart, process/filesystem isolation, full Controls projection and
  verified commit, charged reconfiguration and scoped gameplay routing remain
  open. T05/G1 stay `not_run`; T03/G0 retain the actual Mineflayer/E9E failure.
  Continue independent integration and qualification preparation while desktop
  is paused; do not treat synthetic process recovery as a game recovery pass.

### 2026-09-18 — Host settings recovery fencing and evidence binding

- Previous goal turn was progress (private bridge plus JVM/HTTP evidence).
  Advanced M1.1c.1/c.2, F06/F09/F16/N01/N02/N04/N08, C10/C11/C12/C15; full
  settings/native/supervisor integration remains c.3. No desktop interaction,
  game launch or model inference occurred; the user's desktop pause persists.
- Corrected two discrepancies against SPEC 8.2: the Python workflow previously
  allowed new repairs after `failed` rollback and accepted unrelated concurrent
  edits while declaring rollback successful. Failed rows now retain profile and
  avatar holds; unrelated changes cause a recovery conflict without overwriting
  them. The earlier synthetic fixture's permissive expectation was corrected,
  not used to amend the specification or claim acceptance.
- Added OS profile-operation locks within the operator store, durable phase CAS,
  policy/qualification/ownership drift fencing, repeated-plan idempotency,
  transaction IDs/directions on adapter writes, final release before publication,
  no-change rejection without restart, and retained/fenced legacy active plans.
  Actual Python subprocess tests exercise lock exclusion and clean/crash release;
  database tests prove a process lock's release cannot clear a failed recovery hold.
- Verification now requires transaction/plan-bound global and per-binding
  before/after-restart checks, including potential competitors and conservative
  GUI/chat/unknown-context coverage. It reads actual proof/source bytes, checks
  their hashes and metadata, bounds proof objects/aggregate read allowance, and
  rejects missing, malformed, replayed, duplicate or unverified-context evidence.
  Production rejects synthetic proofs; simulation mode is durable and cannot be
  reopened as production. Proof producers still need authentic qualification.
- Executed `uv run --frozen pytest tests/test_controls.py tests/test_controls_fencing.py tests/test_storage_controller.py tests/test_checkpoints_artifacts.py -q`:
  **87 passed in 5.70s**, including 37 new workflow/fencing/evidence cases.
  Explicit pinned-Java `tests/test_native_settings_jvm.py`: **four passed in
  5.57s** separately. Targeted Ruff passed. No full Python or Java rerun claimed.
- The private workflow contract is documented in
  [settings-workflow.md](docs/operations/settings-workflow.md). Actual native
  effect/restart/commit, authenticated producer/isolation, action-lane fencing,
  reconfiguration clocks/costs and scoped gameplay routing remain open. T05/G1
  remain `not_run`; T03/G0 retain the authentic Mineflayer/E9E failure. Continue
  those integrations without resuming desktop control until the user does.

### 2026-09-18 — Host settings final recovery review

- Final review of M1.1c.1 found that a failed rollback of a committed transaction
  could lose its original revision restriction on retry. Added a reopened-database
  regression and a no-drift release-retry case; both failed before the correction.
  Failed receipts now retain the committed revision through repeated recovery
  attempts. A newer revision remains fenced even when key values happen to match.
- Executed the two new/extended regressions before the fix: **two failed, 36
  deselected in 0.33s**. After the fix,
  `uv run --frozen pytest tests/test_controls.py tests/test_controls_fencing.py -q`:
  **52 passed in 1.59s**; targeted Ruff passed. This is a narrow follow-up to the
  preceding 87-test selection, not another full suite or JVM run.
- Archived the final synthetic CAS transaction, ten example proof/witness blobs,
  command/result summary and source hashes outside the repository in
  `C:\Users\Darian\.strata\evidence\2026-09-18-settings-workflow-01\`.
  The summary distinguishes recorded results from raw runner output. All archived
  effects are explicitly synthetic; no connection descriptors/credentials were copied.
- Desktop remains paused at the user's request; no app control, game launch or
  inference occurred. Authentic/native/supervisor gates remain unchanged. Next:
  M1.1c.3 action-lane reconfiguration and accounting integration, while retaining
  the native adapter/commit/effect/restart qualification requirements.

### 2026-09-18 — Per-avatar controller/settings repair coordination

- Previous goal turn was progress: corrected and tested durable settings rollback
  fencing. This turn advanced M1.1c.3.1, F06/F09/F11/F16, N01/N02/N03/N05,
  C10/C11/C12/C15/C18; T01/T05/T07/T11/T12 retain aggregate `not_run`.
- Added private [repair coordination](src/mcbench/reconfiguration.py) around
  Controls, Controller, Budgets and CAS. Before-start immutable policy binds
  profiles/condition; cognitive probes cannot enable repair. Request/stop/apply/
  observation phases hold only the affected avatar while the campaign remains
  RUNNING. Stop and readiness evidence bind the transaction, profile, generation,
  old lease, witness bytes and typed post-settings Observation. Actual receipt
  producers and worker-side authority enforcement are still unimplemented.
- Controller action grants require ready avatar authority and its current input
  generation; replacing an input-bearing grant revokes the predecessor. Startup
  read grants survive readiness. Profile/operation uniqueness, phase checks,
  process locks, UTC/monotonic deadlines and database holds prevent concurrent or
  uncertain forward writes. New owner/clock recovery inherits the hold and admits
  rollback only; missing legacy lane authority is not inferred from old tokens.
- Repairs require a scoped reserved tool-budget operation and settlement before
  completion; reused operations, unsettled/unknown costs and exhausted budgets
  cannot authorize resumed input. Overruns remain consumed. Clocks retain full
  team active/reserved exposure and measured ticks, tagging holds at interval
  ingestion without double counting or pretending to know exact repair boundaries.
  Full native usage and telemetry settlement are still c.3.3 work.
- Initial integration selection: **50 passed in 5.50s**. Expanded settings,
  controller, budget, clock and checkpoint selection: **122 passed in 8.29s**.
  Freshness/startup regressions: **32 passed in 2.43s**; after preserving read-only
  startup grants, final repair/controller selection: **52 passed in 4.81s**.
  Gameplay package: **one passed in 0.30s**. Targeted Ruff passed. No full Python,
  Node, Java, live game or provider suite was rerun.
- Archived three actual synthetic test databases/CAS bundles (completed repair,
  interval accounting and interrupted-write rollback), command/result summary
  and source hashes at
  `C:\Users\Darian\.strata\evidence\2026-09-18-reconfiguration-01\`.
  [Workflow contract](docs/operations/settings-workflow.md) and
  [verification report](docs/verification/2026-09-18-long-horizon.md) distinguish
  this operator integration from the absent worker transport/qualified producers.
- No desktop interaction, live profile changes, game launches or inference.
  T03/G0 retain the authentic Mineflayer/E9E failure; T05/G1 stay unrun. Continue
  c.3.2 actual worker authority/stop/recovery transport while desktop remains
  paused. Native settings commit/effects/restart, exact charged intervals, public
  patches, terminal-campaign repair resolution and full isolation remain open.

### 2026-09-18 — User reaffirms API-driven gameplay priority

- User asked why desktop control was needed when the character should use
  Mineflayer or an API. Reaffirmed D01: ordinary benchmark gameplay uses scoped
  `mcgame` calls to a persistent structured backend. Desktop actions performed so
  far served official provisioning/launch and separate Forge Controls discovery;
  desktop-driven gameplay cannot replace the primary structured contract.
- Reinspected the current Mineflayer adapter, FML3 decoder/tests and failed exact
  E9E evidence. The adapter is vanilla 1.19.2; the Forge code only decodes offers
  and does not implement advertised channels, modded registries or a successful
  login. T03/G0 therefore remain failed, not an inferred compatibility pass.
- Reprioritized M0.3 structured API compatibility ahead of further keybinding UI
  work. A Forge API fallback remains a separate backend/system identity allowed
  by SPEC 8.1/16.1; there is no silent Mineflayer support claim or requirement
  removal. Keybinding validation remains required before the full MVP.
- No desktop control, game launch, inference or new runtime test occurred during
  this clarification. The desktop pause persists. Next work: source-backed exact
  Forge compatibility assessment and implementation of the viable structured path.

### 2026-09-18 — D06 native structured Forge observation API

- Advanced M0.3/M0.3b.1a, F01/F06/F16/N04 and C09 through an explicitly separate
  `forge1192-structured-development/1` candidate. Inspected pinned Forge channel
  validation and registry-installation source; selected the fallback already
  authorized by SPEC 8.1/16.1. M0.3 returns to `in_progress` because this workstream
  can advance; M0.3.3 remains `blocked` and the authentic Mineflayer failure remains.
- Implemented native registered-ID/player/menu projection, conservative fixed
  voxel visibility, bounded frozen pagination, session/deadline-fenced private
  HTTP and typed Python operator reads. Split M0.3b.1 into .1a observation/transport
  and .1b ordinary action motor. Only observe/capabilities are supported; no action,
  raw/admin/eval/settings endpoint or campaign admission is advertised.
- Executed pinned Java build/test/classpath generation: **39 Java tests passed**.
  Explicit Python/JVM/settings/packaging selection: **31 passed in 8.98 s**,
  including two actual game HTTP/JVM cases with synthetic geometry and four actual
  settings JVM cases. Initial cross-language run failed one case (29 passed)
  because Java timestamps exceeded public Utc precision; millisecond serialization
  and a regression case fixed it. Targeted Ruff and diff whitespace checks passed.
- [Evidence and exact limits](docs/verification/2026-09-18-forge-game-api.md),
  [runbook](docs/operations/forge-game-api.md). Built JAR SHA-256
  `04a61c4c2a381062e2fc26be2fdf34461971ee2a788b4fe149511c568961f651`;
  not installed. Private reports/source hashes are under
  `%USERPROFILE%/.strata/evidence/2026-09-18-forge-game-api-01/`.
- No desktop interaction, game/server launch, live profile change or inference.
  Read-only .1a is `implemented_unverified` for actual game behavior; no release
  gate closes. Next: M0.3b.2 durable native/public-worker authority, clock/delivery
  receipts, cancellation/ambiguity and charge integration; then .1b ordinary
  actions and .3 authentic expert recipe/container/machine/reference checks.

### 2026-09-18 — Native durable action lane and ordinary Forge motors

- Previous turn was progress: the read-only API changed implementation and yielded
  actual local transport evidence. This turn advances M0.3b.1b/.2, F06/F09/F11/F16,
  N02/N03/N04/N05/N08 and C09/C15/C18 without narrowing the full goal.
- Implemented `GameBatch`, `GameActionLane`, signed coordinate parsing, process
  ownership, immutable authority/body binding, fresh delivered observations,
  epochs/sequences/leases/deadlines, pre-input forced intent and primitive records,
  cancellation/release, retained uncertain attempts and recovery without replay.
  Four ordinary native motors compile: look, dig, block interaction and inventory
  clicks. Source uses normal player APIs and reports `emitted`, never fake task
  completion. All other action variants remain visible .1b.2 work.
- Review found that an already queued new lease could cross stop-all; rotating
  fence tokens now reject it. Urgent cancellation has reserved queue capacity and
  precedes motor dispatch. Read-only observations no longer increment state revision
  solely because they are reread. Journal failures cannot suppress safety release;
  missing release evidence remains unknown/unhealthy.
- Executed pinned Forge client build: **56 Java tests passed**, including 16 lane
  cases. Explicit Python/JVM/settings/package selection: **38 passed in 15.86 s**,
  zero skipped, including six actual game HTTP/JVM cases with synthetic runtime
  and four settings JVM cases. Actual synthetic process kill/lost-ack/status/stop
  tests pass; retained state is not a Minecraft/world-restore claim. Targeted Ruff
  and diff whitespace checks passed. No unrelated full suites or paid runs.
- [Evidence](docs/verification/2026-09-18-forge-game-actions.md),
  [operator contract](docs/operations/forge-game-api.md). Built JAR SHA-256
  `14b24422f18ca155cca7788d105a70e2e7440bc723269a7e166b703955a2214b`,
  not installed. Private reports/source hashes:
  `%USERPROFILE%/.strata/evidence/2026-09-18-forge-game-actions-01/`.
- Desktop remains paused. No Minecraft launch/profile change, account interaction
  or inference. Native .1b.1/.2a are `implemented_unverified` for authentic effects;
  M0.3b stays partial, T03/G0 retain the Mineflayer failure and no gate closes.
  Next: .2b scoped public worker plus asynchronous confirmed release and identity/
  observation mapping; .2c full charges/clocks, watchdog/storage/isolation; then
  remaining motors and authentic exact-pack conformance.

### 2026-09-18 — Confirmed asynchronous worker release

- Continued background API work while desktop control remains paused. Split
  M0.3b.2b into .2b.1 stop/release/shutdown and .2b.2 native worker routing before
  claiming partial coverage. Affects F06/F09/F16, N02/N05/N08, C09/C15,
  partial T01/T07 and the still-open G0/G1/G2 contracts.
- `Backend.stop()` now permits a confirmation promise. The worker retains its
  active mutation until confirmation, waits in HTTP cancel/stop-all, fences idle
  and queued work, and shares a pending release across cancellation and shutdown.
  Timeout/rejection/blocking past 250 ms yields unknown/unconfirmed release;
  late resolution cannot upgrade the terminal receipt. No action is replayed.
- Worker shutdown drains before closing SQLite. Failed release or terminal
  evidence prevents clean close and a success exit. Capability contract minor 5
  pins the changed implementation and `confirmed-local-release/2` policy.
- Ran `npm test`: **74 passed**, zero skipped, before the final clean-close and
  journal-failure refinements. Final `npm run build` and action/HTTP/CLI selection:
  **29 passed**, zero skipped, including eight added cases. Gameplay-package
  test **1 passed**; whitespace check passed with existing CRLF notices only.
  [Report](docs/verification/2026-09-18-worker-release.md); private command/result
  metadata and source hashes under
  `%USERPROFILE%/.strata/evidence/2026-09-18-worker-release-01/`.
- No desktop input, Minecraft launch, live profile/JAR change or inference.
  M0.3b.2b.1 remains `implemented_unverified` for authentic backend behavior;
  .2b stays `in_progress`. Next: .2b.2 private native transport, asynchronous
  observations/delivery, full actor/body/capability/batch binding and public
  receipt mapping; .2c retains aggregate clocks/charges and external client kill.
  Both profiles' real conformance, remaining motors and every existing gate remain.

### 2026-09-18 — Scoped Forge worker/CLI routing

- Continued the active goal in background code/JVM tests while desktop control
  remained paused. The preceding goal turn made concrete release/shutdown progress.
  M0.3b.2b.2 now uses an explicit Forge configuration through the existing
  supervisor, shared actor-scoped gateway and unchanged `mcgame` CLI. Mineflayer
  remains the vanilla default; E9E's failed Mineflayer handshake is unchanged.
- Added `ForgeLane`, bounded private Node transport, worker factory/config and
  separate capability identity. Verify loaded immutable authority, body and
  generation before arm; atomically tag native observations with identity. Pin
  all compiled broker modules and retain native/public source clocks separately.
  Public grants do not contain native credentials or expose operator operations.
- Journal the public projection and delivery; keep one native action POST and
  status-only recovery. Native input-only receipts remain `emitted`; uncertain
  action/release stays unknown and fenced. Reconcile cumulative attempted native
  primitives, including safety releases, into local counters without refunds or
  duplicate charges across epochs. Split .2c into local broker accounting (.1),
  controller/aggregate/clock qualification (.2), and external client process/
  archival/isolation (.3), preserving every original requirement.
- Final strict TypeScript build and full Node suite: **90 passed**, zero skipped,
  including 15 Forge tests, 12 using actual synthetic JVMs/HTTP. Actual supervisor/
  worker wall-limit drain, second-broker denial, old-epoch retention, a killed JVM,
  lost response/no replay, hidden fields and body/generation mismatch were checked.
  Pinned Forge build: **58 Java tests passed**. Explicit Python native/JVM/gameplay
  package selection: **21 passed**, zero skipped. Targeted Ruff and whitespace
  checks passed. [Evidence](docs/verification/2026-09-18-forge-worker.md) and
  [operator workflow](docs/operations/forge-game-api.md).
- Private logs/JUnit/XML/source hashes retained under
  `%USERPROFILE%/.strata/evidence/2026-09-18-forge-worker-01/`. Built JAR SHA-256
  `645ddf1b6968b1c53e5dbea0da0aa96bab7301db566a3c5710624a9a754ac5b0`;
  not installed. No desktop input, Minecraft launch, account flow or inference.
- .2b.2/.2c.1 are `implemented_unverified` for authentic behavior; M0 remains
  incomplete and campaign admission false. Next: .2c.3 independent process-bound
  Forge client watchdog; .2c.2 controller/aggregate integration; remaining eight
  native motors and authentic exact-pack conformance. Keybinding/model/isolation/
  soaks/team/research and later-pack gates retain their full original scope.


### 2026-09-18 — Independent Windows Java process lifetime guard foundation

- Continued authorized background implementation while desktop control stayed
  paused. Answered the E9E compatibility question: the observed Mineflayer case
  fails at Forge login negotiation, before expert mechanics; vanilla evidence
  remains partial. No scope waiver or failed-gate relabeling.
- Split M0.3b.2c.3 into .3a exact-process/lease foundation, .3b worker/native
  session/client-thread health integration, and .3c archival/launch/isolation
  qualification. .3a is now `implemented_unverified` for authentic deployment;
  its parent remains `in_progress`. A private grant and held Windows handle bind
  PID, full-precision creation time, executable path/hash before attaching a
  kill-on-close Job Object. Second guard ownership is denied without harming the
  existing owner. Bounded challenge leases, immutable expiry/wall limits and
  separate pipe IO threads fence failed supervision. No cached-PID kill/replay,
  detach path or claim of clean game/input release was introduced.
- Checks: test-only Java fixture compiled against the pinned classpath; final
  **24 selected Python tests passed**, zero skipped, in 23.73 s (17 new guard,
  six shared process wrapper, one gameplay package). Hung disposable JVM plus
  silent supervisor exited in **1516 ms**; pipe/crash faults in **15–32 ms**.
  Sibling and stale/replacement identity negatives passed; a post-attachment
  descendant exited with no late synthetic effect. Targeted Ruff and whitespace
  checks passed. Initial 2/15 failures exposed an incorrect test assumption that
  forced Windows job termination must return nonzero; exit code zero is possible
  and is never treated as an input-release or clean-checkpoint receipt.
- Files: `src/mcbench/process_guard.py`, shared `processes.py` handle attachment,
  `tests/test_process_guard.py`, test-only `ProcessGuardFixture.java`, and
  [operator workflow](docs/operations/process-guard.md)/
  [verification report](docs/verification/2026-09-18-process-guard.md). Private
  JUnit/log/timing/source-hash evidence is under
  `%USERPROFILE%/.strata/evidence/2026-09-18-process-guard-01/`.
- IDs advanced: partial F09/N01/N02/N05/N08, C15/C30, T01/T06/T07; no aggregate
  suite/gate passes. No Minecraft launch, desktop input, live JAR/profile edit or
  inference. The existing Node route is not yet protected by this standalone
  guard. Next: .3b bind native listener/session and health to guarded ownership
  before arming, coordinate worker/controller faults and retain durable terminal
  evidence; .3c deployment/archival/isolation and .2c.2 aggregate grants/costs.
  Remaining motors, authentic E9E conformance, keybinding/model/soak/team/research
  and later-pack work remain required.


### 2026-09-18 — Guarded Forge worker with independent native health and process-chain faults

- Continued the active M0–M6 goal with desktop control paused. Advanced
  M0.3b.2c.3b to `implemented_unverified` for authentic deployment; parent M0 and
  the cross-cutting .2c work remain incomplete. The standalone guard is now
  connected to the version 2 Forge development worker: exact process/listener,
  native descriptor/session, loaded authority and body-generation checks precede
  arming; independent authenticated client-thread health reads detect a frozen
  JVM even while Node remains responsive. Old Forge worker v1 config rejects;
  vanilla remains unchanged. No automatic backend or guard bypass was introduced.
- Added `src/mcbench/forge_guard.py`, the Node guardian/evidence adapter and
  worker/factory/config/capability integration; refined the existing guard's
  readiness hooks. Required guard policy/Python/source pins enter capability
  identity. Bounded private `SupervisorEvent/1` frames retain a source clock,
  hash chain and forced readiness before child configuration, plus exit/fault
  evidence. Process termination remains distinct from release confirmation;
  incomplete parent-crash evidence cannot establish a clean checkpoint.
- Verification: pinned test-only Java fixture compile passed. Full Node run:
  **95 passed**, no skips, 51.437 s. Selected Python native/guard/process/package
  regressions: **51 passed**, no skips, 44.78 s. After final admission and clocked
  evidence refinements, **20 Forge Node tests passed**, no skips, 48.779 s.
  Final native freeze/worker kill/worker hang/parent kill measurements were
  **1466/45/1922/31 ms** to JVM exit. All four retained one action intent with no
  replay. Listener/sibling/active-owner/mismatched-grant negatives passed; normal
  shutdown verified private log hashes and termination/release separation.
  Targeted Ruff and whitespace/Markdown/ledger checks passed.
- Initial integrated normal-stop failure was traced to discarding a challenge
  before the worker's first heartbeat. The adapter now retains that one challenge
  until a fresh heartbeat permits the answer; its original deadline is unchanged.
  All affected cases were rerun. No authentic failure was relabeled as success.
- IDs advanced: partial F06/F09/F16, N01/N02/N03/N04/N05/N06/N08,
  C03/C09/C15/C18/C30, T01/T03/T06/T07/T12/T13. [Evidence](docs/verification/2026-09-18-forge-guard-integration.md),
  [operator contract](docs/operations/process-guard.md). Private logs/JUnit/timings
  and 13 changed-source hashes are retained under
  `%USERPROFILE%/.strata/evidence/2026-09-18-forge-guard-integration-01/`.
- No Minecraft launch, live JAR/profile change, desktop input or inference.
  Genuine Forge/E9E validation, controller generations/repair/aggregate accounting,
  complete process-tree launch containment, installed runtime pins, archival/disk
  recovery and actual isolation remain unqualified. T03/G0 retain the failed
  Mineflayer/E9E result; no gate closes. Next: remaining eight native motors
  (M0.3b.1b.2) through this guarded development route; retain .2c.2/.3c and all
  keybinding/model/soak/team/research/later-pack gates as required work.

### 2026-09-18 — Native item/entity/chat gestures with selection and identity fences

- The preceding discussion turn clarified the Mineflayer/E9E login failure but
  made no implementation progress. Revalidated current files and resumed M0's
  authorized implementation with desktop control paused. Split M0.3b.1b.2 into
  .2a gestures and .2b movement/place/equip/craft; .2a is now
  `implemented_unverified`, while .2b remains `not_started`. No original action,
  modded mechanic, milestone or acceptance gate was removed.
- Added `GameGestures` and pinned native `useItem`, `attack`, `interactAt`/
  `interact` and signed-chat dispatch. Held use starts once, charges continuing
  ticks and releases on cancellation/exhaustion; tick-START processing plus a
  Forge input hook prevents implicit repeated use. Entity input requires a
  delivered opaque identity, fresh visibility/reach/native ray checks and checks
  after aiming and the mod hook. Chat allows bounded Unicode text and rejects
  commands/control/format codes/malformed surrogates. Native effects are still
  input-only `emitted`, with existing unknown/no-replay/release semantics.
- Private captured selection fences prevent unchanged inventory slots from
  authorizing use after a hotbar change; each page retains its scene's fence.
  Salted entity UUID digests reject recycled numeric IDs without exposing raw
  UUIDs. Capability minor 7 and observation policy revision 2 bind Java/TS/Python
  consumers to the new motor/identity rules. Local units are explicitly declared;
  complete controller/aggregate model/body/clock accounting remains separate.
- Executed pinned client test/build/reobfuscation: **67 Java tests passed**.
  TypeScript build and full Node suite: **96 passed**, zero skipped, 49.775 s.
  Selected Python native/JVM/guard/process/package run: **48 passed, one failed**,
  zero skipped, 44.20 s. The new Unicode test exposed a Windows default-encoding
  reader; explicit UTF-8 fixture/journal reads fixed it. All affected JVM/guard
  cases reran: **17 passed**, zero skipped, 23.26 s. Existing xunit2 property
  warnings retained. Targeted Ruff passed. Tests use synthetic runtime ports and
  disposable test JVMs; they do not claim authentic game effects or latency.
- IDs advanced: partial F01/F06/F09/F11/F16, N02/N03/N04/N05/N06,
  C09/C15/C18, T01/T03/T06/T07/T12. [Evidence](docs/verification/2026-09-18-forge-gestures.md)
  and [updated operator contract](docs/operations/forge-game-api.md). Private
  logs/XML/source and rebuilt-artifact hashes are retained under
  `%USERPROFILE%/.strata/evidence/2026-09-18-forge-gestures-01/`.
- No Minecraft/client launch, live JAR/profile edit, desktop input or inference.
  T03/G0 preserve the failed Mineflayer/E9E result; authentic Forge T03 is unrun.
  Next: .2b movement/place/equip/craft, then exact modded metadata/recipes/menus/
  machines/quests, while retaining .2c.2 controller/aggregate and .2c.3c isolation/
  deployment work. All M1–M6 model/keybinding/soak/team/research/later-pack gates
  remain required and the long-running goal remains active.

### 2026-09-19 — Native equipment, initial placement and server-menu feedback

- Continued after the prior gesture implementation, which was concrete progress.
  Revalidated code/ledger/SPEC and kept desktop control paused. Split
  M0.3b.1b.2b into placement/equipment, navigation and recipe/craft children.
  Equipment/menu feedback (.2b.1a) is `implemented_unverified`; complete placement
  (.2b.1b) remains `in_progress` with the initial observed-air route implemented.
  Movement and crafting remain `not_started`, not waived or renamed complete.
- Added `GameInventory`, `GameMenuFeedback`, `GamePlacement` and private
  `NativeWindowSync`; wired ordinary placement/equipment calls and upgraded
  `click_slot` to wait for real full-menu responses. Fixed pickup/destination/
  optional return clicks verify source/cursor/slot permissions and capacity,
  conservation and applied server state before continuing. Private component
  comparisons include Forge capabilities, with a per-item bound; public state
  gains no raw NBT, hidden container contents or arbitrary packet API.
- Pinned native-source inspection established the fixed negative-slot
  `PICKUP_ALL` refresh mechanism: no transfer branch for slot -999, state-ID
  mismatch requests full contents. This is source evidence, not a live no-op
  pass. The observer retains at most one callback per current-menu request;
  cancelled/stale/replaced/unapplied replies cannot resume a motor. Inventory
  uncertainty survives cancellation/rearming until server reconciliation.
  Missing feedback may require a new connection and classified recovery; the
  action is never replayed automatically. Receipts remain input-only `emitted`.
- Capability minor 8 pins ten actions, fixed menu feedback and explicit charged
  click/refresh/active-wait units. Placement checks delivered support/adjacent
  air, held block item, native hit face and Forge reach. Qualified replacement,
  interactive-support/crouching and actual modded placement effects remain open.
  No native method compilation or synthetic fixture is treated as game success.
- Executed: final pinned client test/build/reobfuscation **85 Java passes**;
  TypeScript build; targeted Forge Node suite **21 passes**, zero skipped,
  50.718 s; selected Python native/JVM/guard/package suite **34 passes**, zero
  skipped, 27.36 s. Source-scoped Ruff passed. One existing xunit2 property
  warning remains. Synthetic native-freeze/worker-kill/worker-hang/parent-kill
  guardian cases stopped the JVM in **1411/37/1932/30 ms**, one intent/no replay.
  New pure motor/feedback tests cover predictions/rejections/resource changes,
  cursor conservation, bounded equipment, missing feedback, stale/cancelled/
  unapplied callbacks and strict placement/equipment preconditions.
- Partial IDs advanced: F01/F06/F09/F11/F16, N01/N02/N03/N04/N05/N06,
  C09/C15/C18, T01/T03/T06/T07/T12. [Evidence](docs/verification/2026-09-19-forge-inventory-placement.md)
  and [operator contract](docs/operations/forge-game-api.md). Private logs/XML and
  source/JAR hashes are retained under
  `%USERPROFILE%/.strata/evidence/2026-09-18-forge-inventory-placement-01/`,
  retaining this task's start date across the local-date rollover.
- No game launch, live JAR/profile edit, desktop input or Strata inference job.
  T03/G0 retain the actual Mineflayer/E9E failure; authentic Forge T03 is unrun.
  Next: delivered-map movement (.2b.2), player-accessible recipes/crafting (.2b.3),
  remaining placement and exact-pack mechanics; continue controller/aggregate
  accounting and deployment/isolation without dropping the full M0–M6 goal.

### 2026-09-19 — Resumed desktop validation and authentic JarJar startup fix

- User explicitly renewed desktop control authorization. Revisited SPEC 3/8/16–19
  and the current M0/M1 contracts; deployed the previously tested ten-action JAR
  to the dedicated E9E profile with private original JAR/profile/options backups.
  Enabled only the private read-only game bridge through the official launcher's
  pinned Java 17 configuration. No account dialog, security setting, publication
  or model inference was automated.
- First actual boot failed before endpoint creation: Forge JarJar's
  `PathPath.toRealPath()` returns null, invalidating the host-file validator used
  by loaded-artifact hashing. Added `ArtifactFiles` for bounded reads of the
  loader's actual host/Union/JarJar entry bytes; writable settings/journal paths
  explicitly reject non-default filesystems. Both native fingerprints include
  the revised hash policy. The initial crash and regression-test failures remain
  in the private evidence. No failed attempt was relabeled as a pass.
- Final pinned Gradle test/build/reobfuscation/classpath generation passed:
  **91 Java tests**, zero failures/errors/skips, including six provider/path cases.
  Explicit-JVM native game/package checks passed **27 Python tests**, zero skipped,
  19.00 seconds. Targeted Ruff and whitespace checks passed. No broad Node or full
  Python rerun. Deployed corrected JAR SHA-256
  `c2218c6c9ae2e1e4a7e6f216d9fd16f084404d38bcebf0f47ccca17a24f462ce`.
- Actual corrected E9E title screen loaded 240 mods and exposed the read-only
  endpoint. `tools/check_forge_observations.py` passed six disconnected/read-only
  assertions and ten transport assertions, with exact checker source/hash and
  private raw results. Missing/wrong auth, browser Origin, foreign Host, wrong
  session, expired deadline and cross-protocol schema requests reject. These
  checks do not qualify OS isolation, gameplay observations or game actions.
- A Windows Security firewall prompt for Java blocked the direct-connection
  click. Requested user handling under the computer-use skill; no security
  dialog input was sent. Both bounded server attempts reached ready and stopped
  normally with complete logs, exit 0, no forced termination (150.515 and 245.031
  seconds). The client remains at the disconnected multiplayer screen with the
  prompt and read-only authority. No world join, game mutation or inference.
- Partial IDs: M0.3b.1a/.1a.1/.1a.2, shared M1.1a.2.2,
  F01/F05/F06/F16, N01/N04/N06, C04/C09/C10, T01/T02/T03/T06.
  [Report](docs/verification/2026-09-19-forge-live-api.md); private archive
  `%USERPROFILE%/.strata/evidence/2026-09-19-forge-live-api-01/` (credential-bearing
  `bridge/` excluded from exports). T03/G0 preserve the Mineflayer/E9E failure;
  no authentic body/action gate closes. Next: continue delivered-map movement
  and player-accessible crafting; restart the bounded server and exercise
  connected native observations once the user clears the security dialog.

### 2026-09-19 — delivered-map movement authority

- M0.3b.1b.2b.2a now retains immutable native states from filtered captures and
  promotes only durably delivered pages. Four captured scenes and 1,024 delivered
  cells have independent bounds; stale/conflicting metadata rejects atomically.
  Connection/body changes and lane rearming clear this state. Journal or promotion
  failure cannot silently grant authority. Movement remains unsupported.
- Pinned client Gradle tests/build passed **103 Java tests**, zero failures/skips;
  scoped synthetic worker/JVM checks passed **21 Node tests** and selected native
  client/package checks passed **27 Python tests**, zero skips. Final JAR SHA-256
  `b1601850dde8e43f6fc76b2b7c00ef262349ebafa426588c7fe537642dbcd98d`
  is built but not installed. [Report](docs/verification/2026-09-19-forge-delivered-map.md)
  and private logs/XML/source manifest under
  `%USERPROFILE%/.strata/evidence/2026-09-19-forge-navigation-01/` retain exact scope.
- Partial F01/F06/F09/F16, N01/N02/N04/N06/N08, C09/C15 and T01/T03/T06/T07;
  no authentic gate closes. A read-only screenshot confirmed the existing client
  and Windows Security prompt; no desktop input, live installation change or
  inference occurred. Next implement .2b collision/planning using delivered cells,
  then .2c native controls/cancellation/tick charging and player-accessible crafting.

### 2026-09-19 — bounded native route preparation

- Split M0.3b.1b.2b.2b into initial level-walking/collision candidate (.1) and
  broader geometry/loaded-pack qualification (.2). GameRoute uses a fixed bounded
  search with swept clearance and continuous footprint support. NativeCollisionView
  has copied delivered states, explicit ID/class/physics checks, age bounds and
  no Level/Entity/block-entity fallback. NativeGameRuntime.planMove uses the same
  capture clock and standing/grounded survival preconditions. No `move_to` action
  is advertised; steps, jumps, fluids and unqualified block types reject.
- Final pinned Gradle tests/build/reobfuscation passed **115 Java tests**, zero
  failures/errors/skips, 22 seconds. New coverage: eight synthetic geometry and
  search-bound tests, three native-view boundary tests and one clock test.
  Initial plain-JUnit game bootstrap failed because Forge's runtime-transformed
  NetworkEvent constructor was absent: 111 tests passed and one initialization
  failed. The failure/source/XML remain private evidence, not a native pass.
- The real-shape assertions now live in an explicit, operator-only 13-case
  ClientCollisionProbe that runs after actual Forge loading. It is **unrun**;
  even success would qualify only native shape conversion on constructed inputs,
  not authentic observed routes, movement effects or timing. Final JAR SHA-256
  `7f30ca7496ee25102c759be3da75ac0f858edfc16e08f6246032fdb65432e0a4`
  is built but not installed. [Report](docs/verification/2026-09-19-forge-route-planning.md);
  private evidence `%USERPROFILE%/.strata/evidence/2026-09-19-forge-navigation-02/`.
- Partial F01/F06/F09/F16, N01/N02/N04/N06/N08, C09/C15, T01/T03/T06/T07;
  all larger gates retain their status. No new Node/Python suite, desktop input,
  live profile change, game launch or inference. The pending Windows Security
  prompt requires user handling. Next connect ordinary controls, charged ticks
  and interruption/release to the existing lane; execute native probe/connected
  observations when UI work can resume, then finish crafting and modded mechanics.

### 2026-09-19 — ordinary native movement and charged interruption

- M0.3b.1b.2b.2c.1 now connects the level route to ordinary forward KeyMapping/yaw,
  eight neutral ticks before each new press, coasting and settled turns. Exact
  input classes/settings, logical input agreement, own state/health/absorption,
  collision/ground, body ticks, displacement and progress are rechecked. Short
  corridors use delivered states and their original ages only. No raw-world
  replanning, automatic sprint, block edits, teleport or momentum reset is added.
- Java/TypeScript/Python and capability minor 9 advertise eleven development
  actions and explicit navigation/collision/movement policies. `move_to` accepts
  at most 30 seconds and strict finite tolerance; other actions retain 10 seconds.
  All active neutral/coasting/walking decisions and safety release are charged.
  Existing durable intent, cancellation, lease/deadline and budget fencing remain
  authoritative; input-only receipts do not assert server completion.
- Final Gradle client tests/build/reobfuscation: **126 Java tests passed**, zero
  failures/errors/skips, 21 seconds. Eleven new tests cover toy trajectories and
  the real durable lane with a synthetic walking body, including release on
  cancellation/deadline/damage/exhaustion and no duplicate intent. TypeScript build
  passed; **21 Forge Node tests passed** in 41.781 seconds, and **28 selected Python
  tests passed** in 17.59 seconds with the explicit pinned JVM. Movement envelopes
  reach actual JVM fixtures once; their game effects remain synthetic. Guard
  injections stopped disposable JVMs in 492/42/1738/25 ms, not Minecraft timings.
  Targeted Ruff and whitespace checks passed. Final exact-KeyMapping restriction
  was followed by the final Java rerun; native behavior still needs live evidence.
- [Report](docs/verification/2026-09-19-forge-movement.md); private logs/XML/source
  hashes under `%USERPROFILE%/.strata/evidence/2026-09-19-forge-movement-01/`.
  Final JAR `e0d658a7b2a1dc7421e55b75eb781caa2afb358d3e1115b20f7cbb643f6e562e`
  is not installed. A fresh read-only window capture confirmed the old client
  and Windows Security prompt; no desktop input, live profile change, new game
  launch or inference. The pending user handling request remains unchanged.
- Split authentic qualification into M0.3b.1b.2b.2c.2, still `not_started`.
  Affected F01/F06/F09/F11/F16, N01/N02/N03/N04/N05/N06/N08, C09/C15 and
  T01/T03/T06/T07/T12 remain partial. Current position was condensed; historical
  checks/failures and requirement/gate rows remain in this ledger and reports.
  All larger milestones/gates retain their scope. Next: player-accessible
  crafting/expert mechanics and remaining placement work; deploy and qualify
  native shapes/observations/movement when the security prompt is cleared.


### 2026-09-19 — player-unlocked recipes and native single-recipe crafting

- Advanced M0.3b.1b.2b.3.1/.2 to `implemented_unverified`; retained .3.3 authentic
  expert source/serializer/effects qualification as `not_started`. NativeRecipes
  uses actual player-known book entries and exact native recipe/ingredient classes;
  GameRecipes projects bounded sorted pages with visible-catalog revisions. No
  hidden recipe manager dump, vanilla recipe substitution or raw components.
- GameCrafting/native port uses ordinary recipe-book fill, then confirmed exact
  grid/output/consumption/remainders and bounded ordinary slot transfers. Initial
  empty grid/cursor and reserved empty own-inventory capacity are conservative
  restrictions. Recipe/menu/selection changes stop continuation. Cancellation,
  deadline and budget tests retain grid/cursor effects and avoid blind replay.
- Updated GameBatch, GameActionLane, NativeGameProtocol, scoped Forge broker,
  public async recipe routing and typed Python transport. Twelve actions and
  capability minor 10 identify the recipe/crafting policies; old manifests reject.
  Native source/body-generation binding and response-field/bounds negatives are
  covered synthetically. Campaign admission remains disabled.
- Executed pinned Gradle client test/build/classpath: **144 Java passed**, zero
  final failures/errors/skips, final build 21 s. TypeScript build and targeted Ruff
  passed. Explicit-JVM/guardian **23 Forge Node passed** in 43.369 s, zero skips;
  existing freeze/worker-kill/worker-hang/parent-kill disposable JVM cases stopped
  in **511/45/1741/24 ms**, one intent/no replay. Explicit-JVM selected Python
  suite **38 passed** in 19.25 s, zero skips. Synthetic game effects are labeled.
- Retained failed attempts: one Python test caught overridden result-count bounds
  (fixed with strict bounded integer fields); final review also rejected numeric booleans. Two Java lane test assertions ran
  before deferred start (fixture clock corrected, assertions preserved). Actual
  native recipe-book/mod-hook/resource and menu feedback ordering are untested.
- Private logs/XML/JAR/source hashes are under
  `%USERPROFILE%/.strata/evidence/2026-09-19-forge-crafting-01/`; public report:
  [crafting evidence](docs/verification/2026-09-19-forge-crafting.md). Built JAR
  `287a2c21cbcfa2855cebbd46c759df174c2fe51607e43db854ceaaedb593dcc2`
  is not installed. No inference or game/server launch occurred. Fresh read-only
  desktop capture still showed the Windows Security prompt over the old client;
  no input sent, pending user handling unchanged.
- F01/F06/F09/F11/F16, N01/N02/N03/N04/N05/N06/N08, C09/C15 and
  T01/T03/T06/T07/T12 retain partial coverage. No release gate or M0–M6 closes.
  Next: deploy/qualify native shapes, connected state, movement and crafting when
  the prompt clears; continue remaining placement/menu/custom-recipe/machine
  work independently. Full controller/aggregate accounting, isolation, native
  host, soaks, simultaneous capacity and research milestones remain required.

### 2026-09-19 — D07 explicit close and inventory lifecycle

- Added SPEC v0.2.1 clarification D07 for the missing ordinary `close_window`
  action. Opening a menu had stranded Forge movement, which correctly requires
  a closed screen. Explicit current-window/revision closing now has its own
  strict contract, generated schemas and capability version; movement does not
  close menus implicitly. No requirement or gate was removed.
- Split M0.3b.1b.2b.1c into candidate .1 (`implemented_unverified`) and authentic
  qualification .2 (`not_started`), including the Mineflayer M0.2e counterpart.
  GameMenuClose/native port and Mineflayer closeMenu preflight cursor/grid return
  capacity using private item identity and own inventory; existing offhand may
  merge, empty offhand/armor are not implicit destinations. Ordinary close and
  full own-inventory feedback must conserve resources and leave armor unchanged.
  Unsupported menus/stacks, stale windows/revisions, loss/gifts/components,
  menu replacement and interrupted feedback reject or preserve uncertainty.
- Thirteen-action policy / Forge minor 11 / Mineflayer minor 6 are synchronized
  across Java/TypeScript/Python. Close/refresh/active waits are charged; native
  release remains reserved. No blind reopen/replay, refunds or invented cleanup.
  Complete aggregate controller accounting remains open.
- Executed pinned Gradle test/build/reobfuscation/classpath: **153 Java passed**,
  no failures/errors/skips, build 24 s. Full explicit-JVM/guardian `npm test`:
  **107 Node passed**, zero skips, 44.407 s; TypeScript build passes. Selected
  explicit-JVM Python contract/record/native/package suite: **95 passed**,
  zero skips, 21.67 s; targeted Ruff passes. Native compile/bytecode and scripted
  Prismarine/JVM menu feedback are source/synthetic evidence, not game effects.
- Retained failed attempts: invalid typed NBT test-fixture field corrected;
  Node feedback delay wrapped the cancellation reason in AbortError, now fixed
  to propagate the original reason without weakening the assertion. Final full
  suite passes. Disposable JVM freeze/worker-kill/worker-hang/parent-kill stops
  measured **505/42/1731/24 ms**, one native intent/no replay, not Minecraft timing.
- Private evidence: `%USERPROFILE%/.strata/evidence/2026-09-19-menu-close-01/`;
  [public report](docs/verification/2026-09-19-menu-close.md). Built JAR SHA-256
  `7b14b6b8546e43377667e5122ee03c060480676c54c65ea8f88c561cbace304b`
  remains uninstalled. A fresh read-only capture still showed the Windows
  Security prompt covering the old client; no desktop input, new game/server
  launch or Strata inference. Pending user handling is unchanged.
- F01/F06/F09/F11/F16, N01/N02/N03/N04/N05/N06/N08, C09/C15 and
  T01/T03/T06/T07/T12 retain partial coverage. T03/G0 retain the actual
  Mineflayer/E9E failure; no aggregate gate or M0–M6 closes. Next: remaining
  placement/full geometry/custom recipe/menu/machine work, then authentic close
  and resource/reference qualification alongside pending native live tests.

### 2026-09-19 — authentic vanilla close/cursor/grid return

- Advanced M0.2e / M0.3b.1b.2b.1c.2 with the official vanilla 1.19.2 server,
  authenticated survival worker and ordinary scoped API actions. Empty close,
  cursor seed return, crafting-grid seed return and duplicate terminal receipt
  pass in the final attempt. Six accepted actions retained 18 primitive events;
  31 assertions include repeated connected-state checks. Final saved player NBT
  after normal shutdown independently confirms exactly the original one seed
  in hotbar slot 0, no other items, survival and non-operator status.
- Attempt 1's operator checker used the wrong UTC form; schema rejection occurred
  before acceptance, zero primitives. Corrected the fixture only. Attempt 2's
  CLI completed close and pickup, then received REVISION_CONFLICT before its
  cursor-close acceptance; two actions/six primitives retained. The final attempt
  used the same scoped public API directly. No uncertain action was replayed;
  each predecessor was fenced and its authenticated connection absent before
  the next worker began. All journals/attempts remain private and costs retained.
- Recorded M0.2h for CLI freshness diagnosis/qualification; the successful direct
  API test does not silently substitute for full native host/CLI conformance.
  No production behavior, clock, revision or acceptance requirement was relaxed.
- Bounded server ready/clean stop: 337.032 s, exit 0, complete logs, no force.
  All three worker supervisors exited 0. No desktop input, admin gameplay,
  resource grant, model inference or campaign admission. Windows Security still
  covers the E9E client; no new Forge JAR installed or connected close case run.
- [Live report](docs/verification/2026-09-19-vanilla-menu.md). Private evidence:
  `%USERPROFILE%/.strata/evidence/2026-09-19-vanilla-menu-server-01/` and
  `2026-09-19-vanilla-menu-01/` through `-03/`; the last includes all journal
  copies, source hashes, saved player file and bounded inventory-only report.
  Resources/account identifiers/grants remain outside the source repository.
- Full external-menu/component/capacity/interruption/reference cases and all
  E9E close qualification remain open. T03/G0 retain Mineflayer/E9E failure;
  no aggregate gate or milestone closes. Next: diagnose CLI freshness while
  continuing remaining placement/custom mechanics and pending Forge live tests.

### 2026-09-19 — body revision repair and authentic CLI freshness

- Advanced M0.2h.1 to `implemented_unverified`; full native host/body-transition
  qualification remains M0.2h.2. Pinned Mineflayer physics emits `move` for idle
  one-second position heartbeats; the adapter previously incremented its state
  revision on every such event. Added exact body identity/dimension/pose/velocity/
  ground sampling on physics/movement/spawn and before fresh snapshots. No epsilon,
  timestamp refresh, revision bypass or automatic action replay was introduced.
  Independent inventory/window/cursor/health/recipe fences remain unchanged.
- Mineflayer capability minor 7 identifies `exact-body-pose-motion-ground-dimension/1`.
  New synthetic tests cover idle/duplicate events, all tracked fields, tiny changes,
  returning to old coordinates, invalid numbers, replacement/missing bodies,
  cleanup and actual ActionLane state/age rejection. TypeScript build passes;
  34 focused Node tests pass, then **112 full Node tests pass**, zero failures/
  skips, 47.531 s, with explicit JVM/guardian fixtures. Gameplay package test:
  **1 Python pass**, 0.41 s. No Java source/build change was required.
- Authentic official vanilla 1.19.2 scoped CLI test deliberately waited 1.1 s
  across an idle heartbeat, then acted using that observation successfully. An
  actual look invalidated the old revision, and 2.1 s age rejected a stable idle
  observation. Empty/cursor/grid close and duplicate checks then passed using
  separate CLI processes. Eight accepted actions, two expected pre-acceptance
  negative requests, **23 primitive events**; 38 assertions include repeated
  connectivity checks. Saved server NBT confirms exactly the original one seed,
  survival and non-operator status. This is partial real conformance, not a campaign.
- The official bounded server stopped cleanly at 96.813 s, exit 0, complete logs,
  no force; its bounded worker also exited 0. No desktop input, admin gameplay,
  resource grants, model inference or Forge deployment. Private logs/source/
  journal/NBT evidence: `%USERPROFILE%/.strata/evidence/2026-09-19-body-revision-01/`,
  `2026-09-19-body-revision-server-01/` and `2026-09-19-body-revision-live-01/`.
  [Report](docs/verification/2026-09-19-body-revision.md). Prior failed attempts remain;
  the exact old CLI rejection lacks telemetry proving a unique cause, so its
  attribution is qualified separately from the demonstrated heartbeat defect.
- No complete T03/T04 or release gate passes. M0–M6 remain open, M7 conditional.
  Continue remaining placement/custom mechanics and native host integration,
  with authentic E9E testing still awaiting the Windows Security prompt.

### 2026-09-19 — D08 focused JEI discovery and scoped query transport

- Advanced M0.3b.3.1a/b to implemented_unverified and added explicit .1d for
  visible-but-book-locked execution. SPEC v0.2.2, Forge capability minor 12 and
  generated RpcRequest agree on the new read-only query. Parent .3.1 and M0 remain
  in_progress; all original Mineflayer failures, later features and gates remain.
- Added exact public API compile pin and transformed-byte verification, lifecycle
  plugin, visibility-filtered item focus, bounded projection, query/source echo,
  recipe/book revision changes, separate discovery authority and strict scoped
  Java/TypeScript/Python/CLI delivery. No new action motor or global recipe export.
- Actual checks: 160 Java tests/build, 30 initial selected Node then 114 full Node,
  76 final selected Python, Ruff pass; zero skipped tests in successful selections.
  Actual CLI/HTTP/JVM and process tests use synthetic game sources/effects.
  The first Python path error and unmatched initial Node paths remain documented;
  no unexecuted selection is counted. [Report](docs/verification/2026-09-19-jei-query.md)
  links exact commands, source files, pins and private retained evidence.
- Candidate JAR `80e6bdfb644fce25f8cc512f21402e1357eddec74f60d4500c078cf337c6aede`
  is uninstalled; archive inspection confirms JEI/test classes are not bundled.
  No desktop input, real-game actions or inference dispatched. Last observed
  Windows Security prompt still requires the operator; no repeated approval request.
- Remaining: .1c native plugin/JEI/UI/lifecycle/hidden-source/reference checks,
  cooperative-time limits under actual JEI, .1d ordinary locked-recipe execution,
  .3.2 custom serializers/categories and machines/quests. Next independent work is
  .1d; deploy/qualify the candidate when the existing desktop prerequisite clears.

### 2026-09-19 — D09 explicit source selection and ordinary manual crafting

- Advanced M0.3b.3.1d.1/.2 to implemented_unverified; parent .1d remains
  in_progress and authentic .1d.3/.1c remain not_started. Added GameRecipeGrid and
  GameRecipeSelection, connected NativeGameRuntime/GameCrafting and regenerated
  source-selected craft schemas. Forge capability minor 13 pins the new route;
  Mineflayer explicitly rejects it with no crafting input.
- Manual allocation is bounded to 4,096 visits over 36 own inventory slots.
  Ordinary pickup/place-one/return waits for exact feedback after every click;
  the existing selected-output/consumption/remainder routine follows. Source
  generation/visibility/object/definition, menu/body, deadline/cancel and resource
  checks persist; book unlock alone does not invalidate the selected definition.
  Partial cursor/grid effects and consumed charges survive failure without replay.
- Checks: **173 Java / 115 Node / 78 Python**, zero skipped tests, plus Ruff pass.
  Ten new grid and three source-selection unit tests; exact 3x3 case uses 26 clicks/
  52 charged primitives. Actual cross-language HTTP/JVM envelopes use synthetic
  game motors; they do not qualify live JEI. [Report](docs/verification/2026-09-19-manual-craft.md)
  records procedures, limitations and private source/XML/log evidence.
- Built/uninstalled JAR `7151fffbed4744a2b516c6d9503d3ebcb329bde0694733b400aa8815aa5b4cf4`.
  No game action, desktop input or inference was used for implementation/tests.
  Recheck desktop prerequisite next, then deploy/qualify when available; otherwise
  continue .3.2 custom container/machine/source adapters. Full inventories requiring
  rearrangement, custom recipes, source latency, feedback ordering, server/reference
  evidence and all original gate failures remain explicit required work.

- Desktop recheck after implementation (recorded 09:13 UTC): refreshed returned
  windows and captured the unique E9E window through the computer-use skill.
  The Windows Security/OpenJDK network prompt is still present over multiplayer.
  No input/activation was sent. The skill's guidance forbids acting on security
  permission requests; the existing operator handoff remains pending. This is a
  live-prerequisite observation, not a reason to stop independent implementation
  or mark the whole goal blocked.

### 2026-09-19 — exact Thermal current-menu observation

- Split M0.3b.3.2 into .1 GUI observations, .2 machine transactions, .3 remaining
  custom recipe/category/ingredient/quest discovery and .4 authentic reference
  qualification before implementing .1. F01/F06/F16/N01/N04/N06, C09 and partial
  T01/T03/T06 advance; all original requirements and aggregate results remain.
- Added `GameMachineMenu` / `NativeThermalMenu`, native runtime/protocol routing,
  nullable machine display models and generated schemas/types, Python/Node
  validation and capability minor 14. Exact currently open furnace/crucible,
  runtime/class/registry/layout and loaded-artifact guards protect fixed public
  getters. Base/player active slots retain indices; hidden augment-panel contents
  are omitted. RF and mB values are bounded; raw/tagged fluid components reject.
- Inspected installed Expansion 10.3.1.25, nested Thermal Core 10.3.0.9 and CoFH
  Core 10.3.1.48 bytecode/metadata. Their runtime metadata omits build suffixes;
  corrected guards require both the reported versions and exact three JAR hashes.
  The initial strict full-version guard never ran against Minecraft. No mod
  distribution was committed or added to the built extension.
- Final Java build/tests: **182 pass**, zero failures/errors/skips, including nine
  new projection/artifact/context/bounds/layout cases. Full Node **116 pass**;
  after final byte-pin/capability changes, **30 focused contract/Forge tests pass**.
  Selected Python **96 pass**, with 18 initially skipped JVM cases then all
  **18 pass** under explicit pinned Java/classpath. Thus 114 distinct selected
  Python cases pass. Ruff/schema/type generation/diff checks pass.
  [Report](docs/verification/2026-09-19-thermal-menu.md) records exact commands,
  scope and retained private logs/XML/source hashes; effects remain synthetic.
- Built/uninstalled JAR `f34f6c2e786f02dbe6c97693cceab50c540d8621c054c68df8c532121dd55ec6`.
  The active E9E client still has the old read-only build and the Windows Security
  prompt. Fresh read-only capture sent no input; no server/gameplay worker launch
  or Strata inference occurred. Existing handoff remains pending.
- .1 is **implemented_unverified**. Machine slot mutation is explicitly rejected
  before input until .2 handles processing/charging between replies; no resource
  conservation or freshness exception was introduced. GUI values affect strict
  revisions and may invalidate pending actions. Actual loaded GUI/close/feedback
  parity, machine operation, independent server reference and all other original
  gates remain open. Continue .2, then execute connected qualification when the
  operator prerequisite is available; the long-horizon goal stays active.

### 2026-09-19 — Thermal transfers, masked feedback and D10 input fences

- Previous turn was progress: it implemented .3.2.1 and established source/build
  evidence. This continuation split .3.2.2 into .2a ordinary visible transfers,
  .2b full routing/panels/controls and .2c energy/fluid operation, retaining .4
  authentic/reference qualification. Advanced F01/F06/F09/F16,
  N01/N02/N03/N04/N05/N06, C09/C15/C18 and partial T01/T03/T06/T07/T12.
- `GameMachineInventory`, `NativeGameRuntime`, `NativeWindowSync` and native
  policy negotiation now support ordinary Thermal pickup/place and outgoing
  quick-move. A conserved/scoped immediate prediction is followed by full applied
  server feedback and exact owned slots/cursor checks. Processing may alter
  machine storage independently; no production/provenance assertion follows.
  Invalid predictions still request resynchronization; post-input errors become
  unknown/fenced and never replay. Hidden augment slots are masked before stack
  readers, and inactive visible slots reject the motor view.
- Installed CoFH bytecode confirms incoming quick-move can reach augments.
  That branch remains a named required .2b gap. D10/SPEC v0.2.5 explicitly fixes
  v0.2.4's telemetry-dependent input fence: passive energy/tank displays remain
  observable but cannot invalidate a slot/close solely by changing. All
  slot/cursor/window/body/control/lease/generation/latest-observation/age guards
  remain. The new behavior is a distinct Forge capability minor 15 candidate.
- Final checks: **200 Java / 116 Node / 114 Python pass**, zero failures/skips;
  Java has 18 new cases, including the real durable lane around synthetic machine
  effects for cancellation, unknown outcomes, duplicate requests, budget and
  deadline. An intermediate test run had 199 passes and one `SETTINGS_UNSAFE_PATH`
  setup failure due to a missing test child directory; the fixture now creates
  it, and failed XML/logs remain retained. Ruff/TypeScript/diff checks pass.
  [Report](docs/verification/2026-09-19-thermal-transactions.md) records commands,
  exact scopes and private logs/XML/source hashes. These are not real-pack passes.
- Built/uninstalled JAR `1e857474cacd9a269d85c133e4396b39986a4820665c295e47dd2da9b7f7e725`.
  A fresh read-only screen capture again shows the Windows Security/OpenJDK
  prompt (recorded 10:03:40 UTC); no desktop input was sent. The skill requires
  the operator to handle that prompt, and the existing handoff is pending. No
  game server/worker or Strata inference was started; the old read-only client
  stays installed. All test processes exited normally.
- .2a is **implemented_unverified**; .2b/.2c/.3/.4 and full vanilla/Forge, host,
  keybinding, isolation, accounting, soak/capacity and scientific gates remain.
  Next extend player-accessible machine recipe discovery and remaining machine
  interfaces while awaiting live prerequisites, then qualify against actual GUI
  and server/reference evidence. T03/G0 retain the failed Mineflayer/E9E result.

### 2026-09-19 — Focused Thermal recipe discovery and D08 extension

- Split M0.3b.3.2.3 into exact Thermal discovery (.a), other custom/counted
  ingredients/categories (.b), and player-accessible quests (.c). Implemented .a
  with `GameMachineRecipe`, `JeiMachineRecipes`, the existing JEI plugin/query
  projection, native/public contracts, broker/CLI and Forge capability minor 16.
  F01/F06/F16/N01/N04/N06, C09 and T01/T03/T06 partial coverage advance; G0 stays open.
- Inspected exact installed JEI/Expansion/Thermal Core/CoFH Core bytecode and
  primary category sources. Four artifact hashes and exact recipe/category classes
  gate machine queries. Default non-hidden JEI lookups and public layout slots
  provide the data. No transfer hook, global recipe scan, undisplayed XP/raw chance
  fields, custom predicate guesses or machine craft authority are introduced.
- Item/fluid focus, sorted bounded alternatives/counts, energy RF and the displayed
  integer output-tooltip percent have strict cross-language validation. Category
  and ingredient kind enter revision identity; runtime/body/source and byte/time
  bounds remain. Machine queries cannot enter `craft.recipe_selection`.
- Actual final checks: **207 Java pass** (25 s build), **117 Node pass** (46.197 s),
  **131 Python pass** (23.51 s), all without skips/failures. Added seven Java and
  seventeen Python cases, one Node HTTP boundary test, and both machine categories
  to the existing JVM-to-scoped-CLI fixture. Schema generation/build and Ruff pass.
  All game/JEI effects in those tests are synthetic. [Procedures/evidence](docs/verification/2026-09-19-thermal-recipes.md);
  private bundle `2026-09-19-thermal-recipes-01` retains source/bytecode/XML/logs.
- Candidate JAR SHA-256 `19eb090569302a5dce18cede266bc4d1343f17444216180948f638f886ff698e`
  is built and uninstalled. Desktop authorization remains active; a fresh read-only
  capture still showed the Windows Security network prompt. No input was sent;
  the existing operator handoff remains pending under the linked computer-use rule.
  No server/gameplay worker or Strata inference started; $0 inference dispatched.
- .3a is **implemented_unverified**. Actual JEI/UI/timing and machine/reference
  evidence, remaining custom/quest/control/energy/fluid features, full host,
  isolation/accounting, keybinding effects, team capacity, soaks and scientific
  gates remain open. Next inspect exact custom ingredients/quest sources and
  continue machine interfaces while preserving the pending live deployment tests.

### 2026-09-19 — Player-visible FTB catalog and custom recipe inspection

- Split M0.3b.3.2.3c into catalog (.1), readable details/task/reward surfaces
  (.2) and ordinary quest interactions (.3), preserving authentic qualification
  under .4. Implemented .1 through NativeQuests/GameQuestCatalog, private native
  protocol, Python/TypeScript contracts, broker, generated schemas and `mcgame
  quests`. SPEC v0.2.7 / Forge minor 17 records the source policy within D06.
- Pinned all three installed FTB artifacts. Public own-team/membership/editing,
  chapter/quest visibility, progress/startability/detail rules are checked; no
  hidden entry content, team selector, benchmark predicate or raw NBT is exposed.
  Bound projection/time/pages/titles, stable source/body and revision handling,
  strict response schemas and fail-closed unsupported paths are retained.
- Installed KubeJS serializer/assembly inspection found that client-null
  modify-result callbacks do not establish server fixed-output semantics. No
  permissive subclass substitution was enabled. Custom/staged/remainder recipe
  support remains .3b, without misclassifying the observed expert furnace recipe.
- Actual final checks: **214 Java / 118 Node / 148 Python pass**, zero
  failures/skips; schema export, generation/build and changed-Python Ruff pass.
  JVM/native transport fixtures are real processes with synthetic FTB/game
  sources. [Report](docs/verification/2026-09-19-quest-catalog.md), private bundle
  `.strata/evidence/2026-09-19-custom-discovery-01/` retain exact commands, logs,
  JUnit XML, source copies, installed API bytecode and artifact hashes.
- Candidate `2fb018e989c06d29510d6321619925473dac5c3e45e51e0701ce8faef21b734a`
  is built but uninstalled. Fresh read-only desktop capture confirms the Windows
  Security prompt remains; no desktop input was sent. Existing operator handoff
  persists; desktop authorization itself is active. No new server/worker/model
  run, soak, capacity test or study; Strata inference remains $0 dispatched.
- F01/F06/F16/N01/N04/N06, C09 and partial T01/T03/T06 advance without aggregate
  gate changes. Next: .c.2 readable quest surfaces and remaining independent
  required adapters; deploy/qualify the candidate once the security dialog clears.
- Final catalog review tightened Python/TypeScript/generated-schema IDs against
  a final-newline regex discrepancy; Java already required the exact length.
  Schema generation/TypeScript build and **75 Python / 1 Node** focused follow-up
  checks pass. No broader rerun or new Java build was needed; candidate JAR is
  unchanged. Tracked `git diff --check` passes with line-ending warnings only.

### 2026-09-19 — Readable quest text with independent hiding gates

- Split M0.3b.3.2.3c.2 into plain text (.1), visible tasks/rewards (.2) and
  dependencies/links/guide/rich surfaces (.3). Implemented .1 in GameQuestText,
  shared NativeQuests source, native protocol, strict Python/TypeScript/generated
  contracts and `mcgame quest-text`; all actual qualification remains .4.
- Enforce visibility/detail access before title/subtitle reads and independent
  hideTextUntilComplete before description access. Source/team/editing/body
  guards remain. Native page breaks and unsupported rich lines are explicit;
  no hidden descriptions, team selectors, raw components, actions or evaluator
  predicates are exported. Bounded line/component/page/time checks and source
  rechecks precede delivery. SPEC v0.2.8 / Forge minor 18 pins this candidate.
- Actual final checks: **220 Java / 119 Node / 167 Python pass**, zero final
  failures/skips; schema export, generation/build and changed-Python Ruff pass.
  Six Java and eighteen Python new cases plus HTTP/JVM/CLI cases use synthetic
  FTB/game data. Initial setup path error prevented a build; corrected. Initial
  Node run had 118 pass/1 fail due to a missing `quest-text` CLI allowlist entry;
  fixed and final full run passed. Both attempts are retained.
- [Report](docs/verification/2026-09-19-quest-text.md) and private bundle
  `.strata/evidence/2026-09-19-quest-text-01/` retain exact commands, logs,
  JUnit XML, source snapshots and installed parser/API inspection. Candidate
  `04720ab93d81c0136d3a44e29b73c21948d48833a2e17b97ce89e39943e95079`
  is built but uninstalled. No new desktop input/server/worker/model experiment;
  the existing Windows Security handoff remains pending and Strata inference
  remains $0 dispatched. Native UI/parser/team/latency/isolation remain unverified.
- F01/F06/F16/N01/N04/N06, C09, partial T01/T03/T06 advance without closing
  any aggregate gate. Next: visible task/reward surfaces and remaining adapters;
  deploy/qualify on the exact pack once the operator clears the security dialog.
- Final reconciliation: tracked whitespace and changed-document local-link checks
  pass. A fresh read-only capture after tests again shows Windows Security over
  E9E; no input was sent and the existing operator handoff remains unresolved.

### 2026-09-19 — Visible task/reward tooltips and own-player claim state

- Split M0.3b.3.2.3c.2.2 into bounded normal-tooltip/status projection (.a) and
  remaining player-opened item-alternative/choice/extension displays (.b).
  Implemented .a in GameQuestComponents/FtbQuestDisplays/NativeQuests, native
  protocol, strict Python/TypeScript/generated contracts and scoped CLI.
  SPEC v0.2.9 / Forge minor 19 pins the policy; mutations remain .c.3.
- Parent visibility/detail access and native reward blocking/invisible gates
  precede identifiers/display. Ordinary task progress formatting respects
  hidden numbers; own-player claim state uses the private current UUID and
  exports no raw counts/commands/NBT/team selector. Public TooltipList capture
  is bounded, requires normal modifiers, and never invokes button callbacks.
- Official exact FTB Maven POM/JAR returned 403. The already-authorized exact
  installed Library JAR now supplies a hash-checked compile-only prerequisite.
  Missing/wrong bytes reject with typed errors; no FTB classes are bundled.
  Build runbooks document this requirement. First compilation used the wrong
  TooltipFlag constant, corrected before final checks; failed log retained.
- Actual final checks: **228 Java / 120 Node / 187 Python pass**, zero final
  failures/skips; schema export, TypeScript generation/build and changed-Python
  Ruff pass. Both build-negative checks reject as expected. Tracked whitespace
  and changed-document local links pass. FTB/game effects remain synthetic.
- [Report](docs/verification/2026-09-19-quest-components.md) and private bundle
  `.strata/evidence/2026-09-19-quest-components-01/` retain logs, JUnit XML,
  installed bytecode/acquisition results, source snapshots and verification.json.
  Candidate `ca3493f0fda699822b81c5e6f2d6ca6bec4303751bc626ea4cd2b2be1af12cd2`
  is built but uninstalled. A fresh read-only capture still shows Windows
  Security over E9E; no desktop input was sent. Existing operator handoff
  persists; no server/worker/model experiment, soak, capacity test or study
  started. Strata inference remains **$0 dispatched**.
- F01/F06/F16/N01/N04/N06, C09 and partial T01/T03/T06 advance; no aggregate
  gate changes. Loaded callbacks, UI/claim/team/modifier/timing and isolation
  remain unverified. Next: remaining quest displays/actions and required
  independent adapters; deploy/qualify once the operator security prompt clears.

### 2026-09-19 — Ordinary quest menu API audit

- Began M0.3b.3.2.3c.2.2b with exact installed FTB UI inspection; no new
  capability or runtime implementation claim. The [audit](docs/verification/2026-09-19-quest-menu-audit.md)
  records item-list viewport limits, recipe-navigation behavior, task eligibility,
  Submit's separate disabled-widget check, and choice reward/index binding.
  Calling a callback alone is insufficient to preserve ordinary UI constraints.
- Private `.strata/evidence/2026-09-19-quest-menu-audit-01/` retains bytecode
  and public API signatures. An initially guessed nested class was absent;
  corrected using the JAR inventory and the final inspection exited zero.
  This is inspection evidence, not a test or game compatibility pass.
- Next concrete work: menu back/scroll (.c.3.2b.2), other task/choice/JEI/UI routes (.3), occupied crafting-state lifecycle (.4), then submission/claim server-resource effects (.c.3.3). Choice/extension displays (.c.2.2b.2), dependency/guide/rich surfaces (.c.2.3), custom/counted recipes (.3b), machine routing/control/energy/fluid (.2b/.2c) and actual reference qualification (.4) remain required. Deploy/qualify the candidate once the Windows Security prompt clears.
  viewport identity, then ordinary charged opening/submission/selection actions
  under .c.3 and actual server/UI qualification under .4. Private reflection,
  direct progress writes and raw packet callbacks are not substitutes. All
  aggregate gates and the pending operator security handoff remain unchanged.

### 2026-09-19 — Current item-alternatives menu with viewport filtering

- Split M0.3b.3.2.3c.2.2b into current item-menu observation (.1) and remaining
  choice/extension displays (.2). Implemented .1 across GameQuestMenu,
  NativeQuestItemMenu/FtbQuestDisplays, native protocol, Python/TypeScript,
  generated RPC contracts, broker and `mcgame quest-menu`. SPEC v0.2.10 /
  Forge minor 20 pins the new source; ordinary mutations remain .c.3.
- Require the exact active screen/widget tree, own-team source, visible chapter/
  quest/detail access and task membership. Compute native scroll truncation and
  clipped viewport before stack readers; recheck source/context/screen/layout.
  Reject context menus, unsupported relations/clipping, active render offsets,
  overlapping controls, advanced tooltips and held modifiers. Export ordinary
  item/control displays; no raw geometry, NBT, predicates or UI mutations.
- Actual checks: **236 Java / 121 Node / 212 Python pass**, zero final failures/
  skips; **80** quest-focused Python checks and Ruff pass. Schema export and
  TypeScript generation/build pass. Final Java guard/null-context changes
  passed the full Java suite again; subsequent **2 Node / 1 Python** focused
  HTTP/scoped CLI/JVM checks pass. FTB/game effects are synthetic.
- First TypeScript compile found an out-of-scope validator helper; corrected.
  The first Node suite attempt stopped during compilation because the new
  fixture used endpoint instead of host/port; fixed before the passing run.
  These are retained failures, not live game failures. Final transport review
  tightened item-ID whitespace rejection; focused negative cases pass.
- [Report](docs/verification/2026-09-19-quest-item-menu.md) and private bundle
  `.strata/evidence/2026-09-19-quest-item-menu-01/` retain installed bytecode,
  logs, JUnit XML, source snapshots, exact artifact hashes and verification.json.
  Candidate `2e8c620529c02c15d8378f3da2c6faf9d0f5dd183dab3b1732fc4634e335fae8`
  is built but uninstalled. No new game server/worker, inference, soak, capacity
  test or study started; Strata inference remains **$0 dispatched**.
- A fresh read-only capture still shows Windows Security over E9E; no input
  was sent and the existing operator handoff persists. F01/F06/F16/N01/N04/N06,
  C09 and partial T01/T03/T06 advance without aggregate gate changes. Next:
  ordinary quest actions and remaining menus; qualify loaded behavior once
  that prompt clears.
- Final reconciliation: changed-Python Ruff, tracked whitespace and changed-
  document local-link checks pass; the private collector verified 236 JUnit
  cases and the candidate SHA-256, copied 29 source files, and found no bundled
  FTB classes. All real integration and release gates remain unchanged.

### 2026-09-19 — Ordinary own-team quest-book opening

- Advanced M0.3b.3.2.3c.3.1 to implemented_unverified; split parent .3 into
  opening, navigation (.3.2) and submissions/claims (.3.3). SPEC v0.2.11 / Forge
  minor 21 and `ftb-own-team-open-screen-cas/1` record the additive required UI
  operation. F01/F06/F09/F16/N01/N02/N04/N05/N06, C09/C15 and partial
  T01/T03/T06/T07/T12 are mapped in the [opening report](docs/verification/2026-09-19-quest-open.md).
- Inspected the exact installed FTB public opening callback: disabled quests and
  locked teams reject, non-editing ordinary UI construction stays native. Added
  GameQuestOpen/NativeQuestOpening, NativeQuests/runtime/strict-batch integration,
  Python/generated/TypeScript contracts and new capability policy. No private
  callback, progress write, arbitrary selector or packet route was added.
- One durable charged callback verifies root catalog generation/revision before
  dispatch and the actual new screen/source immediately and on the next tick.
  Cancellation preserves any already-opened UI and charges. Refusal or failure
  after possible input is fenced/unknown; durable duplicate and restart paths
  never repeat it. Stock Mineflayer advertises no support and rejects the action.
- Executed full Java module test/build/classpath: **246 pass**, zero errors/skips;
  full Node suite: **123 pass**, zero failures/skips; nine selected Python suites
  with explicit actual JVM path/classpath: **214 pass**, zero skips. Ten new Java
  cases test motor/journal failure paths; public CLI/native HTTP exercise the
  real pure motor with synthetic UI authority. These are not live FTB effects.
- The first Java run had two fixture failures: new journal subdirectories were
  absent, correctly triggering SETTINGS_UNSAFE_PATH. Created the test directories;
  did not relax the production guard. Both attempts are retained privately.
- Final schema export/generation, TypeScript build, changed-Python Ruff and
  tracked diff checks pass (CRLF warnings only). A focused scoped CLI rerun passes
  one test after the capability field explicitly says server effects are unverified.
  The evidence collector checks linked local docs and no bundled FTB classes.
- Candidate JAR `382a674d43ec6b844cdff55e23fc9580cf46c3ea6adc254cb76b9e9e43775048`
  is built and uninstalled. Private evidence is under
  `C:\Users\Darian\.strata\evidence\2026-09-19-quest-open-01`.
- A fresh read-only desktop capture still showed Windows Security over E9E.
  No desktop input, new game/server/worker or inference was started. The existing
  skill-mandated operator handoff remains pending; $0 Strata inference dispatched.
- Next: implement visible chapter/task navigation, explicit close/back/scroll;
  preserve submission/claim server/resource feedback, choices/rich displays and
  exact-pack reference/isolation qualification. All M0–M6 gates remain open;
  M7 remains conditional and the long-horizon goal stays active.

### 2026-09-19 — Current quest-book state and basic navigation

- Advanced M0.3b.3.2.3c.3.2a to **implemented_unverified** under SPEC v0.2.12 /
  D06. F01/F06/F09/F16/N01/N02/N04/N05/N06, C09/C15 and partial
  T01/T03/T06/T07/T12 are mapped in the [navigation report](docs/verification/2026-09-19-quest-navigation.md).
- Added GameQuestScreen/GameQuestNavigation/NativeQuestNavigation, native runtime
  and protocol plumbing, strict Python/generated/TypeScript contracts, Forge
  broker/capability policy and `mcgame quest-screen`. The fifteen-action candidate
  binds navigation to the exact visible catalog page and current source/screen;
  hidden/off-page/inaccessible entries and replaced native targets reject.
- Exact installed FTB bytecode establishes ordinary public chapter/quest link,
  back and hotkey-close callbacks. One charged call confirms the local transition
  immediately and next tick, retains partial effects/costs and never replays.
  Same-chapter navigation preserves native no-op behavior. Private native objects,
  layout fingerprints and body/connection identity stay outside public responses.
- Found ordinary book close also closes the player container. Initial opening
  and navigation now require empty carried/crafting/result slots. Occupied-grid
  resource confirmation and other native UI contexts remain explicit .3.2b work;
  no resource-conservation or full lifecycle pass is claimed.
- Executed full Java module test/build/classpath: **257 pass**, zero failures,
  errors or skips; full Node suite: **126 pass**, zero failures/skips; ten selected
  Python suites with explicit JVM/classpath: **230 pass**, zero skips. Eleven new
  Java cases exercise lifecycle, identity/freshness, selection races, hidden/off-page
  data, callback refusal, cancellation, durable deduplication/reopen and uncertain
  post-effect failures. Real JVM/HTTP/scoped CLI run open/chapter/quest/back/close
  through pure motors with **synthetic FTB/game/UI authority**.
- Initial Node run: 124 pass, one new fixture failure because its HTTP response
  lacked JSON content type. Corrected the fixture without relaxing transport;
  added a body-generation negative and reran the full suite successfully. Both
  logs remain private. Existing Java/Gradle deprecation warnings remain.
- Schema export/generation, TypeScript build and changed-Python Ruff pass.
  Candidate JAR `387c2d6aa51cf241d008f9c4aef97112964e1f2af3116d3b3c69af9e03fb59bd`
  is built and uninstalled. Evidence bundle:
  `C:\Users\Darian\.strata\evidence\2026-09-19-quest-navigation-01`.
- Fresh read-only desktop capture still showed the Windows Security prompt;
  no input was sent and the existing operator handoff remains pending. No new
  real client/server/worker, inference, soak, capacity test or study started.
  Strata inference remains $0 dispatched. T03/G0 retain the Mineflayer/E9E failure;
  all aggregate gates remain open, M7 conditional, long-horizon goal active.
- Next: task/menu opening and back/scroll, remaining contexts/resource lifecycle,
  ordinary submissions/claims, choice/rich displays and authentic qualification.

### 2026-09-19 — Visible item-task menu opening

- Split M0.3b.3.2.3c.3.2b into item-task opening (.1), menu back/scroll (.2), other
  task/choice/JEI/UI contexts (.3), and occupied crafting-state lifecycle (.4).
  Advanced .1 to **implemented_unverified** under SPEC v0.2.13 / D06. Mapping:
  F01/F06/F09/F16/N01/N02/N04/N05/N06, C09/C15, partial T01/T03/T06/T07/T12.
- Added GameQuestTaskOpen/NativeQuestTaskOpen, native runtime/batch/policy routing,
  Python/generated/TypeScript contracts and Forge minor 23 capability metadata.
  A returned task-page entry must match the current book/quest and a visible enabled
  native TaskButton. Exact public ancestry, clipped viewport, truncated scroll and
  later sibling layers fence selection before IDs; native task/button/layout identity
  is checked again inside charged dispatch. Ordinary LEFT emits once and confirms
  the distinct actual item menu, retained task and previous book, without submission.
- Exact installed TaskButton/ItemTask/Panel/Widget bytecode distinguishes the menu
  route from single-item non-consuming JEI and empty-item toast routes. Other routes
  remain required. No arbitrary callback, private field, server progress write or
  packet route was added. Cancellation retains UI changes/costs; uncertain effects
  fence and never replay. Stock Mineflayer explicitly rejects the action.
- Full Java test/build/classpath: **264 pass**, zero failures/errors/skips. After
  improving the synthetic port to use the actual components projector, focused
  task-motor tests: **7 pass**. Eleven selected Python suites with explicit JVM:
  **232 pass**, zero skips. Final full Node suite: **128 pass**, zero failures/skips;
  focused actual scoped CLI: **1 pass**. HTTP/JVM/CLI use real pure motors with
  synthetic native/game authority. [Report](docs/verification/2026-09-19-quest-task-open.md).
- Retained failed attempts: focused Gradle option was attached to writeTestClasspath,
  so parsing failed before tests; corrected option order passed. Initial concurrent
  Node/Python run had 127 Node pass/one CLI exit-4 rejection without retained response
  text. Added synthetic diagnostic output; focused and full Node reruns passed.
  Root cause remains unresolved, not claimed fixed. Production deadlines/freshness/
  retry policy were unchanged; authentic/load timing gates remain open.
- Candidate JAR `5b42905061db0947fb1b0eaa387b1a6508b808911cbcff6b851c153cec790a15`
  is built and uninstalled. Private logs, installed bytecode, JUnit and source hashes:
  `C:\Users\Darian\.strata\evidence\2026-09-19-quest-task-open-01`.
- Fresh read-only desktop capture still shows Windows Security/OpenJDK over E9E;
  no input sent, existing operator handoff pending. No new real game/server/worker,
  inference, soak, capacity or study execution. $0 Strata inference dispatched.
  No aggregate gate changes; T03/G0 retain Mineflayer/E9E failure, M7 conditional.
- Next: ordinary menu back/scroll, then remaining task/choice/JEI/UI contexts,
  occupied-grid resource lifecycle, submissions/claims and authentic qualification.

### 2026-09-19 — current item-menu Back and one wheel gesture

- Split M0.3b.3.2.3c.3.2b.2 into exact item-menu controls (.2a) and choice/other
  controls (.2b); .2a is **implemented_unverified**, .2b remains required.
  SPEC v0.2.14 / D06; F01/F06/F09/F16, N01/N02/N04/N05/N06, C09/C15,
  partial T01/T03/T06/T07/T12. No aggregate status changes.
- Added `GameQuestMenuAction`, `NativeQuestMenuAction`, ordinary runtime dispatch,
  strict Python/generated/TypeScript contracts and Forge minor 24 metadata.
  Back and one up/down native wheel callback retain current source/menu/task/
  parent/layout fences, clipping, native step/clamping, restored logical hover,
  charged cancellation/deadlines/budgets and no ambiguous replay. The OS pointer
  is not moved. Menu observer policy `/2` adds wheel-sensitive revision inputs;
  fields remain unchanged. Stock Mineflayer rejects the new action.
- Inspected exact installed FTB Panel/Widget/Back bytecode. Synthetic tests do
  not establish actual callback/hover/viewport/resource/reference behavior.
  Executed full Java build/tests: **273 pass**, zero failures/errors/skips,
  26 s; twelve Python suites **235 pass**, zero skips, 32.44 s. Final full Node
  suite with explicit JVM/classpath/Windows guardian: **129 pass**, zero skips,
  54.302 s. JVM/HTTP/scoped CLI tests exercise opening → down → up → Back,
  observing revisions and exact parent quest through the real pure motors.
- First Node attempt: 128 pass / one `LEASE_EXPIRED` at the first menu query.
  Direct-lane test had no supervisor renewal and exceeded its six-second lease.
  Added the worker's ordinary two-second renewal lifecycle to that fixture with
  cleanup; full rerun passes. Production expiry/freshness/deadline/replay policy
  unchanged. Earlier task-opening rejection remains separately unresolved;
  this finding cannot retroactively prove its cause. Both current logs retained.
- Ruff on changed Python, schema export, TypeScript generation/build and tracked
  `git diff --check` pass (CRLF warnings only). Candidate JAR SHA-256
  `a3a13eb08385bd757c1acbb6ebb3ae452f4f46bf88c21f7952aaf96298cb20d8`,
  built but uninstalled. [Report](docs/verification/2026-09-19-quest-menu-action.md);
  private bytecode/logs/JUnit/source hashes and verification record under
  `C:\Users\Darian\.strata\evidence\2026-09-19-quest-menu-action-01`.
- Desktop tool works; fresh read-only capture still shows Windows Security over
  E9E. No input sent; operator handling requested under the skill. No new live
  game/server/worker, inference, soak, capacity or study. $0 Strata inference
  dispatched. Goal active, M7 conditional, T03/G0 Mineflayer failure retained.
- Next: choice/other menu projection and lifecycle, remaining task/JEI/UI routes,
  occupied crafting-state conservation, submissions/claims; deploy and qualify
  the candidate when the security prompt is handled.

### 2026-09-19 — eligible choice opening and bounded current-menu projection

- Split .c.2.2b.2 into exact choice opening-bound display (.a) and other extension
  displays (.b), and .c.3.2b.3 into choice opening (.a) and remaining routes (.b).
  M0.3b.3.2.3c.2.2b.2a / .3.2b.3a are **implemented_unverified**.
  SPEC v0.2.15 / D06; F01/F06/F09/F16, N01/N02/N04/N05/N06, C09/C15,
  partial T01/T03/T06/T07/T12. No aggregate status changes.
- Added `GameQuestRewardOpen`, `NativeQuestRewardOpen`, `NativeQuestChoiceMenu`,
  runtime/strict schema/native transport dispatch and Forge minor 25 policies.
  Opening requires current rewards page `can_claim`, displayed parent quest,
  visible enabled native button, current-player eligibility and exact source/
  layout. One ordinary callback opens and confirms the actual choice menu.
  Pre-opening table inspection is count-only (512 limit), without entries.
- Private parent/reward binding is retained from opening and expires on screen/
  source changes. Current reads recheck membership/visibility/eligibility before
  IDs and display content. Public widget children/titles/tooltips provide clipped
  bounded choice rows; no private fields, raw table indexes, weights, commands,
  definitions or claim route. Menu policy `/3` adds `reward_choices` while preserving
  item fields. Item Back/wheel remains item-only; choice controls remain required.
- Inspected pinned ChoiceReward/RewardButton/choice screen and Library list-panel/
  scrollbar bytecode, including opening versus claim callback separation. Source
  inspection is not loaded behavior. Full final Java suite/build: **285 pass**,
  zero failures/errors/skips, 25 s. Earlier Java builds also passed. Fourteen
  Python suites: **254 pass**, zero skips, 34.70 s. Full Node with explicit JVM/
  classpath/Windows guardian: **130 pass**, zero skips, 54.367 s. Synthetic JVM/
  HTTP and CLI tests execute opening/projection/deduplication; no game authority.
- Changed-Python Ruff, schema export, TypeScript generation/build and tracked
  diff checks pass; CRLF and existing Java/Gradle deprecation warnings remain.
  Candidate JAR `43ab8799484bc8ce4b2737ab318185102a08b98d18bf9f2f1fc256d127016e74`
  is built but uninstalled, with no bundled FTB classes. [Report](docs/verification/2026-09-19-quest-choice.md);
  private logs/bytecode/JUnit/source hashes and verification record:
  `C:\Users\Darian\.strata\evidence\2026-09-19-quest-choice-01`.
- Existing Windows Security handoff remains pending after the earlier fresh
  capture in this task. No desktop input/new real game/server/worker, inference,
  soak, capacity test or study. $0 Strata inference; goal active; M7 conditional.
  T03/G0 retain the exact Mineflayer/E9E failure.
- Next: choice Back/scroll, other task/JEI/UI/extension displays, occupied-grid
  conservation, submissions/claims and authentic exact-pack/reference qualification.

### 2026-09-19 — opening-bound choice Back and attached-scrollbar controls

- Split M0.3b.3.2.3c.3.2b.2b into exact choice controls (.1) and other extension
  controls (.2). Child .1 is **implemented_unverified**; .2 stays not_started.
  SPEC v0.2.16 / D06, F01/F06/F09/F16, N01/N02/N04/N05/N06, C09/C15;
  partial T01/T03/T06/T07/T12. No aggregate status or release claim changes.
- Added `NativeQuestChoiceAction`, full scrollbar state to `GameQuestMenuAction`,
  wheel-sensitive revisions in `NativeQuestChoiceMenu`, dispatch in `NativeQuests`,
  strict Python/TypeScript policy changes and Forge minor 26 capabilities.
  `ftb-current-item-choice-menu-back-wheel/2` and menu projection `/4` retain
  eighteen action kinds and current response fields, with no claim authority.
- Audited installed ScreenWrapper, BaseScreen, Panel, ScrollBar, PanelScrollBar
  and mapped Mth. Back uses the normal Backspace/onBack callback; choice controls
  remain empty. Native close may restore the pointer; no-pointer wording applies
  specifically to temporary wheel targeting. Exact attached scrollbar value and
  panel offset are confirmed, including a negative maximum with stationary panel.
- Nine new Java tests plus extended JVM/HTTP and scoped CLI sequences cover
  traces, stale/raced state, invalid bounds, retained effects/charges and durable
  deduplication. Initial Java run: 293 pass / one new-test failure expecting zero
  pre-dispatch cancellation cost. Corrected the assertion: safety release is charged,
  and a throwing callback leaves emitted count unknown. Production accounting
  unchanged; failed log/XML retained. Final full Java build: **294 pass**, zero
  failures/errors/skips, 24 s. Python: **255 pass**, zero skips, 35.89 s. Node:
  **130 pass**, zero skips, 58.331 s. Game/UI authority is synthetic throughout.
- Changed-Python Ruff, schema export and TypeScript generation/build passed.
  Candidate JAR `f5785b62ccb9aa8e1bf7d6acf4aef0fc618168d24a874e34ed3412099df131ac`
  built but uninstalled. [Report](docs/verification/2026-09-19-quest-choice-controls.md);
  private logs/bytecode/JUnit/source hashes under
  `C:\Users\Darian\.strata\evidence\2026-09-19-quest-choice-controls-01`.
- Fresh read-only desktop capture still shows Windows Security over E9E. No
  desktop input or new real client/server/worker, inference, soak, capacity test
  or study. Existing operator handoff pending. $0 Strata inference; goal active;
  M7 conditional. T03/G0 retain exact Mineflayer/E9E failure.
- Next: remaining task/JEI/extension contexts, occupied crafting lifecycle,
  submission/claim effects and authentic callback/drag/polling/pointer/viewport/
  resource/reference/isolation qualification when the security prompt is handled.

### 2026-09-19 — exact item-task to JEI integration prerequisite audit

- Split .c.3.2b.3b into exact non-consuming single-item recipe route (.1,
  **in_progress**) and other task/UI contexts (.2, **not_started**). No omitted
  feature, new runtime capability or gate pass. SPEC v0.2.16 unchanged.
- Read installed ItemTask, XMod JEI helper/integration, RecipesGui/logic and
  mapped Minecraft Screen APIs. Actual route creates OUTPUT focus through
  XMod's public runtime. Helper availability alone is insufficient; missing
  runtime/ingredient or failed showFocus can produce no new screen. JEI Back
  is recipe history; ordinary onClose returns to parent and clears history.
- Public IRecipesGui has no current-focus/current-page/parent getter. Record
  this interface boundary explicitly; do not invent an API, equate lookup with
  current display, or export private recipe graphs. Existing focused recipe
  query and current task-route rejection remain unchanged. Added [audit](docs/verification/2026-09-19-quest-jei-route-audit.md).
- Captured exact installed JAR hashes and javap output in private
  `C:\Users\Darian\.strata\evidence\2026-09-19-quest-jei-route-01`.
  Read-only inspection; no broad suite rerun justified by this documentation.
  Prior code evidence remains 294 Java / 130 Node / 255 Python pass, synthetic.
  Tracked diff and source/link checks remain required before handoff.
- Next resolving action: implement an explicitly identified recipe screen and
  retained opening-parent/runtime binding with ordinary close, no-open and
  stale/cancel/unknown cases; separately qualify readable current-page contents.
  Windows Security handoff still pending; no desktop input/live run/inference.
  All aggregate gates open, goal active, M7 conditional.
- Final audit verification: three installed artifact hashes, eight source
  snapshots, four bytecode/API files and 432 local document links checked;
  `git diff --check` passed with CRLF warnings only. Choice-controls evidence
  collector separately verified 294 JUnit cases, 53 source files, 493 local
  links and no bundled FTB classes. No additional runtime test was claimed.

### 2026-09-19 — ordinary task-to-JEI opening, origin state and close

- Previous goal turn classified **progress**: implemented choice controls and
  audited exact task-to-JEI routing. This turn continues that route under
  M0.3b.3.2.3c.3.2b.3b.1, split into .a opening/origin/return and .b required
  current-page projection/history/category/page controls. Child .a is
  **implemented_unverified**; .b remains not_started. No scope/gate reduction.
- SPEC v0.2.17 / D06 / Forge minor 27; F01/F06/F09/F16, N01/N02/N04/N05/N06,
  C09/C15 and partial T01/T03/T06/T07/T12. Added `GameQuestRecipeView`,
  `NativeQuestRecipeView`, exact public runtime/helper binding in `JeiRecipePlugin`,
  the native ItemTask branch, retained parent reading, explicit screen kind,
  default-denied recipe navigation/close confirmation and strict Python/TS policies.
  Existing eighteen action kinds and action envelopes remain.
- All five FTB/XMod/JEI artifacts and current helper/runtime/screen identity are
  pinned. Existing visible selected task/page/widget/source guards remain; the
  native ingredient is visible/known and privately copied/rechecked. One ordinary
  callback must open the actual distinct recipe screen; no-open is fenced with
  retained costs. State reports originating chapter/quest only, never current
  focus/page/private parent. Normal close returns to the exact book and quest;
  recipe-history Back and other navigation reject. No raw graph/claim/transfer route.
- Ten new Java cases exercise pins, projection, wrong/missing origins, source/
  runtime/layout/screen changes, binding expiry, no-open, wrong return, cancellation,
  uncertain costs and durable deduplication. Read-only code review added a guard
  for removed/changed parent quest before task access, with regression assertion.
  Initial compile passed 15 s; initial full Java passed 25 s. Final full Java:
  **304 pass**, zero failures/errors/skips, 26 s. Python: **262 pass**, zero skips,
  39.08 s. Node: **131 pass**, zero skips, 58.260 s. Native/JVM/HTTP/CLI game/UI
  authority is synthetic; no real pack conformance inferred. Python/Node ran before
  the final native-only origin guard; final Java covers its pure origin regression.
- Changed-Python Ruff, schema export and TypeScript generation/build passed.
  Candidate `109e437a88948c34df14a40eb5a1d82993843db50a4f27af287c888ef30d8533`
  built but uninstalled. [Report](docs/verification/2026-09-19-quest-jei-lifecycle.md);
  logs/JUnit/source hashes and pin checks:
  `C:\Users\Darian\.strata\evidence\2026-09-19-quest-jei-lifecycle-01`.
- No desktop input/recapture or real client/server/worker/inference/soak/capacity/
  study in this phase. Last observed Windows Security prompt has the same pending
  operator handoff. $0 Strata inference; goal active, M7 conditional. T03/G0
  retain exact Mineflayer/E9E failure; all aggregate gates remain open.
- Next: current JEI page projection and further navigation using qualified
  current-screen hooks; preserve other extension/rich/custom-recipe, occupied-grid,
  submission/claim, machine and authentic input/resource/reference/isolation work.
- Final evidence collector verified all 304 JUnit cases, five artifact pins,
  59 source snapshots and 505 local links; candidate contains no FTB/JEI classes.
  Tracked `git diff --check` passed with CRLF warnings only. No release claim.

### 2026-09-19 — bounded provenance from actual JEI layout draws

- Previous goal turn classified **progress**: ordinary task-to-JEI opening and
  origin-bound close implemented but unverified. This turn advances the independent
  current-page work; no blocked audit accrual. Split M0.3b.3.2.3c.3.2b.3b.1b into
  .1 render provenance, .2 copied filtered public page, .3 further navigation and
  .4 authentic qualification. Only .1 is implemented_unverified; parent in_progress.
- Read relevant SPEC requirements/contracts/gates and current ledger. SPEC v0.2.18
  records the D06 internal instrumentation; F01/F06/F09/F16, N01/N02/N04/N05/N06,
  C09/C15 and partial T01/T03/T06/T07. No public affordance/policy/action or budget
  change; Forge minor 27 and eighteen actions retained. All original scope remains.
- Added GameRecipeRenderCapture, task-bound native event lifecycle and optional
  exact RecipeGuiLayouts Mixin. The wrapper calls native draw once with unchanged
  receiver/arguments and propagates its exception. It retains only normally drawn
  identities after complete matching Pre/loop/Post; no private JEI fields, graph
  enumeration, recipe transfer, input or public raw-object route.
- Ten synthetic renderer cases test partial/missing hooks, nested/repeated loops,
  wrong/duplicate layouts, identity/dimension/source boundaries, 32-entry bounds,
  clock regression, 100-ms frame/250-ms age bounds, immutable order and no content
  inspection. Full Java test/build/classpath command passed in 28 s: **314 tests**,
  zero failures/errors/skips. Installed JEI hash and exact method/call bytecode,
  built wrapper order and manifest/config checked. These do not execute Mixin or
  authentic frames. Previous 262 Python / 131 Node pass retained; public surfaces
  unchanged, so no broad rerun. Existing build deprecation warnings remain.
- Candidate `17203aab532914c12e5762edae6dcc9c7f6e8b76af42503d18cfe02a28a56ab4`
  built, uninstalled; no bundled FTB/JEI classes. [Report](docs/verification/2026-09-19-jei-render-capture.md).
  Logs/JUnit/bytecode/source snapshots and collector:
  `C:\Users\Darian\.strata\evidence\2026-09-19-jei-render-capture-01`.
- Fresh read-only computer-use capture confirms the Windows Security/OpenJDK
  prompt still covers E9E. No desktop input sent; the previous operator handoff
  remains pending under the computer-use skill, while desktop authorization is
  active. No real server/client/worker launch, inference, soak, capacity or study.
  $0 Strata inference dispatched. Exact Mineflayer/E9E T03/G0 failure retained;
  all aggregate gates open, goal active, M7 conditional.
- Next: copy/filter displayed contents during actual rendering, not later mutable
  object reads; qualify clipping/overlays/custom ingredients and strict transport,
  then history/category/page controls. Native hook loading, frames, input,
  overhead/mechanics and isolation stay .1b.4. Other required quest/resource,
  custom recipe, machine and reference work is unchanged.
- Final collector passed: 314 JUnit results, exact installed/candidate bytecode
  checks, 15 source snapshots and 510 local links. Tracked `git diff --check`
  passed with CRLF warnings only. No authentic integration or release claim.

### 2026-09-19 — immutable copies of actual JEI slot draw operands

- Previous goal turn classified **progress**: complete-frame render provenance
  added, with 314 Java cases passing and exact packaged-hook audit. This turn
  advances M0.3b.3.2.3c.3.2b.3b.1b.2, split into .a immutable operands, .b remaining
  labels/rich/custom/overlay content and .c public transport. Only .a is now
  implemented_unverified; parent in_progress. No blocked-audit accrual or scope cut.
- SPEC v0.2.19 / D06; F01/F06/F09/F16, N01/N02/N04/N05/N06, C09/C15,
  partial T01/T03/T06/T07. Added GameRecipeSlots, JeiSlotCopies and exact slot Mixin;
  extended frame capture, native render lifecycle and view runtime binding. No
  public schema/transport/action change: Forge minor 27 and eighteen actions remain.
- Installed bytecode establishes the actual slot selection/draw path and final
  TypedIngredient wrapper. Capture selection-return and matching draw-operand
  identity, including a positive empty-selection event; missing hooks cannot
  become empty slots. Ignore getters outside the slot's own draw, reject incomplete,
  nested, repeated or reordered callbacks. Read geometry before content; whole
  off-screen layouts reject, clipped slots omit payload/role, and tagged/custom
  ingredients remain explicit unsupported markers without raw content.
- Copy only immutable category/slot/index/role/kind/registry/amount values, at most
  128 expected slots per layout, 32 layouts and 32 KiB including array punctuation.
  Malformed or mixed copied/uncopied frames invalidate in full. Retain all prior
  task-origin/runtime/source, frame-completion, 100-ms/250-ms and identity fences.
  Native internal reads now return copies; no public page route or pixel-parity claim.
- Initial full Java build/test passed in 26 s. Review corrections for unrelated
  getter calls, invalidation and byte accounting passed in 26 s. Final native
  off-screen-layout/exact-wrapper guards and regression assertions: **326 Java pass**,
  zero failures/errors/skips, 25 s, using pinned JDK 17.0.20.101/Forge 43.4.23 and
  the exact external FTB Library. Twelve new cases use synthetic draw/ingredient
  callbacks. No relevant public changes warranted Python/Node rerun; retain prior
  262 Python / 131 Node pass. Existing build deprecation warnings remain.
- Collector verified all five installed hashes, exact slot/layout/getter bytecode,
  wrapper call order and Mixin packaging; actual transformation/rendering remains
  unrun. Candidate `5e134a386a81de9dda28e41ca51972e3e37e716bf45fdd4a5617a83a499e987d`
  built, confirmed absent from installed Strata JARs, no bundled FTB/JEI classes.
  [Report](docs/verification/2026-09-19-jei-slot-copies.md); private logs/JUnit/source
  and bytecode evidence: `C:\Users\Darian\.strata\evidence\2026-09-19-jei-page-01`.
- No desktop recapture/input, real client/server/worker launch, inference, soak,
  capacity or study this phase. Last observed Windows Security prompt and its
  operator handoff remain unresolved; no fresh state inferred. $0 Strata inference;
  goal active, M7 conditional; exact Mineflayer/E9E T03/G0 failure retained and all
  aggregate gates open.
- Next: strict copied-page transport with explicit coverage, source/body/lease and
  schema/content fences; complete labels/custom/rich/overlay semantics and page/
  category/history controls. Authentic hook loading, rendering/overhead/mechanics,
  UI/input/reference/isolation and other required quest/machine/resource work remain.
- Final evidence collector passed with 19 source snapshots and 515 local links;
  tracked `git diff --check` passed with CRLF warnings only. No release claim.

### 2026-09-19 — scoped current JEI slot-page transport

- Previous goal turn classified **progress**: immutable draw operands established.
  This turn advances M0.3b.3.2.3c.3.2b.3b.1b.2c to implemented_unverified; parent
  remains in_progress. No scope cut or blocked-audit accrual. SPEC v0.2.20/D06;
  F01/F06/F09/F16, N01/N02/N04/N05/N06, C09/C15 and partial T01/T03/T06/T07.
- Added GameRecipePage and native runtime/protocol/view routing, strict Python and
  TypeScript validators, public request/generated schema, scoped broker/CLI route
  and Forge minor 28 capability. Public output is explicitly incomplete copied
  slot_draw_operands, bounded to 32 layouts/128 slots/32 KiB including envelope.
  Recheck origin/source/screen/copied content, canonical digest, body/connection,
  deadline/lease/stop state; strip private schema/body fields. No extra selectors,
  raw objects/components or input authority. Stock Mineflayer rejects the route.
- Pinned Java build/test passed: **333 cases**, zero failures/errors/skips, 29 s.
  Selected Python: **285 passed**, zero skips, 39.10 s. Full Node initially 133 pass
  (60.211960 s), then 134 pass (59.499551 s) after adding stop-during-read coverage;
  zero failures/skips. Review removed string coercion from slot roles; rebuilt
  TypeScript and ran the selected transport regression: one pass, 0.755569 s.
  Schema export/generated bindings and changed Python Ruff passed. Real JVM/HTTP/
  scoped CLI transports use synthetic game/render authority; no authentic pass.
- Candidate 64ccebf745b5c4519863df79415ec046ff848e7d71ee8d22b4f6698ca9c5f35d
  built and uninstalled. [Report](docs/verification/2026-09-19-jei-page-transport.md);
  private evidence: C:\Users\Darian\.strata\evidence\2026-09-19-jei-page-transport-01.
- Fresh read-only desktop capture still shows Windows Security/OpenJDK network
  permission over E9E; no input sent. Existing operator handoff remains. General
  desktop authorization is active. No real client/server/worker launch, inference,
  soak, capacity or study; $0 Strata inference, all aggregate gates open, exact
  Mineflayer/E9E T03/G0 failure retained, M7 conditional, long-horizon goal active.
- Next: displayed labels/rich/custom/overlay semantics (.2b), ordinary history/
  category/page controls (.3), authentic hook/render/input/mechanics/clock/overhead/
  reference/isolation qualification (.4), and remaining quest/machine/resource work.
- Evidence collector passed: five artifact pins, packaged Mixin/no bundled FTB/JEI,
  uninstalled candidate, exported request schema/generated method, 32 source
  snapshots and 518 local links; tracked diff check passed with CRLF warnings only.
  Initial collector duration-string formatting mismatch corrected numerically;
  no test or measured result changed. No release claim.

### 2026-09-19 — actual category/page header operands and typed transport

- Previous goal turn classified **progress**: copied-slot public transport completed
  its synthetic/JVM/CLI checks. This turn advances .c.3.2b.3b.1b.2b, split into
  .1 ordinary header operands and .2 remaining rich/custom/category/overlay content.
  Only .1 is implemented_unverified; parents in_progress, no blocked-audit accrual.
- SPEC v0.2.21 / D06; F01/F06/F09/F16, N01/N02/N04/N05/N06, C09/C15,
  partial T01/T03/T06/T07. Forge minor 29, policy/header response version 2, still
  explicitly incomplete slot_and_header_draw_operands; eighteen actions unchanged.
- Exact installed JEI bytecode distinguishes visible/truncated category text from
  stored full title and identifies the page-string drawing helper. New optional
  screen/category/helper hooks retain normal calls and require complete ordered
  callbacks within the same frame as slots. Wrong/missing/changed/unfinished hooks
  invalidate. Read only actual draw operands through fixed public methods.
- Native copy requires known font/identity pose and checks rectangle geometry before
  text. Pin rounded centering, nine-pixel line and shadow bounds; clipped or rich
  unsupported markers expose null text. Exactly two ordered headers, 1,024 code
  points / 4,096 UTF-8 bytes each, within the full 32-KiB page bound and digest.
  Preserve origin/source/body/deadline/lease/age fences. Java canonical encoding
  now handles Unicode U+2028/U+2029 without relying on Gson's escaping.
- Initial Java build/test passed in 29 s. Final geometry helper/regressions:
  **342 Java pass**, zero failures/errors/skips, 26 s. **293 Python pass**, zero
  skips, 39.16 s; **134 Node pass**, zero failures/skips, 60.653792 s. Explicit
  pinned JVM/classpath/guardian Python used. Nine new Java and eight Python cases;
  Node transport/lifecycle expanded with Unicode and negative header authority.
  Real JVM/HTTP/scoped CLI uses synthetic game/render authority. Ruff and TypeScript
  build pass; no unrelated schema regeneration or paid testing.
- Candidate 599ad772892d30d9f8d24fae33b279b3ad28e47e4e2866d42d6758f1da43f5fc
  built, uninstalled. [Report](docs/verification/2026-09-19-jei-page-headers.md);
  private evidence: C:\Users\Darian\.strata\evidence\2026-09-19-jei-page-labels-01.
- No desktop recapture/input, authentic launch, inference, soak, capacity or study.
  Previous observed Windows Security prompt awaits the existing operator handoff;
  no fresh desktop state inferred. $0 Strata inference, long-horizon goal active,
  M7 conditional; all aggregate gates open and exact Mineflayer/E9E failure retained.
- Next: remaining rich/custom/category/overlay surfaces (.2b.2), ordinary history/
  category/page controls (.3), authentic hook/render/input/Font/viewport/mechanics/
  clocks/overhead/reference/isolation (.4), and other quest/machine/resource work.
- Collector passed: five installed pins, exact header/helper/centering bytecode,
  compiled annotations/five-hook packaging, no bundled JEI/FTB classes, uninstalled
  candidate, unchanged request schema/generated method, 38 source snapshots and
  523 local links. Tracked diff check passed with CRLF warnings only. Actual Mixin
  application remains unrun; no release claim.


### 2026-09-19 — copied JEI navigation controls and resumed authentic testing

- Advanced M0.3b.3.2.3c.3.2b.3b.1b.3a to implemented_unverified. Split remaining
  .3b native preview/execute motor and .3c history Back explicitly; both not_started.
  Affects F01/F06/F09/F16, N01/N02/N04/N05/N06, C09/C15 and partial
  T01/T03/T06/T07. All aggregate results and the exact Mineflayer/E9E failure remain.
- Native GuiIconButton HEAD/RETURN capture requires four distinct ordered controls,
  unchanged operands and complete frame. Clip before flag readers; project only
  kind/state, keeping widget/geometry private. Same digest/source/body/lease/age
  and response bounds, strict Python/TypeScript controls and cross-language fixtures.
- Installed bytecode confirms ordinary mouse-down SIMULATE, mouse-up EXECUTE and
  router cleanup. Observation adds no navigation input. SPEC v0.2.22 / minor 30 /
  NativeRecipePage/3, eighteen actions and complete:false retained.
- Executed client Gradle test/build/writeTestClasspath: 350 Java pass, zero failures,
  errors/skips, 26 s. Selected Python suites: 301 pass, 39.66 s. Full Node: 134 pass,
  zero failures/skips, 62.0797557 s. Changed Python Ruff and TypeScript build pass.
  Tests use synthetic game/render authority. [Report](docs/verification/2026-09-19-jei-page-controls.md).
- Private evidence: `C:\Users\Darian\.strata\evidence\2026-09-19-jei-page-controls-01`.
  Candidate f10e7ad6ddbbf48df176183cc4e0dc60891a50d2528858ceb452b2c96a6aa625.
  User completed security prompt; fresh capture confirmed absence. Backed up old
  c2218c6c client and deployed tested candidate for a read-only authentic restart.
- No inference dispatched ($0), soak, capacity certificate or study. Next concrete
  action: authentic startup/hook and connected-observation checks; then bounded
  production-guarded API gestures and remaining complete-page/control contracts.


### 2026-09-19 — authentic E9E join, paged observations and discovery reads

- Advanced M0.3b.1a.2 and recipe/quest qualification work; .3.2.3c.3.2b.3b.1b.4
  now in_progress for deployment/precondition evidence only. F01/F05/F06/F09/F16,
  N01/N04/N06, C09/C15 and partial T01/T02/T03/T06/T07. All aggregate gates remain
  open and the failed Mineflayer/E9E profile is unchanged.
- User completed security prompt; absence observed. Backed up old client, deployed
  tested minor-30 JAR f10e7ad6…, restored pinned Java/private read-only bridge after
  CurseForge regenerated launcher settings, then launched through the authenticated
  official launcher context. No auth/security prompt was automated. Interventions
  and the initial wrong launcher-context attempt are retained in the report.
- Ran tools/check_forge_observations.py against the authentic client: disconnected
  6 pass, transport 10 pass, world 2,745 pass (20 pages/2,489 block rows), then
  disconnected-after-stop 6 pass. These are structural/bounds/body/age/cursor and
  negative-transport assertions, not full visibility/reference or action proof.
- Private read-only scripts returned 20 quest chapters, three sampled quest lists
  and text/task/reward pages, one expert Thermal iron recipe and five lava recipes.
  Empty unlocked/crafting-furnace pages are recorded without completeness claims.
  Unbound recipe_page rejected GAME_RECIPE_RENDER_UNAVAILABLE; native frame hooks
  and rendered parity remain unrun. No ordinary game API mutation was enabled.
- tools/development_server.py used the reviewed 600-second official loopback plan.
  Operator stop file produced full save/exit 0 after 532.875 s, no forced stop,
  complete logs. Client remains read-only/disconnected; no server/worker kept alive.
- An optional UI reference attempt encountered an input-state change, then the
  desktop helper reported a stop. No further computer-use call/input followed.
  Physical-key causation is unverified. No forced client shutdown or tool-state
  workaround was used. Independent evidence/ledger work continued.
- [Connected report](docs/verification/2026-09-19-forge-connected.md), private
  C:\Users\Darian\.strata\evidence\2026-09-19-jei-live-01. Credentials and launcher
  backups stay private. $0 inference; no soak/capacity/study or release claim.
- Next: fresh authority plus independent guardian, restart/rejoin and scoped API
  action/cancel/menu/recipe/machine checks; preserve required implementation gaps.

### 2026-09-19 — JEI router provenance and cancellation ownership

- Advanced M0.3b.3.2.3c.3.2b.3b.1b.3b to in_progress and split its internal
  input foundation (.1, implemented_unverified) from the charged current-page
  motor/public contract (.2, not_started). F01/F06/F09, N01/N02/N04/N05/N06,
  C09/C15 and partial T03/T06/T07; no acceptance threshold or public affordance
  changed. SPEC v0.2.22, Forge minor 30 and eighteen public actions remain.
- Added GameRecipeInput/JeiRecipeInput and three optional constructor/factory/
  router/button Mixins. Private bounded identity records confirm exact ordinary
  SIMULATE then EXECUTE callbacks. Sticky invalidation prevents phase replay;
  non-executing reset retains router ownership on failure. No private-field
  getter or callback replacement, action-lane wiring or public navigation action.
- Final Gradle test/build/writeTestClasspath: 368 Java pass, zero failures/errors/
  skips, 32 s. Eighteen new tests use synthetic callbacks and reset outcomes.
  Pinned native bytecode and compiled selector audits are separate from actual
  Mixin application. The first 34-second successful build preceded a static
  Mixin array-rank finding; corrected Object[] callback was rebuilt/retested.
  Diagnostic audit mistakes/corrections remain in the private record.
- Candidate 8e41322e4acfa4108b8ebca5af4f91c701bab8bb299e0893343cb1076b27586f
  remains uninstalled; deployed f10e7ad6… read-only state/evidence stays separate.
  [Input provenance report](docs/verification/2026-09-19-jei-input-provenance.md),
  private C:\Users\Darian\.strata\evidence\2026-09-19-jei-navigation-01.
- Explained the desktop dependency to the user: restart with guarded actions,
  launcher/server connection and actual GUI/keybinding reference checks. Normal
  character control uses the scoped API. Continued this implementation without
  computer-use calls; the helper stop remains respected and its cause unverified.
  Corrected stale current rows that still described the resolved security prompt.
- No Python/Node rerun, game mutation, inference, soak, capacity test or study.
  $0 Strata inference. All aggregate gates and the long-horizon goal remain open;
  M7 conditional. Next: .3b.2 current-page motor and safety-lane integration,
  then native hooks/input/cleanup/reference qualification when desktop resumes.

### 2026-09-19 — bounded JEI navigation through the action lane and scoped CLI

- Advanced M0.3b.3.2.3c.3.2b.3b.1b.3b/.2 to implemented_unverified. D06 / SPEC
  v0.2.23 / Forge minor 31 / nineteen actions; F01/F06/F09/F11/F16,
  N01/N02/N03/N04/N05/N06, C09/C15/C18 and partial T01/T03/T06/T07/T12.
  Prior turn classified progress; no blocked-audit accrual or changed release gate.
- GameRecipeNavigation, NativeQuestRecipeView, NativeQuests, native runtime/lane
  and scoped broker now carry strict recipe_navigate. Exact page/source/screen/
  control/geometry and input checks precede ordinary preview and later execute;
  a private fresh-frame witness confirms only emitted input. Both admissions
  require four primitive units; waiting is charged and bounded to 200 ticks
  under the existing ten-second and tighter authority limits.
- Native safety release always attempts the JEI non-executing reset, retaining
  ownership on cleanup failure and both exceptions if ordinary cleanup also fails.
  No private recipe logic or release-click cancellation. Python/JSON Schema/TS/
  Java contracts and capability identity agree; stock Mineflayer still rejects.
- Final Gradle test/build/writeTestClasspath: 383 Java pass, zero failures/errors/
  skips, 39 s. Selected Python: 328 pass, 40.63 s. Full Node before final minimum-
  budget refinement: 135 pass, zero failures/skips, 75.8680505 s. Final targeted
  Python/JVM: 3 pass (21 deselected), 10.44 s; Node: 3 pass, 6.9494057 s, covering
  unsupported/malformed selectors, four-unit admission and actual scoped CLI/JVM
  navigation. Reruns are not added to totals. Ruff/schema generation/TS build pass.
- Initial Java run: 381 tests, one failure from calling getAsInt on the correctly
  null emitted-event count after injected cleanup failure. Updated the test to
  assert durable attempted costs and unknown emissions; no weakened production
  guarantee. Intermediate 382-test run passed; the final added admission test
  produced 383. Retain original logs and synthetic process evidence privately.
- [Motor report](docs/verification/2026-09-19-jei-navigation-motor.md), private
  C:\Users\Darian\.strata\evidence\2026-09-19-jei-navigation-motor-01.
  Candidate 5053fcb666060db203cb1349aaf99b83ccb929bcdfe382176dfe27ba3ec64ad9
  remains uninstalled. Deployed f10e7ad6… read-only client and prior authentic
  observations are separate; new strict capabilities intentionally reject it.
- Desktop stop respected; no computer use or live game mutation. $0 inference,
  no soak/capacity/study. Explicitly retained cycling/empty/incomplete-page limits,
  history Back, rich/custom/overlay and actual hook/input/reference/isolation gates.
  Next: ordinary history motor and remaining complete-page/lifecycle work, plus
  guarded native qualification when desktop input resumes. Goal remains active.

### 2026-09-19 — ordinary recipe-history Back

- Advanced M0.3b.3.2.3c.3.2b.3b.1b.3c to implemented_unverified. Exact installed
  JEI bytecode confirms its Back handler uses concrete RecipesGui.back(), with
  empty history a no-op. This is not an IRecipesGui API or physical-key test.
- GameRecipeNavigation/NativeQuestRecipeView, native lane, Python/TypeScript
  contracts, Forge capability minor 32 and scoped CLI now accept history_back.
  Retain current-page/source/screen authority and fresh-frame confirmation;
  callback/frame-check/release admission costs three units. No private history
  reads, Close fallback or replay. SPEC v0.2.24 records the explicit policy.
- F01/F06/F09/F11/F16, N01/N02/N03/N04/N05/N06, C09/C15/C18 and partial
  T01/T03/T06/T07/T12 advance. Twelve added Java cases cover positive/no-op and
  failure paths; synthetic history is explicitly supplied by the fixture.
- Actual Gradle test/build/writeTestClasspath: 395 pass, zero failures/errors/
  skips, 42 s. Sixteen Python suites: 329 pass, 41.78 s. Full Node: 136 pass,
  zero failures/cancelled/skipped/todo, 76.64169 s. Ruff, schemas, TypeScript
  generation/build and evidence/link/diff checks pass. No broad rerun afterward.
- [Report](docs/verification/2026-09-19-jei-history.md); private logs, compiled
  inspections, source hashes and collector at
  C:\Users\Darian\.strata\evidence\2026-09-19-jei-history-01.
  Candidate 1323c60f3d99ccfee4c7f7df477769c33ad7859610fc8d9f684fc5bbd7acc9e4
  is uninstalled. The deployed minor-30 read-only client remains unchanged.
- Desktop input remains paused. Clarified that GUI work is for launcher setup
  and testing the bridge's native rendering/input behavior; routine avatar
  actions use the scoped API. No game mutation or inference ran; $0 dispatched.
  Populated/empty native Back, full content, physical-key parity, hooks, timing,
  reference and isolation gates remain open. Next: empty-layout render handling
  under .1b.2b.2 and guarded live qualification when desktop input resumes.

### 2026-09-19 — witnessed empty pages and shared-desktop constraint

- Previous goal turn made progress through ordinary history Back. This turn
  split .1b.2b.2 into empty-loop handling (.a) and remaining rich/custom/overlay
  content (.b); advanced .a to implemented_unverified, keeping native .1b.4 open.
- Audited the exact installed JEI draw loop. Extended JeiLayoutsDrawMixin and
  GameRecipeRenderCapture to observe the existing iterator predicate once and
  pair each true with one completed draw, requiring terminal false/normal return.
  Missing hooks or unfinished draws cannot masquerade as an empty page. Public
  GameRecipePage/native protocol, Python/TypeScript validators and capabilities
  now use SPEC v0.2.25 / Forge minor 33 / NativeRecipePage/4. Nineteen actions and
  motor charges remain. No extra iteration, private list reads or exposed iterator.
- Actual Gradle test/build/writeTestClasspath: 405 pass, zero failures/errors/
  skips, 38 s, including ten additional tests. Sixteen selected Python suites:
  330 pass, 41.45 s. Full Node: 136 pass, zero failures/cancelled/skipped/todo,
  76.4166114 s. JVM/HTTP/scoped CLI navigate to a synthetically empty page and
  Back. Ruff, schema export, TypeScript build, compiled hook, pins, source/link
  and diff checks pass. All render/history effects in these tests are synthetic.
- [Report](docs/verification/2026-09-19-jei-empty-page.md); private evidence at
  C:\Users\Darian\.strata\evidence\2026-09-19-jei-empty-page-01.
  Uninstalled candidate 4db8ae89f0e095653eee8a05f745409073f1196f495e8796291a53c3030d8171;
  installed minor-30 f10e7ad6… remains unchanged. Actual hooks, reachable empty
  pages, visual/reference/native timing and isolation remain unqualified.
- User clarified that lengthy computer use prevents them from using their
  computer. Keep desktop input paused. Routine effects should be verified through
  scoped API state and independent server evidence. Source audit found idle-input
  and native pointer-restoration behavior and screenshots:false, not proof of
  a safe background client. Prioritize unattended verification/isolation under
  .2c.3c/.1b.4, with separate graphical execution for long UI/physical-key checks.
  Do not weaken T03/T05 or treat API success as independent visual evidence.
- F01/F06/F09/F11/F16, N01/N02/N03/N04/N05/N06, C09/C15/C18 and partial
  T01/T03/T06/T07/T12 advanced. No desktop input, game launch/mutation or
  inference occurred; $0 dispatched. No aggregate gate or milestone closes.

### 2026-09-19 — bounded non-input desktop launch and graphics prerequisite

- Previous goal turn advanced witnessed empty pages. This turn split
  M0.3b.2c.3c into launch foundation (.1, implemented_unverified) and production
  client/guardian/isolation qualification (.2, not_started). SPEC v0.2.26 records
  the user's shared-desktop availability constraint without changing gameplay
  affordances or waiving physical-key acceptance cases.
- Added operator-only DesktopProcess, disposable Windows fixtures/tests and a
  test-only Java graphics fixture/probe. A fresh non-input desktop receives an
  exact environment and suspended child; the existing kill-on-close job owns it
  before resume. Bounded watchdog, startup failure, owner-crash, orphan and
  cleanup paths do not switch desktops or inject input. Same-user desktop/job
  placement is not credential/filesystem/process/network isolation.
- Initial one-test failure exposed the venv redirector PID assumption and
  redundant termination during asynchronous job stop; both were corrected.
  Eight launch tests then passed in 2.72 s. Final combined pytest execution of
  test_desktop_process.py, test_processes.py and test_gameplay_package.py had
  18 passes (12 launch, 6 process) and one stale package-help assertion failure,
  7.20 s. Corrected the existing recipe-query assertion and kept explicit launcher
  exclusion; focused test_gameplay_package.py rerun passed, 0.29 s. Failed logs
  remain retained; this is not a claim of a single clean 19-test run.
- Gradle :forge1192-client:compileTestJava and writeTestClasspath passed in 16 s.
  tools/probe_desktop_render.py with the pinned JDK/test classpath passed twenty
  hidden/unfocused OpenGL 3.2 color/readback frames on the actual RTX 3090 stack,
  unchanged input desktop, exit 0: initial 398 ms and final fingerprinted rerun
  393 ms. Missing empty Gradle resources/test output initially failed preflight;
  that directory was created. Existing-output preflight still rejects reuse.
  Ruff and source/artifact/link/diff checks pass. No broad game suite rerun.
- [Report](docs/verification/2026-09-19-desktop-launch.md); private logs, probe
  outputs, source copies/hashes and collector are under
  C:\Users\Darian\.strata\evidence\2026-09-19-desktop-launch-01.
  Forge candidate 4db8ae89f0e095653eee8a05f745409073f1196f495e8796291a53c3030d8171
  remains uninstalled; deployed minor-30 f10e7ad6… is unchanged. The graphics
  fixture is absent from the mod JAR. F06/F09/F16, N01/N02/N03/N04/N05/N06/N08,
  C02/C09/C15/C18 and partial T01/T06/T07/T12 advanced; no gate closes.
- No computer-use input, Minecraft launch/mutation, authentication UI automation
  or inference ran; $0 dispatched. Next: dedicated actual-client launch and
  private game-only visual evidence integrated with the independent guardian,
  then authentic focus/render/input and security/resource qualification. Keep
  the user's desktop usable and all required M0–M6 work visible; goal active.

### 2026-09-19 — guarded actual E9E startup on a non-input desktop

- Previous turn made progress through launch/graphics evidence and durable
  reconciliation. This turn split .2c.3c.2 into bounded operator startup (.a) and
  full frames/worker/security qualification (.b). Added DesktopJava and four
  disposable real-JVM lifetime/fault tests. Independent fresh challenges stop
  Java when the caller stalls; guardian crash cannot become a successful stop.
  Journals are exclusive, bounded and forced to disk, with no args/env/nonces.
- Actual pytest tests/test_desktop_client.py: 4 pass, 7.37 s. Focused
  test_gameplay_package.py: 1 pass, 0.31 s, explicit launcher exclusion retained.
  Ruff and source/artifact/link/diff evidence checks pass. No full Java/Node or
  paid test suite was rerun; the production mod JAR did not change.
- Inspected actual official installed parent/Forge metadata. Initial preparation
  rejected a mismatched base vanilla-client JAR; retained that finding and used
  the Forge-profile JAR that matches Mojang's exact download digest. Verified
  selected library/index/logging/game artifacts, preserved 93 classpath entries,
  Windows rules and Forge overrides. Copied 9,862 files to a private test client;
  retained expert/config/resource content, omitted saves and account/server-list
  caches. Source CurseForge profile was not changed. This direct JVM bootstrap
  is explicitly distinct from automating the official launcher UI.
- First cached-session preparation failed on a local compiled-module path before
  authentication. Corrected dist/src paths; cached Java-owning account refresh
  succeeded without GUI sign-in. Protected temporary session arguments were
  retired after the run; original cache retained. No credentials in public logs.
- Actual exact E9E1.27.0/MC1.19.2/Forge43.4.23/Temurin17.0.20.101 run loaded
  minor-33 candidate 4db8ae89… in the private copy. Read-only title bridge ready
  after 171.266 s, listener owned by held Java PID, ten capability reads and ten
  expected disconnected observations pass. Guardian confirmed requested forced
  termination in 329 ms; total 175.172 s; input desktop unchanged. Subsequent
  held-process inspection confirmed owned PID absent. No world join, server
  launch, game mutation, input injection, worker, inference or campaign occurred.
- [Report](docs/verification/2026-09-19-desktop-client.md), private evidence at
  C:\Users\Darian\.strata\evidence\2026-09-19-desktop-client-01;
  stopped copy C:\Users\Darian\.strata\clients\e9e-noninput-01.
  Original CurseForge minor-30 f10e7ad6… unchanged. SPEC v0.2.27 records the
  operator path; .2a implemented_unverified for production. F01/F05/F06/F09/F16,
  N01/N02/N03/N04/N05/N06/N08, C02/C04/C09/C15/C18 and partial
  T01/T02/T03/T06/T07/T12 advance. All aggregate gates remain incomplete.
- Next: private bounded game-only frame evidence under .2b/.1b.4, actual native
  focus/render/pointer/physical-key qualification, world/worker/guardian and
  independent server evidence. Desktop/job placement is not a security sandbox;
  forced stop is not a clean checkpoint. Preserve all M0–M6 and conditional M7.
  $0 Strata inference dispatched; active goal, no genuine impasse this turn.

### 2026-09-19 — bounded private frame requests and actual E9E imagery

- Previous turn made progress through guarded unattended title startup. This
  turn split .2c.3c.2b into private frames (.1) and full world/worker/reference/
  security qualification (.2). Added PrivateFrames, ClientFrameProbe and a
  separate optional exact MinecraftFrameMixin/config, preserving the existing
  nine JEI hooks and public minor-33 structured/screenshots:false contract.
- Exact mapped/native callsite audit selects pre-Window.updateDisplay after
  main-target blit. Native Screenshot readback/PNG restores texture/pack alignment
  and rejects unsupported pack state, texture size and noRender. Four frames,
  one-second spacing, ten-minute session, 1920×1080/12 MiB PNGs and 4 KiB strict
  requests bound execution. Durable intent precedes readback; failure retains
  partial files and disables capture. UTC plus monotonic request expiry prevents
  backward-clock extension. No arbitrary path, GUI/input action or public image.
- Full Java test/build/writeTestClasspath passed, 28 s, after nine new tests.
  Focused nine-test build passed, 15 s, after noRender rejection. Final focused
  ten-test/build passed, 16 s, after the monotonic-expiry regression; final XML:
  ten tests, zero failures/errors/skips. Synthetic PNG/clock/file tests do not
  qualify native GPU failure/reference behavior. No broad Python/Node/paid rerun.
- Initial authentic run initialized the hook but rejected vanilla TitleScreen
  before pixels/intent; stopped in 128.875 s, input desktop unchanged. Installed
  PackMenu bytecode confirms ExtendedMenuScreen subclass; fresh-run request used
  that exact class without weakening the guard. Final startup ready 122.703 s;
  two 854×480 frames captured, 930,916 and 943,899 bytes, 141.7151/101.2564 ms.
  Independent CRC/zlib/scanline/hash checks and actual image inspection pass;
  first frame shows loading-overlay fade, second clear Enigmatica menu. Small-
  window footer overlap and capture's main-target-only coverage are recorded.
- Deliberate wrong-screen request 3 fails; correcting it cannot create another
  intent/image. Read-only API survives diagnostic failure; guardian requested stop
  confirms in 235 ms, total 127.5 s, input desktop unchanged. Latest owned PID
  confirmed absent. Both temporary session argument files retired; frame ACL
  verification passes for operator/SYSTEM. Same-user isolation is unqualified.
- [Report](docs/verification/2026-09-19-private-frames.md); private source/JAR,
  XML, callsite/PackMenu audit, retained failures, frames, decoder/visual evidence
  and collector under C:\Users\Darian\.strata\evidence\2026-09-19-private-frames-01.
  Candidate/private-copy ef06b88892ea06f551d137ed0c0fc8bba99e5e5cfe8577b7d517207619a5d88a;
  original CurseForge minor-30 f10e7ad6… unchanged. Manifest-folding verification
  and the driver's frames-02 summary-member quirks are retained/documented.
- SPEC v0.2.28; .2b.1 implemented_unverified. F01/F06/F09/F16,
  N01/N02/N03/N04/N05/N06/N08, C02/C09/C15/C18 and partial
  T01/T03/T06/T07/T12/T13 advance. Source/artifact/link/diff checks pass.
  No world join, server launch, game action, desktop input, inference or campaign;
  $0 dispatched. Next: authentic world/worker/guardian and private GUI/reference
  integration, complete native input/graphics/resource/isolation qualification.
  All required M0–M6 and conditional M7 remain; active goal, progress this turn.

2026-09-19 — Private-frame evidence collection finalized for
M0.3b.2c.3c.2b.1. The collector's development-name assertion failed against the
reobfuscated artifact; pinned SRG mappings verified the actual texture/pack-state
calls. Corrected collector passed 585 links, 13 source snapshots, artifact and
callsite checks, and git diff check. Evidence: private-frames-01/verification.json
in the private evidence directory documented above. Client bytes and test scope
unchanged; no new game or inference run. Next remains world/worker/guardian
integration; no aggregate gate or milestone closed.

2026-09-19 — Native startup world integration (M0.3b.2c.3c.2b.2a;
F01/F06/F09/F16, N01/N02/N03/N04/N05/N06/N08, C02/C09/C15/C18;
partial T01/T03/T06/T07/T12/T13). Progress; no aggregate gate closure.
- ClientGameBridge supports native --server startup that skips TitleScreen,
  requiring an unobstructed RenderTick.END for the same player/level/connection.
  GameStartupReadiness rejects partial, obstructed and stale-body readiness.
  GameBodyEndpoint preserves menu-joined identities and uses the actual resolved
  TCP peer/port when native startup has no saved-server entry. No guessed server
  data, DNS fallback or new gameplay join operation. Source links and exact
  native callsites are in [world startup evidence](docs/verification/2026-09-19-desktop-world.md).
- Retained first actual failure: authenticated server join, but old body identity
  returned GAME_NOT_CONNECTED; guardian terminal receipt failed generically.
  Client subsequently absent. Typed guardian failures now retain a bounded reason
  in the private journal, without exception text or a false stop confirmation.
  Existing challenge/wall/500 ms confirmation limits remain unchanged.
- Retained second run: initial 500 ms identity read returned
  GAME_OBSERVATION_UNAVAILABLE; precise cause unproven. Third run completed a
  traced 5 s startup identity read, then capabilities timed out/unavailable after
  5,015 ms while startup recipe/book/JEI work was still logged. Neither failure
  was hidden or relabeled as a successful observation suite. The new render
  readiness barrier was added before the fourth run.
- Verification: offline :forge1192-client:test :forge1192-client:build passes
  415 tests / 32 s, then 420 / 33 s, then 424 / 29 s, all zero failures/errors/skips.
  Five endpoint and four readiness tests are synthetic. Python initially 9 pass /
  15 skip because the JVM classpath was absent; after supplying it, all 18
  test_process_guard.py cases pass in 19.14 s. Six test_desktop_client.py cases
  passed in the first invocation. One gameplay-package/CLI exclusion check passes
  in 0.28 s. Disposable JVMs and package layout do not prove live timing/isolation.
- Fourth actual check: exact E9E 1.27.0 / MC 1.19.2 / Forge 43.4.23, authenticated
  native loopback connection under a fresh non-input desktop. Ready in 186.219 s;
  2,745 world assertions (20 pages / 2,489 blocks / no entities), 10 transport
  rejection assertions, ten 500 ms identity reads at 47-156 ms, and six
  disconnected assertions pass. Two 854x480 world PNGs independently decoded and
  inspected: Twilight Forest scene and HUD, with no operator desktop content.
  Capture work 86.9496 / 68.0227 ms. These do not establish complete visibility,
  machine/menu, compositor/cursor or physical-key parity.
- All four servers saved/stopped normally, exit 0 and complete logs: 396.937,
  406.704, 374.953 and 380.781 s. Subsequent three guardian stops confirmed in
  469 / 422 / 453 ms; the first failure remains unresolved. Final client total
  211.484 s, owned PID confirmed absent, input desktop unchanged. All four
  temporary session-argument files retired. No native action lane, worker, host,
  campaign or Strata inference; $0 dispatched.
- Final private-copy minor-33 JAR:
  234c2d5689386e9f7799a3605fb84776d52e72e73f2e82cc891343a4a4c5ebae.
  Original CurseForge minor-30 f10e7ad6... unchanged. Dedicated-copy
  pauseOnLostFocus:false is explicit engineering configuration; no new cohort or
  physical-input waiver. D05/D06 and the user's shared-desktop availability
  constraint authorize this setup/test path; no scope or acceptance reduction.
- Private evidence and collector:
  C:\Users\Darian\.strata\evidence\2026-09-19-desktop-world-01,
  retaining live/, retry/, attempt-03/ and successful attempt-04/ separately.
  Next: .2b.2b bounded startup to worker-owned Forge guardian/native authority,
  scoped CLI actions/cancellation, then full .2b.2c/.1b.4 references, input,
  resources and security principals. All required M0-M6 and conditional M7 remain.
- Final collector passed: 16 source snapshots, 594 local documentation links,
  97 bootstrap pins, candidate/original-profile hashes, private frame decoding
  and ACL verification, retired credentials and tracked diff check. Exact output
  is verification.json in the evidence directory above; no aggregate gate pass.


### 2026-09-19 — Worker trial and native startup session lifetime

- Scope: M0.3b.2c.3c.2b.2b and new M0.2g.1; F01/F06/F09/F16,
  N01/N02/N03/N04/N05/N06/N08; C02/C09/C15/C18; partial
  T01/T03/T06/T07/T12/T13. SPEC v0.2.29 preserves all gates and affordances.
- Prepared operator-only composition of fenced DesktopProcess startup, immutable
  native authority, the worker-owned Forge guardian and scoped CLI actions.
  Private run budgets: 480-second client, 90-second worker, 1,000 primitive units,
  600-second server; no desktop switching/input injection or inference.
- Before repair: npm test reports 111 pass / 25 skipped / 0 fail, 5.577 s;
  enabling pinned Java 17/Python 3.12.14 fixtures gives all 37 Forge tests pass,
  64.343 s, including 12 overlapping cases. Synthetic fixtures are separate from
  actual Minecraft evidence.
- First authentic attempt fails before login: GAME_BRIDGE_STARTUP_TIMEOUT at the
  280-second startup bound. Owned client stopped; total 284.516 s; input desktop
  unchanged. Server saved/stopped normally, 405.563 s, exit 0, complete logs.
  Token had 88.480 seconds at preparation and had expired 50.928 seconds before
  launch. Private-key retrieval failures and later profile HTTP 401 retained.
  No worker/action/image checks ran. Temporary arguments retired after PID absence.
- Implemented optional minimum-lifetime policy in authentication.ts and
  session_lifetime.ts: suppress only the short-lived Minecraft cache entry from
  a read, preserve Microsoft/Xbox credentials, use ordinary provider refresh,
  recheck returned expiry before binding, reject unknown/malformed/short expiry.
  JWT expiry is a reuse restriction, not signature/account verification.
- Actual build passes. Fourteen targeted compiled authentication/dependency/
  session-lifetime tests pass, no failures/skips, 5.670 s. Tests use synthetic
  credentials and the real pinned token manager's refresh decision. One compiled
  gameplay-package exclusion/CLI test passes, 0.36 s. Existing vanilla default
  authentication and public schemas/19 action kinds remain unchanged.
- First collector: 18 source snapshots, 97 bootstrap pins, four protected-path
  ACL checks, normal-stop private telemetry (277 records), no native/guardian
  frames; zero-frame checks are not_run. Raw failure and session timing remain
  under C:\Users\Darian\.strata\evidence\2026-09-19-forge-worker-live-01.
  Authentication verification metadata explicitly cites captured command output.
- Fresh retry-01 uses a new scope, new authority/grants and refreshed session,
  requests 20 minutes at preparation and rechecks client lifetime plus 30 seconds
  immediately before launch. Client JAR remains 234c2d56...; changed compiled
  broker identity is recorded, with all 33 modules archived. This follow-up is
  in progress; its result must be recorded separately. No campaign admission,
  aggregate gate or milestone closure; $0 Strata inference dispatched.


### 2026-09-19 — Refreshed session joins; startup identity read unavailable

- Fresh retry-01 passed prelaunch lifetime with 86,206,333 ms remaining.
  Independent server logs confirm authenticated login/join; no profile-key
  retrieval errors. Its first identity read returned GAME_OBSERVATION_UNAVAILABLE,
  so worker/actions/guardian were not run. Raw world_joined:false means the
  driver's verification was incomplete; it is not evidence of a failed join.
- Client/check 209.953 s; outer owned job cleanup, input desktop unchanged.
  Server saved/stopped normally in 386.000 s; zero forced stop, complete logs.
  Native journal contains one profile frame and no armed/action lane. Full
  private telemetry has 200 records. Collector retained 18 source snapshots,
  33 compiled broker modules, 97 bootstrap pins and four ACL checks; account
  arguments retired after actual process absence. No inference or gate pass.
- Read timeout cause is unproven. Diagnostic retry-02 keeps exact Java/Node
  bytes and fresh scope/authority/session, records transport responses and up
  to six bounded read-only startup probes inside the original startup budget.
  A first unavailable read may trigger one private bounded jstack diagnostic
  before arming. This is a recorded intervention, not campaign timing evidence.
  No mutation retry, changed guardian deadline or acceptance reduction.
  GI/QA continue .2b.2b; M0.2g.1 remains implemented_unverified overall.


### 2026-09-19 — Diagnostic native-read failure isolated to client-thread initialization

- retry-02: same exact native/broker artifacts as retry-01; session lifetime at
  launch 85,619,670 ms. Six identity probes fail at five seconds each. All 456
  HTTP exchanges (six POSTs, 450 GETs) return valid accepted responses, with no
  completed response. This is retained failed evidence, not a successful retry.
- One bounded private jstack attachment, exit 0, samples the render thread inside
  Shapes/SupportType/BlockBehaviour cache construction under Blocks and
  ClientPacketListener handling ClientboundUpdateTagsPacket. HTTP workers are
  waiting for work. It proves that client-thread initialization at the sampled
  instant; it does not prove that exact stack persisted for all thirty seconds
  or retroactively explain retry-01's untraced unavailable response.
- No native arm, worker, guardian, action or image check ran. One native profile
  journal frame. Client/check 262.000 s; outer job stopped the owned client.
  Input desktop unchanged. Server saved/stopped normally, 444.078 s, exit 0,
  complete logs. Private telemetry has 249 records, about 19.76 sampled TPS.
  All three worker-trial boots pass the six expert-furnace metadata assertions;
  no player crafting or machine-effect qualification follows from that.
- All three clients and servers now stopped; process absence and argument
  retirement confirmed. Retry collectors check all 33 archived compiled broker
  modules, 97 bootstrap pins, protected paths and journal framing. Empty guardian
  streams remain not_run. Initial evaluator import-path collection failure was
  repaired in the private collector; no live rerun was used to repair collection.
- Split .2b.2b into .1 same-connection initial synchronization readiness (in_progress,
  diagnosis only) and .2 actual scoped worker/guardian/action conformance
  (not_started; checker never reached). Next: audit exact tag/recipe event
  completion and lifecycle, implement/test readiness, then rerun the bounded
  worker trial without relaxing real action/guardian limits.
- Delivered code is the session-lifetime authentication seam, with 14 targeted
  tests and one package check passing. Startup readiness repair, actual worker
  actions, full 19-action support, physical-key/menu parity, isolation, native
  host/accounting, soaks, N-body capacity and research gates remain open.
  No milestone/MVP completion or Strata inference; $0 dispatched.

### 2026-09-19 — initial synchronization readiness candidate

- Advanced M0.3b.2c.3c.2b.2b.1 to implemented_unverified; retained all three
  earlier worker-startup failures. [Report](docs/verification/2026-09-19-forge-readiness.md)
  maps F01/F06/F09/F16, N01/N02/N03/N04/N05/N06/N08,
  C02/C09/C15/C18 and T01/T03/T06/T07/T12/T13. SPEC v0.2.30 records the
  implementation policy without changing public affordances or release gates.
- Audited the exact mapped Forge client packet handlers and Forge event sources.
  Tag events occur after the observed block-cache rebuild path; recipe events
  follow replacement/book/search updates. ClientGameBridge filters current-thread,
  client-packet and exact registry/recipe-manager identities; GameStartupReadiness
  requires synchronization plus a later unobstructed same-body frame/tick.
  NativeGameRuntime rejects pending identity/observation/action preconditions.
  Tracking continues after startup, including title-screen joins. Ordinary menus
  retain qualification; reconnect/partial/replaced bodies cannot reuse it blindly.
- Executed offline Java test/build/classpath tasks: 433 pass, no failures/errors/
  skips, 38 seconds, including 13 focused lifecycle tests. Raw build log, XML,
  source snapshots and reobfuscated bridge inspection are private under
  `2026-09-19-forge-readiness-01`. Candidate 06f29980… installed only in the
  dedicated client copy after old-client absence, original-profile and 97 bootstrap
  hash checks. A fresh read-only authentic trial is in progress; local lifecycle
  evidence is not a timing, physical-input, worker/guardian or campaign pass.
- No action/guardian deadline, lease, primitive budget, public screenshot setting
  or inference authorization changed. Next: complete the authentic readiness run,
  retain its actual fingerprint, then retry scoped worker/actions with a new
  immutable authority. Same-user isolation, all M0–M6 gates and $0 dispatched
  inference remain explicit.

### 2026-09-19 — authentic readiness and first guarded worker findings

- [Readiness report](docs/verification/2026-09-19-forge-readiness.md) records the
  successful read-only candidate run: 233.454 s startup, 2,745/10/6 assertions,
  ten identity reads at 47–125 ms, two decoded/inspected world frames, 359 ms
  base-guardian termination, server normal save/stop and 287 telemetry records.
  One package test passes in 0.38 s. Input desktop unchanged and credentials
  retired; this does not qualify full worker or physical-input behavior.
- The new candidate's worker-01 reaches native readiness in 229.657 s, attaches
  its Forge-aware guardian, arms, and emits one scoped look action. Its fresh
  observation changes pitch by about 1.102 radians. The operator checker compares
  against 5 intending degrees, so it fails and issues stop-all before all other
  action cases. Both captured frames and a separate saved-player pose audit
  corroborate camera change; original checker result stays fail. Corrected next
  checker uses radians and the intended five-degree threshold; saved-player
  comparison converts Minecraft axes/degrees. No gameplay behavior is changed.
- Worker executor drains normally at 90 s, but guardian failure lacks a confirmed
  stop receipt; supervisor exits 1. Its exact internal cause was discarded by
  the adapter and remains unknown. Subsequent client absence/exit 125 is not a
  timely-stop pass. Client/check 337.110 s; server normal stop 510.344 s; 321 telemetry
  records, 11 native frames, seven supervisor frames, one action/four reconciled
  primitives. Input desktop unchanged; no refund or inference.
- Forge guardian now uses the existing bounded failure sanitizer, and Node
  validates/retains the exact private failed event without changing generic
  supervisor rejection or claiming termination. Relevant IDs: M0.3b.2c.3b and
  .3c.2b.2b.2, F09/F16/N01/N02/N04/N05/N06/N08, C15/C18, T01/T06/T07/T13.
  Node build, two focused evidence/negative tests, six guarded synthetic-game
  process integrations, and two Python main-failure tests pass. Raw logs are in
  the private readiness root. No lease/action/stop deadline changes.
- Fresh worker-02 is underway with new immutable scope/authority, corrected
  operator checker and separately pinned broker/Python identity. Candidate JAR
  stays 06f29980…. Prior failures remain. Next: retain actual results, qualify
  cancel/fencing/stop behavior and continue independent mechanic/reference work;
  no aggregate milestone or gate closes.

### 2026-09-19 — corrected scoped actions and explicit stop failure

- Worker-02 on candidate 06f29980… reaches native readiness in 230.469 s,
  without read retry, attaches the independent Forge guardian and arms. Sixteen
  public CLI requests pass look, known-terminal deduplication, held-use
  cancellation/confirmed release and post-fence LEASE_EXPIRED rejection. Dig
  emits; independent server block/resource effect evidence remains unrun.
  Cancellation requires resync, and no uncertain action is replayed.
- The executor exits 0 after its 90 s lifetime. Guardian now retains the exact
  failed receipt PROCESS_STOP_UNCONFIRMED, termination_confirmed:false, about
  517 ms after the executor-exit record. The existing 500 ms process-exit wait
  fails; supervisor exits 1. Overall live result stays fail despite the narrow
  CLI pass. The underlying teardown latency and first worker's discarded cause
  remain unresolved. Client later exits 125 before outer cleanup; no desktop
  watchdog trigger or deadline increase. This is not a confirmed timely stop.
- Server saves/stops normally: 504.485 s total, exit 0, complete logs. Client/check
  335.500 s; 318 telemetry records and expert furnace metadata assertions pass.
  Collector validates 31 native frames, eight supervisor events, three actions
  and 14 reconciled primitive charges. Three saved-player pose comparisons pass
  after unit/axis conversion; two 854×480 PNGs decode and were inspected. Images
  do not supply independent block/resource, quest-score or full GUI proof.
- All three readiness-root clients/servers are stopped; original profile remains
  unchanged, client absence and temporary-argument retirement confirmed, input
  desktop unchanged. The [report](docs/verification/2026-09-19-forge-readiness.md)
  and current ledger distinguish the passing read-only and CLI subsets from
  failed shutdown. F01/F06/F09/F16, N01/N02/N03/N04/N05/N06/N08 and
  T01/T03/T06/T07/T12/T13 remain partial. No aggregate gate closes or inference
  spend occurs. Next: diagnose the bounded process stop, then complete authentic
  mechanic/reference and remaining M0–M6 qualification without desktop takeover.

### 2026-09-19 — bounded stop diagnostics and private intent evidence

- Advanced M0.3b.2c.3c.2b.2b.2 without changing status or its existing failure.
  [Stop report](docs/verification/2026-09-19-stop-latency.md) maps the partial
  F/N, contract and test coverage. `forge_guard.ts` now durably records private
  stop intent before pipe dispatch; it retains failure fencing and the existing
  independent lease/500 ms wait. No public capability change.
- Node build and six targeted guarded integration tests pass: 36.827 s,
  no failures/skips. Normal drain checks the new event's ordering and journal
  chain; mismatched grants and native/worker/parent faults retain coverage.
  Actual disposable processes use synthetic game effects.
- Five private heap/render probes pass the unchanged production wait. Reported
  stop-method durations are 15/94/250/47/297 ms, but Python's GetTickCount64 clock
  has 15.625 ms resolution. Retain these coarse values and the initial missing
  empty-classpath-directory preflight failure. One sample per condition cannot
  establish a performance certificate or explain real Minecraft's failure.
- Fresh authentic trial uses the unchanged 06f29980… native JAR, new authority
  and broker pins, corrected checker, and a bounded read-only held-process/QPC
  observer. Evidence stays under private `2026-09-19-stop-latency-01`; separate
  non-input desktop and existing lifetimes remain. No OS input or inference.
  Next: retain actual exit/memory/CLI/server results, preserve any failure, then
  resolve the shutdown and independent mechanic/reference gates.

### 2026-09-19 — authentic stop observer preserves the 500 ms failure

- Fresh non-input E9E worker trial reaches readiness at 165.328 s, no identity
  retry. Seventeen CLI calls pass look/known-terminal dedup, held-use cancel and
  post-fence rejection; dig is emitted only. Three actions and 13 primitive
  charges retained. Saved-player rotation/position/dimension match; both world
  frames independently decode and were inspected. No block/resource proof.
- Executor exits 0, but supervisor exits 1 with PROCESS_STOP_UNCONFIRMED.
  Private stop intent to failed receipt is 510 ms on the supervisor clock.
  Read-only observer: 108 records/96 memory samples; working set falls from
  5.744 GB before intent to 0.368 GB during teardown. Exit is seen 489.833 ms
  after observed intent, with a 15.359 ms final wait bracket. Those timestamps
  are not the kernel-call start; visibility/scheduling uncertainty and a maximum
  nominal 10 ms wait span of 78.998 ms prevent a sub-500 ms termination claim.
  Failure remains failure. Exact cause is unresolved; next measure job/wait
  boundaries without changing deadlines or gameplay authority.
- Client exits 125 before outer cleanup; client/check 269.797 s. Server saves
  normally in 404.672 s, exit 0, complete logs. Evidence has 28 native journal
  frames, nine supervisor events and 274 telemetry records. Input desktop and
  original profile unchanged, client absent, arguments retired, no inference.
  [Report](docs/verification/2026-09-19-stop-latency.md) retains all limits and
  previous failures. M0–M6 and all aggregate gates remain open; M7 conditional.

### 2026-09-19 — direct guardian job/wait timing

- Continued M0.3b.2c.3c.2b.2b.2 from the prior authentic failure, which was
  progress rather than an unchanged blocker. [Direct timing report](docs/verification/2026-09-19-stop-boundaries.md)
  maps F01/F06/F09/F16, N01/N02/N03/N04/N05/N06/N08,
  C09/C14/C15/C18 and partial T01/T03/T06/T07/T12/T13.
- `AttachedJava` now records process-local QPC boundaries and distinct job/wait
  outcomes. Forge-only private evidence queues after owned handle cleanup;
  Node validates exact shape/order/bounds and requires a separate confirmed-stop
  receipt. Base wire contract, native JAR, public actions and all deadlines stay.
  SPEC v0.2.31 records the diagnostic contract; no acceptance threshold change.
- Six new Python fault/timing-order tests pass (0.14 s); complete two guardian
  modules pass 33 tests (30.01 s, including those six). Node build and ten selected
  evidence/process integration cases pass (36.902 s), no failures/skips. Actual
  fixture processes have synthetic game effects. Five owned-event waits measure
  500.1985–515.3868 ms for the existing 500 ms timeout; no early timeout observed.
- New immutable scope/grants and broker/Python pins prepared in protected
  `2026-09-19-stop-boundaries-01/worker-01`; 06f29980… native candidate unchanged.
  Authentic run preparing on the separate non-input desktop. No inference or
  OS input. Next: collect actual job/wait timing, preserve any failure and charges,
  and use the result to choose a concrete shutdown repair without changing bounds.

### 2026-09-19 — first combined scoped-worker and timely normal-stop pass

- [Direct timing trial](docs/verification/2026-09-19-stop-boundaries.md) passes its
  bounded operator procedure on unchanged native candidate 06f29980… and fresh
  broker/Python pins. Ready at 209.906 s, zero identity retries. Seventeen CLI
  calls pass look/known-terminal dedup/use cancel/release/post-fence rejection;
  dig is emitted only. Three actions retain 13 reconciled primitive charges.
- Executor and supervisor exit 0. Guardian's own QPC records job return at
  1.2930 ms, wait start 1.2980 ms and signaled return 491.1453 ms after start:
  wait duration 489.8473 ms, unchanged 500 ms bound. Separate terminal receipt
  confirms termination, not input release or a clean checkpoint. Independent
  held handle brackets exit at 464.4048–491.0198 ms after that same-host QPC
  start. Its maximum nominal 10 ms wait span elsewhere is 189.1885 ms; retain
  this scheduling variability. Last pre-call working set is 5.434 GB.
- Prior failures remain failures. The roughly 10 ms wait margin and unchanged
  termination behavior prevent calling this a repair/reliability certificate.
  Most measured stop time in this passing sample is waiting for exit; capture
  the same boundaries on a failure to resolve resource/OS contribution.
- Client exits 125 before outer cleanup; client/check 314.875 s. Server saves
  normally, 509.390 s, exit 0 and complete logs. Two PNGs decode; saved-player
  rotation/position/dimension match. Collector validates SQLite/charges, 29
  native journal frames, eight supervisor events and 327 telemetry records.
  Original profile/input desktop unchanged, arguments retired, all processes
  stopped. No inference or campaign admission. All M0–M6 aggregate gates remain
  open; M7 conditional. Continue independent block/resource and other mechanics
  alongside reliable stop qualification.

### 2026-09-19 — independent saved-block reference foundation

- Continued M0.3b.2c.3c.2b.2c as separate saved-reference (.1) and remaining
  world/menu/machine/input/resource/security (.2) work. Added the already-used
  but absent M0.3b.1b.4 ledger row. [Evidence](docs/verification/2026-09-19-saved-block-reference.md)
  maps F01/F06/F10/F13/F16, N01/N04/N06/N08, C09/C19 and partial
  T01/T03/T06/T10/T13. All original scope and aggregate gates remain open.
- Added evaluator-only `saved_blocks.py`: exact 1.19.2 Anvil location/framing,
  gzip/zlib/raw and external streams, bounded NBT/modified UTF-8, dimension paths,
  local palettes and selected states. Unsupported/incomplete/corrupt sources
  reject; no guessed air, server write, public route or causal/scoring credit.
  Independent pinned bytecode audit corrects initial Status assumption to the
  actual `getName()` output `full`; local packing and index order checked.
- Executed Python parser plus compiled gameplay-package tests: **80 pass in
  1.21 s**, no failures/skips; 79 are synthetic format/negative cases. Ruff and
  `git diff --check` pass (existing CRLF notices only). Linked-path negative is
  injected, not an OS isolation certificate. No broad or paid suite rerun.
- Private `2026-09-19-saved-block-reference-01` retains exact script/source/tool
  pins, bytecode audits and one 4,980,736-byte read-only region copy. Source/copy
  hashes match, source stat/hash unchanged, Java absence confirmed before/after.
  Initial comparison preflight rejects a fenced/disconnected post-cancel record;
  script and failure retained. Corrected selection is the last connected record,
  `use_cancel.before`, sequence 5. No game/source mutation occurs.
- Actual official E9E 1.27.0 / Minecraft 1.19.2 / Forge 43.4.23 saved-state
  comparison matches **128/128 block IDs across two chunks**, including mayapple.
  Dig target is saved as air, but no independent pre-action save exists. This
  proves only the recorded final-ID agreement, not causal dig/resource/reach/
  visibility or scoring conformance. Copy covers selected region, not a complete
  checkpoint; same-user ACL/read-only flags are not authenticated isolation.
- User's separate-desktop question answered from implementation, actual trial
  evidence and Microsoft primary documentation. Shared-desktop input remains
  unused; all game processes remain stopped, Strata inference $0. Next capture
  paired pre/post action references and resource evidence in an authorized bounded
  trial, alongside direct failed-stop timing; retain every prior failure and limit.

### 2026-09-19 — paired modded block trial preparation

- Previous goal turn made progress: private saved reader, 80 passing checks and
  128 authentic final-ID agreements. This continuation targets independent
  pre/post block state, keeping all G0–G5 and M0–M6 gaps open.
- Prepared `2026-09-19-paired-block-reference-01/worker-01` with fresh campaign/
  lease scope, unchanged 06f29980… native candidate, current 33 compiled broker
  pins, 480 s client / 90 s worker / 600 s server bounds and the same 500 ms stop
  wait. Scoped checker requires a visible, reachable `twilightforest:mayapple`,
  retains its pre-action observation and checks the public air result. Private
  world files are never used for action selection; no admin or raw packet call.
- Prelaunch copy first rejected full-stat equality; comparison included access
  time but differing fields were not recorded, so the exact first trigger remains
  unproven. Failed script/partial copy retained. Corrected copy compares stable
  identity/size/modify/change fields plus source/copy hashes and records access
  times separately. Five files / 17,604,736 bytes copied with no Java processes
  and prior normal-stop evidence. This is selected reference data, not a full
  checkpoint or authenticated seal. Post-run comparison remains pending.

### 2026-09-19 — failed modded dig resolved to unchanged saved state

- [Authentic trial](docs/verification/2026-09-19-paired-block-reference.md) reaches
  native readiness in 176.266 s, no identity retry. Look/terminal dedup pass;
  the mayapple dig becomes ACTION_UNKNOWN, release confirmed/resync required.
  Checker sends stop-all and never replays; later use/cancel cases are not run.
  Native private journal has no intent or primitive for the dig request. Its
  original typed native rejection was discarded, so the cause is not recovered.
- Normal stopped-state after copy: five files / 17,604,716 bytes, Java absence
  and source/copy hashes checked. All 128 pre-action public IDs match before
  save; all 128 selected saved states, including mayapple, remain unchanged.
  Failure remains failure; no resource/scoring or causal-actor claim.
- Worker exits 0; outer check fails due to gameplay assertion. Client exits 125
  before outer cleanup. Guardian job 1.0083 ms, signaled wait 436.8138 ms under
  unchanged 500 ms bound. Client/check 278.094 s, normal server stop 422.875 s,
  exit 0 and complete logs. Two PNGs decode (not visually inspected); three
  player pose comparisons pass. Collector verifies two actions/four primitives,
  12 native frames, eight supervisor events and 287 telemetry records. All
  processes stopped, argument file retired, input desktop unchanged, $0 inference.

### 2026-09-19 — bounded outline aim and private native failure diagnostics

- Exact installed Twilight Forest 4.2.1518 bytecode shows mayapple outline
  (4,0,4)–(13,6,13)/16. The existing center-at-8/16 ray stays above that shape
  from the recorded eye position. This demonstrates a targeting defect and
  plausible rejection cause, not the discarded native error code.
- New GameBlockTarget/runtime wiring uses at most 64 finite positive-volume
  outline boxes within local [-16,16], distinct stable nearest-first centers,
  current native pick range and ordinary OUTLINE hits on the delivered target.
  Existing context/revision/lease/mutation/charge/release guards remain. SPEC
  v0.2.32, Forge minor 34 and motor revision 2 identify changed behavior in all
  three language contracts; no existing cohort silently gains the new motor.
- ForgeLane records private allowlisted error code/act-status phase after its
  fence/release attempt. Public unknown/resync and no-replay behavior stay;
  raw messages/stacks/unlisted codes omitted. Diagnostic failure cannot block
  the release attempt. Profile/library/script evidence remains private.
- Executed offline Gradle test/writeTestClasspath: **439 Java pass**, no failure/
  error/skip, 25 s, including six new shape tests. Initial TypeScript build fails
  only on unchecked new-test array indexing; explicit presence assertion fixes
  it, next build passes. Complete Node Forge suite with pinned JVM/classpath/
  guardian Python: **42 pass**, no skips/failures, 67.987 s, including five new
  diagnostic/release/privacy/storage fault cases. Selected native Python and
  gameplay package: **41 pass**, 0.93 s, including cross-language policy agreement
  and old/missing/wrong identity negatives. Ruff passes. JVM behavior is synthetic.
- M0.3b.1b.4.1 and the paired-reference parent remain in_progress. Native candidate
  is compiled but not installed/authentically verified. Next obtain its real
  startup identity and repeat the paired action case under fresh authority;
  preserve the unchanged failed world state, all charges and prior stop failures.
  All M0–M6/gates remain open, M7 conditional; no further user input is needed
  for this authorized development work.
- Offline JAR/reobfuscation build passes in 11 s; candidate SHA-256
  `b2a91155a7698d3ce6095ae7c4005827ea10c7f3623bfa086312f29d56916896`.
  Protected `candidate-34/` retains JAR/test XML/16 source snapshots/33 compiled
  broker pins. Both installed JARs unchanged; candidate not installed. Final
  code/broker pins and local links checked, diff whitespace clean. Java process
  count zero. Continue with exact candidate startup identity and authentic paired
  target-effect validation; the failed case and all required gates remain open.

### 2026-09-19 — authentic minor-34 outline targeting and paired saved effect

- Previous discussion turn was explanatory, not implementation progress. This
  continuation revalidated stopped processes and the authoritative worktree, then
  executed the next authorized live checks. [Report](docs/verification/2026-09-19-outline-target.md),
  M0.3b.1b.4.1 / M0.3b.2c.3c.2b.2b.2 / M0.3b.2c.3c.2b.2c.1;
  F01/F06/F09/F16, N01–N06/N08, C02/C04/C09/C15/C18,
  partial T01/T03/T06/T07/T12/T13. No acceptance threshold or SPEC feature changed.
- Installed built minor-34 b2a91155… only in the dedicated private E9E copy,
  preserving original CurseForge f10e7ad6… and all prior failed evidence. Exact
  profile: E9E 1.27.0, Minecraft 1.19.2, Forge 43.4.23, Java 17.0.20.1,
  Node 24.19.0, Python 3.12.14; 97 bootstrap pins. Protected cached-session
  preparation succeeded twice without prompting or exposing credentials.
- Private `read-only/run_live.py`: authentic identity at 165.219 s; **2,750 world,
  10 transport, six disconnected assertions pass**; ten identity reads 62–79 ms.
  Two PNGs decode and were visually inspected. Base guardian stop 312 ms;
  client procedure 187.172 s, normal server save/exit 325.062 s. Collector passes,
  199 telemetry records retained, owned arguments retired and client absent.
- Fresh worker authority uses that observed fingerprint/body and new campaign/
  lease/digest; 33 compiled modules and nine harness files pinned. Added private
  pre-dispatch target/request retention. Before-copy at proven normal stop and
  zero Java processes: four region files plus player, 17,608,827 bytes. Existing
  480 s client / 90 s worker / 1,000 primitive limits and 500 ms kernel wait remain.
- Private `worker-01/run_live.py`: **public procedure pass**, readiness 166.125 s,
  17 CLI calls; look, known-terminal dedup, mayapple dig with delivered air,
  active-use cancel/release, fenced observation and subsequent rejection pass.
  Three actions / **12 primitives** reconcile, 29 native frames / eight supervisor
  events / 293 telemetry records. No native-call-failure diagnostic fired, so its
  live negative qualification remains open. No uncertain mutation was replayed.
- Worker exits 0; guardian confirms client exit 125 before outer cleanup, no
  desktop-watchdog intervention. Client procedure 268.360 s; server saves normally
  and exits 0 at 424.422 s. QPC job call 0.8841 ms; signaled wait **503.6561 ms**
  exceeds requested 500 ms. `final-audit.json` preserves protocol pass and explicitly
  denies proof of a strict wall deadline. Observer's largest nominal 10 ms wait
  is 93.6994 ms. Prior failed stops remain failures; shutdown reliability open.
- After-copy at stopped boundary: same five files, 17,633,401 bytes. Private
  `compare_regions.py`: **six checks pass, 256/256 delivered IDs match**. Only
  selected mayapple (-49,7,9) changes to air; support unchanged. Separate saved
  pose checks pass. Arrow stack 64→63 and second-frame arrow-in-ground retained
  as ordinary use/release consequences, not undone or called full resource proof.
  Two worker PNGs decode and were visually inspected. No desktop content captured.
- Private evidence remains under `2026-09-19-outline-target-01`; raw worlds,
  account/connection material and snapshots are not published. Updated current
  coverage to distinguish installed/loaded JEI-containing code from unproven hook
  application and actual UI conformance. All game processes stopped and both
  argument files retired. No Strata inference or shared-desktop input; D04 $10
  cap remains untouched. No broad unit/paid suite rerun without code changes.
- Next: independent actor/resource/mechanics evidence, authentic shape/reach/
  occlusion negatives, and shutdown-envelope qualification. The tested target is
  now air; later work must preserve the world/resource history. Full M0–M6/gates
  remain open, M7 conditional; no further permission is needed for this work.

### 2026-09-19 — retained startup lease failure before the native rejection case

- Continued the same authorized work with `outline-target-01/worker-02`, fresh
  scope/lease and unchanged native/broker code. Intended observed-air dig tests
  native PRECONDITION_FAILED, post-fence private diagnostics, public unknown/
  resync and no-input saved-state agreement. Public checker and separate private
  audit compiled; the audit is not executed because the case never starts.
- Real startup readiness passes at **164.562 s** and one private world frame is
  captured. Full guardian becomes ready; child worker fork is journaled. No
  public grant, worker action database, native lease or input intent is created.
  Guardian then terminates for **PROCESS_LEASE_EXPIRED** at 2,250 ms of lifetime;
  outer harness records CLIENT_EXITED and forced worker-tree cleanup (exit 125).
  Public rejection case remains **not_run**; the trial is **fail**. No replay.
- Guardian QPC job 1.2999 ms, signaled wait **482.0116 ms**. Client procedure
  178.422 s; server normal save/exit 0 at **310.360 s**, logs complete. Collector
  passes native/supervisor chain checks: one native profile record, seven
  supervisor events, 183 telemetry records. Native action count is zero; absent
  worker database is not invented accounting evidence. Before/after selected
  files 17,633,401 / 17,633,406 bytes retained without a block-effect claim.
  The single PNG decodes and was visually inspected; zero Java processes,
  absent spawned child PID and retired arguments verified.
- Source audit finds a startup gap: parent renewal eligibility requires child
  heartbeat freshness within 200 ms after fork; first child heartbeat is emitted
  only after lane/server initialization. No historical child-phase timing proves
  which operation or OS scheduling caused this sample's delay. New child
  **M0.3b.2c.3c.2b.2b.2.1** tracks bounded bootstrap/initialization liveness,
  true event-loop health, phase evidence and hung/late/crashed-startup negatives.
  Preserve existing gameplay/guardian limits; do not fabricate renewals or rerun
  blindly. Next implement/verify that path, then fresh authentic negative scope.
- Updated [Forge API operation notes](docs/operations/forge-game-api.md) to explain
  ordinary bow release on cancellation and retained ammunition consumption.
  This clarifies existing mechanics; no action/schema/acceptance change. Current
  SPEC remains v0.2.32. Earlier successful mayapple evidence and all failures are
  retained; no complete milestone/gate, inference, OS input or new permission.

### 2026-09-19 — bounded child-worker startup implementation and fault tests

- Previous turn made progress with real paired mayapple evidence and a new
  startup failure. Revalidated worktree and zero Java processes; continued
  M0.3b.2c.3c.2b.2b.2.1, F01/F06/F09/F16, N01–N06/N08,
  C02/C09/C15/C18 and partial T01/T03/T06/T07/T12/T13.
- [Implementation/report](docs/verification/2026-09-19-worker-startup.md): new
  worker_startup.ts private state machine, reordered worker.ts bootstrap/guardian/
  initialization, actual 100 ms child pulses, strict messages and early exit/phase
  evidence. Fixed 2,250 ms bootstrap/initialization deadlines cannot be extended
  by pulses; guardian renewal freshness 200 ms and native health remain. Overall
  worker wall budget includes startup. worker_lane.ts imports Mineflayer runtime
  only for its explicit backend. Native minor-34 JAR and public schemas unchanged;
  compiled broker identity changes. SPEC v0.2.33 records the private policy.
- Added five lifecycle tests and seven actual disposable Node/JVM startup cases.
  Build and initial five tests pass. Full Forge/guardian/lifecycle execution:
  **58 tests, 56 pass/two fail**, 97.154 s. Hung/malformed bootstrap was rejected,
  but evidence closed before child exit arrived. Fixed cleanup to issue stops
  before a bounded 500 ms exit-receipt wait; missing receipt remains a failure.
  This does not delay native guardian termination. Retained the failed log.
- Corrected affected suite: **13 pass**, no failures/skips, 58.741 s, covering
  all seven startup cases, normal drain, mismatched grants and four active faults.
  Synthetic native-freeze/worker-kill/worker-hang/parent-kill JVM exit intervals
  1,020/30/1,831/20 ms. Added a pre-await rejection handler for cleanup entered
  before bootstrap await; final three early-bootstrap failure tests pass again,
  7.006 s. Compiled gameplay-package check **one pass**, 0.21 s. These are
  synthetic game fixtures, not new vanilla/E9E acceptance. Broader unchanged
  action tests were not rerun after the cleanup-only correction.
- Fresh private `worker-startup-01/worker-01` has 34 pinned broker modules, ten
  harness files, new campaign/lease/capability authority and unchanged native JAR.
  Before-save captured at normal stop/zero Java: five selected files, 17,633,406
  bytes. Cached auth prepared; server boots and client is now loading on the
  separate desktop. Expected native observed-air rejection and offline diagnostic/
  save audit remain pending. Existing client/worker/action/guardian limits remain;
  no inference, shared-desktop input, restored resources or repeated mutation.

### 2026-09-19 — authentic startup pass, retained diagnostic/stop failures, transport repair

- Previous discussion turn was no implementation progress; revalidated current
  process/evidence state before continuing. Worker-startup trial is terminal,
  server exit 0/normal save and no Java processes. M0.3b.2c.3c.2b.2b.2.1 startup
  phases pass: 748.3134 ms bootstrap, 280.2607 ms initialization, 1,916.7829 ms
  gateway. Child exit 0; parent exit 1 due guardian stop failure.
- Retain failed private diagnostic audit (UNCLASSIFIED_NATIVE_FAILURE) and
  PROCESS_STOP_UNCONFIRMED: successful job call 1.0723 ms, timeout wait measured
  511.7797 ms at unchanged 500 ms bound. Later process absence is not a pass.
  Public negative checker, one-action/no-intent/no-replay, two safety primitives,
  256 saved-ID comparisons, 128 unchanged selected states, pose checks and two
  decoded/visually inspected PNGs pass. Client 284.891 s/server 439.969 s; arguments
  retired. Selected inventory unchanged, not full conservation/checkpoint proof.
- Split M0.3b.1b.4.1a for the transport loss found by that real check. NativeGameClient
  now preserves only allowlisted failure codes through NativeOutcomeUnknown;
  ForgeLane journals them after fencing/release. No public schema/affordance,
  native JAR, deadline or unknown/no-replay change. Existing native diagnostic
  policy remains applicable; exact historical erased code remains unknown.
- Build passes. Actual HTTP/JVM fixture regression and existing diagnostic cases:
  12 pass, zero fail/skip, 13.107 s; gameplay-package exclusion 1 pass in 0.28 s.
  Sources/tests: native_game.ts, forge_lane.ts, tests/forge.test.ts. Detailed
  [report](docs/verification/2026-09-19-native-diagnostics.md). Fresh authentic
  trial prepared with 34 archived modules, new scope, five stopped saved files
  (17,637,503 bytes), unchanged minor-34 client and cached authentication.
  Server running; public negative/offline diagnostic outcome pending.
- F01/F06/F09/F16, N01/N02/N04/N06/N08, C02/C09/C15/C18 and partial
  T01/T03/T06/T07/T13 advanced. All aggregate gates and full startup/shutdown,
  geometry/resource/scoring/isolation scope remain open. No OS input/inference.

### 2026-09-19 — real mutation diagnostic qualification and repeated shutdown failure

- M0.3b.1b.4.1a verified for its bounded private diagnostic contract. Authentic
  exact E9E/Forge/minor-34 worker-01 passes public negative behavior and all 13
  offline rejection checks. PRECONDITION_FAILED survives the real HTTP mutation
  wrapper, private only, after confirmed-release unknown acknowledgement. One
  action/no native intent, two safety primitives, five native frames/three native
  usage records reconcile; no replay or private code in public CLI results.
- Before/after copies match all 256 delivered block IDs; 128 selected states and
  selected player inventory unchanged. Saved pose and two decoded/visually
  inspected game PNGs pass. Five after-files total 17,637,494 bytes. Complete
  conservation/scoring/checkpoints/physical-input qualification not claimed.
- World readiness 213.437 s; bootstrap 1,116.6618 ms, initialization 294.9302 ms,
  gateway 2,575.8237 ms (including guardian binding). Independent startup bounds
  pass. Child exit 0; guardian stop fails: job 1.0247 ms, unchanged 500 ms wait
  times out after measured 501.9950 ms, PROCESS_STOP_UNCONFIRMED, parent exit 1.
  Later held-handle exit at about 586 ms is not a successful bounded stop.
- Server normal save/exit 0 at 543.906 s; client procedure 330.547 s. Arguments
  retired, input desktop unchanged, zero Java processes verified; 34 prelaunch
  module pins match. Offline scripts capture_regions/collect/audit_negative/
  player_reference/verify_pngs/audit_startup all exit 0; their independent results
  preserve overall failure. Source/report links (601) and git diff --check pass.
  [Full report](docs/verification/2026-09-19-native-diagnostics.md); private evidence
  `2026-09-19-native-diagnostics-01/worker-01`, including final-audit.json.
- Current turn made implementation and authentic verification progress. Keep
  .1b.4.1, .2b.2b.2 and all aggregate gates open. Next independent concrete action:
  run the existing loaded-Forge collision-shape probe and qualify a scoped
  observed level walk with independent saved position; preserve geometry and
  stop failures without increasing deadlines. No desktop input or inference.

### 2026-09-19 — loaded native collision prerequisite passes

- M0.3b.1b.2b.2b.2 in_progress; F01/F06/F16, N01/N02/N06, C09,
  partial T01/T03. Existing ClientCollisionProbe ran on the exact E9E 1.27.0 /
  Forge 43.4.23 / Minecraft 1.19.2 / pinned Temurin 17 / minor-34 client. All
  13 cases pass: native air/stone/slabs, waterlogged/age/identity/missing-state
  rejection and constructed level route. This is native loaded-class integration,
  not actual world movement. Earlier plain-JUnit initialization failure retained.
- Twenty disconnected read-only checks pass, no authority/action journal. Startup
  160.828 s; total 164.812 s; base guardian confirms stop with reported 344 ms
  coarse-clock wait. World-client failures at the unchanged 500 ms bound remain.
  Collector verifies 97 bootstrap pins, options/JAR, six sources, three scripts,
  exact probe cases/policies/digest, argument retirement and zero Java processes.
  No server/world join, controls, desktop input or inference.
- [Report](docs/verification/2026-09-19-native-collision.md); private evidence
  `2026-09-19-native-collision-01/verification.json`. Parent motion/modded geometry,
  steps/vertical traversal and complete filtering/input qualification remain open.
  Next: scoped level walk chosen from fresh public delivered state and independent
  saved-position reference, retaining all charges and stop failures.

### 2026-09-19 — real level walk and independent saved-position evidence

- Prior goal turn was progress; revalidated terminal collision/diagnostic runs,
  normal server stop and zero Java before fresh execution. M0.3b.1b.2b.2c.2 stays
  in_progress. F01/F06/F09/F16, N01/N02/N03/N05/N06/N08, C09/C15/C18,
  partial T01/T03/T07/T12/T13. No runtime source or input/clock/budget policy changed.
- Prepared 11 pinned private harness files, compile/selector checks, fresh scope,
  protected cached session, 34 archived broker modules and five stopped before
  save files (17,637,494 bytes). Target selection uses fresh public cells only;
  one-block cardinal walk with supported ground/air, 5 s action, 0.2 target and
  0.02 settled/reference tolerance. No private target oracle or uncertain replay.
- Exact E9E1.27.0/Forge43.4.23/minor34 passes 12 CLI calls, ordinary walk/release,
  settling/dedup/fencing. One intent, 22 action events, 24 total primitive charges,
  34 native frames/six usage records reconcile. All 15 private checks and six
  saved-player checks pass. Saved X moves -50.5 to -49.42724892248985, Y/Z 7/10.5;
  1.0727510775 displacement and 0.0727510775 target error. 256 block IDs agree with
  before/after saves; selected inventory unchanged. After-copy 17,637,503 bytes.
- Startup 212.750 s; bootstrap 1,008.4497 ms, initialization 291.8282 ms, gateway
  2,768.9977 ms. Child exit 0; parent exit 1 because guardian job call 1.4162 ms
  is followed by a 503.5059 ms measured timeout at unchanged 500 ms wait.
  Overall fail retained. Client 328.015 s; server normal save/exit 0 at 520.328 s.
- Both PNGs decode, but first visual frame has HUD/selection outline/particles
  without terrain; second has terrain. Do not claim complete initial rendering
  or physical parity. Final-audit separates movement pass, visual finding and
  shutdown failure. Arguments retired, zero Java, input desktop unchanged.
- Offline capture/collect/player/movement/PNG/startup scripts all exit 0, with
  actual independent verdicts retained. [Report](docs/verification/2026-09-19-native-movement.md),
  private `2026-09-19-native-movement-01/worker-01/final-audit.json`. Reinspection
  after stop retains all five mode findings (263/268); role/source review made
  no exclusion, config edit or new provisioning claim. No inference dispatched.
- Next: native menu/quest lifecycle and cancellation during walking using fresh
  scoped authority; preserve remaining geometry, full resource/input/render and
  release gates. Continue shutdown/resource qualification independently.

### 2026-09-19 — authentic quest lifecycle and in-flight cancellation qualification

- Previous explanation-only goal turn classified no_progress; revalidated prior
  normal server stop, zero Java and unchanged 34 broker/97 launch pins before
  taking the next authorized action. Split M0.3b.3.2.4 into .4a basic quest
  lifecycle and .4b remaining native menu/machine/reference work; no scope removed.
  Coverage F01/F06/F09/F16, N01/N02/N03/N04/N05/N06/N08, C09/C15/C18,
  partial T01/T03/T06/T07/T12/T13; all aggregate results remain unchanged.
- [Report](docs/verification/2026-09-19-native-quest-cancel.md), private
  `2026-09-19-native-quest-cancel-01`: three exact E9E/Forge minor34 trials,
  unchanged runtime artifacts and bounds, fresh scopes and stopped save copies.
  First client fails before world/worker startup in CTM ResourceUtil's HashMap
  during texture stitch; no game actions/frames. Normal server stop and unchanged
  five selected save files verified. Retained crash/bytecode/upstream evidence
  adds B10; no mod deletion/patch/replacement or reliability pass.
- Second trial passes ordinary quest opening/dedup, then chapter selection is
  unknown/fenced with private UNCLASSIFIED_NATIVE_FAILURE. Checker used root
  revision 1 after reading quest revision 2. Added a real catalog/motor regression
  to GameQuestNavigationTest and documented refresh in forge-game-api.md; 19
  focused Java tests pass with pinned JDK/exact FTB Library. Initial Gradle call
  lacked JAVA_HOME and did not start; retained log. Production guard unchanged.
  The original native failure code remains unknown; stale-selection explanation
  is supported by live page history and the regression, not retroactive recovery.
- Private reference collector initially rejected integral native JSON doubles;
  separate v2 asserts integrality before conversion. Original collector/failure
  and strict saved-world reader retained. Second trial's 256 IDs, saved pose,
  selected inventory and single-sample shutdown pass; later quest/cancel cases
  not_run. Corrected harness starts only after terminal/normal-save verification.
- Third trial passes 53 scoped CLI calls covering open/dedup/chapter/detail/text/
  back/close and cancelled/released/fenced walking. Six intents, 39 primitives,
  72 native journal frames and 15 usage records reconcile; no native call fault.
  Independent 256 saved IDs, settled position/dimension and selected inventory
  agree. Both game-only PNGs decode and show terrain/HUD; no menu-image parity claim.
- Strong cancellation reference fails: saved position is 0.1428304737 blocks
  from target, inside the original 0.2 tolerance. Seven/eight player checks and
  twelve/thirteen aggregate reference checks pass; aggregate remains fail.
  End-to-end cancel CLI takes 297 ms and cannot certify the separate 250 ms
  responsive-worker target. Preserve public cancelled receipt and failed
  cancellation-before-arrival independently; no threshold relaxation.
- Third startup passes (bootstrap 1197.3598 ms / initialization 330.9449 ms).
  Overall procedure fails guardian: job call 0.8438 ms, 500 ms wait timeout after
  measured 507.6092 ms. Client procedure 266.843 s; server normal save/stop
  426.25 s. All owned processes terminal, arguments retired, zero Java verified;
  current player position (-50.5, 7, 11.357169526313502) and costs are preserved.
- No shared-desktop input, gameplay restore or Strata inference. Initial-frame
  finding cross-linked from private-frames.md. SPEC v0.2.33 unchanged. Next:
  distinguish cancellation from arrival on a longer permitted observed route,
  then native quest/task/JEI/menu/resource/visual cases and shutdown diagnosis.
  Complete geometry, physical input, host/isolation/accounting, soaks, capacity,
  scientific confirmation and later-pack gates remain required.

### 2026-09-19 — cancellation before arrival and native budget transport evidence

- The immediately preceding discussion explained separate desktop rendering and
  made no implementation progress. Revalidated the pending server by polling its
  live process handle. Its client had never launched and insufficient bounded
  time remained; requested normal save/stop, confirmed terminal exit 0, retired
  arguments and recorded `worker-02` as not_run due to operator orchestration
  delay. No timeout was treated as a terminal process or grounds for replay.
- [Cancellation report](docs/verification/2026-09-19-native-cancel.md),
  M0.3b.1b.2b.2c.2, F01/F06/F09/F16, N01/N02/N03/N05/N06/N08,
  C09/C15/C18 and partial T01/T03/T07/T12/T13. Retain the first no-target
  failure, all previous arrival/guardian failures and the disclosed bent-route
  selector. New private paired orchestration launches immediately on server
  readiness; same runtime, action/guardian limits and saved-stop predicates.
- Fresh third trial passes 13 public CLI calls, eight independent saved-player
  checks and thirteen reference checks. Saved displacement 0.2101399846 blocks;
  final destination distance 2.2964687270 blocks, outside 0.2 tolerance. This
  stops during initial centering, not a complete bent-route traversal. One
  native intent/20 primitives/five usage records reconcile and 256 block IDs
  match saved regions. Full resource/physics conservation remains unqualified.
- Authentic readiness 174.891 s; worker bootstrap 808.4997 ms, initialization
  370.4133 ms. Guardian wait signals at 451.9577 ms within the unchanged 500 ms
  bound. CLI cancellation 359 ms does not qualify the separate 250 ms worker
  target. Client procedure 275.969 s, server normal save/stop 393.344 s. This
  one successful shutdown does not resolve the retained repeated failures.
- Executed capture-after, collector, independent player reference, cancellation
  audit, PNG decoder and startup audit, all exit 0 with passing narrow verdicts.
  Both actual 854x480 frames were visually inspected and show terrain/HUD.
  Zero Java processes, arguments retired, 34 compiled broker/97 launch/14
  harness pins agree. Final local-link checks and git diff --check pass.
- [Native budget report](docs/verification/2026-09-19-native-budget.md), new
  M0.1c.1, F03/F11/F16, N01/N03/N04/N06, C06/C20, partial T04/T12.
  Actual CLI 0.154.0-alpha.6.2 and 426 freshly generated experimental schema
  files inspected/hashed without inference. Turn start exposes no output-token
  or money cap; separate goal budgets/account limits do not prove D04 admission.
- Two actual-CLI/synthetic-local-provider transport cases pass: rejection gives
  one POST with retries disabled; transient error gives two POSTs with one
  retry, same body digest and distinct dispatches. No Authorization header or
  max_output_tokens field; expected exit 1 without timeout. Fresh credential-free
  profile/workspace and explicit environment, owned bounded process trees;
  no paid model, OAuth qualification, provider token, game grant or model-side
  plugin claim. Published OAuth credit rates do not establish actual USD
  conversion or finite per-call exposure; no gateway qualification issued.
- Production runtime/SPEC v0.2.33 unchanged; no broad or paid suite rerun.
  All authentic and local fixture processes terminal; no shared-desktop input,
  gameplay restore or Strata inference. Full M0–M6 objective remains active,
  all aggregate gates open, M7 conditional. Next: local streaming/compaction/
  helper request paths and durable reservation gateway; remaining native quest/
  JEI/custom menus/resources and shutdown reliability, then the outstanding
  isolation/host/restore/soak/capacity/scientific/legacy requirements.

### 2026-09-19 — implementation checkpoint, durable dispatch accounting and handoff

- User steering: stop new feature/experiment expansion at a reviewable point,
  commit, create a PR, merge to main and review where the next session resumes.
  This changes the immediate task boundary, not required M0–M6 scope or gates.
- M0.1c.1a is implemented_unverified for production. Added
  `src/mcbench/inference_dispatch.py` and `tests/test_inference_dispatch.py`;
  `budgets.py` composes posting/intent atomically and `native.py` rejects mixed
  simulation stores. F03/F11/F16, N01/N03/N04/N06, C06/C20, partial
  T01/T04/T07/T12, G0/G1. See the
  [dispatch report](docs/verification/2026-09-19-inference-dispatch.md).
- Actual checks on pinned Windows/Python 3.12.14/Node 24.19.0/Temurin
  17.0.20.1+1 with all client/settings/guardian fixture opt-ins:
  `python -m pytest -q`: 738 pass, zero skips, 113.77 s, two dependency
  deprecation warnings; `npm test`: build + 166 pass, zero skips, 117.39 s;
  Gradle client/telemetry tests: 440 + 5 pass, zero failures/errors/skips;
  Ruff `src evaluator/src tests tools`: pass. Installed `mcbench --help`: exit 0.
  Initial focused lint found one unused test import, removed before full checks.
- Review refreshed README to SPEC v0.2.33/current authentic limits, condensed
  current position without dropping append-only history, and added
  [status/handoff](docs/STATUS_AND_HANDOFF.md). Publication inventory found two
  compressed local logs; added rotated-log/directory and SQLite sidecar ignores.
  Candidate wrapper SHA matches locked build inputs; initial secret/binary scan
  found no credential material or unexpected binary. Raw audit/check logs stay
  external in `2026-09-19-merge-checkpoint-01`; final staging/merge evidence follows.
- No new game launch, shared-desktop input, model inference, milestone closure
  or altered public contract. M0–M5 partial, M6 later required, M7 conditional.
  Next session starts with actual native/local synthetic transport integration,
  per-call versus whole-job budget composition and complete request-path checks.
  Live OAuth cost/exposure, isolation and all other retained gates remain open.
- Final source review before PR: all 462 staged source/design files scanned;
  877 local Markdown links resolve and all F/N/M/T/G ledger IDs remain present.
  The sole credential-shaped URL finding is the explicit synthetic
  `user:secret` rejection case in `tests/test_provisioning.py`; reviewed as test
  data, not a real credential. `.gitattributes` now pins source LF, batch CRLF
  and binary wrapper handling to preserve source-fingerprint reproducibility.
  Refreshed stale settings/game API introductions and linked the accounting
  follow-up from the earlier native budget report. No code changed after the
  complete test runs; final staged diff and audit are checked before commit.
- Delivery: source checkpoint `3aca278` committed and pushed on
  `codex/strata-implementation-checkpoint`;
  [PR #1](https://github.com/OpenCnid/strata-bench/pull/1) opened against main.
  Final staged audit passes (462 files, 877 links, no unreviewed findings,
  all ledger IDs, wrapper hash), and `git diff --cached --check` passes.
  The PR is the durable reference for its eventual merge commit; subsequent
  delivery-link edits are documentation-only and do not change tested code.

### 2026-09-20 — resumed native CLI dispatch accounting

- Created the explicitly requested long-horizon M0–M6 goal; M7 remains conditional.
  Verified clean main/worktree and GitHub PR #1 merge at 579796d, fetched origin,
  and branched codex/strata-native-dispatch without altering existing worktrees.
- M0.1c.1b, F03/F11/F16, N01/N03/N04/N06, C06/C20, partial T01/T04/T07/T12:
  [native synthetic dispatch report](docs/verification/2026-09-20-native-dispatch.md).
  Added nested job/helper envelopes, exact request-inventory closure and atomic
  native finalization; preserved ordinary additive lineage and unknown holds.
  NativeLaunch budget mode is profile-pinned and generated only in operator schemas.
- Executed the pinned CLI against a credential-free deterministic local provider:
  eight final cases pass, 13 received requests, 12 admitted dispatches, eight
  settled/four intentionally unresolved, nine CLI jobs. Identical-body retries
  charge distinctly; lost-stream retry is blocked before provider execution;
  compaction and separate-job helper totals reconcile; a fresh supervisor
  refuses replay. Restart is after classified interruption, not abrupt crash.
- 130 relevant Python tests pass, zero skips, two existing Typer/Click warnings;
  28 schema checks pass again after LF-preserving generation. Pydantic export,
  TypeScript generation/build, actual gameplay package exclusion, full Ruff and
  diff checks pass. Earlier timestamp/compaction-fixture failures and the stale
  schema failure (128 pass/one fail before regeneration) remain documented.
- Raw evidence/source hashes are external under 2026-09-20-native-dispatch-08;
  earlier -01 through -07 attempts are retained. Read-only accounting inventory:
  25 stores, no live profiles or errors; the three prior accounting stores have
  synthetic tool usage only. No new allowance installed, no OAuth/paid call,
  credentials, game launch, shared-desktop input or threshold change.
- SPEC v0.2.34 documents reservation composition. Production upstream receipts,
  OAuth monetary/exposure bounds, historical spend authority and isolation stay
  unqualified under new M0.1c.1c; USD-per-credit evidence requested asynchronously.
  Next: bounded upstream wire parsing/forwarding and abrupt supervisor-loss
  coverage, then actual pinned plugin/skill/helper and remaining host gates.
  Full M0–M6 remains active; no aggregate gate/milestone closed.

### 2026-09-20 — upstream wire receipts and abrupt supervisor recovery

- M0.1c.1c.1 implemented_unverified for production; .1c.2 explicitly retains
  live monetary/exposure/spending-authority/isolation blockers. Added bounded
  simulation-only HTTP transport and incremental SSE/JSON accounting; unknown,
  conflicting, truncated or unsupported receipts retain holds. Literal loopback,
  no redirects/credentials/internal retry, strict request binding and finite
  response/deadline limits are tested. No live OAuth adapter is implied.
- Final pinned CLI/separate-upstream matrix: nine cases pass in private
  2026-09-20-native-dispatch-wire-final-01, with source/binary hashes. Fifteen
  ingress requests, thirteen upstream dispatches, eight settled/five unresolved,
  ten CLI jobs. Both unknown-usage retries are stopped before upstream execution.
  Compaction/helper/retry totals and receipt deduplication reconcile.
- Abrupt supervisor exit follows an actual flushed stream prefix and bypasses
  cleanup. Durable RUNNING/DISPATCHING states survive. A held outer Windows job
  shows 13 active processes before the crash and zero after; only then does a
  new supervisor recover the pending attempt. Full reservation retained, no
  native/request replay and no new admission. Existing process fencing API gains
  read-only whole-job counts; ordinary stop behavior and bounds are unchanged.
- Expanded relevant Python run: 165 pass, zero skips, 15.24 s, two dependency
  warnings. Final additional transport hardening: all 30 transport checks pass,
  3.51 s. Seven actual process checks pass, including owned grandchild counts.
  Concurrent child envelope admission is tested. Ruff passes; initial unused
  transport-test import was removed. Earlier direct-provider and intermediate
  wire/crash samples remain dated evidence, not erased by final passes.
- F03/F09/F11/F16, N01/N02/N03/N04/N05/N06/N08, C06/C18/C20 and partial
  T01/T04/T07/T12 advanced; no aggregate test/release/milestone closure. Private
  raw bytes, request captures, failure receipts and process evidence stay external.
  [Report and exact limits](docs/verification/2026-09-20-native-dispatch.md).
  Next: actual pinned plugin/skill/helper conformance in credential-free native
  fixtures while the live USD/exposure/isolation gates remain blocked. Goal active.


### 2026-09-20 — actual native plugin discovery and skill loading

- Continued beyond local accounting checkpoint `66baa0f`; goal remains active.
  Added M0.1c.2/.2a/.2b with F03/F07/F11/F16, N01/N03/N04/N06,
  C06/C18/C20 and partial T01/T04/T07/T12 traceability. SPEC v0.2.35 pins
  discovery without removing any of the eight real upstream skills.
- Fixed Windows long-path installed-byte inventory and literal-quoted native
  plugin override keys. Preserve the registered marketplace path. Native TOML
  inline-table serialization permits the actual documented skill-disable array.
  Initial upstream plugin bytes remain unchanged; nested public test fixtures
  are omitted from discovery, not declared inaccessible at the OS boundary.
- Final actual-CLI/synthetic-upstream matrix passes enabled, disabled and explicit
  cases. Six implicit skill entries, both explicit-only bodies in the initial
  native request, the exact fixed skill read/tool result, zero fixture entries,
  unchanged plugin trees and five settled/deduplicated requests are observed.
  Three envelopes finalize; zero real USD. Private source/binary-pinned evidence:
  `2026-09-20-native-plugin-final-01`. Failed samples -01 through -10 and
  intermediate passes -11/-12 remain external with their actual reservations.
- Focused Python: 30 passed, zero skips, 4.35 s; Ruff passes. Initial long-path
  test setup failed until Git longpaths was enabled, then passed. The earlier
  native command-policy rejection and wire-parser expectation failures remain
  documented. Configuring the native unelevated Windows sandbox allowed the
  fixed public read; no shared-desktop input or sandbox-bypass flag was used.
- [Full result, limits and reproduction](docs/verification/2026-09-20-native-plugin.md).
  No model reasoning, gameplay, immutable ACL, helper or adversarial isolation
  pass is implied. Next: M0.1c.2b synthetic canaries and enforceable boundaries;
  live OAuth monetary/exposure/spending-authority gates remain blocked.


### 2026-09-20 — native boundary canaries preserve failed enforcement

- Continued after plugin checkpoint `5e3a047`. Added actual native/tool-loop and
  non-model sandbox canaries, with private synthetic files and a temporary owned
  listener only. No account cache, real operator/evaluator material, installation,
  outside endpoint or shared-desktop input is targeted.
- Private `2026-09-20-native-boundary-01`: workspace controls pass, but the
  unelevated agent command reads the operator dummy and connects to the listener.
  Initial-file write denied; two synthetic dispatches settle, zero real USD.
  `-02`: stricter named filesystem permissions refuse startup because this
  unelevated implementation cannot enforce split read restrictions. No calls.
- Existing enrollment was inspected without copying secrets or invoking setup.
  Non-model sandbox sample `-03` fails its .NET-based fixture under constrained
  PowerShell. Corrected cmdlet/system-curl probes `-04` and `-05` pass workspace
  controls and deny private read/initial write, but still connect to the unapproved
  listener. Sample -05 observes CodexSandboxOffline as the process identity.
  These direct sandbox commands make no agent/model session or inference call.
- Read-only ActiveStore inspection shows matching offline-account SID filters,
  enabled/enforced Codex outbound/loopback rules, active firewall profiles, local
  rule merging and running BFE/MpsSvc. Configuration is not a pass: the independent
  listener confirms the violation. Exact enforcement cause remains unresolved.
  No firewall, account, existing user config or setup policy was changed.
- M0.1c.2b.1 implemented_unverified with qualification fail; .2b.2 blocked on an
  enforceable boundary. F03/F07/F09/F11/F16, N01/N04/N06/N08, C06/C18/C20,
  partial T04/T07/T12. All aggregate gates remain unchanged. Ruff passes.
  [Results/reproduction](docs/verification/2026-09-20-native-boundary.md).
  An existing isolated-worker/VM location is requested; the monetary-evidence
  question remains pending too. Continue independent authorized reliability/game
  work; keep the long-horizon goal active and preserve all failed samples.

### 2026-09-20 — owned-job exit proof and retained counterexample

- Continued after isolation checkpoint `fafd8c3` on the active M0–M6 goal.
  Added M0.3b.2c.3c.2b.2b.2.2, SPEC v0.2.36 and the linked report/runbook.
  F09/F16, N01/N03/N04/N05/N06/N08, C14/C15/C18 and partial T01/T07/T12/T13.
- Initial private `2026-09-20-guardian-tree-01`: 46 pass/two fixture failures;
  the actual job contains three members, not the assumed two. `-02`: 47 pass/
  one real false-confirmation failure. Zero active accounting preceded the
  independently held child's signaled exit after its root had exited normally.
  Both failures remain; the terminal zero/500 ms requirements are not relaxed.
- WindowsJob now retains only membership-verified read-only handles, within a
  256-lifetime-member bound. Guardian stop requires cumulative total = held =
  signaled > 0 and zero active processes. Root/tree checks share one 500 ms wait;
  no repeated terminate or new allowance. Missing members, unsignaled/late exit,
  inventory/query errors and quota exhaustion fail closed. No PID-based kill,
  process arguments, credentials or shared-desktop input is involved.
- Private `-03`: 52 Python pass, zero skips, 34.06 s; five additional synthetic
  member-inventory checks pass in 0.05 s. Direct owned JVM tests reconcile three
  handles at 21.3362/21.3316 ms; no delayed marker mutation. Twelve selected Node
  tests pass, zero skips, 27.034 s, including six guarded process integrations.
  Native-freeze/worker-kill/worker-hang/parent-kill detection-to-exit measurements
  are 1027/44/1818/37 ms, distinct from the stop wait. Ruff, TypeScript and one
  gameplay-package check pass. Offline pinned Java fixture compilation succeeds
  with eight existing API warnings; the full Java suite was not rerun.
- [Report](docs/verification/2026-09-20-guardian-tree.md) preserves previous
  authentic stop failures and the new inventory limitations. No model call,
  Minecraft launch, milestone or aggregate gate pass. Historical native crash
  zero-count evidence cannot establish complete handle exit; strengthen that
  synthetic fence next, then continue independent reliability/mechanic work.
- Final review places the guard's clock read after member observation to prevent
  using a stale lease/deadline time. Five relevant lease/challenge/cleanup checks
  pass again, 6.74 s; private source manifest explicitly records this final edit.

### 2026-09-20 — native crash recovery waits for complete process-handle proof

- Continued after guardian checkpoint `0312d53`; M0.1c.1c.1 remains
  implemented_unverified for production. F03/F09/F11/F16,
  N01/N02/N03/N04/N05/N06/N08, C06/C15/C18/C20, partial T01/T04/T07/T12.
- Strengthened only the synthetic crash fixture with observed member handles,
  cumulative completeness and signaled exit, following the retained guardian
  counterexample. Existing three-second post-supervisor-exit bound stays; this
  does not alter Java's 500 ms bound. Failure cannot invoke fresh recovery.
  Fence evidence is persisted after process cleanup, not before stopping.
- Two real pinned-CLI/separate-upstream synthetic runs pass at private
  `2026-09-20-native-crash-handles-01` / final `-02`. Final source manifest pins
  code and binary. Thirteen active/held members before abrupt supervisor exit;
  zero active and 13 held/signaled members after, observed in 31.0000 ms.
  Fresh recovery retains one ambiguous attempt, full 80,000 synthetic-microUSD
  envelope and other dimensions; new admission denied, zero replay, $0 real USD.
- Focused Ruff and diff checks pass. Other eight matrix cases were not rerun
  for this fixture-only change. [Report](docs/verification/2026-09-20-native-dispatch.md)
  narrows historical count-only proof and retains all previous failures. No
  production OAuth/isolation or aggregate test/gate pass. Continue native helper
  conformance and independent reliability/mechanics while external inputs pend.

### 2026-09-20 — actual native collaboration and explicit session storage

- Continued after crash checkpoint `3f8899d`; added M0.1c.2c/.2c.1/.2c.2
  with F03/F07/F09/F11/F16, N01/N03/N04/N06/N08, C06/C14/C18/C20,
  partial T01/T04/T07/T12. SPEC v0.2.37 records the observed v2 tool surface
  and fingerprinted session-storage mode. All full gates remain open.
- Read-only native feature inventory retains an initial unsupported root flag
  placement and corrected command. Fresh-profile discovery -01/-02 finds no
  collaboration under the legacy feature/agents setting; -03 observes the v2
  namespace and captures real tool schemas. No API/tool names were fabricated.
- Native spawn/wait runs use the real CLI's child, not a second CLI shim. -04
  executes a clean child but fails the fixture's ordinary-message assumption;
  actual delivery is agent_message. -05 passes after parser correction. -06
  full-history spawn fails because the ephemeral parent thread is unavailable;
  both failed samples retain missing receipts/uncertain holds. -07 persistent
  private-profile experiment passes. No failure or charge is erased.
- Explicit NativeLaunch session_storage retains ephemeral default and supports
  private_profile with a changed profile digest; old qualification cannot carry
  across. Updated private schema. Final -08/-09 use ordinary NativeExec.start
  and pass clean-context/ephemeral and full-history/private-profile cases. Each
  observes distinct thread IDs, same root turn, expected parent-canary absence/
  presence, real agent-message result, unchanged plugin bytes and four receipts.
- Each fixture gateway records 40 input/16 output/56 synthetic microUSD; native
  root turn totals are only 30 input/12 output, demonstrating missing child usage
  in terminal totals. Receipt deduplication and one parent envelope reconcile.
  Child-specific enforced sub-budgets and authenticated attribution remain open.
- 77 relevant Python checks pass, zero skips, 5.23 s; full Ruff, schema export,
  TypeScript build and diff checks pass. Request-index capture is locked for
  concurrent native parent/child requests. Private evidence/source pins remain
  in native-helper-01 through -09 outside the repository; zero real USD, game
  launch or OS input. [Report](docs/verification/2026-09-20-native-helpers.md).
  Next: trusted child/lifecycle/accounting work plus independent authentic
  reliability/mechanics; enforceable isolation and live monetary inputs pend.

### 2026-09-20 — Exact E9E overlay findings retained and diagnosed

- M0.3.2a adds bounded private key-path/digest diagnostics; same checks, failure codes
  and acceptance rules. Source and tests are in pack_modes.py/test_pack_modes.py.
- Fresh stopped-server comparison remains 263/268. Static exact-JAR review,
  261 server/267 client JAR inventories including declared JarJar descriptors,
  two client semantic file checks and original archive comparisons identify
  client-specific and legacy settings without changing vendor files. Raw evidence
  remains external in 2026-09-20-e9e-overlay-review-01.
- First fixture snapshot failed the existing private-world inventory guard
  (14 pass/one fail); corrected only the test snapshot. Final 15 pass/zero skips
  in 1.06 s; two existing dependency warnings; targeted Ruff and diff checks pass.
- No authentic runtime test, exclusion, gate promotion, installation change,
  shared-desktop input or paid inference. [Report](docs/verification/2026-09-20-e9e-overlay-review.md).
  Next .2b: bounded loaded-config evidence and source-backed role disposition,
  followed by complete cold-restart/reference/expert-mechanic qualification.

### 2026-09-20 — Bounded loaded Forge configs and authentic cold-restart observations

- M0.3.2b.1/M3.1a: telemetry 0.2.0, ForgeTelemetryConfig/2, ServerStarted/2,
  ConfigSnapshot/1; exact private selector plan, first-tick END, declared/present
  raw values, bounded copies and explicit unsupported/unstable/quota outcomes.
  No ConfigValue getter, mutation, public route or scored predicate. SPEC v0.2.38
  records the partial contract and unqualified consumer/atomicity/isolation limits.
- Initial test compilation failed on fixture constructor/copy API; corrected.
  Initial test-only Ruff errors and missing evaluator PYTHONPATH invocation are
  retained. Final 51 Python tests pass in 0.51 s, 11 Java tests pass with an
  18-second pinned offline build, zero skips; targeted Ruff/diff pass.
- Initial real boot: 32 clean records, 145.672 s, but three placeholder selectors
  fail source-plan qualification. Corrected exact-overlay pair boot-02/-03:
  34/32 clean records, 149.438/145.016 s, distinct boot IDs, same requested six
  snapshots, common list exactly 145 overlay entries, both expert furnace
  assertions pass. No forced stop, player client, OS input or inference.
- Four config files are unregistered; Create legacy paths are absent/undeclared,
  current extraction timer/cannon shots/delay are 8/400/10. Exact ConfigSwapper
  bytecode/source explains missing-file/key skips. All original 268 file
  check/result/code/success-digests are unchanged, including five failures.
- Private evidence: 2026-09-20-e9e-loaded-config-01. Only the server telemetry JAR
  changed in the full mod-file comparison; 0.2.0 remains installed, old JAR is
  preserved externally. All Java/server processes are stopped.
  [Report](docs/verification/2026-09-20-e9e-loaded-config.md). No gate promotion.
  Next: exact role/consumer disposition, authoritative expert mechanics and
  authentic reliability work with current pins; live monetary/isolation inputs pend.

### 2026-09-20 — Native helper lifecycle and active-stream accounting

- Continued after loaded-config checkpoint 8479e97; M0.1c.2c.2a adds actual
  v2 idle message/follow-up/list/interrupt and active-stream interruption fixtures.
  Exact schemas came from prior native discovery, not invented adapters.
- First lifecycle sample fails on empty acknowledgement JSON parsing: four
  receipts settled, one unknown; full 16-call/80,000 synthetic microUSD hold
  remains. Corrected -02 passes flow; final -03 validates exact native statuses.
  Same child thread has two turns; queued message alone starts none; idle
  interruption leaves completed child available. Twelve calls settle/dedup
  to 120 input/48 output/168 synthetic microUSD; root totals omit both child calls.
- Active -01 observes real running-to-interrupted status and missing usage.
  Final -02 requires exact status/error shapes and a fresh supervisor: four
  settled/one unknown, no replay, same complete eight-call envelope retained,
  further admission denied. No claim of provider cancellation or complete resume.
- Original clean-context helper and wire restart regressions pass. Ninety-six
  Python checks pass, zero skips, 8.24 s; full Ruff/diff pass. A temporary patch
  indentation error was caught before native execution and corrected. Private
  source/ledger/receipt/plugin/request/recovery evidence and failed samples remain
  in native-helper-lifecycle-01..03, native-helper-active-01..02 and the two
  named regression directories. [Report](docs/verification/2026-09-20-native-helper-lifecycle.md).
- No game launch, shared input or live inference. Scope is partial
  F03/F07/F09/F11/F16, N01/N03/N04/N06/N08, C06/C14/C18/C20 and T01/T04/T07/T12.
  Next: enforceable native child admission/permissions/budgets/depth and complete
  state; continue independent game/guardian conformance while external live
  monetary and isolation inputs remain pending. No milestone or gate closure.

### 2026-09-20 — Partial source checkpoint published; implementation continues

- Fresh fetch confirms main at 579796d; existing changes preserved. Pushed
  codex/strata-native-dispatch through b8675a7 and opened [draft PR #2](https://github.com/OpenCnid/strata-bench/pull/2)
  under carried D03 publication authorization. No merge or release claim.
- The draft describes actual verification and unresolved gates; no raw evidence,
  credentials or game installations are published. Continue native helper
  concurrency/depth qualification and independent game/reliability work.

### 2026-09-20 — Native helper overlap passes; nested capability remains blocked

- M0.1c.2c.2b adds exact actual-CLI overlap and one-slot rejection through
  tools/native_helper_topology.py and the existing wire-accounted helper probe.
  Final pair/limit samples settle eight/seven calls (112/98 synthetic microUSD),
  each receipt deduplicated, with complete expected running/final agent sets.
  Root JSONL omits child calls. Twelve-request/45-second fixture bounds keep the
  same 80,000 synthetic microUSD envelope; no live ceiling or profile changes.
- M0.1c.2c.2c is blocked for the tested native nested profile. Actual children
  lack collaboration tools; explicit max depth two does not supply them. The
  pinned bundled Luna metadata says v1. Supporting current upstream source is
  separately pinned and does not prove this binary's implementation. Final
  nested capability failures settle all four calls without provider errors.
- Retain initial exact-denial discovery failure and initial nested unsupported
  calls/result-delivery failure: the latter holds four settled/one unknown,
  rejects a sixth ingress and retains all 12 reserved calls/80,000 synthetic
  microUSD. Fresh recovery reports zero replay and the unchanged hold. All raw
  artifacts and source pins remain external; [report](docs/verification/2026-09-20-native-helper-topology.md).
- 113 relevant Python checks pass with zero skips in 8.22 s; full Ruff and diff
  check pass. No game, shared-desktop input or live model dispatch. A required
  grandchild/depth/child-principal contract remains open, not converted into a
  negative-test pass. Next: independent authentic guardian/mechanic evidence,
  and a qualified nested seam when its concrete compatibility blocker is resolved.

### 2026-09-20 — Authentic current-policy guardian timeout retained

- M0.3b.2c.3c.2b.2b.2.2a exercises the current held-member guardian against
  authentic E9E on the prepared non-input desktop. Fresh current source/broker
  pins, unchanged minor-34 client and telemetry 0.2.0; TypeScript build passes.
  Server/client/worker/stop bounds remain 600 s/480 s/90 s/500 ms.
- Server readiness 115.468 s; client world 171.328 s, zero read retries. Worker
  bootstrap 757.9009 ms and initialization 304.6950 ms pass their 2,250 ms bounds.
  Three read-only scoped CLI calls pass; two world PNGs were inspected. No
  action intent, shared-desktop input or inference was requested.
- Required stop case fails: job call succeeds, root wait times out after
  510.8433 ms, tree proof is not_started and no stopped receipt is emitted.
  Complete supervisor chain preserves timing/faults; supervisor exits one.
  T07 changes not_run to fail for this explicit required failed case, with other
  cases still incomplete. Previous failed and single passing samples remain.
- All Java processes are now absent, client exit 125 occurs before outer cleanup,
  the server normally saves/exits zero after 388.188 s, input desktop is unchanged
  and temporary private arguments are retired. Telemetry has 261 valid records
  through tick 5,270 and six selected furnace assertions pass. Eventual cleanup
  does not reverse the deadline failure; no game/agent restore claim.
- [Report](docs/verification/2026-09-20-guardian-live.md); raw artifacts and
  post-stop audit stay external under 2026-09-20-guardian-live-01. A preparation
  shell-quoting failure was corrected before launch; no game sample was erased.
  Next: built native title-screen settings round trip and independent mechanics;
  diagnose authentic cleanup/scheduling without unchanged retries or relaxed
  deadlines. G0 remains fail and G1–G5 remain not_run.

### 2026-09-20 — First authentic native settings transaction and cold readback

- After `11c18f2`, M1.1a.2.3 splits actual round trip (.2.3a), independent cold
  readback (.2.3b), and still-unrun interrupted/foreign-change recovery (.2.3c).
  Existing source-bound Curios probe and unchanged minor-34 JAR run on two fresh
  non-input desktops with current source/Java/library pins, 480-second outer and
  280-second readiness limits. No server/world, physical input or inference.
- Actual first transaction passes unbound→F13→unbound in one client tick:
  exact registered Curios object/JAR, 253 runtime mappings restored, only owned
  file field changes, unrelated options bytes preserved, no commit, six valid
  hash-linked journal frames. Report ready 126.468 s; total 127.015 s.
- A distinct discovery-only client starts after verified terminal rollback.
  All 253 current encodings and persisted values match the restored map; exact
  options digest is unchanged, no transaction property or forward replay.
  Ready 124.625 s; total 125.125 s. Strict client_discovery audit executes with
  format pass/gate not_run, 34 vanilla and 219 unresolved mod owners preserved.
- Both base guardians emit confirmed stop receipts (coarse 250 ms field), both
  independent observation handles signal, input desktop stays unchanged, zero
  Java processes remain and both private argument files are retired. These
  title-screen results do not reverse the authentic-world T07 timeout.
- [Report](docs/verification/2026-09-20-native-settings.md) and updated settings
  runbook; exact private plans, sources, raw outputs, native journal, option
  backups, cold discovery and logs remain under 2026-09-20-native-settings-01.
  No broad tests were rerun for this evidence/documentation-only change. Full
  T05/G1, input/effects, general ownership/CAS, repair charges, interrupted/mid-write
  recovery and isolation remain open. Next: private-bridge pending transaction
  interruption, status and owned rollback without replay; keep conflict cases.

### 2026-09-20 — Authentic applied-pending settings interruption and recovery

- After `301a2ef`, split M1.1a.2.3c into applied-pending termination (.1),
  precise mid-write faults (.2) and foreign-change conflicts (.3). Two authentic
  title-client boots use the unchanged minor-34 JAR, exact Curios identity,
  current source/Java/library pins and unchanged lifetime/readiness/call bounds.
  Private bridge descriptors remain separately protected outside evidence.
- First boot performs one apply and confirms pending runtime/disk state, then
  forces JVM termination before rollback. Second boot's first operation queries
  the same transaction's status, then snapshots/rolls back/reads final status.
  No forward apply is issued after restart. Total times: 126.453/127.000 s.
- Independent audit passes exact call order, one prepared transaction, preserved
  four-frame journal prefix and complete six-frame hash chain, all 253 runtime/
  persisted values and byte-exact original options restoration. Its original
  redundant-observed-frame expectation was corrected against source/digest
  evidence; raw samples and acceptance criteria are unchanged.
- Both guardians confirm title-process stop (coarse fields 328/343 ms), held
  observers signal, Java count is zero, input desktop unchanged and temporary
  arguments retired. No server/world, physical input or inference. This does
  not reverse the authentic-world guardian deadline failure.
- [Report](docs/verification/2026-09-20-native-settings-recovery.md), runbook,
  current handoff and T05 row updated; raw evidence/audit stay external under
  2026-09-20-settings-recovery-01. Partial F06/F09/F16, N01/N02/N03/N04/N06/N08,
  C10/C11/C14/C18 and T05/T07/T13 advance. No aggregate gate closes. No broad
  local tests rerun for this evidence/docs change. Next: foreign-options/revision
  conflicts and precise native mid-write faults with conservative recovery.

### 2026-09-20 — Authentic foreign-options conflict negatives

- After `4ade4e5`, M1.1a.2.3c.3 runs one unchanged minor-34 title client with
  exact pins and a fresh protected broker/journal. No world, physical input or
  inference; client/readiness/API deadlines unchanged. Five expected rejections
  pass: stale apply, two rollback conflicts and two new-apply recovery fences.
- Unrelated bobView edits and an owned persisted third-value encoding remain
  untouched by rejected operations. Runtime state remains unchanged. Only exact
  fixture-owned bytes are removed before the original transaction rolls back.
  All 253 runtime/persisted values and exact options bytes are restored.
- Independent audit passes six intervention captures, one prepared transaction,
  complete ten-frame journal/hash chain and final restoration. Readiness
  126.438 s, total 128.719 s, coarse guardian stop 344 ms; held observer signals,
  Java count zero, desktop unchanged and private arguments retired.
- [Report](docs/verification/2026-09-20-native-settings-conflicts.md), runbook,
  T05 row and handoff updated. Raw evidence stays external under
  2026-09-20-settings-conflicts-01; bearer descriptors remain separately private.
  No acceptance threshold changed, no broad local suite rerun for evidence/docs.
  Partial F06/F09/F16, N01/N02/N03/N04/N06/N08, C10/C11/C14/C18 and T05/T07/T13.
  In-memory foreign changes, writer exclusion, physical effects, precise
  mid-write faults and full T05/G1 remain open; no aggregate gate closes.

### 2026-09-20 — Six explicit settings write-boundary crash points

- After `ea50836`, split M1.1a.2.3c.2 into the private fault fixture (.2a) and
  authentic exact-artifact qualification (.2b). SettingsStore's ordinary
  constructors keep a no-op observer; the explicit probe halts only at one
  planned prepare/runtime/options boundary across apply or rollback.
- Added strict bounded plan/fresh-root checks, source-bound title-only wrapper,
  exclusive diagnostic-mode preflight, forced armed/boundary state/options
  captures and abrupt JVM exit 86 without rollback/shutdown hooks. Existing
  journals/reports reject rearming; no endpoint, gameplay capability or physical
  event. SPEC v0.2.39 records the private fixture and unchanged real gates.
- Eight new tests include six actual abruptly terminated synthetic-runtime JVMs
  and six fresh recovery JVMs. They check precise partial states, bypassed
  shutdown hooks, status-before-rollback without apply, one prepared transaction,
  preserved journal prefixes and complete runtime/file restoration. Invalid/
  repeated plans and incompatible diagnostic modes reject before mutation.
- Focused Java checks: 33 pass. Full client build/tests/classpath: 448 pass,
  zero failures/errors/skips, 28 s. Selected native-settings/JVM/discovery/
  gameplay-packaging Python checks: 33 pass, zero skips, 5.40 s. Full Ruff,
  changed Markdown links, complete F/N/T/G/M rows and diff checks pass.
- [Report](docs/verification/2026-09-20-settings-crash-fixture.md); external
  2026-09-20-settings-crash-implementation-01 retains XML, logs and source/artifact
  manifest. Candidate SHA256 6332576ea722a9ab49255cb0187851b22e4e9f4fb8e42f70dbbdc19eb723f051.
  No Minecraft or live inference ran in these checks. Partial F06/F09/F16,
  N01/N02/N03/N04/N06/N08, C10/C11/C14/C18 and T05/T07/T13 only; original
  failures/full gates remain. Next preserve/install exact candidate and exercise
  authentic boundary/recovery pairs; arbitrary setter/power-loss and full
  effects/isolation/repair-accounting requirements remain unresolved.

### 2026-09-20 — New native crash artifact installed; recurring CTM startup failure

- Published `bb22448` source and updated draft PR #2. Verified clean source,
  zero Java processes, current candidate/source hashes and original options.
  Preserved the prior b2a91155…916896 artifact privately before installing
  6332576e…23f051 in the dedicated profile. No original CurseForge profile edit.
- Prepared six bounded crash/recovery pairs in fresh external storage, then
  launched only apply_runtime_written/crash. It exits signed -1 after 84.157 s
  in exact CTM 1.19.2-1.1.6+8 texture loading, repeating HashMap Node-to-TreeNode
  ClassCastException at ResourceUtil's negative-cache write. No armed report,
  reached report, journal or native fingerprint is produced; no settings apply
  occurs, and no recovery/later client launches.
- Actual sample is fail; settings boundary/recovery remain not_run. Guardian
  confirms PROCESS_EXITED, held observer signals, zero Java, input desktop
  unchanged, original options exact and temporary arguments retired. Independent
  startup audit and crash/log bytes are retained; strict UTF-8 log parsing was
  corrected to exact ASCII-byte signature checks without altering the log.
- [Report](docs/verification/2026-09-20-settings-crash-startup.md). B10 now maps
  M1/T05 as well as startup reliability; .2.3c.2b.1 is blocked on that dependency,
  and .2a.1 tracks diagnosis/remedy. Full requirements and previous failures remain.
- Read-only installed CTM bytecode confirms plain unsynchronized HashMap access
  with null negative entries. Upstream issue #176 has the same reported signature.
  The pinned MC runtime bytecode supports max.bg.threads (range 1–255) and uses
  ForkJoinPool for Bootstrap/Main executors. This is a parallelism setting, not a
  proof that every CTM access is serialized. Fresh one-worker diagnostic profile
  is planned with immutable pins and existing deadlines; no JVM flag, mod,
  threshold or remedy was silently changed. Source review bytes stay external
  under 2026-09-20-ctm-startup-review-01; exact upstream build revision is not yet
  established. Continue without unchanged retries or claiming CTM is repaired.

### 2026-09-20 — Two native crash recoveries; restore M0 priority

- [Authentic recovery report](docs/verification/2026-09-20-settings-crash-recovery.md) records two distinct diagnostic-profile crash/recovery pairs with independent audits. M1.1a.2.3c.2b.1b/.2 are verified only for the explicit write-boundary contract/profile; parent/default-profile/full T05 stay open. No threshold, capability or required case changed.
- Both fresh recoveries perform status before rollback, never another apply. All 253 mappings and original options bytes restore; original journal prefixes remain, all four clients terminal, arguments retired, desktop unchanged, no world/server/inference. Default-profile CTM failure and its exact-source diagnosis remain separate evidence.
- User asked to focus on SPEC and milestone completion. The four unrun M1 boundaries remain not_started while work returns to M0.3b.3.2.4b/G0 item 3: authentic machine/container operations and independent server evidence. This changes work order, not required scope. Live-host monetary/exposure/isolation prerequisites remain blocked; independent no-inference mechanics work continues.

### 2026-09-20 — M0 private machine reference implementation

- M0.3b.3.2.4b split into persisted reference (.1) and authentic prepared-copy operations (.2). [New reader report](docs/verification/2026-09-20-machine-reference.md) links the bounded private parser and exact installed Thermal/CoFH persistence inspection. SPEC v0.2.43 states its limited initial format, rejection behavior and required independent provenance.
- Executed 102 focused saved-block/machine tests (1.01 s); full Ruff passes after four test formatting errors. Synthetic fixtures cover no silent empty state, source/order checks and malformed/unsupported resources. No machine processing or G0 pass claimed.
- A one-shot protected server/world clone is being prepared outside the repository; original profile and prior failed samples remain. Next clean-start setup with no client, save baseline, then ordinary scoped API transfers/processing and private server/player reconciliation. Fixture funding and missing full energy/fluid/routing qualification remain explicit. No inference or shared desktop input.

- Authentic baseline addendum: setup-only server exits zero with complete telemetry and no client joins; 181.109 s. Immutable region, original source digest and three explicit input/20,000 RF setup resources verified. Initial unsupported-empty-ForgeCaps audit is retained; corrected reader accepts only empty compounds, rejects nonempty resource capabilities. Final 103 Python/package checks pass (1.21 s); full Ruff passes. Actual ordinary API trial started separately, pending outcome; no source/world restore or setup replay.

- Operating trial -01 is retained as failed before worker admission: harness used the settings fingerprint in the game domain. Zero native intents, unchanged furnace/chest resources, normal server save, zero Java and exact temporary-argument retirement verified; 404.516 s remains charged to development elapsed evidence. Source inspection explains the distinct game capability fingerprint. Fresh -02 fixes that input, recomputes capabilities before launch and keeps all original limits/current world state; no unknown replay or inference.

### 2026-09-20 — Authentic chest transfer reconciled; machine continuation

- [Native machine report](docs/verification/2026-09-20-native-machine.md) retains both failed attempts. -02 reaches API readiness in 242.079 s and transfers three dust from fixture chest to player through ordinary scoped actions; independent complete-inventory NBT delta and empty saved chest prove the transfer. Furnace remains empty/20,000 RF. Two distinct terminal intents/eight primitives/seven usage records reconcile. No machine-operation pass yet.
- Harness expected completed despite GameActionLane's explicit emitted terminal contract; corrected test treats the receipt as input evidence and still demands observed and independent saved effects. Four synthetic contract controls pass, including unknown and unclosed negatives. Fresh -03 uses the already-collected input and preserves current world state, costs and all failed samples; no forward replay/refill.
- Actual guardian wait fails again at 505.7315 ms against 500, with no tree proof and supervisor exit one. Normal server save/eventual Java zero/retired arguments/unchanged desktop remain cleanup evidence, not a corrected verdict. First/second attempts retain 404.516/514.437 s. G0/T07 remain fail; later gates and all remaining requirements persist. Source checkpoint 2f398f5 is pushed in draft PR #2.

### 2026-09-20 — Preserve bootstrap failure; compile worker schemas at build time

- M0.3b.2c.3c.2b.2b.2.1a / F01/F05/F16, N01/N02/N04/N06/N08, T01/T03/T07/T12 and G0: [startup report](docs/verification/2026-09-20-worker-schema-startup.md) records the concrete implementation and unchanged acceptance bounds. SPEC contract remains unchanged; generated validators retain all semantic checks and source-schema hash rejection, with reproducibility checked before every build and executable bytes included in capabilities.
- [Machine -03](docs/verification/2026-09-20-native-machine.md) retains WORKER_BOOT_TIMEOUT, no grant/guardian/actions, 417.546 s elapsed, intact player/furnace resources and failed pre-cleanup exit observer. Independent cleanup/resource audit passes; outer termination is not guardian proof. Original failures and unknown-action no-replay rules remain.
- Executed npm test: 128 pass/43 explicitly skipped; separately enabled pinned Java/Windows Forge regression: 55 pass/zero skip, covering all 43. Differential schema tests cover 2,467 mutated records, stale-byte rejection for four schemas, no compiler at runtime and capability pins. Initial guessed test case-count assertion failed with no validation disagreements; added boundary values and retained the count assertion. Python canonical/contracts/records 63 pass and gameplay package one pass. No authentic game or release gate is passed by these tests.
- Five idle-host real-child bootstrap samples move from 396.419–424.254 to 158.171–181.280 ms; fresh protocol imports from 284.015–306.297 to 38.602–43.650 ms. Actual loaded-game qualification remains required. Next one bounded continuation on the current saved resources with the changed broker, no reset/replenishment, inference or shared input. Native billing/isolation questions remain pending; full M0–M6 and conditional M7 are preserved.

### 2026-09-20 — Prelaunch session sequencing failure and correction

- M0.3b.3.2.4b.2 / N01/N02/N04/T07/T12: operation-04 retained as SESSION_PREPARATION_OMITTED; the client driver never launched Minecraft, no worker/native intent/session argument file exists. Server saves normally, exact player and selected-region bytes remain unchanged, Java zero. Its 173.954 s remains in development evidence. This is no worker timing measurement and no replay.
- Corrected private orchestrator verifies session preparation/hash/lifetime and all artifact/broker pins before server launch; the client driver still rechecks them. Initial Python escape error is caught by compilation before execution. Fresh -05 starts only after successful session preparation, retains all previous elapsed costs and uses current resources. [Machine report](docs/verification/2026-09-20-native-machine.md) tracks its pending result.
- Generator trailing blank line corrected; regeneration/build and eight focused schema/startup tests pass. Runtime implementation is unchanged; no threshold or contract changed. Source f840f65 is pushed; continuation remains active.

### 2026-09-20 — M0 fixture crash retained; concrete mechanics priority

- Operation-05 is failed: actual worker startup succeeds, ordinary pickup succeeds, deposit becomes unknown during a CoFH crash. ServerStarter exits zero despite crash and failed tile save; the initial audit's normal-save inference is explicitly superseded. Preserve all 3 intents, 11 primitives, 370.828 s and the unknown reservation/state; no replay, refund or fixture repair.
- Implemented bounded critical-log detection in `server_health.py` and the development server runner, plus saved-machine v2 Facing/Sides validation. Installed bytecode explains how partial NBT creates the invalid DOWN orientation. Focused Python 136 pass and full Ruff pass; raw failures and corrected evidence remain private. See the [integrity report](docs/verification/2026-09-20-server-save-integrity.md).
- User again required concrete M0 progress. Prepare a distinct, explicitly funded native-initialized fixture, then execute machine processing and expert crafting. M0/G0 remain incomplete; T07 fail, G1–G5 not_run, M7 conditional. No paid inference or shared-desktop input.

### 2026-09-20 — Correct native fixture prepared; machine/crafting run started

- M0.3.1a / M0.3b.3.2.4b.2a: distinct 18,214-file server copy, nine single-delivery setup commands, native furnace initialization then energy merge. Actual setup elapsed 199.422 s; independent v2 saved reader confirms valid orientation/sides, empty machine/20,000 RF, exact supplied chest resources and crafting table. Original selected region unchanged; no joins or Java left. [Evidence](docs/verification/2026-09-20-machine-crafting.md).
- Prepared and started one bounded API machine/crafting operation with fresh scope/session, exact artifact/source pins and existing deadlines. Prior crash/unknown request stays quarantined. No paid inference, shared desktop input or scientific sample; final operation evidence pending.

### 2026-09-20 — Actual processing succeeded; acknowledgment and craft remain open

- Separate fixture operation-01 produced three saved iron ingots and consumed 12,000 RF. Chest is empty; five andesite and three polished andesite remain in the player's inventory. The deposit receipt is unknown, so collection/crafting never ran. All 8 intents and 27 primitives reconcile; 521.719 s retained, normal recognized-log lifecycle, complete telemetry, terminal desktop/client and retired arguments. Guardian fails 500.5117/500 ms. Original failed audit remains immutable.
- M0.3b.3.2.4b.2b: implement one extra charged read-only refresh only for an exact pre-click owned-state echo; retain exact predicted cursor/all-player-slot confirmation, failure on other owned changes, original deadlines/budgets and zero input replay. Policy version/Forge minor advance explicitly. Tests and authentic causal qualification pending. Existing output will be collected under a fresh epoch after resynchronization; no restoration/refund.

### 2026-09-20 — Implement bounded feedback reacquisition and authority bootstrap

- M0.3b.3.2.4b.2b/.2c: machine policy v2, Forge minor 35, strict cross-language negotiation; one charged read for an exact pre-click echo, never click replay. Add opt-in private loaded-runtime identity publication before static authority/action lane construction. Original lifetime, confirmation, budget and privacy requirements remain. [Implementation and checks](docs/verification/2026-09-20-machine-feedback.md).
- Pinned Forge build/reobfuscation and 55 selected Java tests pass, Node 12 plus four explicitly enabled JVM/broker cases pass, Python-to-JVM 24 pass, targeted Ruff passes. Initial Node selection's 43 opt-outs are not claimed covered by four selected cases. No full gate closes.
- Installed candidate 32e0fb4 with previous JAR retained and no Java processes active. Prepared and launched epoch-2 development continuation from persisted output; all previous costs/state retained. It will observe, collect and craft without replaying the unknown deposit. Actual result pending; no paid inference/shared input.

### 2026-09-20 — Fix vanilla crafting permission continuity while Forge boots

- M0.2i / F01/F06/F09/F16, N01/N03/N04, T01/T03/T07: replace global recipe-book revision equality with selected recipe object and per-unlock authorization binding. Unrelated/duplicate unlocks no longer cancel a partially executed craft; selected revocation/regrant, book reset and declaration replacement still fence continuation. Preserve exact menu/resources, no replay, deadlines and click charges. Vanilla capability minor 8 records the policy.
- Added focused synthetic cases for normal unlocks during crafting and selected-recipe invalidation. They are not yet executed. Do not rebuild the shared compiled broker until the active Forge pair is terminal. Prepare separate protected vanilla mechanics evidence; no vanilla server or worker launched yet.

### 2026-09-20 — machine output collected; EMI discovery implementation

- Operation-02 confirms exact player +3 ingots, empty machine and unchanged 8000 RF; no uncertain deposit replay. Three unique intents/12 primitives, 496.312 s; aggregate 39 primitives/1018.031 s. Craft discovery returned an empty JEI page, so crafting remains failed/unrun. Guardian fails at 513.8277/500 ms. Private audit-03 corrects stale epoch-1 journal/telemetry references in two preserved failed audit attempts, without changing game evidence or thresholds.
- M0.2i: TypeScript build and seven selected recipe checks pass; no authentic vanilla craft claim. M0.3b.3.2.4b.2d begins explicit exact-pack EMI support following installed-bytecode diagnosis. F01/F05/F06/F09/F16, N01/N03/N04/N06, T01/T02/T03/T07/T10/T12/T13; G0 stays fail.

- M0.3b.3.2.4b.2d: explicit EMI source implemented; [bounded projection and cross-language checks](docs/verification/2026-09-20-emi-crafting.md) pass. Rebuilt candidate ff5fbf5 installed after all prior Java processes ended. Operation-03 is running on the same world/resources under epoch 3 for actual expert crafting; previous deposit/collection are not replayed. No inference or shared-desktop input. Actual craft remains pending.

### 2026-09-20 — authentic EMI discovery; interrupted craft retained

- Operation-03: exact EMI expert furnace definition delivered and table opened; craft c3100844-5741-4f68-a5aa-b4c2ae313735 is unknown/REVISION_CONFLICT after 19 emitted primitive events. Two intents/25 total primitives and 408.172 s retained; aggregate 64 primitives/1426.203 s. The stopped save has no furnace, unchanged 3 ingots/3 polished andesite, and five dropped andesite at the avatar (2+1+1+1), not a refund or unexplained loss. No replay. Guardian narrowly passes this sample at 453.2983 ms from wait start; earlier failures remain T07/G0 fail.
- M0.3b.3.2.4b.2e implements derived-preview continuity and a stronger final server-output barrier. A first-row slab preview is observed; the exact prior received/current difference was not logged, so the causal diagnosis remains a source-supported hypothesis. Focused checks and new ordinary recovery/craft are next. Vanilla mechanics fixture copy (59 files, nine explicit setup commands) prepared separately and setup is running with no clients.

### 2026-09-20 — retain second craft failure and advance vanilla mechanics

- Forge operation-04 recovered the five prior dropped andesite by ordinary pickup, discovered the explicit EMI recipe, opened the table, then failed REVISION_CONFLICT after its first placed ingredient. Unknown request efd5c070-6b34-49ba-93eb-980952428685 remains unreplayed. Two intents/16 primitives, 397.688 s; aggregate 80 primitives/1823.891 s. Independent player-plus-entity reconciliation preserves every resource; five andesite remain dropped, no furnace exists, machine remains empty at 8000 RF. Guardian passes this sample at 480.3537 ms from wait start; previous failures keep aggregate T07/G0 fail.
- The preview change is not a complete repair. Add bounded operator-only native fault source locations (no exception messages, arguments, inventory or credentials) to distinguish the remaining failure before another Forge attempt. No new public affordance or acceptance relaxation. Preview implementation passed 32 selected Java checks, TypeScript build and three focused Python/JVM recipe transports; fault logging is source-only pending rebuild.
- Vanilla M0.2i: separate 59-file fixture, nine recorded no-client setup commands, server stopped without recognized failure in 24.625 s. Saved references confirm two logs/chest/table/ground; original player bytes unchanged. First launch queried before join, accepted zero actions, left player unchanged and exposed a private drain/close race; preserve its failed report and superseding audit. Second bounded epoch corrects read-only readiness and log shutdown order and is running the public API mechanics chain.

### 2026-09-20 — diagnose vanilla startup and fence terminal pre-spawn failures

- M0.2i/M0.2j: attempt 02 ended GAME_CONNECT_TIMEOUT with zero accepted actions. The auth lock belonged to exited PID 42696 from interrupted attempt 01. Verified its absence through Win32 process inventory, retained the lock as private evidence, and retired only that reviewed lock. Cached authentication then passed in 1358.3601 ms without a game connection or model call.
- Adapter terminal error/end now reaches ActionLane before the first spawn, fences the epoch and exposes only a sanitized code through existing supervisor health. TypeScript build and four targeted connection tests pass, including the actual pinned backend against a synthetic held cache lock; no credentials/provider traffic in that regression.
- Authentic epoch 3 joined in 16.672 s and completed both ordinary log-mining actions (two primitives). The private checker omitted required movement tolerance; schema validation rejected it before dispatch. Preserve the failed checker, no mining replay or replenishment; continue from independently reconciled saved resources. Aggregate game mechanics remains partial.
- Private Forge fault-location logger compiles/reobfuscates successfully (18 s). It records bounded internal source locations only; no new authentic Forge result yet.

### 2026-09-20 — authentic vanilla conversion and fresh-tool implementation

- M0.2i: epoch 3 stopped normally in 134.016 s; saved blocks are air and player gained exactly two logs, with two journaled primitives. Its full-world resource audit found an unrelated nearby wheat-seed drop without a frozen pre-join entity baseline; retain that limitation. The narrowed mining/player delta is supported, not complete world conservation.
- Epoch 4 completed 11 actions/59 primitives in 133.719 s: bounded walking, chest deposit/withdraw, two plank conversions and one stick conversion. Final server save contains exactly seed 1, planks 6, sticks 4; source chest empty. Wooden pickaxe is unlocked but unsupported under the old blanket NBT restriction; no pickaxe action dispatched. The private checker mislabeled unsupported as RECIPE_NOT_UNLOCKED; preserve its raw report.
- Implement fresh Damage=0 outputs with registry/count/tag bounds, exact output/cursor/destination comparisons and preservation of pre-existing tagged stacks. Capability minor 9, SPEC v0.2.46; other metadata/remainders remain unsupported. TypeScript build and nine focused recipe checks pass. Epoch 5 now completes the ordinary table pickaxe sequence with the existing resources; final save audit pending. Zero paid inference; G0 remains fail.

### 2026-09-20 — saved vanilla pickaxe outcome and return to E9E craft failure

- M0.2i: epoch 5 completed three actions/37 primitives, clean worker/server termination and 74.157 s. Independent NBT audit passes exact delta: planks -3, sticks -2, wooden pickaxe +1 with sole integer Damage=0 tag; final player seed 1/planks 3/sticks 2/pickaxe 1, chest empty, mined cells air. All five attempts retain 98 primitives/397.205 s plus 24.625-s setup. [Public evidence summary](docs/verification/2026-09-20-vanilla-mechanics.md). Full world seed-drop reconciliation, other actions/reconnect/private scoring/isolation and G0 remain open.
- M0.3b.3.2.4b.2e: retained operation-04 client log and prior JAR, installed bounded fault-location candidate df531cd9d6c4dc2bc30d0e4144f03f81f1bc4652f8a2b82a25833372236708b2 only after all Java clients/servers were terminal. Fresh operation-05 scope/epoch, ordinary input-drop recovery, no uncertain request replay/refill, and prior 80 primitives/1823.891 s carried forward. Bounded server/client orchestration is running; no result yet.

### 2026-09-20 — locate Forge owned-state mismatch and implement bounded reacquisition

- M0.3b.3.2.4b.2e: operation 05 failed unknown craft 8177553c-c197-4ef2-be49-c65ac4986de5 with REVISION_CONFLICT, exactly located at GameInventory.Steps.tick:68 (server reply/current owned mismatch). Private stderr/stdout and source-location record retained. Two intents/38 primitives/397.703 s; aggregate 118/2221.594 s. All resources reconcile: five andesite and three polished andesite are now dropped, three ingots remain owned, furnace absent, machine empty/8000 RF. No replay/refill; guardian narrowly passes 445.1679/500 ms, earlier failures retained. All targets terminal and arguments retired.
- M0.3b.3.2.4b.2f / SPEC v0.2.47: implement one charged refresh only for exact current pre-state rollback after a full exact predicted server reply; all other disagreements remain failures. Strengthen unaffected owned-slot checks. Retain final-output barrier, unchanged acceptance bounds and private mismatch diagnostics. Focused Java Inventory/Grid/Crafting: 34 pass, no failures/skips, build 23 s; TypeScript build and one capability identity check pass. Authentic operation 06 is the next step; this failure location does not prove the new recovery case occurred.
- Source checkpoint a2a5b2b pushed to draft PR #2. Fresh remote main remains 579796d. Continue M0 work beyond this checkpoint.

### 2026-09-20 — isolate authentic inventory component conflict

- M0.3b.3.2.4b.2f / F06/F09/F16, N01/N02/N04, T03/T07/T12, G0: operation 06 failed with exact ingredient/cursor reply but changed backpack slot 45. Exact pre-state reacquisition did not apply. Full saved player/drop NBT conservation passes; 29 primitives/401.844 s retained, aggregate 147/2623.438 s. Guardian passes narrowly at 475.203/500 ms; older failures remain. All targets terminal and arguments retired.
- NativeItemDiagnostics adds a bounded operator-only field/hash diagnosis with no acceptance change. Pinned Forge build/reobfuscation passes (16 s); no broad suite rerun for diagnostic-only code. Operation 07 is running, candidate 5432b56ef6a6fa6d7cd6f1d68116df22e3a147da4a5c586738455f9a608e4351. [Evidence and limitations](docs/verification/2026-09-20-emi-crafting.md).

### 2026-09-20 — repair client metadata drift without accepting it

- M0.3b.3.2.4b.2g / F06/F09/F16, N01/N02/N04, T03/T07/T12, G0: operation 07 fails native craft b0e405b3-9d02-426f-adb0-439be5d6b285 with REVISION_CONFLICT after client-only tag/contentsUuid initialization; its public report ends LEASE_EXPIRED. Full saved resource conservation passes. Retain 45 primitives/398.735 s; aggregate 192/3022.173 s. All targets terminal, arguments retired; guardian 384.7081/500 ms narrowly passes, historical failures remain.
- SPEC v0.2.48 / Forge minor 39 adds one bounded charged reacquisition for untouched client component drift, with identical IDs/counts/positions, exact cursor/clicked stack, original server component identity and renewed exact current/server equality. Persistent drift and changed server components reject, with zero repeated mutations. Java Inventory/Grid/Crafting 35 pass, no failure/skip; build 22 s. TypeScript build and the named capability test pass. An initial Node selector matched no cases and receives no verification credit. Operation 08 is running with candidate 5424bfd7d7d75d2149321e4edeb8d2d2d7c9f1345d740c6989bb034975758c18. Source of upstream UUID initialization remains unproven; share-tag normalization was not implemented.

### 2026-09-20 — extend exact restoration through craft barriers

- M0.3b.3.2.4b.2g: operation 08 recovered two distinct client contentsUuid drifts, completed the grid and failed unknown craft 1a16ae11-b6eb-4153-a9e2-0bb53cca4761 at GameCrafting.feedback before output pickup. Exact final mismatch fields were not captured; diagnostics now cover this boundary. Full saved resource conservation passes, ingredients dropped, no furnace. Retain 55 primitives/405.859 s; aggregate 247/3428.032 s. All targets terminal/arguments retired, guardian narrowly passes 472.6411/500 ms; previous failures remain.
- SPEC v0.2.49 / minor 40 adds one exact-baseline metadata reacquisition at each fill/take feedback barrier without changing original output, grid, remainder, resource or timing criteria. Eleven focused Java crafting checks pass, build/reobfuscation 19 s; TypeScript build and named Node capability check pass. Operation 09 is running candidate 75d9308fe42ec90f3f0742b18cd159fb24ecbe4ffb2cba287a2eec2f1b684def. Authentic result pending; [report](docs/verification/2026-09-20-emi-crafting.md).

### 2026-09-20 — handshake repair and actual reconnect prerequisite

- M0.3b.3.2.4b.2g: operation 09 fails before worker admission because Python and TypeScript native capability literals still expected craft policy v2. Zero primitive actions; ordinary join picked up prior drops, and independent full saved player/drop resources reconcile. Machine remains empty/8000 RF. All targets terminal/arguments retired. Retain 305.485 s, aggregate 247 primitives/3733.517 s. Correct both validators; actual Python/Node-to-JVM handshake checks pass (two Python, one Node, no skips), plus the tightened Python old-policy rejection and targeted Ruff. Operation 10 is running the same Java candidate with corrected compiled broker/source pins.
- M0.2k/M0.2d / SPEC v0.2.50: two authentic reconnect preparations reach PATH_BLOCKED with zero movement input, 148.406 s retained. Public-only offline reproduction locates nearby floor eviction during a 2203-cell pagination sequence; restoring already-delivered nearby cells restores the route. Implement nearest-eye retention, unchanged 1024-cell capacity and delivery-only knowledge, vanilla minor 10. Build/checks deferred until the active Forge broker finishes to preserve its pinned bytes. Cancellation/reconnect has not passed.

### 2026-09-20 — authentic vanilla cancellation and fresh-epoch continuation

- M0.2k.1 / F06/F09/F16, N01/N02/N03/N04, partial T03/T07/T12: six focused navigation/pagination checks and same-public-data route reproduction pass with the 1024-cell nearest-eye retention fix. Phase 03 actually moves and cancels with confirmed release, 23 primitives, and mandatory reconnect; its incorrect no-resync checker assertion is retained as fail. Phase 04 passes fresh observation, preserved cancelled receipt/dedup, stale-epoch rejection and one fresh look (1 primitive). Independent saved-player/NBT/journal audit passes all checks. Four attempts retain 297.156 s; inherited 37 plus new 24 primitives = 61 in the durable journal. No reset, refill, inference or desktop input. All targets terminal; broader recovery/Forge/guardian/soak gates remain open.
- M0.3b.3.2.4b.2g: operation 10 fails unknown craft a17a9de7-b7c3-4334-9f42-6d266c89a20f at final feedback comparison after several recovered metadata drifts. Its final structural difference was not logged. Full saved resource conservation passes, both ingredients dropped; retain 60 primitives/396.765 s, aggregate 307/4130.282 s. Guardian narrowly passes 356.6464/500 ms; historical failures remain. Full slot/cursor ID/count/hash diagnostics now compile/reobfuscate (16 s). Operation 11 is running candidate 48ff462042134cc0d5f3464db8acba6edebfd513f83b9f85c6d81e31cd89bf0a, with unchanged acceptance.

- M0.3b.3.2.4b.2h / F01/F06/F10/F16, partial T03/T10/T12, G0 item 3: operation 11 public expert craft/close and independent exact saved-resource audit pass. Consume 5 andesite/3 polished andesite, gain exactly 1 furnace, preserve all other full NBT. 70 primitives/393.234 s; all eleven pairs 377/4523.516 s. Narrow guardian 414.9795/500 ms pass does not erase failures. No reset/refill/replay/inference/desktop input; all targets terminal. Raw callback remains score-ineligible. Next M0 work is server causal provenance/private scorer controls, with isolation/monetary questions still pending.

- M0.3.10.1 / SPEC v0.2.51: implement server-only ordinary result-click HEAD/RETURN records and private exact-resource qualifier, retaining callback ineligibility. Pinned telemetry 0.3.0 compiles/reobfuscates in 15 s; 72 focused Python checks pass in 0.80 s, targeted Ruff passes after formatting. Authentic witness, setup/team/role authority, scorer admission and nonleakage remain unverified. A distinct operator reference fixture is preparing; no live inference or shared input. [Report](docs/verification/2026-09-20-craft-witness.md).

- M0.3.10.1: telemetry 0.3.0 real setup boot/stop passes recognized-log checks, 136.719 s retained. Saved baseline confirms inherited 1 furnace/3 ingots and declared chest inputs (5 andesite, 3 polished andesite, 1 gifted furnace), no craft callbacks/witnesses. A prelaunch stale escaped JSON path was caught and corrected with original template/pins retained; no action occurred. Distinct `craft-witness-01`, epoch 1, operation-01 is running; candidate server JAR 9d206432e99a39a4e747faa93f0731857e45433088f66f93068176ea9a742aa7, unchanged client minor 40. Final duplicate-ID/old-module negatives bring the focused witness suite to 24 pass (0.43 s). No paid inference, shared desktop input or campaign admission.

- M0.3.10.1 / M0.3b.3.2.4b.2i: witness control 01 transfers the declared gift and inputs, then craft cc5e3f9a-de61-4f38-aafc-26ce5b31920f stops at the filled-grid cursor/conservation/output guard before any result take. No native craft callback/witness; unknown action retained. Saved full resources reconcile: player has 2 furnaces/3 ingots, 5 andesite/3 polished andesite dropped, machine empty/8000 RF. Retain 69 primitives/401.375 s; linked development pairs 446/4924.891 s plus this fixture's separate 136.719-s setup. Guardian narrowly passes 479.5841/500 ms. The initial independent audit had a zero-padded supervisor filename error; its partial report remains alongside corrected complete audit, without overwriting saved evidence. Gift possession produces no craft credit; positive witness still unrun.
- Minor 41 captures a server-confirmed baseline before each fill instead of storing a local possibly materialized component snapshot. This resolves a reproducible contract defect, not a proven explanation of the preceding final guard failure. Twelve focused Java checks pass (0.115 s), build/reobfuscation 20 s; TypeScript build, two Node checks including actual JVM, two Python checks including actual JVM, and targeted Ruff pass. Initial Python selector matched no test; corrected executed selection is recorded. Candidate 7fabe027fdad35a531c6e91ecb0d26c0dfce2aa4375508911f32320fee37f01d is running as witness control 02, fresh scope/epoch 2 with existing saved resources, no replenishment, replay, inference or desktop input.

- M0.3b.3.2.4b.2i / M0.3.10.1: control 02 public craft/close and independent full saved resource audit pass with minor 41: five andesite + three polished andesite -> one more furnace (2 -> 3), no other NBT changes, no drops, machine empty/8000 RF. Retain 68 primitives/403.297 s; linked pairs 514/5328.188 s plus 136.719-s setup. Guardian fails 506.6415/500 ms (507.4500 ms after termination start), so the overall run remains fail. All targets terminal, arguments retired. Raw callback exists, but zero click witnesses; private positive acceptance fails.
- Exact installed FastWorkbench 7.1.4 bytecode identifies CraftResultSlotExt replacing the vanilla slot and using ResultContainer.getRecipeUsed during its native consumption loop. The original telemetry explicitly rejects that class. Implement telemetry 0.3.1 exact class/artifact allowlist, mandatory applied-mixin marker and private type diagnostics; no resource threshold change. One focused Java boundary check/build passes (17 s), 79 Python witness/telemetry/config checks pass (0.93 s), targeted Ruff passes. New candidate 8e5c06c3aadc482643f54094629872abfafe7197b63b15b65fb41feebfef8ca7 is in setup-fastbench. This is a second explicitly supplied operator control (5 andesite/3 polished andesite), preserving all prior outputs/failures/costs; no world reset, campaign restore, paid inference or shared input. Authentic witness still pending.

- M0.3.10.1: telemetry-0.3.1 authentic setup boot/stop and independent saved baseline pass. Applied click-hook marker and exact loaded FastWorkbench hash confirmed, prior player bytes unchanged, declared eight inputs in chest, machine 8000 RF. Additional setup 130.188 s (both witness setups 266.907 s). Public control 03 is running, fresh scope/epoch 3, unchanged minor-41 client; audit_operation_03.py prepared. Authentic positive witness remains pending.

- M0.3.10.1 / M0.3b.3.2.4b.2i: control 03 fails before result take; private logs identify clean cursor, conserved resources and empty derived output. Independent saved audit preserves all eight inputs as drops, player 3 furnaces/3 ingots, machine empty/8000 RF. Unknown 08b7aaed-80ec-4571-afc9-7e033fb65095 remains unreplayed. Retain 69 primitives/398.547 s, linked pairs 583/5726.735 s plus both witness setups 266.907 s. Guardian passes 375.1394/500 ms narrowly for this run; earlier failures remain. No callback/witness. Pinned FastWorkbench bytecode and loaded config establish pooled result updates at server END every two ticks. Minor 42 implements at most 20 charged fresh preview reads with frozen non-result resources, unchanged deadline/budget and no repeated fill. Focused tests pending.

- M0.3b.3.2.4b.2i / SPEC v0.2.52: minor-42 delayed preview motor passes 15 focused Java checks (0.092 s), pinned build/reobfuscation (20 s), TypeScript build, two Node checks including actual JVM (1.90 s), and two Python checks including actual JVM (2.78 s). Candidate 59f113e4972fbe0d07e349f9d83f6452ac4e9f5f802d7491c5c863176f4b0da4. Distinct control 04, epoch 4, starts with unchanged telemetry 0.3.1 and the eight previously dropped inputs; no new allocation or unknown replay. Raw independent audit prepared, runtime result pending.

- M0.3b.3.2.4b.2i / M0.3.10.1: control 04 fails before output take with REVISION_CONFLICT, unknown db2d6c9c-b623-463e-b26a-5fe6dbe9f20f. Diagnostics show a full reply with empty result followed by the ordinary expected furnace update; all non-result state agrees. Minor 43 requests fresh full feedback for only that exact transition, retaining the same 20-read bound and all resource/deadline/budget checks. No unknown replay. Independent saved audit and full charges recorded in the witness report. Targeted verification next.

- M0.2c.1: start reusable private evidence reconciliation while the bounded craft control runs. Replace repeated operator-only aggregate counting with source-byte pins, per-request native/public binding, charged high-water marks and measured server clock summaries. This does not admit scores or claim complete host/helper accounting.

- M0.2c.1 / SPEC v0.2.53: reusable private cost join now reconciles exact native/worker action and high-water charges with server telemetry. Fourteen synthetic negative/positive checks pass (0.51 s), Ruff passes, and authentic retained control 04 reconciles 57 primitives, three global safety releases, its unknown action and measured 5505 ticks/278.1160466 s, with final tick 5515 separately retained. No fabricated tail time, score admission, full inference accounting or isolation claim. [Report](docs/verification/2026-09-20-run-costs.md).

- M0.3.10.1a: authentic control 05 public craft/close, independent saved-resource audit and exact private resource witness all pass. Player 3 -> 4 furnaces; eight ingredients consumed, other full NBT/3 ingots/8000 RF unchanged, no drops. Native bracket/callback matches exact recipe at tick 4297. All current targets terminal, arguments retired; zero Java verified. Retain 69 primitives/428.688 s, linked pairs 709/6557.205 s plus 266.907-s setups. Guardian 373.5694/500 ms passes this sample only. Audit SHA add85a89446c3be9c18e777f53f57858fe9bfeee4c734411d9b2bdc80c187e44. Scoring authority and isolation remain blocked; no campaign/scientific admission.
- M0.2c.1: actual cost-join CLI also reconciles control 05: 69 primitives, two global safety releases, 5998 sampled server ticks/302.8138054 s and final tick 6013. Report digest 9865619d151ee4347ea2ecd7d911990429b33de0181b0c4ac2206629f2dd7e05. Previous failed controls and their unknowns remain outside this single-scope report and in linked aggregates.

- Packaging cross-check initially fails on an old recipe-query help string that omitted the already implemented --source jei|emi selector. Update that exact expectation and explicitly list the new private evaluator files among exclusions. The unchanged four-file allowlist, forbidden-grant behavior and source-path nonleakage all pass; one actual packaged CLI check 0.23 s, targeted Ruff pass. Initial failure is retained here; no production privacy boundary was relaxed.

- M0.2k.2: prepare a distinct Forge cancellation/restart reference with no new resources, unchanged minor-43 client/telemetry-0.3.1, exact source pins and private two-phase shared 1200-s immutable authority/1000-primitive cap. Each process remains 480 s, worker 90 s, action 5 s and guardian 500 ms. No restart renewal or cost refund. [Procedure](docs/verification/2026-09-20-forge-reconnect.md); first phase preflight passes, runtime not_run.

- M0.2k.2: authentic phase 01 fails before dispatch, OBSERVED_LONG_ROUTE_UNAVAILABLE; fourth page 1970 ms excluded under declared 1900-ms margin. No movement or cancellation. Independent stopped-player/resource/cost audit passes its applicable checks; complete cancellation audit fails. Retain 2 safety releases/416.078 s, linked totals 711 primitives/6973.283 s plus setups 266.907 s. Guardian 361.7626/500 ms passes this sample only. No phase-02 cancellation continuation admitted and no authority renewal. Advance M0.2c.1 multi-epoch cost reconciliation while route prerequisite remains unresolved.

- M0.2c.1a / SPEC v0.2.54: implement private cumulative restart cost reconciliation, unchanged native/public histories and authority, retained unknowns/counters, distinct boot clocks and incremental charges. Existing 14 checks pass; expanded run 29 pass/one CLI-envelope test failure, then corrected case passes. Targeted Ruff passes; actual retained Forge source reconciles two releases. No authentic restart or full accounting gate claimed. Source/report digests and invocation history in the cost-join report.

- M0.3.2b.3 / SPEC v0.2.55: implement one-shot private connected-client config probe, unchanged exact selector plan, bounded non-mutating snapshots and strict private importer. Telemetry 0.3.2 JAR 120dd7f445c809ef47fae7024b9cb09e354bd5410380926f569ee1ac712531de; seven Java checks/19-s offline build, 11 client importer checks and 10 prior/current producer witness-schema checks pass. Actual role evidence remains unrun. All five stopped-file failures retained.

- M0.3.2b.3: source-pinned authentic client-role trial 01 launched with exactly one added client diagnostic JAR, original server 0.3.1 and no new resources. Cached session/preflight pass; result pending. Private root C:/Users/Darian/.strata/evidence/2026-09-20-client-config-role-01. Each process remains 480 s, worker 90 s, guardian 500 ms. One additional strict numeric-flag negative passes.

- M0.3.2b.3: authentic trial 01 and all 18 audit checks pass; exact six selected client-role observations, process/JAR/plan binding, unchanged full inventory/ender NBT, position and selected client files. Two global releases/404.063 s, aggregate 713 primitives/7377.346 s plus setups 266.907 s. Guardian 367.8943/500 ms for this sample; prior failures retained. Actual private importer CLI passes; arguments retired, normal server stop and zero Java verified. Selected observation child verified; parent lock/consumer/cold-restart/isolation and G0 remain open.

- M0.2k.2: read-only source verification identifies the existing original reference world with its prior public three-step route still clear. The newer crafting fixture occupies that route. Preserve both worlds and failed trial; next cancellation/restart pair uses current original-reference bytes. Position/full inventory/ender match prior reference, but Attributes and warden_spawn_tracker differ; retain that actual baseline without restore. No policy/threshold change. Current client minor 43 plus telemetry 0.3.2; original server telemetry 0.2.0. Prepare both phases before dispatch.

- M0.2k.2: replacement original-reference pair fully prepared before launch, including immutable authority, epoch-2 public dedup/stale denial/fresh look, terminal-only journal backup, independent saved-state audits and reusable restart cost join. Phase 01 launched; runtime result pending. Phase 02 has not been dispatched and requires passing source safety plus >700 s remaining original authority. Active private root C:/Users/Darian/.strata/evidence/2026-09-20-forge-reconnect-02. No world reset, visibility expansion, route-threshold change or paid inference.

- M0.2k.2 / M0.2c.1a: replacement Forge restart pair terminal; public cancellation/fresh-epoch/dedup/stale denial and all saved-state/journal/cost checks pass. Two guardian waits fail unchanged 500-ms bound: 529.8644 and 505.9196 ms, with independently confirmed delayed root exit. Narrow cost join verified: 27 inherited + 4 new = 31; paired elapsed 1032.735 s, interphase gap 15.760 s separately retained. Linked pairs 744 primitives/8410.081 s plus witness setups266.907 s. Normal server stops, retired arguments, zero Java confirmed. Complete G0/reliability remain fail; no unchanged repeat.

- M0.2k.2a / SPEC v0.2.56: implement reusable private stopped-journal staging instead of one-off transfer code. Preserve full native/database bytes, original authority, unresolved receipts and charges; reject unconfirmed/foreign/changed sources, active WALs, stale epochs and expiration. Exclusive destination with manifest-last commit retains interrupted partials and refuses overwrite. Initial15 synthetic cases pass; four affected final cases pass after publication strengthening, Ruff passes. Actual expired Forge source is correctly rejected with no launch/renewal. Report and runbook linked in child row; authentic successful staging and all aggregate gates remain open.

- M0/G0 reliability: source-backed JVM diagnostic profile g1-periodic-heap-return/1 prepared; exact installed JVM accepts periodic-GC/free-heap flags. Existing artifact/options/server/world pins preserved, bounded private GC logging added, deadlines and memory cap unchanged. One read-only authentic pair launched; independent audit is prepared and will run automatically. No paid inference. Prior shutdown failures retained; no performance or stop claim yet.

- M0.2k.2a: add staged-set verification against the original private receipt digest before launch preparation. Recheck every byte, epoch/authority/headroom/expiry and reject extra or partial files. Seven new/affected verification/interruption cases pass1.63 s; the existing staging CLI still passes0.42 s after argument routing changes. Ruff passes. Source83fd34ed8fb4e58ab7cdb649db2275cdc92163d5afb2e51c51201f8b2084ce3b. No game or inference launched by this operation; authentic successful consumption remains unverified.

- M0/G0 reliability: g1-periodic-heap-return/1 fails GAME_BRIDGE_STARTUP_TIMEOUT before bootstrap/authority/worker creation. Client277.906 s/pair469.891 s; zero observed native inputs, full cost joinnot_run. Original audit retains missing-public-report error; separate failure audit passes eight applicable cleanup/resource checks and preserves Attributes/warden_spawn_tracker changes. GC log631 pause lines/27 concurrent-mark lines/no periodic events. Complete server spool265 records/5403 sampled ticks/272.5801656 s. All targets terminal, arguments retired, zero Java verified. Linked references744/8879.972 plus prior setup/gap costs. Candidate and G0 remain fail; no unchanged retry.

- M0.2k.2 / .2a: prepare and launch original-world restart pair03 with3 GiB heap/default GC ratios, complete current-source baseline and unchanged artifacts/options/deadlines. Replace manual transfer with reusable staging+verification; add another pinned verification before client2 dispatch and matching terminal audit. All sources/checkers/audits/pins prepared before launch. Single immutable1200-s/1000-input authority; no world reset, new resources, inference or unknown replay. Outcome pending; previous failures retained.

- M0.2k.2 / .2b: pair03 terminal before mutation, SUPPORTED_START_FOOTPRINT_UNAVAILABLE from its centered-fixture assumption. Native movement not run; phase2 not dispatched. Full guardian proof passes490.7032/500 ms for this sample; two releases/528.922 s retained, completed linked746/9408.894 plus previous setups/gap. Implement public full-footprint/swept-centering proof without changing route/cancel/stop criteria. Ten geometry tests0.10 s/Ruff pass; retained384-cell public evidence selects four steps/2.541177393 displacement with two support cells. Original failure remains; live corrected reference and reusable staging still unverified.

- 2026-09-20: M0.2k.2a/b receive narrow authentic verification in pair04; both public phases and journal/saved-state/cost audits pass, but the second guardian fails 508.2221/500 ms. Overall fail retained. 20 new primitives/824.829 s plus 3.899-s gap; completed linked 766/10233.723 s, prior gaps/setup separately retained. Source staging manifest and final native journal pinned in [report](docs/verification/2026-09-20-forge-reconnect.md). All Java terminal; no paid inference or authority renewal. No unchanged rerun.
- 2026-09-20: M0.2c.2 / M3.1, SPEC v0.2.57: implement durable private scorer source bindings and content-bound transaction deduplication after reproducing cross-campaign false completion. 112 focused cases pass in 1.70 s and targeted Ruff passes. Unknown/changed scope, conflicting restored receipt and unbound legacy state reject without score mutation; raw telemetry remains unscorable. Operator assertions stay unqualified. [Evidence](docs/verification/2026-09-20-scorer-scope.md). Authenticated ingress/setup/team/isolation and full G0 remain unresolved; existing monetary/isolation questions pending.
- 2026-09-20 final source-boundary check: real compiled gameplay bundle exclusion test passes (1 case, 0.26 s); only its four allowlisted files are packaged. This is package exclusion, not process/filesystem/network isolation. `git diff --check` passes with known Windows line-ending notices.
- 2026-09-20, 14:10 CDT: source checkpoint5edcf3d is pushed and draft PR2 head verified; worktree was clean. No game/worker operation remains active. M0 integration cannot be admitted with the currently failed worker/helper isolation or unqualified original-project monetary authority/OAuth exposure. Existing requests for an isolated worker/VM and authoritative prior spending/bounds remain unanswered; do not repeat paid/game trials to substitute for these inputs. The 500-ms shutdown failure also remains unresolved. This is a blocked integration checkpoint, not completion of M0 or the long-horizon goal.
- 2026-09-20 blocked-prerequisite recheck: previous goal turn made source/integration progress. Current checkout c65efa1 was clean and no Java processes remain. Pair04 independent root observer confirms an alive wait beginning509.1911 ms and first exit confirmation539.5148 ms, corroborating the actual500-ms failure. No justified code-only timing fix identified; no unchanged game/paid run. Pending isolated-worker and original monetary-authority/OAuth-bound inputs remain absent. M0 cannot be admitted on current evidence; full objective remains active.
- 2026-09-20, 14:14 CDT: third consecutive blocked-prerequisite audit. Previous turn added independent evidence corroborating the actual shutdown failure; this turn revalidated clean90707fa, no Java processes, unchanged prepared worker/operator inventory and no supplied isolation/monetary qualification. No safe admitted live integration is available. Mark the long-horizon goal blocked pending external worker and spending/exposure inputs, without reducing its objective or claiming M0 complete. No additional tests, game launch or paid dispatch.
- 2026-09-20 D11: recorded user confirmation of no outside model trials and rough subscription-usage budget intent; private operator statement retained. Updated SPEC to v0.2.58, current ledger and handoff; previous blockers/failures remain historical. No code-policy migration, model dispatch, game launch, budget reset or isolation waiver. Next implementation is explicit API-equivalent estimate accounting and a concrete minimal native capability boundary; no further request for billing proof or a supplied VM.

### 2026-09-20 — Session-transition documentation and merge preparation

- User requested synchronized documentation, PR and merge to main for a new Codex session. Updated SPEC v0.2.59, AGENTS, README, BUILD_PLAN, current ledger and handoff; added STATUS and the D11 validation-admission contract. Historical reports/progress remain retained; current directions no longer request a supplied VM or exact OAuth billing conversion, restart completed synthetic work, or prescribe already-terminal pair04. D01–D11, the original allowance, desktop pause, M0–M6 objective and M7/conditional activation conditions remain.
- Coverage: M0.1c.1c.2/M0.1c.2b.2, F03/F04/F07/F11/F16, N01/N02/N04/N06, C06/C12/C20, partial T01/T04/T06/T07/T12 and G0 items 1/6. Updated current G0/T03 evidence to include authentic craft and restart while retaining shutdown/config/isolation failures. No requirement, threshold or aggregate gate changed.
- Merge verification found four stale Java fixture failures: three lane cases omitted the newly required server baseline; the manual-grid case assumed an old immediate empty-preview rejection. Updated only those two test files to supply baseline feedback and assert the charged refresh/no-take behavior, then reject wrong output. Cancellation, exact budget, deadline, resource retention and invalid-output assertions remain. No runtime change. Full final local results: 1054 Python, 178 Node and 483 Java (469 client + 14 telemetry), zero skipped; Ruff and installed CLI help pass. Initial failed Gradle log is retained. [Verification and publication review](docs/verification/2026-09-20-session-handoff.md).
- No game/model experiment, allowance migration, budget reset, source qualification or milestone closure occurred in this handoff task. Next session: verify PR/main and private stopped/accounting state, create a fresh branch/worktree from updated main, then implement the versioned D11 estimate basis with the admission contract’s failure cases. Continue minimum native capability-boundary work and other M0 closure items without a repeated permission question.
- Publication checks: all 555 candidate source files inventoried, 1083 local Markdown links resolve, all 55 required F/N/M/T/G rows remain present, and the prior append-only progress history is unchanged. Only the pinned Gradle wrapper is binary; its digest matches build inputs. No sensitive-path or high-confidence secret-pattern candidates; heuristic review is not a complete security audit. git diff --check passes with existing CRLF notices. PR #2 is the existing checkpoint PR; finalize it instead of creating a duplicate.


### 2026-09-20 — D11 estimate accounting implementation

- Resumed from fetched PR #2 merge `542a77ac760fb305b26941085e33447f392f8ba8` on fresh branch `codex/strata-estimated-usage`; prior worktrees preserved. Long-horizon M0–M6 goal created; M7 conditions unchanged.
- Implemented `accounting.py`, authorization v2 and explicit migration, estimate dispatch bounds/valuations, synthetic wire valuation, native basis binding and <=$1 initial-stage jobs. Original $10 lineage/cap and existing accounting rows/holds persist; no fixture-to-live conversion. Coverage M0.1c.1c.2a/.2b, F03/F11/F16, N01/N02/N04/N06, C06/C12/C20, partial T01/T04/T07/T12, G0 1/6.
- Fresh private audit: 97 accounting stores, 88 model/helper stores all synthetic, no installed authority. Installed archived D04 into the existing project operator store and explicitly migrated to D11 with inventory/decision/snapshot evidence. No experimental model usage, game launch or shared-desktop input. [Report](docs/verification/2026-09-20-estimated-accounting.md).
- Initial affected checks: 114 Python pass, Ruff pass; one pinned-CLI/local HTTP/SSE estimate fixture passes (one request, 7 synthetic micro-USD equivalent, duplicate deduplication and finalized envelope). Final added-guard checks follow below. Earlier loopback, shutdown, effective-file and Mineflayer/E9E failures remain; G0 fail, G1–G5 not_run. Next: minimum native tool/helper boundary and qualified OAuth ingress, then <=$1 trial when prerequisites pass.

- Final focused checks: an added basis guard exposed one stale native-proof fixture (115 passed/1 failed); the corrected affected run passed 30 tests, then 60 final dispatch/native checks passed in 6.91 s. Ruff and whitespace checks pass. Added durable exposure-overrun quarantine: charge authoritative usage, then block new dispatch/native starts across restart. Private logs retain both the failure and correction.

### 2026-09-20 — Native restricted-tool candidate and broker identity

- M0.1c.2b.2a, F03/F04/F07, N01/N04, C06/C20, partial T04/T06/T07/G0 item 1: implemented a fixed owned-canary probe using supported tool restrictions, unchanged native Dovetail and the existing synthetic provider. Four actual CLI requests: shell absent, process/require/fetch globals absent, outside-workspace patch rejected; both canaries remain absent. Envelope settled at 56 fixture units. [Evidence and limitations](docs/verification/2026-09-20-restricted-native-tools.md).
- Accounting implementation committed at `e38a5c4`; original-authority private migration remains intact. No live inference/game launch or desktop input. Next: test native MCP caller metadata with root/helper spoof cases, then implement restricted brokerage; no source or integration gate closed.

- Implemented `NativeBrokerGrant/1`, private projected-artifact storage, strict native metadata authentication, parent revocation/expiry, own-result helper writes, executor-only fixed-worker transport and durable game no-replay. Added 28 focused tests; final version-corrected run passed in 1.10 s, full Ruff pass. Native metadata fixture passed (6 calls/84 fixture units). First broker fixture failed on version-banner mismatch and default MCP write approvals; both corrected and retained. Second actual CLI/Dovetail/helper + synthetic HTTP worker fixture passed all nine checks (6 calls/84 fixture units); inspected each distinct tool result and exactly one root worker request. No live/model budget or game state changed.
- SPEC v0.2.61 records C36 candidate activation for the demonstrated enforcement need while preserving app-server and all other conditions. F04/F07/C06/C36 and current handoff now point to actual partial evidence. No RuntimeQualification issued; live child-budget enrollment, full canaries/skill integration, OAuth exposure, actual game join and all prior G0 failures remain open.

- Final boundary source regression: 94 broker/storage/controller/checkpoint/artifact/contract tests passed in 4.83 s; full Ruff and whitespace checks passed. Existing gameplay packaging was inspected: its explicit four-file allowlist does not include the new operator broker or source. Original pre-session progress log remains byte-equivalent text before appended entries.

### 2026-09-20 — Native broker adversarial canaries

- Previous goal turn classified as progress: two implementation commits, explicit original-authority migration and actual CLI/helper/synthetic-worker evidence. Fresh Git/process inspection found the same clean branch at `33b8a69`, no Java or Python experiment processes.
- M0.1c.2b.2b, F03/F04/F07/F16, N01/N04, C06/C36, partial T04/T06/T07/G0 item 1: centralized supported native tool settings, disabled inherited project-document loading, and reject broker tool/server/approval expansion. Added owned ancestor-instruction, private-file, resource, direct-shell and loopback probes for root/helper. [Evidence](docs/verification/2026-09-20-native-broker-canaries.md).
- Actual pinned CLI/Dovetail with synthetic provider/worker: one changed-profile run, eight requests, 80 input/32 output/112 fixture units, no provider errors, finalized envelope. Scoped positive controls pass; all owned canary checks pass, both direct shell calls explicitly return unsupported, both catalogs exact. No actual OAuth use, Minecraft or desktop input. Earlier loopback failures remain tied to their original profiles.
- Strengthened captured-output validation, then re-analyzed the same raw evidence without re-execution: all eight added output checks pass. Focused broker/policy/verifier tests: 30 passed in 1.28 s; full Ruff pass. Protected bootstrap/source/config identity, budget-linked live child enrollment and clean-fork/descendant enforcement are next. Full T06/M0/G0 remain open; no qualification issued or threshold changed.


### 2026-09-20 — Native participant admission and sealed helper budgets

- M0.1c.2b.2c / M0.1c.2c.2 / M0.1c.1c.2b, F03/F04/F07/F11/F16, N01/N03/N04/N06, C06/C12/C20/C36, partial T01/T04/T06/T07/T12 and G0 items 1/6: implemented native stdout-bound identities, exact request/reservation admission, clean child context validation, nested helper envelopes, scope/depth/capacity checks, broker runtime/budget revocation and atomic terminal participant/envelope closure. [Report](docs/verification/2026-09-20-native-admission.md). Historical profile hashes remain unchanged when the new optional broker policy is absent.
- Source checks: initial test fixture had 19 usage-schema setup errors, corrected without weakening behavior. Final targeted suite 102 passed in 10.04 s; targeted Ruff and whitespace checks pass. Tests retain unknown holds/restart, reject inherited/smuggled context before child reservation, cover child/grandchild/capacity/deadline/revocation and require exact fenced inventories before closure. No full-suite or release claim.
- Actual pinned CLI/Dovetail/local synthetic services: clean helper six requests/84 fixture units, every request admitted and both envelopes closed. First full-fork negative sample failed in ephemeral native storage before child creation; retain four root calls/56 units and failure. Declared private-profile sample reaches ingress, rejects inherited child before forwarding or reservation, and closes four root calls/56 units. Three samples total 196 synthetic fixture units, zero OAuth/game use. Final deadline/quarantine tightening has focused source evidence, without an unchanged native rerun.
- Read-only original project accounting remains schema-2 with zero experimental operations; original allowance unchanged. Owned processes terminal; no Java, desktop input or evaluator launch. SPEC v0.2.62 and current handoff record partial implementation. Next: protected bootstrap/source/config and ingress credential identity, actual skill/artifact integration and helper lifecycle, then qualified OAuth/game trial. M0/G0 and all historical failures remain open.


### 2026-09-20 — Sealed native broker bootstrap

- Previous goal turn was progress: committed native participant/budget admission at `4182950` with actual CLI synthetic evidence. Fresh worktree/process inspection was clean/terminal. M0.1c.2b.2d, F03/F04/F07/F11/F16, N01/N03/N04/N06, C06/C20/C36, partial T01/T04/T06/T07/T12 and G0 items 1/6: implement dedicated software bundle, exact manifest/launch binding, Windows deny-write and ancestor-directory leases, isolated Python with origin/pinned-source loading, read-only native profile and private workspace separation. [Report](docs/verification/2026-09-20-native-bootstrap.md).
- Actual failures retained: bootstrap-01 long-path inventory failure before launch/dispatch; bootstrap-02 durable root-event ordering race, one ingress/zero forwarded; bootstrap-03 driver prematurely ended after a helper polling timeout, five settled calls/70 fixture units. Fixed extended paths, bounded independent-root-event wait and polling under the previously declared hard job bound. No action/shutdown acceptance threshold relaxed.
- Bootstrap-04 passes seven admitted/settled calls/98 fixture units, scoped root/helper operations and sealed budget closure; an independent write-open challenge while RUNNING is denied with unchanged bytes. Bootstrap-canaries-01 passes nine calls/126 units, all 14 root/helper access canaries and accounting/broker checks. Native executable/plugin pins unchanged; new sealed launch profiles explicit. All samples total 294 synthetic fixture units, zero live OAuth/model charges or Minecraft/shared input.
- Verification: 104 focused source/process/native tests pass in 20.35 s; final additional source-loader/scope/pre-reservation guards pass 14 focused tests in 0.88 s. Final copied real dependency imports pass through SealedSourceLoader in 8.125 s; retained canary seal passes offline scope/membership reacquisition (3460 files including manifest). Targeted Ruff passes. These final guards were checked without repeating the unchanged native interaction. Original project account remains schema-2/zero experimental operations with the original allowance; owned services terminal.
- SPEC v0.2.63, ledger, status and handoff distinguish integrity/capability evidence from credential/HTTP/OS/resource qualification. Next: authenticated job-bound native inference ingress and upstream credential separation using supported native transport; actual Dovetail skill/learned-artifact execution/export and full helper lifecycle; qualified OAuth exposure/receipts before the <=$1 trial. M0 incomplete, G0 fail, G1–G5 not_run; retain all previous loopback/shutdown/effective-file/Mineflayer/scorer/provenance/recovery gaps.

### 2026-09-20 — Authenticated native inference ingress

- Previous checkpoint `02d1392` sealed the native broker bootstrap; current work implements M0.1c.2b.2e without restarting the completed synthetic accounting matrix. F03/F04/F07/F11/F16, N01/N03/N04/N06, C06/C12/C20/C36, partial T01/T04/T06/T07/T12 and G0 items 1/6: job/profile/authority-bound random native transport capability, exact request-digest registration, persistent revocation and checks before helper-envelope/dispatch reservation. [Report](docs/verification/2026-09-20-native-ingress.md).
- Source verification: 99 affected tests passed in 15.32 s; three additional cross-job/body/helper-envelope negatives bring the ingress file to 27 passing tests in 1.45 s, without production changes or another native run. Targeted Ruff passes. Unsupported auth/config aliases, bad/duplicate headers, wrong routes/hosts, job expiry/revocation/profile drift, digest rebinding and restart/no-refund behavior are covered.
- Actual pinned CLI/Dovetail sealed local-synthetic fixture `native-ingress-01`: seven root/helper calls authenticate/admit/settle to 98 synthetic fixture units; all 18 checks pass, seven owned unauthorized HTTP clients rejected before capture/reservation, no ingress secret in context/tool feedback/native output/journal, budgets finalized without envelope double counting. No OAuth credentials or real model charge. Native duration 35.433 s is not a shutdown-threshold result. Owned services terminal; no Minecraft/shared input.
- Read-only original accounting remains schema 2, one migration and zero experimental operations; no allowance reset. SPEC v0.2.64 and handoff preserve all gates and failures. Next implement supported upstream OAuth credential separation/transport, actual Dovetail skill/artifact integration and full helper lifecycle; live qualification still precedes the authorized <=$1 trial within the original $10. M0 remains incomplete, G0 fail, G1–G5 not_run.

### 2026-09-20 — Native OAuth transport candidate

- Previous turn made concrete progress at `a8b4e58`. Fresh state: worktree clean, origin/main still merged `542a77ac760fb305b26941085e33447f392f8ba8`, owned prior services terminal. M0.1c.2b.2f, F03/F04/F07/F11/F16, N01/N03/N04/N06, C06/C12/C20/C36, partial T01/T04/T06/T07/T12 and G0 items 1/6: private native OAuth header capture and request binding, bounded observed native header allowlist, fixed verified HTTPS destinations, no redirect/retry, literal split-reflection filtering and expiring individual private qualification artifacts. Shared existing receipt/valuation implementation; the original synthetic adapter remains prohibited from live use. [Report](docs/verification/2026-09-20-native-oauth-transport.md).
- Executed checks: 106 affected tests pass in 11.77 s. Final OAuth suite, including protocol/media-header controls and production-only evidence/expiry guards, passes 19 in 5.96 s; targeted Ruff passes. No full-suite/gate claim. Fixed TLS construction is tested without opening a socket. Missing/truncated usage, reflection, redirects and timeouts retain holds and do not retry.
- Actual pinned CLI/Dovetail, fabricated private login cache and owned synthetic services: oauth-01 passes initial credential-path checks with six calls/84 fixture units, revealing native headers requiring preservation. Changed oauth-02 passes seven calls/98 units and all 21 checks, including independent upstream equality for preserved header values, root/helper credential supply, context/journal secret absence, seven unauthenticated-client rejections and finalized budgets. Total 182 synthetic units; no real OAuth/model charge. Final private-proof and media-negotiation guards were added afterward and verified locally; no later native execution is claimed.
- Original authorization remains schema 2, one migration, zero experimental operations, $10 total and <=$1 first-trial ceiling. No real credential copy/login/refresh, Minecraft or shared input; all owned services terminal. SPEC v0.2.65 and handoff retain M0 incomplete, G0 fail, G1–G5 not_run and historical failures. Next: production inference gateway/lifetime and qualification wiring, actual Dovetail skill/artifact integration and full helper lifecycle, then real TLS/account/receipt/exposure/game qualification before the staged trial.


### 2026-09-20 — M0 native gateway and actual restricted skill reads

- Continued from `ab43880`; user explicitly called for focus on M0. Implement M0.1c.2b.2g/.2h and advance .1c.1c.2b, F03/F04/F07/F09/F11/F16, N01/N03/N04/N06, C06/C12/C18/C20/C36, partial T01/T04/T06/T07/T12 and G0 items 1/6. [Report](docs/verification/2026-09-20-native-gateway.md). The operator gateway now connects authenticated ingress, exact participant/request admission, finite reservations, OAuth transport and receipt accounting. Shutdown revokes/cancels before releasing the listener; confirmed native termination and exact fenced request inventory precede envelope closure. Unknown usage remains reserved; no replay or fresh allowance.
- Found and fixed the restricted-profile skill read gap: native Dovetail discovery existed but shell-based body reads were unavailable. Pin all eight unchanged bodies against installed/sealed bytes, project immutable per-participant broker paths and supply sanitized native routing/capability instructions. Supporting-file/script/learned-activation/export and complete helper lifecycle requirements remain open.
- Verification: 58 focused gateway/OAuth/transport tests pass in 17.08 s; 102 affected native/ingress/admission/dispatch tests pass in 8.22 s; final 16 skill/gateway checks pass in 8.57 s. Targeted Ruff passes. Initial nine gateway cases passed but five teardown paths failed due to an uninitialized participant table; bind-time initialization fixed that failure before the passing runs.
- Actual pinned CLI/Dovetail with fabricated OAuth cache and synthetic provider/worker: `native-gateway-01` passes 22 checks and six calls; changed `native-skills-broker-01` passes 24 checks and six calls, including exact skill text in real root/helper tool outputs. Each totals 42 microUSD of API-equivalent estimates on synthetic token counts, no experimental usage or actual charge. Both jobs and participant envelopes finalize; all owned services stop. No Minecraft/evaluator/shared input.
- Original private account remains schema 2, one migration and zero experimental operations, with original $10 and <=$1 initial ceiling preserved. SPEC v0.2.66 and handoff record the next concrete M0 work: bounded live conformance admission must acquire account/TLS/receipt evidence without assuming it already exists, then measured native/game/private integration. Full-limit concurrent helper/root holds exceed the first-trial cap; preserve that cap and implement an explicit measured stage/helper lifecycle rather than inventing a smaller bound. M0 incomplete, G0 fail, G1–G5 not_run; all prior failures and conditional extensions remain.

### 2026-09-20 — First authentic OAuth receipt trial; unknown usage retained

- Continue from `ccaf711` directly on M0.1c.1c.2b.1/.2 and M0.1c.2b.2; F03/F04/F07/F09/F11/F16, N01/N03/N04/N06, C06/C12/C18/C20/C36, partial T01/T04/T06/T07/T12 and G0 items 1/6. [Report](docs/verification/2026-09-20-native-oauth-conformance.md). Implement one-call conformance admission with explicit pre-dispatch safeguards, no invented receipt prerequisite, no helper/game grant, original authority and fixed durable no-replay job.
- Actual source-matched native synthetic preflight: nine requests, 38 checks pass, 63 microUSD estimates on synthetic counts. Actual OAuth trial: one request, unsupported response media, no authoritative usage, native exit 1 in 12.973 s. Gateway closes; budget closure rejects METERING_UNKNOWN. One root envelope plus one request hold 755400 microUSD once; zero valuations, original 10000000 cap/one migration unchanged. No replay, refund or actual-charge claim. Authenticated metadata GET succeeds but is not an inference receipt.
- Fix loss of safe HTTP status/media diagnostics, retain bounded credential-filtered rejected bodies privately without forwarding/settlement, and make failed operator results exit nonzero. The original trial's upstream media/status/body remain unknown; local 403 is not upstream evidence. Initial diagnostic test assertions expected an exception instead of the existing UNSETTLED no-forward result; corrected, no production gate change.
- Implement supported native startup catalog snapshot and bootstrap pinning. Actual metadata-only CLI checks load the unchanged selected model. Preserve sample01's early assertion race; sample02 fences before reporting zero inference/model-catalog requests and one denied featured-plugin GET. Source/integrity checks: 23 pass/0.83 s. Final conformance/OAuth/transport/gateway checks: 88 pass/29.27 s; targeted Ruff passes. No unchanged broad native accounting matrix or live retry.
- Fetch confirms origin/main remains PR2 merge 542a77ac760fb305b26941085e33447f392f8ba8; main checkout clean, work on existing fresh implementation branch. Original accounting rechecked read-only; owned services terminal, no Minecraft/evaluator/shared input. SPEC v0.2.67/status/admission/handoff now record blocked model admission, not zero current experiment use. M0 incomplete, G0 fail, G1–G5 not_run; retain all original failed samples and M0–M6/M7 scope. Next advance independent M0 private scorer authority, shutdown/provenance and recovery; do not replay the unresolved first receipt or relax uncertainty gating.

### 2026-09-20 — Private authenticated telemetry source for G0 item 5

- Previous turn was concrete progress at `14b3b9a`; source clean and owned services terminal at continuation. Original accounting was read-only rechecked: one UNSETTLED request, aggregate hold 755400 microUSD, no new inference. Continue independent M0.2c.3 under the unchanged full M0–M6 objective, with M7 conditional.
- Implement per-boot private key/challenge issuance, instance/campaign/epoch fingerprint, exclusive durable boot claim, HMAC-SHA256 chained exact GameEvent bytes and bounded private verification. Telemetry candidate 0.3.3/configuration 3 preserves unsigned historical profiles separately. Encoded bytes consume existing quotas; missing/forged/replayed/foreign records cannot produce a successful inspection. No automatic key/grant renewal and no raw event becomes scorable. [Report](docs/verification/2026-09-20-authenticated-telemetry.md).
- Actual cross-language failure retained: signature checks succeeded but Gson omitted a required explicit null. The production writer now serializes nulls; Java regression and Java-to-Python fixture pass. Final focused Python suite 136 pass/3.72 s with actual Java opt-in and zero skips; The first corrected Gradle telemetry build succeeds in 20 s with 19 XML tests; final cross-worktree key-location and server/client-profile guards pass 24 focused Python tests (2.09 s) and the rebuilt Java suite has 20 XML tests, zero failures/errors/skips. Targeted Ruff passes. Synthetic operator CLI issuance, actual JVM production spool and private CLI inspection verify three records/20 synthetic ticks; score eligibility remains false. No Minecraft or evaluator experiment/scientific sample, model call or shared input.
- SPEC v0.2.68, runbooks, status and handoff retain the full process/key isolation, actual server source, setup/team facts, parity, scorer controls, online ingestion and complete recovery requirements. Next qualify the changed telemetry module on an authentic dedicated reference with exact launch/artifact identity, then bind setup/team/recipe/resource evidence and controls. M0 incomplete, G0 fail, G1–G5 not_run; all prior shutdown/file/loopback/Mineflayer failures and the unresolved OAuth hold remain.

- Final package exclusion check initially rejected BUILD_REQUIRED in the fresh worktree. Cached locked npm dependencies and the TypeScript build were restored, then the gameplay package check passed (1 test, 0.27 s). No raw evaluator/key material enters the four-file gameplay package; runtime isolation is still separate. Final targeted Ruff and whitespace checks pass.


### 2026-09-20 — Authentic signed Forge telemetry reference

- M0.2c.3a narrow reference passes from committed ec15bbd with module 0.3.3/config 3. A distinct protected headless E9E clone changes only the declared telemetry/port/private scope; all 18,215 recorded original source files remain byte-identical. No setup mutation, client, model, shared input or scientific campaign. [Report and audit pins](docs/verification/2026-09-20-authenticated-telemetry.md#authentic-dedicated-reference).
- Actual bounded server run: 156.203 s (surrounding reference 156.859 s), 13 signed records, 188 final/186 sampled ticks over 9.2608555 s, no avatar exposure, six exact expert-recipe assertions pass, clean stream termination and zero remaining Java processes. Private CLI inspection and deterministic reinspection pass. Derived altered/duplicate/missing-stop/foreign-authority controls reject with their expected codes. The actual writer also refuses the consumed authentic grant in a plain JVM; no second Minecraft boot or evidence mutation.
- This is authentic telemetry authentication, not scorer eligibility, a 500-ms guardian test, complete clean-save proof, process isolation, pack parity or full recovery. Retain original shutdown/loopback/five-file/Mineflayer failures and the unresolved $0.7554 OAuth hold. Next M0.2c.3b binds authenticated setup/team/resource provenance and scorer controls; do not repeat the unchanged stream trial. M0 in_progress, G0 fail, G1–G5 not_run; full M0–M6 and conditional M7 remain.

### 2026-09-20 — Private fixture seal and authenticated craft reference join

- Previous goal turn made concrete progress at ec15bbd/655e262: actual signed Forge reference passed narrowly; working tree was clean and no Java game process remained. Continue M0.2c.3b with no model/game dispatch and the full unchanged objective.
- Implement `craft_reference.py`, private setup plan/archive, actual file/hash/completeness checks, finite copy capacity, setup-bound `TelemetrySpoolAuthority/2`, one-use prelaunch reservation and immutable complete-stream import receipts. Preserve raw witnesses/failed candidates without scorer writes. Archive corruption, source/roster/recipe/window mismatches, changed imports, partial publication and reused grants fail closed. Private CLI output cannot overwrite existing evidence or enter the game/seal tree. [Verification](docs/verification/2026-09-20-craft-reference-seal.md).
- Focused Python: initial 47 pass; later affected six-suite run 133 pass/8.97 s with actual Java enabled, zero skipped. Final 35 reference tests pass/4.30 s after output safeguards. Pinned telemetry Gradle build/test/classpath succeeds in 16 s, 20 XML tests, no failures/errors/skips. Targeted Ruff passes. Compiled gameplay package exclusion passes (1/0.26 s). Six actual private CLI/JVM commands produce one synthetic resource candidate, identical replay and used-grant denial; final CLI report remains byte-identical. This is fabricated save/event data, no Minecraft/model/scientific trial.
- SPEC v0.2.69 and handoff keep scoring eligibility, setup mechanics and launch ownership explicitly false. Next .3b.2 binds the owned launcher to sealed inputs; .3b.3 proves native setup/admin/mode/team facts and joint controls. Retain the original $0.7554 unresolved estimated-usage hold, all shutdown/five-file/loopback/Mineflayer failures, M0–M6 and conditional M7/extensions. M0 in_progress, G0 fail, G1–G5 not_run.
- Final archive-path guards pass six focused checks (29 intentionally deselected, 1.42 s), including the actual JVM writer. Targeted Ruff and whitespace checks pass; 895 changed-document local links resolve. Private source/test manifests and byte-identical final report remain outside public source. No broad suite or unchanged authentic game/model trial repeated.

### 2026-09-20 — Owned sealed reference launch and actual native identity

- Continue M0.2c.3b.2 from committed 1e82ccb, preserving the existing source changes and active full M0–M6 goal. Implement `reference_launch.py`, durable one-use dispatch states, exact reviewed official bootstrap/configuration admission, immutable Windows file leases, native `LaunchIdentity`/`ServerStarted/5` in telemetry 0.3.4, retained Job-handle identity and bound complete-stream imports. Source coverage: F04/F09/F10/F13/F16, N01/N02/N04/N06/N08, C12/C18/C24, partial T01/T06/T07/T10/T13 and G0 item 5. [Evidence and limits](docs/verification/2026-09-20-reference-launch.md).
- Focused checks: 104 affected Python tests pass/19.63 s; three later bootstrap admission negatives pass/0.60 s. Gradle produces 22 passing XML tests and candidate JAR; actual JVM positive/fault fixtures exercise production signing and process observations without Minecraft. Package exclusion passes 1/0.36 s; targeted Ruff/whitespace pass. Preserve initial hang/early-exit classification test failures; lifecycle requirements were not weakened and uncertain attempts remain unreplayed.
- One changed-profile actual CLI/Forge reference uses a fresh protected private clone, complete 104-file world seal, 1,540 immutable software files, reviewed 2–5 GiB headless official serverstarter and telemetry 0.3.4. Native PID/start/executable/world/module/online/port bind to retained owned-process handles. Normal stop, all six Job members signaled, 13 signed records, 209 final/207 sampled ticks, 10.3133128 sampled seconds; launcher 216.437 s, surrounding CLI 221.235 s. No client/model/setup command/shared input. All 18,226 original source files and immutable launch bytes rehash unchanged. Nineteen independent audit checks pass, complete import replays without a new event, relaunch rejects and no Java remains.
- Mark only the named .3b.2a launch-binding reference `verified`; .3b.2 remains `in_progress`. Add explicit .3b.2b for concurrent mutable-world/config writer exclusion. Next .3b.3 implements native setup/admin/mode/team facts and authentic scoring controls; no resource candidate receives credit. SPEC v0.2.70, status, runbook and handoff preserve private data, all original failures and full required/conditional scope.
- Read-only durable-accounting recheck: original schema-2 $10 cap, one migration, one UNSETTLED request, zero valuations and 755400 microUSD held once, uncertainty blocks model admission. No model request, reset, refund or blind replay. Retain failed 500-ms samples, five effective-file failures, loopback failures and Mineflayer/E9E incompatibility. M0 in_progress, G0 fail, G1–G5 not_run; M7/extensions remain conditional.
- Final targeted Ruff/whitespace checks pass and 898 changed-document local links resolve. Private JUnit XML, both initial classification failures, final focused-test output, exact source/artifact manifests and the successful authentic terminal audit remain outside source. Process recheck finds no remaining Java/Python fixture/server. No broad suite or unchanged live trial repeated.

### 2026-09-20 — Native setup/admin/mode/team observations and versioned point controls

- Previous goal turn made concrete M0 progress at 236dd2b; verify the clean branch and no remaining game process, then continue .3b.3 with the full unchanged goal. Implement server-thread native setup snapshots, fixed exact-artifact KubeJS/FTB reads, startup and paired craft points, strict scope/adjacency/counter validation, and private reference-plan v2 with complete expected-native-team mapping. No world/team setter, script evaluation, raw command argument or gameplay route is added. Coverage: F04/F09/F10/F13/F16, N01/N02/N04/N06/N08, C12/C18/C24, partial T01/T06/T07/T10/T13 and G0 item 5. [Report](docs/verification/2026-09-20-native-setup.md).
- Inspect actual installed JAR interfaces/bytecode before calling them. Exclude the state-creating FTB `TeamManager.getId()` and use the nonmutating UUID team lookup. Unsupported dependencies, missing mode/team, wrong rank/member/roster, admin/creative/command exposure and changed observations cannot produce a v2 resource candidate. Native point agreement never grants setup continuity or scoring authority. Old seals/streams remain independently readable with no retroactive upgrade.
- Correct the stale version-5 craft parser allowlist and add a signed resource regression. Correct stale `mods.toml` 0.3.2 metadata by stamping the project version; candidate 0.3.5's built metadata is verified. Retain the earlier metadata discrepancy and source artifacts; no authentic version-5 craft claim is manufactured. Keep client diagnostic 0.3.2 identity and its five effective-file failures separate.
- Focused affected Python run: 156 pass, one rejected-roster test expected the wrong exception wrapper; final native suite after correction/additional controls passes 29/4.79 s, actual Java signer included. Preserve earlier resource-sequence and negative-fixture tick-order failures in the development record; explicit additional end-point validation preserves all resource/scope checks. Gradle compile/test/classpath/JAR succeeds in 27 s, 25 XML tests pass. Targeted Ruff/whitespace pass; compiled gameplay-package exclusion passes 1/0.30 s. Synthetic point/team data is not authentic gameplay evidence.
- One changed-module actual CLI/Forge reference uses a fresh clone, 104-file world seal and 1,540 immutable software pins. Signed startup observes loaded expert mode with zero script errors, survival/normal/nonhardcore settings, world commands/command blocks/RCON disabled, no operators or observed command attempts, and the FTB manager on the same native server. Independent audit passes 27 checks against sealed NBT/properties/ops and owned process identity. All six members stop normally; 14 records, 208 final/206 sampled ticks, 10.2690427 sampled seconds; launcher 194.687 s, outer CLI 199.000 s. All 18,225 original source files and immutable launch files remain unchanged. Import replay adds no event; relaunch denies; no Java remains. No client/model/setup command/shared input was used.
- .3b.3a remains `implemented_unverified` because actual actor/team/rank/craft points are untested. Next .3b.3b prepares that sealed v2 client trajectory and required joint controls; .3b.2b, complete setup/mutation history, instrumentation parity, isolation and all original failures stay open. SPEC v0.2.71, status/runbooks/handoff retain the original $0.7554 hold and no replay/refund. M0 in_progress, G0 fail, G1–G5 not_run; required M0–M6 and conditional M7/extensions remain intact.
- Final targeted Ruff/whitespace checks pass; 909 changed-document local links resolve. Read-only accounting confirms the original 10000000-microUSD cap, 755400 aggregate hold, one migration, zero valuations and continuing uncertainty. No model allowance/receipt changes. Process check finds no remaining Java/Python fixture or server. Private audit/source/artifact pins and test outputs stay outside source; no unchanged live trial repeated.

### 2026-09-20 — Bounded participant coordination for the sealed M0 client craft

- Continue M0.2c.3b.3b from 2e3873f. Implement `reference_participant.py` and versioned `PrivateReferenceLaunch/2` in the owned launcher: register one external operator participant, full finite window within the existing server ceiling, native-bound durable readiness, atomic non-replacing publication, exact bounded terminal-report retention/leases and single stop after terminal receipt or timeout. Version 1 retains its 60-second headless policy. The 600-second server, 120-second maximum graceful stop and 500-ms client guardian thresholds are unchanged. [Source/JVM evidence](docs/verification/2026-09-20-reference-participant.md); F04/F09/F10/F13/F16, N01/N02/N04/N06/N08, C12/C18/C24, partial T01/T06/T07/T10/T13 and G0 item 5.
- Initial participant/launcher checks pass 40/20.07 s; final participant/import checks with added premature/full-exposure/hardlink cases pass 58/15.03 s. These overlap and are not 98 independent cases. Actual Windows/JVM fixtures prove owned server binding/termination, completed/missing/foreign/failed receipts, denied uncertain imports/replays and normal cleanup on terminal coordination faults. Report corruption/quota/deadline/write-denial and pre-dispatch path/version/exposure controls pass. Four initial Ruff fixture-shadow annotations were corrected; final Ruff/whitespace pass. Gameplay-package exclusion passes 1/0.32 s. No Java remains.
- Read the actual stopped-world prerequisites without launching Minecraft: survival player state, four furnaces, zero andesite/polished andesite; the existing FTB player-team/owner record supplies expected-team registration input only. Next prepare a fresh declared ingredient setup, clean-stop seal and ordinary API craft with the new coordination. Keep the existing bounded non-input-desktop client/worker ownership and its real guardian verdict; submit client terminal report before awaiting server stop. No previous inventory, instance, consumed grant or failed trajectory was reset.
- .3b.3b is `in_progress`; .3b.3b.1 is `implemented_unverified` pending authentic participant integration. Coordination reports explicitly keep participant execution and scoring false. Native craft/team controls, concurrent mutable ownership, full mutation history, parity and isolation remain open. SPEC v0.2.72/status/handoff/runbook retain M0 in_progress, G0 fail, G1–G5 not_run, required M0–M6 and conditional M7/extensions.
- Read-only accounting confirms original 10000000-microUSD cap, 755400 aggregate hold, one migration, zero valuations and uncertainty. No model/game/shared-input dispatch, allowance change, settlement, refund or replay. Preserve all original 500-ms/five-file/loopback/Mineflayer failures. Private test/prerequisite/accounting artifacts remain outside public source and gameplay access.


### 2026-09-20 — Failed authentic sealed client reference and strict preregistration

- Continue M0.2c.3b.3b/.1 from d9aa6b1 and implement .3b.3b.2. Coverage: F04/F09/F10/F13/F16, N01/N02/N04/N06/N08, C12/C18/C24, partial T01/T06/T07/T10/T13 and G0 item 5. [Authentic failure, correction and verification](docs/verification/2026-09-20-reference-client-binding.md).
- A fresh declared fixture setup stops normally in 161.328 s; 13 checks verify exact eight saved inputs, unchanged player/team bytes, no client/craft and all members terminal. Original 18,225 source files unchanged. Seal the complete 105-file stopped world and 1,540 software pins. Setup intervention remains separate from gameplay.
- Actual private client reference reaches native-bound readiness, then fails GAME_BODY_MISMATCH before worker/action admission because the preparation copied a body digest from an older endpoint. Stale descriptive labels remain preserved too. Failed completion makes dispatch UNCERTAIN; server stops normally, all six members and both outer Jobs terminal. Client 244.14 s including cleanup, server 454.891 s, paired 459.625 s; 242 signed records / 4,900 sampled server ticks / avatar 725 ticks at last sample. No primitive/craft or guardian timing sample; inventory unchanged and eight inputs retained. Twenty independent failure-audit checks pass; failed import and replay remain denied, no scoring.
- Implement strict operator client binding/CLI; production E9E v2 requires it before reservation, preserves binding digest/bytes and rechecks pins under held handles. Expected body is computed from declared endpoint/actor, not adopted from a response. Scope/team/module/fixture/finite exposure and unknown-field failures covered. 70 affected source/JVM checks pass in 22.66 s; after held-pin recheck, final 27 binding cases pass in 1.32 s (overlapping). Package exclusion 1/0.33 s, final Ruff/whitespace pass. Actual retrospective CLI consistency is not corrected live integration.
- Read-only accounting preserves original 10,000,000-microUSD allowance and 755,400 aggregate uncertain hold. No model call, settlement/refund/reset or shared-desktop input. Local frozen Python environment installed for the existing credential preparer; source/lockfile unchanged by installation. Raw/private credentials/evidence remain outside public/gameplay scope.
- SPEC v0.2.73 and handoff/runbook retain all old shutdown/five-file/loopback/Mineflayer failures. Next fresh lineage from current stopped state with clean binding, explicit finite startup exposure and actual craft/team controls; no consumed-grant reuse or inventory rollback. .3b.3b in_progress, .1/.2 implemented_unverified. Mutable ownership, full history/parity/isolation/scoring remain open. M0 in_progress, G0 fail, G1–G5 not_run; all M0–M6 and conditional M7/extensions preserved.


### 2026-09-20 — Real CLI boundary correction and abrupt corrected-body reference

- Previous goal turn made progress at d894901. Continue M0.2c.3b.3b/.1/.2; add .3 as the next concrete lifecycle correction. F04/F09/F10/F13/F16, N01/N02/N04/N06/N08, C12/C18/C24, partial T01/T06/T07/T10/T13 and G0 item 5. [Report](docs/verification/2026-09-20-native-craft-reference.md).
- Reproduce the real module CLI's model-class boundary defect with a subprocess that cannot dispatch; serialize the validated plan at both client-validator boundaries. Initial regression fails; final 28 client-binding checks pass in 2.62 s. Targeted Ruff/whitespace pass. Preparation failures (oversized inline inventory; flat credential-cache checker on nested game tree) retained; no threshold/ACL relaxation. Superseded seals have zero reservations and no game/model dispatch.
- Actual corrected profile uses registered 380-s participant/365-s client/90-s worker/15-s terminal reserve, unchanged server 600-s/graceful 120-s/guardian 500-ms limits. Server readiness 196.781 s; actual native body matches. Client fenced readiness 265.641 s, first-frame request leaves 99.331 s, below full worker + 10-s margin. No worker/database/epoch/action/craft or guardian timing sample. The outer Fault code is missing, so an inventory race remains a hypothesis; do not invent a terminal client cause.
- Outer run forces both trees down at 466.375 s, with zero active Job counts but incomplete held-signal/log-drain evidence and absent inner terminal reports. Fresh process observation confirms no Java/owned outer PID; temporary args retired. Append durable UNCERTAIN recovery while preserving last dispatch and consumed grant. Retain 263 authenticated prefix records through tick 5312; complete import rejects missing clean stop. Copy final bytes as explicitly unclean; inventory/eight inputs remain, no checkpoint claim. All 18,227 parent files and implementation pins unchanged during trial.
- Final abrupt-stop audit passes 15 checks preserving uncertainty. Original 14/15 audit expected the consumed-grant code but observed earlier existing-path denial; preserve it and independently prove consumed-grant preflight rejection. Prepared successful-craft audit never executed. No score, actual craft/team points, full cost join or guardian pass.
- Original 10,000,000-microUSD allowance and 755,400 uncertain hold unchanged; no model call/reset/refund/replay or shared input action. Next implement/test typed bounded outer failure/abort/report cleanup and adequate finite startup exposure before another game. Preserve unclean instance and use no blind restart. M0 in_progress, G0 fail, G1–G5 not_run; all prior failures, M0–M6 scope and conditional M7/extensions remain.


### 2026-09-20 — Typed private aborts and independent owned-client cleanup

- Continue M0 from 9c57852; user asks why M0 is not advancing. D11 and native broker source/synthetic work remain delivered, while one unresolved OAuth receipt still blocks model admission. Advance independent M0 scorer/recovery dependencies; no M1 expansion or repeated native accounting matrix.
- Implement M0.2c.3b.3b.3a in `reference_abort.py` and launcher v3: bounded scope/challenge-bound non-replacing control, sanitized original fault codes, sticky invalid/valid aborts, no new readiness, finite cleanup and uncertainty despite completed receipts/normal server stop. Independent guard fences creation/commands and stops only retained owned client/worker objects; stalled stop cannot claim confirmed close. [Report](docs/verification/2026-09-20-reference-abort.md).
- Initial abort run: 13 passes/5 missing shared-fixture setup errors, fixed; first complete suite 22 passes/12.78 s. Added combined owned-child/JVM and late-receipt abort cases: 97 affected Python/Windows/JVM checks pass/40.17 s. Actual module CLI v2/v3 and compiled package exclusion: 3 passes/2.09 s, overlapping. Targeted Ruff passes after import/fixture-shadow corrections. No Minecraft, model or desktop input; synthetic fixtures cannot qualify an authentic client or guardian.
- Read-only durable check preserves schema 2, one migration, original 10,000,000-microUSD cap and 755,400 uncertain aggregate exposure. No refund/reset/replay. No Java or previous-reference port listeners remain. Original abrupt trial still has an unknown outer Fault cause, missing inner reports, unclean bytes and consumed grant.
- Coverage F04/F09/F10/F13/F16, N01/N02/N04/N06/N08, C12/C18/C24, partial T01/T06/T07/T10/T13 and G0 item 5. SPEC v0.2.74 declares the private abort profile without changing deadlines, gameplay capabilities or acceptance. Next .3b.3b.3b integrates durable outer pair monitoring/client-driver guards, hard fallback and terminal reconciliation, with owned-process faults before another changed authentic profile. Actual craft/team controls, mutable ownership, history/parity/isolation and score admission stay open. M0 in_progress, G0 fail, G1–G5 not_run; prior failures and all required/conditional scope retained.

### 2026-09-21 — Durable outer M0 pair and guarded private-driver candidate

- Prior turn made progress at 510606e. Continue M0.2c.3b.3b.3b with `reference_pair.py`/CLI and private one-use `reference_pairs` state. Hold declared source/driver/configuration pins, hash parsed bytes, require exact durable native-bound readiness and full client exposure, retain typed failures before abort, and enforce independent Job deadlines even while the monitor blocks. Preserve exact terminal reports and never fabricate a missing receipt. `craft_reference.py` now rejects nonterminal/uncertain outer pairs. [Evidence](docs/verification/2026-09-20-reference-pair.md).
- Initial pair tests: 3 failures/7 passes in 16.72 s, retained with raw result files. Fix premature outer cleanup before descendant signaling and a watchdog firing on an already empty client tree. The injected early fault's missing member history remains failed; the cooperative positive fixture now exposes its fully running child before injection. Revised 10 pass/16.82 s; expanded 17 pass/40.44 s; final six affected suites 151 pass/78.01 s. Actual module CLI completes the synthetic pair; abrupt coordinator exit retains CLIENT_DISPATCHING, one consumed grant, no manufactured result, denied import/replay.
- Copy the existing private Forge driver/helpers into a new protected candidate, preserving all originals. Guard desktop/worker creation, waits, native calls and public CLI admission; close after independent guard completion and force failure on abort. Four files parse; actual candidate public-call denial reaches neither worker nor subprocess. The candidate has not launched Minecraft. Future sealed preparation must provide explicit paths/identity/pins and sufficient complete startup/worker/terminal exposure.
- No Minecraft, model experiment or shared-desktop input in this change. Coverage F04/F09/F10/F13/F16, N01/N02/N03/N04/N05/N06/N08, C12/C18/C24, partial T01/T06/T07/T10/T13 and G0 item 5. SPEC v0.2.75 preserves all server/client/guardian thresholds. Next authentic changed reference remains unqualified; mutable writer exclusion, craft/team controls, full history/parity/isolation, scoring and complete recovery remain open. M0 in_progress, G0 fail, G1–G5 not_run; all prior failures and required/conditional scope retained.
- Final interruption review also preserves KeyboardInterrupt type/code before cleanup: 2 targeted checks pass/3.37 s (overlap with the affected suite). Compiled gameplay package exclusion passes 1/0.28 s; targeted Ruff/whitespace pass. Read-only durable accounting at 2026-09-21 05:01 UTC retains the original schema-2 authority, one migration, 10,000,000-microUSD cap and 755,400 uncertain exposure. No Java or prior-reference listener remains.

### 2026-09-21 — Authentic native craft points; retain uncertain outer inventory

- Continue M0.2c.3b.3a/.3b/.3b.3b from 538242b. Fresh registered pair-v1/launch-v3 reference, sealed clean-source lineage, guarded separate-desktop API driver and declared 400-second participant window admit the complete worker. One authentic expert furnace consumes five andesite plus three polished andesite; signed native actor/team/mode and independent saved resources agree. All 74 primitives reconcile, unknown requests empty, 280 authenticated complete records/5,545 sampled server ticks; no model calls or shared-desktop input. [Report](docs/verification/2026-09-21-native-craft-points.md).
- Retain overall failure: first outer client-monitor Fault is PROCESS_MEMBER_INVENTORY_UNAVAILABLE; API subcase absent. Client already completed; abort cannot become a pass. Server stops normally; client/server outer 112/11 and inner server 6 retained handles all signal, Jobs empty, no force. Audit fails 2/29 (paired lifecycle, sealed candidate admission); import rejects CRAFT_PAIR_UNQUALIFIED. New 487.6584-ms guardian sample passes only its own case; all prior 500-ms failures remain. Derived negative point controls are not authentic negative trajectories.
- Implement bounded ProcessInventoryObservation/1 in processes.py and durable pair/launcher retention before abort/cleanup. Preserve existing codes, fixed handle quota, ownership, no-replay and deadline rules; no retries or weakened history. Seven stage cases distinguish API failure from successful-call predicates, capture last error before close can overwrite it, and exclude paths/arguments/PIDs. SPEC v0.2.76 records the private diagnostic contract without changing gameplay capability.
- Verification: initial 27 pass/1 test-expectation failure in 9.32 s; early abort correctly retains a reservation, so correct only the expected denial code. Affected process/guard/pair/launcher/abort suites: 109 pass/17 missing explicit client-JVM fixture skips in 71.16 s. Configured pinned pure-JVM guard/package follow-up: 37 pass/23.60 s, including all 17 skips and 19 overlapping prior passes; eight JUnit-format warnings retained. Ruff/whitespace pass. One finite owned Python churn case: 48 child launches, 122 observations, 101/101 signaled handles, 3.109 s, failure not reproduced. No unchanged Minecraft retry.
- Preserve private live-01 bundle, 75 dispatch-source copies, original source's unchanged 18,227 files, prior unclean copy and every consumed grant. Private accounting remains original 10,000,000-microUSD cap/755,400 uncertain hold, no refund/reset/new spend. Coverage F04/F09/F10/F13/F16, N01/N02/N03/N04/N05/N06/N08, C12/C18/C24, partial T01/T03/T06/T07/T10/T12/T13, G0 items 3–6. Next resolve the named inventory fault with diagnostics/finite owned cases and advance independent mutable ownership/scorer/provenance/recovery. M0 in_progress, G0 fail, G1–G5 not_run; five effective-file failures, loopback failures, Mineflayer/E9E incompatibility and all required/conditional scope retained.
- Final read-only authority check at 2026-09-21 05:42 UTC retains schema 2, one migration, the original 10,000,000-microUSD cap and 755,400 uncertain aggregate hold. No Java or old reference-port listener remains. Local link check passes 943 targets; all 283 existing milestone-row IDs and every earlier append-only progress entry are preserved.
