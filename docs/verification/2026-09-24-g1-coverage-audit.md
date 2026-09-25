# M1/G1 opening coverage audit

Operator-only. D20 authorizes M1 implementation and the dependencies necessary
for complete G1, beginning from merged PR #8. It does not extend M0 spending
authority. M0 remains verified and G0 remains a pass only for its named D14
development slice. **M1 in_progress; G1 not_run.** No runtime qualification is
issued by this audit.

## Starting state and evidence rules

`git fetch origin` and `gh pr view 8 --repo OpenCnid/strata-bench` verified
MERGED at `215c4e0d01f0602c91504ad631dc2343ffc9f354`, merged
2026-09-24T23:27:01Z. The checkout was clean and branch
`codex/m1-g1-isolation` starts at that updated main. Frozen offline `uv sync`
installed the locked environment; isolated Python imports resolve to this
checkout. No private installation or evidence directory was modified.

WAL-aware SQLite `mode=ro` transactions match all 40 authority table hashes to
the G0 opening/final checkpoint. Exposure is 4,887,796 microUSD of the original
10,000,000, retaining the 755,400 hold and four full 1,000,000 envelopes without
double charging settled children. Jobs: 15 FINALIZED, 5 UNSETTLED; gateways:
20 CLOSED. Process inventory found no matching Strata-owned Java/native process.
The unresolved jobs remain fenced historical failures. D12 and every used pilot
remain consumed. Private readback is retained in
`C:/Users/Darian/.strata/evidence/2026-09-24-m1-g1-start-01`.

Use the [G0 assembly](2026-09-24-g0-assembly.md) for exact source, worker,
PackLock, capability and seal hashes. Its
[318-child crosswalk](2026-09-24-g0-child-dispositions.md) remains authoritative
history: verified children retain their named scope; residual M1/G1 children
are reopened for implementation under D20, never bulk promoted. Historical
M2/G2 recovery/soak dispositions remain there unless a specific G1 dependency
requires a narrower integration check.

## Exact profiles

| Profile | Existing evidence | G1 disposition |
|---|---|---|
| Native CLI 0.154.0-alpha.6.2, binary `960c111d47afd61669954b9df9e56083e302edbfa3ef6962d81dcc14a30051dc`, exact companion pins; Dovetail `15c306ccfef28eb5f616fadcd5fd8eac0663e361` | Actual tool/skill/helper/cell/lifecycle fixtures and live15/live18; each has its own source/configuration identity | Reuse unchanged evidence only under its original identity. Current selected model remains `gpt-6-luna`; older 5.6 catalog/helper results do not automatically qualify its different helper catalog. |
| Vanilla 1.19.2, Mineflayer 4.39.0, minor12 | Live18 and cancellation PackLock `5487245831247e59eb26d1154d033f29ab296bc59fcb0ac20d98145105394d8d`; held worker `146c1a067bc2535c135432a9e79f4a21923a90f47c8306b8c797035dfe2cbce6`; capability `f85d0a61af5843298e3d4cef001cf93a0bc350a505f08d6467711050d482de0d` | Authentic refusal/corrected turn, cost/clock joins and cancel/reconnect pass their scopes. Full runtime boundary and changed-profile integration remain open. Settings remain unsupported. |
| Exact E9E 1.27.0 with Mineflayer | Actual Forge negotiation/channel refusal | Remains unsupported; no fallback result is assigned to it. |
| E9E 1.27.0 / Forge 43.4.23 separate structured client | Sealed bootstrap PackLock `660dceda185db8f11b0ff5d9bb99b6f4c192f7295ddd5dded9d5d6331b75570a`, launch `023fc52227314bb1cf73b1de354c99816e16c66f7808e888b684eec3bf50d172`; historical recipe/machine profiles are distinct | Required G1 settings/scorer dependencies use their own qualified extension identity. No complete keybinding, protected score or isolation claim. |
| Native settings diagnostic `ctm-startup-bg1-diagnostic/1` | Two authentic crash boundaries and recovery, source-bound Curios apply/rollback and cold readback | Original CTM startup failure remains blocked. Four other crash boundaries, physical intended/competing effects, persistence and host integration remain open. |

## Required suite coverage and next verification

G1 is G0 plus **complete T01/T04/T05/T06/T10/T11**, including the capable
keybinding extension. Every case in SPEC16 remains required. Entries below are
work partitions, not substitute test definitions or fresh passing results.

