# Native Dovetail to real Minecraft: first connected run

September 21, 2026. Partial M0.1d; F03/F04/F06/F09/F11/F16,
N01/N02/N03/N04/N06, T01/T03/T04/T06/T07/T12, G0 items 1/4/6.

The native CLI now uses the restricted broker to observe **real vanilla
Minecraft**, perform one bounded look action and read its outcome. A native
clean-context helper runs in the same job and cannot use the game tool.
Native termination stops the bound game lane. The worker journal and the
independent stopped player save agree with the returned action receipt.

**Model responses are scripted. This is an authentic game/native integration
test, not a live Luna run, a reasoning result, private scoring or G0 closure.**
M0 remains in_progress, G0 fail, G1–G5 not_run. The next priority is completing
this connected path, not expanding unrelated fixtures or later controls.

## Runnable implementation

`tools/m0_native_game.py PRIVATE_PLAN.json` owns the existing server launcher,
Mineflayer worker, sealed native Dovetail/broker/helper execution and cleanup.
It preserves separate model fixture accounting and real primitive receipts.
The launcher requires existing private installations and explicit plans; it
does not install anything, accept an EULA, spend model allowance or use desktop
input. Run with the repository Python and `PYTHONPATH=src;tools`.

The private plan has schema `strata/M0NativeGameSmoke/1` and these fields:
`output` (fresh private directory), `server_plan` (existing DevelopmentServer/1),
`worker_config` (DevelopmentWorker/1), `codex`, `node`, `tool_projections` and
`model_catalog`. Server/worker scope, finite lifetime and primitive limit come
from those explicit operator inputs. The smoke command currently supports
vanilla only. Forge retains its separate identity and evidence.

`src/mcbench/native_worker.py` binds one executor/job/epoch to an operator-held
worker descriptor. It records stop intent before transport, accepts only the
matching successful stop receipt, and records completion durably. Lost, wrong
or incomplete receipts stay STOPPING and cannot be replayed or rebound. This
is local lane shutdown, not proof of a complete game/agent checkpoint.

The worker also supplies `--check-vanilla-runtime`: load dependencies without
constructing an avatar, authenticating or opening a game socket. The launcher
runs it before the server and retains a private Node compile cache. Parent
startup failures now emit a sanitized code instead of silently exiting. No
2250-ms startup, action or 500-ms guardian threshold changed.

## Actual execution

Private bundles: `.strata/evidence/2026-09-21-m0-native-game-01` and `-02`.
Each used a fresh checked copy of the existing official vanilla 1.19.2 server
and player state; no claim of a qualified initial research checkpoint is made.
The original source copy remained unchanged. Node 24.19.0, Mineflayer 4.39.0,
protocol 1.68.0, Java 17.0.20.1+1 and the existing pinned Codex/Dovetail apply.

- **01: fail.** Server starts, worker exits before API readiness. Its older
  parent discarded the failure reason. No native request or gameplay action
  ran. Server stops normally; total 20.907 seconds. Slow cold dependency
  loading is a hypothesis, not an established cause. Preserve the interrupted
  worker journal/lock; never reuse its epoch or silently remove that lock.
- **02: pass for the connected smoke scope.** With dependency preflight and
  startup diagnostics, the avatar connects and native execution completes.
  Six scripted provider requests consume 84 synthetic fixture units once.
  Root/helper admission, helper game denial, worker credential exclusion,
  actual observations/action and native-exit stop checks pass. Native exit is
  zero/FINALIZED. The action emits one primitive; its completed receipt is
  byte-equivalent between the native broker response and worker journal.
  Saved player orientation changed and matches the final public observation
  within 0.01 degrees; saved position also matches. Native execution lasts
  25.837 seconds; the full finite worker/server run lasts 194.906 seconds.
  Both return zero and the server saves/stops without forced cleanup.

The source/pins at dispatch are archived privately. Subsequent source changes
only copy the descriptor defensively and make missing journal evidence fail
the report; they have focused checks, not a repeated authentic trial.

## Limits and next action

The original authority was rechecked read-only before both preparations:
original $10, $0.7554 reserved once, uncertainty true, no new live inference.
The successful six-call model usage above is fabricated fixture usage and
must not be reported as experimental OAuth tokens, an API estimate or charges.

Live model admission remains blocked by SPEC §15 and the installed
`unknown_metering: block` policy. D12 now explicitly permits
one **distinct** receipt request bounded at $0.7554 while retaining the
original $0.7554 hold unchanged (combined exposure $1.5108 within $10).
The one-use policy is implemented; the authorized live outcome is tracked in
the handoff. It cannot replay the original request, refund it or grant a fresh allowance.

Real OAuth reasoning/usage, complete runtime isolation, private milestone
scoring/controls, full clock/evidence reconciliation and authentic paired
recovery remain open. Preserve failed loopback/sibling canaries, every failed
500-ms sample, the five effective-file failures and Mineflayer/E9E failure.
The completed vanilla mechanics and separate Forge evidence remain valid only
for their recorded scopes. No threshold, M0–M6 requirement or conditional
M7/extension was removed.

Both private evidence bundles are now inventoried and sealed. Case 01 seal:
`e4416b5c78a73bfc71abc678bc9b82cd5fc2d38a6614f5a46647359fa9c34596`;
case 02 seal:
`866250d9c903c7d9183349b7a6b3a164aa3f0cdd173def627f1677ee95c4006d`.
The subsequent [D12 receipt trial](2026-09-21-native-oauth-d12.md) is distinct:
it supplies recovered authentic model usage, not live reasoning for this game run.
