# M1 runtime profile reconciliation and campaign catalog

Operator-only. M1.3a/M1.3b.9d; F03/F04/F07/F16, N01/N04/N06,
C06/C12/C13/C20/C36, partial T01/T04/T06. M1/G1 remains active and G1
not_run. This audit issues no RuntimeQualification or evidence transfer.

## Evidence and source reconciliation

At source commit `45cf10f`, read-only EvidenceBundle verification validates
all files in nine externally pinned private bundles. WAL-aware stopped database
reads reconstruct eleven FINALIZED NativeLaunch profiles using the current
reader. They share the pinned CLI binary/Dovetail identities and selected Luna
metadata, but have different exact profile digests and scripted providers.
Neither the synthetic provider nor a FINALIZED job proves authentic model play.

The comparison covers all 98 current top-level `src/mcbench/*.py` modules.
It is a source inventory comparison, not dependency analysis or blanket
equivalence. Tests, fixture drivers, bootstrap dependencies, catalogs, paths,
prompts and provider/game bindings still need their own comparison when used
in a qualification transfer. Original reports and failed attempts stay intact.

| Sealed bundle suffix under `2026-09-24-m1-` | Native profiles | Same modules | Changed modules | Current modules absent from captured source |
|---|---:|---:|---:|---:|
| runtime-boundary-02 | 1 | 83 | 12 | 3 |
| output-boundary-01 | 1 | 83 | 12 | 3 |
| state-boundary-02 | 1 | 83 | 12 | 3 |
| retirement-boundary-01 | 1 | 83 | 12 | 3 |
| notification-drain-01 | 1 | 83 | 12 | 3 |
| process-drain-02 | 1 | 84 | 12 | 2 |
| helper-pair-03 | 1 | 85 | 11 | 2 |
| cross-team-01 | 2 | 85 | 11 | 2 |
| team-native-01 | 2 | 98 | 0 | 0 |

The first five differ in broker/stdio, communication, native launch/admission/
bootstrap/policy, cell lifecycle, export, game authority, tool projection and
process management. Process-drain adds its source but that module subsequently
changes; helper-pair/cross-team have the current cell lifecycle. Team modules
are new relative to the preceding slices. These include enforcement changes,
not just report formatting. The named original results remain valid for their
original identities; none is automatically a passing result for the current
combined runtime. Per-file old/current hashes and complete profile digests are
retained privately.

After this inventory, the change below modifies only the runtime's projection
module. Current-reader checks reconstruct both retained team /4 projections and
both committed exports exactly. Those readback checks do not rerun native /4
or exercise new /5 in a native process.

## SPEC13.5 routes and remaining evidence

This matrix states the smallest unresolved integration claims. It does not
replace the complete T04/T06 tests or promote a union of unlike profiles.

| Required route | Retained evidence and enforcement | Remaining qualified-profile evidence |
|---|---|---|
| Filesystem traversal and CAS guesses | [First boundary](2026-09-24-m1-native-boundary.md): root/helper absolute, traversal, alternate stream, CAS and foreign artifact attempts refuse; own artifacts work | Bind actual worker/server/settings/evaluator targets and allowed artifacts to the combined source/profile; validate its canaries and unchanged private bytes |
| Process inspection and environment | First boundary: IO globals unavailable, process/subprocess imports denied, code constructors cannot obtain process; native launch restricts environment | Combined root/helper host boundary, actual worker ownership and no credentials/private environment in returned data |
| Inherited instructions/plugins | First boundary: ancestor canary absent; exact immutable skill catalog and native tool projections | Final corpus including learned overlays, executable-skill support and fresh handoff; prove no operator instructions or inherited user tools |
| Localhost/network scans | First boundary: owned HTTP target and resource/import attempts denied, listener positive control; no general network tool | Final controlled inference/game routing, owned private-service targets and permitted request path; transport credentials remain host-only |
| Credential access | Fake credential canaries, filtered headers and captured-request checks on named conformance profiles; old fixed-TLS OAuth receipt is a distinct M0 profile | Final provider credential boundary and all-call gateway joins, with no M0 spending/permit transfer |
| Tool schemas/errors | Closed broker/tool projections, malformed and foreign calls refuse; [team](2026-09-24-m1-native-team.md) has fourteen actual denials | New campaign projection, actual game/settings error paths and complete filtered catalog; no private schema/error bytes |
| Returned logs/crash dumps | [Output](2026-09-24-m1-output-boundary.md), [state](2026-09-24-m1-state-boundary.md) and [notification](2026-09-24-m1-notification-drain.md) slices bind caller/output frames and block local/network media | Actual worker/client failure outputs and private server/scorer data in the final permitted observations; no raw crash-log escape |
| Client registry introspection | Scoped structured game facade and retained G0 filtering; exact E9E Mineflayer refusal remains unsupported | Authentic supported client/extension registry, recipe and container filtering. No global/private dump through settings or fallback backend |
| Helper inheritance and cross-arm messages | [Retirement](2026-09-24-m1-retirement-boundary.md), [process drain](2026-09-24-m1-process-drain.md), [helper pair](2026-09-24-m1-helper-pair.md), [cross-job](2026-09-24-m1-cross-job.md) and team slices | Combined final profile with game access restricted to executor, allowed roster messages and foreign arm denial; clean fresh handoff and one-way probe disposal |
| Probe-created canary disposal | Artifact filtering and synthetic checkpoint/reset controls are retained separately | Actual disposable matched clones; no probe revision, message, session/cache or artifact canary enters the resumed parent. M1.6/T11 remains open |

