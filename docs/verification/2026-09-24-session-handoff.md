# September 24 M0 checkpoint and fresh-session handoff

Operator-only. The user requested a documentation refresh, PR and merge to main,
then a fresh session. This checkpoint records implementation through `b31d184`
and its documentation follow-up. It does not close M0/G0 or authorize more work
during this stopping task. **M0: in_progress; G0: fail; G1–G5: not_run.**

## What the next session is building

Strata is an LLM gameplay harness. Pinned native Codex/Dovetail gives the model
filtered public observations and typed game commands. GPT-6 Luna chooses goals,
targets and actions; a persistent Mineflayer worker executes bounded motors and
returns receipts. A helper can review permitted evidence. Fixture preparation,
local motor execution and independent checking are scripts; the actual pilot's
gameplay decisions are made by the model. Scripted-provider integration remains
separately labeled. Exact E9E uses a separately identified Forge development
fallback; Mineflayer's exact-pack incompatibility remains recorded.

## Latest stopped result

D19.11 / `validation-2026-09-18:m0-pilot-18` is consumed and FINALIZED. All eleven
model requests settled: ten root calls cost $0.009194 and one delivered helper
reply costs $0.000502, totaling **$0.009696 API-equivalent**. There was no model
transport failure in this trial.

The model first submitted action sequence 4 where 1 was expected. Minor12's
`atomic-acceptance-sequence-refusal/1` journal proves rejection before input or
receipt allocation. The model then submitted sequence 1, completed a 101.25-degree
turn and obtained contiguous acknowledgments 1/2/3. No walk occurred. The original
two-action goal stays failed (9/14 checks), with its strict join false. The new
independent reconstruction verifies the refusal and corrected action without
rewriting those original outcomes.

The combined audit passes19/19: exact request preimages, declared/actual worker
identity, source/schema/dependency/pack locks, stopped player, model/helper/tool
costs, worker measurements and actual server/avatar ticks. All 54 owned processes
exit normally, none forced. There are 4,137 completed server ticks and 4,018 avatar
callbacks. Outer elapsed time is 295.218s; the monotonic wrapper partition is
255.344s, including 200.750s for the native harness and thinking. These intervals
overlap and must not be added. [Complete result and limits](2026-09-24-action-refusal-evidence.md).

Earlier live15/D19.8 independently passed actual model-selected turn/walk/helper
play (14/14); live16b and live17 retain their distinct failures and instrumentation
limits. Do not demand another lucky paid run to erase a recorded gameplay failure.

## Six-outcome closure work

| G0 outcome | Retained evidence | Next disposition |
|---|---|---|
| 1: native host/action/helper | Live15 actual turn/walk/helper, receipts and saved player; live18 helper delivery/costs | Passed for named D14 development scope; preserve full isolation under M1/G1 |
| 2: authentic installations | Official vanilla/E9E locks, thirteen E9E checks and sealed Forge bootstrap 34/34; exact Mineflayer/Forge incompatibility | Passed for named profiles; keep fallback identity separate |
| 3: ordinary/modded mechanics | Vanilla navigation/mining/inventory/crafting/container; Forge modded block, expert furnace recipe and real machine | Bind each selected result to its exact qualified profile in the final assembly |
| 4: cancel/reconnect | Retained vanilla/Forge cancellation and reconnect journals; D13 normal stop; prior lineage audit 30 checks / 20 artifacts | Resolve the changed minor 12 worker's cancellation lineage explicitly; never upgrade historical 500-ms failures |
| 5: private milestone | Connected positive craft 26/26 and headless negative 49/49 in the private development scorer | Named D14 scope only; negative contains no craft, not a valid-craft causal test; isolation/scientific authority unqualified |
| 6: costs/time/evidence | Live18 complete accepted/refused-action/source/lock/saved-player/cost/clock join19/19 | Assemble alongside the other exact profiles; full campaign active clocks, capacity and checkpoint qualification remain separate |

