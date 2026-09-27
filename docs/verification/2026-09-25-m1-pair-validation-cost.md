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

## Continued stopped software and persistence profiling

The next read-only diagnostic uses case07's externally sealed initial tree and
private registered-world provenance. `VanillaPersistence` validates it in6.4363s
under `cProfile`, holding664 files across four immutable trees. Separately,
the real WAL-aware software resolver takes10.5409s over the unchanged sealed
installation. Neither diagnostic reconstructs a live grant, dispatches a process,
changes a world or admits a probe. All40 authority tables remain unchanged.

The measured costs include repeated filesystem metadata queries for the same
ancestor and repeated parsing of directory names. `storage.reject_links` now
uses one non-following metadata query per component instead of checking existence
and then requesting metadata. Missing components still reach their ancestors;
link/reparse/access-denial failures remain enforced. `inventory.directory_layout`
validates each repeated lexical path once within a call against that call's
fixed reviewed-path policy. All collision, private-content, directory closure and
quota checks remain; there is no filesystem cache or reuse across calls.

After those changes, persistence/resolution measure5.6526/8.1547s. Immutable and
lease inventory digests, resolved launch identity and every source seal are
unchanged. These individual samples diagnose cost, not live deadline acceptance.

Session construction now retains local writer and software-lease checks within
the coordinator's complete before/after pair validation. Both sessions finish
preparation and the full source/software/account/resource/deadline checks pass
before either server can start. New fault injection after the first constructor
proves that an added software directory, changed account or expired preparation
still refuses both dispatches and retains cost/capacity holds.

The initial focused selection passes181 cases in318.27s. It includes real
Windows junction refusal, per-call changed-ancestor/access-denial cases, lexical
policy/collision cases, storage/controller/provisioning/pack resolution and
ordinary/probe persistence plus paired-runtime verification. Native process/JVM
behavior in the runtime tests remains explicitly substituted.

A subsequent change borrows installation entries from the pair's existing live
software lease rather than hashing and leasing that entire tree again per arm.
Each session acquires a separate launch-helper lease. The merged inventory uses
the existing pinned-inventory quota/conflict checks and retains the exact prior
helper-plus-installation file/tree identity. The pair owns the software lease
through both writer lifetimes, and full software validation still runs at the
joint boundaries and before each actual launch. Final focused runtime checks
pass15/15 in311.15s, including exact fresh-snapshot equality, helper/software write
denial and lost-software-lease refusal before dispatch. The selections cover182
distinct cases; both source versions and all first-stage results are retained.
The private `2026-09-25-m1-persistence-profile-01` store is sealed with12,864
files/67,100,781 bytes and SHA-256
`434a4856edf1241fc971a7ddc27839407b305e9b9299c174de5bfbe4966b18e5`.
All40 authority tables remain unchanged; no owned process remains after these
source checks. Fresh native case08 used a new host/port/accounting preflight and
the unchanged300/200/170/60/60s bounds. No model calls.

Case08 passes joint preflight. Its initial server reaches readiness, passes the
three source/copy/software write denials, stops normally with12/12 retained owned
processes and exports26 state files/13,304,918 bytes in snapshot /3. The snapshot
manifest SHA-256 is
`7118230e8a740130c212ba9bafc5fbe4ff7fbe5651f2f991cb634dbf103aa24c`.
The sibling records launch intent but refuses `WRITER_EXPOSURE_INSUFFICIENT`
before creating its server process: its full60s window no longer fits. The whole
test remains FAIL in195.56s, inner/outer custody UNCERTAIN at131.188/142.906s,
pair FAILED/FENCED and all200 synthetic units/whole capacity retained. Both
copiers stop normally10/10 each. All40 authority tables remain unchanged; no
owned runtime remains. The initial stopped server is a narrow success inside a
failed pair, not a paired/T11/G1 pass or proof of all clean-save semantics.

| Retained case08 store | Files / bytes | SHA-256 seal |
|---|---|---|
| `2026-09-25-m1-paired-vanilla-08` |686 /65,709,556|`5631b3b9010f021311bec7022cc408fbb394c5640bfc700183d8d86a0ce4ec1c`|
| `2026-09-25-m1-paired-vanilla-08-initial-tree` |378 /240,363,299|`4e666368f48bf84e107f7d29510f0823f52684d255046f9c5f2d83a6965b4eb6`|
| `2026-09-25-m1-paired-vanilla-08-experienced-tree` |376 /240,118,273|`7d1f54b39353c1a9d032ce9116ad21df84140638a8308939924506a324910451`|

