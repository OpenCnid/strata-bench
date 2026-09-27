# M1.6q.4 exact initial worker projection and stop evidence

Status: **implemented_unverified** for authentic paired integration. G1-G5 remain not_run.

Case04 rejected the pinned Mineflayer adapter's ordinary inventory window and
would subsequently have rejected a journal comparison after schema validation
added an omitted optional default. Both original records and failures remain in
[the case04 evidence](2026-09-25-m1-worker-check-composition.md).

The private verifier now accepts window=None or the ordinary player inventory
window with id0, type minecraft:inventory, no cursor item or machine, and slots
equal to the own-inventory projection. Connected state, scope, zero actions and
primitives, no held controls/gaps, authenticated identity and saved-player
projection checks remain required. Opened or inconsistent windows still refuse.
The coordinator validates incoming observations without replacing the delivered
JSON with a model dump. Exact journal equality and the observation digest use
the original delivered representation; adding a default is not silently accepted
as an exact delivery match. No producer schema, capability or profile changes.

Normal worker stop and complete owned process-custody results are flushed and
fsynced before later projection validation. Receipt persistence failure aborts
the reference and preserves parent reservations. A supervisor drain receipt does
not substitute for complete owned process custody, and neither establishes full
checkpoint or shutdown-gate qualification.

The base coordinator's complete composed check immediately after server readiness
also covers worker startup; the private continuation no longer repeats that
adjacent check. The whole-arm live-body check after observations remains. A
binding changed at server readiness still fails before any worker starts.

Focused synthetic verification with actual held source/configuration files:

```text
pytest tests/test_probe_worker_observation.py tests/test_probe_worker_runtime.py -q
pytest tests/test_probe_worker_observation.py tests/test_probe_worker_runtime.py -q -k 'held or test_complete_pair or ready_binding'
```

The first selection passes35 and fails one newly written held-key fixture in
348.79s: it supplied a string where the schema requires a typed physical-key
record. The corrected fixture plus the final lifecycle/readiness checks pass3
with34 deselected in55.69s,37 distinct passing cases across both selections.
The initial source and failed output remain. Ordinary inventory with an omitted
optional default passes exact delivery; replacing it with normalized JSON fails.
Opened/foreign/inconsistent windows, carried items, disconnected state, controls,
gaps, changed health/scope/identity/journal/order, action/primitive/epoch changes
and missing import custody refuse. Stop/custody persistence failures fence and
retain holds; later state failure retains both successful stop/custody receipts.
Both-arm positive ordering, immutable first export and readiness-binding refusal
pass. Ruff passes. These source cases are not authentic game or isolation proof.

A read-only audit of the sealed case04 journal and identity-native02 saved player
confirms the ordinary window agrees with own inventory and the saved/live own
projection matches. The normalized observation differs by machine:null only.
This diagnosis cannot supply case04's missing complete worker job receipt and
does not change its failed outcome. The diagnostic's first SQLite open used an
extended-path URI unsupported by SQLite and failed; that script/output remain.
The corrected read-only drive URI succeeds against the independently verified
sealed bundle. No game/model dispatch or source evidence alteration occurs.

Fresh authentic case05 uses the same profile02/runtime02/source world and original
parent300s, writers200/170s and servers60/60s. It fails in224.87s after the first
worker's exact journal/identity/saved-player projection succeeds. Both copiers
have normal10/10 retained-process stops; both import receipts persist exit0 with
three total and zero active/terminated Job Object processes. The first worker
has a persisted exit0 receipt with seven total, zero active/terminated Job Object
processes and held runtime/configuration custody. Supervisor normal drain is
37.7704ms; owner-observed drain is94ms. Stop, custody, joined result and runtime
records agree. Delivered JSON retains the omitted machine field and matches the
journal exactly. These are bounded own-state/normal-worker-stop claims only.

The first server's watchdog records REFERENCE_PAIR_HARD_DEADLINE in phase
server_deadline. The controller's subsequent stop send fails PROCESS_NOT_RUNNING;
the outer world failure remains PROBE_WORLD_CLOSE_UNCERTAIN. No normal server-stop
event or stopped export exists. Forced exit125 terminates all12 held processes,
with zero active Job Object processes and complete logs. The second server/worker
never starts. Both writer rows remain UNCERTAIN, world FAILED and parent FENCED;
all reservations stay held. Cases01-04 remain failed, without larger windows.

Diagnostic initial-state holds occur125.453s/130.844s after acquisition, launch
intent139.766s, first server ready178.422s. The post-continuation software check
runs201.813s-207.422s; the controller reaches normal stop after the finite server
has already been terminated. Twelve software checks total65.328s and18 parent
checks total15.422s overlap. These intervals are not authoritative campaign clocks.
The software holder still calls full pack resolution in every check. Next reduce
that repeated work under held custody and avoid delaying normal stop with work
that can safely follow it, retaining live authority/bytes/membership checks and
pre-dispatch rejection. Verify changed authority and failure handling before
another changed native case; no unchanged retry or bound increase is supported.

The failure audit matches435 captured source files, exact worker journal/receipt
joins, both copier/import receipts, the server watchdog and fenced reservations.
All40 real authority tables remain unchanged at$4.887796, including the old$0.7554
and four$1 holds and consumed decisions. No owned runtime remains; no model call.
The agent/protocol/capacity fixture remains synthetic, even with authentic game
and worker inputs. Native admission, complete live-state equivalence and disposal
remain unqualified.

Coverage inherits M1.6q F01/F02/F04/F07/F08/F09/F16,
N01/N02/N03/N04/N05/N06/N08, C06/C20/C23/C24/C36 and partial T01/T06/T11.
Complete live body/tool/policy matching, native admission, authoritative clocks,
disposal, T05/T10 and remaining isolation/native-loop evidence stay open. M0/G0
and unrelated M2-M7 remain unchanged; D18/D19 do not authorize M1 inference.

| Private evidence store | Files / bytes | SHA-256 |
|---|---|---|
| `2026-09-25-m1-worker-pair-native-05` | 695 / 48,972,664 | `5f0aba48171015a17136e7063ac4ee3c2aeb88121f0ff2a0e211372e711223b5` |
| `2026-09-25-m1-initial-worker-projection-01` | 6,087 / 23,827,018 | `ac3ad129113f0dd20f9c875890eb8932ca9ed50bc4d562a8c62fa21a47e1211c` |

Both bundles independently verify with extended Windows paths. The source store
retains both test selections and versions, the diagnostic failure/correction,
435 source pins and final authority/process checks. All415 prior milestone IDs
remain (416 current);1,634 local links resolve, progress is append-only and prior
SPEC/JSON are preserved. Seal pointers follow the archived documentation snapshot.
