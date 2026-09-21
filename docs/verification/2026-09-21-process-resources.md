# M0 bounded independent process observation

September 21, 2026. Operator-only. M0.3b.2c.3c.2b.2b.2.2a.4;
F09/F16, N01/N03/N04/N05/N06/N08, C14/C15/C18, partial T07/T12/T13/G0.
M0 remains incomplete, G0 fails and G1–G5 are not run.

The authentic protected craft reference still fails shutdown at 500.1327 ms.
This change supplies missing resource evidence for diagnosing that failure.
It does not fix or waive it. No game, model request or shared-desktop input ran
for this change.

## Implementation

[process_resources.py](../../src/mcbench/process_resources.py) opens a separate,
identity-checked read-only handle to the already owned native x64 process.
It adds QUERY_INFORMATION for aggregate metadata, with no VM_READ, memory
contents, mapped filenames, environment, command lines or process mutation.
Guardian handle rights and its 500-ms threshold remain unchanged.

`PrivateProcessResources/2` records CPU and I/O counters, handle count,
working/private memory, and a non-atomic census of committed private/mapped/image,
reserved and free regions. Cumulative 64-bit CPU/I/O values are decimal strings.
Native failures retain their error codes. Undefined free-region fields are
ignored; coalesced regions count only the unvisited suffix. Allocation addresses
stay internal and cannot double count observed allocation bases.

Each sample has a 25-ms query budget checked between native calls. An individual
kernel call cannot be preempted; measured overruns stay partial. The census
continues from its cursor at the next 1-Hz sample, with **8,192 total regions,
eight segments and eight seconds maximum per census**. It never restarts the
prefix within a census or silently extends its bounds. Completion records the
whole observation interval; it is not an instantaneous memory snapshot. Exit,
quota, API failure and expiry retain the partial prefix. Terminal process
counters remain distinct from live allocations.

[process_observer.py](../../src/mcbench/process_observer.py) policy
`held-process-qpc-exit-resources/3` places resource queries in their own thread
with their own handle. Independent exit waits and incremental supervisor-journal
tailing cannot wait for the resource sampler. Observation has finite 480-second,
512-sample and journal-size bounds. Finalization allows two seconds total;
a timeout remains failed even if the thread later completes. Each owning thread
closes its own handle and durably closes its journal. Lifecycle status and counts
of complete counters, complete region censuses and partial observations are
separate. Observer failure cannot modify a guardian verdict.

[probe_guard_graphics.py](../../tools/probe_guard_graphics.py) policy
`held-native-resources-census/5` adds opt-in observation and a fixed five-second
hold. The existing fixture, allocation/headroom, silent audio, non-input desktop,
45-second outer deadline and 500-ms guardian remain. Source pins include both
observer modules. The probe joins observers only after termination and cleanup.
The gameplay package exclusion check passes; no gameplay tool is added.

The Windows metadata interpretation follows Microsoft's
[VirtualQueryEx](https://learn.microsoft.com/en-us/windows/win32/api/memoryapi/nf-memoryapi-virtualqueryex)
and [MEMORY_BASIC_INFORMATION](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-memory_basic_information)
contracts. Mapped/image copy-on-write pages retain those classifications;
these categories are not an independent resident-memory measurement.

## Executed verification

Private bundles `2026-09-21-process-resources-01` and `-02` retain exact dispatch
sources, plans, JSONL, JUnit results, audit and original failures. Windows x64,
Python 3.12.14, Temurin 17.0.20.1+1, RTX 3090/NVIDIA 591.86 and the existing
LWJGL/OpenAL fixture-v2 artifacts were used. No new dependency installation.

Focused checks: 54 pass in the resources/observer/graphics/package selection;
three existing guardian identity/stop checks pass; a later observer-only run
passes nine, including four new summary-classification cases. **61 distinct
checks**, without adding overlapping reruns. Ruff passes. An actual owned JVM
rejects termination through the metadata handle (Win32 access denied 5).
Another actual guardian stops while its metadata sampler is deliberately
blocked; bounded observer finalization fails and remains failed after release.
Synthetic tests cover census continuation, whole-census quota/expiry, partial
exit, identity/API failure, coalescence, incomplete journals and durable closure.

Three finite native cases used the same 3,072-MiB heap, 1,024-MiB textures,
silent WASAPI stream and five-second hold:

| Observation policy | Complete tree proof (ms) | Parent CPU (ms) | Whole case wall (ms) | Region evidence |
|---|---:|---:|---:|---|
| Baseline, no observer | 322.8981 | 203.125 | 7,919.9502 | Not collected |
| Original full walk per sample | 320.1987 | 296.875 | 8,101.8502 | All six live walks partial |
| Incremental census | 294.1257 | 421.875 | 8,088.9178 | Three complete censuses |

These are single cases, not a statistical overhead bound or an authentic game
qualification. Both retained outer processes terminated in every case, input
desktops stayed unchanged, source pins matched, and no watchdog or cleanup
fault occurred. The original observer exceeded 25 ms on every live region walk.
Its raw audit incorrectly counted six live observations as complete; a separate
hash-bound `native-comparison-erratum.json` corrects that count to **zero** without
overwriting the original audit or raw evidence. Shutdown results are unchanged.

The changed census case has six complete live counter samples (maximum counter
query 0.3067 ms), three complete two-segment censuses spanning about 1.023–1.025 s,
three partial prefix samples and one terminal counter sample. Maximum sample
wall time is 25.0856 ms; observer thread CPU totals 109.375 ms at Windows' coarse
CPU-accounting resolution. The first two censuses finish before stop; the third
overlaps forced teardown despite the process not yet being signaled. Its lower
allocation total is **not** a pre-stop memory reading. The first census observes
1,588 regions/483 allocation bases; all observations remain non-atomic.

A read-only transaction on the original accounting store retains schema 2, one
D11 migration, the original $10 cap and $0.7554 unresolved exposure counted once.
No inference receipt, settlement, refund or new allowance was created. Independent
process inspection after the cases found no Java processes.

The combined private manifest verifies 71 files / 7,234,905 bytes; SHA-256
`e20498cf33d40ec4c820d6ca99584334e3d39e49cc8149c6f3c1769b4f32ce78`.
Source validation preserves the entire prior append-only log and all prior
milestone IDs (293 total now), and resolves 1,091 local document links.

## Next M0 action and remaining gates

Connect the new observer to one freshly registered protected reference using
the original unplayed fixture lineage and fresh authority/source pins. Compare
pre-stop region density, CPU/I/O and the independently observed exit with these
retained fixtures. Keep observations spanning shutdown labeled separately.
Do not replay a consumed scope, restore its progressed world, extend a deadline
or infer that matching private-byte totals identify the failure's cause.

Authentic observer integration, the shutdown remedy and full production resource
qualification remain unverified. All previous 500-ms failures, five effective-file
failures, Mineflayer/E9E incompatibility, sibling-read/loopback failures and scorer,
setup, provenance and recovery requirements remain. Required M0–M6 and conditional
M7/extensions are unchanged.