The existing `NativePreflightTransfer/1` in the M0 OAuth driver is explicitly
limited to first-receipt conformance or D14 development piloting. It compares
source/config/catalog pins and declares provider/path changes, but says full
T06 is false. It is not an M1 transfer certificate or an unused execution permit.

## Campaign catalog implementation

`NativeToolProjection/5` / `native-additional-tools-exact/5` supplies the missing
campaign-scoped team catalog identity. Operator setup must explicitly select
`campaign_team=True`, use the team broker and private communication policy,
purpose `campaign`, model `gpt-6-luna`, and one or two configured helpers.
The closed settings /3 and exact previously reviewed root/helper bytes remain
mandatory. Its pin differs from /4 even when the reviewed wire tools match.
Absent, conflicting or non-boolean selection flags refuse; /1–/4 scopes remain
unchanged. Catalog/body changes refuse at the existing admission consumers.

This is an auxiliary private runtime artifact, not a fourteenth experiment
record. It grants no game lease, helper envelope, provider credential, budget,
or execution authorization. Production NativeExec still requires all six
campaign qualification proofs, exact profile binding, sealed bootstrap,
ingress/gateway, policy/roster/lease and spending authority. Tests use synthetic
attestations solely to verify that all six are required; they do not issue a
real qualification. No campaign profile has been launched or qualified here.

## Verification and next work

169 distinct focused tests pass:98 projection/team cases and71 admission,
ingress and existing team fixture cases. Changed-file Ruff and whitespace pass.
Independent current-reader checks pass5/5: two /4 catalogs, two unchanged
stopped exports, and40 unchanged durable authority tables. No game, native
CLI, model or desktop input was executed. Exposure remains $4.887796/$10;
all unresolved holds and consumed decisions remain unchanged.

```powershell
.venv/Scripts/python.exe -m pytest -q tests/test_native_team.py tests/test_native_tool_projection.py --tb=short
.venv/Scripts/python.exe -m pytest -q tests/test_native_admission.py tests/test_native_ingress.py tests/test_native_team_channel_probe.py --tb=short
.venv/Scripts/ruff.exe check src/mcbench/native_tool_projection.py tests/test_native_team.py
git diff --check
```

Private audit bundle `C:/Users/Darian/.strata/evidence/2026-09-24-m1-profile-audit-01`
contains9 files/125,018 bytes; seal SHA-256
`3adcb73ce6512e6f1085a24222c29a84533f5dcc44c2efc7d3afe7a8edfbcff3`.
It preserves the pre-change inventory, all nine external pins, WAL-aware authority
snapshots, changed source/tests and independent post-change readback. No prior
bundle was modified. The nine original seals are in this audit and their linked
public reports; failed siblings remain preserved in those original histories.

Next compose a bounded credential-free integrated candidate using /5, the
actual scoped worker, root/helper isolation attempts and permitted game/artifact/
team controls. Keep scripted provider evidence labeled, with fresh private
state and exact pins. Reconcile each carried route against source/control changes;
run missing or affected routes without replaying unchanged historical suites.
Then complete selected skill execution/handoff and probe disposal before any
full certificate. Prepare a concrete bounded actual-model procedure before
requesting M1 spending authority. T05, T10 and T11 retain their independent
authentic evidence obligations; this catalog change does not close .9d or G1.
