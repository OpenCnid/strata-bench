# M1.4b no-self-play capability enforcement

**Native follow-up:** [actual verification](2026-09-25-m1-no-self-play-native.md)
retains the first feature-only configuration failure. The pinned CLI additionally
requires `agents.enabled=false`, now enforced live. The changed profile passes
37/37 plus22/22 reconstruction; matched controls and full G1 remain open.

SPEC13.2 requires native direct reasoning/artifact editing with helper/self-play
tools disabled. The existing retention registration checked `self_play=false`
but did not bind native helper capability to that arm; older synthetic retention
fixtures even enrolled a helper. Their historical export/retention evidence is
preserved, but it cannot establish the complete no-self-play control.

This source change adds a read-only arm guard at native launch (including an
unbrokered plan), request admission and broker use. Registered no-self-play
requires the exact declared agent configuration, zero helpers, root executor
scope, no helper activation, and an explicit helper-free broker policy. Missing
registration for a declared disabled agent or a contradictory existing job
fails before a new dispatch/envelope/tool effect. New registrations also require
zero helpers. Historical stopped reconstruction does not rewrite registration.

Two separate basic/team broker policy identities use closed settings policy /4,
with `features.multi_agent_v2=false`. Selected campaign tool projection /6 pins
an executor-only functions namespace and carries no helper reference; old
projections remain unchanged. The team form retains the existing separately
scoped team API, distinct from reasoning helpers. Operator NativeLaunch schema
is regenerated, also correcting its stale omission of the existing team policy
and private team reference. All record/schema consistency cases pass. This pin
does not supply RuntimeQualification or paid authority.

Corrected synthetic no-self-play fixtures now have only root admissions and
actual root costs (14 fixture units in their stopped export), not fake helpers.
This is not a matched experiment or evidence of an ablation effect. Full-arm
helper behavior and historical fixture results remain separate.

## Verification

Windows/Python3.12.14, this checkout's source, local synthetic providers:

- Initial checkpoint/projection/admission selection:103 passed in35.06s.
- Broker/native/team/activation/revision/export regression selection with the
  initial arm cases:250 passed in200.08s.
- Expanded arm cases:25 passed in3.52s, followed by the final additional
  unbrokered-launch case in the final selection below.
- Final arm/records/launch-integrity/sealed-native-game selection:108 passed,
  three existing Windows symlink-privilege skips in33.84s. Includes26 arm cases;
  overlaps above, so these counts are not summed as distinct coverage.
- Final Ruff and whitespace checks pass. The first regression command named a
  nonexistent test module and ran no tests; the first archive command lacked
  the evaluator import path and failed before writes. Both setup failures are
  retained in the check record, corrected without an experiment rerun.
- Current-source read-only reconstruction of both sealed full-arm handoff
  episodes passes42/42. Their original37/37 reports, profile/export/checkpoint
  identities, process-drain evidence, costs, exact active scripts and fresh
  context/private-state checks remain unchanged. The producer seal verifies.
- All40 real authority table hashes still match; exposure$4.887796/$10 and all
  unresolved holds/consumed decisions remain unchanged. USD0; no native/game run.

Private source/check/audit bundle:
`C:/Users/Darian/.strata/evidence/2026-09-25-m1-no-self-play-source-01`,
403files/4,210,721bytes, seal SHA-256
`d73823a1abb111dcb69872dd8816dfd8af64dfef4ddca53fcf9584f913ae0ab7`.
`final-focused.xml` records the final tests; `result.json` records reconstruction.
The archived process query has an over-escaped path filter and is not process
absence evidence. Recheck actual owned process state before the next execution.

## Remaining acceptance

M1.4b is in_progress, inheriting M1.4, F03/F04/F07/F11/F16, N01/N04/N06,
C06/C07/C12/C14/C20/C36 and T01/T04/T06/T11. Actual pinned native /6 catalog,
missing-tool spawn refusal, zero child admission/cost, permitted root game and
artifact behavior and fresh retention still need authentic evidence. A new
arm must be registered before source jobs; never relabel a used store. Preserve
matched opportunity ceilings/public schedules and report actual spend in later
frozen/no-self-play controls. Full T04/T06/T11 and G1 remain not_run; full
settings/scorer/probe requirements and unrelated M2-M7 statuses are unchanged.