| Suite / stable owners | Retained behavior | Incomplete contract / required evidence |
|---|---|---|
| T01; M1.2, M1.3, F16/N01/N06 | All 13 strict model examples; public/operator/evaluator schemas; many negative auth/path/epoch/action cases | Complete cross-record fixture references, migrations, Python/TypeScript/conditional Java round trips; explicit N validation and large-N capacity refusal; malformed/unknown discriminants, nullable fields, limits, stale scope, token/audience/deadline and traversal/reparse cases across actual bindings. |
| T04; M1.4, M0.1c/M0.1d residuals, F03/F07/F11 | Pinned Dovetail installation; eight native skill bodies and supporting text; actual root/helper play and accounting; source-bound retirement/drain; learned overlay/fresh-handoff synthetic execution | Exact selected-profile root/helper permissions, full clean self-play, explicit/implicit invocation, events, interruption and fresh handoff/resume, restricted executable skills, complete admitted artifact reset/export and every-call accounting. Image test only if advertised. Complete game/agent recovery/soaks remain G2, while T04's own runtime continuation is G1. |
| T05; M1.1 and all children, F06/N02 | Stock Mineflayer CAPABILITY_MISSING; synthetic conflict/allocation/rollback; authentic discovery and selected native transactions/crashes | Real overlapping conflict repair and intended/competing effects; disjoint-context unchanged; high-key/Unicode and legacy-code rejection; GUI/game/chat modifiers, hold timeout, exhaustion, protected/unknown consumer, revision conflicts, remaining mid-patch crash/rollback cases, repaired-effect restart persistence and cross-client isolation. Qualified commit, worker action fencing, charged RECONFIGURING continuity and public control card/CLI integration remain necessary. |
| T06; M1.3, M1.4, F04/F07/N04 | Scoped CAS/grants/broker; actual restricted shell/patch/resource rejection and root/helper state/cell separation on named historical profiles | Full filesystem/process/network/credential/tool/helper and probe boundary. Test private canaries through every SPEC13.5 route, with positive public access, permitted game/artifact use, correct team communication, cross-team denial and probe disposal. No private bytes in requests, returned logs/errors or campaign artifacts. Same-user arbitrary shell sibling/loopback failures remain failed. |
| T10; M1.5 depends on M3.1/M3.1a/M3.1b and M0.2c residuals, F10 | Connected D14 development craft scorer; authenticated craft-resource witnesses; headless negative and synthetic predicate controls | Reachability for each supported fixture, alternate valid strategies where available, authentic authoritative setup/resource/team/mode provenance, complete idle/fake text/duplicate/gifted/incomplete/unstable/wrong recipe/normal/admin/wrong-team controls; protected scoring, blinded fixture IDs, telemetry overhead and mechanics parity. The old negative has no craft and cannot prove a tainted-craft rejection. |
| T11; M1.6 depends on M1.4 and minimal M3 probe integration, F08/F07 | Artifact filtering, retained-state/activation/frozen-arm synthetic fixtures and private evaluation models | Actual disposable matched clones, complete pre-start manifest diff including bodies/game/keymap/tools/budgets/prompts and allowed artifacts only; t=0 equality/zero designed synthetic gain; denied probe revisions/imports, development-only helpers, exact frozen session/cache resets and one-way canary disposal. No confirmatory experiment or powered effect claim is part of M1. |

Cross-cutting feature rows: C03/C04/C06-C15/C18-C20/C22-C24/C30/C35/C36.
Required supporting contracts in SPEC4-13/15 retain all visibility, clocks,
no-replay, budgets and scientific-comparison constraints. F01/F05/F09 and N02/N03/
N05/N08 are dependencies where these suites exercise game/runtime ownership,
repair continuity, source custody and accounting. F02's contract negatives are
G1; demonstrated N-body capacity remains G3. Full F12-F15 studies/releases and
unrelated M2-M7 implementation are untouched.

## First boundary work

1. Audit the actual selected root/helper native catalog and code execution
   surface. Keep shell/patch, arbitrary resources and inherited user tools
   disabled; test direct dispatch bypass as well as catalog absence.
2. Exercise owned synthetic filesystem, credential/environment, process,
   network and cross-agent targets through the real pinned native runtime.
   Require successful public artifact/game controls, caller-bound outputs,
   no conflicting repeated evidence, and independent target/listener state.
3. Bind evidence to executable/companion/plugin/configuration/source identity.
   Any accessible private channel blocks qualification and receives an enforced
   repair plus a changed-profile test. Tool restrictions and native code-mode
   isolation must be demonstrated; a prompt, folder, desktop or sandbox setting
   is insufficient.
4. Then integrate this boundary with actual game/credential admission, native
   skill/helper lifecycle, settings and the minimal scorer/probe dependencies.
   Scripted provider evidence is runtime conformance, never model-selected play.

Current independent work is authorized: code, source/contract tests and bounded
credential-free native fixtures. D18/D19 remain M0-only spending authority.
Prepare a concrete bounded M1 authentic-model procedure before requesting its
missing spending authorization. No broad rerun of unchanged M0 matrices, old
one-use script replay, shared-desktop input or new allowance is selected here.


## Campaign-team communication dependency clarified

M1.3b.8 exercises separate native job/helper communication and control attempts.
It cannot substitute for SPEC10.2 team.send/team.receive. The controller
Communication service exists, but the current restricted broker exposes only
artifact/game operations. M1.3b.9 now tracks the minimal M4.1 dependency required
by complete T01/T06/G1: typed scoped native team operations, declared policy,
permitted roster delivery, cross-campaign refusal, cursors/deadlines/limits and
durable receipts. This does not start N-body capacity qualification or unrelated
M4 work; the original gate still requires correct team communication.
