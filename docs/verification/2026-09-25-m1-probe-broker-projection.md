# M1.6g probe bootstrap and broker artifact projection

D20 continuation. Affected F03/F04/F07/F08/F16, N01/N04/N06/N08,
C06/C12/C20/C22/C23/C24/C36 and T01/T04/T06/T11. M1.6g is implemented_unverified for actual native integration.
M1.6 remains in_progress; G1 is not_run.

The native consumer now compares the exact prepared workspace, including
catalog bodies and empty-directory inventory, with its committed binding and
complete pinned bootstrap tree. Every body hash and size must match; a missing,
extra, changed or unpinned input refuses. This is preflight inventory evidence,
not ownership of process or file handles. The supervisor still needs the actual
bootstrap lease and held world/runtime custody throughout execution.

NativeAdmission checks the probe catalog before participant/envelope admission
and invokes a distinct probe projection after broker enrollment. The projector
first authenticates the exact grant/job/profile/campaign/agent/epoch/model and
explicit helper selection. It copies only approved role content into the scoped
CAS namespace, then revalidates the grant and source before one atomic file/index
commit. Inert CAS copies alone grant no artifact path. Private bindings and
provenance stay outside gameplay/helper content. Fresh namespaces cannot carry
unlisted artifacts; one-use projection records prevent later admission from
resetting mutable notes or local adaptation. Initial/docs/supplied/active files
remain immutable, and helpers do not receive root notes, handoff or drafts.

## Verification

**141 focused cases pass:**28 new bootstrap/projection cases and113 native
admission/broker/account regressions. Ruff and whitespace checks pass.

```text
PYTHONPATH=src;tools;evaluator/src
.venv/Scripts/python.exe -m pytest tests/test_native_probe_artifacts.py -q -x
.venv/Scripts/python.exe -m pytest tests/test_native_admission.py tests/test_native_broker.py tests/test_native_account_policy.py -q
```

The new suite uses complete synthetic source/checkpoint/pair/binding records,
actual prepared disk files and actual broker methods. Grants use the existing
explicit simulation-only enrollment path; no running native probe, funded
dispatch or production grant is fabricated. Five positive cases cover full,
t=0, frozen-persistence, frozen-skills and no-self-play projections. These prove
artifact selection, not full enforcement of those controls during native play.
Permitted root notes and helper results survive repeat projection; immutable
writes and helper reads of root notes refuse. Other cases cover changed catalog
or initial bytes, added files/empty directories, missing/duplicate/changed pins,
foreign/revoked grants, source changes during copy, nonfresh namespaces, atomic
file/journal failure and refusal to launch despite a completed projection.

Read-only reconstruction passes137/137 checks across five positive cases plus
3/3 common checks. It independently joins private binding bytes, exact role
inventories plus local writes, immutable bits, scoped content hashes, complete
prepared workspace/bootstrap pins, one projection event per role, explicit
simulation grants, unchanged stopped seed jobs and zero evaluation operations.
Original databases, all40 durable authority tables and producer seal remain
unchanged; no owned runtime remains. No Codex, Minecraft or provider run occurs.

The first audit reader failed when comparing an extended Windows workspace
path with an ordinary source-root path. Retain its script and failure log.
The corrected reader normalizes the source root with the existing extended-path
helper, without following new archived paths, changing producer bytes, editing
SQLite journals or rerunning any fixture. It then passes the complete audit.

Producer `2026-09-25-m1-probe-broker-projection-01`:4,544 files,43,211,547 bytes;
seal `04aa4c8a51134d39e545371bfde9a6636446be93f6408760951ffd9bf77667f8`.
Failed audit `2026-09-25-m1-probe-broker-projection-audit-01`:2 files,6,588 bytes;
seal `1ac32d88dcff281b7c73e59ca1fb2fe5227ea019d5374ec549137ef70a483528`.
Passing audit `2026-09-25-m1-probe-broker-projection-audit-02`:3 files,11,447 bytes;
seal `9b32ae216a92683809aec0f47c93516f7bc7eb8bfdbd3d1c9fb8205cf89f45cb`.
Exposure remains $4.887796/$10 with every hold and consumed decision retained.
D18/D19 remain M0-only; no paid M1 execution or allowance extension occurs.

## Remaining acceptance

NativeExec and purpose/account guards still refuse every probe launch. This
change supplies no world/runtime launch permit, measured capacity, new wire-tool
profile, RuntimeQualification or disposal proof. Connect actual live custody,
all-N readiness, frozen/no-self-play enforcement, matched live state, fresh
sessions and one-way destruction before enabling dispatch. Actual native catalog
loading and broker admission must be verified on that complete profile. Positive
N>1 preparation, remaining isolation routes, T05 and scorer controls remain open.
Unrelated M2-M7 work is unchanged.
