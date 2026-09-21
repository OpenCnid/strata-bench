# Native learned-skill execution, fresh handoff and budget-denial recovery

September 21, 2026. Operator-only. M0.1c.2b.2c.6 and .3a; partial
F03/F04/F07/F09/F11/F16, N01/N02/N04/N06/N08,
C06/C07/C08/C12/C14/C16/C17/C19/C20/C23/C36,
T01/T04/T06/T07/T11/T12/T13 and G0 items 1/6. M0 remains incomplete;
G0 fails and G1–G5 are not run.

## Delivered behavior

The [activation probe](../../tools/native_activation_probe.py) continues the
existing pinned CLI/local-provider harness. It verifies a sealed synthetic
checkpoint store before copying it, preserves its accounts and costs, and uses
the production activation, admission, enrollment and broker paths. Its fixed
provider reports ten input tokens, four output tokens and fourteen fixture units
per forwarded request. These are neither actual charges nor experimental
API-equivalent usage. Smaller fixture reservations are justified only by that
fixed provider; no real model bound is changed.

Root and explicitly supplied clean-context helper read exact active skill bodies,
supporting text and revision IDs. Writes to active/initial files reject; helpers
cannot read root notes, draft publication requests or handoffs. The actual native
`$learned-crafting` invocation injects the body. Root writes a replacement bundle
with the exact active parent, and the operator derives its private source-bound
publication from successful broker write receipts. Scripts remain readable text,
not executable capabilities.

The [dispatch gate](../../src/mcbench/inference_dispatch.py) now adds
`durable-budget-denial-before-dispatch/1`. After validating the finite exposure,
known budget or envelope exhaustion and existing unknown usage produce an atomic
private `InferencePreDispatchRejection/1` record. A savepoint removes the failed
reservation before committing its denial and journal event. No usage receipt or
zero-cost settlement is invented. Reusing the rejected operation fails even if
capacity later becomes available or the controller restarts. A new distinct
request still needs its own complete admission.

Database/commit faults and failures before validated budget admission do not
become rejection proofs. Already dispatched or ambiguous requests retain their
original reservations. [Finalization](../../src/mcbench/native.py) and
[export](../../src/mcbench/native_export.py) require every admitted request to
have dispatch history or an exact, independently checked rejection record.
Rejections are exported separately from settled calls, receipts and ledger
operations. Missing, altered or overlapping evidence blocks closure/export.
Legacy absence is never backfilled; exports with no denials retain their source
identity. This is an additive private-store migration, not a new allowance.

## Actual native evidence

All runs use actual Codex CLI 0.154.0-alpha.6.2, SHA-256
`960c111d47afd61669954b9df9e56083e302edbfa3ef6962d81dcc14a30051dc`,
and unchanged OpenCnid/dovetail-codex 0.4.1 at
`15c306ccfef28eb5f616fadcd5fd8eac0663e361`. The selected model identity remains
`gpt-5.6-luna`. Upstream responses and OAuth cache credentials are fabricated
fixtures on owned loopback servers. The scoped game worker and world checkpoint
are synthetic. No RuntimeQualification is issued.

Private evidence directories share the prefix
`2026-09-21-native-activation-exec-`:

| Case | Observed result | Accounting / disposition |
|---|---|---|
| 01 | Pre-start account-category mismatch rejects | No new model requests; copied 56 fixture units preserved |
| 02 | Pre-start conformance-purpose/training-account mismatch rejects | No new model requests; copied 56 units preserved |
| 03 | Native exit 1; six forwarded calls settle, another admitted request fails ENVELOPE_EXHAUSTED | 84 new units plus prior 56 = 140; original report fails 4/32 checks; retained export gap below |
| 04 | Native exit 0, FINALIZED; all 32 checks pass | Six actual CLI/local-provider calls, 84 new units; total 140, no uncertainty |
| 05 | Fresh native process from case 04's derived complete checkpoint; exit 0, FINALIZED; all 32 checks pass | Six new calls, 84 new units; prior 140 preserved, total 224 across 16 calls |
| 06 | Declared seven-call envelope exhaustion after the production fix; native exit 1, FINALIZED | Five forwarded calls settle; one durable pre-dispatch denial; 70 new units plus 56 = 126; 13 targeted recovery checks pass |

