# Native OAuth budget surface inspection

Operator-only. M0.1c.1 in_progress; F03/F11/F16, N01/N03/N04/N06,
C06/C20, partial T04/T12, G0/G1. Read-only inspection does not qualify dispatch.
D04 remains ChatGPT OAuth, gpt-5.6-luna and $10 aggregate inference; no model,
authentication mode, budget or acceptance threshold changed.

The installed `codex-cli 0.154.0-alpha.6.2` matches the repository candidate.
Its executable SHA-256 is
`960c111d47afd61669954b9df9e56083e302edbfa3ef6962d81dcc14a30051dc`.
Executed `codex --version`, `codex exec --help`, and
`codex app-server generate-json-schema --experimental --out <private>/schema`.
The generated protocol was parsed, selected definitions retained, and every
generated JSON file hashed. Those inspection commands started no app-server
session or model turn; the separate local transport cases are described below.

## Findings and limits

- `TurnStartParams` has neither `maxOutputTokens`/`max_output_tokens` nor an
  explicit per-turn monetary cap. This is a finding about this generated
  protocol, not proof that every possible provider control is unavailable.
- `ThreadGoalSetParams.tokenBudget` exists separately. Its schema does not
  establish a provider-enforced completion limit, descendant charging, or an
  upper bound on already-dispatched requests. Do not use it as a dollar proof.
- `TokenUsageBreakdown` distinguishes input, cached input, cache-write input,
  output, reasoning output and total tokens. Its definition supplies no USD
  amount or unique identity for every billable request/retry.
- `RateLimitSnapshot` includes optional credit and individual-limit data.
  `SpendControlLimitSnapshot` has string limit/used values and reset/remaining
  fields. Schema presence does not prove this account has that control or that
  it isolates Strata's spending from other activity.

The current [official pricing page](https://learn.chatgpt.com/docs/pricing)
lists Luna at 5 input / 0.5 cached-input / 30 output credits per million tokens.
It states that credit purchase prices depend on the plan or agreement and that
active turns can continue after a usage limit is reached. Consequently, neither
the rate table nor an account quota percentage establishes D04's hard USD bound.
API-key prices are not silently substituted for OAuth credit pricing.

The [app-server documentation](https://learn.chatgpt.com/docs/app-server)
describes account-wide quota/activity reads and thread token updates. Those
observations alone do not demonstrate a pre-dispatch reservation boundary for
each root/helper/retry/compaction call. The
[configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference)
documents context-window/compaction settings and HTTP/stream retry controls;
the inspected page contains no `model_max_output_tokens` setting. Context size
and local process timeout must not be presented as enforced provider output
limits. Documentation and schemas are surface evidence, not live conformance.

## Actual native requests to a synthetic local provider

Ran the pinned CLI twice with fresh protected credential-free home/workspace/
temporary directories, explicit environment, ignored user configuration/rules,
an ephemeral read-only session, and a loopback-only synthetic provider URL. The
fixture always rejects requests and never produces model output. Each owned
process tree has a 25-second cutoff and bounded private logs; no external model,
account credential, gameplay grant or Dovetail invocation is involved.

Both transport cases pass: HTTP 400 with request retries disabled produces one
POST; HTTP 503 with one allowed retry produces two POSTs. Both processes exit 1
as expected without timeout. Requests reach `/v1/responses`, name gpt-5.6-luna,
enable streaming, contain no Authorization header, and omit `max_output_tokens`.
The retry repeats the same body digest but is a distinct dispatch. Therefore a
body digest cannot be the sole identity for billable-call deduplication.
Request bodies are 35,266 bytes; only field names, sizes/digests and selected
nonsecret values are retained by the fixture. This supports these local
transport/retry cases only, not OAuth routing, successful streaming, helpers,
compaction, isolation or complete metering. No billable call occurred.

## Next resolving work

The later [dispatch checkpoint](2026-09-19-inference-dispatch.md) implements the
durable reservation boundary with synthetic accounting tests; it is not yet
connected to this transport fixture. Extend the local provider checks to
streaming interruption, successful turns, compaction and descendants, and connect
each distinct upstream dispatch to that boundary. Then establish
the actual OAuth monetary conversion and a finite provider exposure bound,
including unresolved calls, before authentic host conformance. A native proxy
configuration is documented in
[authentication](https://learn.chatgpt.com/docs/auth), but compatibility and
credential/process/network isolation still require their own tests. No proxy or
spending control was installed by this inspection.

[NativeExec](../../src/mcbench/native.py) continues requiring
`all_call_budget_gateway`, verified pricing semantics and finite dispatch bounds.
[ExecUsageReader](../../src/mcbench/runtime.py) continues reporting turn totals
with unknown model-call count and USD cost. No qualification receipt was issued.
All-call accounting, the host/plugin/helper suite and all aggregate gates remain
open. No credentials were read/copied; $0 Strata inference was dispatched.

Private generated schemas, inspection script/result, hashes and generation log:
`C:\Users\Darian\.strata\evidence\2026-09-19-native-budget-01`.
