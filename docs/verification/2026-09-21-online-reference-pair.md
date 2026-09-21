# M0 protected server and owned client coordination

September 21, 2026. Operator-only. Partial M0.2c.3b.2b.3.2;
F04/F09/F10/F13/F16, N01/N04/N06/N08, C12/C24,
partial T01/T06/T07/T10/T13 and G0. M0 remains incomplete.

## Delivered implementation

`PrivateWriterPreparationPlan/2`, `PrivateWriterLaunch/2`,
`PrivateReferenceLaunch/5` and `ProtectedReferencePlan/2` declare the
`native-online-private-server/1` capability. They retain the pinned native
Codex sandbox, actual retained-Job/token checks, protected workspace, immutable
input handles, pre-start grant and private telemetry pipe. This changes the
private server's token/network and finite runtime profile. It neither changes
the selected Dovetail gameplay loop nor admits gameplay tools to server storage.

The server needs networking for its official bootstrap and authenticated joins.
The new private profile explicitly enables direct networking and disables the
network proxy. It makes **no domain-filtering or network-isolation claim**.
OpenAI's [permissions documentation](https://learn.chatgpt.com/docs/permissions?translationFallback=fr-FR)
distinguishes direct networking from proxy enforcement. Its
[Windows sandbox documentation](https://learn.chatgpt.com/docs/windows/windows-sandbox?translationFallback=fr-FR)
describes dedicated sandbox accounts; actual pinned-native token evidence below
is separate from those current documentation semantics.

The versioned preparation lifetime is at most 900 seconds, with at least
60 seconds beyond the planned server/cleanup windows. Existing server limits
remain 600 seconds plus 120 seconds graceful cleanup; the native child limit
is at most 720 seconds. Preparation copying retains its original finite
20-second helper/22-second supervisor limit, 12,000 files and 1-GiB total quota.
Legacy offline profiles retain their original limits and reject mixed versions.
These process windows do not change the 500-ms guardian acceptance threshold.

Authentic server dispatch accepts only the already reviewed E9E ServerStarter
command, bootstrap hashes and reviewed installed-state lock. It pins the JRE, PATH, module and descriptor;
existing complete software inventory, online/loopback properties, EULA and
client binding checks still apply. Synthetic fixtures remain explicitly labeled.

`PrivateReferencePair/2` now owns the protected preparation/server process and
the client driver. It pins both plan files and requires their exact launch
identity. Pure registration checks happen before preparation; complete module
and fixture-byte checks happen under live custody before server dispatch and
again before client dispatch. Native readiness must match the durable row,
challenge, scope and full remaining client window. The outer deadline covers
the entire protected lifetime. The existing separate-desktop driver can use
this path without bypassing its abort guard or guardian tests.

Closure preserves exact server, client and protected reports. STOPPED requires
the matching durable protected plan/body, matching inner launch result and
closed stopped preparation custody, in addition to existing outer process,
participant and telemetry checks. Missing/ambiguous evidence remains uncertain;
neither a clean child exit nor a complete telemetry prefix repairs it.

## Actual native, synthetic-content evidence

Private prefix:
`C:/Users/Darian/.strata/evidence/2026-09-21-online-reference-pair-`.
Both samples execute the production module CLI and pinned native sandbox on
Windows with Temurin 17.0.20.1+1. The actual expected online account is enabled,
SID ending `1004`; admission verifies the held process token, group and scope.
Only synthetic JVM world/events and a disposable owned Python participant are
used. No Minecraft, model, shared-desktop input or authenticated game join runs.

| Case | Evidence |
|---|---|
| `01` positive | STOPPED pair in 16.984 s. Preparation 10/10 and gated native launch 12/12 terminate normally. Outer server 27/27 and client 10/10 have complete histories/logs, active zero, no force. Private broker stops; exact reports reconcile. Twelve independent audit checks pass. Candidate import is idempotent and unscorable. |
| `02` missing participant report | Owned client exits without its required receipt. `REFERENCE_PAIR_CLIENT_REPORT_MISSING` is durably recorded, followed by a bound abort. Pair/protected lifetime remain UNCERTAIN. Outer server 27/27 and client 5/5 stop normally with complete histories/logs. Import rejects `CRAFT_PROTECTED_REFERENCE_UNQUALIFIED`. |

Both stores were reopened. New preparation IDs/workspaces/output paths with the
same instance reject `REFERENCE_PAIR_ALREADY_DISPATCHED` before child dispatch.
No new output trees appear; exact pair rows and stream hashes stay unchanged.
Dispatch source bytes are archived privately for both samples.

The first failure audit incorrectly expected the later outer-pair rejection.
The protected-lifetime check correctly rejects first. That failed audit is
retained; the corrected nine-check audit records the actual error and passes.
This was an audit expectation correction, not a relaxation of import admission.

## Source checks and remaining M0 work

Initial affected preparation/custody/protected checks: 47 passed. Pair/client
changes: 49 passed and one explicitly configured legacy JVM fixture skipped.
Final changed-profile/package checks: 30 passed, including direct authentic-entrypoint
registration denial, unreviewed bootstrap/argument rejection, finite exposure,
mixed profile refusal and durable closure corruption controls. These runs cover
106 distinct passing Python cases; the final selection overlaps the initial
20 online cases. The package exclusion check also passes. Ruff passes for changed
implementation/tests. The actual native pair samples above supply integration
evidence separately from unit tests.

The private 287-file source/evidence inventory has SHA-256
`63202f62cd58eaa9afaaf426ab81133d6c4406c5cff6c6c9aa290e9be4b678a4`.
It precedes this manifest-reference insertion. Final process inspection finds
zero Java processes and zero game listeners on ports 25565–25580. Prior
append-only history, 288 unique milestone IDs and 1,051 local links pass checks.

The authentic E9E branch is implemented but unverified. Module 0.3.6 remains
built and uninstalled. Continue from the preserved initial fixture and existing
owned real-client driver; do not copy the progressed instance-06 world. The old
immutable-software/fixture inventory is not the complete preparation input set:
its full original source inventory lists 18,227 files/598,175,721 bytes, including
9,605 installation `overrides` files. The inspected official source and actual
pinned-JAR lock bytecode agree: a matching installed lock skips pack installation
and override application. The
new authentic profile pins that exact lock; missing or changed state rejects.
All 18,227 original files were rehashed unchanged. The private disposition
manifest selects 8,609 runtime files/563,280,519 bytes, within the existing
quotas; it retains the 9,605 installation override files and 13 historical
output/lock files in their original archive. No source files were deleted.
This candidate manifest is not a successful preparation or authentic launch.
Materialize it with the explicitly recorded 0.3.6 module change and the initial
fixture before validating the real-client path. Do not silently omit content
or raise quotas merely to pass a trial.
Any necessary preparation resource-profile change needs a finite declared bound
and focused conformance. No new hardware or user permission is required for this
engineering work.

The original authority was read without mutation at 09:22:10 UTC: schema 2,
original $10 allowance, $0.7554 unresolved request/envelope exposure counted
once, uncertainty retained. Reserved token maxima are not measured consumption.
No new model experiment, settlement, replay, refund or allowance was created.

Preserve sibling-read and original loopback failures, all failed 500-ms samples,
the five effective-file failures and Mineflayer/E9E incompatibility. Full
authentic setup/history, scorer controls/parity, provenance, recovery, soaks,
capacity and scientific gates remain. **G0 fails; G1–G5 are not run.**
M0–M6 remain required; M7 and other extensions retain their activation conditions.
