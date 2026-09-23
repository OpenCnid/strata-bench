# M0 development piloting trial

Updated September 23, 2026. Operator-only. Implements D14; live execution remains
blocked by original accounting admission. This document does not authorize a
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
the one-run identity is `validation-2026-09-18:m0-pilot-01`.

Read-only accounting checks run before Java, the worker, or credentials are
opened. The current unresolved hold returns `PILOT_ACCOUNTING_BLOCKED`.
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
dispatched. D14 changed isolation scope only. No such exception has been
installed, and no model call has been made by this implementation.
