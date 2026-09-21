# M0 silent OpenAL shutdown discrimination

September 21, 2026. Operator-only. M0.3b.2c.3c.2b.2b.2.2a.3;
F09/F16, N03/N05/N06/N08, C14/C15/C18, partial T07/T12/T13 and G0.
M0 remains incomplete, G0 fails and G1–G5 are not run.

The [graphics/heap cases](2026-09-21-guardian-native-graphics.md) did not reproduce
the authentic 500.1327-ms failure. The stopped client log identified another
native subsystem absent from those fixtures: OpenAL. This change extends the
same finite fixture to hold a silent, live audio stream during forced stop.
It is diagnostic implementation and native synthetic evidence, not a game fix.

## Implemented behavior

[GuardianRenderFixture](../../tests/fixtures/GuardianRenderFixture.java) version 2
binds an explicit audio Boolean into both boot and ready records. When enabled,
it opens its default OpenAL device/context, creates a zero-filled 0.1-second mono
PCM buffer and loops it with **source gain zero**. It checks the source remains
playing, gain stays zero and native AL/ALC errors are absent before readiness.
Only the fixture's source is controlled; no capture device, system-volume setting
or other application's audio is changed. Normal cleanup releases only its own
source, buffer, context and device. Forced-stop measurements occur while those
resources remain live; a later normal fixture expiry remains a failure.

[probe_guard_graphics.py](../../tools/probe_guard_graphics.py) policy
`held-hidden-gl-silent-al/3` adds fixed `context-audio` and `combined-large-audio`
profiles. It requires exact process/scope/load/audio binding and live silent-source
evidence before invoking the unchanged production guardian. Numeric Boolean
substitutes, missing/empty native identity, stopped source, nonzero gain or missing
PCM evidence reject. Private OpenAL logs retain the actual backend initialization.
No audio driver override was set or game resource profile changed.

Existing admission, 8-GiB desktop memory margin, GPU headroom, at-most-three distinct
profiles, fresh non-input desktops, private native extraction, 45-second outer
watchdog and complete held-process cleanup remain. The guardian still has exactly
500 ms; successful later cleanup cannot erase a failed measurement. Historical
fixture-v1/policy-1/2 artifacts remain tied to their original dispatch sources.

## Executed verification

Private bundle `2026-09-21-guardian-audio-native-01`, Windows x64 / Python 3.12.14 /
Temurin JRE/JDK 17.0.20.1+1. Two existing pinned LWJGL 3.3.1 OpenAL JARs extend the
previous seven-artifact classpath; no download or broad Forge build occurred.
Runtime reports **OpenAL 1.1 ALSOFT 1.21.1 / OpenAL Soft**. Both logs identify
the **WASAPI** backend. Exact device strings, source/compiled/runtime hashes,
intents, ready reports, timing, logs and independent audit stay private.

| New profile | Heap / textures (MiB) | Private bytes | Root wait (ms) | Complete tree proof from wait start (ms) |
|---|---:|---:|---:|---:|
| context-audio | 0 / 0 | 245,514,240 | 24.1664 | 24.2821 |
| combined-large-audio | 3,072 / 1,024 | 5,888,827,392 | 261.7210 | 261.9040 |

Both cases pass their individual 500-ms criterion. Each has one guardian member,
two retained/signaled outer members and zero active processes. No watchdog or
cleanup fault occurred, no normal fixture terminal report exists, input desktops
were unchanged and all dispatch source pins match. The final independent process
query found no Java. Previous graphics-only cases were not repeated.

`pytest -q tests/test_guard_graphics_probe.py`: **27 pass / 0.25 s**, with private
JUnit output. These include the previous 18 cases plus nine audio binding/silence/
readiness negatives; do not count overlap as extra unique coverage. Focused Ruff
and native compilation pass. Original guardian code and its acceptance thresholds
are unchanged. No Minecraft, inference, shared input or new allowance was used.

The private manifest verifies 40 files / 4,767,711 bytes; SHA-256
`7e4eb937abaefae287172a18e6d4c325eae78c45b1a9895ae4e42772f3120811`.
Final source validation preserves the append-only log, 292 unique milestone IDs
and 1,049 local links in the changed status/report files. A fresh read-only
transaction on the original accounting store confirms schema 2, one migration,
the same $10 cap and $0.7554 unresolved exposure counted once.

## Conclusion and next implementation

Silent WASAPI audio with these bounded graphics/heap allocations did not reproduce
the game failure. The loaded case's 5.89-GB private allocation is near the authentic
client's 5.87-GB pre-stop observation, but equal allocation totals do not establish
equivalent threads, memory mappings, I/O, native driver activity or CPU contention.
The earlier 5.68-GB observation was during teardown and remains labeled as such.
No disabling of game audio, relaxed stop bound or inferred remedy is justified.

Next implement bounded operator-only resource snapshots from the held owned
process: CPU time, I/O, handle counts and aggregate memory-region observations.
Integrate them into the independent observer, outside the guardian's stop path;
measure observer overhead with owned fixtures before a specifically changed
authentic trial. This will compare the actual loaded process with the now-retained
resource cases instead of repeating unchanged synthetic/game profiles. Do not
block or postpone termination for snapshot completion, expose memory contents or
credential-bearing paths, or promote incomplete observation to a passing result.

All original guardian failures, five effective-file failures, Mineflayer/E9E
incompatibility, sibling-read/loopback failures and remaining scorer/setup,
provenance and recovery requirements persist. Original model authority and the
unresolved $0.7554 hold remain; no replay, settlement or refund occurred. Required
M0–M6 and conditional M7/extensions remain intact.
