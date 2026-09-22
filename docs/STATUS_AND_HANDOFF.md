# Implementation checkpoint and next-session handoff

Updated September 22, 2026. Operator-only. [SPEC v0.2.123](../SPEC.md) defines
acceptance; [MILESTONES.md](../MILESTONES.md) owns progress and history.
[STATUS.md](STATUS.md) is the compact evidence index.

**Restored sealed baseline — M0.1d.8 (in progress):** [Implementation and authentic evidence](verification/2026-09-22-restored-native-baseline.md) now restore verified stopped state into a new sealed installation and run the existing native root/helper/action path on that declared baseline. Actual restoration succeeds; Java reaches readiness in 32.487 s within the unchanged 80 s bound. All 29 native checks and independent evidence reconciliation pass: one real primitive, seven scripted calls/98 fixture units, 26 captured state files and 46 normally exited owned processes. The 133 affected source checks plus the gameplay-package check pass. Materialization adds one expected journal event; all old rows, 33 other tables and original accounting are preserved, and restore/gameplay leave all 34 tables unchanged. D12 remains consumed. Next restore this run's game, agent and accounting state together under a new epoch; no unchanged baseline rerun. The old 97.408/80-second fresh-start failure stays failed. Scorer/setup, isolation, authoritative clocks/save custody, E9E and full recovery remain open; M0 incomplete/G0 fail.

**Sealed native execution — M0.1d.8 (in progress):** [Implementation and retained startup failure](verification/2026-09-22-sealed-native-startup.md) connect the existing native action/helper runner to the actual sealed worker and inventory-bound stopped capture. The changed authentic run fails `SERVER_START_TIMEOUT`: Java reaches readiness after 97.408 s against the 80 s bound, before any avatar or native/model action. All 14 owned processes exit normally; the independently verified stopped component retains 20 state files, without claiming a complete checkpoint. Source checks pass after correcting a malformed synthetic observation fixture. All 34 original authority tables and consumed D12 remain unchanged. Next implement explicit sealed-template restoration from the retained no-avatar world, then qualify connected execution and joint recovery; do not reuse the mutated instance as fresh or repeat the unchanged startup profile. Scorer/setup, clocks, isolation and E9E remain open; M0 incomplete/G0 fail.

**Actual vanilla seal and joint launch — M0.3a.2/.3:** [Implementation and evidence](verification/2026-09-22-vanilla-packlock.md) seal the original vanilla request with nine bound provisioning checks and fix server/worker startup ordering. M0.3a.2 is verified for the installed vanilla template/provenance disposition; M0.3a.3 remains implemented_unverified for authentic joint launch. The actual 11,722-file sealed import passes with all owned processes exited; 70 distinct focused source cases pass (final affected selection 41/41). Original accounting, consumed D12, all old object/event rows and 31 other authority tables are preserved. Next connect the existing native action/recovery runner and inventory-bound capture to this sealed launch, then collect changed-profile evidence. Scorer/setup, E9E, isolation, complete clocks and canonical recovery remain open. M0 incomplete/G0 fail; no game/model/shared input in this checkpoint.

**Prior checkpoint (fc9b381), sealed worker launch — M0.3a.3:** [Implementation and actual-file inspection](verification/2026-09-22-pack-worker-launch.md) add LaunchProfile/2 and `pack launch-worker`: pinned software/settings with typed fresh run identity, generated held configuration and owned cleanup. 127 distinct focused source cases pass; the final affected selection is 34/34. The actual 11,722-file candidate validates after retaining its initial escaped-property rejection. All 34 authority tables and $0.756858 accounting remain unchanged. The original pack stays VERIFIED/unsealed and rejects launch; new candidate review refs are not yet published. Next complete bound provisioning checks and the actual seal, then join native launch/server custody/capture to it. Fresh-instance launch only; scorer/setup/clocks/isolation and canonical recovery remain open. M0 incomplete/G0 fail; no game/model/shared input.

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

