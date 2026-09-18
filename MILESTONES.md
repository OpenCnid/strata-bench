# Strata implementation milestones and coverage ledger

Updated: 2026-09-18. Authority: [SPEC.md](SPEC.md) v0.2.0; maintenance rules: [AGENTS.md](AGENTS.md).

**Operator-only. Never expose this ledger or its linked private evidence to gameplay agents or their helpers.**

## Current position

- Delivered: specification, standing instructions and ledger, updated for D01 (Mineflayer first / structured actions), D02 (direct Codex CLI; MCP optional), and D03 (Strata / public strata-bench repository).
- Implementation: **not started**. No installed/launch-tested game, paid agent job, compatibility result, soak, capacity certificate, or benchmark result is recorded.
- Active work: Strata naming and public repository publication completed at [OpenCnid/strata-bench](https://github.com/OpenCnid/strata-bench); implementation remains not started.
- Next implementation action, when requested: M0.1–M0.3 (below): pin a Node/TypeScript Mineflayer worker and scoped local CLI, prove bounded vanilla actions, then immediately test the exact E9E Forge/registry/recipe/machine surface. G0 requires modded evidence; vanilla-only success is partial.
- Execution prerequisites unresolved: exact official acquisition/vanilla path, E9E distribution/JVM lock, account and hardware availability, pinned headless Codex capabilities, and any required paid-inference budget/experiment authorization. These do not block independent documentation or authorized local implementation.
- Most recent verification: 2026-09-18 document checks passed for 13 JSON examples/top-level type shapes, all original IDs, local links, balanced fences and the revised CLI/backend defaults. No T-suite or G-gate has passed.

Statuses: `not_started`, `in_progress`, `implemented_unverified`, `verified`, `blocked`, `deferred`. Test/gate results: `not_run`, `pass`, `fail`, `blocked`. A dash in implementation/evidence means none yet, not not-applicable. Owner roles are defined in SPEC section 3; assign an actual owner when work starts.

## Milestone plan

| ID | Owner | Dependencies | Required deliverables / exit | Status | Implementation / evidence | Next action |
|---|---|---|---|---|---|---|
| M0 | GI; AR owns host seam | Execution prerequisites | Mineflayer/host vanilla slice followed immediately by exact E9E API/recipe/machine conformance, cancel/reconnect, private milestone and complete charges; G0 | not_started | — | Execute M0.1–M0.3; no game or inference run authorized by this doc change. |
| M1 | PL | M0 | Typed Python/TypeScript/conditional Java contracts, scoped local CLI, durable controller, capability isolation; full keybinding skill/extension T05; G1 | not_started | — | Consolidate validated seams and implement M1.1. |
| M2 | QA | M1 | Durable single-agent play, input fencing/watchdog, complete snapshots, recovery, budgets/clocks and operational report; G2 | not_started | — | Implement fault semantics, then staged 1/8/24-hour validation. |
| M3 | RS | M1 | Private fixtures/scorers/probes, artifact projections, ablations, pairing/analysis and canary tests; T10/T11/T13 | not_started | — | Define public development fixtures and scorer controls. |
| M4 | PL | M2 | Team communication, simultaneous capacity, atomic N-body admission, distinct accounts/routing; G3 | not_started | — | Test N=1/2/4; actual N=2 required, N=4 disposition explicit. |
| M5 | RS | M3, M4 | Development cost/power pilot, locked preregistration, confirmatory execution, report/export and operations handbook; G4 | not_started | — | Freeze protocol only after pilot and integrity evidence. |
| M6 | GI; RS owns calibration | M5 | Calibrated tasks/graduation/anchors, retention/transfer and separately conformant E6E/E2E modules; G5 | deferred | — | Required later release work; preserve all compatibility gates. |
| M7 | PL | Stable M5 workload and demonstrated need | Distributed workers/storage/scheduling and optional dashboard, with unchanged integrity/conformance guarantees | deferred | — | Activate individual extensions only on measured need or user request. |

Dependencies govern milestone closure. Shared foundation work can advance before an entire prerequisite milestone closes when its own inputs are available; this does not waive gates. M1's G1 includes probe-isolation evidence also developed in M3: start that minimal evidence in M1, then extend it in M3, avoiding a circular dependency. MVP is M0–M5; later mandatory work and conditional extensions remain separate.

### D01 child work items

| ID | Owner | Scope / affected coverage | Status | Evidence / next action |
|---|---|---|---|---|
| M0.1 | GI/AR | Pin Mineflayer/Node/TypeScript/plugins; worker/GameBackend/CLI; Dovetail structured delivery. F01/F03/F06/F16, C03/C06/C09, T01/T03/T04 | not_started | No implementation; inspect exact dependency/API seams. |
| M0.2 | GI/QA | Vanilla move/mine/craft/container state, filtering, local cancellation, stale/ambiguous actions and reconnect. F06/F09/N02/N03, C09/C15/C18, T03/T07 | not_started | No runtime evidence; bounded standalone conformance first. |
| M0.3 | GI | Exact E9E handshake/channels/registries, expert recipe, container and operating machine. F01/F05/F06, C04/C09, T02/T03/T10, G0 | not_started | A join cannot pass; record gaps and separately qualify any fallback backend. |
| M1.1 | GI | Required keybinding skill plus capable Forge settings extension: repair/effect/persistence tests; stock Mineflayer rejects unsupported operations. F06, C10/C11, T05, G1 | not_started | Retained MVP feature; no fabricated binding support. |

## Requirement coverage

All rows start without implementation/evidence. Status refers to complete requirement coverage, not the first related prototype. Split child work as needed and replace the dash with real file/component and evidence links.

| ID | Required behavior | Owner | Milestones | Tests | Status | Implementation / evidence / gap |
|---|---|---|---|---|---|---|
| F01 | Authentic vanilla/E9E servers; Mineflayer first, exact modded API conformance | GI | M0, M2 | T02, T03 | not_started | — |
| F02 | Positive configurable N and whole-team simultaneous admission | PL | M1, M4 | T01, T09 | not_started | — |
| F03 | Native selected Dovetail for each body; helpers/self-play accounted | AR | M0, M1 | T04, T12 | not_started | — |
| F04 | Enforced hidden objective/criteria/holdout isolation | SI | M0, M1, M3 | T06 | not_started | — |
| F05 | Official CurseForge/Forge acquisition, provenance and blocked states | GI | M0 | T02 | not_started | — |
| F06 | Bounded structured state/actions and capability-gated verified keybinding skill | GI | M0, M1, M2 | T03, T05 | not_started | — |
| F07 | Information, communication, learned-artifact and context policies | AR | M1, M3, M4 | T04, T06, T11 | not_started | — |
| F08 | Persistent campaigns separated from matched one-way probes | RS | M1, M3, M5 | T11 | not_started | — |
| F09 | Durable lifecycle, leases, fenced input, consistent recovery | PL | M1, M2 | T07, T08 | not_started | — |
| F10 | Authoritative scorer and positive/negative controls | RS | M0, M3 | T10, T13 | not_started | — |
| F11 | All nested usage and team/agent/evaluation budget enforcement | PL | M0, M1, M2, M4 | T12 | not_started | — |
| F12 | Fixed-system cohorts, model-generation/drift quarantine | RS | M1, M5 | T14 | not_started | — |
| F13 | Reproducible evidence, uncertainty, censoring and interventions | RS | M2, M3, M5 | T13, T15 | not_started | — |
| F14 | Calibrated graduation/retention and frozen historical anchors | RS | M6 | T16 | deferred | Required in M6 before promotion claims. |
| F15 | Each later pack/version separately conformant; fresh-world transfer | GI | M6 | T17 | deferred | Required E6E/E2E work in M6. |
| F16 | Typed lifecycle/acquisition/capability/game/settings/telemetry/communication/artifact/evaluation contracts | PL | M1 | T01 | not_started | — |
| N01 | Fail closed on unsupported schema/capability/lock/isolation/accounting | PL | M0, M1 | T01, T04, T06 | not_started | — |
| N02 | One executor; deduplicated dispatch; ambiguous-ack resync | GI | M1, M2 | T07 | not_started | — |
| N03 | Real-time clocks, ticks, latency and performance accounting | QA | M1, M2, M4 | T08, T09, T12 | not_started | — |
| N04 | Secrets/private records/initial artifacts protected from agent code | SI | M1 | T06 | not_started | — |
| N05 | Safe exhaustion handling; costs retained; gameplay failures preserved | QA | M2 | T07, T08, T12 | not_started | — |
| N06 | Pinned dependencies/protocols and report replay | PL | M1, M2, M5 | T01, T13 | not_started | — |
| N07 | Measured operating envelope before confirmation | QA | M2, M4 | T08, T09 | not_started | — |
| N08 | Durable bounded private storage; no silent evidence deletion | PL | M1, M2 | T07, T13 | not_started | — |

## Feature coverage beyond requirement titles

This inventory preserves important prose obligations. Full details and edge cases remain in the cited SPEC sections. Each row must acquire implementation/evidence links or child items as work proceeds; a broad row cannot close while an applicable child behavior is absent.

| ID | Feature scope | SPEC | Milestone / requirements | Status | Implementation / evidence / next detail |
|---|---|---|---|---|---|
| C01 | Definitions of system/cohort/lineage/campaign/episode/probe; body/helper/replica separation | 1, 13 | M1, M3; F02/F03/F08 | not_started | — |
| C02 | Prior-art/source provenance, factual/proposed/unverified labels; bounded compatibility claims | 2, 7, 18 | M0, M5; F01/F05/N06 | not_started | Source research exists; runtime claims remain unverified. |
| C03 | Package layout, stack/toolchain locks, deployment profiles; single-controller SQLite/journal/CAS | 4–5 | M1; F16/N06/N08 | not_started | — |
| C04 | Official acquisition, role inventories, exact bootstrap/client/server/JVM bytes, expert recipe/quest assertions | 7 | M0; F01/F05 | not_started | — |
| C05 | Supported authentication, distinct simultaneous player identities, clean templates/materialization and missing-artifact states | 7, 15 | M0, M4; F02/F05/N04 | not_started | — |
| C06 | Native Codex CLI loop/plugin load, JSONL/command-bridge negotiation, exec-job conformance, explicit invocation and host capability failures | 6 | M0, M1; F03/F16/N01 | not_started | — |
| C07 | Immutable initial skills, learned revisions, executable macro restrictions, notes/handoffs/compaction/resume and artifact quotas | 6, 9, 13 | M1, M3; F03/F07/F08 | not_started | — |
| C08 | Helper/self-play clean context AND file/tool isolation, depth/concurrency, ancestry, returned evidence and parent budget | 6, 15 | M0, M1; F03/F04/F11 | not_started | — |
| C09 | Mineflayer structured state/actions, observed-map filtering, pinned local navigation and exact modded API suite; optional pixel/input parity separately | 8 | M0, M1; F01/F06 | not_started | — |
| C10 | Capability-gated keybinding discover/diagnose/tested-pool allocation, contexts/backend/Unicode distinctions, protected controls, transactional patch and rollback | 8–10 | M1.1; F06/N02 | not_started | — |
| C11 | Actual intended/competing key effects, persistence/restart, cross-client isolation; charged in-play repairs and matched probe keymaps | 8, 13 | M1.1, M2, M3; F06/F08/N03 | not_started | — |
| C12 | Worker/game/runtime/evaluator process and host boundaries, credential brokerage, filesystem/network/capability enforcement and leak attempts | 4–6, 10, 13 | M1; F04/N04 | not_started | — |
| C13 | Pinned allowed docs, player-accessible recipe/quest projections, sanitized goals/control cards, declared messages and no implicit shared memory | 4, 6, 8, 10, 13 | M1, M4; F04/F07 | not_started | — |
| C14 | Campaign/worker/agent states, ownership, deadlines, durable revisions, sequence/epoch fencing and health leases | 10–11 | M1, M2; F09/F16/N01 | not_started | — |
| C15 | Action deduplication, ambiguous emission recovery, cancel/stop-all watchdog, hung-client termination and late-tool rejection | 8, 10–12 | M2; F09/N02/N05 | not_started | — |
| C16 | Complete clean-stop world/player/quest/team/machine/client/runtime/skill snapshots, atomic commit, same-boundary restore | 11–12 | M2; F09/N06/N08 | not_started | — |
| C17 | Crash/rate-limit/credential/disk/resource/stall incidents, interventions; no gameplay undo, cost refund or future-knowledge retention | 12 | M2; F09/N05 | not_started | — |
| C18 | Active/elapsed/server/avatar clocks, checkpoint timing/drain overrun, state/action/model lag, event-loop lag/TPS/MSPT and conditional FPS | 11–12, 15 | M2, M4; N03/N07 | not_started | — |
| C19 | Durable raw evidence, delivered structured state/signals and optional images/video, retention/tombstones, private export/redaction and report replay | 5, 12 | M2, M5; F13/N06/N08 | not_started | — |
| C20 | Team/agent budget reservations/settlement/reconciliation, descendant/retry/practice/probe charges and unknown metering | 9–10, 15 | M1, M2; F11/N01 | not_started | — |
| C21 | Measured backend hardware/accounts/provider capacity (displays only when used), N=1/2/4, atomic team queue/reject, no time-sharing/substitution | 11, 15–16 | M4; F02/N07 | not_started | — |
| C22 | Persistent natural play, one-way disposable probes, matched fresh contexts/world/equipment/keymap, sealed instances and no tuning feedback | 13 | M1, M3; F08 | not_started | — |
| C23 | Full/frozen-persistence/frozen-skills/no-self-play policies; exact reset surfaces and budget-dependent experimental arms | 13.2 | M3, M5; F07/F08/F11 | not_started | Implement policies; never claim effects of unrun arms. |
| C24 | Server-verified milestones, alternate strategies, sustained automation and positive/negative controls | 13, 16 | M0, M3; F10 | not_started | — |
| C25 | AG/absolute success/AULC/AUG, independent paired samples, clustering, CI/multiplicity, censoring/attrition bounds and power plan | 13 | M3, M5; F13 | not_started | — |
| C26 | Retention and fresh-world target-pack transfer, source cost, fixed-system versus new-generation cohorts and drift quarantine | 13 | M3, M5, M6; F08/F12/F14/F15 | not_started | — |
| C27 | Fixed aggregate versus fixed-per-agent N comparisons; summed ticks/reserved body time, repeated-call costs and concurrency reporting | 13, 15 | M3, M4; F02/F11/N03 | not_started | — |
| C28 | Task DAG/calibration, promotion/retention thresholds, repeated-look control, independent confirmation, ceiling/prerequisite outcomes and historical anchors | 14 | M6; F14 | deferred | Required in M6; not replaced by pack-number ordering. |
| C29 | E6E and E2E version-specific Java/loader/input/GUI/quest/save modules and conformance | 7, 14, 16 | M6; F15 | deferred | Required later support, each exact profile separately gated. |
| C30 | Operator CLI/services, typed errors, status/stop/abort, handbook, static reports, versioned reproducible release | 10, 17 | M1, M2, M5; F13/F16 | not_started | — |
| C31 | Optional pixel/OS, expanded semantic assistance and open-web conditions with distinct affordance/information/score identities | 4, 8, 13 | Later explicit condition; F06/F07/F13 | deferred | D01 makes structured control primary; these expanded/alternative conditions remain optional. |
| C32 | Budgeted practice worlds and optional mechanic-intervention diagnostics, reachability and no holdout contamination | 6, 13, 15 | Later explicit condition; F03/F08/F11 | deferred | Optional; practice quota remains zero by default. |
| C33 | Additional packs, provider extensions and broader platform/input modules | 5, 7, 17 | M6 / later scope; F05/F15 | deferred | Preserve boundaries; add each target by explicit lock and conformance. |
| C34 | Remote workers/mTLS, distributed scheduling, PostgreSQL/object storage and interactive dashboard | 4–5, 17 | M7; F02/F13/F16/N04/N08 | deferred | Needs-driven and optional; retain individual activation decisions. |
| C35 | Full test suite, staged gates, risk ownership, requirement traceability and no unjustified completion claims | 3, 16–19 | M0–M7; all requirements | not_started | This ledger initializes tracking; execution evidence still absent. |
| C36 | Optional MCP game facade and app-server lifecycle adapter, sharing the same scoped contracts and independent conformance | 4, 6, 10 | Later demonstrated portability/lifecycle need; F03/F16/N01 | deferred | D02 selects direct CLI/IPC first; neither optional adapter is an MVP prerequisite. |

### Schema inventory

SPEC section 9 defines these typed contracts. All are `not_started` in implementation and `not_run` for T01 generated-schema conformance; the specification's illustrative JSON parsing is documentation evidence only. Own them under M1, with domain owners as in SPEC.

| Record | Owner | Required integration | Status | Implementation / evidence |
|---|---|---|---|---|
| PackLock | GI | Candidate/sealed invariants, provenance and installed inventory | not_started | — |
| CampaignConfig | PL | Roster, profiles, budgets, schedule, admission and recovery | not_started | — |
| AgentConfig | AR | Runtime/model/plugin/skills/credentials references and helper policy | not_started | — |
| Observation | GI | Scoped structured state/signals, observation age/revisions/capability digest; optional image/keymap | not_started | — |
| ActionBatch | GI | Lease/epoch/sequence/preconditions, one typed bounded action, conditional raw events | not_started | — |
| ActionAck | GI | Accepted/executing/completed/failed/cancelled/unknown, partial effects and resync | not_started | — |
| GameEvent | GI | Private authoritative payloads, event identity and validation | not_started | — |
| SkillRevision | AR | Provenance, ancestry, activation and forbidden probe imports | not_started | — |
| KeybindingPatch | GI | Stable IDs/owner/backend/contexts/modifiers/CAS/restart evidence | not_started | — |
| CheckpointManifest | PL | Consistent full set including backend cache/state and conditional keymap; exposure/cursors | not_started | — |
| BudgetLedger | PL | Reserves/settles/adjustments, actual calls and unknown metering | not_started | — |
| EvaluationProtocol | RS | Private sealed definitions, budgets, samples and analysis | not_started | — |
| EvaluationResult | RS | Private paired results, evidence, censoring and validity | not_started | — |

### API inventory

Each domain inherits SPEC section 10's authentication/authorization, version negotiation, IDs, deadlines, errors, persistence and idempotency rules. Track implementation under M1/F16, tested by T01 plus domain cases.

| Domain | Contract scope | Status | Implementation / evidence |
|---|---|---|---|
| Lifecycle | Campaign create/status/start/checkpoint/stop/abort; worker register/heartbeat/reserve/release | not_started | — |
| Pack acquisition | Resolve/acquire/verify/seal/materialize; operator/artifact waits | not_started | — |
| Capabilities | Required/optional negotiation and fail-closed profile fingerprints | not_started | — |
| Observation/actions | Observe/wait-events/act/typed wrappers/status/cancel/stop-all; conditional input; stale/ambiguous-action handling | not_started | — |
| Keybindings | List/capabilities/plan/apply/status/rollback; serialized verification | not_started | — |
| Telemetry | Private authenticated authoritative event stream and durable cursors | not_started | — |
| Communication | Scoped team send/receive, ordering, rate/size/TTL and cost | not_started | — |
| Artifacts | Authorized content storage, safe paths, quotas and skill publication | not_started | — |
| Evaluation | Private schedule/score/export, sealed access and one-way clones | not_started | — |
| Agent runtime | Inspect/start/deliver/events/interrupt/export/resume/helpers/stop | not_started | — |

## Test suites and release gates

Record each test attempt in the progress log or linked report with its exact profile, procedure, date, raw evidence and limitations. Partial execution does not pass the aggregate suite. Keep different N/pack/backend/model profiles separate; a successful synthetic test does not pass its real-game equivalent.

| Test | Owner | Scope (full acceptance is SPEC section 16) | Result | Profile / evidence / outstanding work |
|---|---|---|---|---|
| T01 | PL | Strict contracts, schemas, config, auth, paths and negative cases | not_run | — |
| T02 | GI | Official clean provisioning, locked inventory, expert mode and blocked acquisition | not_run | — |
| T03 | GI | Structured vanilla and exact Forge/registry/recipe/machine actions; optional input parity separately | not_run | — |
| T04 | AR | Native host/plugin/structured tools/helpers/accounting/interruption/resume; optional images | not_run | — |
| T05 | GI | Stock-Mineflayer rejection plus full real keybinding-extension effects/restart/rollback/isolation cases | not_run | — |
| T06 | SI | Private/cross-agent/helper/filesystem/process/network/tool/holdout leaks | not_run | — |
| T07 | QA | Ack/lease/process/server/controller/disk/credential/snapshot faults and recovery | not_run | — |
| T08 | QA | Ordered 1-hour, 8-hour, 24-hour operating-envelope soaks | not_run | — |
| T09 | PL | N=1/2/4 simultaneous capacity, whole-team rejection, shared and independent topology | not_run | — |
| T10 | RS | Reachability, scorer positive/negative controls and alternative strategies | not_run | — |
| T11 | RS | Matched clones, probe disposal/non-feedback, exact ablation state | not_run | — |
| T12 | PL | All nested usage, dedup/retries/reservations and reconciled clocks/caps | not_run | — |
| T13 | RS | Deterministic report/accounting reconstruction, retention and safe export | not_run | — |
| T14 | RS | Model/reroute/runtime drift, quarantine and unavailable identity | not_run | — |
| T15 | RS | Preregistered confirmatory pilot, all assignments/attrition and honest inference | not_run | — |
| T16 | RS | Calibration/graduation/history/retention/ceiling/prerequisite decisions | not_run | Deferred to M6; no promotion claims. |
| T17 | GI | Each later pack/backend/quest/save module separately conformant | not_run | Deferred to M6; no legacy support claims. |

| Gate | Required milestone/evidence | Result | Profile / evidence / remaining condition |
|---|---|---|---|
| G0 | M0; all six SPEC 16.1 vertical-slice items together | not_run | No real integration evidence. |
| G1 | G0; complete T01/T04/T05/T06/T10/T11 including settings extension | not_run | No contract/integrity execution evidence. |
| G2 | G1; T07/T08/T12/T13 at N=1 | not_run | No durable single-agent/24-hour proof. |
| G3 | G2; T09, actual N=2, explicit N=4 disposition, N=2 soak/security | not_run | No simultaneous capacity certificate. |
| G4 | G3; development cost/power pilot, T14, locked protocol and T15 | not_run | No research MVP or scientific result. |
| G5 | G4; T16/T17 per new target | not_run | Later packs and graduation unverified. |

## Blockers, open decisions, and change history

These are unresolved prerequisites, not proof that future implementation cannot proceed. Convert a specific active work item to `blocked` only when its progress actually depends on the missing input. Keep unrelated work moving.

| ID | Owner | Affected work | Open condition | Default / next resolving action | Evidence or decision reference |
|---|---|---|---|---|---|
| B01 | GI | M0, F01/F05, T02 | Official vanilla workflow and exact E9E distribution/JVM/expert mode | Inspect official workflow and actual distributed artifacts under authorization; seal only validated profiles. | SPEC 7, risks R02/R03/R06; no execution evidence. |
| B02 | AR | M0, F03/N01, T04 | Exact CLI/plugin/helper/command/accounting/resume capability | Pin CLI/event schema and Dovetail; test direct command bridge and required capabilities, version any validated shim. | SPEC 6, R04/R15; no host conformance evidence. |
| B03 | GI | M0/M1.1, F01/F06, T03/T05 | Mineflayer exact Forge/registry/recipe/machine compatibility; separate keybinding-capable extension | Immediate compact modded API suite; qualify any fallback by its own backend identity; retain actual T05 repair evidence. | SPEC 8/16, D01, R01/R07/R10; no runtime evidence. |
| B04 | PL | M0/M4/M5, F02/F11 | Accounts, hardware, provider access, installation/experiment authorization and spending ceilings | Confirm actual resources and existing authorization at execution time; preserve whole-team admission. | SPEC 15; this task authorizes documentation only. |
| B05 | SI | M1, F04/N04, T06 | Credential/process/filesystem/network separation and leak resistance | Implement actual boundaries and adversarial canary cases. | SPEC 4.1/13.5, R05/R11/R17. |
| B06 | QA | M2/M4, F09/N07 | Complete pack persistence, recovery and long-run capacity envelope | Inventory all mutable state; staged faults/soaks and capacity certificates. | SPEC 12/16, R08/R09/R16. |
| B07 | RS | M3/M5/M6, F10/F12/F13/F14 | Scorer reachability, identity assurance, costs, samples and calibrated thresholds | Develop controls; pilot first, then freeze powered/qualified protocol and untouched tests. | SPEC 13–14, R12/R13/R14. |
| B08 | PL | M7, C31–C34 | Whether conditional extensions are needed | Retain all extensions visibly; record need and scope before activating each. | SPEC 4/17; no activation decision. |

Baseline history: the initial ledger recorded no authorized scope changes. **D01, 2026-09-18:** the user explicitly requested Mineflayer for controlling characters and as the first backend. SPEC v0.2.0 supersedes pixel-first A01, updates F01/F06 and related contracts/gates, and moves required real keybinding-extension evidence from G0 to G1. Original requirement/test/milestone IDs remain. Modded play, CurseForge + Forge, Dovetail, N, adaptation controls and the hotkey skill remain required. Optional physical-input profiles remain visible; no runtime capability or gate was passed.

**D02, 2026-09-18:** user steering questioned the need for MCP and proposed direct Codex CLI integration. The design defaults to native command calls through `mcgame`/scoped IPC and a persistent bot worker. CLI exec JSONL is the initial host adapter; MCP/app-server remain optional. A04, M0.1, C06/C09/C12, F03/F06/F16 and T01/T04/T06 are affected. Read-only CLI help/official docs support feasibility; real integration remains not run.

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
