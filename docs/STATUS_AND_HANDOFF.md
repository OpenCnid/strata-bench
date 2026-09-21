# Implementation checkpoint and next-session handoff

Updated September 21, 2026. Operator-only. [SPEC v0.2.99](../SPEC.md) defines
acceptance; [MILESTONES.md](../MILESTONES.md) owns progress and history.
[STATUS.md](STATUS.md) is the compact evidence index.

## Resume from the merged checkpoint

[Implementation PR #3](https://github.com/OpenCnid/strata-bench/pull/3) merged at
`f305b32005a61a9d72c430436127134ea64c1a3a`, including source head
`f55a00f993bfe72c0887a567cc9387de2d57d759`. It follows merged PR #2 at
`542a77ac760fb305b26941085e33447f392f8ba8`. This handoff is the separate
documentation change requested after the implementation merge. Verify its PR
and fetched main rather than assuming the implementation merge is the latest
commit. [Merge checks](verification/2026-09-21-session-handoff.md).

The full objective remains:

> Complete Strata according to SPEC.md and AGENTS.md through every required
> M0–M6 deliverable and acceptance gate. Preserve M7 and other conditional
> extensions with their activation conditions. Completion requires authoritative
> evidence for the full specification, not merely passing local tests.

**M0 remains incomplete; G0 fails; G1–G5 are not run.** The user requested this
stopping checkpoint to move sessions, not a scope reduction or permission
question at each later checkpoint. Verify the long-horizon goal and create it
only if absent. Do not mark it complete because these PRs merged.

1. Read AGENTS.md, SPEC.md, MILESTONES.md, this handoff, STATUS.md,
   [validation admission](operations/validation-admission.md) and the
   [September 21 checkpoint report](verification/2026-09-21-session-handoff.md).
   Revisit SPEC sections 3, 4.1, 6, 15–19 and impacted contracts; a first
   implementation review still requires the full specification.
2. Fetch origin, inspect actual Git/PR/worktree state and preserve changes.
   Start a fresh branch or worktree from updated main. Do not reuse an old
   merged implementation branch as the new baseline.
3. Recheck private accounting and relevant process state read-only. No game
   needs to launch to inspect this checkpoint. Never expose auth caches or
   secret-bearing process arguments.
4. State the next bounded M0 deliverable and verification criteria, then
   implement it. Do not restart the completed native accounting matrix,
   repeat unchanged live trials or expand unrelated M1 settings work.

## First implementation deliverable: M0.1d.1

The runnable `tools/m0_native_game.py PRIVATE_PLAN.json` already owns a real
vanilla server/worker and the selected native Dovetail root/helper/broker path.
Case 02 performs one real bounded look action, joins its receipt to the worker
journal, checks saved orientation and stops normally. **Its six model replies
are scripted (84 fixture units), not authentic model reasoning.** Case 01's
startup failure is retained. [Command, plan and evidence](verification/2026-09-21-m0-native-game.md).

Implement a reusable read-only evidence verifier around this existing path.
This work has **not started**. Join durable native attempts/receipts and
root/helper budget envelopes to executor/job/epoch-bound worker actions,
primitive charges, source/profile pins, stop receipts and available clock
evidence. Reuse `native_worker.py`, existing dispatch/accounting records and
the private run-cost verifier where applicable; do not rebuild the runner.
Keep synthetic fixture units, API-equivalent estimates and actual charges
distinct. Report unavailable clocks or scorer evidence as gaps, never zeros
or invented proof.

Exit evidence: the sealed case-02 bundle produces an independently reconstructed
report agreeing with its recorded six calls, 84 fixture units, one primitive
and terminal state. Tampered copies with missing, duplicate, foreign-scope or
conflicting receipts, altered sources and ambiguous stop evidence must reject
or retain explicit incompleteness; originals remain byte-identical. This is
verification of an existing authentic game run with scripted inference, not
a new run or full G0 closure. Keep M0.1d implemented_unverified until its
remaining live/model, clock, scorer, isolation and recovery contracts qualify.

Continue next through actual M0 dependencies: protected setup/writer authority
and scorer controls/nonleakage, bounded shutdown/resource behavior, and complete
game plus agent restoration with costs retained. Do not substitute more
documentation for implementation. If model admission stays blocked, these
independent implementation paths remain authorized.

## Durable accounting: D12 is consumed

Original authority: `validation-2026-09-18`, account
`authorization:validation-2026-09-18`, schema 2/D11, digest
`7aca7758f12eb1089f481d5d4bc19de2c6022cf1167b03056c32d41c3e4a819a`.
Store: `C:/Users/Darian/.strata/operator/provisioning/controller.sqlite`;
CAS: adjacent `objects`. Read these in place before any spending; do not
install another authorization. The original cap remains 10,000,000 microUSD
($10 API-equivalent), including helpers/retries/summaries. It is not an OAuth
invoice, exact subscription-quota conversion or fresh allowance.

| Request | Durable outcome | Estimated amount |
|---|---|---|
| `gateway-cd3156b226424332ac152974e1afc3ea` / `oauth-first-receipt` | UNSETTLED; missing original usage; request and envelope hold counted once | $0.7554 held |
| `gateway-0628d059d68c4106b3cc1062fc67095b` / `oauth-receipt-d12` | SETTLED from exact captured completed receipt; new envelope FINALIZED | $0.001458 settled |
| Aggregate | Two actual requests; one valuation; uncertainty remains | **$0.756858 committed/reserved** |

D12 allowed one distinct request within the original allowance and is consumed
(`REQUEST_RESERVED` is the durable one-use trial state). Its original native
run exited 1; successful offline settlement does not pass reply delivery.
No request was replayed and every old operation row remained unchanged.
General admission remains blocked by the first hold. Do not refund it, blindly
replay it, rearm D12 or infer another request from remaining allowance.
[Outcome, usage and sealed evidence](verification/2026-09-21-native-oauth-d12.md).

The changed `native-chatgpt-fixed-https-responses/2` transport validates a
complete bounded usage receipt before normalizing unsupported-media HTTP 200
to SSE. It has source/local-HTTP evidence only; future authentic conformance
requires admissible authority and the exact changed profile. No new model run
is needed for M0.1d.1. D01–D11 persist; no VM, prior-spending or exact OAuth
billing question is pending. D11's zero opening baseline is historical, not
the current total.

## Evidence and failures to preserve

- [Native accounting](verification/2026-09-20-native-dispatch.md) already covers
  retries, deduplication, streaming, compaction, helpers and restart on the
  pinned CLI/local synthetic provider. Continue that implementation.
- [Restricted tools](verification/2026-09-21-native-no-patch.md) and
  [native reader canaries](verification/2026-09-21-native-reader-boundary.md)
  give narrower positive evidence; raw loopback/sibling-read failures remain.
  Preserve Codex/Dovetail, declared tool projections and protected brokerage.
- [Activation and fresh handoff](verification/2026-09-21-native-activation-exec.md)
  preserve synthetic usage 56→140→224 without refund. Full native frozen-skills,
  script/macro capability and authentic joint restoration remain incomplete.
  Retain missing-denial/export failures and all derived/source generations.
- [Completed Forge reference](verification/2026-09-21-completed-craft-reference.md)
  passes its 30-check audit with 78 primitives and scoring disabled. The newer
  [protected case 04](verification/2026-09-21-process-history.md) completes
  craft and 80 primitives but fails guardian at 500.1327/500 ms: pair UNCERTAIN,
  audit 28/32, failure audit 18/18, score import denied. Terminal outer handles
  (29 server/118 client) do not erase that failure.
- Every prior failed 500-ms sample remains in the ledger/reports, including
  501.995, 503.5059, 507.6092, 503.6561, 510.8433, 508.2221 and 500.1327 ms.
  Passing later samples do not relax the threshold. Preserve the unexplained
  inventory failure and interrupted reference scopes; no unchanged retry.
- The five effective-file failures remain: BHMenu/NoMoreWorldSettings client
  roles, old InventorySorter/SophisticatedCore missing entries and obsolete
  Create keys. Mineflayer/E9E negotiation remains failed; Forge is a separately
  identified fallback. Complete role/config provenance and seals are required.
- Private scorer setup history, writer/team authority, joint controls/parity,
  nonleakage, full host/game costs/time and game/agent recovery remain required.
  T05, simultaneous N=1/2/4 capacity, 1/8/24-hour soaks, pilot/confirmation and
  later required E6E/E2E/M6 work remain open. N=2 needs a second licensed identity
  when that dependent work is reached. M7/extensions retain activation conditions.

## Local operational map

| Location | Purpose |
|---|---|
| `C:/Users/Darian/Desktop/codex/minecraft-benchmark` | Main checkout; verify clean state before updating or branching |
| `C:/Users/Darian/.codex/worktrees/09a0/minecraft-benchmark` | This checkpoint worktree; implementation branch merged, documentation branch follows; preserve local tools and changes |
| `.codex/worktrees/581d/minecraft-benchmark` and `.codex/worktrees/56fa/minecraft-benchmark` under the user home | Prior worktrees; preserve them |
| `C:/Users/Darian/.strata/evidence/` | Private raw source/run/audit bundles, never public or gameplay-visible |
| `.../2026-09-21-m0-native-game-02` | Existing sealed connected game/native bundle for the next verifier |
| `.../2026-09-21-native-oauth-d12-audit-01` | Before/after accounting and offline receipt recovery; preserve originals |
| `C:/Users/Darian/.strata/servers/e9e-1.27.0` | Original reference server; preserve saved bytes |
| `C:/Users/Darian/.strata/clients/e9e-noninput-01` | Prepared separate-desktop client; shared-desktop input stays paused |

Pinned native CLI: 0.154.0-alpha.6.2, SHA-256
`960c111d47afd61669954b9df9e56083e302edbfa3ef6962d81dcc14a30051dc`;
Dovetail 0.4.1 at `15c306ccfef28eb5f616fadcd5fd8eac0663e361`.
Development toolchains: Python 3.12.14, Node 24.19.0, Windows x64 Temurin
17.0.20.1+1. Exact private launch/source/profile pins come from each bundle;
do not infer runtime identity from an old installed-version paragraph.
[README](../README.md) records build inputs. No clean-machine qualification.

Keep the ordinary desktop usable. Separate folders/conversations/desktops are
not isolation. Never mount operator source, hidden criteria, credentials,
raw world/server data, admin controls or sibling/probe artifacts into gameplay
or helpers. Dated reports and the append-only log retain superseded next
actions as history; this handoff is the current instruction sequence.