**Pinned native worker — M0.1d.7:** [Connected implementation and evidence](verification/2026-09-22-pinned-native-worker.md) now launch the real vanilla worker from its expected-hash private bundle, with file locks retained through owned stop. The changed headless trial passes 29 native checks and reusable evidence reconciliation: one real action, six scripted calls/84 fixture units, 28 stopped state files and zero active owned processes. All 34 original authority tables and 69 source-server files remain unchanged. 121 distinct focused source cases pass. Pinned recovery passes 35 native checks and a 28-check independent audit: saved player/root state restored, old token/epoch denied, one fresh action, costs preserved to 12 scripted calls/168 fixture units and two total primitives. M0.1d.7 is verified for this development scope. Next bind the actual PackLock/server launch and custody; no unchanged pair rerun. Actual PackLock/server custody, scorer/setup, complete clocks and isolation remain open. M0 incomplete/G0 fail; no live model or shared input.

**Private worker runtime — M0.3a.2:** [Preparation and relocated checks](verification/2026-09-22-worker-bundle.md) copy the exact Mineflayer worker, Node and stdlib-only Python ACL helper outside the checkout. All 11,722 files stay pinned during a successful worker import and real Windows ACL checks using a synthetic cache; weakened permissions reject. Fourteen Python and 12 Node source cases pass. Both initial Windows-path failures remain retained. All 34 authority tables and original $0.756858 accounting are unchanged; no game, account authentication, model or shared input. The subsequent M0.1d.7 profiles now use this bundle through execution and development recovery. Actual PackLock/server custody and canonical recovery remain open. M0 incomplete, G0 fail.

**Installed Mineflayer runtime — M0.3a.2:** [Implementation and actual verification](verification/2026-09-22-mineflayer-runtime.md) add offline lock/archive/file verification and an operator command. All 111 packages and 9,376 installed files match; 39 npm wrappers independently regenerate. A real import-only worker check passes under 9,599 held inputs. 26 distinct source cases, 10 independent evidence checks and 39 publication/conservation checks pass. One private report object/event is added; prior history, 32 other tables and $0.756858 accounting remain unchanged. The pack stays VERIFIED/unsealed. The authenticated worker/Python helper are now connected under M0.1d.7. Next bind the actual server/worker launch and configuration/update policy, finish remaining component review, then seal and connect canonical custody/recovery. D05 account/EULA evidence already exists. M0 incomplete, G0 fail.

**Sealed-pack launch connection — M0.3a.3:** [Implementation and verification](verification/2026-09-22-pack-launch.md) connect a durable PackLock to the bounded server runner. Both role inventories, marker, command and executable are checked before launch; overrides and changed instances reject. 116 distinct source/process cases pass, including a disposable Python process. The actual unsealed vanilla request is refused with 11/11 checks and all 34 tables/accounting unchanged. This is fresh-instance preflight, not runtime custody or an authentic game pass. M0.3a.3 is implemented_unverified; M0 incomplete, G0 fail. Next complete the actual Mineflayer/server launch/runtime/update and legal/source checks, seal the pack, then inventory-bound custody/recovery.

**Current vanilla installed inventory — M0.3a.2:** [Actual publication and source fix](verification/2026-09-22-vanilla-inventory.md) advance the original vanilla request to VERIFIED for all 4,097 installed-file entries; the PackLock remains unsealed. File import preserves existing typed operator evidence while rechecking bytes and refusing visibility changes. Ninety focused source checks and 25 independent actual-state checks pass. All 31 unrelated tables, previous object/event history, source roles and original $0.756858 accounting remain unchanged. Forty-one component records retain source notices, distribution terms and absent declarations without a standalone license or legal-qualification claim. Both preparation/import failures remain retained. Next pin the active Mineflayer worker/server launch and runtime/update policies, complete required legal/source review and bound provisioning checks, then the actual PackLock and canonical custody/recovery. Vanilla uses Mineflayer without a renderer under SPEC §7. No game/model/shared input; M0 incomplete, G0 fail.

