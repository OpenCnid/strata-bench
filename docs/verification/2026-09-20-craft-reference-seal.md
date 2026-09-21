# Private craft fixture seal and authenticated evidence join

September 20, 2026. M0.2c.3b.1; F04/F09/F10/F13/F16,
N01/N02/N04/N06/N08, C12/C18/C24, partial T01/T06/T07/T10/T13,
G0 item 5. Source and synthetic integration evidence only. No Minecraft,
model request or shared-desktop input occurred in this change. M0 remains
in progress, G0 fails and G1–G5 are not run.

## Implemented behavior

[CraftReferenceStore](../../evaluator/src/strata_evaluator/craft_reference.py)
checks a complete selected fixture file inventory and separately pinned supporting
files. Unknown files, missing/changed bytes, case collisions, hardlinks, unsafe
paths and source-checkout destinations reject. It checks for enough
free space for the copies plus 5 GiB, then stores private independent copies of
the fixture and supporting evidence. Every copied file is hashed; the source is
checked again before publication. Database publication occurs last. Partial
directories remain nonadmittable and are never automatically overwritten.

The versioned plan fixes the instance, campaign/epoch, evidence kind, Strata
team/agent-to-Minecraft-UUID roster, complete craft predicate, expected runtime
recipe digests and inclusive server-tick window. Roster members are unique and
must match the predicate. This is a registered benchmark roster, not proof of
FTB Teams or quest membership.

`TelemetrySpoolAuthority/2` includes the canonical setup digest in its authority
fingerprint. Existing Forge telemetry 0.3.3 already signs that opaque fingerprint,
so the production Java protocol/module is unchanged. Legacy version-1 authority
continues to inspect its original streams; it cannot be relabeled as a sealed
craft source. The thirteen public top-level record schemas remain unchanged.

Preflight rechecks the live fixture, supporting files, preserved archive and
unconsumed key, then durably reserves one launch. A second preflight or consumed
grant rejects; an uncertain launch is not automatically renewed. This reserves
an operator reference intent, not a campaign or inference allowance.

Inspection requires the durable seal and launch reservation, unchanged archived
evidence and matching version-2 authority. It verifies the complete signed spool,
recomputes native resource witnesses, checks exact recipe definitions, actor
membership and the tick window, then applies the resource part of the predicate.
Gift/no-consumption/wrong-actor/wrong-recipe/early/late cases contribute no
candidate output. Distinct transactions contribute separately; duplicate native
transactions reject. Importing the identical complete stream after database
reopen adds no row or outbox event. A changed stream conflicts with the retained
receipt, even if someone possessing the key signed it correctly.

Reports are private, create-exclusive and cannot target the game or seal
directory. Existing evidence is not overwritten. No `Scorer` predicate state
is created or advanced. `candidate_output` and `candidate_complete` describe
the resource join only: `scoring_eligible`, `scoring_authority_qualified`,
`setup_mechanics_qualified` and `launch_ownership_qualified` remain false.

## Executed verification

Windows x64, Python 3.12.14, pinned Temurin 17.0.20.1+1 and Gradle 8.8 /
ForgeGradle 6.0.42. Existing exact Minecraft/Forge build-input verification runs.

| Check | Result |
|---|---|
| Reference, authentication, native-witness, scorer-scope, evaluator and telemetry Python suites | 133 pass, zero skipped, 8.97 s; actual Java opt-in enabled |
| Final reference checks after report-path hardening | 35 pass, zero skipped, 4.30 s |
| Final archive-path guard checks | 6 pass, 29 intentionally deselected, 1.42 s; actual JVM writer included |
| Targeted telemetry Gradle tests/classpath | Build succeeds in 16 s; 20 XML tests, zero failures/errors/skips |
| Actual Java writer with version-1 and version-2 authorities | Both complete and verify; reused grants reject |
| CLI seal → preflight → actual Java writer → inspect → replay → rejected preflight | Six commands pass their expected outcomes; one synthetic resource candidate, no score |
| Targeted Ruff | Pass |
| Compiled gameplay package exclusion | 1 pass, 0.26 s; evaluator/keys remain absent, runtime isolation separate |

The test-only Java fixture now accepts a bounded set of synthetic events. This
exercises the production spool/claim/MAC implementation without a Minecraft
server or authentic player action. The CLI control uses fabricated save bytes,
synthetic actor/recipe data and `evidence_kind=synthetic`. Its original and final
private reports have identical bytes after the final CLI safeguards. The actual
Forge stream from the preceding change stays a separate authentic reference;
it was not retroactively attached to a new setup seal.

Private evidence is under
`C:/Users/Darian/.strata/evidence/2026-09-20-craft-reference-01`:
control script, commands, synthetic plan, baseline/supporting copies, keys/claim,
signed stream, SQLite state and reports. None belongs in public source or a
gameplay distribution.

## Remaining acceptance work

Prelaunch byte agreement cannot establish that the eventual server used those
bytes. The next implementation must bind the one-use reservation to the owned
launcher, exact working directory/configuration/artifacts and actual server
process. Scans are not held-file/process isolation. Keep the reserved intent if
dispatch becomes uncertain; no automatic replay or new grant.

Native setup/admin/mode and pack-team facts, authentic joint craft controls,
reference reachability/alternate strategies, mechanical parity/overhead and
nonleakage remain required before a protected score. Supporting files are
verified evidence bytes, not automatically trusted assertions that their
contents prove setup validity. The server-tick window does not qualify the
complete wall-time/budget cutoff or recovery contract. The online telemetry API
also remains required. Raw witnesses stay unscorable.

The original unresolved OAuth request still retains $0.7554 estimated exposure;
this code cannot modify its allowance or release the hold. Preserve the failed
500-ms shutdown samples, five effective-file failures, Mineflayer/E9E and
loopback failures, M0–M6 scope and conditional M7/extensions.
