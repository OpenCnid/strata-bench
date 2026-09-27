# M1 selected-runtime boundary: first conformance slice

Operator-only. M1.3b.1; F03/F04/F07/F16, N01/N04/N06,
C06/C12/C13/C20/C36, partial T01/T04/T06. M1 is in_progress and G1 remains
not_run. No RuntimeQualification, protected-scoring or full isolation claim.

## Implementation

[NativeToolProjection/3](../../src/mcbench/native_tool_projection.py) adds a
separate exact-catalog policy for `gpt-6-luna`, purpose `conformance`, and one
or two configured helpers. It does not allow campaign or development-piloting
use, change /1 or /2, enroll a helper, authorize paid dispatch or relax runtime,
credential or budget prerequisites. Every actual caller still passes the
existing exact metadata/catalog/admission/receipt checks. Model, purpose,
helper count, configuration and source changes require their own profile.
This fixture exercises **one** clean helper; two-helper behavior remains open.

[Owned runtime canaries](../../tools/native_runtime_boundary.py) extend the
existing credential-free native fixture. Root and helper test direct IO
globals, ordinary/host/async function constructors, dynamic imports of
filesystem/process/subprocess modules, an owned private module, an owned HTTP
listener and a disposable fake credential file. Artifact attempts cover absolute
paths, traversal, alternate streams, CAS-shaped guesses and the other
participant's private artifact. Existing positive artifact/game controls,
shell/patch direct-dispatch rejection and empty resource catalogs remain active.

The verifier binds outputs to caller and call ID, accepts identical repeated
context, rejects contradictory copies, duplicate/missing cases, wrong actors,
unknown errors, simultaneous error/success and extra fields. Expected import
rejection is exactly `unsupported import in exec`; absence of private bytes
alone cannot pass a missing attempted route. The native code-mode constructors
can execute ordinary JavaScript but cannot obtain a `process` global in these
tests. This preserves permitted computation rather than treating all computation
as an escape.

## Actual native evidence and retained failures

Both attempts use the pinned CLI 0.154.0-alpha.6.2 and its verified companion
executables, Dovetail `15c306ccfef28eb5f616fadcd5fd8eac0663e361`, the selected
GPT-6 Luna metadata and a **local scripted provider with a synthetic game
worker**. No real model request, Minecraft process or shared-desktop input.
Raw profiles, fake credentials, captures, source and databases remain private.

| Attempt | Actual outcome |
|---|---|
| `2026-09-24-m1-runtime-boundary-01` | `FORBIDDEN_ENVIRONMENT` before native launch: the fixture tried to add a private marker variable outside the environment allowlist. Preserve this failed fixture and unchanged enforcement. |
| `2026-09-24-m1-runtime-boundary-02` | Changed fixture uses existing environment access and its disposable fake auth file. Native root/helper finish normally in 42.598341 seconds; 11 settled requests, 110 input/44 output tokens and 154 synthetic fixture units; both participant envelopes CLOSED and native job FINALIZED exit0. Original verifier68/74 retains six unrecognized import-error checks. |
| Offline reconstruction of `-02` | Reviewed the actual exact native import denial, updated only its recognition and reconstructed the unchanged captured requests. Independent24/24 joins all11 raw CAS captures, ingress authentication, request admission, exact root/helper catalog, settled attempts, participant closure and aggregate accounting; all16 boundary checks pass. The original68/74 report remains unchanged. No rerun was used to change this result. |

The successful capture's exact native profile is
`79957879b84a6f4ca8373de693656c10399e010f9d928242b856eed130f4e865`.
The reused pre-reviewed projection file is SHA-256
`05cbc452d2bb8c40623b3207c78e69499a7f6a1f57cea7425169fe1df0ea2294`;
it was pinned before dispatch, not learned from the request being admitted.
The sealed producer source and separately retained revised audit source are
distinct. Original shell-enabled sandbox sibling/loopback failures remain
failed under their historical profiles.

| Private bundle | Files / bytes | Seal SHA-256 |
|---|---|---|
| `2026-09-24-m1-runtime-boundary-01` | 3,656 / 70,728,917 | `d646097fa41742e349be04e2e59e880c0bf345f394a8f0d00a3d4a71b9af7007` |
| `2026-09-24-m1-runtime-boundary-02` | 3,792 / 75,409,484 | `6dfe10964be008dbe025058331a4d24de4419cd7039510823b98b58195d4e0b2` |

WAL-aware read-only checks retain all40 real authority tables unchanged.
The original $4.887796 exposure, $0.7554 hold, four full $1 envelopes and
consumed decisions remain untouched. The synthetic store is separate and its
154 fixture units are neither dollars nor OAuth charges. Post-run process
inventory finds no matching owned fixture process.

## Checks and remaining work

187 focused Python cases pass across native launch, admission, ingress,
catalog projection and both canary verifiers. After the import-recognition
change, all37 boundary-verifier cases pass again. Full source Ruff and
`git diff --check` pass. Tests include policy-scope changes, helper bounds,
changed catalogs, missing/contradictory capture and simulated successful leaks;
they are not authentic game or model evidence.

Commands:

```powershell
.venv/Scripts/python.exe -m pytest -q tests/test_native_runtime_boundary.py tests/test_native_tool_projection.py tests/test_native_admission.py tests/test_native_ingress.py tests/test_native.py tests/test_native_broker_canaries.py --tb=short
.venv/Scripts/python.exe -m pytest -q tests/test_native_runtime_boundary.py --tb=short
.venv/Scripts/ruff.exe check .
git diff --check
```

Next qualify remaining code-mode output/media helpers and cross-agent
communication/state/lifecycle surfaces, then join the boundary to actual game
and protected credential admission. Complete executable-skill, two-helper,
settings, scorer and probe contracts remain open in the
[G1 audit](2026-09-24-g1-coverage-audit.md). Catalog absence, these named negative
routes and same-user process placement alone are not a full T06 certificate.
No new paid M1 authority is inferred from D18/D19.