Cases 01/02 were corrected by carrying the source account category and campaign
purpose. No source account was rewritten. Case 03's eight-call parent reservation
did not cover the requested root progression while the four-call helper envelope
remained held. Case 04 explicitly reserves nine calls, within the unchanged
100,000-unit synthetic allowance, and uses a 30-second native helper wait.
The 90-second native deadline is unchanged. This fixes the fixture plan; it does
not relax an acceptance threshold.

Case 03's original aggregate checks assumed every received HTTP request had been
forwarded. The corrected verifier uses durable settled attempts; the original
failed report remains. On a fresh derived copy, export rejects METERING_UNKNOWN:
seven admissions, six settled attempts and no durable pre-dispatch denial.
Its 140 units are unchanged. This evidence prompted the production fix above;
the old store is not repaired retrospectively.

Case 04 takes 37.0906174 native seconds, 76.282 seconds including setup. Its
profile digest is
`c8d8da329098e4e55bffcb8bb84229b8d594c3b483d6750eb901f57442b24936`.
A fresh derived copy passes eight further checks: source-bound revision 2
publication with parent revision 1, typed retained active metadata, committed
complete synthetic checkpoint, private materialization, unchanged second skill,
unchanged accounting and no dispatch authority. Its active set is
`cas:sha256:16a464d3a2af239e0dc022d81f73090514db6efcd81139a1efdc2c6ed211facb`.
The sealed derived checkpoint manifest has SHA-256
`4485c373250bc655e54a07e8a0c1817828c5366e746123609b8653314a9ebb74`.

Case 05 verifies that seal and starts a new native job at epoch 3. It takes
32.1120003 native seconds, 71.171 seconds including setup, on profile
`0a5c1513d615c22b457f364e2cd6c5f87013476fd886b49a846f52e943811960`.
The root and clean helper load revision 2, and root writes candidate revision 3
with parent 2. Nine additional derived export/publication checks pass. Its stopped
export is
`cas:sha256:695ecd39164be6209668482fd42f353d0af00df7d8957fbbebf0180149561fad`.
The first audit script incorrectly asked for `revisions` rather than the actual
`records` field after successful publication; the failed script and corrected
idempotent audit remain. No native rerun was needed for that verifier correction.

Case 06's fault was declared before launch. Its ordinary positive-run report
retains two failures (`provider_clean`, `upstream_credential_all_requests`): six
authenticated admissions correctly produce only five upstream calls. The separate
13-check audit verifies that exact denial, durable proof, unchanged accounting,
terminal closure and export with five settled calls plus one separate rejection.
It is not relabeled as a successful gameplay run. Native time is 33.2859995 seconds,
wall time 73.515 seconds, profile
`46cc2e614fa134228d6312e843d18203ee04e01a3f820a7eda372d7f101bd4bf`.
Its export reference is
`cas:sha256:7c79c56349bb97aab4ee427550f0598e9997151a2b04db86a41b89a59ddc18c6`.

Cases 04/05 each settle four root and two helper calls; case 06 settles three root
and two helper calls. Each records 31 terminal broker operations: 19 returned and
12 rejected as scoped negative controls. Copied historical receipts are not new
consumption. Do not sum independent copied-store totals as if they were new usage.

## Focused source verification

- `pytest tests/test_inference_dispatch.py tests/test_native_rejection_export.py
  tests/test_native_export.py tests/test_native_admission.py
  tests/test_native_gateway.py tests/test_native_skill_activation.py
  tests/test_native_activation_probe.py -q`: **133 passed in 143.15 seconds**.
- `pytest tests/test_estimated_dispatch.py tests/test_estimated_accounting.py
  tests/test_native_checkpoint.py -q`: **58 passed in 28.52 seconds**.
- The initial narrower run had 60 passes and one test setup failure: an unsupported
  free-text uncertainty reason. The test now uses the existing typed
  `transport_or_receipt_uncertain` reason; production reason validation was retained.
- The copied-source activation test passed separately before execution. It verifies
  account/purpose/epoch preservation and rejection of corrupted sealed source
  before creating destination data.

These checks cover reservation rollback, failed rejection commit, terminal IDs
across restart and later available capacity, retained unrelated uncertainty,
missing/changed proof, export/source identity and checkpoint compatibility. No
unchanged native accounting matrix or broad repository suite was rerun.

