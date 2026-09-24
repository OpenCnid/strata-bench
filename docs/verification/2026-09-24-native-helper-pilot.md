# Native root/helper development pilot

M0.1d.9d implements the missing root/helper admission path for the existing LLM
harness. The final pinned native preflight passes **26/26** with synthetic model
replies. The authentic case fails before gameplay/helper creation because receipt
storage exhausts its existing quota. Real helper piloting remains unverified. M0 stays in_progress and G0 fail.

Coverage: F03/F04/F06/F11/F16, N01/N02/N03/N04/N06, C06/C09/C12/C15/C18/C20,
partial T01/T03/T04/T06/T07/T12/T13, G0 items 1/6. D14 isolation deferral and
the complete M1–M7 roadmap remain unchanged.

## Implemented path

The earlier real pilot deliberately allowed zero helpers. Its retained-hold
exception accepted only root model reservations, so it could not qualify a
real helper. [pilot_budget.py](../../src/mcbench/pilot_budget.py) now has an
explicit `PilotBudgetDecision/2` for fresh D19.6-or-later jobs under continuing
D18/D19 authority. It retains the original $10 and all unknown holds, admitting
one helper response, sixteen combined requests, 240 native seconds and at most
$1. Historical decisions retain their original bounds and cannot be rearmed.

Root and helper costs share one envelope. Each can have at most one pending
request; both finite exposures must fit before dispatch. The helper has one
nested envelope and one response. Extra helpers, grandchildren, duplicate
in-flight root calls, a second helper call and new uncertainty block admission.
Envelope closure preserves actual child costs without double counting.

[native_piloting.py](../../src/mcbench/native_piloting.py) keeps the model-selected
turn and short walk, then asks one clean-context helper to assess only the
public observations and terminal receipts. The helper has no avatar lease and
must return one final reply without tools or further delegation. The native
gateway permits two bounded handlers. Worker/server/outer limits remain
360/440/600 seconds. No private target, route or scoring criterion is supplied.

[native_tool_projection.py](../../src/mcbench/native_tool_projection.py) adds
explicit projection /2 for the observed GPT-6 Luna helper catalog. Every tool,
description and schema exactly matches the previously reviewed root catalog;
the older helper projection omitted collaboration. The new pin is prepared
offline before a fresh run, and its scope is the one-helper development profile.
Legacy /1 remains strict. Catalog advertisement does not override participant,
budget or broker authority. Full OS isolation remains unqualified under D14.

[native_pilot_report.py](../../tools/native_pilot_report.py) produces private
NativePilotResult/2 for this profile. It joins the helper participant, one
settled request, closed nested envelope and a final-answer message in a later
root request. Root-written summaries, foreign helper messages, wrong recipients,
task messages and empty payloads do not count. The reader accepts the pinned
native single-text-block final reply and the explicit split payload form. This
proves delivery and accounting, not the correctness of the helper's assessment.

The launcher, permit, request validator and preflight consumer use these same
profile bounds. The existing vanilla baseline binding now checks the declared
helper count; it does not silently reuse a zero-helper system identity.

## Executed verification and retained failures

```text
python -m pytest tests/test_helper_pilot_budget.py tests/test_luna6_pilot_budget.py
  tests/test_pilot_budget.py tests/test_native_piloting.py
  tests/test_native_helper_piloting.py tests/test_native_tool_projection.py
  tests/test_native_admission.py tests/test_native_game.py -q
270 passed in 34.81s
```

Earlier test runs exposed a test-only nonexistent closure convenience method
and two incomplete test-plan shapes. Tests now use the actual transactional
envelope closure and explicit helper count. The original failed outputs were
not integration successes.

Four distinct native cases use the pinned CLI and Dovetail with a synthetic
provider/worker; none spends model credits or starts Minecraft:

| Case | Result and scope |
|---|---|
| helper-native-01 | 7/20; helper catalog rejected before provider forwarding, native exit 1 and UNSETTLED closure retained. No helper receipt fabricated. |
| helper-native-02 | 20/20 native checks; separate production-reader audit 4/5 because it expected two reply parts while native emitted one. Retained as a reader failure. |
| helper-native-03 | Corrected reader and native 25/25; six settled requests, two CLOSED participants, normal native finalization in 21.542 seconds. Preflight consumer accepts. |
| helper-native-04 | Added deliberately overlapping root/helper requests; 26/26, six settled requests, both participants and envelopes closed, normal native finalization in 19.789 seconds. Preflight consumer accepts. |

