# M1.6b.1 failed and interrupted pair verification

D20 continuation of [pair staging](2026-09-25-m1-probe-pair-staging.md).
M1.6b.1 is verified for the controller preparation boundary described here.
M1.6b remains implemented_unverified, M1.6 in_progress and G1 not_run.
Affected: F08/F09/F16, N01/N05/N06/N08, C12/C20/C22/C23/C24/C36,
T01/T06/T07/T11. This is a G1 dependency, not a broader G2 recovery claim.

The previous verifier rolled back a failed check and left PREPARED. Restoring
changed files could therefore make the same pair pass again. The
[verifier](../../evaluator/src/strata_evaluator/probe_pairs.py) now commits
VERIFYING with a private intent event before inspecting source records or trees.
Only a complete successful recheck returns PREPARED. A caught failure commits
FAILED; abrupt controller death or failure to journal the error leaves VERIFYING.
Neither state can verify, prepare again, or reuse the reserved fixture/world
under another pair/instance label. Original files and accounting remain retained.

Authorization and existence checks precede the intent. Unauthorized callers
cannot invalidate a pair. If the intent transaction fails, no source/tree
inspection occurs and the prior state remains. Successful checks can repeat,
but provide no dispatch authority, file custody, resource admission or evidence
of a live backend's initial state. No native launch/publication guard changes.

## Executed checks

Initial selection: six pass, two fail before the intended crash boundary because
the child fixture passed a string to Database, which requires a Path. Retain
those artifacts and the failure; they do not establish process-death behavior.
Initial lint also found an unused import and fixture import naming issue; both
are corrected without changing the verifier.

Final command, with `PYTHONPATH=src;tools;evaluator/src`:

```text
.venv/Scripts/python.exe -m pytest tests/test_probe_pair_verification_fence.py tests/test_probe_pairs.py -q
```

**42 pass** in151.54 seconds: eight new cases plus34 existing staging cases.
The recorded invocation also supplies a fresh private `--basetemp` and JUnit
output. Checks include repaired-byte refusal, source/read interruption, intent
and error-journal failure, unauthorized access and repeat successful verification.

Two actual child Python processes open the synthetic controller/CAS, then use
`os._exit(83)` after the first preparation copy or after complete verification
inside its final transaction. Both bypass Python cleanup. Independent reopening
retains PREPARING/VERIFYING, refuses reuse and preserves the original costs.
This tests actual process death, not power loss, arbitrary disk failure, native
Codex execution, Minecraft or OS isolation. Game/native source records are
synthetic; no provider call is made.

Read-only reconstruction passes **19/19**: committed intent/events, one reserved
pair, retained partial/complete files, no new native job, absent launch authority,
unchanged database hashes and real accounting. Ruff and whitespace checks pass.
No matching owned runtime remains. All40 real authority table hashes match
before/after; exposure stays $4.887796/$10 with all holds and consumed decisions.

Private bundle `2026-09-25-m1-probe-verification-fence-01` contains4754 files,
43,280,324 bytes. Its externally pinned seal is
`fcb1afe2e6a8b5146b7069572d7366f3a67d5836174bf8158bc9df062223397b`.
It retains initial failures, final test trees/JUnit/log, source snapshot,
authority snapshots, read-only audit and stopped-process inventory.

## Remaining work

Continue the disposable native probe adapter and held launch/disposal boundary,
with a fresh source whose policy/configuration refs resolve before registration.
Preserve campaign activation and evaluation-account import guards while allowing
probe-local adaptation. Live matched worlds, N>1 positive preparation, resource
admission, development-only practice, canary disposal, final runtime isolation,
T05 and scorer controls remain open. No M1 paid authority or qualification is
inferred; unrelated M2-M7 work remains unchanged.
