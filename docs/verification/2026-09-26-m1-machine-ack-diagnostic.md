# M1.5b.3c private machine acknowledgment diagnosis

From8f3b97a, the failed operation01 proves real native completions but retains
an unknown/resync deposit receipt. Its exact at-failure owned-state mismatch
is absent. M1.5b.3c inherits M1.5b.3b plus F06/N02/T03/T07 for the impacted
action confirmation boundary; unrelated M2-G2 recovery work is not selected.

Record fixed difference masks for the already-read before/predicted/received/
current owned state. Bit0 is cursor; bits1-36 are player slots relative to the
menu's player inventory. Separate item-ID, count and component-equality masks;
no values, hashes, paths, credentials or arbitrary exception text. Exclude
machine storage/hidden slots. Publish through the operator logger after existing
fence/release/terminal handling; no extra game read, click, refresh, retry or
acceptance change. Missing diagnostics cannot repair an unknown receipt.

Implementation/verification pending. All40 real authority tables unchanged at
$4.887796; original holds, failures and consumed decisions remain. No new game
or model dispatch selected. Full M1/G1 remains open.

## Source and executed verification

GameMachineMismatch carries only fixed masks; GameMachineInventory reuses its
existing views at both failure sites. It preserves the same error code and exact
owned-state comparisons. GameActionLane captures the request identity, performs
its existing fence/release/durable terminal handling, then calls the private
runtime diagnostic hook. NativeGameRuntime uses the normal Forge logger with
STRATA_PRIVATE_MACHINE_ACK_DIAGNOSTIC. No new public endpoint or receipt field.
Output exceptions cannot change the stored receipt; failed input release still
replaces the original error with GAME_RELEASE_UNCONFIRMED. Missing output is not
proof that no mismatch occurred. Native log integration remains unverified.

Executed offline Gradle selections with the pinned Java17 compiler and installed
FTB library (no dependency installation):

- Initial GameMachineMismatchTest/GameMachineInventoryTest/GameMenuFeedbackTest/
  GameActionLaneTest:48 cases,47 pass and1 fails because the new nested temporary
  directories were not created. Failure occurs before the lane opens. Preserve
  original source/XML/log. Production compile and reobfuscated artifact complete.
- Corrected diagnostic selection plus explicit success/no-diagnostic check:
  seven pass; build succeeds17s. Prior42 unaffected lane/inventory/feedback
  cases are not repeated. Both failure branches, all37 owned mask positions,
  separate ID/count/component masks, value exclusion, private-copy semantics,
  machine/hidden-slot exclusion, one pre-click refresh, sink failure, terminal
  publication and duplicate no-replay behavior are checked.
- Added release-failure case initially fails because its test expects the
  earlier transfer error in the terminal journal. Existing release precedence
  correctly records GAME_RELEASE_UNCONFIRMED. Corrected assertion verifies the
  actual final code and release_confirmed=false; targeted case passes14s.
  Production code is unchanged by either test correction.

Total50 distinct passing cases (42 existing plus8 diagnostic); no skipped cases
in those selections. Original failures remain. No authentic Minecraft or model
run was selected in this increment. The built candidate is615,239bytes with SHA
 d0e30db07a821dde0917ecea424c60b7e350060dc2499a506b3b77bf72a0b171.
The installed client remains612,038bytes, SHA
 54568cb131ad22dac9bb078ddf3e5f8c2f4f33ba746f3fce4cec60edea0d3ff9.
The candidate has not replaced the installed client or inherited its evidence.
Private evidence root2026-09-26-m1-machine-ack-diagnostic-01.

Next use a fresh scoped reference with the changed native artifact and retain
its operator log before another client overwrites it. Inspect the diagnostic
instead of inferring confirmation from later machine output. Keep operation01's
unknown receipt and all original costs/holds/consumed state. Native effect,
log secrecy, installation/profile binding and actual mismatch cause stay open;
no G1 or broad reliability claim follows these synthetic checks.

Final integrity audit passes492 source pins,443 unique milestone IDs and1,797
local links, preserving previous progress and all40 authority tables at$4.887796.
Private source/build/test archive2026-09-26-m1-machine-ack-diagnostic-01:
48files/2,938,735bytes, seal
7ba6a132287b7c1bc720858b8ddecbd3b04638bcbd0fc1750252556522f1607e.
Exact bundle verifies. This pointer follows the archived documentation snapshot.
Installed client unchanged; authentic diagnostic integration and full G1 not_run.
