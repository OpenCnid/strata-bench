# Native job-bound inference ingress

September 20, 2026. Operator-only. M0.1c.2b.2e is **implemented_unverified**:
source and actual pinned-CLI/local-synthetic-provider evidence, not qualified
OAuth dispatch or complete credential/OS isolation. M0 remains incomplete,
G0 fails and G1–G5 are not run.

Affected coverage: F03/F04/F07/F11/F16, N01/N03/N04/N06, C06/C12/C20/C36,
partial T01/T04/T06/T07/T12 and G0 items 1/6. This extends the existing
accounting/admission implementation; it does not repeat the completed retry,
compaction, streaming or restart integration matrix.

## Implemented behavior

[native_ingress.py](../../src/mcbench/native_ingress.py) defines
`native-job-http-header/1`. A random 256-bit capability is supplied by the
native custom-provider transport in `X-Strata-Ingress`, outside model arguments.
Its durable registration stores a digest bound to one job, exact launch profile
and literal loopback authority. Only the two Responses routes are permitted.
Unknown/stopped/revoked/expired jobs, changed profiles, missing/wrong/duplicate
capabilities, wrong/duplicate Host, cookies and proxy credentials reject.
Unsupported provider authentication commands, environment headers, query
parameters and nested override aliases reject during profile validation.

The credential is operator-private in the launch plan/process configuration;
it is not an OS boundary against arbitrary same-user code. Its secrecy depends
on the restricted native tools and sealed bootstrap. It neither authenticates
model-supplied identity nor replaces the native stdout/parent/context checks.

Registration replay cannot renew revocation. Each authenticated request binds
its operation and exact body digest durably. Native participant admission checks
that binding before creating child reservations; the dispatch transaction checks
it again before reserving/forwarding. Distinct requests remain distinct costs;
previous intents never replay and revocation/restart never release unknown holds.
Live broker profiles now require an explicit ingress policy in addition to the
existing bootstrap and private qualification evidence. Profiles without the new
optional field retain their previous digest/intent semantics.

The existing local-provider fixture authenticates headers before reading or
capturing request bodies. It journals hashes and bounded denial codes, not header
secrets. Upstream OAuth headers are a separate, explicitly declared mode and
validated without persisting their contents. That mode has source tests only:
the actual fixture uses no upstream credential, and live upstream credential
storage/forwarding remains unimplemented and unqualified.

Supported static provider headers were checked against the saved schema of the
pinned binary and the official [configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference).
The documented custom-provider authentication switch is distinct from these
headers; see [Codex authentication](https://learn.chatgpt.com/docs/auth). Neither
document is evidence that this candidate has qualified actual OAuth behavior.

## Executed verification

```text
python -m pytest -q tests/test_native_ingress.py tests/test_native_admission.py tests/test_native.py tests/test_inference_dispatch.py --tb=short
python -m pytest -q tests/test_native_ingress.py --tb=short
python -m ruff check src/mcbench/native_ingress.py tests/test_native_ingress.py tools/native_mcp_identity_probe.py tools/native_dispatch_probe.py src/mcbench/native.py src/mcbench/native_admission.py src/mcbench/inference_dispatch.py
python tools/native_mcp_identity_probe.py --codex '<pinned codex.exe>' --output '<fresh private directory>' --broker --admission --bootstrap --ingress
```

Affected suite: **99 passed in 15.32 s**. After adding three explicit
cross-job/body/helper-envelope negatives, the ingress file alone passed
**27 tests in 1.45 s**; production source was unchanged. Targeted Ruff passes.
The tests cover revocation between admission and dispatch, restart/registration
replay without refunds, digest rebinding, credential separation/redaction and
rejection before helper envelope allocation. No full-suite/release claim.

Actual native fixture `2026-09-20-native-ingress-01` passes with CLI
`0.154.0-alpha.6.2`, binary SHA-256
`960c111d47afd61669954b9df9e56083e302edbfa3ef6962d81dcc14a30051dc`
and Dovetail `15c306ccfef28eb5f616fadcd5fd8eac0663e361` unchanged.
All responses and worker results are deterministic fixtures, not Minecraft or
model-generated play. Raw evidence stays in private `.strata/evidence/`.

- Seven root/helper requests authenticated, admitted and settled; 70 input,
  14 cached-input subset and 28 output tokens, **98 synthetic fixture units**.
  No actual charge or API-equivalent experimental debit is inferred from them.
- Seven owned negative HTTP clients (missing/wrong/duplicate capability,
  wrong/duplicate Host, unapproved route and cookie) receive 403 before request
  capture/reservation. They produce no provider call or child envelope.
- All 18 broker/admission/ingress checks pass. Scoped executor worker control,
  helper result write and forbidden helper-game/parent-write checks remain live
  positive/negative controls. Both participant envelopes close; aggregate costs
  count each receipt once and do not add envelope reservations again.
- The ingress secret is absent from captured native request bodies, tool
  feedback, decoded native stdout/stderr and exported journal. This is an exact
  fixture observation, not a general proof about every native/plugin code path.
- Native process duration is 35.433 s; process exit is followed by explicit
  ingress fencing and budget closure to `FINALIZED`. All owned services are
  terminal. No shutdown acceptance threshold is changed or claimed passed.

Profile: `5b1eab12eac7a8f53e174a551ba12abe5d8ba355d4703824e3420156930591e3`.
Result SHA-256: `cecf8db9d07b5cbbd84d8ab0095c5eabeae634e231c758addcd5b661eafacf8b`.

## Remaining dependency

Read-only inspection of the original project account still finds authorization
`validation-2026-09-18`, schema 2, one explicit migration and zero experimental
operations. The original $10 allowance is unchanged. No live OAuth inference,
Minecraft launch, evaluator exposure or shared-desktop input occurred.

Next implement supported upstream OAuth credential separation and authenticated
transport without rebuilding receipt accounting. Then finish actual Dovetail
skill-body projection/learned-artifact activation/export and helper lifecycle,
and qualify the full runtime/game prerequisites before the existing <=$1 trial.
The old loopback, five effective-file, 500-ms shutdown and Mineflayer/E9E failures,
and scorer/provenance/recovery gaps remain unresolved in their recorded scopes.
