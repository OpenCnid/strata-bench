# M0 private reference abort component

September 20, 2026. Operator-only. M0.2c.3b.3b.3a is implemented with
source/owned-process verification; authentic integration remains unverified.
M0 is in progress, G0 fails and G1–G5 are not run.

The preceding authentic reference caught an outer `Fault` without recording
its code, then forced both process trees down before inner terminal reports.
Its exact fault cause remains unknown. This change exercises the cleanup path;
it does not reinterpret that failed run or make its saved world a checkpoint.

`reference_abort.py` preserves a sanitized phase/type/code in a non-replacing,
scope/challenge/launch-digest-bound private abort request. Readers bound input
size, reject linked or malformed controls and latch any observed abort.
`PrivateReferenceLaunch/3` adds explicit abort policy while retaining version-2
registration. The server denies new readiness, allows finite participant cleanup,
then sends ordinary stop with the existing hard fallback. Abort always yields
uncertainty, including a falsely completed client receipt and a signal arriving
during final receipt validation. Consumed grants stay consumed; import stays denied.

The trusted participant guard owns at most two existing managed-process objects.
It fences creation and command admission and watches independently while the
driver is blocked. A child created concurrently with abort remains retained and
is stopped. Cleanup failures preserve typed codes; a stalled stop cannot produce
a confirmed guard close or close handles beneath its watcher. These are private
operator facilities, never gameplay tools or process-isolation certification.

The new 500–15000-ms cooperative cleanup interval does not extend existing
server/client deadlines or change the 500-ms guardian. The 600-second server,
120-second maximum graceful stop and complete participant-window requirements
remain. Version-1/2 histories are unchanged. No Minecraft, model request or
shared-desktop input was used for this change.

## Executed verification

Windows x64, Python 3.12.14, existing locked environment, Temurin
17.0.20.1+1 and the pinned telemetry test classpath. JVM cases use the existing
`OwnedLaunchFixture` and signer; they are synthetic game substitutes.

| Check | Observed result |
|---|---|
| Initial abort test collection/execution | 13 passed, 5 fixture setup errors; missing shared `reference` fixture import corrected |
| First complete abort suite | 22 passed in 12.78 s |
| Abort, participant, launch and client suites after two additional race cases | 97 passed in 40.17 s; 24 abort cases included |
| Actual module CLI v2/v3 binding regression and compiled gameplay package exclusion | 3 passed in 2.09 s; overlaps prior v2 test |
| Targeted Ruff and whitespace checks | Pass after unused import/fixture-shadow lint corrections |

Cases cover scope/challenge/digest mismatch, oversized/truncated/linked controls,
abort during creation, blocked-driver child termination, stalled/failed cleanup,
late admission, failed/missing/falsely completed receipts, prereadiness abort,
late receipt-validation abort, strict unchanged limits and denied import/replay.
The combined owned-Python/JVM case preserves a failed participant report before
normal server stop while retaining an uncertain reference result. A normal v3
synthetic receipt retains its narrow coordination result, not execution/scoring credit.

Private logs and the read-only accounting snapshot are under
`C:/Users/Darian/.strata/evidence/2026-09-20-reference-abort-01`.
Original authority `validation-2026-09-18` remains schema 2 with one migration,
10,000,000 microUSD cap and 755,400 microUSD aggregate uncertain exposure. No
refund, replay, allowance reset or new model dispatch. Final process inspection
found no Java process or listener on the two prior reference ports.

## Remaining M0 work

Implement .3b's durable outer pair coordinator and wire the actual private
client driver to this guard, preserving the first typed failure before abort
publication. Keep hard watchdog fallback and truthful missing/uncertain terminal
results. The guard alone cannot bound a stalled outer driver or prove full pair
cleanup. Exercise those owned-process faults before another changed game trial.
Register adequate startup + full worker + terminal exposure inside the existing
ceiling and use a fresh declared lineage from a qualified stopped source.

Native craft/team positive/negative controls, mutable world/config writer
exclusion, complete setup history, parity, isolation and score admission remain
open. The 500-ms failures, five effective-file failures, original loopback
failures, Mineflayer/E9E incompatibility and unresolved OAuth receipt remain.
Coverage: F04/F09/F10/F13/F16, N01/N02/N04/N06/N08, C12/C18/C24,
partial T01/T06/T07/T10/T13 and G0 item 5. Required M0–M6 and conditional
M7/extensions are unchanged.
