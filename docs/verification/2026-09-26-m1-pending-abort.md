# M1.5b.8b: pending early-abort delivery

The operation10 failure exposed a concrete coordinator defect: a single early
monitor exception could precede creation of the server evidence directory.
Healthy subsequent iterations never delivered its pending abort. Delivery
occurred only at the later hard deadline. The original sealed failure and its
unqualified29-held/27-signaled history remain unchanged.

`reference_pair.py` now retains the first durably recorded failure and checks
for the server-owned directory on subsequent monitor iterations, before
participant admission. It publishes the original phase/type/code when possible.
Deadlines still shorten only once and never extend. Publication is attempted
at most once, including failure before writing or an ambiguous exception after
writing; no replacement or retry is allowed. The hard watchdog remains active.

`processes.py` adds private `ProcessInventoryObservation/2` only when an
attempted incomplete-list reconciliation rejects a known predicate. The five
bounded reasons distinguish an unretained list entry, lifetime-total mismatch,
assigned count beyond history, active count outside history and limit
termination. No PIDs, paths, command arguments or exception messages are exposed.
All qualification predicates, strict-default behavior, handle ownership, API
errors and quotas remain unchanged. Existing observations retain version1.
This does not explain operation10 retroactively or convert uncertainty to a pass.

## Focused verification

Windows x64, Python3.12.14 and the existing pinned Temurin17.0.20.101 fixture
profile; no Minecraft or model dispatch. Commands executed:

```text
.venv/Scripts/python.exe -m pytest tests/test_process_history.py tests/test_processes.py -q
.venv/Scripts/python.exe -m pytest tests/test_reference_pair.py -q -k "single_early_fault or monitor_fault_is_durable or failed_first_monitor or independent_deadline"
.venv/Scripts/python.exe -m pytest tests/test_reference_pair.py -q -k single_early_fault
.venv/Scripts/ruff.exe check src/mcbench/processes.py evaluator/src/strata_evaluator/reference_pair.py tests/test_process_history.py tests/test_reference_pair.py
```

The first two selections pass49 and8 cases:57 distinct passes, including12 new
cases. Tests cover all five reasons, rejection of unstructured/mismatched
diagnostics, unchanged no-retry/ownership semantics, durable diagnostics before
abort, and independent deadlines. The8 pair cases use actual owned Windows/JVM
fixtures with synthetic faults; these are not authentic game acceptance.

The final3-case selection adds terminal-history assertions and archives exact
pair results in JUnit properties. All3 pass. Normal delayed-directory delivery
has complete terminal proof and no forced outer cleanup. Before-write and
after-write failures remain uncertain with exactly one publication attempt.
JUnit emits3 existing-format compatibility warnings for `record_property` with
`xunit2`; properties are present and verified in the retained XML. No rerun was
made to suppress warnings. Ruff passes.

## Scope and remaining work

M1.5b.8b is `implemented_unverified` for the authentic game profile. This is a
required M1.5b.8/.8a cleanup dependency: F09/F16, N01/N04/N05/N08, T01/T10 and G1;
it does not start the unrelated G2 recovery/soak roadmap. No acceptance threshold,
time bound, permission, gameplay action, source installation or budget changes.

Next perform a fresh changed-coordinator reference to verify declared telemetry
capacity, complete interval/retirement capture and settlement. Preserve the
operation10 consumed launch, stale inner states and256 MiB RESERVED hold; never
rearm or repair them into passing evidence. The original inventory cause is
unknown. The new diagnostic will distinguish failures if encountered, without
seeking an unchanged lucky rerun.

Full native-host/isolation, T05 keybinding, T10 scoring controls and T11 probe
contracts remain open. M1 stays `in_progress`; G1 stays `not_run`. All40
controller accounting tables remain unchanged at4,887,796microUSD, with D18/D19
still M0-only. Private evidence root:
`C:/Users/Darian/.strata/evidence/2026-09-26-m1-pending-abort-source-01`.

Final audit passes:453 unique milestone IDs with all historical IDs retained,
append-only progress,1,908 valid local links, both original operation10 seals
verified and no owned runtime. Evidence seal:27 files/2,358,544 bytes,
SHA256 `bb00a1bf5d0761657282d2af1f96593867279efbfa70e847b6147ec411f0e6e2`.
This pointer was appended after the archived documentation snapshot.
