# 2026-09-19 native placement, equipment and menu feedback

Operator-only. Scope: M0.3b.1b.2b.1 and the existing click-slot implementation;
partial F01/F06/F09/F11/F16, N01/N02/N03/N04/N05/N06, C09/C15/C18,
T01/T03/T06/T07/T12 under G0/G1/G2. No authentic gate closes.

## Implemented behavior and limits

The Forge development candidate now advertises ten action kinds. New `place`
dispatch checks delivered support and adjacent air, held block-item identity,
Forge reach and the native hit face, then performs ordinary main-hand use after
aiming and the Forge input hook. Hidden/occupied cells, wrong faces and replaced
supports fail. This remains an initial air-destination placement policy: qualified
replaceable states, interactive supports/crouching and exact-pack placement
effects are still required work. An ordinary block-use result may open a menu
instead of placing; receipts never claim successful placement from emission.

New `equip` selects an explicit hotbar slot or executes at most three fixed
pickup/destination/return clicks in the player inventory. It checks source item,
slot permissions/capacity and an empty starting cursor. Every inventory click,
including `click_slot`, waits for full server contents, checks the applied menu,
cursor/target poststate and item/component conservation before continuing. No
resource gathering, inventory search, item drop or guessed custom serializer is
added. Crafting preview slots remain reserved for the unfinished craft motor.

`GameInventory` contains the transaction logic; `GameMenuFeedback` bounds and
fences callbacks; `NativeWindowSync` implements the private native transport.
The pinned 1.19.2 client predicts clicks, and the server need not respond to a
correct prediction. The adapter therefore sends one fixed outside-slot
`PICKUP_ALL` refresh (`-999`, button 0, impossible state ID -1, no changed slots)
for the validated open menu. Inspection of the pinned native menu/server handler
shows the negative slot skips transfer and the mismatched state ID requests full
contents. That is an implementation basis, **not an authentic no-op test**.
The gameplay API exposes none of these packet fields or arbitrary packet access.

The network observer forwards normal handling before scheduling a bounded
client-thread callback. It accepts only the pending menu's full contents and
compares them with the actually applied menu. Stale/replaced/unapplied/malformed
feedback cannot authorize another click. Cancellation invalidates continuation
but retains inventory uncertainty; a valid late reply may reconcile the state.
Until then, fresh mutation rejects with `GAME_MENU_RESYNC_REQUIRED`, including
after epoch rearming. Missing feedback or replaced-menu cases can require a new
connection and classified recovery; this path remains unqualified in-game.

Server menu responses contain no request nonce and are not proof of causality.
All action outcomes remain input-only `emitted` with fresh observations, or
explicit failed/cancelled/unknown receipts. Scoring remains private server work.
Private comparison hashes include serialized item components/Forge capabilities,
bounded to 16 KiB per item. None of those raw components are exported publicly.

Capability minor 8 pins `durable-intent-client-thread-ten-actions/1`, the fixed
refresh policy and explicit primitive units. Clicks, refreshes and every active
feedback-wait tick are charged, alongside existing aim/gesture/held-input/release
units. Unknown attempts are not refunded. Complete aggregate accounting remains
M0.3b.2c.2; these counters do not claim model/tick budget qualification.

## Executed verification

Windows 11, Python 3.12.14, Node 24.19.0, Temurin 17.0.20.1+1,
Minecraft 1.19.2 / Forge 43.4.23 mapped build artifact. No live game was launched.

- Pinned Gradle client test/build/reobfuscation and fixture-classpath generation:
  **85 Java tests passed**, zero failures/errors/skips. Eighteen new tests cover
  prediction without feedback, rejected replies, right-click splits/merges/full
  stacks, component/resource conservation, cursor accounting, quick move, fixed
  three-click equipment, intervening updates/menu replacement, slot permissions,
  exhausted refresh allowance, cancelled/stale callbacks, unapplied contents,
  observed placement cells and strict face/equipment envelopes.
- `npm run build` passed. `node --test dist/tests/forge.test.js`, with explicit
  pinned Java/classpath and Python guard environment: **21 passed**, zero skipped,
  50.718 s. Expanded envelope routing includes equip/place, exact native journal
  intents and no duplicate dispatch. The generic fixture's effect is synthetic;
  it does not run the native placement or menu transport. Guarded synthetic
  native-freeze/worker-kill/worker-hang/parent-kill cases stopped the fixture JVM
  in **1411/37/1932/30 ms**, respectively, retaining one intent and no replay.
- `uv run --frozen pytest tests/test_native_game.py tests/test_native_game_jvm.py
  tests/test_forge_guard.py tests/test_gameplay_package.py`: **34 passed**, zero
  skipped, 27.36 s. One pre-existing xunit2 `record_property` warning remains.
- Targeted Ruff passed. The broader 96-test Node result belongs to the preceding
  gesture change; it was not rerun or relabeled as this change's full-suite result.

Private logs/XML, changed-source and rebuilt-JAR hashes are retained under
`%USERPROFILE%/.strata/evidence/2026-09-18-forge-inventory-placement-01/`.
The directory retains the task's start date; completion crossed into September 19.
JAR SHA-256: `05f8c300aeda0a1a1bc3851fc907fa67a80255f9b19a36f944abfa5a5f2e5119`.
The JAR was not installed into a live profile. Credentials/grants/private account
identity and game installations remain outside this report/source tree.

## Remaining gates

Native packet ordering, the fixed refresh's actual no-effect behavior, mod hooks,
slot/cursor/resource effects, recovery and deadlines still require authentic
Minecraft testing. Synthetic ports are not substitutes. Movement and crafting
remain unsupported; complete placement and exact modded metadata/collision,
expert recipes, custom containers/machines and quest surfaces remain explicit.

Controller/repair/aggregate accounting, launch containment, OS/process/network
isolation, keybinding/native model/budget, soaks, simultaneous bodies, scientific
studies and later packs retain their required gates. T03/G0 keep the actual
Mineflayer/E9E failure; the Forge candidate's authentic T03 remains `not_run`.
Desktop control remained paused, and no inference was dispatched.
