# M0 owned Java preparation candidate

September 21, 2026. Operator-only. M0.2c.3b.2b/.2; F04/F09/F10/F13,
N01/N04/N06/N08, C12/C24, partial T01/T06/T07/T10/T13 and G0.

## Implemented behavior

`evaluator/src/strata_evaluator/writer_preparation.py` and
`evaluator/java/StrataWriterPreparation.java` add the private
`native-private-java-preparation/1` candidate. It accepts synthetic fixtures
only. An authentic game plan fails admission; no scoring or protected-setup
certificate can be issued. The selected native Dovetail gameplay runtime and
its capabilities are unchanged.

The strict plan pins the Codex executable, Java executable, compiled helper and
each source file. A deny-write lease covers those files, the interpreter and
bootstrap, and the complete JRE inventory. Pins are checked again after lease
acquisition; the runtime inventory and digest are persisted. Staged helper,
manifest and source copies remain leased through normal termination or failure
cleanup. Plans reject escaping/colliding paths, overlapping private stores,
existing output, excessive files/bytes and insufficient remaining exposure.

A durable one-use SQLite intent precedes filesystem creation and dispatch.
`OperatorWorkspace` atomically creates a final protected operator/SYSTEM DACL
and holds list-access namespace handles. The native sandbox then enrolls its
group and workspace scope; the controller requires the exact resulting ACL.
The workspace may use readable ancestors for Java canonicalization, but its
own ACL does not inherit Public/Users/Everyone access. No private-store ancestor
permissions are broadened.

The actual Java process publishes a fresh challenge, PID, start time, executable
and requested path, then waits. That receipt supplies no authority by itself.
The controller matches it to a retained member handle of the exact owned Windows
Job and reads that handle's OS token: expected user, enabled sandbox group and
the enrolled restricting SID must agree. Only then does it create the protected
writer root and durably record BOUND before publishing the non-replacing copy
grant. Java canonicalizes that root, copies with CREATE_NEW, verifies hashes and
sizes, forces data, and publishes its actual root and counts. The controller
checks the complete copied tree and inherited ACLs before COPIED and the finish
grant. Complete logs, normal exit and total == held == signaled with zero active
processes are required for STOPPED.

Exposure is finite: a 25–60-second plan, at most 22 seconds for the owned native
dispatch, a 20-second Java deadline and bounded cleanup. `OwnedCli.finish()` now
reconciles asynchronous descendant signaling for at most two seconds after
forced stop. An unconfirmed watchdog cannot bypass Job close or certify terminal
proof. These cleanup bounds do not change the 500-ms guardian requirement.
Missing process history still fails even when all retained handles signal.

The first fault is durable UNCERTAIN before cleanup. A fresh controller refuses
both existing output and the same reserved ID under new paths; no journal reset,
replay or permission refund occurs. Closing preserves the DACL but releases
namespace custody. The result is therefore **not** reusable server-launch or
recovery authority. Continuous preparation-to-server custody is the next item.

## Actual native evidence, including failures

Private evidence directories use prefix
`C:/Users/Darian/.strata/evidence/2026-09-21-writer-preparation-`.
All trials use the pinned Codex SHA-256
`960c111d47afd61669954b9df9e56083e302edbfa3ef6962d81dcc14a30051dc`,
the existing sandbox enrollment and Temurin JRE 17.0.20. The helper was compiled
with the installed JDK 17.0.20. These are actual Windows/native CLI/JVM executions
with **synthetic files**, not Minecraft, model or authentic evaluator trials.

| Private suffix | Observed result |
|---|---|
| `01` | Initial separate enrollment completed 10/10. Java then failed canonicalizing the private-store root before any copy grant. Preparation ended 10/10, exit 1; state UNCERTAIN. |
| `02` | A separately protected workspace under readable ancestors allowed copying two files/53 bytes. Enrollment and preparation each ended 10/10; exit 0, no force. This earlier profile lacked the held-token check. |
| `03` | Short-lived enrollment observed only 9 of 10 process handles. No copy or token binding; UNCERTAIN. The full-history threshold was preserved. |
| `04` | Single Java dispatch waits for binding, eliminating the separate enrollment command. Actual retained-handle token binding, copy/hash/ACL checks and normal 10/10 termination pass. |
| `05` | Final preparation path adds staged-lease lifetime, exact workspace ACL, saved runtime inventory and pin rechecks. Two files/53 bytes verified; token bound; 10/10 signaled, active 0, normal exit/no force. |
| `06` | Wrong expected writer token rejected before protected-root creation or copy grant. Initial forced cleanup sampled 4 of 10 signaled handles despite zero active; terminal proof failed and remains retained. |
| `07` | After the signaling fix, injected interruption after durable COPIED records UNCERTAIN before cleanup. A separate SQLite reader confirms ordering; helper, staged source and manifest all reject write-open until cleanup. No finish grant; forced exit 125, 10/10 signaled, active 0, complete logs. |
| `08` | Changed cleanup repeats only the unresolved wrong-token control: rejection before root/grant, forced exit 125, 10/10 signaled, active 0, complete logs. State remains UNCERTAIN despite successful cleanup. |

