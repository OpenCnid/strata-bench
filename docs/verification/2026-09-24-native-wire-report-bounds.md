# Native wire bounds and report-failure cleanup

M0.1d.9d.2 addresses the two distinct size failures and skipped worker drain
retained in D19.7. The implementation passes 475 focused tests, a changed native
preflight 27/27, and an authentic injected-report cleanup audit 49/49. Fresh
D19.8 also passes the actual LLM/Mineflayer/helper pilot, 14/14. This closes
M0.1d.9d/.9d.2 and G0 item 1 for the named D14 development profile. M0 remains
in_progress and G0 fail pending the remaining scorer and recovery/time/cost
evidence.

Coverage: F04/F11/F16, N01/N02/N08, C09/C18/C20, partial T04/T07/T12/T13,
G0 items 1/4/6. D14 isolation deferral and M1–M7 remain unchanged.

## Connected producers and consumers

`native-bounded-receipt-wire/2` gives native OAuth replies an explicit **8 MiB**
wire bound. The generic transport/parser default remains **256 KiB**. Dispatch
reserves the selected full bound before provider contact; receipt persistence,
settlement, cell state, retirement and stopped recovery share the same native
bound. Oversized/incomplete replies still fail closed and retain available
prefixes without invented usage, replay or refunds. The bound accommodates
verbose native event framing; it does not increase calls, tokens, latency or
spend and cannot guarantee every response will fit.

Private native pilot reports now have an explicit **32 MiB** object bound.
Gameplay object/quota defaults, the **128 MiB** operator quota, startup headroom,
original **$10** experimental allowance and all unresolved holds remain unchanged.

The native runner exports its journal and closes its database in a finally path
around final report publication. The outer game runner attempts the existing
bounded owned-worker stop after native/report exceptions before forced fallback.
Successful cleanup cannot turn a failed model/report result into a pass.

## Executed source and native checks

```text
python -m pytest tests/test_native_wire_bounds.py tests/test_worker_stop.py
  tests/test_inference_transport.py tests/test_native_oauth.py
  tests/test_receipt_capacity.py tests/test_receipt_recovery.py
  tests/test_native_retirement.py tests/test_native_cell_lifecycle.py
  tests/test_native_conformance.py tests/test_helper_pilot_budget.py
  tests/test_luna6_pilot_budget.py tests/test_pilot_budget.py
  tests/test_native_piloting.py tests/test_native_helper_piloting.py
  tests/test_native_tool_projection.py tests/test_native_admission.py
  tests/test_native_game.py -q
475 passed in 122.99s
```

Tests exercise exact bounds/overflow, unchanged generic limits, a local HTTP
native reply larger than 256 KiB, storage reservation and settlement before
delivery, actual report-quota failure with journal/database cleanup, journal
failure cleanup, and owned Node worker drain/timeout behavior. The earlier
177-test selection overlaps and is not added. Repository Ruff and diff checks
pass.

Private `2026-09-24-helper-native-06` runs the actual pinned CLI/Dovetail with
synthetic provider/worker replies. A valid SSE comment deliberately makes one
wire larger than 256 KiB without adding model tokens or game behavior. **27/27**
checks pass in **21.227262 seconds**: six settled requests, closed root/helper,
FINALIZED/exit0, and exact large receipt persistence. The live preflight consumer
accepts the current source pins. All **40** original authority tables remain
unchanged, zero model credits/game launches. Full 3,759-file archive verification
passes; SQLite is checkpointed into DELETE mode before sealing. Seal:
`73bc48ddfdbc479dca6a00530583ba9ed46f94d44bede8d32a9b6cc8a9ad0eda`.

## Retained failure readback

Private `2026-09-24-wire-report-audit-01` invokes the actual changed report
publisher against an isolated private store. It publishes and reads back the
exact **322,961-byte** retained D19.7 report, digest
`a28619ad6325ba82391a0cd92e4b164d448ccbbee0c1ec5d512c8ae722ce0ade`.
Its failed verdict remains failed. The old **261,906-byte** response prefix still
raises **TRUNCATED_EVENT_STREAM** under the larger native bound; no terminal
usage, charge recovery or refund is inferred. All 40 live authority tables remain
unchanged at **$4.831942/$10** exposure. This is offline publication/readback,
not a replay or replacement of the original missing live report.

Four-file archive seal:
`d0f9fe73ab57c3c780c08257acdd4e337229a63fe671efe167845ae60272f56f`.

