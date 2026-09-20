# Authentic pending settings recovery across client termination

2026-09-20. Operator-only. Partial M1.1a.2.3c.1/.2.4, F06/F09/F16,
N01/N02/N03/N04/N06/N08, C10/C11/C14/C18, T05/T07/T13. The executed
applied-pending interruption and recovery case passes. Complete T05/G1 remain
unqualified; the separate authentic-world T07 timing failure remains.

The source checkpoint is `301a2ef`. The exact E9E 1.27.0 client, Forge 43.4.23,
Java 17.0.20.1 and installed minor-34 client JAR are unchanged from the
[round-trip/readback samples](2026-09-20-native-settings.md). Each launch pins
the source, Java, libraries and artifact hashes. Client JAR SHA256 remains
`b2a91155a7698d3ce6095ae7c4005827ea10c7f3623bfa086312f29d56916896`.
No server/world, physical input, live inference, campaign or scored run occurs.

Both clients use a fresh non-input desktop, independent lifetime guardian,
480-second outer lifetime and 280-second readiness limit. Only the private
settings bridge is enabled. Its bearer descriptors remain in protected operator
broker storage, separate from evidence and gameplay; no descriptor is published
or copied to evidence. Each boot creates a fresh session. Before using it, the
operator verifies the native fingerprint and listener ownership by the held
client PID. API calls use a bounded background thread while the main loop pumps
the lifetime guardian; the five-second native call bound is unchanged.

## Pending transaction and forced termination

The first client calls `snapshot`, one `apply`, then `snapshot`. The existing
source-bound Curios binding changes from unbound to the F13 encoding. Its exact
artifact, public registration-object identity and native fingerprint are the
same as the prior round trip. The transaction reports
`applied_pending_verification`, `committed:false`. Exactly one of 253 runtime
bindings changes, and the options bytes differ only by that owned field.

After confirming this state, the operator closes the dedicated client's job,
forcing JVM termination before rollback. There is no JVM clean-shutdown recovery
or replay. The four-frame private journal ends in applied_pending_verification.
Its SHA256 is
`7a0c3f31e7ca26c58c8cdfcee57cf2c1fb0e4977d374f855fe0da2dcae2d01d7`.
Native readiness takes 125.375 s; total procedure time is 126.453 s.

## New session, status and rollback

Only after independent terminal-process observation and argument retirement,
the second client starts against the same journal and modified options. Its
first API operation is `status` for the existing transaction, which reports
applied_pending_verification. A snapshot confirms the reloaded F13 encoding
and all other original runtime bindings. The remaining calls are `rollback`,
`snapshot`, and `status`. **No apply operation exists in the recovery branch.**

The final transaction is rolled_back, still committed:false. All 253 runtime
values equal the original map; each persisted value matches without ambiguity.
The options file is byte-for-byte original, SHA256
`38b89fb282ee5c4cc0ecd9d3180dbc76b43a9aa7624e1d970ece9a07fda03833`.
Native readiness takes 125.750 s; total procedure time is 127.000 s.

Independent read-only audit validates exact call order, one total forward apply,
zero recovery applies, complete binding/file restoration, all frame hashes and
the unchanged original journal prefix. The complete six-frame sequence is
profile, observed, prepared, applied_pending_verification, rollback_prepared,
rolled_back. Journal SHA256 is
`9964abf6651c95947c40ba2f9f0dec67696752eec3d0e0fa461304a4dcc0a7d8`;
audit SHA256 is
`9be7760d0387eae38275b2a01762dafb5b05378d759d61b11242b3ed8d7263fc`.
The audit initially expected a redundant final observed frame; source review
and the equal restored digest show that no such frame should be written. The
audit correction is retained; no raw sample, threshold or implementation changed.

Both independent base guardians confirm termination, with coarse stop fields
328 and 343 ms respectively. Separate held observers signal, zero Java processes
remain, input-desktop identities are unchanged and both populated argument files
are retired. These are title-screen process receipts, not a replacement for the
failed high-resolution authentic-world guardian case.

## Limits and handoff

Plans, runners, API intents/results, immutable option captures, journals, audit
and client logs remain under external
`C:\Users\Darian\.strata\evidence\2026-09-20-settings-recovery-01`.
The private broker is separately protected; parent-directory preparation was
corrected before any client launch. There was no live inference expenditure.

This case terminates **after** a fully acknowledged pending apply. It does not
establish interruption within a runtime/file write, ambiguous apply response,
foreign-writer exclusion, power-loss durability or complete restore of game and
agent state. Physical keys, intended/competing effects, tested key pool, general
ownership/CAS, repair charges, cross-client isolation and gameplay admission
remain unqualified. Next exercise foreign options/revision conflicts with exact
owned-intervention cleanup, then precise mid-write faults on the native runtime.
G0/T07 remain fail; G1–G5 remain not_run.
