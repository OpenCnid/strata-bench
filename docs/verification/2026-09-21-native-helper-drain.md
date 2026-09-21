# M0 broker work and native helper cell drain

September 21, 2026. Operator-only. M0.1c.2b.2c.2 advances partial
F03/F04/F07/F09/F11/F16, N01/N02/N04/N05/N06/N08,
C06/C14/C18/C20/C24/C36, T01/T04/T06/T07/T12/T13 and G0 items 1/6.
M0 is incomplete, G0 fails, G1–G5 are not run.

## Implementation

[Broker call lifecycle](../../src/mcbench/broker_lifecycle.py) declares
`native-broker-call-drain/1`. Authentication, quota consumption, the existing
call event and STARTED inventory entry commit atomically before work. Each real
invocation has its own event identity even when native call IDs repeat. Work
records RETURNED, REJECTED or UNKNOWN, elapsed monotonic time, completion time
and a safe fault code. Transport ambiguity remains UNKNOWN; a crashed caller
leaves STARTED durable across restart. No exception message is journaled.

The [broker](../../src/mcbench/broker.py) rechecks the grant at result publication.
A read started before revocation cannot publish a successful result after the
fence. Previously committed effects remain; this does not roll back mutations.
Permanent helper retirement joins every broker call to its work record and
rejects pending, uncertain, missing or legacy untracked work. It retains capacity
and exposure instead of assuming a timeout means termination.

The native diagnostic below found that **interrupting a helper leaves its
yielded code cell alive**. Accordingly, [native cell drain](../../src/mcbench/native_cell_lifecycle.py)
adds `native-source-bound-cell-drain/1` to the retirement gate. It reconstructs
each helper's actual issued `functions.exec`/`functions.wait` calls from settled
raw provider receipts and matches them to later private native request captures.
Preserve source order, exact tool identity/arguments, first observation, caller
and request/profile binding, including history removed by compaction. Reject
reused call/handle IDs and missing, changed, duplicated or unrecognized results.

A yielded cell remains pending after an aborted wait. Only a subsequent exact
owner completion, termination or confirmed absence closes it. The owner must
have received the original handle before its wait was issued. An interrupted
exec without an observed handle/result remains unknown. Terminal helper status
alone cannot release the slot. Broker drain, all model settlements and descendant
closure remain separate prerequisites. No provider replay, inferred receipt,
budget reset or refund is introduced.

Historical ingress verification authenticates saved captures without admitting
or reviving a job. Live request admission and retirement still require their
existing active job/ingress checks. An initial offline reconstruction correctly
failed `INGRESS_REVOKED` when it used the live check; the separate historical
check resolves that inspection need without editing the recorded terminal state.

## Verification

187 focused source checks pass, with focused Ruff and `git diff --check`:

```powershell
$env:PYTHONPATH='src;evaluator/src'
.venv/Scripts/python.exe -m pytest -q tests/test_broker_lifecycle.py tests/test_native_broker.py tests/test_native_retirement.py tests/test_native_interrupt_probe.py tests/test_native_admission.py tests/test_native_helper_probe.py tests/test_native_cell_lifecycle.py tests/test_native_ingress.py --tb=short
```

Coverage includes a concurrently held artifact read: retirement refuses while it
runs, revocation suppresses its eventual result, and only the recorded terminal
work permits closure. Unknown transport/runtime failures and crashed or legacy
work retain their holds. Synthetic native histories cover pending/aborted cells,
missing/duplicate/changed results, wrong targets, reused IDs, explicit owner
cleanup, completion/absence and compaction. Verifier negatives reject late or
missing cleanup, early observations, missing positive controls, wrong caller,
changed output, a non-running interruption target and surviving effects.

The actual native trial uses pinned CLI `0.154.0-alpha.6.2`, binary SHA-256
`960c111d47afd61669954b9df9e56083e302edbfa3ef6962d81dcc14a30051dc`,
Dovetail `15c306ccfef28eb5f616fadcd5fd8eac0663e361`, selected
`gpt-5.6-luna`, authenticated ingress, the prior root/helper tool projections,
the restricted model catalog and a local synthetic provider/worker. Its explicit
bound is 20 requests, one helper, eight helper requests and 90 native seconds.
It does not change the original OAuth authority or a release threshold.

[The interruption fixture](../../tools/native_interrupt_probe.py) starts a helper
cell scheduled to write an owned artifact after 60 seconds. The root interrupts
the helper while native status reports running; the waiting tool reports
`aborted by user after 0.7s`. A follow-up owner wait still finds the same cell
pending. Explicit owner cancellation returns `Script terminated`. A later
successful artifact listing, with the helper grant still active, occurs 60.503 s
after cell start and contains only the expected earlier files: no delayed write.
Only then does revocation and source-bound retirement occur.

Private bundle `2026-09-21-native-interrupt-01` passes all 33 native integration
checks and 24 independent audit checks. Nine root plus eight helper requests
settle once to 238 **synthetic fixture units**. All eleven admitted broker calls
have terminal work records, both participant envelopes close, and the native
job is FINALIZED exit 0. Native lifetime is 88.4897 s within the unchanged 90-s
bound; setup plus execution is 129.3130 s. All source and wire pins match the
trial archive; no owned native CLI/broker processes remain observed.

The cell-drain guard was added in response to that trial. It was **not** present
during the native run. Separate archived source and read-only reconstruction of
the actual receipts/captures prove seven issued helper tools, one yielded cell
and zero unresolved cells. A derived in-memory prefix before cancellation's
return fails `NATIVE_CELL_RESULT_MISSING`. Original evidence and accounting are
unmodified, and the native trial was not repeated. This is source plus recorded
native-evidence verification of the new guard, distinct from fresh live guard
integration or a production RuntimeQualification.

Original authority inspection remains $10 total with $0.7554 unresolved and held;
no real model inference, Minecraft or shared-desktop input occurred. Prior
retirement/state fixture failures and synthetic holds remain unchanged.
Raw records, installations and both source generations stay private.

The sealed inventory contains 8,976 files / 127,127,002 bytes, with manifest
SHA-256 `0e6ae070ec0b6342721dcf61bdec42844bf66e402c2921a0dc26467e34b68336`.

## Remaining M0 work

Complete helper lifecycle recovery and clean state export, including unknown
native tool results, broker work left pending by a crash and full fresh-handoff
semantics. Unrecognized native result forms deliberately block early retirement;
whole-job termination remains a separately proven fence. One timed cell does
not qualify arbitrary CPU/memory work, every cancellation race or a full soak.
Continue required skill supporting-file/learned activation/export integration.

Keep underlying sibling-read/loopback failures, original OAuth uncertainty,
every failed 500-ms shutdown sample, five effective-file failures,
Mineflayer/E9E incompatibility and scorer/provenance/recovery requirements.
Required M0–M6 and conditional M7/extensions are unchanged.
