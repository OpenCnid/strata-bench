# M0 native graphics shutdown discrimination

September 21, 2026. Operator-only. M0.3b.2c.3c.2b.2b.2.2a.2;
F09/F16, N03/N05/N06/N08, C14/C15/C18, partial T07/T12/T13 and G0.
M0 remains incomplete; G0 fails and G1–G5 are not run.

The [heap fixture](2026-09-21-guardian-native-memory.md) did not reproduce the
authentic guardian failure. The existing `DesktopRenderFixture` releases graphics
resources before exiting, so it cannot measure forced termination with those
resources still held. The new [GuardianRenderFixture](../../tests/fixtures/GuardianRenderFixture.java)
reuses its hidden OpenGL setup and exact pixel checks, then retains the context,
declared textures and optional heap for the unchanged production guardian to stop.
The original renderer and production guardian are unchanged.

## Implementation and bounds

[probe_guard_graphics.py](../../tools/probe_guard_graphics.py) accepts one to three
explicit, distinct profiles from a fixed list. Each has a fresh non-input desktop,
no inherited handles, exact environment, an owned Job established before resume,
a 45-second outer watchdog and the original 500-ms guardian proof. The source-bound
fixture publishes a scoped boot record; only after guardian attachment does the
operator arm initialization. Ready evidence binds PID/scope/load and 20 successful
pixel samples. A boot record, wrong process, visible window, resource retirement,
missing GPU headroom or failed fixture cannot substitute for readiness.

The 64×64 window is hidden and unfocused throughout. Rendering is paced at roughly
60 Hz. Optional textures are sixteen or sixty-four 2048×2048 RGBA8 images uploaded
from a nonzero patterned buffer, with dimensions/errors checked and `glFinish`
before readiness. Optional 3,072-MiB heap arrays have every 4-KiB page touched and
remain strongly referenced. The fixture continues rendering until forced stop;
its own 20-second post-readiness expiry records failure and releases resources.

CPU memory checks reuse the previous probe's 8-GiB desktop margin and finite heap
plus native-overhead allowance. Texture profiles additionally require the actual
context's `GL_NVX_gpu_memory_info` and at least 2 GiB free after loading. The
[extension specification](https://registry.khronos.org/OpenGL/extensions/NVX/NVX_gpu_memory_info.txt)
defines approximate current-availability observations; these are not reservations
or exact residency guarantees. Unsupported or insufficient headroom rejects.
This profile is specific to available hardware, not portable capacity qualification.

Private evidence retains durable intent, source/runtime/JAR hashes, ready payload,
actual memory observations, original guardian timing and separate late cleanup.
Cleanup errors still close the owned Job and stop subsequent profiles. A failed
500-ms result remains failed even if later cleanup succeeds. No desktop switch,
input injection, Minecraft, model call or account cache is involved. New fixture
classes are outside mod artifacts and gameplay tools.

## Actual verification

Windows x64, Python 3.12.14, Temurin JRE/JDK 17.0.20.1+1, pinned LWJGL 3.3.1 and
Gson 2.8.9. Seven existing JARs supply the minimal fixture classpath; no downloads
or broad Forge build were needed. Native context reports NVIDIA GeForce RTX 3090,
OpenGL 3.2.0 NVIDIA 591.86. The initial CPU headroom checks pass.

| Profile | Heap / textures (MiB) | Private bytes | Root wait (ms) | Complete tree proof from wait start (ms) |
|---|---:|---:|---:|---:|
| context | 0 / 0 | 241,774,592 | 22.5313 | 22.6607 |
| textures | 0 / 256 | 701,452,288 | 44.5904 | 44.6925 |
| combined | 3,072 / 256 | 4,559,421,440 | 172.3803 | 172.4791 |
| combined-large | 3,072 / 1,024 | 5,892,354,048 | 249.2631 | 249.3811 |

The first three cases are private `2026-09-21-guardian-graphics-native-01`, policy
`held-hidden-gl-textures-heap/1`. All were terminal before adding the larger fixed
profile and explicit selection under policy `/2`. Only `combined-large` ran in
`2026-09-21-guardian-graphics-native-02`; no previous case was replayed. Both
versions' exact sources, compiled classes, inputs and results are preserved.

Each case has one guardian member and two outer retained/signaled members, zero
active processes, no watchdog/cleanup fault, unchanged input desktop and matching
source pins at its audit. No normal fixture `terminal.json` exists, consistent
with resources remaining held until forced stop. A final process query confirms
no Java. GPU availability declined by approximately the requested texture size:
the larger profile reports 21,937,852 KiB before and 20,889,532 KiB loaded.
All samples pass only their individual synthetic workload's 500-ms criterion.

Final `pytest -q tests/test_guard_graphics_probe.py`: **18 pass / 0.21 s**, with
private JUnit output. These include wrong binding/readiness/headroom, forbidden
profile selection, retained late failure, cleanup faults and mandatory closure.
Earlier runs passed 15 then 17 overlapping cases; do not add them to the total.
Initial Ruff rejected two semicolon statements before tests; split statements
fixed that lint issue. Final focused Ruff and native compilation pass.

The combined private inventory verifies 71 files / 4,976,491 bytes, manifest SHA-256
`cb2a9f503ded5dc79317199438a1a82bb54d55aaa2b9d0b337e9bd58bf3fad12`.
Each policy's archived dispatch sources match its original pins. Final source
validation preserves the append-only log, 291 unique milestone IDs and 1,046
local links checked in the changed ledger/status/report files.

## Remaining inference and next action

The largest fixture's private allocation is close to the authentic client's last
pre-stop observation: **5,867,569,152 private bytes**, 4,841,512,960 resident bytes,
sampled 761.485 ms before the guardian job call. The previously cited 5,676,453,888
private-byte reading was **242.0199 ms into termination**; it must not be treated as
the pre-stop baseline. The larger synthetic case still stops within 250 ms.
Neither equal private bytes nor one passing sample establishes equivalent resource
composition, load, driver activity or reliable Minecraft shutdown.

These cases do not establish the authentic failure's cause or qualify a remedy.
The current stopped client's log explicitly records OpenAL initialization and
sound-engine startup. That read-only observation is retained privately; it is not
a reestablished binding to the failed scope or proof of causation. Next test the
missing OpenAL resource path with a finite silent fixture, preserving ordinary
desktop audio and the same guardian. Do not change the game profile or repeat the
passing graphics cases merely to obtain more samples. Full loaded-game, setup,
scorer, provenance, isolation and recovery qualification remains required.

All previous failures remain, including 500.1327/500 ms and earlier stop samples,
five effective-file failures, Mineflayer/E9E incompatibility and sibling-read/
loopback canaries. The original model authority and unresolved $0.7554 hold are
unchanged. Required M0–M6 and conditional M7/extensions remain intact.