First do the read-only profile/coverage assembly. The ledger contains 369 stable
milestone IDs and 51 unchanged M1–M7 rows. Many M0-prefixed children retain broader
contract gaps. Give each applicable remaining gap an explicit disposition before
closing its parent; do not bulk mark children verified. Full T05 and D14 isolation
belong to G1, and complete canonical recovery/soaks to G2. Preserve those contracts
and IDs without implementing unrelated later work. A new test or source change
must resolve a named missing G0 outcome, not create another generic layer.

## Durable authority and private inputs

Read `C:/Users/Darian/.strata/operator/provisioning/controller.sqlite` with
WAL-aware read-only access. A checkpoint read verified all 40 tables unchanged
since live18 and **$4.887796 exposure of the original $10**. This includes the
old $0.7554 unknown hold and four full $1 failed-job envelopes. Settled children
inside held envelopes are not charged twice. D12 remains consumed with its
offline receipt settlement; retained legacy reservation state is not permission
to replay it. D19.11 and every previous used pilot stay terminal/consumed.

D14 defers full isolation qualification to M1/G1. D17 selects `gpt-6-luna`.
D18 authorizes necessary bounded M0 runs within the original allowance; D19
permits fresh sequential jobs with every unresolved amount reserved and earlier
jobs terminal/fenced. No per-run reapproval is needed within that scope. A new
unknown stops its own job. Never refund, blindly replay, rearm a used decision,
claim an exact OAuth bill, or expand the allowance. Shared-desktop input remains
paused. D05 sign-in/entitlement/EULA authorization persists.

Private evidence roots are under `C:/Users/Darian/.strata/evidence/`:

| Artifact directory | Seal SHA-256 |
|---|---|
| `2026-09-24-m0-refusal-live-18` | `da5aa94c08d57e57abbfca50aefd3f8742cd9f573ae2ebdb6a595b6ed398f125` |
| `2026-09-24-reconciled-pilot-18-01` | `33ed135c98caed1a91a1c0346fedc1f900f22023ae8075b231d0fa78349d64f5` |
| `2026-09-24-refusal-worker-runtime-01` | `db83bb6b1a07c74664edef858ddd6c9d064160ee4098d9168a7a3eb690ac2d9a` |
| `2026-09-24-refusal-profile-01` | `6e9f368181c051304291175417e5cbcc91044f076b7c5520a34168d1e354ed6c` |
| `2026-09-24-helper-native-11` | `e800eba61f2747e672a93fae14f0cef56dd3c32e3d260518ef05562c714b9a0a` |
| `2026-09-24-refusal-pilot-preparation-01` | `dba40b23a3b522e7e0311947f4af1a2f0bcd6c3b5a86b56a74938a42453860de` |
| `2026-09-24-g0-lineage-audit-02` | `74e744ac23adcdb222e32f778234250e0b611e48e82b59dd84da0822d18c89f3` |

The selected worker manifest is
`C:/Users/Darian/.strata/runtime/vanilla1192-refusal-worker-01/runtime.manifest.json`,
SHA `146c1a067bc2535c135432a9e79f4a21923a90f47c8306b8c797035dfe2cbce6`.
Its observed capability digest is
`f85d0a61af5843298e3d4cef001cf93a0bc350a505f08d6467711050d482de0d`.
Successor PackLock is
`cas:sha256:5487245831247e59eb26d1154d033f29ab296bc59fcb0ac20d98145105394d8d`,
request `vanilla-1192-refusal-20260924`. It uses the original player-free baseline
and corrected clock JAR66f4b618. The m0-pilot-18 instance is now used; preparation,
publication, execution, audit and archive scripts are one-use history, not resume
commands. Do not modify sealed evidence or rebuild unchanged installations.

The prior [normal/recovery checkpoint](2026-09-22-session-handoff.md),
[successful root/helper pilot](2026-09-24-native-wire-report-bounds.md),
[private milestone](2026-09-24-development-milestone.md),
[sealed E9E bootstrap](2026-09-24-sealed-forge-bootstrap.md) and
[lineage/cost audit](2026-09-24-pilot-outcomes.md) retain earlier exact pins.