Each case preserves its original source, request frames, accounting, errors and
output. Case01's two catalog-rejected requests remain distinct from forwarded
requests. The new catalog was reviewed after that stopped failure: all nine
tools match the already pinned executor catalog exactly. Case03/04 prove actual
native helper spawning/delivery with scripted replies, not real LLM reasoning.
All original authority tables remain unchanged across these cases.

The OpenAI Docs skill supplied the official context for native delegation;
actual pinned-runtime observations determine this implementation's accepted
wire shape. See [official subagent documentation](https://learn.chatgpt.com/docs/agent-configuration/subagents).

| Private archive | Seal SHA-256 |
|---|---|
| 2026-09-24-helper-native-01 | `5ab17bdf9addd71e758aedc4e6e64ef5071947128bd12043149c316354f2ca9b` |
| 2026-09-24-helper-native-02 | `0d23b7aa71b5eed14819d844da4c8e74548ecb712f033ae38317b4e5318317af` |
| 2026-09-24-helper-native-03 | `7bbc002a91cbac2f9173c60b9280e4c22ce896e721342f95fb0ef794966a96cf` |
| 2026-09-24-helper-native-04 | `97e0576e2ebfefa1d8588becbbc9e62d25d29b144d5df7c9ff6159f5d5159afc` |

Private roots are under `C:/Users/Darian/.strata/evidence/`. All four archives
pass complete EvidenceBundle readback. Credentials and live fixtures stay private.

## Authentic case

Fresh D19.6 / m0-pilot-13 ran once under D18/D19. Preparation preserved all
39 authority tables, materialized a fresh instance without rebuilding the worker,
and sealed with SHA-256
`a4cc9a5a85bd2e0f79268b526e2d85075df2833311427598651e68a80b552178`.

The authentic run **fails**. The first two requests settle for **$0.001160**.
Request three returns HTTP 200 and a complete usage-bearing stream, but saving
its **60,884 bytes** fails with `ARTIFACT_QUOTA` during `receipt_recording`
after 3,734 ms of its 60,000-ms allowance. The retained normalization event pins
the response hash `3959fa6e684e16553886637bfcd3dbb3142bebf82d92ae13ed88a56115e7f347`;
the raw receipt was not durably stored, so that hash is not a recoverable receipt.
The operator namespace has a shared 20 MiB default limit. Its stopped size is
20,938,057 bytes; adding the refused receipt exceeds 20,971,520 bytes. The
synthetic preflight used a fresh store and therefore did not expose this
accumulated-capacity condition. No quota was raised and no evidence was deleted.

Native delivery preceded durable recording. The model's contract-read tool call
then receives `BROKER_BUDGET_UNCERTAIN`; no game call or helper is admitted.
Two subsequent native requests are rejected without dispatch. The model and
Mineflayer backend are not shown failing to produce or execute an action: this
attempt never reaches action selection. Native ends UNSETTLED/exit 1 after
24.164371 seconds. Worker drains normally in 22.0115 ms; all 53 outer-owned
processes terminate without forced termination. The complete owner takes
179.532 seconds. No saved-player movement join or complete checkpoint is claimed.

The entire new **$1 envelope remains reserved**, including the two settled
charges, without double counting. Combined committed/reserved exposure is now
**$3.831942/$10**. All predecessor accounting rows, original allowance, D12 and
older holds remain unchanged. D19.6 is consumed and cannot replay. Continuing
D18/D19 authority remains; no permission is pending.

Executed private procedures: `prepare.py`, preparation `seal.py`, one
`execute.py`, stopped `audit.py`, and scoped `archive.py`. The first audit assumed
an existing primitive counter and failed on this zero-action journal; its source
and failure are retained. The corrected audit treats the absent counter as zero
and leaves movement/helper checks failed. The first archive hit Windows long-path
handling in plugin fixtures; the corrected read uses the existing extended-path
helper. Both failures remain in the archive.

Live archive `2026-09-24-m0-helper-live-13`: **3,969 files / 200,534,480 bytes**,
seal **`36723ba70f98c2153ea5acae08624221d7694fba8d4df5bd4a02ba0fee37c247`**,
complete EvidenceBundle readback passes. It preserves exact executed source,
stopped run, full controller snapshot and 30 scoped JSON/text CAS objects.
Eighty-eight external references remain explicitly listed; this is not a standalone
Minecraft distribution. Credentials are removed from the stopped native profile.

Next fix operator evidence capacity admission and durable receipt delivery order,
with full/near-full-store regressions before another paid dispatch. Preserve the
failed run and all reservations. Then qualify a changed native preflight and a
fresh sequential root/helper case within the remaining original allowance.
Successful zero-helper gameplay and sealed Forge installation need no replay.
M0.1d.9d is in_progress, G0 items 1/6 remain incomplete, and M0/G0 stay open.
