# Connected native/game failure cleanup — September 23

Scope: **M0.1d.9b**, under M0.1d.9; F03/F06/F09/F11/F16,
N01/N02/N04/N06, C06/C12/C20, partial T01/T03/T04/T07/T12/T13,
G0 items 1/4/6. M0 remains in_progress and G0 fail. D14's full isolation
deferral and D18's continuing original-budget approval remain unchanged.

The D18.4 paid pilot received an incomplete response and subsequently forced
worker cleanup. The source correction drains the worker before rejecting
accounting closure. This control exercises that ordering with the pinned
native Codex/Dovetail loop, authentic vanilla Minecraft and the existing sealed
Mineflayer worker. Its model provider is a fixed local script, using GPT-6 Luna
as the native catalog identity. It makes **zero actual model requests**.

## Changed behavior

`tools/m0_native_game.py` accepts the separate `M0NativeGameFailure/1` plan.
It keeps the sealed launch/profile and fresh imported baseline requirements,
selects zero helpers and the fixed producer in
`tools/native_game_failure_probe.py`, and retains the existing 90-second native
bound. The local provider permits at most four synthetic dispatches. It must
receive the native observation acknowledgment before emitting HTTP 200 with a
started response and a truncated terminal frame, without a usage receipt.

Complete observations remain in the broker journal. The acknowledgment uses
only observation ID and connected state, so a large observation cannot destroy
its JSON marker through native output truncation. It supplies no action target
or private game state. This is a fixed fault control, not gameplay reasoning.

The shared transport must preserve the partial wire and typed diagnostic;
accounting must retain the unknown reservation and refuse closure. The driver
drains Mineflayer before reporting that refusal, stops the server normally and
retains stopped world evidence. It does not register or publish a resumable
joint checkpoint. Negative-control assertions are separate from the failed
native/game result. The original budget database is read only; synthetic
accounting lives in its own permanently simulated store.

## Verification

The initial test collection found an invalid import of `OPERATOR`; corrected
to the existing `Principal` API before execution. The focused selection passed
169 cases:

```text
pytest tests/test_native_game_failure_probe.py tests/test_worker_stop.py tests/test_native_game_retention.py tests/test_sealed_native_game.py tests/test_inference_transport.py tests/test_native_oauth.py -q
```

Two defensive pre-launch changes then passed the affected 50-case producer and
worker-stop selection. The subsequent compact-acknowledgment regression executes
the actual generated JavaScript in Node against a large synthetic observation;
all 11 producer/profile cases pass. This totals 170 distinct focused cases,
not 230 different cases. Changed-file Ruff and diff checks pass. No full-suite,
new paid-pilot or Java-profile pass is claimed.

Case01 is retained as **fail**. Two authentic observations settled, but the
full second observation exceeded native output limits and its trigger marker
was no longer parseable. The producer therefore refused before injecting the
intended partial response. One synthetic dispatch settled and the next remained
unknown; closure was refused. The worker drained normally in 23.3816 ms
(109-ms owner interval), and all 45 outer processes became terminal without
forced termination. The independent audit passes 40/47 checks, not the intended
fault-control gate. Original authority and template are unchanged.

Its private archive is `2026-09-23-native-failure-live-01`: 3,912 files,
120,720,698 bytes; seal
`c5744ed01645df5624018f2da197283f1ea20c631ce21bd1822eee1cb2d97b9a`.
Retain both preregistration versions and the first audit script's missing-trigger
assumption; the corrected read-only audit records the actual failure.

Case02 **passes all 47 independent negative-control checks**. The deliberately
failed native/game result remains `PILOT_NATIVE_CLOSURE`; native exit is 1 and
closure is UNSETTLED/METERING_UNKNOWN. Two authentic observations settle. Of
three incoming local requests, two reach the scripted upstream: one settles
for 14 fixture units; the second has the exact 281-byte partial SSE capture.
The third is durably refused before dispatch for METERING_UNKNOWN. The shared
transport records `receipt_validation` / `TRUNCATED_EVENT_STREAM`, 14 ms elapsed
under its 3,000-ms deadline. No unknown request is replayed or settled.

The unknown child retains its 10,000-unit reserve inside the still-open
40,000-unit synthetic parent envelope. The envelope's four reserved model-call
units are not four actual dispatches, and these fixture units are not dollars
charged to the original account. There are zero actions/primitives and no
helpers. The root accounting participant remains unresolved; the native process
has exited and the game lane is STOPPED.

Mineflayer drains in **26.2379 ms** (110-ms owner interval), within the existing
2,250-ms worker drain policy. Server stop-to-exit is 1,718 ms. All **45 outer
processes** become terminal with zero forced termination, complete logs and
normal worker/server driver exits. Native duration is 14.126180 seconds;
outer duration is 141.469 seconds. The stopped snapshot's 26 state files /
13,587,704 bytes are independently reverified. These measured intervals do not
qualify authoritative game/avatar clocks or the distinct Java-tree policy.

All 39 original accounting tables and the template remain unchanged; all 150
preregistered runtime/source pins match execution. Private archive
`2026-09-23-native-failure-live-02` contains 3,910 files / 120,806,602 bytes:

- Seal: `53a6d12b59d0ef63341a3733d418c610179e394751c28249b0d085c08eea6fa4`.
- Independent audit: `d1813bf506285d5424b557859a9618d4da126503a622b1db5a106f0ebdc570b6`.
- Partial response: `6063b311d466c0c3027ec99f00df5a5c38d4df9fd1af7c837b080d7af6572e20`.

M0.1d.9b is **verified only for this fixed failure-control scope**. Preserve
case01 and the original D18.4 failure. Do not repeat case02 unchanged.

## Limits

This control does not settle, replay or identify the exact upstream interruption
cause of D18.4. Its local synthetic OAuth transport shares the response parser,
failure diagnostics and durable dispatch path; it does not exercise the paid
gateway's external TLS endpoint or demonstrate a successful model-selected
walk. Unsettled native participants retain their ACTIVE accounting row while
the native process is terminal and the worker lane stopped; that is retained
uncertainty, not permission to reuse the run.

The original $0.7554 hold, settled valuations and new unresolved $1 job envelope
remain unchanged at $1.795559 aggregate committed/reserved exposure. New paid
admission remains blocked by unknown usage, with no user approval pending.
Authoritative clocks, complete save custody, full scorer/setup continuity,
exact E9E profile qualification and the other G0 gaps remain open. Preserve
M1–M7; do not repeat an unchanged successful control.
