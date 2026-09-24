# Accepted and refused action evidence

M0.2c.1d.2; F06/F09/F11/F13/F16, N01/N02/N03/N05/N06/N08,
partial T03/T07/T12/T13 and G0 items4/6. D14 and M1–M7 remain unchanged.

The Mineflayer capability manifest advances to minor12 with
`atomic-acceptance-sequence-refusal/1`. An out-of-order action now commits a
private `ActionSequenceRefusal/1` record before returning `OUT_OF_ORDER`.
It binds the batch digest, scope, expected action sequence, current acknowledgment
and primitive counters, and time. It accepts no intent, spends no primitive and
allocates no acknowledgment. Failed storage returns an error, without claiming
a proved refusal. Other ambiguous errors retain their existing treatment.

The independent worker consumer can explicitly admit this policy. It matches
each refused RPC to exactly one private record, checks its position relative to
observations/accepted intents/acknowledgments/charges, and retains read-only
`ACTION_UNKNOWN` queries separately. It still rejects unproved refusals,
unknown errors, missing terminal receipts, ambiguous effects and counter gaps.
The default successful-action consumer remains strict. No historical refusal
record is synthesized for live17.

`python -m strata_evaluator.native_game_measurements --bundle PRIVATE_BUNDLE
--seal SHA256 --output PRIVATE_REPORT` joins this action evidence to normal
native closure, stopped own-player state, held worker and official pack locks,
source bytes, actual root/helper receipts and measured intervals. It preserves
the recorded gameplay result and makes no automatic G0/scientific pass.

The instrumented pilot producer now archives its declared Python/compiled-worker
sources, dependency lock and public schemas before launch, under 8-MiB per-file
and 32-MiB total limits. Hash drift, unsafe paths and overwrites refuse admission.
Worker bytes come from the held runtime, not an unrelated checkout. Credentials
are outside the source inventory. The consumer reads the sole player directly
from the verified stopped snapshot rather than requiring an absent duplicate.

At the source checkpoint, 191 distinct focused Python checks pass in31.83s;
TypeScript build and38 Node action tests pass in5.752s; full Ruff passes. The
earlier187-case run also passed before the four source-archive tests were added.
Read-only live17 component checks pass native stop and pack binding; source and
saved-player checks initially reject missing legacy archive paths. Those
refusals are retained as diagnostics, not relabeled archive corruption or passes.

Authentic qualification of the changed runtime remains pending. The old
live17 archive, failed gameplay goal, receipt gap and all unresolved reservations
remain unchanged. Exposure at this checkpoint is$4.878100/$10; no new model run
has yet occurred. Next prepare a fresh held runtime/profile and current native
preflight, then exercise the connected profile under continuing D18/D19 authority.

## Prepared worker and identity correction

The new held worker imports in2.672s with all three owned processes terminal:
11,724files/654,086,943bytes, manifest
`146c1a067bc2535c135432a9e79f4a21923a90f47c8306b8c797035dfe2cbce6`.
Its archive seal is
`db83bb6b1a07c74664edef858ddd6c9d064160ee4098d9168a7a3eb690ac2d9a`.
Native preflight10 passes27/27 with six synthetic requests and normal finalization
in20.524s; seal
`fe0a7c88879212644514f9ed9af79d19e14babd79d86350f9a5fa276d305c044`.
No inference charge or game run occurs in these preparations.

The successor lock is
`cas:sha256:5487245831247e59eb26d1154d033f29ab296bc59fcb0ac20d98145105394d8d`,
request `vanilla-1192-refusal-20260924`. It reuses the original player-free
baseline and official installation; only objects/outbox/provisioning append,
all prior rows and37 other authority tables remain unchanged. It does not
declare the changed runtime's game behavior qualified.

Preparation review found that the copied retention capability reference still
declared an older worker path/hash/import capability. Actual runtime evidence
was retained separately, but that stale declaration cannot certify the intended
system identity. The instrumented driver now checks declared runtime and entry
bytes before launch, then checks the actual observation capability digest before
model dispatch. The offline joined reader performs the same checks. Six focused
binding cases pass (0.38s), and the report CLI's evidence-overwrite denial passes
(0.46s). One current Forge/JVM at-most-once fixture passes (1.981s, synthetic game
effects). These bring distinct focused source coverage to198 Python/39 Node
cases; earlier cases were not rerun unnecessarily. Native preflight11 is required
for this changed Python source; the already prepared Node bundle remains valid.

