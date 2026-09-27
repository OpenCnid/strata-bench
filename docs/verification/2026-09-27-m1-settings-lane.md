# M1.1b transaction-owned native effect route

The candidate input engine is now connected to the Forge game bridge, settings
store and the avatar's existing input lane. This implements a private route for
collecting transaction-bound observations; it does not qualify keybinding effects
or complete T05/G1. M1.1b remains in_progress.

## Admission and ownership

An explicit `strata.settingsEffects=true` launch enables the private candidate
route only with the existing game bridge and durable game authority. Startup
rejects simultaneous settings bridges, transaction/crash/discovery diagnostics
and collision diagnostics. The opt-in is included in the native runtime identity
as `settings_effects_candidate_policy`; the rebuilt artifact also changes source
identity. Default game profiles retain `keybindings=false` and refuse these calls.
No gameplay tool catalog or public action mode is expanded.

The private game protocol accepts strictly parsed `settings_snapshot`,
`settings_apply`, `settings_status`, `settings_rollback`, `settings_effect_start`
and `settings_effect_status` operations. Effect requests bind a stable binding ID,
pending transaction, expected revision/digest, plan digest, context, restart-stage
label, bounded hold and observation window. There is no raw key-code argument.
The source-bound native resolver admits only the exact Curios mapping and selected
known vanilla control objects. Its encoded-key/candidate-pool checks remain
prerequisites, not evidence that a key or consumer is qualified.

`SettingsStore.verificationHead` requires an applied-pending-verification
transaction, matching complete runtime values/ownership metadata, owned persisted
values and unchanged non-owned options. The run checks this head before input and
during observation. Neither interrupted prepare nor rollback authorizes effects.

`GameActionLane` cancels/fences normal work before entering reconfiguration. The
same immutable avatar/body authority, primitive cap and journal cover writes,
verification input, waits and cleanup. It rejects concurrent gameplay, a second
owner, consumed operation IDs, body/generation changes and expired authority.
The deadline is pinned before cancellation/release work, so that work cannot
extend the input allowance. A chord reserves three cleanup primitives. Safety
release remains possible after ordinary admission expires; uncertainty is never
refunded. Completion leaves gameplay fenced until a fresh epoch/resynchronization.

Admission metadata is durable before the first input: transaction/request,
settings fingerprint, plan/keymap head, context and stage label. Observations and
attempted primitives share the game journal. Reopening an interrupted owner
never renews its input deadline; ordinary arming stays blocked. The explicit
recovery path can only run the settings store's owned-value CAS rollback under
reserved safety accounting, then end the interrupted scope as unknown.

## Observations and limits

The native port uses ordinary keyboard callbacks and the previous window-scoped
polling engine. It captures current visible screen/menu type, own position,
sneaking/sprinting/use state, window activity and client-tick index. Forge screen
opening events are recorded separately with their cancellation flag: an opening
request is not proof that a screen appeared or rendered. The run continues normal
client ticks after key release to observe delayed GUI/server effects. Trace count
and bytes are bounded, and lost callbacks are not replayed.

Every result explicitly has `verified=false` and `committed=false`. State
`observed` means the bounded procedure completed, not that intended/competing
effects passed. The restart-stage label is a caller-supplied join field, not proof
of an actual restart. The settings transaction remains pending until the full
verification workflow decides commit or rollback; this route adds no commit API.

The existing native writer still permits its source-bound Curios unbound/F13
development values. Unknown consumers, mouse bindings, unsupported key encodings
and currently unsupported standalone modifier keys remain refusals. Full conflict
repair, expanded proven key/chord allocation, essential-control checks, rendering,
restart/rollback and isolation still require implementation and authentic evidence.

The Python operator client does not yet expose these new operations; its existing
allowlist still refuses them. Next implement its strict bindings and result/source
joins, prepare the exact-profile native verification, and execute the real
Curios/competing-control cycle. The qualified gameplay settings adapter, complete
T01 reconciliation and final T04/T06 accounting/isolation remain open. No hidden
evaluation material or free evaluation fixtures enter this route.

## Executed verification

Windows, Java17.0.20.101, Forge1.19.2-43.4.23, exact existing FTB Library compile
dependency; offline commands:

```text
java/gradlew.bat -p java --offline :forge1192-client:test
  --tests '*SettingsEffectRunTest' --tests '*SettingsEffectAdmissionTest'
  --tests '*NativeGameProtocolTest' --tests '*GameActionLaneTest'
  --tests '*SettingsStoreTest' :forge1192-client:jar --console=plain
```

After admission/source-join review, the changed `SettingsEffectRunTest` and JAR
were rebuilt separately. Across the final applicable results, 22 new and 43
affected existing cases pass, without skips. Compilation/reobfuscation and
`git diff --check` pass; deprecation warnings remain. Earlier passing runs are
retained, rather than counted again.

The tests use real temporary options/journal files and an actual authenticated
loopback HTTP bridge with deliberately synthetic game/body/clock/input state.
They exercise pending transaction through input/observation, conflicts, missing
contexts, budget/deadline exhaustion, stop-all, body change, consumed IDs,
interrupted/complete journal reopen, and HTTP duplicate delivery with no repeat
input. They do not run Minecraft, load the installed mixin or prove real effects.

F04/F06/F09/F16, N01/N02/N03/N06, SPEC8.2 and the affected T01/T05/T06 dependencies
remain under the original G1 criteria; no aggregate gate changes. There was no
game/model call or installation. All 40 authority table hashes, the historical
inference exposure and three separate 256MiB telemetry holds remain unchanged.
D18/D19 remain M0-only. No further furnace trial is selected.

Private evidence `2026-09-27-m1-settings-lane-01` is sealed: 33 files,
2,630,864 bytes, seal
`f672512e5a15f2cbc18a72b18337bb0b6c23ffb0a2dc0768896ea282fb2de6f0`.
Source pins, all test/build outputs, rebuilt uninstalled JAR and final audit are
retained. The audit preserves 458 milestone IDs, append-only history and 1,818
local links; no Java process remains. This seal pointer follows the source snapshot.
