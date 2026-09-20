# Thermal slot transfers and D10 input fences — September 19, 2026

Operator-only. **Implemented but unverified in Minecraft.** M0.3b.3.2.2a advances
F01/F06/F09/F16, N01/N02/N03/N04/N05/N06, C09/C15/C18 and partial T01/T03/T06/T07/T12.
The parent keeps separate children for full routing/panels/controls (.2b), ordinary
energy/fluid operation (.2c) and authentic GUI/server/reference qualification (.4).

## Behavior

`GameMachineInventory` handles one ordinary native Thermal furnace/crucible
left/right pickup/place or machine-to-player quick-move. The existing exact
artifact/version/menu/screen/tile/layout guards still apply. `NativeGameRuntime`
uses normal `handleInventoryMouseClick` and the existing bounded current-menu
server refresh; no server-side machine setters or arbitrary packet interface is
added. The ordinary vanilla-menu motor retains its previous verifier.

Immediately after the native click, on the same client-thread call stack, the
motor checks its predicted visible resource totals and permitted changed slots.
It then waits for actual full server contents that the normal client handler has
applied. Every owned player slot and the cursor must exactly match the prediction,
including private component identity; the current owned state must still match
the reply. A prediction alone cannot confirm a transfer. Machine processing or
charging may independently change machine storage during this wait. The receipt
does not attribute those changes to the click or prove production, recipe
correctness, provenance or a private milestone. Those require server/reference
evidence and scorer controls, including gifted-output negatives.

Wrong owned quantities/components, gifts, losses and subsequent owned changes
fail. A prediction that creates resources or rearranges unrelated slots still
requests resynchronization after already-emitted input, then fails. The real
action lane classifies failures after an attempted primitive as `unknown`, fences
the lane and preserves charges; it does not retry the click. Cancellation,
deadline and exhaustion release/fence through the existing lane. Click, refresh,
feedback-wait ticks and safety release remain charged.

Augment-panel slots are masked before motor and feedback stack readers run.
`NativeWindowSync` applies the same projection to the packet and current menu;
masking preserves native indices without inspecting those stacks. An inactive
base/player slot rejects the motor view. Machine close only needs the player's
inventory and carried stack for its return-capacity check; it no longer copies
machine/augment contents for that purpose.

## Exact-source finding and remaining routes

The installed CoFH `ContainerCoFH.performMerge` uses `TileCoFH.invSize()` as the
player-to-machine range; the installed Thermal `AugmentableBlockEntity.invSize()`
includes augments. Therefore that direction of native shift-click could operate
on currently hidden slots. It and direct hidden-slot requests reject before
input. Ordinary pickup/place provides the initial insertion route; full routing
and panel/control coverage remains a required .2b item.

This was inspected in the installed bytecode, using the same three pinned JARs
recorded in [the observation report](2026-09-19-thermal-menu.md). Upstream
[CoFH container source](https://raw.githubusercontent.com/CoFH/CoFHCore/1.19.x/src/main/java/cofh/core/inventory/container/ContainerCoFH.java)
and [tile container source](https://raw.githubusercontent.com/CoFH/CoFHCore/1.19.x/src/main/java/cofh/core/inventory/container/TileCoFHContainer.java)
support the investigation; installed bytes remain authoritative. No source
inspection is counted as live operation or GUI parity.

## D10: display versus input revisions

SPEC v0.2.5 and Forge capability minor 15 explicitly declare:

- `thermal-visible-slot-owned-transfer-feedback/1` for the transfer behavior.
- `thermal-display-independent-slot-cursor-fence/1` for input preconditions.

Passive machine energy/tank values remain in observations and capture revisions.
They are excluded from the window input revision and live input comparison so a
running machine cannot prevent even normal close. Slot contents, cursor, window
identity/revision, body/control/lease/generation, latest captured observation and
two-second age checks remain. Unknown machine policies and type mismatches do
not receive this exception. This supersedes the overly broad v0.2.4 input fence
explicitly; it does not relabel an existing experiment or waive any gate.

## Executed verification

Windows x64; pinned Temurin JDK 17.0.20.1+1, Forge 43.4.23/Minecraft 1.19.2 build,
Node 24.19.0 and frozen repository Python environment. These tests use synthetic
game effects. Java journal/locks and Python/Node HTTP/JVM transports are real.

| Command / procedure | Actual result |
|---|---|
| `gradlew.bat :forge1192-client:test :forge1192-client:build :forge1192-client:writeTestClasspath --no-daemon --console plain` | Final **200 pass**, no failures/errors/skips; 24 s build |
| `npm test`, with pinned `STRATA_CLIENT_TEST_JAVA`, `STRATA_CLIENT_TEST_CLASSPATH` and `STRATA_GUARD_TEST_PYTHON` | **116 pass**, no skips/failures, 46.097 s |
| `uv run --frozen pytest tests/test_native_game.py tests/test_contracts.py tests/test_records.py tests/test_native_game_jvm.py -q`, with pinned Java/classpath | **114 pass**, no skips/failures, 23.20 s |
| Ruff on changed Python; TypeScript build; `git diff --check` | Pass; ordinary line-ending warnings only |

Eighteen new Java cases cover input-fence policy, hidden reader canaries,
prediction-only rejection, processing during deposit/withdrawal, charging,
right-click remainders, matching-cursor output pickup, multi-destination outgoing
quick-move, owned gifts/loss/components, invalid prediction, replaced state,
permissions, cancellation, unknown receipts, duplicate requests and budget/deadline
stops. The latter cases run the actual durable lane with scripted machine effects.

One intermediate run had 199 passing cases and a fixture setup failure:
`SETTINGS_UNSAFE_PATH` because the deadline/budget test's child directory did not
exist. The fixture now creates its dedicated temporary directory. The path guard
was preserved; no production acceptance rule was weakened. Its failed XML/log
remain alongside the final successful evidence.

Final built, **uninstalled** client SHA-256:
`1e857474cacd9a269d85c133e4396b39986a4820665c295e47dd2da9b7f7e725`.
Private evidence root:
`C:\Users\Darian\.strata\evidence\2026-09-19-thermal-transactions-01`.
It contains logs/XML, selected source hashes/copies, inspection evidence and the
verification manifest. No auth cache or native connection descriptor is copied.

## Live status and next work

A new read-only E9E screen capture again confirmed the Windows Security/OpenJDK
network permission prompt (recorded at 10:03:40 UTC). No desktop input was sent.
The computer-use skill forbids acting on security permission requests; the existing
operator handoff remains pending. No game server/worker or Strata inference was
started. The running client still has the old read-only JAR; the new candidate
is not installed.

Keep .2a `implemented_unverified`. Continue exact player-accessible machine recipe
discovery and the remaining transfer/control/energy/fluid adapters while .4 awaits
the operator prerequisite. Then deploy and qualify actual JEI/expert crafting,
native movement/menus/cancellation, Thermal GUI/slot/processing/feedback behavior
and server/reference evidence. Full source visibility, host/isolation/accounting,
keybindings, soaks/capacity, scientific and later-pack gates remain open.
T03/G0 retain the failed Mineflayer/E9E result; this report closes no aggregate gate.