Focused Ruff and whitespace checks pass. Coverage review retains all 305 prior
milestone IDs and adds .3a (306 total); all required F/N/T/G identifiers remain.
All 1,165 local links in the changed specification/status/ledger/report set
resolve. A final process observation finds no owned activation-fixture native,
Python or Java process still running. The six final production/harness files
match the case-06 executed source snapshot byte for byte.

The six private directories are closed and sealed. Each manifest covers its raw
results, executed source generation, copied store and derived audits; hashes are
SHA-256. Case 04's inner checkpoint seal above remains unchanged.

| Case | Files | Bytes | Manifest digest |
|---|---:|---:|---|
| 01 | 3,654 | 70,054,873 | `f08606918070fe4f31b10daddbf3825b64a590c279787c7fc068642b7d766005` |
| 02 | 3,654 | 70,038,321 | `c53bf350bdd1146393a33d94f64b4bbfbf45d279e34a770a64d29f2d69ee0376` |
| 03 | 3,862 | 74,949,546 | `22698ff63e741a62918ad014b0c7fe3009d9271c8abf45960a8e4e6708e45414` |
| 04 | 3,914 | 74,866,718 | `417b25d6feb1959591ddcda4e81fda7269f0bf336fdd717d97d3199bf25f7ce9` |
| 05 | 3,938 | 75,696,666 | `3d3323d74d600ec0436b28bba6f71ff7f08efafba43e502317581b87aa222b1c` |
| 06 | 3,865 | 74,862,386 | `df725c6e861bc57c7f1acd5854e8664209680deabeeb7891be343f8fc8a3b31d` |

## Limits and next evidence

These results establish actual native invocation and a full-arm native-to-native
handoff over synthetic game checkpoints. They do not establish real game restore,
preregistered frozen-arm native execution, interrupted activation, executable
snippets/macros or the complete ninety-file initial Dovetail support projection.
Those remain required integration work. Never change the full-arm source policy
after execution to manufacture a frozen-arm control.

Original live accounting was rechecked read-only before each native fixture:
authorization digest
`7aca7758f12eb1089f481d5d4bc19de2c6022cf1167b03056c32d41c3e4a819a`,
$10 total allowance, one unresolved $0.7554 hold counted once, zero valuations.
No real model request, OAuth retry, Minecraft launch, shared-desktop input,
allowance reset or cost refund occurred. Raw evidence, databases, credentials and
runtime profiles remain outside public source and gameplay access.

Retain prior native sibling/loopback and patch-read failures, failed 500-ms
shutdown samples, all five effective-file failures, Mineflayer/E9E incompatibility
and remaining scorer/control/parity/provenance/recovery requirements. Required
M0–M6 work and conditional M7/extensions are unchanged.

## Retained supporting work after the full-arm checkpoint

The preregistered frozen-persistence source and two actual native/local-provider
runs now verify recovery retention followed by episode reset. Recovery reads the
two active revisions (32 checks); the subsequent fresh root/helper sees the
initial empty active set and no old learned bodies (34 checks). Constructed and
scripted usage progresses 56→140→224 fixture units without refunds. World
checkpoint components remain synthetic. The seed and both execution bundles
are private and sealed; execution seals are
`3a91a7eb4618dfc62151a249415148e9f28b8677202eb3df661901728513480d` and
`7539314710149d49bc7eed41c5939be2c35f6675f2ef8f99fe2fc64600530e1c`.

Source enforcement also keeps frozen-skills candidate publications private and
inactive across recovery/episode boundaries. Four policy cases pass. Four
owned-process interruption fixtures pass at pre-commit, mid-copy, post-rename
and pre-view-commit boundaries: no partial launchable view, unchanged costs,
and retained occupied orphan output. The initial four PID-targeting fixture
failures remain in test history; the corrected runner launches the actual base
interpreter so the owned PID matches. These are source/process fixtures, not
authentic game restore. The combined affected native/worker/broker/activation
suite passed 118 tests in 172.82 s.

Actual native frozen-skills, restricted script/macro capability and complete
game/agent restoration remain open. The user redirected immediate work to the
[connected M0 path](2026-09-21-m0-native-game.md); do not expand this supporting
workstream before its concrete dependencies are needed.
