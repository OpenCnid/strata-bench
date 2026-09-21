# M0 native retention and complete-set materialization

September 21, 2026. Operator-only. M0.1c.2b.2c.4 advances partial
F03/F04/F07/F09/F11/F16, N01/N02/N04/N06/N08,
C06/C07/C08/C12/C14/C16/C17/C19/C20/C23/C36,
T01/T04/T06/T07/T11/T12/T13 and G0 items 1/6.
M0 is incomplete, G0 fails, G1–G5 remain not_run.

## Implemented boundary

[NativeCheckpointStates](../../src/mcbench/native_checkpoint.py) implements
`native-preregistered-retention-checkpoint/1`. A private
`NativeRetentionPolicy/1` binds the campaign, agent, system, arm, initial artifact
inventory and fresh-handoff mode through the stored CampaignConfig/AgentConfig.
Registration must precede every native job for that campaign/agent. Repetition
is idempotent; replacement or late registration rejects. Controller and native
simulation modes must agree. This adds no authority to the original inference
allowance.

`NativeCheckpointState/1` derives its root files from a committed, source-bound
stopped export. Immutable initial/docs/supplied files must match the frozen
baseline. Full and no-self-play retain current root artifacts. At an episode
boundary, frozen-persistence restores exactly the initial set; frozen-skills
retains current notes/handoff and initial skills. Mid-episode recovery retains
the same saved knowledge under the configured fresh-handoff mode. Every path
clears sessions/runtime caches, excludes helper-private inventories, enforces
the total handoff limit of 8,000 UTF-8 bytes and preserves cost accounting.

A scheduled target on an episode boundary cannot claim recovery to bypass the
retention transition. Unscheduled boundary classification still comes from the
private supervisor; authentic clock/lifecycle qualification remains required.
New components must use the latest executor source. Already committed history
remains available after subsequent jobs for legitimate development rollback.

Skill files retain their **draft** status. Existing active revisions cause
`NATIVE_REVISION_EXPORT_REQUIRED`; they are not silently dropped or downgraded.
Complete active revision/provenance/supporting-file capture and atomic native
activation are still required. Initial corpus selection remains an operator
responsibility; filename guards do not prove arbitrary text contains no secret.

[Checkpoints](../../src/mcbench/checkpoints.py) now requires this typed component
for native broker campaigns. Merely supplying existing workspace/runtime blobs
and a matching clean-stop assertion no longer suffices. Match checkpoint ID,
campaign/agent/epoch/system/pack, model, retained workspace/skills and ledger
position. Revalidate under the checkpoint writer lock before committing, and
again when loading. The old stopped `NativeState/2` cannot claim that retention
has already occurred.

`materialize_set` stages all recorded world/external files, every roster member's
retained workspace and private backend/keymap/runtime records in one new
operator directory. Member paths use identity digests, not raw IDs. Verify
every copied byte and the exact output inventory, recheck native source and
durable epoch/configuration, then rename the complete directory into place.
Changed/missing/extra files or an epoch advancing during copy prevent publication.
Existing destinations and previous committed snapshots remain intact.

The returned `RestoredCheckpoint/1` is explicitly labeled by simulation mode and
has `dispatch_authorized: false`. Only the workspace subdirectory is a candidate
for later scoped broker projection; private metadata is not gameplay material.
Fresh capabilities, backend restore assertions, native profile continuity and
actual session restart remain required. The native resume API rejects this
component as incomplete authority. Development-only recovery and unrefunded
costs remain enforced; materialization does not authorize a confirmatory rollback.

## Verification

Windows checkout, Python 3.12.14, existing dependencies. **103 affected tests
pass in 35.11 seconds**, with focused Ruff:

```powershell
$env:PYTHONPATH='src;evaluator/src'
.venv/Scripts/python.exe -m pytest -q tests/test_native_checkpoint.py tests/test_native_export.py tests/test_checkpoints_artifacts.py tests/test_native.py --tb=short
```

After final staging-race review, **28 native checkpoint tests pass in 26.25
seconds**, with focused Ruff. Coverage includes all four arms, recovery versus
episode retention, private helper exclusion, missing policy, immutable baseline
drift, aggregate handoff quota, mixed components, late/replaced policies, missing
active-revision support, source races, stale/during-copy epochs, unauthorized
configuration changes, corrupted/extra staged files, synthetic-to-live promotion
denial, restart, denied direct native resume and future unknown costs.

One intermediate negative fixture failed because it used the nonexistent
`native_jobs.digest` column; it was corrected to the actual `plan_digest` schema.
That fixture failure was not a passed lifecycle case.

Private `native-checkpoint-01` passes **10 audit checks**. A wholly synthetic
controller/native/accounting/world fixture commits a frozen-persistence set,
closes its database, then restores from a fresh Python process. The exact five
initial files return, with neither later notes nor helper-private results. Both
world and external-state files and all recorded agent components are present.
The original 56 settled fixture units plus a later unresolved 100-unit reservation
remain **156 synthetic fixture units**, uncertainty true, admission denied.
Three final review checks reproduce the same materialized manifest under the
additional staging guards, retain those costs and grant no dispatch authority.

A separate verified copy of the sealed prior native-export-02 store rejects
new checkpoint sealing with `NATIVE_RETENTION_NOT_REGISTERED`. The actual prior
native history has no preregistered retention policy; this work does not invent
one retrospectively. Its 17 requests/238 fixture units and original export remain
unchanged, and all 92 sealed source files verify before and after. This is a
recorded-native negative, not a new native or game integration trial.

The original OAuth authorization was separately read in read-only mode: the
same $10 estimated allowance, $0.7554 unresolved exposure and uncertainty remain.
No model inference, Minecraft launch or shared-desktop input occurred. Raw
artifacts, scripts, source generations and restored fixture sets remain private.
The sealed bundle contains 159 files (2,045,533 bytes); its manifest SHA-256 is
`1d4a3e3799ad62276682e2477e6c5294edcfb6c3e78e44557f32571cc0ccefc0`.

## Remaining M0 work

Complete skill supporting-file and active revision/provenance export, native
activation and fresh scoped broker/session restoration. Then qualify the joint
game/backend/native state and accounting boundary on the declared profile.
Existing clean-stop reports and pack persistence assertions still require their
authoritative integration evidence; this implementation does not turn synthetic
world blobs or operator assertions into an authentic Minecraft checkpoint.
Preserve OAuth uncertainty, sibling/loopback failures, all failed 500-ms shutdown
samples, five effective-file failures, Mineflayer/E9E incompatibility, private
scorer controls/provenance/parity and full recovery obligations.