## Authentic cleanup and fresh helper execution

Private `2026-09-24-report-failure-live-01` uses a fresh vanilla instance and
synthetic provider. An explicit operator wrapper lets the native truncated-wire
case finish, then invokes an actual CAS write one byte above its default object
limit. This injects **ARTIFACT_QUOTA** before the outer runner receives the native
result. It tests the production outer finally path, not a naturally occurring
model/report fault or paid provider response.

The run remains **fail/exit1** as required. The independent read-only audit passes
**49/49**: normal worker drain **30.6094 ms** within 2,250 ms, worker/server driver
exit0, no forced cleanup, all **45** owned processes terminal with zero Job
terminations. The server stop follows the worker exit; stop-to-exit is **1,828 ms**
and the stopped world inventory verifies. No game actions/primitives occur.
The partial synthetic response remains unsettled with its reservation retained;
no complete joint checkpoint is claimed. Native time **12.871162 s**, inner
game-run time **103.359 s**, outer owner **145.969 s**. These different intervals
are retained separately.

All **40** original authority tables and the original template are unchanged at
**$4.831942/$10**, with zero paid requests. The actual changed source pins match.
The complete **3,932-file / 120,992,907-byte** archive verifies; seal:
`60ae1af8959d042cad91529cad4727e22583443fc2bce5565e5a400e28222c92`.
This qualifies the bounded injected-report cleanup path only, not every N08 or
recovery failure case.

Fresh D19.8 / m0-pilot-15 is prepared under existing D18/D19 authority, preserving
all unresolved reservations. Preparation seal:
`748fff91130b24ec9e5f63fca20af839fc7f285c15daca4d268ae14307c34356`.
The fresh actual GPT-6 Luna pilot **passes all 14 checks**. The model chooses
and completes a **71.55-degree turn** followed by a **1.072751319-block walk**,
with a **0.072751319-block** target residual and unchanged health20. Both actions
release controls, and ten primitive events join the model requests to the worker
journal. The independently read stopped player matches the final observation.
The targets were selected by the model from public observations; no scripted
route or operator-selected target supplies these results.

One clean-context advisory helper receives only the root's public movement
facts, makes one real model request and sends its final review back to the root.
The reader verifies delivery in a later root request, rather than accepting a
root-written summary. Only the root makes game calls. Both participants close
and the helper envelope closes without uncertainty. This proves the bounded
native helper path; it does not establish full OS isolation or advice quality.

All **16 requests** settle: **15 root requests/$0.016588** plus **one helper
request/$0.000637**, totaling **$0.017225**. Native execution is **211.623544 s**,
within the 240-second bound, with FINALIZED/exit0. Inner game-run time is
**321.766 s**, outer owner time **364.313 s**. The normal worker drain is
**36.0872 ms**, both game drivers exit0, and all **53** owned processes terminate
with zero Job terminations. No complete checkpoint or scientific score is claimed.

The live **311,259-byte** report is durably published and matches its digest and
returned content; the journal is exported. All sixteen native wires match their
stored digests/lengths and declared 8-MiB policy. The largest is **209,020 bytes**:
this successful paid case does not itself exercise the larger-than-256-KiB wire
boundary; native06 and the local HTTP test supply that evidence. Report ref:
`cas:sha256:9144fb4ff0747b1e6874106f3fb9b607fd5ffe6c6bd9318f23b19cd831074397`.

Every predecessor accounting row, D12, original allowance and unresolved hold
remains unchanged. Combined committed/reserved exposure is now
**$4.849167/$10**. D19.8 is consumed; no new unknown charge was created.
Full private archive `2026-09-24-m0-helper-live-15` verifies: **4,003 files /
209,477,397 bytes**, including the stopped controller snapshot and 71 scoped
CAS objects. Eighty-nine external installation/opaque refs remain explicit; it
is not a standalone game distribution. The stopped expendable credential copy
is removed. Seal:
`082abec906fe9470718b5df62dcc268e83ac5f3e9078b333314234a8b9bd339b`.

No unchanged successful pilot is replayed. G0 item 1 now passes for this D14
development profile; full helper/worker isolation remains deferred to M1/G1.
Item 6 gains actual nested receipts and measured intervals but retains its
remaining authoritative time/private-cost joins. Next connect the existing
private positive/negative milestone evidence to the private report and reconcile
the remaining applicable item 4/6 recovery, clock and save requirements. All
earlier failures remain failed; M1–M7 are unchanged.
