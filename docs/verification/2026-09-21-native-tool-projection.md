# M0 native tool projection admission

September 21, 2026. Operator-only. M0.1c.2b.2b.2;
F03/F04/F07/F11/F16, N01/N04/N06/N08, C06/C20/C24/C36,
partial T01/T04/T06/T07/T12/T13 and G0 items 1/6.
M0 remains incomplete, G0 fails, G1–G5 are not run.

## Delivered behavior

[NativeToolProjection](../../src/mcbench/native_tool_projection.py) declares
`native-additional-tools-exact/1`. Operator setup stores the previously reviewed
root/helper catalogs in private, hash-checked CAS and binds their references to
the CLI binary/version, Dovetail revision, model and exact native settings. The
manifest reference participates in `NativeLaunch.profile_digest()`. No request
or gameplay tool can establish its own allowlist.

Live broker startup requires that pin before native intent/process/budget. On
every request, [participant admission](../../src/mcbench/native_admission.py)
checks the full advertised tools before creating a participant or reserving a
helper envelope. The existing independent stdout/metadata/lineage checks remain.
[Dispatch](../../src/mcbench/inference_dispatch.py) then re-reads the immutable
private request and pin, verifies hashes and checks the catalog again before
per-call reservation/forwarding. Admission events record both the manifest
reference and the observed role-specific digest.

Only `additional_tools.id` is normalized. Descriptions, namespace/tool order,
schemas, grammar, strictness and every other field retain exact canonical hash
identity. Reject missing/duplicate catalogs, alternate top-level `tools` or
`functions`, unreviewed tool/namespace names, root/helper swaps and changed
definitions. Hash comparison also distinguishes JSON booleans from numbers.
The captured helper has no collaboration namespace; this change does not claim
nested-helper support. Unpinned historical simulations keep their profile hashes
and remain readable, but live broker admission rejects them. Reservations and
unknown usage retain their existing no-refund/no-replay behavior.

## Focused verification

162 distinct source checks pass across these executed commands:

```powershell
$env:PYTHONPATH='src;evaluator/src'
.venv/Scripts/python.exe -m pytest -q tests/test_native_tool_projection.py tests/test_native_admission.py tests/test_native_ingress.py tests/test_native.py --tb=short
.venv/Scripts/python.exe -m pytest -q tests/test_native_tool_projection.py tests/test_native.py::test_live_broker_requires_prior_projection_before_native_intent --tb=short
.venv/Scripts/python.exe -m pytest -q tests/test_native_gateway.py tests/test_native_conformance.py --tb=short --junitxml=<private>/gateway-conformance.xml
.venv/Scripts/python.exe -m pytest -q tests/test_native_tool_projection.py tests/test_native_admission.py tests/test_native_ingress.py --tb=short --junitxml=<private-followup>/admission.xml
```

The first combined run passes 122 checks. Two added setup/legacy tests and one
live-startup rejection test bring that scope to 125 distinct checks; their final
focused run passes 42. Gateway/conformance adds 35. A final review added two legacy-live admission cases;
the affected projection/admission/ingress subset passes 96 checks, bringing the
distinct total to 162. An earlier development run
passed 37/39 with two test-harness faults (wrong journal table and an intentionally
corrupted fixture left in place); both were corrected before these passing runs.
Fixture-import lint findings were also corrected; final focused Ruff and
`git diff --check` pass. No accounting retry/compaction matrix was rerun.

Coverage includes root/helper positives, stable projection across dynamic IDs,
duplicate admissions without additional reservation, altered continuation
catalogs, 28 pre-reservation root/helper negatives, runtime/settings pin drift,
private visibility, corrupted pin/raw bytes, restart-time dispatch rejection and
live startup/dispatch rejection of missing pins. These are synthetic source
checks, not a production isolation certificate.

## Changed actual native integration

