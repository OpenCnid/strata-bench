# M1 notification-safe native cell drain

Operator-only. M1.3b.5, inheriting M1.3b.4 coverage. M1 is in_progress;
G1 not_run. This verifies the named content-frame path, not full lifecycle.

[Cell-drain policy /2](../../src/mcbench/native_cell_lifecycle.py) separates
model-controlled notify() strings from native result frames. Notifications share
an exec call ID and can contain arbitrary text, including an exact imitation of
a native completed, terminated or pending header. They cannot establish a handle
or release a helper slot/envelope. The verifier requires a separate native content
frame, exact source call/actor/type, and unchanged repeated results. Duplicate
native frames still fail. Inline image payloads are permitted but contribute no
status evidence; aborted waits keep cells pending.

The prior /1 implementation rejects a valid completion accompanied by a
notification as a duplicate. The new implementation preserves permitted
notifications/media without trusting their contents as lifecycle evidence.
SPEC6 records the changed implementation contract and retained historical /1
scope; no acceptance threshold or scientific requirement is reduced.

**Remaining limitation:** the pinned native runtime also represents a silent
yield with a scalar string. That shape cannot be distinguished from notify text
using these captured requests alone. Policy /2 conservatively refuses its drain
proof with NATIVE_CELL_RESULT_MISSING. Independent readback of the sealed
selected-state `-02` capture confirms this refusal without modifying that
historical successful state/cell-ownership result or its accounting. Unambiguous
runtime framing or independently qualified whole-process drain is still needed
for this path. A stopped-looking agent or model prose is insufficient.

## Actual native evidence

The selected conformance retirement fixture now has an explicit notification
variant. All three participants emit each of three forged-status notifications,
an exact public inline PNG and an ordinary completion marker. Actual native
outputs contain nine scalar notifications and three separate content frames;
the native main frames establish completion. The original helper retires under
/2, its resume is denied, and a fresh replacement completes under the one-slot
limit. On this same capture, the retained /1 source returns
NATIVE_CELL_RESULT_DUPLICATE. No old capture was rewritten or rerun.

Profile: `18505ec803f561dd220a2f5ad0b9bd56162e1575079620ffbd6e8ee885cf7e83`.
Pinned CLI0.154.0-alpha.6.2, verified companions, Dovetail commit and selected
GPT-6 Luna catalog remain as in the [boundary audit](2026-09-24-m1-native-boundary.md).
Local scripted provider, fake OAuth and synthetic worker: zero real inference,
Minecraft or shared input. Native FINALIZED exit0 after49.366538s;15 settled
requests and one rejected old-helper resume;150 input/60 output tokens and210
synthetic units. Three participants/envelopes CLOSED.

Original34/34 and independent20/20 pass. The audit joins raw captures,
authenticated ingress/admission, exact catalog, settled receipts, post-fence
native status issuance/result, source-bound /2 drain, replacement, accounting,
all actual notification strings and exact image bytes. All40 real authority
tables, holds and consumed decisions remain unchanged; no owned process remains.

Private bundle `C:/Users/Darian/.strata/evidence/2026-09-24-m1-notification-drain-01`:
3,855 files/76,463,997 bytes; independently verified seal SHA-256:
`b6450cdd1f3effe48606a9a60d6574f5d89d7615e364ca5ef0a9eba4eac8fa78`.

200 focused cases pass across cell drain, retirement, broker lifecycle, stopped
export, checkpoint and selected-fixture verifiers. Tests preserve holds on
scalar-only forged status, scalar wait completion, pending cells and malformed
frames; real framed completion and owner cancellation pass despite notifications.
Full Ruff and whitespace pass.

```powershell
.venv/Scripts/python.exe -m pytest -q tests/test_native_cell_lifecycle.py tests/test_native_retirement.py tests/test_broker_lifecycle.py tests/test_native_export.py tests/test_native_checkpoint.py tests/test_native_state_boundary.py --tb=short
.venv/Scripts/ruff.exe check .
git diff --check
```

Next investigate held native process-tree drain for the ambiguous scalar path,
without treating kill-on-close configuration, a vanished parent PID or a model
message as proof. Cross-team/probe boundaries and all other G1 gaps remain open.
