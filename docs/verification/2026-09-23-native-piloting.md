# D14 Mineflayer piloting implementation

**Inventory correction from the subsequent preparation:** the original
top-level seals below omit 211 deep Windows paths each. They remain failed as
standalone complete inventories. Their already sealed bootstrap manifests bind
all omitted bytes; complete transitive verification passes without changing
old seals or rerunning tests. See the [preparation report](2026-09-23-pilot-preparation.md)
for exact complete counts and the ready private pilot inputs.

M0.1d.9 is **implemented_unverified** for authentic integration. M0 stays
in_progress and G0 stays fail. The complete M1–M7 roadmap remains represented.
Coverage: F03/F06/F09/F11/F16, N01/N02/N04/N06, C06/C12/C20, partial
T01/T03/T04/T07/T12/T13 and G0 items 1/4/6; full isolation qualification remains
deferred under D14 to M1/G1.

## Delivered behavior

- `native_piloting.py` adds a distinct `development_piloting` native purpose,
  `NativePilotAdmission/1` and `NativePilotPermit/1`, both explicitly
  isolation-unqualified. Campaign and one-receipt conformance admission retain
  their previous requirements. NativeLaunch JSON/TypeScript bindings are updated. Generation also refreshes
  the stale ExecutionAuthorization TypeScript binding to its existing version 2;
  the authority contract itself is unchanged.
- The shared native OAuth runner uses the actual provider for this purpose.
  Its six-request/$1 job envelope, zero-helper profile, pinned runtime/catalog,
  original authority and fixed-destination transport remain enforced. D12
  cannot be selected for a gameplay trial. No retained-hold exception exists.
- The `M0NativePilot/1` branch composes the existing sealed Mineflayer/server
  lifecycle with that native runner, fresh ordinary goal and live observations.
  The broker transaction rejects a third action, unsupported mutation, or action
  longer than two seconds before forwarding it. Existing action schemas also
  reject missing release. No backend implementation or worker bundle changed.
- `native_pilot_report.py` joins chosen targets and action receipts to public
  observations, rejects stale/foreign/missing observations, checks actual yaw
  toward the requested target and walking displacement/target tolerance, and
  retains costs and stopped-lane evidence. The outer runner matches exact model
  action batches against the Mineflayer journal. No scripted response can be
  reported as authentic model evidence by this path.

The [reviewable trial](../operations/m0-piloting-trial.md) records its full bounds
and remaining admission condition. This is not a successful LLM piloting result.

## Executed source verification

- 243 focused Python cases pass across `test_native_piloting`, native
  conformance, broker, D12 accounting, native lifecycle, OAuth, gateway,
  retention and sealed-game joins. This includes 39 new piloting cases.
- 29 record/schema cases pass after schema export and TypeScript generation.
  A final native-exit review adds three regressions: all 42 piloting tests pass,
  including nonzero exit and timeout refusal. Total: 275 distinct focused passes.
  These are labeled synthetic/source tests.
- Focused Ruff passes. Initial test construction failures are retained in the
  task history: incomplete v2 companion fixture, release rejected earlier by
  the existing schema, and invalid physical-key fixture. Production checks
  were not loosened to accommodate them.

The read-only refusal regression proves that an unknown request stops this
driver before game launch, leaves accounting unchanged and never opens its
deliberately invalid credential fixture.

## Native compatibility preflight

Fresh pinned CLI/Dovetail runs use a local synthetic OAuth provider and synthetic
game transport. No Minecraft, paid-model dispatch, real credential use or
shared input occurs. The first run passes all 58 checks, with 11 scripted
requests and FINALIZED closure. Original authority remains unchanged.

Retained case01 seal: `cb884d07c6692e94b689e43e5195358228b6091124e21754371b7892d8691cf6`,
3,440 files / 73,447,779 bytes. A subsequent source correction makes an unknown
live request count explicit on early outer-run failure; case01 is not transferred
to the changed source. Case02 also passes 58/58 checks, 11 scripted requests,
FINALIZED closure and unchanged authority. All 111 current source pins match.
Its seal is `5985b95fa1729fc460b46943945531fbce1f767468164fcbb77e5524e3e7b599`,
3,441 files / 73,447,905 bytes. Both complete bundles and external seal receipts
remain in private evidence storage; use the inventory correction above when
assessing completeness.

Final review adds a required normal native exit before success. Case02 remains
retained for its exact source; case03 refreshes the native preflight after that
reporting change: 58/58 pass, 11 scripted requests, FINALIZED zero-exit
closure, all 111 source pins matching and original 34 authority tables unchanged.
Case03 seal: `067a71e6a8a8ee211eef36be040fdc240908e4e51a7fe21f903450070281cbc0`, 3,442 files / 73,600,079 bytes. No live model or game process was started.

A WAL-aware read-only call against the original controller returns
`PILOT_ACCOUNTING_BLOCKED` before credential contents or game startup. All 34
authority tables remain unchanged at 756,858 microusd combined exposure and
uncertainty true. The first shell invocation of that read-only check omitted
PYTHONPATH and failed at import, before any check or mutation; the corrected
invocation is retained in the task history.

The operator was asked to authorize exactly the reviewable one-run retained-hold
exception. An answer is pending; no exception, new allowance or dispatch has
been installed.

## Remaining acceptance

Authentic live-model reply delivery, model-selected game actions, complete
cost/game evidence, and the other five connected G0 outcomes remain open.
The original $0.7554 unknown hold plus $0.001458 settled D12 is retained, D12
is consumed, and general admission remains blocked. The new source purpose
does not clear the hold or grant a new allowance. Full gameplay/helper isolation
qualification is deferred, not falsely passed.
