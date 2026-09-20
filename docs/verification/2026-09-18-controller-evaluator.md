# Controller and evaluator implementation evidence

Date: 2026-09-18. Operator-only. This extends the [M0 foundation](2026-09-18-m0-foundation.md);
it does not close G0, an aggregate T-suite, or any milestone.

## Implemented and exercised

Environment: the same Windows 11 host, Python 3.12.14 and Node 24.19.0 pins as the
foundation report. No Minecraft, Forge, authenticated account, inference job,
paid experiment or private holdout was used. All new execution fixtures are synthetic.

- All 13 canonical records: strict Python models, partitioned JSON Schemas and
  generated TypeScript. All 13 SPEC examples round-trip in Python and validate
  in Ajv; unknown fields and major versions fail. Semantic cases include roster,
  schedules, model assurance, seals, key representations, input balance, ledger
  subsets, checkpoint and outcome consistency.
- SQLite WAL/FULL controller: revision checks, leases and increasing epochs,
  revocation, indivisible team/resource/account reservations, all-body readiness,
  scoped method grants and bounded deadlines/quotas. Simulation databases cannot
  be reopened as live controllers. Live admission requires resolvable private
  evidence, a sealed lock and spending ceilings. No game launch is implemented here.
- Content store and transactional outbox: namespace/visibility authorization,
  quota checks before blob writes, immutable hash verification, safe path rules,
  and repeatable atomic JSONL reconstruction. Guessed private hashes fail; a public
  canary succeeds. These checks do not prove filesystem/process/network isolation.
- Budgets and clocks: hierarchical reservation/settlement, nested ancestry,
  notification deduplication, separately charged retry operations, concurrent
  reservation races, recorded overruns and unknown-cost blocking. Rollback is not
  a refund. Measured tick deltas remain separate from active/elapsed/reserved-body
  time; server-offline reasoning still counts as exposure.
- Checkpoints: complete-roster and audited path inventory checks, clean-stop
  attestation consistency, canonical digest, atomic commit and fresh-directory
  materialization. Partial/mixed/traversing snapshots fail. Recovery plans contain
  game and all agent references; confirmatory rollback fails and development
  recovery requires a newer epoch. Actual server stop/restore is unverified.
- Artifact activation and episode policies: provenance, parent comparison,
  immutable initial revisions, handoff bounds, probe-origin exclusion and exact
  retention projections. Team messages enforce membership, 4 KiB, 10/minute,
  bounded queues, per-sender order, deduplication, acknowledgment and expiry.
- Settings transaction engine and sanitized gameplay skill: tested-pool planning,
  context overlap, protected/unknown binding rejection, revision/fingerprint
  checks, effect/restart receipts, rollback and crash recovery preserving unrelated
  edits. All settings tests use an explicitly synthetic adapter. No Forge adapter
  or real keybinding support is claimed; stock Mineflayer remains unsupported.
- Separate evaluator package: registered craft/machine telemetry payloads,
  causal/source/team/mode checks, sustained operating windows, duplicate-event and
  restored-progress protection, paired lineage analysis, absolute competence,
  10,000-replicate seeded intervals, missing-assignment bounds, common-support areas,
  Holm correction and a labeled sample-planning heuristic. Clone plans and drift
  decisions exist; actual probe spawning/disposal and drift stop integration do not.
- Operator commands: validate/create-DRAFT/status/preflight and private journal
  export. Offline evaluator CLI reconstructs identical report digests; publication
  projection excludes private IDs/refs and retains the synthetic marker.

## Executed verification

```powershell
uv run --frozen python tools/export_schemas.py
npm run generate --prefix backends/mineflayer
uv run --frozen ruff check src tests tools evaluator
uv run --frozen pytest -q
npm test --prefix backends/mineflayer
uv run --frozen mcbench --help
```

Results: **107 Python tests passed; 18 Node tests passed; Python lint and TypeScript
worker compilation passed.** Typer emits two upstream Click deprecation warnings.
The command tests initially caught required options being interpreted as positional
arguments; explicit Typer option declarations corrected that failure. Review also
moved artifact quota checks before blob writes to prevent rejected requests from
accumulating disk usage; the regression test checks that no extra blob is created.

## Remaining integration and coverage

T01–T17/G0–G5 remain `not_run` in aggregate. These services are not yet wired into a
qualified process supervisor, native Dovetail job loop, official pack provisioner,
Forge settings adapter or authoritative game telemetry producer. Real body actions,
account isolation, helper escape resistance, complete persistence-path coverage,
all-call provider metering, automatic recovery and safe exhaustion need integration.
Unknown-cost reconciliation, complete retention/tombstone handling, probe execution,
full survival/power/graduation analyses and later pack modules also remain open.

## Same-task continuation: body surface and packaging

After the 107/18 core check, continued M0.2/M1.3 work:

- Added persistent public signal cursors, bounded ring/pages, single concurrent
  event wait, normal timeout with original observation age, and fixed public
  templates. The actual CLI/HTTP transport exercises `wait-events` and `recipes`.
- Inspected the pinned Mineflayer inventory/craft/place/chest implementations and
  minecraft-data 1.19.2 recipe/unlock packet schemas. Implemented player-unlocked
  recipe projection and a fixed crafting motor using normal slot operations and
  native `_syncWindow` feedback. A synthetic server fixture deliberately supplies
  false client-predicted output; only resynchronized output passes. Wrong output,
  unknown serializers/items, NBT/remainders, hidden recipe guesses, stale windows
  and interrupted continuation fail. Actual server behavior remains unverified.
- Added bounded same-named vanilla block placement and corrected furnace/table
  opening to use generic `openBlock` rather than the chest-only helper. Placement
  is compiled but has no authentic-game acceptance evidence.
- Added an allowlisted client bundle containing only CLI/errors/skill/package
  metadata. Its actual compiled client runs outside the repository without worker
  dependencies; missing grants fail. No operator/spec/evaluator content is copied.
- Pinned canonical record hashing to RFC 8785 using
  [the upstream Python implementation](https://github.com/trailofbits/rfc8785.py)
  at 0.1.4, with matching Node behavior. A cross-process test covers negative zero,
  integer-valued floats, exponent cutoffs and UTF-16 key ordering. This resolves
  an implementation detail in SPEC 9; it changes no requirement or release gate.
- Qualified identity flags remain visible in analysis without silently discarding
  valid observations. Invalidating flags are explicit analysis-plan inputs.

Latest executed results: **115 Python tests passed; 26 Node tests passed; lint,
worker compilation, and separate operator/evaluator TypeScript binding checks
passed. Both operator and evaluator wheels built successfully.** Build checks do
not establish deployment isolation. The new TypeScript code initially exposed
nullable-slot narrowing and ES-library declaration errors; those were corrected
before the passing checks. Two upstream Typer/Click deprecation warnings remain.

Final reconciliation also passed: all original requirement/feature/milestone/test/
gate IDs and 13 record rows remain; all aggregate gates remain unrun; changed
documentation links/fences and `git diff --check` passed. Wheel contents were
inspected: the operator wheel excludes evaluator code, and neither wheel includes
test fixtures or repository instruction/specification documents.

The user confirmed that official vanilla and E9E installations are unavailable.
Code work continues independently. Acquisition/terms/account setup and an actual
inference ceiling are required before authentic integration or paid execution.
