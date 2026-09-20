# Operator core

These modules and commands are operator-only. Store data outside this repository
and outside every gameplay workspace. Python service authorization assumes a
trusted caller has authenticated the principal; it does not create an OS sandbox.

For current D04/D11 interpretation and the first outstanding native accounting
deliverable, read [validation admission](validation-admission.md). The checked-in
`ExecutionAuthorization/1` remains a legacy hard-dollar policy; documentation
clarification has not migrated its schema, stores or production admission checks.

The controller persists state and reservations; it does not launch a Minecraft
server or a Codex job. `DRAFT`, `STARTING`, and a synthetic test's `RUNNING` state
are not evidence of authentic game operation. Simulation stores are permanently
identified as simulations and cannot become live stores.

```powershell
uv run --frozen mcbench campaign validate --config C:/private/config.json --agents C:/private/agents.json
uv run --frozen mcbench campaign create --config C:/private/config.json --agents C:/private/agents.json --store C:/private/strata
uv run --frozen mcbench campaign status c1 --store C:/private/strata
uv run --frozen mcbench campaign preflight --config C:/private/config.json --agents C:/private/agents.json --store C:/private/strata
uv run --frozen mcbench journal export --store C:/private/strata --destination C:/private/audit.jsonl
```

Preflight exit 2 means prerequisites remain blocked. Never fabricate readiness,
capacity, clean-stop, isolation or usage receipts to pass it. The API's trusted
supervisor integration must resolve actual evidence from the protected CAS.
Reservation expiry requires cleanup before capacity or accounts can be released.

The evaluator is a separate package under `evaluator/`. Install it only in an
operator/evaluator environment after the root package is available. Its
`strata-evaluate --plan ... --results ... --output ...` command consumes private
registered assignments and canonical EvaluationResult JSONL. An optional
`--publication-output` writes an explicit summary projection with no private IDs.
It is an offline analysis command, not a probe launcher or scientific certification.

Budgets must reserve worst-case exposure before dispatch. Settlement retains actual
overruns and unknown prices. Active campaign clocks come from measured intervals;
model-call wall latency must not be summed as campaign active wall time. No code
path restores the ledger when materializing an earlier game checkpoint.

Native `per_dispatch` jobs explicitly reserve nested envelopes; individual
requests and helpers consume the reserved capacity without duplicating charges.
Ordinary parent-linked operations remain additive. An open envelope keeps its
full bound (or an observed overrun), and unknown requests block its ancestors.
Only fenced native processes/ingress, an exact sealed request inventory and
settled descendants permit atomic envelope closure/native finalization.
See the [native accounting verification](../verification/2026-09-20-native-dispatch.md)
for runnable credential-free fixtures and the unresolved production gates.
The synthetic HTTP adapter rejects live stores and non-loopback endpoints.

The sanitized gameplay keybinding skill is under `gameplay/skills/`. Package it
with an isolated gameplay runtime only after loading and tool conformance are
qualified. The current Mineflayer worker advertises settings unsupported.
