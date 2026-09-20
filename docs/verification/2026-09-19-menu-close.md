# 2026-09-19 explicit menu-close lifecycle

Operator-only. D07, M0.3b.1b.2b.1c.1/.2 and M0.2 inventory lifecycle; F01/F06/F09/F11/F16,
N01/N02/N03/N04/N05/N06/N08, C09/C15, T01/T03/T06/T07/T12. Implemented but
unverified in authentic Minecraft; no milestone or aggregate gate closes.

## Contract and behavior

Inspection found that the original typed action union could open a menu but could
not explicitly close it. The Forge movement path correctly rejects an open screen,
so this omission prevented continued structured gameplay after container use.
SPEC v0.2.1 records D07 and adds ordinary `close_window` with current window ID and
revision. It remains a single bounded action with a 10-second maximum, scoped
authority, one mutation lane and existing cancellation/uncertainty semantics.
No implicit close was added to movement or another action. No requirement was
removed, and all 13 top-level record types remain unchanged.

[GameMenuClose](../../java/forge1192-client/src/main/java/io/github/opencnid/strata/client/GameMenuClose.java)
and [Mineflayer closeMenu](../../backends/mineflayer/src/menu_close.ts) preserve own
inventory plus cursor/temporary crafting inputs, excluding output previews and
persistent container contents. Before close, simulate return capacity using matching
private item/component identities, merges and empty main/hotbar slots. Existing
offhand stacks may merge; empty offhand and armor slots are not auto-equipment
destinations. Capacity shortages reject before dispatch. The candidate supports
the existing native/pinned player, crafting, chest/generic and furnace menu classes,
with item/stack bounds; arbitrary mod menus and larger stacks remain explicit gaps.

Forge invokes the actual container screen's `onClose`, or ordinary player close
for inventory menu zero without a screen. It fences screen/menu/selected-slot/body
continuity, then requests actual full player-inventory contents. Mineflayer invokes
pinned `closeWindow`, then `_syncWindow` for player inventory; the before-state uses
the open menu's current own-inventory region, not a possibly stale inventory copy.
Neither implementation queries persistent container slots after closing.

Prediction alone never confirms completion. After server feedback, require empty
cursor/crafting grid, conserved owned item/component totals, unchanged armor and
agreement with the currently applied state. Close, refresh and active waits are
charged; native final release is also retained. Interruption may leave the menu
closed while its server effects remain uncertain. Never reopen, replay, refund or
invent cleanup after cancellation, deadline, missing reply or exhausted budget.
Receipts stay input-only `emitted` with fresh observations/recovery requirements.

The schema exporter regenerated ActionBatch/RpcRequest and their TypeScript
bindings. Both backends advertise thirteen action kinds; Forge capability minor 11
uses `durable-intent-client-thread-thirteen-actions/1`, and Mineflayer minor 6 adds
the same explicit close operation. Close policy is
`explicit-close-own-inventory-feedback-conservation/1`. Native Java/TypeScript/Python
capabilities agree; old manifests do not silently acquire this operation.

## Executed verification

Windows / Node 24.19.0 / Python 3.12.14 / Temurin JDK 17.0.20.1+1 /
Forge 43.4.23 compilation artifacts. Private evidence:
`%USERPROFILE%/.strata/evidence/2026-09-19-menu-close-01/`.

- `uv run --frozen python tools/export_schemas.py`, then `npm --prefix
  backends/mineflayer run generate`: completed. Cross-language checks retain all
  13 SPEC example records and reject malformed close action fields/duration.
- Pinned Gradle client tests/build/reobfuscation/classpath: **153 Java passed**,
  zero failures/errors/skips, build 24 seconds. Nine new tests cover pending feedback,
  cursor/grid returns, merging/space reservation, offhand semantics, loss/gifts,
  component/armor changes, stale/replaced state, failed refresh charge, strict
  envelope and actual durable-lane cancel/deadline/budget cases with synthetic menus.
- Explicit pinned JVM/Python guardian `npm test`: **107 Node passed**, zero skips,
  44.407 seconds; TypeScript build passes. Eight new Mineflayer motor tests use
  pinned Prismarine window/item models and scripted server contents; a new schema
  test covers the explicit action. Actual Forge broker/JVM fixtures also accept the
  close envelope once, with synthetic effects. Guard fault injections stopped
  disposable JVMs after native freeze / worker kill / worker hang / parent kill
  in **505 / 42 / 1731 / 24 ms**, one intent/no replay. These are not Minecraft
  stop-timing or authentic menu-effect results.
- Explicit-JVM `uv run --frozen pytest tests/test_contracts.py tests/test_records.py
  tests/test_native_game.py tests/test_native_game_jvm.py tests/test_gameplay_package.py
  -q`: **95 passed**, zero skips, 21.67 seconds. Targeted Ruff passes.
- Failed attempts retained: a test fixture initially supplied an invalid typed NBT
  `name` field (removed); a cancellation test exposed the Node timer's AbortError
  wrapping the declared reason. The wait now propagates the original abort reason;
  the full suite passes without weakening the cancellation assertion.
- Pinned native bytecode confirms normal close invokes player close/server packet
  and inventory return paths, with ordinary existing-offhand merge behavior. This
  source evidence does not substitute for actual loaded-pack effects.

Built JAR SHA-256:
`7b14b6b8546e43377667e5122ee03c060480676c54c65ea8f88c561cbace304b`.
It is **not installed**. The implementation and synthetic-test phase used no
desktop input, new game/server launch or inference. A fresh read-only capture
still showed the Windows Security prompt covering the old client; user handling
remains pending. Subsequent [authentic vanilla player-menu checks](2026-09-19-vanilla-menu.md)
provide partial live evidence separately.

## Remaining qualification

Run explicit close on both authentic profiles with server/reference evidence:
ordinary chest/furnace/player/crafting menus, cursor/grid return, full inventory,
interruption before/after close, menu replacement and loaded mod hooks. The native
full-menu refresh still has no causal nonce; ordering/no-op conformance remains
unverified. A successful synthetic resource check is not a live server-close proof.
No API can yet admit campaigns. Finish remaining placement/full geometry/custom
recipe/menu/machine work, controller/aggregate accounting, isolation, native host,
soaks, simultaneous capacity and research milestones. All original gates remain.
