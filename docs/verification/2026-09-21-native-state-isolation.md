# M0 native code-mode state and cell ownership

September 21, 2026. Operator-only. M0.1c.2b.2b.4 advances partial
F03/F04/F07/F11/F16, N01/N04/N06/N08, C06/C20/C24/C36,
T01/T04/T06/T07/T12/T13 and G0 items 1/6.
M0 remains incomplete, G0 fails, G1–G5 are not run.

## Implemented probe and observed behavior

[State canaries](../../tools/native_state_canaries.py) exercise the actual pinned
CLI's `store`/`load`, yielded `functions.exec` cells and `functions.wait`. The
existing [native identity fixture](../../tools/native_mcp_identity_probe.py)
supplies the sealed restricted broker, native clean helper, prior exact root/helper
tool projection pins and durable accounting. It does not rerun the completed
patch/resource or retry/compaction matrices.

Each participant writes a different owned marker under the same storage key in
a completed initializer. Subsequent calls retrieve their own value, while the
other participant's private key is absent. The synthetic provider passes only
the other participant's observed cell ID for adversarial reads/cancellation;
neither private marker reaches the other's model inputs. Both attacks finish
before the target cell completes. Both owners subsequently retrieve their own
completion and value, proving the rejected cancellation did not kill the target.
Foreign and nonexistent IDs produce the same native `exec cell <id> not found`
error. Root's live ID is 3 and helper's is 2; IDs are participant-local, and the
fixture explicitly avoids a collision with an owned active handle.

This separates persistent storage from an unfinished cell's writes. The retained
fourth run found that a yielded cell's writes were not visible to another call;
cancelling the root's writing cell also left no value. It did not prove completed
storage publication. The final run tests completed initializers and passes that
positive control. It does not qualify every concurrent-write ordering, cancelled
write transaction, restart/export or future session reset.

The fixture keeps the parent bound at 12 requests and native lifetime at 90 s.
Its declared partition is seven root and five helper requests. The
[local provider](../../tools/native_dispatch_probe.py) now accepts a strictly
bounded helper-request limit within its parent limit; the existing default is
four. Child token/unit reservations scale with that declared limit and remain
inside the original aggregate envelope. This is a synthetic fixture parameter,
not an increase in the user's OAuth allowance or any release threshold.

Failed budget closure now produces a durable fixture report with its typed error
instead of losing the report to an exception. It neither settles uncertain
requests nor releases their reservations.

## Source verification

41 focused checks pass, with focused Ruff and `git diff --check`:

```powershell
$env:PYTHONPATH='src;evaluator/src'
.venv/Scripts/python.exe -m pytest -q tests/test_native_state_canaries.py tests/test_native_helper_probe.py --tb=short
.venv/Scripts/ruff.exe check tools/native_state_canaries.py tools/native_mcp_identity_probe.py tools/native_dispatch_probe.py tests/test_native_state_canaries.py
```

The new tests reject missing actors/results, same live handle, leaked/overwritten
state, coerced booleans, unrelated errors, successful foreign reads/cancellation,
cancelled own cells, marker contamination, late attacks and missing timestamps.
Actual caller binding and duplicate-output consistency are checked. Finite helper
exposure rejects zero, negative, boolean, fractional, missing and over-parent
values. An uncertain closure is reported after one attempt, with no retry/refund.
These are synthetic verifier tests, separate from the native evidence below.

## Native evidence and retained failures

All five private bundles use CLI `0.154.0-alpha.6.2`, SHA-256
`960c111d47afd61669954b9df9e56083e302edbfa3ef6962d81dcc14a30051dc`,
Dovetail `15c306ccfef28eb5f616fadcd5fd8eac0663e361`, selected
`gpt-5.6-luna`, a local deterministic provider and synthetic game worker.
No real model inference, Minecraft or shared-desktop input occurs.

