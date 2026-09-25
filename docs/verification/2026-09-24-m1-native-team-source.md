# Versioned native team facade — source verification

M1.3b.9b is implemented_unverified pending actual native integration. Coverage
inherits M1.3b.9: F07/F16, N01/N04, C13, partial T01/T06, the minimal M4.1
dependency required by G1. No runtime qualification or campaign-team acceptance
is claimed. M1/G1 remains active.

The explicit broker policy `native-stdio-projected-artifacts-executor-game-team/1`
adds one typed `team` MCP facade with send/receive operations. The historical
policy retains exactly its four tools. Closed settings policy /3 and selected
conformance tool projection /4 bind the expanded catalog. Projection /4 requires
the selected gpt-6-luna, conformance purpose and one or two helpers; it cannot
expand an old campaign/development authorization. The private communication-policy
reference is bound into NativeLaunch's profile digest and omitted when absent,
preserving old model serialization/profile identities. Launch revalidates copied
models before touching runtime state.

Preflight, dispatch admission and broker grants require the running controller
roster/epoch, live lease, matching private policy and matching simulation state.
Native metadata identifies the caller. Only its executor can use the team facade;
helpers retain their artifact capability but cannot impersonate their parent or
another body. The service rechecks native authority inside the same transaction
before effects and before commit. The existing publication fence also checks
revocation before returning output. Policy/lease/epoch/state changes fence an
already enrolled caller. Arguments and rejection errors expose no private policy
bytes, paths or credential data.

Each committed native team operation has a private receipt tied to its exact
broker-call event, request and response digest. Stopped export joins those
receipts to immutable request identity, actual message/recipient/cursor data and
explicit acknowledgments. It retains committed effects even when publication
was subsequently fenced. Missing, duplicated or inconsistent successful receipts
refuse export. Only these immutable scoped receipts enter the new export source;
this does not restore shared queue state or authorize a campaign checkpoint.
Old profiles' export source is unchanged.

## Executed checks

417 distinct focused tests pass; three existing opt-in launch integration cases
remain skipped. These are synthetic controller/native-wire source tests and owned
process fixtures, not a real CLI team conversation, model call or Minecraft run.
The 34 new facade cases include positive send/receive/ack, helper and cross-scope
refusal, live policy/lease/epoch revocation, commit rollback, exact projection
versioning, error sanitization and coherent stopped-evidence corruption.

The first focused group passes203/203. Compatibility collection first fails on
the existing test_native_piloting tools import; the explicit tools path resolves
it. That group reports168 passes, eight outdated SimpleNamespace fixture failures
and three opt-in skips. Test stubs now declare the broker policy and the same nine
bootstrap mutations exercise both old/new catalogs. The expanded core/facade
group passes105/105, and final native/launch/export/facade group passes123 with
three skips. Counts overlap;417 is the distinct passing total. Ruff and whitespace
checks pass. Initial failures remain recorded here and in private verification.

```powershell
.venv/Scripts/python.exe -m pytest -q tests/test_native_team.py tests/test_team_protocol.py tests/test_native_broker.py tests/test_native_tool_projection.py tests/test_native_admission.py --tb=short
.venv/Scripts/python.exe -c "import sys; sys.path.insert(0,'tools'); import pytest; sys.exit(pytest.main(['-q','tests/test_native.py','tests/test_native_export.py','tests/test_native_skills.py','tests/test_native_conformance.py','tests/test_native_piloting.py','tests/test_launch_integrity.py','--tb=short']))"
.venv/Scripts/python.exe -m pytest -q tests/test_native_team.py tests/test_team_protocol.py tests/test_storage_controller.py --tb=short
.venv/Scripts/python.exe -m pytest -q tests/test_native_team.py tests/test_launch_integrity.py tests/test_native_export.py tests/test_native.py --tb=short
.venv/Scripts/ruff.exe check .
git diff --check
```

The sealed source-only bundle is
`C:/Users/Darian/.strata/evidence/2026-09-24-m1-team-facade-source-01`:
16 files/228,563 bytes, seal
`7b86d00e1ca56f4c8717e10df9fff25388918fe5a22d2e921be1b741df3e17b3`.
It retains source, observed verification results and WAL-aware authority readback.
All40 authority tables match the prior specific-bounds checkpoint; no matching
owned fixture process remains. Exposure and every historical hold stay unchanged.

## Required next evidence

M1.3b.9c must exercise actual selected native jobs through the sealed broker:
sender/receiver roots in the same declared controller roster, durable delivery,
send dedup, cursor/explicit ack, helper refusal, foreign-campaign/sender/epoch
refusal and exact stopped receipt reconstruction. Use a private synthetic
controller with an owned live heartbeat, bound policies and separate job/agent
identities. A second separate store with copied campaign labels cannot prove
roster delivery. No simultaneous game-body capacity claim follows from this test.

No paid inference is needed for that scripted native fixture. Actual-game and
paid model qualification retain their separate evidence/authority requirements.
Complete G1 skills, capable keybindings, scorer controls and probe boundaries
remain open; unrelated M2-M7 work is unchanged.