**Role assembly and cold-restart checkpoint — M0.3a.2:** [Implementation and authentic bounded evidence](verification/2026-09-22-vanilla-roles.md) assemble 4,097 exact client/server/Java files, reject incomplete provenance before any installed-file import, and qualify the changed-environment server start/restart narrowly. Both rounds stop normally in 67.312/26.282 s; software, configuration and saved-world continuity match. Fifty-one focused source checks plus two process/package checks and 34 independent conservation checks pass. The empty-environment JNA failure remains retained. Original accounting, 32 durable tables and 3,781 source files are unchanged; no model/client/shared input or Java remains. The installed inventory is now separately verified, with absent declarations retained in component records; remaining legal/source review, active Mineflayer launch/update policy and the PackLock stay open; canonical custody/recovery, scorer/setup and isolation remain open. No unchanged server-pair rerun. M0 remains incomplete and G0 fails.

**Client/Java software checkpoint — M0.3a.2:** [Actual client preparation and Java source inventory](verification/2026-09-22-vanilla-client.md) now provide 3,432 exact client software files, 65 ordered classpath entries and all 3,364 distinct assets. Four missing shared-cache libraries use exact verified server copies; the shared installation remains unchanged. All 316 installed Java files match the publisher ZIP, and a separate private copy preserves them and 183 legal/notice files. Fifty-one focused source checks plus the gameplay-package check pass; 32 durable tables and original accounting remain unchanged. Role assembly and bounded server cold restart now have separate evidence; complete licensing, client launch/update policy and the PackLock remain open. No game/model/input activity or complete PackLock claim.

**Server software checkpoint — M0.3a.2:** [Acquired vanilla server preparation](verification/2026-09-22-vanilla-runtime.md) now joins the original acquired bundle to the installed inner server and all 29 libraries, then prepares 31 independent private software files. The actual audit preserves all 63 source files, 32 durable tables, existing evidence and original accounting. Sixty-seven distinct focused source cases pass. The SLF4J archive-metadata rejection and initial audit/parser errors remain sealed. Embedded and published provenance/license metadata is retained; five Mojang component license declarations, shaded/native contents, compatible client/Java roles, configuration/update policy and cold restart remain open. Continue those concrete PackLock dependencies using the prepared bytes; no unchanged preparation/game rerun. M0/G0 remains incomplete/fail.

**Current acquisition result — M0.3a.1:** [Metadata-bound vanilla intake](verification/2026-09-21-vanilla-acquisition.md) is verified for distribution intake: the original vanilla request is now ACQUIRED with exact official client/server artifacts and a version-2 receipt. The altered shared client JAR was rejected and retained; the installation was not replaced. Forty focused source tests pass. All 31 non-intake tables, existing objects/journal prefix, E9E record and original $0.756858 accounting remain unchanged. No game/model/desktop input occurred. Next complete compatible installed-role provenance, runtime configuration/update policy and the real PackLock; scorer, isolation, client-startup and canonical recovery gaps remain.

**Current history admission — M0.2c.3b.3c.2:** [Plan 3 implementation and evidence](verification/2026-09-21-protected-craft-history.md) requires signed clear startup before client readiness and complete history at import. 196 focused source/JVM checks pass. Authentic case 01 passes startup binding but fails the 420-second reservation; fresh case 02 fits a smaller reservation, then fails client bridge startup at its existing 270-second bound. No new craft/guardian sample or score is claimed. Both failures are sealed; retention audits pass 16/16 and 19/19, all processes exit, credentials retire and accounting stays unchanged. Continue independent M0 provenance/lock and canonical recovery work; revisit the integrated history craft only after a relevant startup fix.

