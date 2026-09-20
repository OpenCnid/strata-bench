# Owned-job stop evidence — September 20, 2026

Operator-only. M0.3b.2c.3c.2b.2b.2.2; F09/F16,
N01/N03/N04/N05/N06/N08, C14/C15/C18 and partial T01/T07/T12/T13.
Implemented but unverified for authentic Minecraft. No aggregate gate closes.

## Failure and resulting behavior

The guardian previously waited only for the root Java handle after terminating
its job. A root exit cannot certify descendant exit. The initial revision added
zero-active accounting, but a real disposable-JVM test disproved that as a
complete exit proof: after the root had already exited, job accounting reached
zero while the independently held child handle remained unsignaled. That failed
sample is retained. No late-effect success was inferred from the zero count.

[WindowsJob](../../src/mcbench/processes.py) now supports optional, bounded
member observation. The guardian retains read-only, non-inheritable handles
whose membership in its held job is verified. Handles remain open, preventing
PID reuse from aliasing earlier members. It observes at attachment, during its
poll loop and immediately before termination. It never terminates by a
rediscovered PID, inspects process arguments or reads another account's data.

[AttachedJava](../../src/mcbench/process_guard.py) still requests job termination
once and uses the existing 500 ms root wait. It spends only the remaining part
of that same bound on accounting and zero-time handle checks. Success requires
zero active processes, a positive cumulative total equal to the number of held
handles, and every handle signaled. A late zero, an unsignaled child, a missing
member, a query error or an incomplete inventory cannot confirm termination.
Inventory failure before termination does not suppress the kill request.

The private policy `job-call-wait-tree-qpc/2` adds total/held/signaled counts and
tree-check boundaries/outcomes to the retained policy-1 diagnostics. The
[Node supervisor](../../backends/mineflayer/src/forge_guard.ts) rejects
inconsistent evidence and requires this proof plus the separate confirmed-stop
receipt. Records are queued after handle cleanup. Public gameplay capabilities
and the base guardian wire format are unchanged; source fingerprints change.

This uses documented [job member enumeration](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_basic_process_id_list)
and [membership checks](https://learn.microsoft.com/en-us/windows/win32/api/jobapi/nf-jobapi-isprocessinjob).
[TerminateJobObject](https://learn.microsoft.com/en-us/windows/win32/api/jobapi2/nf-jobapi2-terminatejobobject)
applies termination to associated processes; [TerminateProcess](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-terminateprocess)
documents asynchronous exit and the need to wait on a process handle for completion.
No undocumented job-signaling behavior or assumed notification delivery is used.

## Executed checks and retained failures

Private evidence: `C:\Users\Darian\.strata\evidence\2026-09-20-guardian-tree-01`
through `-03`. Python 3.12.14, Node 24.19.0, pinned Temurin 17.0.20.1+1,
Windows and the current worktree's compiled Forge fixture classpath. No Minecraft
launch, desktop input, model request or inference cost occurs in these checks.

- Offline `:forge1192-client:writeTestClasspath` succeeds in 24 seconds, with
  pinned input verification. Eight existing Java API deprecation warnings and
  the existing Gradle deprecation notice remain. This compiles fixtures; it is
  not an execution of the entire Java suite.
- `-01`: 46 pass, two fail. New assertions incorrectly expected exactly two
  job members; actual accounting contained three. The corrected fixture records
  all owned members and requires the root and child as a minimum, preserving
  the strict zero-process terminal criterion.
- `-02`: 47 pass, one fail. The count-only implementation falsely returned while
  the held child was unsignaled. Retained timing: root already exited, zero
  accounting observed 0.0521 ms after the wait began. This motivated the handle
  proof; the failed sample remains a failure.
- `-03`: all **52** selected Python checks pass, zero skips, 34.06 seconds.
  Covers identity/ownership, leases, pipe/parent loss, JVM freezes, descendants,
  retained late-effect checks and deterministic deadline/accounting failures.
  Five additional synthetic handle-inventory tests pass in 0.05 seconds after
  being added: read-only ownership/dedup/cleanup plus foreign, query, truncation
  and quota failures. These are additional checks, not a claim that one 57-test
  command was executed.
- All **12** selected Node checks pass, zero skips, 27.034 seconds. Six actual
  guarded JVM integrations and six private evidence validation checks include
  normal drain, mismatched grants, native freeze, worker kill/hang and parent
  loss. Fault-to-JVM-exit measurements are 1027/44/1818/37 ms respectively;
  these include their different detection paths, not just the 500 ms stop wait.
- TypeScript build and focused Ruff pass. Sixteen deterministic Python timing
  and failure-order cases also passed during development; they are included
  in the final 52, not additional unique coverage.
- Final review takes the loop's current time after member observation, so its
  latency cannot reuse a stale lease/deadline time. Five relevant lease/challenge/
  cleanup checks pass again, 6.74 seconds. Full Ruff and the gameplay-package
  exclusion check pass (one test, 0.23 seconds). Source hashes are retained in
  the private `source-manifest.json`, with the final edit timing explicitly noted.

The new direct tests retain three accounted/held/signaled members. With the root
alive at stop, its wait is 10.1832 ms and complete proof arrives at 21.3362 ms.
With the root already exited and two remaining members, its wait is 0.0066 ms
and complete proof arrives at 21.3316 ms. Both keep the original 500 ms bound
and independently confirm no delayed marker mutation.

Reproduction: use README's pinned Java/classpath opt-ins and run
`pytest -q tests/test_process_guard.py tests/test_forge_guard.py tests/test_processes.py`.
After `npm run build`, select Node tests in `forge.test.js`/`forge_guard.test.js`
matching `actual guarded supervisor|mismatched process grants|guarded process chain|guardian failure|malformed guardian|termination diagnostic|termination timing|root exit alone|empty job proof`.
Set `STRATA_GUARD_TEST_PYTHON` to this worktree's environment interpreter.

## Remaining qualification

The inventory has a 256-lifetime-handle development bound. Missed short-lived
members deliberately prevent confirmation; observation completeness and the
quota's suitability for real workloads remain open. Pre-attachment descendants,
non-inherited external process creation and adversarial containment remain
separate launch/isolation requirements. OS scheduling can exceed the bound;
such samples still fail. Forced termination is not input release or a clean
game/agent checkpoint. No consumed costs or uncertain actions are reset.

Earlier authentic 501.9950/503.5059/507.6092 ms failures and the separate
503.6561 ms measured wait remain unresolved. A new authentic candidate must
use new source/capability pins and retain complete game/reference evidence.
Prior native crash recovery's 13-to-zero accounting remains an accounting
observation, not proof that every process handle was signaled. Strengthen that
synthetic recovery fence next; do not promote its trusted sealing assertions
to production isolation or whole-tree exit evidence.
