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