**Current shutdown result — D13:** [The new 1,000-ms policy passes its authentic normal-shutdown sample](verification/2026-09-21-d13-shutdown.md): complete Java tree proof **568.994 ms**, real seven-operation craft, 74 reconciled primitives, normally closed protected custody and stopped pair. Independent audits pass 33/33 and 28/28; all held processes terminal, credentials retired and desktop unchanged. Earlier 500-ms failures stay failed under their old profile. This resolves the named normal-stop blocker for D13, not full T07/G0 or scoring. Next connect the sealed candidate to remaining scorer/setup/provenance and canonical recovery requirements; no unchanged craft rerun or more 500-ms optimization.

**Latest working behavior:** [M0.1d.6 development recovery](verification/2026-09-21-native-game-recovery.md) resumes the captured vanilla world, native root notes and preserved accounting together. Case 02 passes 35/35 native checks with scripted replies, stale token/epoch rejection, saved-player assertions, one new action and normal recapture. Cumulative 12 calls/168 fixture units/two primitives; original accounting unchanged. Failed case 01 and failed source case 04 remain sealed. This closes the bounded development continuation only. Next connect canonical checkpoint/provenance, scorer/setup and isolation; D13 now passes the authentic normal-stop sample, with other fault qualification still required. No unchanged live rerun.

M0.1d.1 is verified for its bounded read-only evidence-reconstruction contract. [Implementation, command and exact evidence](verification/2026-09-21-native-game-verifier.md): existing case 02 independently reconciles six scripted calls, 84 fixture units, one real primitive, root/helper closure and stopped state; 52 focused checks and 16 synthetic derived-copy negatives pass. The original flat manifest omitted 105 deep plugin files; their preexisting sealed bootstrap hash chain verifies them. Preserve the flat-inventory failure and original bytes. No game or model run was repeated. Missing authoritative clocks/scorer/isolation/shutdown/recovery evidence remains explicit; parent M0.1d remains implemented_unverified.

M0.1d.2 is verified narrowly for durable request/charge attribution. [Changed-profile integration](verification/2026-09-21-native-game-traces.md) adds exact original/forwarded broker requests, atomic per-primitive charges and complete request/event/receipt joins. 139 distinct Python/35 Node checks, 28 actual native/game checks and six new synthetic derived-copy negatives pass. One new real vanilla run used scripted inference, six calls/84 fixture units, one primitive and normal cleanup. Its flat 4,244-file seal is complete; all 69 original source files and the $0.756858 held/settled accounting remain unchanged. No Java remains. Old case-02 gaps/failures are preserved. No full scorer, isolation, clock, shutdown or recovery qualification.

Current **M0.2c.3b.3c setup mutation history** has partial authentic evidence. [Implementation/evidence](verification/2026-09-21-setup-history.md): telemetry 0.3.7/startup 8, eight required mixins/25 verified native selectors, sticky counters, exact signed point/stop joins and rejection of reversed mutations. Native shutdown requires a single exact parsed command matched to its actual native handler/source/thread. Source/JVM controls pass. One changed headless E9E reference passes 33/33 independent checks: hooks applied, clear startup/history, one correlated native stop, six processes exited, all 18,225 source files unchanged. It performs no authentic mutation or craft. Next implement and exercise preregistered private mutation controls, retaining all unmediated FTB/KubeJS/write routes, custody, parity/nonleakage and scoring gaps. Do not promote failed protected references or repeat the unchanged startup. Model admission remains blocked; the original authority rechecked at 23:26:31 UTC still totals $0.756858 with uncertainty and D12 consumed.

Continue next through actual M0 dependencies: protected setup/writer authority
and scorer controls/nonleakage, bounded shutdown/resource behavior, and complete
game plus agent restoration with costs retained. Do not substitute more
documentation for implementation. If model admission stays blocked, these
independent implementation paths remain authorized.

