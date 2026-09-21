# M0 native helper retirement and slot reuse

September 21, 2026. Operator-only. M0.1c.2b.2c.1 advances partial
F03/F04/F07/F09/F11/F16, N01/N02/N04/N06/N08, C06/C14/C18/C20/C24/C36,
T01/T04/T06/T07/T12/T13 and G0 items 1/6. M0 is incomplete; G0 fails;
G1–G5 are not run.

## Implemented behavior

[Native admission](../../src/mcbench/native_admission.py) now retains helper
capacity after revocation, including unknown participant states. Revocation
fences the participant and descendants from further broker/dispatch access and
records the last admitted request ordinal. Existing closed participants never
reopen. Their names, identities and namespaces remain tombstones.

[Permanent retirement](../../src/mcbench/native_retirement.py) implements
`native-fenced-participant-retirement/1`. An operator-private
`NativeParticipantRetirement/1` binds the frozen job/profile/helper to two exact
root requests. The first must occur after the revocation fence and have settled
usage whose raw provider response issued the native `collaboration.list_agents`
call. The later admitted root request must contain that exact call and its
native tool result, reporting the helper completed or interrupted. Model prose,
an old snapshot, changed arguments, duplicated/missing results and unrelated
tools do not establish retirement. Live mode also requires authenticated ingress.

An incremental first-seen tool-call index survives context compaction. Reissuing
an old call ID cannot refresh an old status. Upgraded jobs lazily index their
private historical request captures before accepting a proof. The index is
transactional and idempotent; source digest conflicts fail closed.

Only a revoked leaf with all its calls settled and all descendants closed may
retire. Envelope closure uses the existing zero-owned-usage receipt identity;
descendant consumption stays charged. Full-job closure recognizes a previously
closed helper without counting it again. Repeating the same proof is idempotent
after restart; a different proof conflicts. A resumed old helper is denied, and
replacement requires a fresh name, thread and scoped namespace. Missing or
ambiguous usage retains the slot and exposure. There is no provider replay,
inferred receipt, budget reset or refund.

This retires broker/model admission capabilities. It does not establish complete
physical drain of an interrupted helper's background cells or already-started
tool operations. The native positive sample retires a completed helper. Complete
interruption/drain, restart/export and fresh-handoff qualification remain required.

## Source verification

224 distinct focused source checks pass: 207 in the affected controller suites
and 17 in the existing helper-fixture suite. Focused Ruff and whitespace checks
pass. The commands actually executed were:

```powershell
$env:PYTHONPATH='src;evaluator/src'
.venv/Scripts/python.exe -m pytest -q tests/test_native_retirement.py tests/test_native_admission.py tests/test_native.py tests/test_native_broker.py tests/test_native_tool_projection.py tests/test_native_ingress.py --tb=short
.venv/Scripts/python.exe -m pytest -q tests/test_native_helper_probe.py --tb=short
.venv/Scripts/ruff.exe check src/mcbench/native_admission.py src/mcbench/native_retirement.py tools/native_mcp_identity_probe.py tools/native_retirement_probe.py tests/test_native_retirement.py
git diff --check
```

The [new tests](../../tests/test_native_retirement.py) cover JSON/SSE issuance,
settled usage and restart idempotency, one-slot retention/replacement, old
broker/dispatch/name denial, stale and reused status IDs, legacy index backfill,
changed scope/tool/results, private evidence, descendant/pending/unknown holds,
unknown participant states, and finite local receipt waiting. These are synthetic
contract checks, separate from actual native evidence.

## Actual CLI with local synthetic provider

The [retirement fixture](../../tools/native_retirement_probe.py) extends the
existing sealed native identity fixture, preserving selected CLI
`0.154.0-alpha.6.2`, binary SHA-256
`960c111d47afd61669954b9df9e56083e302edbfa3ef6962d81dcc14a30051dc`,
Dovetail `15c306ccfef28eb5f616fadcd5fd8eac0663e361`, and `gpt-5.6-luna`.
It uses authenticated native ingress, the prior complete root/helper wire pins
and the explicit no-patch catalog. The declared fixture bound is 20 requests,
90 native seconds, one simultaneous helper and four requests per helper.
This changes only the synthetic trial allowance, not the original OAuth budget.

| Private bundle | Retained outcome |
|---|---|
| `2026-09-21-native-retirement-01` | Failed safely: native tool output returned before the preceding issuance receipt committed. Retirement rejected `RETIREMENT_ISSUANCE_UNSETTLED`. Seven settled requests/98 fixture units and one uncertain request remain; full 200,000-unit synthetic envelope is held. Helper remains REVOKED, slot retained, no replacement; native exit 1, accounting UNSETTLED. |
| `2026-09-21-native-retirement-02` | Changed fixture waits at most 0.5 s for that known local DISPATCHING receipt; missing/uncertain/timeout cases abort. All 31 integration checks and 27 independent audit checks pass. Fifteen admitted/settled requests plus one rejected old-helper follow-up; three CLOSED envelopes, FINALIZED exit 0. |

Final profile:
`87a98e20aef1ca464b37decf7c2026a5928cf3255d1b4aa4063160f9f47cce83`.
Its revocation fence is request ordinal 6, native status issuance 7 and actual
tool-result observation/first call-ID occurrence 8. The actual result reports
the original helper completed. Its follow-up fails `NATIVE_ADMISSION_SCOPE`
before provider forwarding; the fresh replacement then completes with a distinct
identity and namespace despite the one-slot limit.

Eleven root, two original-helper and two replacement requests consume 150 input
and 60 output tokens, settling once to 210 **synthetic fixture units**. These are
neither real model charges nor estimated OAuth spending. Native lifetime is
39.3812 s; setup plus execution is 79.2030 s. Source hashes remain unchanged,
every admitted request matches its prior wire pin, and the final process audit
finds no owned native CLI/broker processes for either trial.

Across both private stores, 22 settled requests account for 308 fixture units;
one uncertain request and the first store's full hold remain. Read-only original
authority inspection confirms the unchanged $10 total, authorization digest and
$0.7554 unresolved OAuth hold. No real inference, Minecraft, shared input,
RuntimeQualification or acceptance threshold change occurred.

Raw requests, receipts, profiles, source archives and failed verdicts remain in
private storage. Sealed inventories preserve both original outcomes:

| Bundle suffix | Files / bytes | Manifest SHA-256 |
|---|---|---|
| `retirement-01` | 8,912 / 126,113,176 | `77ce6d81c5cc99a5b7486e5d9116807a9b0833f2c92ef7eaf3bb15141e2ce9b6` |
| `retirement-02` | 8,942 / 126,824,328 | `1085db011fcd32d0d57cc92d1313c0d32a384a583853cbca51c70ed657655d1a` |

## Remaining work

Next connect helper retirement to bounded cancellation/drain evidence for
already-started broker calls and native background cells. Do not treat the
completed-helper sample as interruption or full capacity/resource qualification.
Continue required skill supporting-file/learned activation/export and fresh
handoff work after their prerequisites. Existing successful accounting,
patch/projection and state matrices do not need unchanged reruns.

Retain the underlying sibling-read/loopback failures, original OAuth uncertainty,
all failed 500-ms shutdown samples, five effective-file failures,
Mineflayer/E9E incompatibility and remaining scorer/provenance/recovery gates.
M0–M6 remain required; M7 and other extensions retain their activation conditions.