The first Java failure is consistent with OpenJDK's Windows implementation
listing each path component during
[real-path canonicalization](https://raw.githubusercontent.com/openjdk/jdk17u/master/src/java.base/windows/classes/sun/nio/fs/WindowsLinkSupport.java).
The fix preserves canonicalization and private-parent permissions. It does not
claim that moving an unprotected directory would provide isolation.

Restart controls reopen stores 05–08, reject both existing paths and new paths
under the same ID, preserve exact rows/event counts and create no new output or
process. Completed and uncertain attempts are not replayed. Exact dispatch source
is archived at 05; the cleanup delta is archived at 08. Earlier exploratory
variants retain raw evidence without a claim of complete source snapshots.
The final 150-file private inventory includes those attempts, synthetic workspace
artifacts, final source, accounting/process checks and test records. Its SHA-256 is
`3ac506f68d8b10784f92ce8e1a621b93b59b5bab447b2a63bf29606a031610e6`.
A fresh compile of the final Java source reproduces the dispatched class hash
`c292561773ba57a08fed706192d898a5e17e109299f196d2f49a5b6b6f6dc12e`.

## Focused verification

With explicit existing `STRATA_WRITER_TEST_SID` and `STRATA_WRITER_TEST_GROUP`:

```text
pytest tests/test_writer_preparation.py tests/test_windows_writer.py
       tests/test_reference_pair.py::test_unconfirmed_watcher_cannot_bypass_job_close_or_claim_terminal_proof
       tests/test_reference_pair.py::test_forced_cleanup_waits_for_signaling_without_forgiving_missing_history
       tests/test_reference_pair.py::test_actual_owned_pair_completes_only_coordination_and_preserves_exact_reports -q
```

51 pass / 0.61 s; the JVM pair was initially skipped because its explicit profile
variables were absent. With `STRATA_TELEMETRY_TEST_JAVA` pointing to the pinned
JRE and `STRATA_TELEMETRY_TEST_CLASSPATH` to the existing generated fixture
classpath, that pair plus `tests/test_gameplay_package.py` pass **2/3.76 s**.
Thus all 53 selected checks executed and passed. The first 48-check run also
passed; its nine Ruff style errors were corrected. Final affected-file Ruff and
whitespace checks pass. No broad unchanged suite or positive craft rerun ran.

Run a fresh admitted synthetic preparation with:

```text
python -m strata_evaluator.writer_preparation --database <private-db> --plan <private-plan>
```

The private `07/control.py` and `08/replay_controls.py` preserve the exact fault
and restart procedures. Compiled helper, source inventories, logs, SQLite
stores, fixtures and control artifacts remain outside public source/gameplay.

Read-only accounting at **07:34:04 UTC** preserves schema 2, one migration,
original **10,000,000 microUSD** allowance and **755,400 microUSD uncertain
aggregate exposure**, counted once. No model request, settlement, refund or reset
occurred. Process/listener inspection found no Java/access-fixture process or
listener in the reference port range. No desktop input, credential inspection
or copying, account installation or firewall change was used.

## Remaining M0 work

M0.2c.3b.2b.2 is implemented but not an authentic server integration pass.
Connect preparation, token/scope and namespace custody continuously to the owned
server launch, including protected telemetry/configuration brokerage. Then prove
setup/history authority and the required joint scorer controls, parity and
nonleakage. The previous **sibling-read canary remains FAIL**; protected writes
alone do not establish credential, sibling or evaluator isolation. No automatic
adoption of these stopped fixture paths is permitted.

M0 remains in progress; G0 fails; G1–G5 are not run. Preserve every failed 500-ms
sample, the five effective-file failures, Mineflayer/E9E incompatibility,
loopback failures, unresolved inventory case and OAuth receipt, full provenance,
recovery, soaks, capacity and pilot requirements. Required M0–M6 and conditional
M7/extensions are unchanged.
