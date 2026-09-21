# M0 continuous native writer custody

September 21, 2026. Operator-only. Partial M0.2c.3b.2b.3.2; F04/F09/F10/F13,
N01/N04/N06/N08, C12/C24, partial T01/T06/T07/T10/T13 and G0.

## Implemented behavior

`WriterPreparations.run(..., continuation=...)` now retains the original
workspace, protected writer tree, original inputs and staged preparation leases
while an operator continuation launches and stops the native fixture. There is
no close/reopen interval. The borrowed `WriterCustody` cannot be used after the
continuation returns, reconstructed from a result, or driven by another thread.
The continuation must finish its owned launch; returning early is uncertainty.

`native-private-java-custody/1` and strict `PrivateWriterLaunch/1` admit only the
synthetic JVM profile. The existing native Codex sandbox remains selected. The
code does not admit an authentic game or model. It pins the launch helper,
fixture classpath, descriptor and module, checks the exact broker/root/token
scope, records intent, and holds both original and staged launch inputs.
Arguments use a bounded encoded manifest and `ProcessBuilder`, with no shell.

`StrataWriterLaunch` publishes its PID/start/executable/root and waits at most
10 seconds. Before granting child launch, the controller matches that report
against the retained member handle of the exact owned Job and reads the actual
user/group/restricting token. It rechecks custody and publishes a fresh,
non-replacing grant. The helper does not access the world or start a child before
that grant. The child independently passes the private pipe's OS-peer/token
checks. The helper/JVM profile has a 15–30-second process deadline inside the
original finite preparation allowance; the used trials reserve 20 seconds.

One lifecycle owner observes Job members. The broker consumes those retained
handles without running a competing process observer. This exercises the final
owner-only broker change left for integration in the prior pipe report.

Every process and broker closes before input/namespace leases release. Cleanup
is in `finally`, including when journal writes fail; lease unwinding attempts
all registered closes. The first uncertainty is recorded before normal fault
cleanup. Missing process history, failed telemetry closure or a live unfinished
launch cannot become a successful result. Result fields distinguish stopped,
uncertain and live custody. No closed path is adopted for restart.

## Actual native synthetic evidence

Private prefix: `C:/Users/Darian/.strata/evidence/2026-09-21-writer-custody-`.
Pinned Codex SHA-256 remains
`960c111d47afd61669954b9df9e56083e302edbfa3ef6962d81dcc14a30051dc`;
Temurin 17.0.20, existing sandbox enrollment, the production private pipe/client
and two synthetic files totaling 53 bytes. The fixture sends synthetic
startup/health/stop events using schema 5/module 0.3.4. No Minecraft, model,
listener, account change or desktop input is involved. Candidate Forge module
0.3.6 is still not installed.

| Case | Actual result |
|---|---|
| `01` normal | Preparation stops normally with 10/10 held processes signaled. The production continuation, native gate and broker then complete with 12/12 signaled, active zero, complete logs, exit 0 and no force. Three authenticated records inspect successfully. Both original namespace objects are still open at launch; the returned borrowed object rejects reuse after all handles close. Scoring remains false. |
| `02` interruption | An explicitly injected operator continuation exception after two durable records produces UNCERTAIN before native cleanup. The 12/12 owned processes signal, active zero, exit 125 with deliberate force and complete logs. Two records and the consumed authority remain; no automatic replay or refund. |
| `03` wrong expected token | The control substitutes the operator SID only as the expected principal passed to the original token reader. The actual native token is still read from the retained handle. `WRITER_TOKEN_SCOPE_MISMATCH` rejects before the launch grant: zero settings/events/claims/spools, and no fixture child starts. Preparation was normal 10/10; the gate tree is deliberately forced, 10/10 signaled, active zero and complete logs. |

These controls use the production continuation instead of the former private
monkeypatch of `OwnedCli.finish`. No threshold or process-history requirement
was relaxed. Reopening each of the three stores and attempting the same ID
under new output paths rejects with `WRITER_ALREADY_RESERVED` before dispatch.
Exact preparation/broker rows, outbox events and claim/spool hashes remain
unchanged, and neither proposed output directory is created.

The positive predates the cleanup-finally refactor, which the two negative
controls exercise. The final projection/path hardening has focused source
checks; it is not an additional authentic game result. Case 02's raw nested
status remains `admitted` under an UNCERTAIN parent; the final source now marks
closed unfinished custody `uncertain` and `live=false`. Preserve that raw report.

## Focused checks and limits

Initial writer custody/preparation selection: **25 passed**. New broker-state
and launch-path negatives add five distinct checks; the final custody selection
is **11 passed**.
The compiled gameplay package exclusion check passes separately: **31 distinct
selected Python checks executed and passed**. The Java launch helper compiles
with the pinned JDK. Ruff and diff checks pass. No broad suite or unchanged
authentic trial was repeated. Native controls above are synthetic-file/event
integration evidence, not full T06/T07 or setup/scoring qualification.

Private 103-file source/evidence inventory SHA-256:
`dd02389d075b526fd1730390ce5c7f05a2edcc66b14405d8bb13ee7648e617ed`.
It precedes this final manifest-reference insertion. The ledger's prior
append-only history, 288 unique milestone IDs and changed local links pass
inspection. Final process inspection found no Java process or listener on
ports 25565–25580.

Next, complete this same M0 child by wiring the live custody into versioned
`ReferenceLauncher` and participant dispatch. Seal the newly prepared world
while custody remains held; use the pipe instead of the legacy private key/spool
paths; keep exactly one Job observer and one owner for log streams. The current
launcher still follows the legacy direct-launch path. Only after that integration
and its negative controls should a changed authentic reference run qualify
setup/history and joint scorer controls. Do not adopt these closed fixture roots.

The original $10 allowance and unresolved $0.7554 reservation are unchanged;
these checks make no model request. Sibling-read and original loopback failures,
failed 500-ms shutdown samples, five effective-file failures, Mineflayer/E9E
incompatibility and remaining scorer/provenance/recovery/soak/capacity/pilot
requirements remain. **M0 is incomplete; G0 fails; G1–G5 are not run.** Required
M0–M6 and conditional M7/extensions are unchanged.
