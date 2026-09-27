# M1.2b public record semantic parity and finite T01 closure audit

The reproduced incomplete-keybinding-commit defect is fixed. Python and the
TypeScript runtime validator now agree on the shared positive/negative cases
for KeybindingPatch, SkillRevision, ActionBatch, ActionAck and Observation.
M1.2b/M1 remain in_progress; T01/G1 remain not_run because other canonical
records and required integration cases remain open. No game/model run occurred.

## Behavior changed

[records.py](../../src/mcbench/records.py) exports portable conditional schema
rules for executed evidence, committed keybinding effects/restart evidence and
skill activation timestamps. Empty changes are invalid. Python's existing
cross-field acceptance criteria are preserved. Missing verification cannot be
turned into a committed record merely by changing the phase string.

[protocol.ts](../../backends/mineflayer/src/protocol.ts) adds the required semantic
checks after structural validation: unique changed binding IDs, strictly
increasing committed revision, physical-key representation/modifiers, real
calendar dates, action-mode consistency, ordered/balanced input events, action
bounds/selection semantics, observation clock/frame/state consistency and
receipt completion/resynchronization. These checks do not grant a capability.
Mineflayer still rejects input mode in actionSemantics; syntactically valid
high codes still need T05's separately qualified physical-key pool. Existing
motor-stage restrictions and explicit source/selection limits remain intact.

JSON Schema2020-12 does not express arbitrary comparisons between fields, so
raw schema acceptance is not semantic admission. Consumers must use the full
validator. The original incomplete-commit case now fails both the exported
schema and the full validator. Revision ordering, ID uniqueness and related
comparisons remain explicit typed runtime checks, tested against Python.

Generated public validators now include SkillRevision and KeybindingPatch.
The private [worker bundler](../../src/mcbench/worker_bundle.py) copies all six
startup schemas under its held inventory; the four game-message capability
schemas retain their separate scope. Compiled module bytes and bundle inventory
change, so historical native profiles are not promoted to this source. No
installed client/server artifact or immutable historical bundle was altered.
The gameplay CLI allowlist still excludes operator/evaluator material.

Regeneration also corrects two stale operator-only TypeScript bindings:
NativeLaunch now reflects the already-existing probe/team/no-helper fields,
and RoleInventoryInput reflects existing extra_directories. Their Python
models/schemas and authority are unchanged. Both bindings compile independently.

## Executed verification and retained failures

The [shared corpus](../../tests/fixtures/public_record_semantics.json) has140
explicit cases consumed by both languages. Tests preserve input bytes/values,
exercise valid boundary cases, and reject malformed state; they are synthetic
contract tests, not authentic keybinding effects or gameplay evidence.

- Python:297 distinct passing cases across public-record semantics, records,
  settings/control fencing, artifacts, gameplay packaging and worker bundles.
  The first expanded run has139 passes and one failed test fixture: a case named
  look-over-cap inherited SPEC's move_to action, for which10,001ms is valid.
  The retained fixture is corrected to an explicit look_at action; that case
  passes alone without rerunning unchanged cases.
- Node:full source run has306 passes, five failures and43 existing opt-in skips.
  Four failures expected invalid quest records to survive until motor admission;
  the new contract validator rejects them earlier. Updated tests require both
  the earlier SCHEMA_UNSUPPORTED and the retained direct motor rejection. The
  fifth is the same misconstructed look fixture. All five focused corrected
  cases pass:311 distinct passing cases,43 still skipped, no remaining observed
  failure. The original failure log and old fixtures/tests are retained.
- TypeScript build, reproducible compiled-schema checks, independent operator
  binding compilation, changed-file Ruff and whitespace checks pass. Shared
  input cases run on Node24.19.0 with locked Ajv8.20.0. No unchanged authentic
  suite, installation, paid inference or gameplay trial is repeated.

Commands:pytest tests/test_public_record_semantics.py tests/test_records.py;
pytest tests/test_controls.py tests/test_controls_fencing.py
 tests/test_checkpoints_artifacts.py tests/test_gameplay_package.py;