Private `2026-09-21-native-tool-projection-01` contains the one-use driver,
archived changed sources, prior capture hashes, reviewed projections, intent,
new sealed native bundle, six requests/receipts, journal, audit and unit XML.
Its manifest seals 8,776 files / 123,854,057 bytes; SHA-256
`3ea8c730ab08eca66b5aca48940c6b031fd3a36c4b57956823b8aaab6a7b80d7`.
Before startup, all eight requests from the retained reader-boundary fixture
normalize to exactly two projections: five root and three helper captures.

| Pin | Value |
|---|---|
| CLI | `0.154.0-alpha.6.2` |
| CLI SHA-256 | `960c111d47afd61669954b9df9e56083e302edbfa3ef6962d81dcc14a30051dc` |
| Dovetail | `15c306ccfef28eb5f616fadcd5fd8eac0663e361` |
| Selected model label | `gpt-5.6-luna` |
| Root projection | `2caa55277dbdb196b703e40ad975d4c31fd9ac560800e0f7f405e1eaa2480ac2` |
| Helper projection | `482f5e0aaf2d9614fa5d83fd0e85bdfbfda9dd3a8905104d93a92feabdba5a46` |
| New native profile | `47b22717ef7b2b356e14c456e1ff0a2cda32c59113e75817e58828c2b2f4ff99` |
| Projection manifest | `cas:sha256:93312fb5044391c71799e46113672c3e7ee2241434b44e409db0b65e840cb91f` |

One changed pinned-CLI/Dovetail run uses the existing local deterministic provider
and synthetic game worker, with pre-pinned catalogs installed before launch.
All 16 integration checks pass: four root and two helper requests match their
pins; admitted artifact operations and executor game forwarding work; helper game
access and existing spoof/write negatives deny. Both participants/envelopes close,
all six requests settle, and the job is FINALIZED with exit 0. Native execution
takes 27.9645 s under its 90-s limit; setup plus execution takes 66.8130 s.
The retained initial runtime snapshot is UNSETTLED before explicit budget closure;
the final closure and current SQLite state are FINALIZED.

A final source-only follow-up also checks the durable native store mode during
participant admission: an already-running unpinned legacy live job cannot create
a new helper envelope before the dispatch guard. Its two new negatives and the
96-case affected subset pass. This follow-up is archived separately in private
`2026-09-21-native-tool-projection-followup-01`; it was added after the native run
and has source verification only. The original run sources/evidence are unchanged.

Consumption is 60 input + 24 output = **84 synthetic fixture units**, six calls,
counted once. These units are neither live OAuth API-equivalent spending nor
actual charges. The independent read-only audit passes 18 checks, including
archived-source integrity, exact catalogs, terminal state and original accounting.
The process audit finds zero owned native-subtree processes after completion.
No Minecraft, live model request, shared desktop input or new sandbox account was
used. The original authority remains schema 2, digest
`7aca7758f12eb1089f481d5d4bc19de2c6022cf1167b03056c32d41c3e4a819a`,
$10 allowance, $0.7554 unresolved exposure. No reset, refund or replay occurred.

## Remaining M0 work

Exact advertised tools do not establish the deferred `ALL_TOOLS` catalog's
behavior or eliminate underlying file/process/network access. Qualify the
remaining unbrokered code-mode tools against private targets, including
`apply_patch` and resource access, with permitted controls. Any other native
request shape must be explicitly inspected and pinned; the existing accounting
matrix is not repeated merely because a new pin exists. Preserve the actual
native loop/plugin and declare any changed capability profile.

Underlying sibling-read and loopback failures remain unresolved. The protected
craft06 513.433/500-ms shutdown failure, all earlier failed samples, five
effective-file failures, Mineflayer/E9E incompatibility, OAuth receipt uncertainty,
full scorer/provenance/recovery and host/game/accounting evidence join remain.
This checkpoint supplies no RuntimeQualification or release gate pass. Required
M0–M6, conditional M7/extensions and every original threshold remain in force.
