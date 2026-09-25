# M1.6m.1 — paired source validation cost

This is a bounded implementation dependency of M1.6m's registered paired
vanilla reference. It preserves the failed case06 joint-preflight deadline,
all writer/server/parent windows, source identities and cost/capacity holds.
It does not qualify full T11 or G1, native probe admission or paid inference.

## Diagnosis and change

A stopped read-only reconstruction of case06's genuine registered pair takes
3.2258 seconds under `cProfile`. `ProbeCustody._source` reconstructs the complete
native/checkpoint/pair chain twice: once to validate the source and again to
derive the role-specific views. Derive the views from this call's already
validated pair instead. There is no cache across calls. Exact stored view-plan,
view-tree, roster, binding and account checks remain.

`PairedVanillaRuntime.check` also calls the same preparation check twice in
succession. Its software check already performs full live preparation,
budget/resource/source validation. Keep that complete software check and remove
only the immediately preceding duplicate call.

The changed stopped reconstruction takes 1.6808 seconds, with identical pair
and view digests and unchanged sealed source files/database. These are individual
diagnostic measurements, not latency qualification or proof that both live server
windows now fit. Every later call revalidates current state.

The measurement uses actual production read methods over the externally sealed
case06 store, with a frozen query-only database and no creating CAS/database
constructor, custody reacquisition or dispatch. It requires the original FENCED
state and retained200 synthetic units. An initial diagnostic reader omitted the
runtime attribute and failed before returning; its script/profile/log remain
retained. Corrected before/after readers complete without changing the source.

## Verification and remaining work

Focused custody, native-view and paired-runtime verification passes63/63 in
695.59s. Its existing negatives include post-acquisition expiry, source-tree drift,
account/category/ledger changes, uncertain costs, missing envelopes and capacity
corruption. Ruff and whitespace checks pass. Documentation QA preserves all405
existing milestone IDs, adds M1.6m.1, preserves the append-only history and
unchanged SPEC, and resolves1,442 initial/1,443 final local links. All40 real authority tables remain
unchanged; no owned runtime remains after these source checks.

Use `PYTHONPATH=src;tools;evaluator/src`:

```text
.venv/Scripts/python.exe -m pytest tests/test_probe_custody.py tests/test_native_probe_views.py tests/test_probe_vanilla_runtime.py tests/test_probe_vanilla_runtime_contract.py -q --basetemp=<fresh private profile>/tests --junitxml=<fresh private profile>/focused-junit.xml
```

The private `2026-09-25-m1-pair-validation-profile-01` bundle contains the
diagnostic scripts/profiles, complete source, tests, initial diagnostic failure,
accounting and process snapshots. Its9,784 files/51,528,274 bytes are externally
sealed by SHA-256
`bd20e711f13284a1f1ad3694d9d275b3ef79ab427eef2bab1b5618789554078e`.
The original case06 seal remains unchanged.

Fresh case07 passes host/port/accounting preflight and retains the same
300s preparation,200/170s writer and two60s server windows. Its source is archived
before execution. Native verification fails in171.35s: both copier trees stop
normally with10/10 retained owned processes each, and both initial-state checks
finish, but joint admission still refuses `PROBE_WORLD_DEADLINE` before Minecraft.
The initial-state events are29.547s apart. Inner custody closes uncertain at
97.078s; outer custody closes uncertain at109.406s with
`PROBE_WORLD_CLOSE_UNCERTAIN`. These observed times do not qualify the deadlines.
The pair remains FAILED/FENCED with200 synthetic units and its whole8GiB/6GiB
capacity hold. No owned runtime remains and all40 real authority tables are
unchanged. No server/model/native gameplay agent starts. Genuine software/world
inputs remain separate from synthetic agent/protocol/capacity fixtures.

The read-only reconciliation script initially shadows Python's `inspect` module;
retain the import failure and rename the reader before inspection. The first
sealed reconstruction incorrectly expects the older M1.6j source archive to have
a newer directory-inventory sidecar. Preserve that failure; validate its actual
original file seal and captured world/compiled directory contract instead.
No archive, acceptance condition or execution changes to accommodate the reader.
Corrected sealed reconstruction passes35/35: source/result identity, genuine
world/software bytes, compiled directories, owned histories/tokens, no game
launch, failure fencing, all cost/capacity holds and unchanged real authority.

| Retained private evidence store | Files / bytes | SHA-256 seal |
|---|---|---|
| `2026-09-25-m1-paired-vanilla-07` |654 /47,250,511|`d4b66d8b0101c2c50c196f6abfb22731e4879b6ec2ed61537a97f90210e92b8c`|
| `2026-09-25-m1-paired-vanilla-07-initial-tree` |376 /240,118,253|`48f6e1dd11cc9a34c87c5cffc5ba6c0873f3644b5e11ae03287c03c18fdfd170`|
| `2026-09-25-m1-paired-vanilla-07-experienced-tree` |376 /240,118,269|`17dc01e3b84303a2f6c59dcedbbe758895d2909a8797ac65dca66f936498daa7`|
| `2026-09-25-m1-pair-validation-audit-01` |11 /31,214|`a5f78d99d56f3cb413e72aac3b3c2970c086ddc6d7cf4c03da6819b7b362c25c`|

No unchanged native rerun is selected. Next profile the remaining stopped
initial-state/software/persistence validation path without dispatch, then remove
only demonstrated duplicate work while preserving full file/lease/source,
budget/capacity and deadline checks. This change improves source reconstruction
but does not resolve joint launch timing; M1.6m.1 stays in_progress.

Affected coverage inherits M1.6m: F01/F02/F03/F04/F07/F08/F09/F11/F16,
N01/N04/N05/N06/N08, C06/C12/C20/C22/C23/C24/C36, and partial
T01/T04/T06/T07/T11. Full source/admission, all-N matching, authoritative clocks,
disposal, capable T05 and scorer controls remain open. M1/G1 stay open; M0/G0,
unrelated M2–M7 and all prior failures/authorizations remain unchanged.
