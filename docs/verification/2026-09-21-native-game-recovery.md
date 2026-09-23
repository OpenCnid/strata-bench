# Connected native and vanilla recovery

September 21, 2026. Operator-only. M0.1d.6; F03/F04/F06/F09/F11/F16,
N01/N02/N03/N06, C06/C09/C12/C16/C20, partial T01/T03/T06/T07/T12,
G0 items 1/4/6. M0 remains incomplete and G0 fails.

The scripted development path now resumes the captured world, worker journal
and native root together. Before recovery the root note is
`STRATA_OWN_ARTIFACT`, six calls have consumed 84 fixture units, and epoch 1
has one completed action. After recovery the root has read that note and
changed it to `STRATA_RESTORED_AND_CONTINUED`, total usage is 12 calls/168
fixture units, and epoch 2 has one new completed action. The old action and
export remain unchanged. This uses real vanilla and the native CLI/Dovetail;
all model replies and their accounting units are scripted.

[Native restoration](../../src/mcbench/native_recovery.py) requires the same
account, campaign, agent, pinned runtime/model and helper bound, a higher epoch,
the committed recovery component, no intervening executor state and a local
scripted provider. It restores root files once into a fresh grant namespace,
preserves immutable initial artifacts, and gives helpers no root history.
Reenrollment cannot overwrite subsequent writes. The optional launch extension
leaves historical plan/profile hashes unchanged when absent. Source export
verification joins the restoration event before root broker calls.

[The integrated runner](../../tools/native_game_recovery.py) checks the old
sealed components, builds a fresh instance from all 28 captured mutable files
plus the exact immutable distribution, and creates a new transient session lock.
It copies the stopped native/CAS and worker stores without reinstalling accounts.
The new fixture reserves at most ten calls within the original fixture cap,
leaving the old consumed costs intact. No original experimental allowance changes.

Before native dispatch it checks saved position/orientation, health, food,
dimension and inventory slots/IDs/counts against the avatar's permitted
observation. Old-token and old-epoch read requests must reject. No old action
is replayed. A new epoch-specific action ID prevents collision with the retained
journal. Raw player NBT and source context remain operator-only.

Source verification: 49 recovery/retention checks passed in 18.93 s; the
expanded recovery/start selection passed 27 in 9.38 s; admission/export/gameplay
package checks passed 57 in 13.89 s. These selections cover **119 distinct
tests**. The corrected null no-action sentinel passed the 12 start checks in
0.27 s. Full source/tool Ruff passed. A private offline copy of the actual
source store also validated attachment with its six calls/84 units unchanged.
These are synthetic/source checks, distinct from the live trials below.

Private `2026-09-21-m0-native-recovery-01` failed after matching the restored
player because the new assertion expected zero instead of the schema's null
`last_action_seq`. It performed no new action or native/model request; forced
worker cleanup (exit 125) is retained. The server stopped normally. Its 653-file
seal is `05ecf2d3c1b325ad4ac6950db0ec725f8b8014a6f96c8ad1dff95066a425f31f`.

Changed trial `2026-09-21-m0-native-recovery-02` passed in **198.375 s**:

- Saved own state matches before native dispatch; old token returns FORBIDDEN
  and old epoch returns STALE_EPOCH. The prior journal remains unchanged.
- **35/35 native checks pass**, including the typed returned retained note,
  helper history denial, unchanged account limits, preserved prior costs,
  one projection, one fresh action and FINALIZED root/helper closure.
- Six additional scripted calls consume 84 units; cumulative usage is 12/168.
  One new primitive brings the preserved worker total to two.
- Worker/server drivers exit zero without forced cleanup. Every held server
  process exits; the new stopped capture and joint component receipt publish.
- Independent read-only audit reconstructs old and new exports, wire usage,
  saved player state, worker actions and new captured bytes. The 4,370-file
  seal is `9f9e32c888a5cb48bd6c15fee65efe22a14c8305e80f58f4ca76a88df01eed2b`.
  Audit report SHA-256 is
  `7b800ddcf8ed1e7ea8a4abbb16ce6b50610f618d11f224c02dcb893b0f671bc6`.
  An initial audit-only KeyError used the wrong receipt field; that failure is
  retained and corrected offline without rewriting the seal or repeating play.

The case-04 source remains an outer publication **failure**. Its independently
verified components were used without promoting that run. Both source/template
bytes and all 172 source pins remain unchanged. Original authority remains
$0.7554 unresolved plus $0.001458 settled; D12 remains consumed. No Java remains,
no shared-desktop input occurred, and no real model request was dispatched.

M0.1d.6 is verified only for this scripted, single-avatar development recovery
contract. It does not qualify a canonical complete checkpoint, external-writer
exclusion, all save semantics, authoritative clocks/scorer, live-model recovery,
or 500-ms shutdown. All previous shutdown/effective-file/isolation/E9E failures
remain. Continue the connected canonical checkpoint/provenance and scorer/setup,
isolation and shutdown dependencies; do not repeat this unchanged trial.
