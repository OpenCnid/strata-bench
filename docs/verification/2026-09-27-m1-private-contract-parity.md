# M1.2b private record parity and supported schema upgrades

The seven reproduced operator/evaluator validation disagreements are fixed.
All eight private canonical records now have a shared Python/TypeScript semantic
corpus, complementing the five public records in the [preceding report](2026-09-27-m1-contract-parity.md).
The actual three supported SQLite schema transitions have preservation/refusal
evidence. M1.2b remains in_progress; complete T01 and G1 remain not_run.

## Implemented behavior

[records.py](../../src/mcbench/records.py) now exports its existing conditional
rules for sealed locks, loader versions, roster/checkpoint schedules, immutable
model identity, committed checkpoints, budget postings and evaluation outcomes.
Python acceptance criteria are unchanged. Signed budget adjustments remain valid;
unknown or censored outcomes do not become invented success/failure observations.

The [operator TypeScript validator](../../backends/mineflayer/operator/records.ts)
performs closed structural validation and the remaining cross-field comparisons:
roster size/uniqueness, increasing schedules, clock ordering, token subsets and
primary exposure membership. It checks calendar timestamps without interpreting
arbitrary GameEvent payload strings as timestamps. Dispatch rejects unknown
record names and mismatched schemas. This validates records; it neither resolves
content-addressed references nor grants execution or scoring authority.

Private code compiles into dist/operator, outside the gameplay dist/src tree.
The worker-bundle test plants private validator/schema canaries and verifies
that neither is copied. Gameplay CLI packaging retains its existing allowlist.
This is package-exclusion evidence, not complete T06 runtime isolation.

## Verification executed

The [shared private corpus](../../tests/fixtures/private_record_semantics.json)
contains 150 positive/negative cases for PackLock, CampaignConfig, AgentConfig,
CheckpointManifest, BudgetLedger, GameEvent, EvaluationProtocol and EvaluationResult.
Both languages agree on every case without changing the input. All seven original
counterexamples from the previous sealed archive now fail semantic admission.
Together with the earlier 140 public cases, every canonical record has named
local semantic coverage; this is not a claim of complete integration coverage.

[Schema-upgrade tests](../../tests/test_schema_upgrades.py) use real temporary
SQLite databases, never the operator authority database:

- Populated version 0 upgrades to 1 and survives close/reopen with exact journal
  and object rows; the next journal cursor follows the preserved cursor.
- Future version 100 is refused without changing its logical schema/data/version.
- The supported grants.generation and control_transactions.profile_id additions
  roll back all schema/data changes when SQLite denies ALTER TABLE. Retrying and
  repeatedly constructing the service preserves old rows and leaves the newly
  added authority field NULL. Unresolved legacy controls still block repair.
- A legacy grant cannot invent an input generation, and service reconstruction
  does not restore consumed quota on a fresh grant.

These tests cover the supported schema transitions, not power-loss recovery,
arbitrary historic schemas, business authorization migrations or the G2 fault suite.

Executed commands and results, retained in the private archive:

- pytest tests/test_private_record_semantics.py tests/test_records.py: 183 pass.
- pytest tests/test_storage_controller.py tests/test_checkpoints_artifacts.py
  tests/test_budget_clocks.py tests/test_budget_envelopes.py tests/test_evaluator.py
  tests/test_provisioning.py tests/test_gameplay_package.py tests/test_worker_bundle.py:
  111 pass, two existing Typer/Click deprecation warnings.
- pytest tests/test_schema_upgrades.py: five pass. Total: 299 distinct Python cases.
- npm run build; node --test dist/tests/private_record_semantics.test.js
  dist/tests/contracts.test.js: 160 pass. One subsequently added dispatch test
  passes separately after rebuilding: 161 distinct Node cases.
- All 16 private generated TypeScript bindings compile with strict/noEmit.
  All 55 generated schema/binding/compiled-validator files reproduce unchanged
  after export/generation. Changed-file Ruff passes.

There were no observed failures in these runs. No unchanged native suite was
repeated. Environment: Windows, repository virtualenv, Node 24.19.0, locked
Ajv 8.20.0; base e2e09f0. These are synthetic contract and real local storage/
packaging checks, not authentic gameplay, selected-skill or keybinding effects.

## Remaining finite T01 work

The [previous acceptance map](2026-09-27-m1-contract-parity.md#finite-t01-acceptance-map)
remains the full case list. Its private-record parity row now has the evidence
above; its migration row has the three supported schema transitions above.
Next reconcile actual cross-record/reference admission, unresolved locks and
large-N admission, then nested RPC/auth/deadline/path boundaries and the Java
records actually consumed. Reuse applicable prior evidence and add only missing
or changed checks. Complete T01 before returning to the keybinding/probe closure
deliverables in the [closure path](2026-09-27-m1-closure-path.md).

No G1 suite closes in this report. Native host/skill integration, keybinding
effects, final isolation qualification, protected scorer controls and matched
probe disposal remain required. No further furnace trial is selected.

## Authority and custody

All 40 durable authority table digests remain unchanged at 4,887,796 microUSD
exposure. D18/D19 remain M0-only; there is no M1 inference spending authorization.
No model or game call occurred. Original failures, consumed decisions and the
three independent 256 MiB telemetry reservations remain preserved.
Source, logs, shared cases and exact checks are retained in operator evidence
2026-09-27-m1-private-contract-parity-01. Final custody audit/seal is recorded below. The first custody-audit script used
len() on the binding report's integer file count and failed before custody
checks. Its source/error are retained; the corrected comparison uses the
existing count directly, without changing test evidence or acceptance.

Final custody audit passes: 23 changed-file pins, 458 preserved unique milestone
IDs, 1,812 local links, all 40 authority tables and the three prior holds/seals
unchanged, zero Java processes. The private archive verifies at 45 files /
1,930,828 bytes, seal
`aafdc12dd7e17f797fc98a1b57b8dbb430fff12afbbe3fb4f32d34f7c610a03e`.
This pointer follows the archived documentation snapshot. T01/G1 remain not_run.
