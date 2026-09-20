# Authentic E9E machine conformance continuation

September 20, 2026. Operator-only. M0.3b.3.2.4b.2, partial
F01/F05/F06/F09/F11/F16, N01/N02/N03/N04/N05/N06/N08,
C04/C09/C14/C18, T01/T02/T03/T07/T10/T12/T13. **In progress.**
The machine-operation requirement and G0 are not passed by the evidence below.

The [private reader/baseline report](2026-09-20-machine-reference.md) records the
protected copy, exact source hashes, six setup-only commands, empty furnace,
20,000 RF and three supplied iron-dust items. Setup has no client joins and a
normal server save. These are labeled development resources, not accomplishments.
The original server/world remains separate and unchanged.

The existing exact E9E/Forge candidate uses native JAR SHA256
`6332576ea722a9ab49255cb0187851b22e4e9f4fb8e42f70dbbdc19eb723f051`,
game fingerprint
`7cc46243b1f430042632cb9b0e61fa82ea3f49d8f9dd56ae7fbbd6b36f4e1fb5`,
and the separately declared `ctm-startup-bg1-diagnostic/1` profile. The 90-second
worker, 1,000-primitive, 480-second client and 500-ms guardian limits remain.
No shared-desktop input, paid inference or campaign admission occurs.

| Attempt | Actual outcome | Preserved interpretation |
|---|---|---|
| operation-01 | Harness supplies settings fingerprint in the game domain; fails before worker admission, zero native intents | Typed startup failure; resources unchanged, server saves, Java zero, arguments retired; 404.516 s retained |
| operation-02 | Chest opens through scoped API; ordinary quick-move transfers three dust into player inventory. Harness then wrongly requires `completed` instead of the pinned Forge terminal `emitted` | Overall fail; transfer independently reconciled, not replayed. Two intents, eight charged primitives/seven usage records, twelve CLI calls; 514.437 s retained |
| operation-03 | Client joins, but worker misses the fixed 2,250 ms bootstrap bound before any gateway or action | Fail; zero native intents, entire player inventory unchanged, three dust retained, furnace empty/20,000 RF; 417.546 s retained |

In operation-02 the client readiness checks pass in 242.079 s with no startup
read failures, and the private world frame is captured. The receipt for the
transfer is terminal `emitted`, with release confirmed and no resync required.
`GameActionLane.tick` deliberately uses that status after its motor finishes;
it never promises authoritative game effects merely from a receipt.

After the server saves normally, independent NBT comparison proves that the
chest is empty and the **entire player inventory differs only by three plain
iron-dust items**. The furnace remains empty with its original 20,000 RF.
Both action IDs are unique and terminal, the native journal hash chain is valid,
and all eight primitives reconcile with the worker's durable usage counters.
This proves the narrow container transfer; it does not prove furnace operation.

Operation-02 also retains a genuine guardian failure: root wait **505.7315 ms**
against the unchanged 500 ms bound (507.0024 ms from overall timing start).
Tree proof does not begin, and the supervisor exits one. Eventual terminal
cleanup, normal server save, unchanged input desktop, zero Java and argument
retirement do not turn that failure into a pass. Earlier failures remain.

Four synthetic harness controls use the actual saved receipt shape: `emitted`
is accepted as terminal local input, `unknown` rejects, an unchanged open window
does not pass close, and an observed closed window can pass that local check.
The fresh continuation additionally checks pickup cursor contents and public
processing/output state, then requires independent final server/player evidence.
It resumes the current saved state and preserves both prior attempts' elapsed
time, resources and charges; it does not restore or replenish the fixture.

Operation-03 reaches native world readiness in 236.860 s with no read failures.
The supervisor records only worker start, `WORKER_BOOT_TIMEOUT` and forced exit;
the journal chain verifies. No gateway grant or action database is created, and
the native action journal has zero intents. Independent saved-state inspection
confirms the empty chest, unchanged full player inventory with three dust, and
empty furnace with 20,000 RF. Normal server save, outer-owner client termination,
argument retirement, unchanged input desktop and zero remaining Java processes
pass the cleanup audit. The diagnostic observer ended before the outer stop and
correctly reports no exit; no guardian was attached, so this is not a guardian
qualification result. Raw client log and selected immutable final region are
retained. No action is replayed. The next attempt requires a concrete startup
change and relevant checks; [schema startup work](2026-09-20-worker-schema-startup.md)
does not itself pass authentic timing or the machine gate.

Raw plans, scoped requests/responses, journals, saved references, logs and audits
remain private under
`C:\Users\Darian\.strata\evidence\2026-09-20-machine-reference-01`.
No bearer descriptor or launch argument file is published. Full expert crafting,
machine energy supply/fluid/routing, negative scorer controls, reference/UI parity,
native host isolation/accounting and every remaining M0–M6 gate stay open.
