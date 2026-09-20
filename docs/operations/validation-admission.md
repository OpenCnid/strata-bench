# Initial validation: budget and native boundary

September 20, 2026. Operator-only. This is the continuation contract for
M0.1c.1c.2 and M0.1c.2b.2, not an executable authorization or qualification.
Authority: SPEC sections 4.1, 6, 15–16; decisions D04/D11 in MILESTONES.md.
Coverage: F03/F04/F07/F11/F16, N01/N02/N04/N06, C06/C12/C20,
partial T01/T04/T06/T07/T12 and G0 items 1/6. All remaining gates stay open.

## Settled user inputs

- Use Codex ChatGPT OAuth and `gpt-5.6-luna`.
- The original $10 total means a rough model-price estimate of experimental
  subscription usage, including helpers, retries and summaries. It is neither
  an additional $10 nor an actual OAuth invoice/exact subscription-quota value.
- The user confirms no outside Strata model experiments. Inspected experiment
  stores used synthetic providers; this establishes zero opening experimental
  usage, not zero subscription use by the coding assistant.
- Recommend a first trial allocation of at most $1 estimated usage within that
  $10 total, then measure tokens/cost per useful action. This is a staged plan,
  not a promise that $10 funds all later soaks or the confirmatory study.
- No user-supplied VM is required. Engineer the smallest enforceable boundary
  on available hardware; keep the user's ordinary desktop usable.

## Versioned estimated accounting: implemented source foundation

The [authorization](../../src/mcbench/authorization.py), [estimate basis](../../src/mcbench/accounting.py)
and [configuration](../../configs/operator/live-validation.json) now implement
`ExecutionAuthorization/2` with explicit migration. The existing dispatch gate,
wire transport and native supervisor now enforce versioned estimate bounds and
valuations. [D11 verification](../verification/2026-09-20-estimated-accounting.md)
records the actual private migration and focused source/synthetic evidence.
The original authority resides in `.strata/operator/provisioning/controller.sqlite`;
read it before dispatch and do not install another allowance. Actual OAuth ingress,
finite exposure enforcement and isolation still need qualification.

The implemented source contract requires an explicit versioned accounting basis that distinguishes actual
charges, API-equivalent estimates and synthetic fixture units. Pin model, price
source/date, currency, service tier and applicable context/cache rules. Preserve
the original authorization lineage and all existing settled usage and unresolved
holds through any migration; reject incompatible or incomplete migration.
Recheck the original project ledger before any future dispatch. Do not turn
this documented opening baseline into a reset during a later session.

Exit evidence for this source deliverable:

1. Deterministic estimates distinguish ordinary/cached input, output and any
   applicable cache-write, long-context or tier rates; unknown categories fail
   closed or retain a conservatively justified bound.
2. Root/helper/retry/summary requests consume one aggregate allowance. Whole-job
   envelopes and per-call reservations do not double count; distinct requests
   still charge separately and duplicate receipts settle once.
3. Missing usage, interrupted streams, ambiguous forwarding and restart retain
   reservations and never cause blind replay or a budget refund. Legacy
   migration cannot increase available budget or convert a simulation into live.
4. A finite bound is established before dispatch and admission stops before the
   aggregate estimate can exceed the allowance. A timer/kill signal alone is
   not proof that an already accepted provider request has stopped consuming.
5. Focused synthetic tests and the affected pinned-CLI fixture establish only
   their stated scope. Actual OAuth all-request ingress and the native
   root/helper boundary require separate real evidence before a live trial.

Published standard short-context Luna rates inspected September 20 were
$0.20/M input, $0.02/M cached input and $1.20/M output. These are now pinned in the runtime estimate record; that installation is not
OAuth ingress or boundary qualification.
Separate cache-write, long-context and service-tier rules apply. Revalidate
the chosen schedule when implementing it: [model documentation](https://developers.openai.com/api/docs/models/gpt-5.6-luna),
[API pricing](https://developers.openai.com/api/docs/pricing),
[subscription credit semantics](https://learn.chatgpt.com/docs/pricing).

## Next deliverable: enforce the minimum native boundary

The gameplay agent needs its scoped game CLI, its own notes/learned skills and
the allowed corpus. It must not read evaluator criteria/holdouts, raw server
files or unopened inventories, use admin controls, reach account secrets, or
read sibling/probe state. This is necessary to interpret benchmark results.
Qualify the actual pinned native Codex tools and helpers, not just a mock caller.

Inspect host-supported tool restriction and a protected broker/service identity
first. SPEC permits these choices with explicit capability identity/conformance;
a VM is an alternative implementation, not an input the user must supply.
Retain Dovetail's required native loop and skill/helper behavior. An unavailable
enforcement capability becomes a specific compatibility gap with a resolving
action, not a reason to stop unrelated source work.

The [restricted native broker candidate](../verification/2026-09-20-restricted-native-tools.md)
now implements explicit per-caller artifact projections, helper result writes,
executor-only fixed-worker forwarding and durable no-replay. Native root/helper
metadata and actual local synthetic-worker positive/negative cases were exercised.
This activates the optional MCP facade for a demonstrated enforcement need;
the native loop/plugin and game contracts are preserved. It remains unqualified
until the remaining protected-bootstrap, live ingress, skill and adversarial
boundary cases pass. [Native participant admission](../verification/2026-09-20-native-admission.md)
now implements stdout-bound root identity, clean child requests, nested budgets
and sealed closure, exercised through actual native CLI/synthetic-provider
fixtures. This does not qualify protected live ingress, credential separation
or complete helper lifecycle/slot reuse.

The [existing canaries](../verification/2026-09-20-native-boundary.md) found
actual unauthorized loopback access even under `CodexSandboxOffline`.
Named policy/firewall labels, packaging, a fresh conversation and separate
desktop placement cannot override that observed failure. Preserve positive
controls (permitted game/workspace access) and negative file/process/network/
tool/helper/immutable-skill controls. Keep canaries synthetic and operator-owned;
never expose real secrets merely to demonstrate a leak.

## Live trial admission

After both deliverables and applicable game/runtime prerequisites are qualified,
prepare one bounded native Dovetail → scoped game action → private evidence join
with a helper case. Record all costs/time, exact source/profile pins and failed
samples. Read the durable allowance first. No additional user permission is
needed for a trial already within the existing authorization, but no amount of
documentation substitutes for actual finite-exposure and isolation evidence.
Do not expand into soaks, team runs or scientific claims before their gates.
