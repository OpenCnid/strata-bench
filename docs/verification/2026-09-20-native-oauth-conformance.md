# First native OAuth receipt trial and retained reservation

September 20, 2026. Operator-only. M0 remains in progress, G0 fails,
G1–G5 are not run. This report records a failed authentic trial, separate
synthetic verification and subsequent source fixes. No gameplay ran.

Coverage: M0.1c.1c.2b.1/.2, M0.1c.2b.2, F03/F04/F07/F09/F11/F16,
N01/N03/N04/N06, C06/C12/C18/C20/C36, partial T01/T04/T06/T07/T12,
G0 items 1/6. No numerical threshold, required milestone or conditional
extension was removed or relaxed.

## Implemented behavior

[Conformance admission](../../src/mcbench/native_conformance.py) and the
[operator runner](../../tools/native_oauth_conformance.py) distinguish
pre-dispatch safeguards from the first receipt being tested. The private
permit admits only one request, one root, no helper/game grant, the fixed
receipt prompt, the pinned OAuth/Luna profile and at most $1 exposure inside
the original migrated authority. Five exact-profile prechecks bind native
tool controls, reservations, credential containment, finite exposure and
verified TLS. Source-matching native preflight transfer declares its synthetic
provider and reduced privileges. It cannot qualify a campaign or create funds.

The fixed durable first-receipt job ID cannot be rerun. Native authentication
uses a private copy of the user's authorized OAuth cache, copied only after
the prechecks; secrets stay outside source, prompts and printed results.
Gateway closure does not settle missing usage. Subsequent source fixes make
the command exit nonzero on a failed receipt or unresolved closure.

[Receipt transport](../../src/mcbench/inference_transport.py) now journals
safe HTTP status/media classification before format validation. Unsupported
uncompressed bodies are bounded to 256 KiB, filtered for literal credential
reflection and retained privately within the existing deadline. They never
reach the native agent or count as usage receipts. Unknown headers are not
journaled, and no redirect/retry or reservation refund is introduced.
This diagnostic fix postdates the failed trial and cannot recover its lost
upstream status/media/body.

## Executed native preflight and authentic trial

Pinned Windows CLI `0.154.0-alpha.6.2`, binary SHA-256
`960c111d47afd61669954b9df9e56083e302edbfa3ef6962d81dcc14a30051dc`;
Dovetail `15c306ccfef28eb5f616fadcd5fd8eac0663e361`.

| Scope | Actual result |
|---|---|
| Source prechecks before dispatch | 42 conformance/OAuth tests pass in 17.50 s; targeted Ruff passes |
| Actual CLI, fabricated OAuth, owned synthetic provider | `native_mcp_identity_probe.py --broker --admission --bootstrap --ingress --oauth --gateway --skills --canaries`: 9 distinct requests, 38 checks pass, 63 microUSD API-equivalent estimates on synthetic counts; finalized |
| Actual CLI, real OAuth, fixed verified HTTPS | One request attempted; `RESPONSE_CONTENT_TYPE`, no authoritative usage receipt/valuation; native exits 1 after 12.973 s |
| Cleanup/accounting | Gateway CLOSED with exact request seal; job/request UNSETTLED; envelope closure rejects `METERING_UNKNOWN`; full $0.7554 remains reserved |
| Read-only controls after failure | Credential-free fixed model-catalog GET returns 401; authenticated fixed GET returns 200 JSON; neither is a model inference request |

Synthetic preflight profile:
`e5f819a214706f05607afead6abc361b7074297d2188dc15d5831eee432d7aed`.
Authentic profile:
`fc7a7989cc95f98aee346acd6f8bf79be1e795627502528c139a7c9e32a81e7c`.
Request: `gateway-cd3156b226424332ac152974e1afc3ea`.

Native stderr also records two unsupported `/v1/models?client_version=0.154.0`
GETs (local 501). Native stdout records a local gateway 403. That 403 is
**not evidence of the upstream HTTP status**. The failed trial did not retain
the upstream media value or body; HTML, NDJSON, authentication failure and
Responses Lite incompatibility are not established diagnoses. No replay ran.
The original runner exit code was incorrectly zero despite its explicit fail
result; the subsequent CLI fix does not rewrite that historical outcome.

## Native startup catalog fix, without inference

[Catalog installation](../../src/mcbench/native_catalog.py) verifies an
operator-supplied source digest and retains the selected model's complete,
unchanged metadata row. `model_catalog_json` is a supported startup override
in the [official configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference).
The selected private file joins `prepare_bundle(static_files=...)`;
[bootstrap admission](../../src/mcbench/native_bootstrap.py) rejects an unpinned
catalog or a gameplay-workspace overlap. The file remains held against edits
for the native lifetime. No limits, instruction text or wire preferences are
invented. This changes the launch identity; it requires its own exec conformance.

Actual pinned `app-server` metadata-only probes used only initialize and
model/list, a fresh credential-free profile and an owned denying HTTP sink.
Both loaded exactly the selected Luna catalog. Sample 01's early assertion
raced a background GET; its original result and corrective audit are retained.
Sample 02 records after fencing: zero model dispatches, zero `/models`
requests, one denied `/v1/plugins/featured?platform=codex` GET. This is native
catalog-loading evidence, not a zero-network claim or adoption of app-server
as the gameplay loop. No live exec retry was performed.

Catalog source SHA-256:
`58eab4ab72c911b8530765e591540922a4549a55d4172eae56352fcf7ed1530c`;
selected snapshot:
`536a7e260d3c5f0340141f358417dd6a64a5da588c81a1a0bc3c50ca6a919189`.
Observed native catalog context/default metadata differs from the API reference
limits; it does not justify shrinking the original 1,050,000-input/128,000-output
exposure or settling the ambiguous call.

## Final checks, durable state and remaining work

- `pytest tests/test_native_conformance.py tests/test_native_oauth.py tests/test_inference_transport.py tests/test_native_gateway.py -q`: 88 pass, 29.27 s.
- `pytest tests/test_native_catalog.py tests/test_launch_integrity.py -q`: 23 pass, 0.83 s.
- Initial diagnostic tests had four incorrect exception assertions: the existing
  deduplication path returns the prior UNSETTLED status without forwarding.
  Corrected assertions verify that status and exactly one upstream request.
- Targeted Ruff passes. These focused source checks are synthetic; there was no
  unchanged full accounting-matrix or broad suite rerun.

Read-only original store recheck: `validation-2026-09-18`, schema 2, one
migration, unchanged 10,000,000 microUSD allowance; one envelope and one request,
zero valuations. Aggregate exposure is 755,400 microUSD, not twice that amount;
uncertainty blocks dispatch. This is neither $0.7554 of proved charges nor a
new $10 allowance. All owned services are terminal; no Java, evaluator launch
or shared-desktop input occurred.

Private artifacts remain outside public source under
`C:/Users/Darian/.strata/evidence/2026-09-20-native-live-preflight-01`,
`2026-09-20-native-oauth-live-01` and `2026-09-20-native-catalog-01`/`02`.
The live bundle includes admission, TLS, result/journal, read-only catalog
controls and accounting recheck; its private cache/catalog must not be published.

Model admission remains blocked by missing authoritative usage. Preserve the
hold and never automatically rerun the first-receipt job. Catalog pinning and
diagnostics do not reconcile the lost receipt. Continue independent M0 scorer
authority, shutdown/provenance and recovery work; full root/helper/game/private
integration, measured stage admission and helper lifecycle remain required.
Retain original loopback canary failures, five effective-file failures,
Mineflayer/E9E incompatibility and failed 500-ms shutdown samples.