pytest tests/test_worker_bundle.py tests/test_worker_runtime.py;
npm run build; node --test dist/tests/*.test.js. Corrected cases use pytest -k
look-over-cap and Node --test-name-pattern for the five named cases. Private
logs/JUnit preserve each exact invocation/result, rather than summing reruns.

## Finite T01 acceptance map

This list follows every case in SPEC16 T01 and keeps full T04/T05/T06/T10/T11
requirements separate. Existing source locations are coverage leads, not fresh
passing evidence unless a check above exercised them.

| T01 obligation | Current evidence / implementation | Remaining closure action |
|---|---|---|
| All13 records; strict unknown fields/schema versions | Python records and TypeScript canonical schema examples; five public semantic records above | Finish semantic admission for the eight operator/evaluator records, retaining authority separation |
| Python/TypeScript round trips and negative parity | Shared140 public-record cases; generated bindings | Seven concrete remaining disagreements reproduced for PackLock, CampaignConfig, AgentConfig, CheckpointManifest, BudgetLedger, EvaluationProtocol and EvaluationResult; also cover GameEvent timestamps and visibility |
| Complete fixture/cross-record references and unresolved lock refusal | Controller admission/CAS, evaluator stores and retained source tests | Audit actual reference resolution and profile/roster consistency at each admission boundary; add missing cases without manufacturing production qualification |
| Migrations | Database0-to1 initialization and future-version refusal in storage/controller tests | Prove preserved populated state, repeat opening/rollback and actual supported schema transitions; do not assume create-if-absent is a complete migration proof |
| Conditional Java bindings | Existing game/settings/telemetry Java parsers and native profiles | Map every consumed wire record and discriminant to actual Java validation/round-trip evidence; keep absent schemas explicit |
| N=0/negative/fractional; duplicate roster | test_records invalid_team_size and roster tests; current33 record tests pass | Cross-language roster/count semantic parity remains in the next batch |
| Large N parses, queues/rejects before allocation | test_storage_controller large_team_queues_without_allocating_any_bodies; existing source | Retain prior evidence identity and reconcile the complete admission path; no N-body capacity experiment belongs here |
| Stale epoch/revision; token/audience/deadline | Controller/grant/broker/native ingress suites and prior evidence | Exact boundary-to-test mapping and any missing current-binding cases |
| Traversal/reparse | Storage/bundle/bootstrap/CAS safe-path checks;55 bundle/runtime cases pass here | Reconcile public/operator paths and actual Windows reparse evidence; this alone is not T06 isolation |
| Structured/input discriminants, nullable frame/keymap fields, action limits | New public semantic checks plus existing structural validation/motor capability checks | Extend differential coverage to RpcRequest nesting and the conditional Java path; no input capability promotion |
| Capability mismatch | Existing worker admission and actionSemantics; retained native refusals | Reconcile current identities and unsupported settings/input behavior; required native integration remains open |

Next address the seven reproduced operator/evaluator semantic disagreements
and GameEvent using the same shared-case method, with private validators kept
outside gameplay packages. Then finish reference/migration/Java mapping and
remaining RPC/auth/path cases. Do not return to another furnace trial as the
next step. This is the [agreed closure order](2026-09-27-m1-closure-path.md),
not a reduction of M1 or a new completion definition.

## Accounting and evidence custody

All40 authority tables remain unchanged at4,887,796microUSD. Operation10,15 and16
each retain their separate268,435,456-byte RESERVED telemetry hold with no actual
settlement. Zero Java processes before/after; no game/model call. D18/D19 remain
M0-only. Private source, cases and logs are retained at
2026-09-27-m1-contract-parity-01 in the operator evidence store. All historical
native failures, including operation16's unknown transfer, remain unchanged.

Final audit passes20 changed-file pins,458 unique milestone IDs,1,800 local
links,55 reproducible generated files and unchanged authority/holds. Exact
private archive49files/2,869,146bytes verifies under seal
`eb63591cb9c4e4756c3795573f1981c0c914a60ac78c90cdef3f09dfe2f8d1e2`.
This pointer follows the archived documentation snapshot. All remaining T01/G1
requirements and historical failure dispositions stay open as recorded.
