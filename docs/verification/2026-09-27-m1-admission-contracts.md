# M1.2b admission references, nested RPC and conditional Java contracts

Campaign preflight now rejects inconsistent rosters and unresolved declared
references before capacity reservation. RPC validation applies the canonical
action rules inside the request envelope. The actual Java structured-action
parser exercises the shared canonical cases. M1.2b/M1 remain in_progress;
T01/G1 remain not_run pending the remaining contract reconciliation below.

Scope: F02/F03/F07/F16, N01/N04/N06; SPEC9/10/16 T01, with T04/T05/T06 affected
by worker identity and admission boundaries. Base e631878. No game, model,
installation or paid-inference job was dispatched.

## Fixed admission behavior

[Controller.configuration](../../src/mcbench/controller.py) is shared by creation
and preflight. Both revalidate canonical records and enforce non-example inputs,
the complete roster, common system identity and unique player accounts. Preflight
previously omitted these checks. The simulation profile still skips production
evidence, but cannot skip configuration consistency or become production.

Production admission now resolves the backend capability manifest and every
declared agent overlay, plus the direct artifact references in PackLock and
EvaluationProtocol. Protocol membership must include the campaign system.
Binary lock assets are hash/size verified without pretending they are JSON;
configuration documents still require JSON objects. Missing namespace authority,
missing bytes, corruption, invalid records and mismatched protocol identity are
refusals. No reference grants execution or scoring authority.

Six controlled before/after counterexamples run the original e631878 controller
and the changed controller against identical temporary CAS fixtures. The old
preflight accepts a missing roster member, wrong agent system, inaccessible
backend manifest, inaccessible learned overlay, inaccessible lock asset and
wrong protocol system; the changed controller rejects all six. Original source
and exact outcomes are retained privately.

The [admission tests](../../tests/test_admission_references.py) remove namespace
access at each of 33 declared reference locations. Each refusal leaves campaign
state, lanes, reservations, accounts, grants and the outbox unchanged, even when
called through admit. Corrupted bytes are also refused. A complete synthetic
fixture resolves through the actual operator preflight CLI and remains
admitted=false; a mismatched roster produces the typed blocked result.

These fixtures contain explicitly synthetic operator attestations. This verifies
reference integrity and routing, not the truth of a conformance assertion.
It does not certify an arbitrary capability document, the contents of sealed
evaluation instances, installed pack provenance or the final runtime profile.
Those services and authentic gates retain their independent requirements.

## RPC and Java boundary

[protocol.ts](../../backends/mineflayer/src/protocol.ts) now validates method/field
relationships, calendar deadlines and nested ActionBatch semantics for RpcRequest.
The HTTP gateway uses that common validator instead of a second partial copy.
Authentication, audience, epoch and live deadline checks remain at the gateway;
backend capability checks still determine whether a syntactically valid action
can run. No input or settings capability is added.

The shared [RPC corpus](../../tests/fixtures/rpc_semantics.json) contains 47
envelope cases; both languages additionally embed all 24 existing shared action
cases. All 71 pass in Python and TypeScript. Two focused real loopback HTTP/CLI
tests pass with a synthetic game backend, including wrong token/agent, stale
epoch, expired/overlong/invalid-date deadlines, invalid nested action, method
confusion, unsupported settings and a valid bounded action. Invalid requests
produce no backend dispatch.

The [Java shared test](../../java/forge1192-client/src/test/java/io/github/opencnid/strata/client/GameBatchSharedContractTest.java)
passes 24 cases at the actual GameBatch parser: 11 structured canonical cases and
13 explicit input-profile refusals. Valid structured records preserve their JSON
values in an independent copy. The fixture changes is_example to false because
the native development parser correctly refuses documentation examples. Input
refusal is CAPABILITY_MISSING and is not a claim of input-mode conformance.

Java consumes canonical ActionBatch directly inside NativeGameRequest; it does
not consume RpcRequest directly. NativeGameProtocol validates that translated
envelope. Native snapshots/receipts are translated by the TypeScript Forge
adapter into canonical Observation/ActionAck. Native settings has a separate
protocol; this report does not claim that it consumes canonical KeybindingPatch.
The eight operator/evaluator record validators remain outside Java gameplay.

Executed Java command: gradlew.bat --offline :forge1192-client:test --tests
io.github.opencnid.strata.client.GameBatchSharedContractTest. Java17, locked
Gradle8.8/Forge dependencies and the existing hash-checked official FTB library;
no downloads or installed-artifact replacement. Existing Gradle deprecation
warnings remain. Application Java sources were unchanged.

## Verification and retained fixture errors

Python commands use the repository virtualenv and PYTHONPATH=src;tools;evaluator/src.
Executed admission/storage/schema-upgrade tests, the new RPC/spending cases,
actual preflight CLI cases, and affected controller reconfiguration/activation/
team/probe-custody tests. The custody tests use real Windows file leases with
synthetic records. All 293 distinct Python cases pass after the documented fixture corrections;
73 Node and 24 Java cases pass. The affected controller regression selection
has 135 passes. Existing Typer/Click deprecation warnings remain. Changed-file
Ruff, TypeScript build and whitespace checks pass. No observed failure remains.

The initial admission run has 72 passes and 12 failures because the intended
positive fixture inherited null spending ceilings. The existing spending check
correctly stopped it. The fixture now supplies explicit synthetic ceilings;
only those 12 failed cases were rerun and pass. Two new negatives preserve the
null-ceiling refusal. A later CLI positive initially fails because its fixture
expiry of 200 is valid only under the test controller's clock of 100. The CLI
uses the real clock. Its fixture now binds a short future expiry; the original
source and failure are retained. Neither fix changes production acceptance.

Commands: pytest tests/test_admission_references.py tests/test_storage_controller.py
tests/test_schema_upgrades.py; focused --lf correction; pytest RPC/spending and
CLI/controller integration selections. Node: npm run build; node --test
dist/tests/rpc_semantics.test.js; selected loopback/cursor tests in actions.test.js.
Logs and JUnit name exact cases; reruns are not counted as new coverage.

## Remaining T01 closure work and G1 sequence

The [finite T01 map](2026-09-27-m1-contract-parity.md#finite-t01-acceptance-map)
remains authoritative alongside SPEC16. This change advances direct reference
resolution, configuration consistency, nested RPC semantics, HTTP auth/deadlines
and the direct canonical Java action binding. It does not close T01 wholesale.

Next reconcile the remaining reference-bearing admission services (checkpoint,
skills, capabilities and private evaluation) with actual current evidence, and
map the translated native game/settings records and path/reparse cases. The
required evidence must bind the particular service/profile; object existence
or a generic pass assertion is insufficient. Preserve typed compatibility gaps
and distinguish structural acceptance from capability/provenance qualification.

Then complete keybinding and matched probes, consolidate protected scoring,
and qualify final T04/T06 as set by the [closure path](2026-09-27-m1-closure-path.md).
No further furnace run is selected. No acceptance threshold or unrelated M2-M7
scope changes. Existing failures, consumed decisions and budget holds remain.

Final integrity audit passes 13 changed-file pins, 458 preserved milestone IDs
and 1,815 local links. All 40 authority tables are unchanged at 4,887,796 microUSD;
three separate 256 MiB telemetry holds and prior sealed failures remain intact.
No Java process remains. Private archive 2026-09-27-m1-admission-contracts-01
verifies at 251 files / 2,573,970 bytes under seal
`0b35aa5346c0cd472887886d08a0ced33b975d154102735735899066462d9f69`.
This pointer follows the archived documentation snapshot. T01/G1 remain not_run.
