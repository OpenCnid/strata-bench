# M1.6e disposable native artifact binding

D20 continuation of M1.6a-d. M1.6e is implemented_unverified for actual native
admission/projection; M1.6 remains in_progress and G1 not_run. Affected:
F03/F07/F08/F11/F16, N01/N04/N06/N08, C06/C12/C20/C22/C23/C24/C36,
T01/T04/T06/T11/T12. No unrelated M2-M7 work or spending authority changes.

## Delivered source boundary

[ProbeNativeBindings](../../evaluator/src/strata_evaluator/native_probe_bindings.py)
reconstructs registered pair/views, verifies their actual trees and atomically
binds both complete rosters to fresh native identities and evaluation accounts.
It refuses incomplete rosters, campaign/source identity reuse, reused jobs or
operations, account misclassification, missing explicit helper supply, and
overlapping workspaces/profiles. The source campaign and stopped job remain
unchanged. Registration consumes identities once but reserves no inference costs
and grants no runtime permission.

The [native reader](../../src/mcbench/native_probe_binding.py) uses only committed
operator records and approved artifact refs. It imports no evaluator package and
returns separate approved role maps without private pair/provenance fields.
It rechecks the complete sibling registration, prepared-source state/digests,
artifact visibility/hashes, native/account scope, ordinary goal and explicit
helper set. Exact catalog preflight rejects missing/altered entries, duplicate
entries/roots, extra blocks and unrelated host skills outside the active overlay.
This preflight is not evidence that the actual native loader emits that catalog.

`NativeLaunch` now has a distinct `probe` purpose and optional root/helper
binding refs. The schema refuses campaign activation, recovery, persistent
sessions, old epochs, separate helper processes and whole-job accounting under
that identity. Its profile hash binds the private artifact identity. Absent
fields preserve old source/profile hashes. The artifact schema is exported only
to the operator domain.

**Every probe launch still refuses**, including simulation fixture launches,
before creating a job, cost reservation or process. Prepared artifacts do not
establish held world/resource custody. Existing native account/admission/broker
guards still reject evaluation in campaign/conformance paths, and do not yet
admit the new probe purpose. No runtime qualification or probe wire-tool profile
is issued. No broker grant or actual native artifact projection is claimed.

## Verification

**140 distinct focused cases pass:**43 binding cases and97 schema/native/account
regressions. The first binding run retains11 passes/26 failures from a nested CAS
transaction. The corrected implementation publishes inert private CAS content
before the atomic registry transaction. A later run retains40 passes/one failed
test expectation: changed bytes correctly raise CORRUPT_EVIDENCE, whereas the
test expected MIXED_SNAPSHOT. The corrected assertion and two additional catalog
cases pass3/3. No gate or product behavior was weakened for that correction.
Both original logs, JUnit, test directories and source versions are retained.

```text
PYTHONPATH=src;tools;evaluator/src
.venv/Scripts/python.exe tools/export_schemas.py
.venv/Scripts/python.exe -m pytest tests/test_native_probe_bindings.py -q -x
.venv/Scripts/python.exe -m pytest tests/test_native_probe_bindings.py -q -k "changed_artifact_tree or duplicate_root or missing_skill"
.venv/Scripts/python.exe -m pytest tests/test_records.py tests/test_native.py tests/test_native_account_policy.py -q
```

Coverage includes full/no-self-play/frozen controls and t=0, complete rosters,
fresh evaluation leaves, scope/prompt changes, failed or changed prepared
sources, sibling deletion, catalog substitutions/duplicates/omissions, private
content without registration, late journal failure with complete rollback,
reused aggregate accounts, and refusal before native process or reservation.
Ruff and whitespace checks pass. The binding cases use synthetic checkpoint,
game and native records. Native lifecycle regressions include synthetic Python
process supervision; no Codex, Minecraft or provider run occurs.

Read-only reconstruction passes72/72 checks across six prepared cases plus3/3
common checks. It independently joins both-arm registration, source digests,
scope, exact role/physical inventories, catalogs, helper exclusions, distinct
locations, empty profiles, unused evaluation leaves, only the stopped seed job,
unchanged database, private schema domain and unchanged evidence seal.
Separate stopped reconstruction also revalidates one authentic native source
and two committed exports, with both old bundle seals and databases unchanged.

Producer `2026-09-25-m1-probe-native-binding-01`:10,642 files,67,732,343 bytes;
seal `2a39bbd281e7e1e1524289ca7080df1d97948887dc2c46c56a4581046966ecf7`.
Audit `2026-09-25-m1-probe-native-binding-audit-01`:3 files,9,114 bytes;
seal `1360e882129d0314d130140d330f91f10b9b7b469cc3312980f61c9d577c5f38`.
All40 durable authority tables remain unchanged; $4.887796/$10 exposure,
every hold and consumed decision remain. No matching Strata-owned runtime
remains, no paid inference or new allowance is used, and no RuntimeQualification
is issued. D18/D19 remain M0-only.

## Remaining acceptance

Implement the held pair coordinator and complete per-arm all-N resource/budget
admission, immutable bootstrap inventory, exact probe wire catalog and scoped
broker projection. Bind actual world/body/keymap/tools/cache equivalence before
either arm starts; enforce registered frozen/no-self-play controls throughout
local adaptation. Preserve six runtime proofs, separate evaluation accounting,
fresh root/helper sessions, stopped evidence custody and one-way destruction.
Actual native loading/projection, N>1 positive preparation and disposal remain
unverified. Full T05, scorer controls and combined isolation remain required.
