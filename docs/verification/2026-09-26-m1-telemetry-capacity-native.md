# M1.5b.8/.8a operation10: startup monitor failure

Operation10 fails before participant dispatch. The launch8/protected3 profile
does durably reserve its declared 256 MiB telemetry spool capacity before native
server dispatch. Complete interval capture, retirement and successful settlement
remain unverified. G1 remains `not_run`.

Source299da94 uses unchanged telemetry0.3.18/startup19 (061712ce), client
minor45/policy4 (31facc27), two-item checker and prior interval/transition
criteria. All563 pair inputs were verified before launch; the8,609-file source
was reused without changing bytes. Finite capacity is268,435,456 bytes and100,000
events. Time/action bounds were unchanged. No model calls or shared-desktop input.

## Actual failure and custody

The first monitor observation reports PROCESS_MEMBER_INVENTORY_UNAVAILABLE:
12 assigned,11 listed and12 retained processes, stage `incomplete_list`.
The diagnostic does not record which independent-history reconciliation
predicate failed; equal assigned/retained counts alone cannot qualify history.

The outbox retains this failure at cursor6, during writer preparation. Later
events continue through bound/copy/hold, sealing and server dispatch. The
consumed launch reservation is cursor13, telemetry reservation14, dispatch
intent15, DISPATCHING17 and RUNNING21. The pair never dispatches the client.

The abort file contains the later REFERENCE_PAIR_HARD_DEADLINE failure, rather
than the original inventory fault. Source inspection identifies a concrete
pending-abort delivery defect: publication is attempted only in the exception
handler when the server evidence directory already exists. If that directory
appears after a single early fault, successful subsequent observations do not
publish the pending abort. This explains the observed delayed delivery path;
the underlying inventory anomaly remains undiagnosed.

At187 seconds the pair is uncertain and forced cleanup reports exit125,
29 held processes,27 signaled, zero active and29 total. Terminal history is
**unqualified**. A later empty OS inventory is supplementary and cannot repair
the missing retained-handle proof. No guardian timing or clean-save claim.
Client/server/protected result files are absent; no authenticated telemetry
stream exists. There were zero client actions.

Durable rows remain exactly as found: pair UNCERTAIN, protected DISPATCHING,
dispatch RUNNING; the one-use craft launch remains consumed. The256 MiB logical
spool reservation stays RESERVED with no actual-byte settlement. Stale inner
states are unresolved, not evidence that a process remains alive, and are not
rewritten or replayed. No capacity is refunded. The unused client session
argument file was verified against its prior pin and retired after confirming
no client dispatch; its credential bytes were neither copied nor printed.

## Verification and next action

The actual stopped audit command was:

```text
.venv/Scripts/python.exe C:/Users/Darian/.strata/evidence/2026-09-26-m1-furnace-operation-10/audit_startup_failure.py
```

It passes the failure-preservation, durable-state, capacity-hold, no-client,
credential-retirement and accounting checks. This is an audit pass of a failed
native reference. The staged positive operation/processing/transition/interval/
capacity/terminal scripts were not run and confer no evidence.

All40 controller authority tables remain unchanged at4,887,796microUSD. D18/D19
remain M0-only. Preserve operation09's quota failure, all earlier failures,
consumed decisions and budget holds.

Next repair pending early-abort delivery and add bounded reconciliation-failure
diagnostics without changing process qualification or retrying an incomplete
inventory. Verify the early-fault/late-directory path with focused tests before
selecting another changed-profile native reference. Full T10 scorer controls,
isolation/native-host/keybinding/probe acceptance remain open. M1.5b.8 and
M1.5b.8a are `in_progress`; no full M1/G1 completion claim.

Private evidence roots: `2026-09-26-m1-furnace-operation-10` and
`2026-09-26-m1-telemetry-capacity-native-preparation-01`, under the operator's
external evidence storage. No private records are committed.

Seals verified after the final audit (815 unchanged source pins,452 preserved
milestone IDs,1,741 valid local links): operation10 contains441 files/80,006,050
bytes, SHA256 `3928935328a52a4a58f7f2f895be65be375a3187d73caa56a08d7a07fdf87b97`;
preparation contains17 files/3,351,124 bytes, SHA256
`1d2fa2e329ad6c25fdbeb59a769440fe2e878585ddc7c246810a0377b171b9ab`.
This seal pointer was appended after the archived documentation snapshot.
