# M0 development piloting trial

**D15 consumed (2026-09-23):** the approved native LLM/Mineflayer pilot completed six settled model requests costing $0.006422, but failed before any game request was forwarded. The model guessed malformed request envelopes; native exit was 1 after the six-request cap. All 53 owned processes are terminal, old accounting rows and D12 are unchanged, and combined original exposure is $0.763280. The public-contract documentation/error-feedback correction passes 102 focused checks but has not had a new native or live-model trial. Preserve the failed used instance and sealed evidence; no automatic replay. See [D15 evidence](../verification/2026-09-23-d15-pilot.md).


Updated September 23, 2026. Operator-only. Implements D14; the approved D15 execution is consumed and failed. This document does not authorize a
new request or reuse D12.

The path is **pinned native Codex/Dovetail → scoped game broker → existing
Mineflayer worker → authentic vanilla Minecraft**. The model chooses its own
targets from filtered observations. No desktop input or replacement backend.

The ordinary goal is to inspect the scene, face a nearby visible landmark,
walk one to two blocks toward it on observed safe ground, stop, and report
the observed change. The operator supplies scope and lease, not target
coordinates or a scripted tool program. Inability to find a safe move is
retained as an outcome, not retried to manufacture a pass.

| Bound | Proposed one-run scope |
|---|---|
| Model | Existing pinned `gpt-5.6-luna`, ChatGPT OAuth |
| Bodies/helpers | One Mineflayer avatar, zero helpers |
| Model calls | At most six, one handler, every request reserved and settled separately |
| Additional API-equivalent estimate | At most $1 total from the original $10; not $1 per call or an OAuth invoice |
| Retained accounting | Existing $0.7554 unknown hold and $0.001458 settled usage remain; maximum combined exposure $1.756858 |
| Native duration | At most 90 seconds after native start; existing worker/server lifecycle limits still apply |
| Mutations | At most two forwarded `act` calls; only `look_at` or `move_to`; each at most 2 seconds with release required |
| Failure | Preserve evidence and costs, stop the worker lane and owned processes; no automatic replay |
| Qualification | Development only, explicitly isolation-unqualified; no private score, research or full G0 claim |

The per-request conservative reservation is $0.7554 under the existing pinned
basis. Six requests are a count ceiling, not a promised number: a subsequent
request is refused if prior consumption plus its reservation exceeds the $1
job envelope. Unknown new usage stops admission without releasing its hold.

`tools/m0_native_game.py PRIVATE_PLAN.json` accepts `strata/M0NativePilot/1`.
It requires a fresh original-baseline restoration and output, the existing
controlled worker/PackLock, a fresh zero-helper preregistration, current native
preflight, and original authority/credential references. Its `pilot` object has
`database`, `objects`, `credentials`, `preflight`, `authorization`, and `job_id`;
the consumed one-run identity is `validation-2026-09-18:m0-pilot-01`.
D15 additionally supplied the private `budget_decision` file, validated against
the unchanged original authorization and retained unknown rows.

Read-only accounting checks run before Java, the worker, or credentials are
opened. Without a decision, unresolved usage returns `PILOT_ACCOUNTING_BLOCKED`;
the now-consumed job returns `PILOT_ALREADY_ATTEMPTED`.
Native D14 admission deliberately makes no isolation-pass record. It retains
the existing pinned binaries, tool catalog, scoped broker, finite exposure,
fixed TLS destination, credential handling and durable accounting checks.
The D12 receipt-only entrypoint rejects a piloting context.

Acceptance joins the actual model request/usage receipts, broker requests,
Mineflayer action journal and ordered public observations. It requires an
observed turn toward the chosen target, actual displacement toward the chosen
walking target, fresh revisions, completed actions and released controls.
An action acknowledgement or the model's claim alone cannot pass. Saved world
capture remains retained, but this trial does not claim a complete joint
checkpoint or authoritative clocks. Failed native startup reports unknown
request count until actual evidence establishes it; it never assumes zero.

The unresolved usage receipt was not retained by the original failed transport.
Current evidence cannot settle it. Under the recorded
[admission contract](validation-admission.md), a distinct, explicitly authorized
bounded exception retaining that hold is needed before this live trial can be
dispatched. D14 changed isolation scope only. D15 supplied that one-run
exception; six actual requests settled, but malformed game calls prevented
piloting. D15 is now consumed and cannot be rearmed.

The [fresh preparation and independent audit](../verification/2026-09-23-pilot-preparation.md)
now establish the actual unused instance and sealed private plan. Use those
inputs were versioned for D15 and the instance was used by the failed pilot.
Preserve it as evidence; another trial needs a fresh baseline and distinct
authorization. No reinstall or unchanged worker rebuild is needed.
