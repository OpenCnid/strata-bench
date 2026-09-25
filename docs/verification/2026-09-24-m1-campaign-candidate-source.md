# Campaign boundary integration fixture

M1.3b.9d remains in_progress. F03/F04/F07/F16, N01/N04/N06,
C06/C12/C13/C20/C36, partial T01/T04/T06. This is source and synthetic verifier
evidence; no actual native/game execution or RuntimeQualification is claimed.

## Implementation

The explicit `campaign_boundary_probe` entry in `native_mcp_identity_probe`
combines the existing scoped real-worker path with the owned synthetic team
controller. The new CampaignBoundaryProbe checks worker campaign/avatar/epoch
against the selected roster identity before creating canaries. The caller owns
the actual worker/server lifecycle and controller heartbeat. NativeWorker still
binds the executor and revokes the game lane on native exit; helpers have no
game or campaign-team authority. GameProbe derives its bounded look action from
permitted observations. The provider remains local and scripted.

This candidate uses campaign projection /5, the team broker policy, selected
Luna metadata, one clean helper, and explicit ingress/OAuth-fixture/bootstrap
controls. The fixture retains `simulation=True` and synthetic controller
readiness. It is not an admitted production campaign or proof of simultaneous
game-body capacity. Its report distinguishes these claims. It cannot supply
M1 spending authority, issue qualification or import an old paid permit.

The new scenario keeps root/helper artifact controls and team send/dedup/scope
refusals, then runs filesystem/environment/process/network/credential probes
through the actual native interface when invoked. Separate protocol phases
attempt direct shell dispatch and both patch forms. A versioned campaign pin
and the verifier's explicit `team_enabled=True` permit only the fifth team
tool; old canary catalogs retain their original four-tool expectations.
Unknown/extra tools still fail. The helper's four-wait completion bound remains
unchanged; the candidate permits at most20 scripted requests, four helper
requests,64 broker calls per participant and90 seconds per native job. These
are fixture limits, not a change to campaign budgets or G1 acceptance.

The fake credential probe now targets the selected job's actual profile
directory instead of assuming `root-profile`. Its positive control requires
the owned fake credential file to exist. Reports check unchanged owned files,
absent secret bytes in requests, the listener's successful public control and
zero unauthorized listener hits. They also require both actors' exact observed
denials and permitted artifact roundtrips. Missing heartbeat admission closes
the owned listener and cannot rearm the fixture.

## Checks and limitations

89 focused tests pass in16.43s. The initial87-pass run is retained; two added
cases cover missing private-file detection and failed-entry listener cleanup.
Tests corrupt or omit helper routes, widen the catalog, simulate shell/patch
success, leak worker/private canaries, hit the owned private listener, remove
the credential target, change/delete a private file and skip protocol phases.
They reject mismatched worker identities and ambiguous mode combinations before
launch. Changed-file Ruff and `git diff --check` pass.

```powershell
.venv/Scripts/python.exe -m pytest -q tests/test_native_campaign_boundary_probe.py tests/test_native_runtime_boundary.py tests/test_native_broker_canaries.py tests/test_native_team_channel_probe.py --tb=short
.venv/Scripts/ruff.exe check tools/native_campaign_boundary_probe.py tools/native_mcp_identity_probe.py tools/native_runtime_boundary.py tools/native_broker_canaries.py tests/test_native_campaign_boundary_probe.py
git diff --check
```

WAL-aware read-only snapshots match all40 original authority tables before and
after. Exposure remains $4.887796/$10 with all holds and consumed decisions.
No matching owned native/game/test process remains. No provider call, game
launch or shared-desktop input occurred. Private source bundle
`C:/Users/Darian/.strata/evidence/2026-09-24-m1-campaign-candidate-source-01`
has8 files/125,034 bytes; seal SHA-256
`d818c8c390529facd727df57daf83a44ebb627fa0ff2726d18e3bba48dc53551`.

Next prepare the outer owned game lifecycle and a fresh private, source-pinned
candidate. The existing M0 game runner validates M0-specific retention/profile
identities and must not simply be relabeled or have those checks bypassed.
Reuse its held pack/worker, stop and journal primitives through explicit M1
orchestration. Execute the candidate only after validating fresh pack/worker/
native pins and current durable state; retain its original outcome and join
native requests, game receipts, worker journal, process drain and stopped
exports independently. The present tests do not prove those runtime joins.

The [profile reconciliation](2026-09-24-m1-profile-reconciliation.md) still
governs source/evidence transfer. Final provider/credential integration,
selected executable skills/fresh handoff, client-specific filtering and probe
disposal remain open, along with complete T05/T10/T11. M1/G1 is not complete.
