# Authentic current-policy guardian failure

2026-09-20. Operator-only. M0.3b.2c.3c.2b.2b.2.2a; partial F09/F16,
N01/N03/N04/N05/N06/N08, C14/C15/C18 and T07/T12/T13. Result **fail**.
This sample does not close a test, milestone or gate.

After the [held-member implementation](2026-09-20-guardian-tree.md), a fresh
authentic E9E 1.27.0 / MC 1.19.2 / Forge 43.4.23 trial exercises ordinary worker
expiry under policy `job-call-wait-tree-qpc/2`. It uses Java 17.0.20.1,
Python 3.12.14, Node 24.19.0, the unchanged minor-34 client JAR
`b2a91155a7698d3ce6095ae7c4005827ea10c7f3623bfa086312f29d56916896`,
the current 34 compiled broker modules, pinned current operator sources and
installed telemetry 0.2.0. The source checkpoint is `e4edad7`. TypeScript build
passes before preparing fresh capability/authority fingerprints.

Server 600-second, client 480-second and worker 90-second lifetimes are
unchanged, as are the two 2,250 ms worker startup bounds and the shared 500 ms
root/tree wait. The client runs on the prepared non-input desktop. The public
checker makes exactly three scoped CLI reads: capabilities and two connected
observations. It requests no mutation. Ordinary safety release still occurs at
worker expiry; this is not a zero-cost gameplay or time-free intervention.
There is no shared-desktop input, inference, world restore or campaign admission.

## Actual result

The server is ready after 115.468 s. Client world readiness takes 171.328 s with
one successful identity read and zero read retries. Worker bootstrap is
757.9009 ms; initialization is 304.6950 ms. Both unchanged startup bounds pass.
The public read-only check passes. Two 854×480 frame captures decode and were
visually inspected: terrain, rain, vegetation, held item and HUD are present.
This is not universal first-frame or input/focus parity evidence.

At ordinary worker expiry, the executor exits normally with code zero. The
guardian requests job termination successfully, but its root process wait
returns **timeout**. The exact private QPC diagnostic is:

| Field | Observed value |
|---|---|
| Job call return after start | 0.8131 ms |
| Wait begins after start | 0.8143 ms |
| Wait returns after start | 511.6576 ms |
| Elapsed wait | **510.8433 ms** |
| Root wait result | `timeout` |
| Tree proof | `not_started`; member counts unavailable |
| Stop receipt | Absent |
| Guardian failure | `PROCESS_STOP_UNCONFIRMED` |

The supervisor records the timing, `guard_failed`, `guard_fault` and
`supervisor_fault` in a complete verified hash chain and exits one. It correctly
does not claim a confirmed stop from an eventual zero process count. The
independent read-only observer eventually sees the held Java process signaled;
its largest wait-call span is 196.3425 ms. Scheduling and observation delays
remain material. Eventual exit cannot reverse the failed 500 ms result.

The client exits 125 before outer cleanup; no desktop watchdog fires. The
client procedure finishes in 272.110 s with failure retained. The server saves
normally, exits zero in 388.188 s and retains complete logs. The paired driver
finishes in 388.718 s; its shell exit zero is **not** its verdict: its structured
result is fail because the client procedure exited one. Zero Java processes,
unchanged input desktop and retired private launch arguments are verified.

The telemetry stream has 261 records through tick 5,270, a validated clean stop
and six passing selected furnace assertions. It is not proof of player crafting,
full expert mechanics, telemetry isolation or complete resource accounting.

## Retained evidence and next action

External root: `C:\Users\Darian\.strata\evidence\2026-09-20-guardian-live-01`.
Its preparation/launch scripts, source and compiled pins, private arguments'
nonsecret expiry/digest receipt, native/public observations, frames, current
client logs, server logs, supervisor chain, read-only exit observer, telemetry
and audit remain private. No cache/token contents were printed or published.
The exact audit SHA256 is
`3844bc351ca8794d7a9f4f0fba3a7c5c870fa1a2b7a59964685e2b02605ffb08`.

The post-stop audit reports the stop-bound, complete-handle and separate-receipt
checks as fail, alongside passing startup, public-read, journal, normal-server
stop, source-pin, cleanup and selected telemetry checks. An initial PowerShell
quoting error occurred during preparation, before launch; an explicit file patch
and compile check corrected it. No attempted game run was erased or repeated.

Earlier 501.9950/503.5059/507.6092 ms timeouts, the separate 503.6561 ms late
signal and the one 451.9577 ms prior-policy pass remain historical evidence.
This new failure does not justify another unchanged repeat or a larger deadline.
GI/QA must diagnose authentic process cleanup/scheduling against the same bound
and qualify complete inventory/launch containment on a concrete supported
profile. Continue independent native settings/mechanic work. G0 remains fail;
G1–G5 remain not_run, and production monetary/exposure/isolation are still open.
