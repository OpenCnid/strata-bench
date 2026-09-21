# Implementation checkpoint and next-session handoff

Updated September 21, 2026. Operator-only. [SPEC v0.2.100](../SPEC.md) defines
acceptance; [MILESTONES.md](../MILESTONES.md) owns progress and history.
[STATUS.md](STATUS.md) is the compact evidence index.

## Resume from the merged checkpoint

[Implementation PR #3](https://github.com/OpenCnid/strata-bench/pull/3) merged at
`f305b32005a61a9d72c430436127134ea64c1a3a`, including source head
`f55a00f993bfe72c0887a567cc9387de2d57d759`. It follows merged PR #2 at
`542a77ac760fb305b26941085e33447f392f8ba8`. The separate documentation PR #4 then merged at c2161a6e79cea0c668ab993df149ab1ed5af119b. This handoff now tracks resumed M0-only implementation; preserve the current branch and changes until its checkpoint is merged. [Merge checks](verification/2026-09-21-session-handoff.md).

The current user request and active long-horizon goal are **M0 and its complete G0 only**. Preserve all required later milestones and conditional extensions; do not advance unrelated M1–M7 work. This is the current task boundary, not removal of product requirements.

**M0 remains incomplete; G0 fails; G1–G5 are not run.** PRs #3/#4 are merged; fetched main matches `c2161a6e79cea0c668ab993df149ab1ed5af119b`. Implementation resumed on fresh `codex/strata-m0-g0`. Do not recreate the already active M0/G0 goal or mark it complete because a checkpoint is finished.

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

## Current implementation and next action

M0.1d.1 is verified for its bounded read-only evidence-reconstruction contract. [Implementation, command and exact evidence](verification/2026-09-21-native-game-verifier.md): existing case 02 independently reconciles six scripted calls, 84 fixture units, one real primitive, root/helper closure and stopped state; 52 focused checks and 16 synthetic derived-copy negatives pass. The original flat manifest omitted 105 deep plugin files; their preexisting sealed bootstrap hash chain verifies them. Preserve the flat-inventory failure and original bytes. No game or model run was repeated. Missing authoritative clocks/scorer/isolation/shutdown/recovery evidence remains explicit; parent M0.1d remains implemented_unverified.

M0.1d.2 is verified narrowly for durable request/charge attribution. [Changed-profile integration](verification/2026-09-21-native-game-traces.md) adds exact original/forwarded broker requests, atomic per-primitive charges and complete request/event/receipt joins. 139 distinct Python/35 Node checks, 28 actual native/game checks and six new synthetic derived-copy negatives pass. One new real vanilla run used scripted inference, six calls/84 fixture units, one primitive and normal cleanup. Its flat 4,244-file seal is complete; all 69 original source files and the $0.756858 held/settled accounting remain unchanged. No Java remains. Old case-02 gaps/failures are preserved. No full scorer, isolation, clock, shutdown or recovery qualification.

Next bounded work is **M0.2c.3b.3 setup-history/scorer authority**: inspect the pinned native mode/admin/team mutation routes and implement history evidence that rejects intervening changes in the existing signed craft importer. Matching startup/before/after points cannot prove continuous setup validity. Keep all protected-custody, authentic-control, parity and nonleakage gates; do not promote the failed protected craft references to scorable outcomes. Model admission remains blocked, but this source work is independent.

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
