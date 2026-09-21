# Connected game request and primitive attribution

September 21, 2026. M0.1d.2; F03/F06/F09/F11/F16, N01/N02/N03/N06,
C06/C09/C15/C20, partial T01/T07/T12, G0 items 1/4/6.
**M0 remains incomplete; G0 fails.** Current work and the active goal cover
M0/G0 only; the later roadmap remains preserved.

## Implemented behavior

The [broker](../../src/mcbench/broker.py) records the validated original game
arguments in the private call event and atomically commits the normalized
forwarded request, event binding and forwarding intent before transport.
`broker-durable-game-request/1` is an additive private database format. Its
original-row boundary preserves legacy missing preimages without backfilling
them. Cached replies still return without forwarding; ambiguous calls remain
unknown without replay. A failed intent write rolls back before transport.
Missing/conflicting new preimages or native argument events reject inspection.

The [Mineflayer journal](../../backends/mineflayer/src/journal.ts) and
[action lane](../../backends/mineflayer/src/actions.ts) commit the primitive
counter and its attribution together before the adapter's attempted emission.
Capability minor 11 declares `durable-pre-dispatch-charge/1`. The private epoch
opening record and each charge bind scope, action/request digest, cumulative
and per-action sequence, local monotonic time and safety-release classification.
A failed write prevents that emission; a crash after commit retains the charge.
Charges explicitly do not confirm packet delivery. Limits, release accounting,
deadlines, cancellation and no-replay behavior are unchanged. The Forge lane
retains its distinct journal rather than claiming this Mineflayer policy.

The [read-only verifier](../../evaluator/src/strata_evaluator/native_game_evidence.py)
now joins exact broker requests to their returned worker observations/actions,
and charge traces to acceptance/terminal order, request hashes and counters.
New incomplete traces reject. The old case-02 archive still reconciles with
both gaps explicitly present; its report after this change has content digest
`3bf56c9bb85871110cc2950265a4626b520c80bf68006763b9d7bebd829c53cb`.
Existing native export source shape remains unchanged for legacy calls.

## Changed-profile authentic integration

One new finite vanilla trial exercised the changed broker/worker. It reused the
existing native Dovetail/root/helper path, with **scripted model replies only**.
This was a new trace-attribution test, not a repetition to replace an old failed
shutdown sample or a scientific/model experiment.

Private `2026-09-21-m0-native-game-03` used a fresh checked copy of the retained
official vanilla 1.19.2 server/world, loopback port 25587, a fresh campaign/lease,
32-primitive limit, 180-second worker and 300-second server bound. All 69 original
source files remained unchanged. The existing licensed avatar cache was used;
no game installation, model request, shared-desktop input or new authority.
Windows x64, Python 3.12.14, Node 24.19.0, Mineflayer 4.39.0, protocol 1.68.0,
Temurin 17.0.20.1+1, pinned Codex CLI 0.154.0-alpha.6.2 and Dovetail
`15c306ccfef28eb5f616fadcd5fd8eac0663e361` apply. Exact dispatch sources are archived.

All **28 native integration checks pass**. Root/helper isolation checks for
this restricted surface, helper game denial, six scripted requests/84 fixture
units, bounded real action, matching receipt and native-exit game stop pass.
The job is FINALIZED with both envelopes closed; worker/server exit zero without
forced cleanup. Whole run: **194.985 s**; native lifecycle: **25.7694511 s**.
Saved player orientation changed and matches the final observation within 0.01
degrees; position matches. No Java remained after cleanup.

The independent reusable verifier passes on the stopped bundle:

- Six forwarded game request preimages exactly join their private call events
  and returned records.
- One actual bounded look has one committed charge event and matching terminal
  receipt. Five worker observations and three returned observations reconcile.
- Root/helper consumption remains six scripted calls, 60 input tokens including
  12 cached, 24 output and **84 synthetic fixture units**, not OAuth usage or money.
- Flat and complete inventories both pass: **4,244 files / 78,645,755 bytes**.
  Dependency-lock and four public schema bytes are now archived and checked.
  The old archive's 105 omitted flat-manifest entries remain a retained failure.

Bundle seal:
`235481abe34d26b9abd5f28b7b7b83f3193c341e4056be798ca3f6b3a771d6bd`.
Private verifier report in `2026-09-21-m0-native-game-verifier-02`, content digest:
`a4a6dc54508d379929c04b548246c0a9862a697124ed348d8ed56293f74fd8f3`.
Native profile `d1828e9a0f7ceffacea683d559c17f1394bcff0d74fafc1ba8d2ece57cb142dc`;
worker capability `16e8359f76bc216afec147187fa8de6170236b35ef307c79b814154bddcc2951`.

Six additional derived-copy negatives pass: missing/changed forwarded request,
changed native arguments, missing charge, wrong charge request digest and wrong
charge sequence. Original bytes remain unchanged. Mutation audit digest:
`385080763affb41084fc77e46b9964563006bbb873128fdd263159debee9632c`.
These are synthetic corruptions of copies, not extra game runs.

## Source checks and retained limits

Executed with current source on `PYTHONPATH=src;evaluator/src;tools;tests`:

| Check | Actual result |
|---|---|
| Native evidence, broker, broker lifecycle and native export Python selection | 109 pass / 11.25 s |
| Gameplay package exclusion and all canonical schema/record checks | 29 pass / 0.90 s |
| Final request-corruption/legacy-migration subset, including added argument conflict | 4 pass / 0.32 s; three overlap the first selection |
| TypeScript validator freshness and build | Pass |
| Selected Node action suite | Initial 34 pass / 1 fail; repaired environment then failed case alone passes; 35 distinct cases |
| Focused Ruff and whitespace | Pass |

There are **139 distinct Python checks** in these selections. The fresh worktree
initially lacked the `.venv/Scripts/python.exe` expected by the Windows cache ACL
helper; `uv sync --frozen --python 3.12.14` restored that environment. The retained
Node failure was `AUTH_CACHE_PROTECTION_FAILED`; the case then passed without
changing its threshold. Dependencies were installed from the pinned locks;
no game was installed. A proposed extra request-history guard initially rejected
a legitimate cached legacy query; the targeted migration test caught it, and the
guard was removed. Later queries cannot establish the original forwarding body.
The actual game trial was not repeated for either source-test correction.

The original authority was read before and after: original $10 allowance,
$0.7554 held plus $0.001458 settled, **$0.756858 unchanged**, two distinct real
requests, one valuation, uncertainty true. D12 remains consumed; general model
admission remains blocked. No replay, refund, reset or new model allowance.

This qualifies only the recorded request/charge attribution contract. Full
native reasoning, isolation, authoritative server/avatar clocks and performance
series, role/pack locks, private scorer/setup controls, 500-ms shutdown and joint
game/agent recovery remain open. Preserve every previous shutdown failure, all
five effective-file failures and Mineflayer/E9E incompatibility. A normally stopped
reference and a passing trace verifier are not an authoritative score or a complete
checkpoint. Continue M0 setup-history/scorer authority using the existing signed
craft importer, then the remaining shutdown and joint recovery dependencies.