Source now removes consecutive whole-pair checks around the launch boundaries.
The caller's full held-pair check precedes session preparation; the coordinator
still verifies its own scope, complete joint preflight and each session's full
check immediately before dispatch. Checks before the callback and normal stop,
plus final stopped/export verification remain. It no longer repeats the full
scan immediately before `start`, between one stopped export and the next
`start`, or immediately after an already verified return. New negative cases
change authority at launch intent and after the first stopped export. All22
focused cases pass in352.80s; the three source selections cover189 distinct
cases. The private `2026-09-25-m1-runtime-boundary-01` store is sealed with5,914
files/21,886,671 bytes and SHA-256
`c786d60bf071491049b3804881893c2e2fa370b2c9b7f4fbbe6c0f95190299bf`.
Case08 read-only reconstruction passes30/30, including exact borrowed input
identity and the normal first-server export inside the failed pair. Fresh
case09 used the changed source and unchanged windows after host/port/accounting
preflight; no unchanged native case was repeated.

This continuation also touches F05's sealed acquisition/inventory dependency;
its broader authentic acquisition/pack compatibility acceptance is unchanged.

## Case09 paired operator reference

Case09 passes in229.74s. Parent300s, outer/inner writer200/170s and two60s server
windows are unchanged. Both genuine vanilla servers reach readiness and stop
normally, each with12/12 complete retained owned-process history and no forced
or terminated processes. Both copiers stop normally10/10. Initial/experienced
writer elapsed times are167.297/155.406s. Each arm verifies three source/copy/
software write denials, the first export stays held during its sibling, and
premature capacity release refuses. All200 synthetic units and whole2-body/
6-slot/8192MiB/6GiB capacity remain held; STOPPED_REFERENCE does not prove disposal.

Both exports use private snapshot /3 provenance with26 state files. Initial:
13,313,112 bytes, manifest SHA-256
`674c6eecae723ed469a6779b42457d8e887f76324ab81644e56a733d483a3462`.
Experienced:13,263,962 bytes, manifest SHA-256
`ec7008fe196730e73d65c21ff590798f4cc6c59229555131c1a3e9be2155b563`.
Neither capture claims a complete clean-save checkpoint. The separately archived
trees are terminal post-game trees, not relabeled initial copies.

| Retained case09 store | Files / bytes | SHA-256 seal |
|---|---|---|
| `2026-09-25-m1-paired-vanilla-09` |716 /80,775,109|`f4653a95712331d5cc3bee41693957b0b5d8375d93ff13f262bdc76a45e98337`|
| `2026-09-25-m1-paired-vanilla-09-initial-tree` |378 /240,371,552|`4525e085eb3f8a44dabdf528941173f2a27a959612e28885791919df3f2ee5fd`|
| `2026-09-25-m1-paired-vanilla-09-experienced-tree` |378 /240,322,364|`72926c4c5fa5a97aa7c25a836342d2678288e3a282cd34367c8d6995d112fbd3`|

Case09 read-only reconstruction passes37/37: exact genuine world registration,
normal owned histories, borrowed launch inventory reconstructed from sealed
installation/helper pins, both26-file tagged captures, terminal-tree equality,
write denials, retained whole capacity/cost, scope labels and unchanged40-table
authority. Preserve the first reader's missing optional failure-key exception
and corrected reader; no native rerun or producer mutation. Case08 adds30/30
checks retaining its failed-pair outcome. No owned runtime remains and all real
accounting holds/consumed decisions persist at$4.887796/$10.

M1.6m.1 is verified for the measured optimization and exact operator-reference
profile. M1.6m remains in_progress: agent/protocol/capacity fixtures are synthetic,
model_calls=0 and worker_bodies=0. Full authentic native agent source/admission,
all-N live matching, authoritative clocks and one-way disposal remain open,
as do T05, protected scorer controls and combined runtime routes. The successful
server reference does not close T11 or G1 or authorize M1 paid inference.

Continuation verification used the following focused selections; all source
stages and XML/logs are retained in the profile/runtime-boundary bundles:

```text
pytest tests/test_storage_paths.py tests/test_inventory_directories.py tests/test_storage_controller.py tests/test_provisioning.py tests/test_pack_launch.py tests/test_vanilla_persistence.py tests/test_probe_vanilla_persistence.py tests/test_probe_vanilla_runtime.py -q
pytest tests/test_probe_vanilla_runtime.py -q
pytest tests/test_probe_vanilla_runtime.py tests/test_probe_vanilla_runtime_contract.py -q
pytest tests/test_probe_vanilla_runtime_native.py -q -x
```

The native command is opt-in with each attempt's fresh pinned private input and
separate evidence/workspace. It passed only case09; prior failures remain.
Final focused Ruff/whitespace checks pass. Documentation QA preserves406 unique
milestone IDs, the entire prior append-only history and unchanged normative
SPEC, and resolves1,438 local links in the four edited documents.

Final read-only audit store `2026-09-25-m1-paired-vanilla-audit-02` is sealed:
18 files/92,970 bytes, SHA-256
`75bf3392ddcb6547ce743f3cf846944f56968365ab2dbe12699adffdb62c4d24`.
It includes both reconstruction results, the retained first reader error,
source-to-case09 byte equality, fresh WAL-aware40-table authority comparison,
empty owned-process snapshot, final focused Ruff/diff checks and documentation
QA. The subsequent public seal pointer changes no production or test bytes.
