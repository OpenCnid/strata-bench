# M1.6l — held paired server references and private probe captures

September 25, 2026. D20 authorizes this M1/G1 integration dependency. M0/G0
remain unchanged, G1-G5 remain not_run and unrelated M2-M7 work stays outside
scope. All execution reported here uses synthetic world/process/token fixtures;
no Minecraft, native writer or model is launched by these checks.

## Implemented behavior

`held-pair-protected-vanilla-reference/1` connects both directory-bound copies
to an explicit server-reference coordinator. It uses registered arm order and
the sealed server arguments. It validates and holds both initial states and
launch inputs before either server starts, then requires sufficient remaining
custody lifetime for both declared server windows. Helper hashes/sizes, server
windows and stopped-state limits must match. Output-state space is included in
the pair's storage reservation before copying. Existing parent/writer deadlines
remain hard bounds and are never extended by this coordinator.

After owned readiness, an operator continuation may collect bounded observations;
the coordinator sends one normal server stop, requires complete normal process
history and captures stopped state before process handles close. Hold the first
export under actual file custody while the sibling runs. Both writers must
finish normally before the pair records STOPPED_REFERENCE; that state is
distinct from the legacy unlaunched DISCARDED path. Failure retains its consumed
intent, stops/unwinds owned resources and fences the pair without releasing
resource or cost holds. Native probe admission and all-N readiness remain false.

The existing undispatched-preparation release originally checked only native
model jobs. It now also rejects any game-reference intent, preventing capacity
release during a reference with no model job. Unlaunched copies retain their
explicit capacity-release path, with cost envelopes still held. This is not a
general stopped-game resource release or a completed probe-disposal contract.

`RegisteredProbeVanillaWorld/1` records exact private namespace/pair/arm/fixture,
PackLock, pair-plan digest and initial world files/directories. Its input check
requires exactly the registered state and immutable sealed software; imported
session locks, extra state, inconsistent provenance and directory/file aliases
refuse. New stopped captures use `StoppedVanillaSnapshot/3`, preserving initial
provenance even when probe outcome bytes change. State-size limits refuse before
copying output. Ordinary restoration rejects these captures with
PROBE_FEEDBACK_FORBIDDEN before same-profile or changed-worker baseline handling.
No version2 restoration identity is fabricated. Legacy captures remain valid.

## Verification and retained failures

Persistence/restoration/existing vanilla-session checks pass86 in41.08s. A
later provenance check exposes a missing standalone file/directory-collision
refusal; the spelling case passes, the collision fails, and the corrected
collision case then passes. Both attempts remain retained. The initial runtime
test fails because its synthetic writer omitted the private evidence directory
that the real preparation path creates. Correct that fixture; the affected
runtime/copy batch passes19 in551.04s.

Subsequent review adds matched runtime-limit checks, the game-intent resource
release guard and joint initial-state preflight. The four asymmetric-limit
cases pass; the changed release behavior passes4 in156.86s, including the
positive paired flow and unchanged allowed releases. The final joint-preflight
batch passes9 in444.08s. Across these checks,115 distinct cases pass:30 new and85
affected existing cases. Ruff and whitespace checks pass.
Repeated source cases are counted once, and intermediate passing source is not
substituted for verification of later behavior changes.

These tests exercise actual registered pair/native-view/budget custody,
Windows file leases and stopped-file copying with synthetic game bytes. Native
writer execution, JVM identity, token results and process exits are substituted.
No authoritative game-clock, physical Java termination or isolation claim follows.

The final changed-runtime command is `PYTHONPATH=src;tools;evaluator/src`
with `.venv/Scripts/python.exe -m pytest tests/test_probe_vanilla_runtime.py -q -x`
and a fresh private `paired-preflight-tests` base directory. Retained logs cover
the persistence/restoration, existing writer/copy, provenance, runtime-limit and
release checks described above. No unchanged native or paid suite is repeated.

Read-only sealed reconstruction passes76/76. It checks both complete producer
file/directory inventories, explicit archive mapping, registered initial-world
identity, both preflight events before launch intent, matched runtime limits,
normal stopped-reference dispositions, complete provenance and every stopped
state/immutable input byte. The two synthetic outcomes differ while retaining
their common initial-world identity. Both clean-save/admission claims remain
false. Five failed paths retain fences,200 synthetic cost units and capacity;
no failed first arm launches its sibling. Production vanilla JAR pins are not
overridden in the audit: these are explicitly synthetic inventory comparisons.

The first reconstruction refuses EVIDENCE_INVENTORY: an intervening read-only
SQLite inspection created18 unsealed WAL/SHM sidecars. All8,294 originally
sealed files are unchanged; all nine added WALs are empty. Preserve the sidecars,
original path mapping and failed audit in the separate audit bundle. The corrected
inspection uses the frozen immutable database reader after archiving only those
new sidecars. Both original producer seals then verify unchanged. Completed
persistence tests also have an explicit original-to-archive mapping to stay
within the evidence reader's per-bundle file limit; their bytes are unchanged.

All40 real durable authority tables match before/after. Exposure remains
$4.887796/$10, including every old hold and consumed decision; this grants no
M1 inference allowance. No owned runtime remains.

| Private evidence store | Files / bytes | SHA-256 seal |
|---|---|---|
| `2026-09-25-m1-probe-runtime-01` |8,294 /33,940,742|`189575a087f2dc632085cca80d62a02fcf48f154c104e67b3b861fde4bd39faa`|
| `2026-09-25-m1-probe-runtime-persistence-01` |6,694 /4,800,419|`011f2b7c5b0f31790efa756d8c721db94c7b77a2446302b754c8fdab86fec66c`|
| `2026-09-25-m1-probe-runtime-audit-01` |24 /324,633|`c6fa763a34f5493cc8be4c3141f7aafbc79297047513939e1a02e3570ddd1e02`|

## Remaining acceptance

M1.6l remains implemented_unverified for authentic paired runtime integration.
Next execute the reviewed paired server-reference profile from complete
registered authentic inputs and retain its actual owned-process/token/source/
saved-state joins. Check host resources and all finite parent windows before
execution; insufficient time must refuse before either server starts. Then
integrate and verify all-N worker/body readiness, live initial-state matching,
scoped native root/helper admission, clocks and one-way agent disposal. Server
references do not establish those contracts. T05, scorer controls and remaining
combined runtime routes still block G1. No M1 paid allowance is inferred.
