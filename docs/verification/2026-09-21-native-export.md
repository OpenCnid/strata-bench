# M0 source-bound native component export

September 21, 2026. Operator-only. M0.1c.2b.2c.3 advances partial
F03/F04/F07/F09/F11/F16, N01/N02/N04/N06/N08,
C06/C07/C08/C12/C14/C16/C17/C19/C20/C36,
T01/T04/T06/T07/T12/T13 and G0 items 1/6.
M0 remains incomplete, G0 fails, G1–G5 are not run.

## Implementation

[NativeExports](../../src/mcbench/native_export.py) implements
`native-stopped-broker-component-export/1` and private `NativeState/2`.
The export is derived from durable source state, rather than accepting arbitrary
workspace/skill blobs as a stopped broker's inventory. Require a finalized
process-sealed job, closed participants, exact request/envelope lineage, settled
receipts, terminal broker work, drained native cells and explicitly revoked
ingress. External helper jobs and unsupported ledger adjustments reject.

Match operation reserves and actual costs to account-bound ledger digests and
usage vectors; join distinct dispatch identities, reservation fingerprints,
settlement events and valuation records. Preserve ancestor allowance identities,
aggregate exposure, uncertainty, usage classes and a ledger cursor. Synthetic
fixture units remain labeled; estimate valuations retain their existing pricing
identity. This does not create an allowance, settle unknown usage, replay a
request or roll back costs. Unrelated unresolved reservations survive export;
later charges cannot be replaced by the export's historical accounting snapshot.

Capture the complete authorized broker-file inventory with content hashes,
namespace, role, immutable status and artifact category. Root artifacts and
private helper inventories remain separate. Verify bytes and path/size policy;
reject case/parent collisions, invalid immutable placement, known credential/cache
paths and missing content. These checks do not claim to detect every possible
secret in arbitrary text. Immutable projections, notes, handoffs and skill
drafts retain their distinct categories; drafts are not activated revisions.

Write private CAS components, recheck source identity, then atomically commit one
export reference. A source change during capture or after commit rejects; repeated
export/load after restart is idempotent. No native sessions, code-mode caches,
credential caches or private logs are projected into gameplay artifacts.

[NativeExec](../../src/mcbench/native.py) rejects the old arbitrary-blob export
for broker jobs. Neither a legacy state nor this component authorizes broker
resume. `NativeState/2` explicitly records `restore_authorized: false` and
`episode_retention_applied: false`. Complete game/agent checkpoint joining,
retention rules, skill activation, fresh scoped materialization and restored
runtime qualification remain required.

## Retained failure and correction

The first derived audit rejected the recorded native-interrupt-01 store with
`INGRESS_NOT_FENCED`. Its FINALIZED job already denied request admission, but
its explicit ingress revocation flag was zero. The original sealed record is
unchanged and this result remains in private native-export-01.

Finalization now writes durable ingress revocation in the same transaction as
envelope closure and FINALIZED state. Missing registration rolls back closure,
retaining exposure. Source tests verify both paths and subsequent authentication
denial. The changed finalizer has not been exercised in a new native trial.

Private native-export-02 starts from a new verified copy of the same sealed
DB/WAL/SHM and CAS. It first records the same rejection, then explicitly invokes
the existing operator revocation API on that derived copy before export. This
is recorded-evidence reconstruction with a declared migration, not a rerun or
retroactive claim that the original native trial used the new finalizer/exporter.

## Executed verification

Windows development checkout, Python 3.12.14. Final affected suite:

```powershell
$env:PYTHONPATH='src;evaluator/src'
.venv/Scripts/python.exe -m pytest -q tests/test_native_export.py tests/test_native_ingress.py tests/test_native.py tests/test_checkpoints_artifacts.py tests/test_native_cell_lifecycle.py tests/test_native_retirement.py tests/test_budget_envelopes.py --tb=short
```

**165 pass in 25.00 seconds**, including the two new atomic finalization cases.
After completeness review, the final **30 export cases pass in 8.66 seconds**;
an unregistered broker grant cannot disappear from the inventory. Focused Ruff
passes. Initial export tests found an
incorrect ledger-digest formula: the verifier omitted the account wrapper.
That implementation error was corrected against the existing ledger contract.
Negatives cover live/incomplete jobs, unknown usage, missing receipts/grants/blobs,
broken budget lineage, altered cost vectors, pending/legacy broker work, unknown
game calls, path violations, capture races, uncommitted state and denied resume.

The derived actual-history audit passes **24 checks**, retaining the original
17 settled requests, 238 synthetic fixture units, eleven terminal broker calls,
two closed participants, drained cells, four root files and two separate helper
files. Private/operator and helper references deny root access. Restart preserves
the same export and accounting; four derived state-corruption controls reject.
The pinned original native profile is
`6b9901588ad27bc2d9991cb574b4b60e1e7c070db0289bd8c54d0ed30e5e50c0`.
No model, Minecraft or shared-desktop input was dispatched for this work.

Three final review checks revalidate that same committed derived export under
the complete-grant guard, reject an injected unregistered grant and preserve
the export/accounting after removing the injected derived row. Both source
generations and the original 24-check audit are retained privately.

All **8,976 files** of sealed native-interrupt-01 were hash/size verified before
copy and after reconstruction, including its manifest digest
`0e6ae070ec0b6342721dcf61bdec42844bf66e402c2921a0dc26467e34b68336`.
Raw copies, source archives, export refs and audit scripts remain outside source.
The sealed failed native-export-01 bundle contains 74 files; manifest SHA-256
`e1f1a7a015151b8b4665aeb4c65f2d860fc72b08bef5d28ba6853f8a5a4e9634`.
Native-export-02 contains 92 files; manifest SHA-256
`23c5ed36fc8d4b34f16ef403905d7858d74e7a59666adac3fe4534bb510b36d7`.
The original authority was separately read using SQLite read-only mode: unchanged
$10 total estimated allowance, $0.7554 unresolved exposure, uncertainty true.
No reconciliation, replay or refund occurred.

Next join this stopped native component to complete checkpoint admission and
fresh scoped artifact materialization, with explicit retention and skill
activation boundaries. Preserve the original OAuth uncertainty, native
sibling/loopback failures, every failed 500-ms shutdown, five effective-file
failures, Mineflayer/E9E incompatibility, scorer controls/provenance/parity and
full recovery obligations. No aggregate gate changes.
