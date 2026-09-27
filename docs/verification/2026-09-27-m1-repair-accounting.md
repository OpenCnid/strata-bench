# Measured worker repair interval and strict publication consumer

M1.1c.3.4 now records a repair charge opening before quiescence and a fixed closing
receipt while the Worker/6 public publication hold remains active. The controller
consumes and stores that actual receipt. This is implemented but unverified in
Minecraft; all complete G1 suites and G1 remain `not_run`.

## Measurement and boundary

The worker records its original plan, clock identity, journal cursor, monotonic
and Unix time, cumulative primitive count and native-source high-water values in
the same transaction as pause intent. The count must equal the sum of native
sources. Its original monotonic clock survives the client replacement because
the worker survives. Reopening the journal creates a different clock identity;
it cannot manufacture the old measured interval.

After verified native resume and before public publication, the private endpoint
checks the native decision/instance, refreshes the native high-water count and
freezes one closing receipt. Closing sources cannot disappear or decrease, and
their sum, total difference and elapsed monotonic time must agree. Repeated reads
retain the first closing receipt. Later consumption is retained but invalidates
preparation; it does not rewrite the old receipt or silently refund anything.

These are **worker charge boundaries**, not proof of the physical timestamp of
each primitive. Previously emitted but newly observed consumption belongs to the
interval in which the worker records it. Full billing must reconcile prior
gameplay allocation against these intervals to avoid counting the same usage
twice. No claim of that complete reconciliation is made here.

The receipt explicitly records `complete_repair_accounting=false`, null game
ticks/model usage and `publication_tail_included=false`. No game ticks are inferred
from elapsed time and no missing provider consumption is assigned zero.
Publication now requires the frozen measured closing count and resume digest;
a caller-supplied count alone is insufficient. The settlement CAS reference
still requires a production controller settlement producer.

`WorkerPublicationClient` validates exact grant/scope binding to the resume
transport, strict publication/measurement records, current control observation
metadata and response identity. It uses one bounded private HTTP request with no
automatic mutation retry. An unusable publication reply is uncertain and must
be reconciled by status. Private transport credentials remain outside gameplay.

`NativeRepairResume.measure_prepared` joins the confirmed controller commit,
replacement adoption, original resume and publication capability. It stores the
worker receipt with the controller's original request-to-observation monotonic
interval. Repeated measurements retain their source reference. Budget settlement,
full accounting and campaign permission are explicitly false and unchanged.

## Executed evidence

The actual Python controller → Node worker → Windows guardian → replacement JVM
test passes on the final implementation. It executes prior gameplay, pauses,
repairs/restarts/commits, prepares resume, collects the measured interval through
the real private endpoint, stores it in controller CAS, and publishes control
metadata before executing the next scoped action. The measured opening is nonzero;
the closing equals worker usage, and its delta equals the sum of actual journal
charge events between the two cursors. Repeated measurement is identical.
Prior action history and the original lease remain intact.

The body, settings qualification, verification and final settlement producer in
this test are synthetic. It is not a Minecraft run or complete settlement proof.
The real worker charge counter, process replacement and private transports are
exercised. No provider/model call or installed-client change was made.

Executed checks:

- `pytest tests/test_controller_restart_jvm.py -k publish -q --tb=short` with
  explicit Windows Node/Java/classpath: final 1 passed, 6 deselected. Earlier
  passing iterations remain retained as the same scenario, not extra coverage.
- `pytest tests/test_worker_publication.py tests/test_native_repair_resume.py -q`:
  29 passed. These cover arithmetic/proof substitution, source regression,
  incomplete-accounting flags, grant binding, unusable publication replies and
  existing controller evidence/stop failure paths.
- Focused Node accounting/publication tests: 12 passed, including nested group
  counts. Missing opening, changed clock, late charges, race/storage failures,
  current publication checks and credential refusal are included.
- Node build/schema-validator check, Ruff and diff whitespace checks pass.

Initial TypeScript cast/narrowing build failures are retained. One Python test
initially expected the inner `Fault` directly; Pydantic correctly wrapped it as a
validation error. The test expectation was corrected without relaxing validation.

## Remaining complete repair accounting

Reconcile the measured primitive interval with prior-gameplay settlement, actual
body/server clock evidence, all related model/helper/retry consumption and the
time through publication/completion. Reserve and retain unknown amounts while
any required source is missing. Then connect actual settlement to typed control
publication and original-lease controller completion atomically.

Generic worker-backed `Reconfigurations.finish` remains closed. Restored-effect
rollback, repeated repair lifecycle, qualification issuer, real launcher, selected
skill and the full authentic controls/isolation/scorer/probe gates remain open.
Preserve essential-native04's health failure and every prior hold/decision. No
unchanged Minecraft retry or M1 inference allowance was used.

The final fixture records opening3, closing21 and18 new worker charges across
6,171ms. These are measured charges, not proof that the opening3 were already
billed. Read-only WAL snapshots of the synthetic worker/controller databases and
the exact interval charge-event audit are retained in the private bundle.

Private evidence bundle `2026-09-27-m1-repair-accounting-01` is sealed:45 files,
2,997,931 bytes, SHA-256
`e21c2d396fb09077f6bb40a80668c35bb8bd711d0a1f4fcbfa1ac7943cfb4a97`.
It preserves source/compiled pins, failed/passing logs and WAL-aware synthetic
process database snapshots. All40 authority tables/eight holds remain unchanged;
installed JAR/options unchanged, no owned runtime remains. All460 ledger IDs
survive and2,123 reviewed local links resolve. The archived source snapshot
precedes this appended seal pointer. Full repair settlement and G1 remain open.