M0.2c.3b.3c.1 is verified for the fixed private world-mode control.
[Source and authentic verification](verification/2026-09-21-setup-control.md):
58 source/JVM/package checks and 42/42 independent authentic checks pass.
Intermediate Creative and final Survival saves are independently retained;
matching final state does not erase two signed mutations. Six held processes
exited; all 18,225 original files are unchanged. No model/client/desktop input.
The single consumed reference in
`C:/Users/Darian/.strata/evidence/2026-09-21-setup-control-live-01`
must not be restarted. Other mutation routes, custody, parity and scoring
remain unqualified. Accounting read-only at 23:59:14 UTC is unchanged.
Continue integrated M0 joint recovery while preserving these independent gaps.

Current M0.1d.3 implements durable complete-set publication and a reusable operator
verifier. [Source/process and recorded-native evidence](verification/2026-09-21-restored-set.md):
107 distinct focused cases and 17/17 offline audit checks pass. The audit retains
an actual native component with scripted responses and synthetic world data;
no authentic game restore is claimed. Costs and old source files stay unchanged.
M0.1d.4–.6 now connect stopped vanilla capture, preregistered retention and
a fresh-epoch development continuation. Canonical checkpoint admission still
requires authoritative save/custody/clocks and a sealed pack. Existing game runs
without prior retention policy cannot be retroactively promoted to checkpoints.

M0.1d.4/M0.1d.5 now have partial authentic component evidence.
[Connected capture and retained failure](verification/2026-09-21-native-game-retention.md):
case 04 passes 29 native checks, six scripted calls/84 fixture units and one real
primitive. Native preregistration/retention and 28 captured real world-state files
independently reconcile after three complete owned-process exits. The outer run
fails `M0_CAPTURE_INCOMPLETE` on normal/extended Windows path equality and has no
joint receipt; keep that sealed failure. The fixed comparison has four focused
passing checks and now publishes successfully in recovery case 02; the original
case-04 failure remains unchanged. Original 68 source files
and $0.756858 accounting are unchanged; no Java remains, D12 stays consumed.

Original bundle: `C:/Users/Darian/.strata/evidence/2026-09-21-m0-native-game-04`;
seal `cbe9ad5579386734b82f1680e01bbd2b8bde214eff370deab4bb598c51e37cfa`.
Independent audit in adjacent `2026-09-21-m0-native-game-04-audit` verifies the
components and explicitly retains outer failure/full-verifier rejection.
Case 03's preparation-created unsealed SQLite sidecars were retained separately
and removed from their exact paths; its original seal/bytes verify unchanged.
Use frozen-store immutable reads for historical SQLite, ordinary read-only
access for live accounting authority. See the report for incident evidence.

M0.1d.6's connected development recovery is committed as `f2b8983`.
Private recovery case 02 and its independent audit verify saved own state,
retained-note read/continuation, denied helper history and stale token/epoch,
preserved old costs/action, fresh action, normal termination and recapture.
The 4,370-file seal is
`9f9e32c888a5cb48bd6c15fee65efe22a14c8305e80f58f4ca76a88df01eed2b`.
The failed first recovery's null-sentinel assertion and forced cleanup remain
sealed. See the latest report for all source tests, failures and qualification limits.

Continue the remaining integrated scorer/setup, provenance, isolation and canonical
recovery work. [D13](verification/2026-09-21-d13-shutdown.md) explicitly changes new
Forge grants to a 1,000-ms tree-proof policy; its authentic normal-stop sample
passes at 568.994 ms and protected custody closes normally. The original
[resource/file](verification/2026-09-21-authentic-resources-and-files.md) and
[CPU-profile](verification/2026-09-21-bundle-preparation.md) failures remain intact.
Do not repeat the unchanged successful craft or resume 500-ms optimization.
Full authentic fault/launch containment and general isolation remain open.
The original vanilla PackLock is now SEALED with actual materialization/import evidence; canonical save/custody/
clock/checkpoint qualification remains open despite the successful bounded
native/world continuation. Original accounting and consumed D12 remain
unchanged; no permission question or missing user input is pending.

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