The corrected stopped-player reader independently matches live17's orientation,
position, dimension, health, food and inventory. This component result does not
retroactively supply its missing refusal/source records or correct its old
declared worker identity. Its original archive and failures remain unchanged.

## Authentic refusal and corrected action

Native preflight11 passes27/27 with six synthetic requests in19.831s, normal
finalization and seal
`e800eba61f2747e672a93fae14f0cef56dd3c32e3d260518ef05562c714b9a0a`.
Corrected pilot18 preparation retains the selected worker identity and seals at
`dba40b23a3b522e7e0311947f4af1a2f0bcd6c3b5a86b56a74938a42453860de`.
No prior played instance or request is replayed.

D19.11 / `validation-2026-09-18:m0-pilot-18` then exercises actual GPT-6 Luna
through the persistent Mineflayer worker. Its first turn uses action sequence4
where1 is expected. The worker commits one exact private refusal, dispatches no
input and consumes no receipt sequence. The model refreshes its observation and
submits sequence1. That turn completes with acknowledgment sequences1/2/3 and
one primitive. Independent public-state comparison measures101.25degrees with
0.001046radian target error; the stopped player matches position, orientation,
dimension, health, food and inventory. No walk occurs: the two permitted action
submissions were both turns. The original two-action goal remains failed, with
9/14 native checks passing and its original strict worker join false. The strict
goal checker stops at the first rejected action; its false turn flag does not
erase the separately verified corrected turn.

All11 model requests settle: ten root requests cost$0.009194 and one delivered
helper reply costs$0.000502, total$0.009696 API-equivalent. There is no actual
invoice-dollar claim. Both envelopes close, the native job finalizes with exit0,
and all54 outer-owned processes exit normally. Outer elapsed time is295.218s;
the independent timing partition is255.344s, including200.750s for the native
harness and thinking. The server records4,137 completed ticks and4,018 avatar
callbacks. Nested intervals are retained separately, never added as wall time.

The complete archive has4,218files/221,615,927bytes, including the declared
source bytes and complete current-job broker workspace references, seal
`da5aa94c08d57e57abbfca50aefd3f8742cd9f573ae2ebdb6a595b6ed398f125`.
The reusable `native_game_measurements` CLI independently reconstructs the
accepted/refused calls, source/worker/schema/dependency/pack bindings, stopped
player, root/helper costs, tool durations and measurements. Its private output
is255,491bytes; content digest
`59fc7dfa72e90b87e58e52307d26899c6733587100fe975a3910d904ca2a4d74`.
The independent audit passes19/19 and seals its report/source at
`33ed135c98caed1a91a1c0346fedc1f900f22023ae8075b231d0fa78349d64f5`.
All eight game-request preimages reconcile; the one rejected mutation has zero
primitives, and the one accepted action has complete contiguous receipts.

The joined reader now treats absent forced-cleanup flags as the producer's
normal representation; explicit true, null or numeric flags still reject.
Independent owned-process and stop proofs remain mandatory. Three focused
regressions pass in1.85s; cumulative distinct source coverage for this increment
is201 Python/39 Node cases. Full Ruff and `git diff --check` pass. This is an
evidence representation fix, not a relaxed stop policy.

Every prior accounting row checked by the execution conservation audit remains
unchanged, as do D12 and the original allowance. Exposure is now$4.887796/$10,
including the old$0.7554 hold and four full$1 failed-job envelopes. D19.11 is
consumed; D18/D19 continuing authorization remains valid. No uncertainty is
refunded, replayed or retroactively reclassified.

M0.2c.1d.2 is verified for this named accepted/refused-action and cost-evidence
scope. The run does not qualify successful turn/walk play, campaign active
clocks, telemetry overhead, complete checkpoint recovery, isolation or general
game conformance. Earlier successful live15 gameplay and historical cancellation
trajectories retain their original identities. Next assemble the exact six G0
profiles and disposition of remaining children, especially cancellation lineage
for this changed worker; do not rerun the paid trial to seek a successful goal.
M0 remains in_progress and G0 fail until that assembly is complete. D14 and
the entire M1–M7 roadmap remain unchanged.
