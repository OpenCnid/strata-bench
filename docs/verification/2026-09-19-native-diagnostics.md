# Native mutation failure diagnostics

Operator-only. SPEC v0.2.33; M0.3b.1b.4.1a verified for this bounded diagnostic contract;
F01/F06/F09/F16, N01/N02/N04/N06/N08; C02/C09/C15/C18;
partial T01/T03/T06/T07/T13. No aggregate gate passes.

The [authentic startup trial](2026-09-19-worker-startup.md) rejected the observed-air
action safely but failed its expected private typed-code audit. The mutation
transport discarded the underlying error when wrapping it as NativeOutcomeUnknown.
The existing direct-Fault tests bypassed this production path. Its historical
UNCLASSIFIED_NATIVE_FAILURE remains unchanged; source inspection cannot recover
the lost runtime code.

[NativeGameClient](../../backends/mineflayer/src/native_game.ts) now retains only
the existing allowlisted code inside the private unknown-outcome wrapper.
[ForgeLane](../../backends/mineflayer/src/forge_lane.ts) reads that sanitized field
only after the existing fence/release attempt. Arbitrary errors/messages/stacks
remain excluded; the public unknown/resynchronization receipt and at-most-once
mutation behavior are unchanged. The existing policy and public schemas remain.
No native JAR change is required.

Regression coverage sends real HTTP responses through the transport and broker,
using the disposable JVM for lane authority, observations and release. Cases:
typed rejection, accepted-then-polled rejection, unknown code, wrong identity,
extra response field and connection loss. Checks require one POST, exact polling,
fencing, confirmed release, private allowlist and no public error-code leakage.
Build passes; six new HTTP cases plus five existing diagnostic negatives and the
single-POST/lost-mutation transport case pass: 12 tests, zero failures/skips,
13.107 seconds. These are synthetic game fixtures; the authentic result below qualifies the observed-air rejection case.

Private evidence: `C:\Users\Darian\.strata\evidence\2026-09-19-native-diagnostics-01`.

The compiled gameplay-package check passes (1 test, 0.28 s). The fresh authentic
trial used 34 pinned broker modules and unchanged minor-34 native JAR.
It uses new authority and protected cached authentication; five selected save
files (17,637,503 bytes) were copied only after normal stop and zero-process
checks. Client/worker/primitive limits remain 480 seconds / 90 seconds / 1,000;
the guardian kernel wait remains 500 ms. No desktop input or inference.

## Authentic result

Official E9E 1.27.0 / Minecraft 1.19.2 / Forge 43.4.23 / pinned Temurin 17,
minor-34 b2a91155... client in the dedicated non-input-desktop copy. World
readiness passed in 213.437 s, with no startup read retries. Bootstrap took
1,116.6618 ms; initialization 294.9302 ms; gateway 2,575.8237 ms from worker start.
Both independent 2,250 ms startup limits passed; total gateway latency includes
guardian binding and is not that per-phase limit.

The public rejection checker and all **13 private negative-audit checks pass**.
One observed-air dig ends unknown/ACTION_UNKNOWN with confirmed release and
required resynchronization. The private event now retains PRECONDITION_FAILED,
only allowlisted fields, after the released unknown acknowledgement. No native
action intent exists; exactly two safety-release primitives are charged. A new
action after fencing rejects, and public CLI outputs contain no private code or
diagnostic. Five native journal frames and three native usage records reconcile;
SQLite integrity passes. The original erased diagnostic remains a failed sample.

Independent stopped saves match 256 delivered block IDs across both boundaries;
all 128 selected block states are unchanged. Saved player position, rotation and
dimension pass; selected inventory fields are unchanged. The after-copy has five
files totaling 17,637,494 bytes. Two 854x480 PNGs pass independent decoding and
visual inspection (world, bow, vegetation and HUD). These limited references do
not establish complete resources, causal scoring, full checkpoints or physical
input parity.

The **overall procedure still fails shutdown**. Child executor exits 0, but the
guardian's 500 ms wait returns timeout after measured 501.9950 ms, following a
successful 1.0247 ms job-termination call. It reports PROCESS_STOP_UNCONFIRMED;
parent worker exits 1. The independent held-handle observer later sees exit at
about 586 ms after QPC start; that cannot override the failed wait. Client
procedure took 330.547 s; server saved/stopped normally (exit 0, complete logs)
at 543.906 s. No desktop watchdog intervention; input desktop unchanged,
temporary arguments retired and zero Java processes verified. All 34 module
hashes still match the prelaunch archive.

Startup-audit and final-audit keep diagnostic/startup pass separate from overall
and shutdown failure. M0.3b.1b.4.1a covers the repaired private transport/journal
behavior only. Parent geometry, gameplay, production isolation, native runtime,
resources and shutdown reliability remain open; no T01-T17 or G0-G5 aggregate
result changes. No inference was dispatched.
