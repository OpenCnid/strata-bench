# Durable inference reservation checkpoint

Operator-only. M0.1c.1a is **implemented_unverified** for production.
F03/F11/F16, N01/N03/N04/N06, C06/C20, partial T01/T04/T07/T12, G0/G1.
SPEC v0.2.33 and D04's model, authentication mode and $10 ceiling are unchanged.

## Delivered behavior

[InferenceDispatches](../../src/mcbench/inference_dispatch.py) is an internal
operator accounting boundary, not an HTTP proxy or a provider price estimator.
It requires private, scoped evidence of a finite reservation and USD semantics
before dispatch. A trusted qualified adapter must supply that evidence; the
module does not establish those claims itself. No live qualification was issued.

Under `reserve-intent-before-distinct-dispatch/1`, the budget reservation,
dispatch intent and journal events commit in one SQLite transaction. Only the
first caller may forward after commit. Each actual retry has a separate operation
and charge even if its request body is identical. Repeated attempt IDs never
resend, and conflicting attempts or receipts reject.

Authoritative scoped receipts settle usage once, with provider-event reuse
rejected. Actual overruns remain recorded. Transport failures, invalid receipts
and recovered pending attempts retain the full reservation and block further
dispatch through the ancestor budget. Recovery requires the supervisor to fence
old transports first; it never replays them. Simulation profiles cannot be
promoted or mixed with live native stores in either constructor order.

[Budgets.post_in_transaction](../../src/mcbench/budgets.py) permits composing a
posting with its durable intent only on the store's own active transaction.
[NativeExec](../../src/mcbench/native.py) checks the shared simulation mode.
The new internal evidence records do not replace the 13 canonical contract types
or introduce a gameplay tool.

## Verification

The complete checkpoint Python suite passed **738 tests**, no skips, in 113.77 s,
with both JVM fixture opt-ins enabled. The two warnings are Typer/Click API
deprecations. Ruff passed across `src`, `evaluator/src`, `tests` and `tools`.

[Synthetic dispatch tests](../../tests/test_inference_dispatch.py) cover durable
reservation visibility before forwarding; duplicate calls and receipts; distinct
same-body retries; parent-cap concurrency; invalid/expired/mismatched bounds;
uncertain transport and late reconciliation; process-state-loss recovery without
replay; rollback on intent-write failure; invalid settlement scope; event reuse;
retained overruns; transaction ownership; and native/dispatch simulation mismatch.
The full suite also exercises existing budget, native host and controller cases.
Prices, proofs, callbacks and receipts in these tests are synthetic.

Private logs are under the operator's external
`2026-09-19-merge-checkpoint-01` evidence directory. Raw evidence is not published.
See the [checkpoint review](../STATUS_AND_HANDOFF.md) for the other language
suites, publication audit and exact test environment.

## Open integration

The native runner still reserves whole jobs. The new per-call module has no
production caller; integrating both must avoid duplicate charges or releasing
unresolved root holds. A transport adapter must intercept every request, retry,
compaction and helper dispatch, enforce bounded transport behavior, and deliver
authoritative usage. The callback must never retry internally. End-to-end
interruption, credentials, egress and provider isolation remain unqualified.

The prior [native budget investigation](2026-09-19-native-budget.md) found no
proven turn-level output/money bound or actual OAuth credit-to-USD conversion.
Private trusted evidence flags alone cannot resolve that gap. Start with local
synthetic transport integration; do not dispatch paid calls until real exposure,
pricing and isolation are qualified. All aggregate gates remain open.
