# M0 bounded native heap and shutdown diagnostic

September 21, 2026. Operator-only. M0.3b.2c.3c.2b.2b.2.2a.1;
F09/F16, N03/N05/N06/N08, C14/C15/C18, partial T07/T12/T13 and G0.
M0 remains incomplete; G0 fails and G1–G5 are not run.

The [protected craft reference](2026-09-21-process-history.md) retained a
500.1327-ms guardian failure corroborated by an independent observer. Earlier
memory correlations and the failed periodic-G1 profile did not establish its
cause. This change supplies a finite native heap diagnostic before another game
profile is considered. Production guardian code and its 500-ms bound are unchanged.

## Implemented behavior

[probe_guard_memory.py](../../tools/probe_guard_memory.py) launches only the
disposable [Java fixture](../../tests/fixtures/GuardianMemoryFixture.java) through
the existing no-breakaway, kill-on-close bootstrap. The production `AttachedJava`
guardian attaches to a verified member before allocation. The fixture retains
16-MiB arrays, touching every 4-KiB page, then blocks on its private input pipe.
It has no game, graphics, network, credential or desktop-input behavior.

The operator supplies one to three distinct loads, each at most 3,072 MiB.
Every case has a 45-second independent owned-tree watchdog. Admission requires
room for the declared maximum heap plus 2 GiB for native overhead and 8 GiB of desktop
headroom against both available physical memory and commitment. Memory is checked
again while awaiting fixture progress. These are conservative diagnostic checks,
not an OS reservation or a guarantee against concurrent external allocation.

Fresh private output and durable pre-dispatch intent prevent accidental same-path
replay. Exact runtime/module, fixture and supervisor source hashes are retained
and rechecked. Original guardian results survive later cleanup. A failed wait,
stop or inventory still closes the owned Job and preserves failure evidence;
incomplete cleanup prevents the next sample. Completed measurement is explicitly
distinct from a passing stop result. No source or capability is admitted for
Minecraft based on this tool's output.

Memory readings use the already held identity handle and documented
[GetProcessMemoryInfo](https://learn.microsoft.com/en-us/windows/win32/api/psapi/nf-psapi-getprocessmemoryinfo)
and [GlobalMemoryStatusEx](https://learn.microsoft.com/en-us/windows/win32/api/sysinfoapi/nf-sysinfoapi-globalmemorystatusex).
No foreign PID is discovered for termination, and process arguments are not read.

## Executed evidence

Windows x64 / Python 3.12.14 / installed Temurin JRE 17.0.20.1+1, compiled with
the pinned JDK 17 and `--release 17`. Private bundle:
`2026-09-21-guardian-memory-native-01`. Initial headroom was approximately
37.2 GB physical and 28.0 GB commitment. Sequential cases used G1,
`-Xms64m`, and `-Xmx(load + 512)m`; these are declared synthetic profiles,
not the Minecraft JVM argument set.

| Retained arrays (MiB) | Resident bytes | Private bytes | Root wait (ms) | Complete tree proof from wait start (ms) |
|---:|---:|---:|---:|---:|
| 256 | 323,612,672 | 527,278,080 | 15.7207 | 15.8761 |
| 1,536 | 1,736,949,760 | 2,330,337,280 | 63.8385 | 63.9651 |
| 3,072 | 3,409,104,896 | 4,007,219,200 | 131.1098 | 131.2826 |

All three complete the unchanged 500-ms proof, with one guardian member and
four outer retained/signaled members per case. No watchdog fired, no cleanup
error occurred, all source pins match, and the independent final process query
found no Java. The evidence re-audit checks each bound and full terminal equality.
Compilation, intent, individual results, summary, archived sources and audit are
retained privately. No Minecraft or model call occurred and no shared input was used.

`pytest -q tests/test_guard_memory_probe.py`: **11 pass / 0.13 seconds**.
Checks cover invalid/repeated/unbounded loads, both memory constraints and
cleanup failure with preserved evidence and mandatory Job closure. Focused Ruff
passes. This is new diagnostic coverage; the previous 91 process-history checks
were not repeated.

The final private manifest verifies 19 files / 67,420 bytes; SHA-256
`d27c07f05b1965d21f104614f08cf3f71be70d1d2be8ea0183d8f007f105d708`.
Source validation retains 290 unique milestone IDs, checks 1,043 local links in
the affected status/report files and preserves the previous append-only log.

## Interpretation and next action

These three native synthetic workloads did not reproduce the authentic failure.
Larger retained heap increased shutdown time within this small fixture; this is
not a causal model or reliability qualification. The largest case has less private
memory than the failed Minecraft process and omits native graphics, game I/O,
its actual thread/resource population and the loaded server. Do not infer that
heap can never contribute or that a lower game heap would fix the failure.

Next inspect the already available separate-desktop OpenGL fixture and native
resource teardown path to select a finite discriminating case. Make a relevant
source or declared profile change before any further authentic game trial.
Preserve every failed 500-ms sample, five effective-file failures, Mineflayer/E9E
incompatibility, sibling-read/loopback failures and all remaining scorer/setup,
provenance and recovery gates. Original $10 model authority and the unresolved
$0.7554 reservation remain; no replay, settlement, refund or reset occurs here.
