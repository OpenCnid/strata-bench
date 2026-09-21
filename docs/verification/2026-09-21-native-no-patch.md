# M0 native patch read-channel removal

September 21, 2026. Operator-only. M0.1c.2b.2b.3; partial
F03/F04/F07/F11/F16, N01/N04/N06/N08, C06/C20/C24/C36,
T01/T04/T06/T07/T12/T13 and G0 items 1/6.
M0 remains incomplete, G0 fails, G1–G5 are not run.

## Failure and implemented restriction

The expanded [deferred-tool canary](../../tools/native_broker_canaries.py)
found that the pinned CLI's read-only patch tool reads files before deciding
whether it can write. Both root and helper receive different errors for missing
files, invalid UTF-8 and unmatched context. Matching updates, additions, deletes
and moves reject writes, but that does not prevent the read/error channel. The
owned private marker was not returned and files were unchanged; this is not a
claim of full-content exfiltration. The failed profile remains failed.

The pinned CLI lists `apply_patch_freeform` as removed. Its model metadata exposes
`apply_patch_tool_type`, and the supported
[startup catalog setting](https://learn.chatgpt.com/docs/config-file/config-reference)
allows a pinned catalog. The new explicit policy
`native-selected-model-without-apply-patch/1` installs only the selected Luna row
and changes exactly `apply_patch_tool_type: "freeform"` to `null`. All other fields
of that row, including instructions, context limits and wire preferences, remain
unchanged. Only Luna is advertised as a helper model override. The unchanged
snapshot installer retains its original preservation contract; this separate
restriction is implemented in [native_catalog.py](../../src/mcbench/native_catalog.py).

`NativeLaunch.tool_catalog_policy` binds the restriction into the native profile.
The catalog file must be held in the existing sealed bootstrap inventory. Live
broker startup, already-running live participant admission and live dispatch now
require this policy as well as the prior exact tool projection pin. Selected
model/null-tool validation runs at startup and admission/dispatch; inventory
rechecks protect the actual bytes. Old unqualified simulations remain readable.
No runtime/plugin replacement, model substitution, budget reset or game API
change is made. Scoped broker drafts/results remain available; complete learned
activation/export and executable-artifact conformance remain required.

Hooks were not substituted for this boundary. Official
[hook coverage documentation](https://learn.chatgpt.com/docs/hooks) describes
coverage exceptions and error paths that continue tool calls; it does not supply
complete enforcement. The catalog restriction is instead tested in the pinned
native loop, including direct calls that bypass discovery.

## Source verification

157 distinct focused checks pass. The combined catalog/canary/native/admission/
ingress/projection run passes 153. Four added live startup/participant/dispatch
guard cases pass in a five-case subset containing one existing case. The earlier
26-case catalog/canary subset overlaps these totals. Final focused Ruff and
`git diff --check` pass.

```powershell
$env:PYTHONPATH='src;evaluator/src'
.venv/Scripts/python.exe -m pytest -q tests/test_native_catalog.py tests/test_native_broker_canaries.py tests/test_native.py tests/test_native_admission.py tests/test_native_ingress.py tests/test_native_tool_projection.py --tb=short
.venv/Scripts/python.exe -m pytest -q tests/test_native.py::test_live_broker_requires_prior_projection_before_native_intent tests/test_native_tool_projection.py::test_live_job_with_pinned_but_patch_capable_tools_cannot_admit tests/test_native_tool_projection.py::test_live_dispatch_requires_catalog_restriction_even_after_old_admission --tb=short
```

Tests cover exact selected-row preservation apart from the declared field,
unexpected/already-modified catalog rejection, no overwrite, changed tool type,
mandatory live restriction before new reservations, and canary-verifier negatives.
Missing helper observations, unrelated errors, nonempty resource catalogs,
wrong artifact contents/caller and unsuccessful permitted operations cannot pass.
The completed accounting retry/compaction matrix was not rerun.

## Actual native evidence

All four runs use the same pinned CLI SHA-256
`960c111d47afd61669954b9df9e56083e302edbfa3ef6962d81dcc14a30051dc`,
version `0.154.0-alpha.6.2`, Dovetail
`15c306ccfef28eb5f616fadcd5fd8eac0663e361`, selected `gpt-5.6-luna`, a local
deterministic provider and a synthetic game worker. No real model inference,
Minecraft or shared-desktop input occurs.

| Private bundle | Actual outcome |
|---|---|
| `2026-09-21-native-deferred-tools-01` | Nine settled requests, 126 fixture units. Three patch denial cases fail for both callers. Four resource checks initially misclassify valid native JSON-string empty catalogs/explicit broker denials; offline correction retains the original report and the three patch failures. |
| `2026-09-21-native-no-patch-01` | New catalog removes patch from the wire definitions, but one request fails exact projection admission because the helper model-description list also narrows to Luna. Zero provider calls/reservations/fixture units; FINALIZED exit 1. The captured difference is reviewed before the next fresh run. |
| `2026-09-21-native-no-patch-02` | Eleven settled requests, 154 fixture units, FINALIZED exit 0. Root/helper patch calls are unavailable and direct custom calls reject. Original verifier result 45/46 is retained: its expected error omitted the word “custom.” Offline exact-output analysis resolves that verifier mismatch without rerunning this case. JSON function-call bypass remains untested in this bundle. |
| `2026-09-21-native-no-patch-03` | Adds the JSON function-call bypass and current live admission guards. All 47 integration checks pass; eleven admitted/settled requests, 154 fixture units, both participant envelopes CLOSED, native FINALIZED exit 0. Independent audit 24/24. |

The final profile is
`1b81d9fc4494d0d434506938cfe50a8373d776e07b2878e615e3043fe000eed0`.
Its root wire projection is
`463331dd394d9ca9eb6c891b61deb65e777a81c088e244d84928e11dc5388595`;
helper projection is
`b2de5881a527194a9212c5331187d99e2f5e92ac92c493dab4a758cec17848cc`.
Both were pinned before dispatch. The selected source catalog SHA-256 is
`58eab4ab72c911b8530765e591540922a4549a55d4172eae56352fcf7ed1530c`.

The final root/helper catalogs contain exactly the three native MCP resource
tools and four broker tools. All eight patch forms are unavailable through code
mode. Direct custom and JSON function calls reject as unsupported before patch
processing. Resource catalogs are empty globally; the broker rejects resource
enumeration/read methods. Private bytes remain absent and files unchanged.
Both permitted artifact round-trips succeed, and only the executor reaches the
synthetic game worker. Shell/image/direct-shell denials and existing broker
spoof/immutable-write negatives also pass.

Final native execution is 31.6660 s within 90 s, or 71.0780 s including setup.
Seven root plus four helper calls consume 110 input/44 output = 154 **synthetic
fixture units**, counted once. Across the four separate stores: 31 settled calls,
434 fixture units. These are not OAuth API-equivalent expenditure or actual
charges. Initial UNSETTLED snapshots remain alongside explicit FINALIZED closure.
All owned native-subtree processes are terminal. Read-only accounting confirms
the original $10 authority and unresolved $0.7554 hold are unchanged; no refund,
replay or new allowance.

## Seals and remaining work

All raw content, installations, profiles and evidence remain private. Bundle
manifests preserve original failures and analyzer corrections separately:

| Bundle suffix | Files / bytes | Manifest SHA-256 |
|---|---|---|
| `deferred-tools-01` | 8,819 / 423,952,120 | `827feee39d180cde60f8eaf7fd44b5c8ad75ccfcb6937454946c9c07f52a7d83` |
| `no-patch-01` | 6,344 / 101,147,966 | `1eaa101e320fdbb934420fd3893e101778222abe614742a41c824d10e228647b` |
| `no-patch-02` | 8,951 / 126,281,577 | `b0b09a98065d7cecd84a4056ed411a4d923f57e0cdb448327667a5adc9c99366` |
| `no-patch-03` | 8,954 / 126,305,007 | `942bcd7a9e04f0279f663c2a57e1da7b1ec8dcee38697d49be2e8431e2e349ee` |

Next test native code-mode stored state and asynchronous cell ownership across
root/helper boundaries, then join remaining native lifecycle/artifact evidence.
This checkpoint closes the tested patch path only; it does not issue a
RuntimeQualification. Retain underlying sibling-sandbox reads and loopback
failures, the old patch read channel, original OAuth uncertainty, all failed
500-ms shutdown samples, five effective-file failures, Mineflayer/E9E
incompatibility and full scorer/provenance/recovery requirements. Required
M0–M6 and conditional M7/extensions remain unchanged.
