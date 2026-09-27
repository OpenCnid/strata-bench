# Inference closure before native resume — September 27

Private evidence sealed: 285 files / 9,591,768 bytes,
SHA-256 `295aaaede79d6c26db9ba6bab48ce4ae1b51e6bf18bba6511216a309e31f7376`.
All 40 authority tables, eight telemetry holds and both installed-file hashes
are unchanged; final matching runtime process count is 0. All 460 milestone IDs
and 2,177 local links were checked. This pointer postdates the archived snapshot.

M1.1c.3.4 remains `in_progress`; no aggregate G1 suite closes. The previous turn
was progress at `3e1a527`. This change invokes the existing inference closure in
the real controller resume path rather than leaving it as a separate service.

[NativeRepairResume](../../src/mcbench/native_repair_resume.py) now freezes the
owned inference window before journaling a new resume intent. If any tracked
call is pending, the method refuses with `REPAIR_INFERENCE_PENDING`; the public
pause stays held and no worker resume call or durable resume intent occurs.
Existing calls keep their original settlement path and costs. No lease extension,
replay, new allowance or inference call is introduced.

Once tracked calls settle, the controller stores their frozen audit privately
and rechecks it under the same database transaction as the resume intent and
audit-reference binding. A changed audit or expired decision refuses dispatch.
New `ControllerResumeWitness/2` receipts carry the inference reference. Repeated
status and subsequent worker-charge measurement revalidate that original binding
and audit. Removing a new binding cannot silently downgrade it to historical
status evidence. Legacy `/1` status reconciliation remains available; it does not
provide the new prerequisite for measurement or complete accounting.

Executed on Windows, Python 3.12.14, Node 24.19.0 and Java 17.0.20.1+1:

- 31 distinct focused source/controller cases pass across repair inference,
  native resume fault handling and retained consumption. This includes missing/
  changed audit bindings, legacy absence, storage faults and retained overruns.
- Two selected actual controller → Node → Windows guardian → replacement JVM
  cases pass: publication and lost resume reply. The publication case admits a
  synthetic helper dispatch, observes refusal before worker resume, settles its
  one usage receipt, then resumes once and retains the audit through measurement
  and publication. The next action executes without replaying the prior action.
  Lost-reply recovery queries the original decision and preserves its audit.
- Ruff and whitespace checks pass. Production Java, installed game files and
  worker wire/profile policy are unchanged.

The first process selection retained one pass and one failure. Publication
measurement observed21 primitives against the original20 reservation and correctly
refused further work. Its opening worker counter was1 and closing counter22:
the fixture had waited for native preplay completion but not the worker's final
observation/charge join. The corrected fixture waits for the public worker
terminal receipt before requesting repair. The final process case measured19
repair primitives within the unchanged20 reservation. The failed result, costs
and source diagnosis remain archived; no cap, deadline or gate was relaxed.

Game body, helper provider/usage, native effect verification and settlement
producer in these process tests are synthetic. The Java/Node processes and their
owned lifecycle/transport are real. This is not authentic Minecraft, paid model,
helper isolation or complete settlement evidence. No actual inference or game
run was made, and D18/D19 authority remains M0-only.

Coverage: M1.1c.3.4, F03/F06/F07/F09/F11/F16, N01/N02/N03/N04/N08;
T01/T04/T05/T06 G1 dependency. Scope, private reference custody, budgets, clocks,
versioned evidence and at-most-once decision history are retained. Both campaign
permission and full consumption-settlement claims remain false.

Next: join complete primitive/body interval allocation and final publication to
controller settlement/original-lease completion, then qualify authentic gameplay
repair/restart/restoration/resume. The native-health failure and the remaining
contract/isolation/scorer/probe acceptance cases remain open.
