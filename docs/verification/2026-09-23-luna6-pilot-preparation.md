# Fresh GPT-6 Luna pilot preparation

M0.1d.9 remains in_progress; G0 remains fail. The preceding D17 turn made
progress by selecting GPT-6 Luna in source and durable authority. This turn
fixes the remaining launcher/export gaps and prepares a concrete next pilot.
D18 is a **pending proposal**, not a granted execution decision.

Coverage: F03/F06/F09/F11/F12/F16, N01/N02/N04/N06, partial
T01/T03/T04/T07/T12/T13/T14, G0 items 1/4/6. Full isolation remains deferred
under D14. M1–M7 and every prior failure remain intact.

## Source corrections and checks

The outer game launcher still compared preregistration against the historical
scripted model constant. It now obtains the admitted model from the original
authorization and checks it before pack/output preparation. Tests exercise the
real launcher and sealed retention consumer with synthetic admission: matching
GPT-6 Luna reaches pack preparation; either cross-model mismatch fails earlier.

The operator JSON/TypeScript exports now include `ModelExecutionAuthorization`
and the current model/catalog enums. Public schemas and worker implementation
bytes are unchanged; the existing sealed worker is reused.

The prepared D18 admission path requires both old pilots finalized with all six
requests settled, exactly $0.773794 prior exposure, the current D17 model
authorization, the retained unknown-row digest and an explicit approved private
decision. A proposal with `user_authorized=false` is rejected. The original
allowance, unknown holds, request count, timeout and zero-helper limits persist.
No D18 grant was installed in the original database.

Actual verification:

```text
python tools/export_schemas.py
node backends/mineflayer/tools/generate.mjs
pytest tests/test_native_game_retention.py tests/test_records.py tests/test_native_piloting.py tests/test_model_selection.py tests/test_luna6_pilot_budget.py tests/test_pilot_budget.py -q
# 148 passed
npm run build --prefix backends/mineflayer
# pass
ruff check .
# pass
git diff --check
# pass
```

The initial new admission tests retained two fixture failures: one expected the
later reinstall error instead of the earlier retained-exposure rejection; the
other attempted two simultaneous synthetic jobs for the same avatar, correctly
violating its unique lease constraint. Corrected fixtures pass; admission was
not weakened to accommodate them.

Native cases04 and05 both pass 16/16 with scripted responses and a synthetic
worker. Case05 includes the proposed admission source and is accepted by the
actual preflight consumer. Each makes three scripted requests, forwards one
valid observation, exits zero and closes. These checks do not establish live
reasoning or full observation-to-action correctness. Both preserve all 39
original authority tables and make zero real model requests.

## Prepared private inputs

`C:/Users/Darian/.strata/evidence/2026-09-23-luna6-pilot-preparation-01/plan.json`
references the fresh `m0-pilot-03` vanilla baseline, the unchanged sealed
Mineflayer worker/PackLock, and case05's selected catalog/tool projections.
The new cohort is `gpt-6-luna-2026-09-23`, provider is OpenAI, helpers are zero,
and learned_overlay is null. Both earlier used instances remain untouched.

The independently rehashed instance has 4,118 files, no player save and an empty
session lock. The audit checks the real retention identity, fresh artifacts,
current source pins, exact public prompt and proposal bounds, then calls the
actual driver. It receives `PILOT_ACCOUNTING_BLOCKED` before output or game
startup. The false-approval proposal separately receives
`PILOT_DECISION_REQUIRED`. All original authority tables, template files and
the prepared instance remain unchanged; no credentials were read.

Proposed execution: one body, zero helpers, at most six requests and 90 native
seconds, at most two bounded look/walk actions and $1 additional API-equivalent
estimate from the original $10. Existing exposure remains $0.773794, including
the $0.7554 unknown hold; the maximum combined exposure would be $1.773794.
The native duration excludes the separately bounded server startup/drain.

Plan SHA-256: `d1b15ed0c55c071a5a9924b205bc87d81d966a119abc0eb68e41189a75811833`.
Preregistration: `3c9292a24cfdc7901a1f564a22be2a19d9207bea823d0661016a5018443550cd`.

All three private archives independently verify under EvidenceBundle:

| Archive under the private evidence directory | Seal SHA-256 | Files / bytes |
|---|---|---|
| 2026-09-23-luna6-native-04 | `5df85d2a87fb0fad695a001e6e9a37ac19adb26c62d72811d5500e11672434fc` | 3,722 / 73,435,989 |
| 2026-09-23-luna6-native-05 | `1c1d0928671daf920afe220fe18a95b50c3ee6590f1af56fb158c83a548a6aa7` | 3,727 / 73,602,510 |
| 2026-09-23-luna6-pilot-preparation-01 | `03a061f185cbd65fcaf62f8529f9a716d76f8d98f556f2d585f9fabe798dc3fe` | 16 / 1,581,175 |

Next: after a distinct execution approval, write its exact approved decision
and a new input version referencing this unused instance. Recheck original
authority/process state, then run once and retain the actual outcome. No new
installation, worker rebuild, replay of old requests or new allowance is needed.
While approval is pending, independent M0 source work remains authorized.