| Private bundle | Actual outcome |
|---|---|
| `2026-09-21-native-state-01` | Decoder omitted native `input_text` chunks and failed to recognize the yielded root cell. Two requests: one settled, one uncertain. Native exit 1; UNSETTLED. Original source and missing-closure failure retained. |
| `2026-09-21-native-state-02` | Provider-side peer wait exceeded the synthetic transport timeout. Four requests: three settled, one uncertain; native exit 1, UNSETTLED. Original failed report retained. |
| `2026-09-21-native-state-03` | Five-second native delay was shorter than observed helper tool startup. Six requests: five settled, one uncertain; native exit 1, UNSETTLED. This does not establish an isolation failure or pass. |
| `2026-09-21-native-state-04` | Native helper waiting permits both live cells. Twelve requests settle to 168 fixture units, FINALIZED exit 0. Original 27/34 verdict retained: four denial checks expected the wrong wording; three storage/completion controls fail because pending/cancelled writes were used. |
| `2026-09-21-native-state-05` | Completed storage initialization and separate pending cells. All 33 integration checks and 28 independent audit checks pass. Twelve settled requests, 168 fixture units once, both participant envelopes CLOSED, FINALIZED exit 0. |

Final profile:
`32f35c110610eb094115fb0a9189cc0efdc9a1fa790cc91dd223d1af2a87b985`.
Prior root wire pin:
`463331dd394d9ca9eb6c891b61deb65e777a81c088e244d84928e11dc5388595`;
helper pin:
`b2de5881a527194a9212c5331187d99e2f5e92ac92c493dab4a758cec17848cc`.
All twelve admitted requests match these pins. The selected catalog retains the
explicit patch restriction from the previous checkpoint.

Final native lifetime is 52.5458 s within 90 s; total fixture setup/execution is
92.1870 s. Twelve calls consume 120 input plus 48 output = 168 **synthetic fixture
units**. Across all five stores, 33 settled requests account for 462 fixture
units; three uncertain requests remain. The first three stores retain their full
120,000-unit synthetic envelopes; they are not refunds or real OAuth charges.
All five native processes have terminal exit codes, and the final process audit
finds no owned native CLI or broker processes remaining. Budget uncertainty is
distinct from an active process.

Read-only inspection confirms the original $10 authorization, its digest and the
unresolved $0.7554 hold remain unchanged. No replay, refund, new allowance or
RuntimeQualification was issued. Raw requests, profiles, installations and
source snapshots remain private.

Sealed inventories preserve every original outcome:

| Bundle suffix | Files / bytes | Manifest SHA-256 |
|---|---|---|
| `state-01` | 8,953 / 125,355,733 | `92578c3e6504665c85a3ba90ae3c8d24ad79fdafbdc8c726b5e5a0fd8be465a0` |
| `state-02` | 8,966 / 125,608,299 | `3fd757e8d61b37127052c4bda7f801f7bb28b5c980c0cc6424e482784ca53f50` |
| `state-03` | 8,974 / 125,849,098 | `e7b2715a9a0c47976a83743493a4c13e11d2a26ccfba64597eea2efde7f71ea5` |
| `state-04` | 8,988 / 126,235,438 | `eef1fa019fc45b2a1249b2766ed3e90b572e4094f083066fea819a8c1344335c` |
| `state-05` | 8,994 / 126,313,607 | `b1e6325ca768eb6dff99447b2b3ba77b317e7c972e05a3abddf0c04890c77bd0` |

## Remaining M0 work

Next connect existing participant revocation/accounting to measured native helper
retirement and slot reuse: revoked or resumed helpers must not regain broker or
dispatch access, and pending/uncertain consumption must remain charged. Continue
from `native_admission.py` and the existing lifecycle/topology fixtures. Complete
skill supporting-file/learned activation/export and fresh-handoff evidence remain.

Retain underlying sibling-sandbox read and loopback failures, the old patch
read channel, original OAuth uncertainty, every failed 500-ms shutdown sample,
five effective-file failures, Mineflayer/E9E incompatibility and remaining
scorer/provenance/recovery requirements. Required M0–M6 and conditional M7 and
extensions are unchanged.