## Verification and merge checkpoint

Source through `b31d184` has the focused verification recorded in the linked
reports, including201 distinct Python/39 Node cases for the refusal increment,
native preflight11 27/27 and authentic audit 19/19. Those scopes are not a claim
that the entire repository or all game gates passed.

The stopping task performed the following local checks. No Minecraft or paid
inference run occurred. Full-run failures remain recorded; focused corrections
are not relabeled as a new clean full-suite run.

| Check | Actual result |
|---|---|
| Full Python after the companion fixture correction | 3,529 passed,174 skipped,two failed in1,163.75s; existing two warnings |
| Final focused companion/gateway/process-lock suites | 68 passed in13.03s after correcting all three stale fixture assumptions |
| Node build/default suite | 159 passed,43 opt-in JVM cases skipped,zero failures;6.003s test time |
| Enabled Node/JVM scope | First pass47/56; nine guard failures used the older worktree's isolated Python import. All12 guard lifecycle/fault cases then pass in64.130s using the current environment; the remaining grant-denial case passes in3.950s. All202 distinct Node cases have passing coverage across these runs, not a single clean enabled-suite claim |
| Java client/telemetry | Offline Gradle BUILD SUCCESSFUL in37s; client469 passes, telemetry40 passes in its up-to-date task; no failures/errors/skips |
| Ruff and whitespace | `ruff check .` and `git diff --check` pass |
| Documentation and coverage | Local Markdown links/fences checked;369 milestone IDs,51 M1–M7 rows,13 JSON examples, SPEC sections3–19 and append-only progress history preserved |
| Publication and authority | No credential patterns/private runtime artifacts found; the existing Gradle wrapper is the sole tracked JAR. All40 original authority tables match stopped live18; no added experimental spend |

The initial Python run stopped at three companion-fixture failures after947
passes/17 skips in197.30s. Its mock lacked the source-manifest file entry and
plan schema now required by the reader. The corrected companion suite passed20/20
and also passed in the subsequent full run. That full run's gateway failure was
the old expectation of HTTP200 before usage settlement; the existing producer
correctly returned403 and retained the unknown hold. Its process-lock crash
fixture killed a Windows virtualenv redirector instead of the interpreter holding
the lock. The corrected fixture launches the base interpreter with explicit test
import paths and proves its PID is the lock owner before kill/wait. No production
locking, receipt, shutdown threshold or gameplay behavior changed.

The Node guard failures independently exposed an environment mismatch: `-I`
ignored `PYTHONPATH` and loaded the older978a checkout's editable installation.
`uv sync --frozen --offline` prepared this checkout's existing environment; its
isolated import was checked before rerunning only the affected guard scope.
Python's174 skips remain unrun optional integration cases in this merge check;
they do not become game or isolation passes. Local logs/procedures are retained
under `C:/Users/Darian/.strata/evidence/2026-09-24-session-checkpoint-01`.

[PR #7 — Checkpoint M0 LLM gameplay and September 24 handoff](https://github.com/OpenCnid/strata-bench/pull/7)
includes the60 accumulated implementation commits after main's earlier `f3b009e`
checkpoint, documentation/test-fixture commit `5ec6749` and this PR-binding
follow-up. GitHub reported MERGEABLE/CLEAN with no hosted status checks at PR
creation. The requested merge preserves commit history. The PR's merged state
and fetched origin/main ancestry are the authoritative merge receipt; verify
that main contains both `b31d184` and `5ec6749` on resume. These local checks do
not become hosted CI or G0 passes.

On the next implementation request, fetch origin/main, verify the merged PR and
actual private authority/process state, then start a fresh branch from updated
main while preserving any user changes. Resume the exact-profile G0 audit above.
Do not restart M0.1d.1, normal-stop case 04, successful helper play, installation
selection, isolation-first work, or a design/SPEC rewrite. A merge is a source
checkpoint, not a release-gate pass.
