# M0 client preparation admission and retained scope05 failure

September 21, 2026. Operator-only. M0.2c.3b.3b.2a and
M0.3b.2c.3c.2b.2b.2.2a.4; F09/F16, N01/N03/N04/N05/N06/N08,
C14/C15/C18/C24, partial T01/T07/T12/T13/G0.
M0 remains incomplete, G0 fails and G1–G5 are not run.

## Authentic failure retained

After [independent observer implementation](2026-09-21-process-resources.md),
one fresh protected reference, private `2026-09-21-protected-craft-live-05`,
attempted the changed observer profile from commit `759b5ca`. It used the
original unplayed source from protected case01, new registration/challenge and
unchanged game mechanics, resources, deadlines and 500-ms guardian threshold.
The previous case04 scope and progressed world were not replayed.

The operator omitted the cached-session preparation step. The private driver
raised `FileNotFoundError` reading its required `session-preparation.log` before
creating a client, worker, live directory or observer. The controller had already
started the authentic server. This is an admission failure, not an authentic
observer result or a new guardian timing sample.

The pair completed **UNCERTAIN / exit 1 / 375.079 s**. Client failure triggered
the existing coordinated abort. The server stopped normally; retained histories
are inner server **14/14**, outer server **29/29**, and driver **5/5**, all terminal
without a forced outer stop. No client credentials were created, no client game
process or worker dispatched, and no model request or shared-desktop input occurred.
The authenticated server stream has **17 records / 270 sampled ticks**, with no
craft witness. These costs and the consumed scope remain recorded.

A separate failure audit passes **15/15**: durable pair/dispatch/protected states
stay UNCERTAIN, no invented client completion, full cleanup, unchanged original
8,609 source files and all 118 archived dispatch sources. It does not pass the
trajectory or resource audit; those could not run without client evidence.
Independent inspection found no Java processes. Original model accounting was
read-only checked before dispatch: schema 2, one migration, original $10 cap and
$0.7554 unresolved exposure counted once.

## Admission implementation

[reference_preparation.py](../../evaluator/src/strata_evaluator/reference_preparation.py)
introduces strict private `PrivateReferenceClientPreparation/1`, binding the
client registration digest, exact driver, preparation time, session receipt and
argument-file hashes. The existing Node receipt must say prepared, disclose no
credentials, bind the argument bytes, and declare a sufficient remaining lifetime.
Missing, changed, malformed, stale/future, foreign, insufficient or expired inputs
reject with bounded typed errors. Credentials and validation payloads are never
included in returned errors/reports. Files remain outside source/gameplay access.

[reference_pair.py](../../evaluator/src/strata_evaluator/reference_pair.py)
adds `PrivateReferencePair/3`. New E9E production dispatch requires this version
and its preparation pin; legacy plans remain parseable as historical records.
Synthetic profiles retain their separate v1/v2 contracts. The pair holds the
preparation and nonsecret session receipt alongside its existing source leases.
It verifies preparation **before durable pair intent and before server dispatch**,
requiring session lifetime for the complete registered outer exposure. Immediately
before client dispatch it repeats the check for the full client window plus the
existing 30-second sign-in margin. Failure after intent stays uncertain and follows
the existing abort/cleanup path; there is no auto-refresh or retry.

Argument bytes receive a transient native deny-write/delete lease while being
verified. That lease closes before dispatch so the driver can perform its own
launch check and retire its credential file. This is prepared-byte/expiry admission,
not authentication attestation, continuous credential-file custody or a new isolation
certificate. Receipt age is limited to 30 minutes; preparation and receipt records
are bounded to 8 KiB and argument files to 64 KiB. Full original process, action,
server and guardian limits remain unchanged.

## Verification and next step

`test_reference_preparation.py`, `test_online_reference.py`,
`test_reference_client.py` and package exclusion initially pass **75 checks**.
After explicit typed-error handling and a numeric-Boolean negative were added,
the preparation selection exposed one incorrect missing-file classification.
It was corrected; final **17 preparation checks pass**. Two explicitly enabled
existing native JVM pair cases (normal coordination and interrupted-intent replay
denial) pass. **78 distinct checks total**; overlapping reruns are not added.
Targeted Ruff and whitespace checks pass. No sign-in/network/model operation
occurs in these tests; argument contents are synthetic.

The private combined manifest verifies 352 files / 69,949,622 bytes; SHA-256
`5194c720fb77d0c3bc1381119a213f93bf7d497f82690b5a1ebcc54a42d00a54`.
Source validation preserves the entire previous append-only log, all prior
milestone IDs (294 now), and 1,105 local links. Final read-only accounting retains
the same authority digest, migration, $10 cap and $0.7554 unknown hold.

Production v3 admission and authentic resource collection are still unverified.
Next prepare one new scope with the cached-session step completed before admission,
pin its receipt and current modules, and exercise the new preflight before starting
the server. Never rerun scope05. Preserve case04's 500.1327-ms failure, all earlier
shutdown/effective-file/loopback/sibling-read/Mineflayer failures, the model hold,
and the remaining setup/scorer/provenance/recovery work. M0–M6 remain required;
M7 and other extensions retain their activation conditions.
