# M1.5b.3e private preflight comparison diagnosis

From8f0a719, operation03 preserves unknown/resync REVISION_CONFLICT before deposit
input. Its two charged events are the fixed read and release; no exact failing
comparison was retained. Add bounded private evidence for this missing seam,
inheriting M1.5b.3d F/N/C/T mappings plus N04/T06 for log isolation. D20 permits
implementation; no paid M1 inference or unrelated roadmap work is selected.

GameMachinePreflightFailure retains the original IOException message/cause and
adds only fixed machine-preflight-comparison-masks/1 diagnostic fields. Phases:
context, reply, wait, reply_layout, input_fence, current_view, current_layout,
current_match, selection_match, final_baseline, transfer_start. A transfer_start
failure is not itself proof of no click; retain the actual primitive journal.

For current_match, expected is the server reply and actual is current state.
For selection_match, expected is initial local state and actual is server reply.
For final_baseline, expected is the frozen server baseline and actual is the last
already-required validateClick view. Other phases have comparison:null; no extra
game read supplies missing evidence. Masks distinguish IDs/counts/components for
cursor/player slots (cursor bit0, player-relative0–35 at bits1–36) and visible
machine base slots (zero-based bit indices). Selected-slot flags report each
of those three differences. No hidden augment reads, item IDs, components, hashes,
values, credentials or arbitrary exception text enter the diagnostic.

GameMachinePreflight separates existing comparisons without changing their
order or outcome. GameMachineInventory preserves the final exact baseline read
and comparison. GameActionLane publishes through the existing native operator
logger only after original fencing/release/durable terminal handling. Sink
failure is ignored for receipt authority; failed release still controls the
public error. The private receipt contains no diagnostic fields. No added
refresh, mutation, retry, accepted state, deadline, budget or public capability.
The new artifact still forms its own native identity; no old conformance transfers.

Executed offline pinned Java17/Forge Gradle selection and reobfuscated jar:
GameMachinePreflightFailureTest4, GameMachinePreflightTest11,
GameMachineMismatchTest8, GameMachineInventoryTest18, GameActionLaneTest20.
All61 cases pass, zero failure/error/skip; build26s. New cases exercise all11
phases, original error preservation/read and click counts, all37 owned positions,
machine/hidden-slot separation, selected flags, component-only drift, bounded
value-free/copy-safe JSON, terminal-before-publication, sink failure, release
precedence and duplicate no-replay. These are synthetic ports and real lane
logic, not authentic native diagnostic qualification. Unchanged TypeScript/Python
suites were not repeated; their public contracts are unchanged.

Candidate622,975bytes, SHA
1d4935ed77a265842945f37a1dc0c2aee8a31c3fba68299182dedb8bbffefdea.
Installed client remains5fbb4eca32808f721ff1be981447e99ff1410621b35b3c9eded4c2625c754bb4.
Private archive2026-09-26-m1-preflight-diagnostic-source-01. Entry accounting:
all40 controller tables unchanged, exposure$4.887796 and original holds intact.
No game/model dispatch or shared-desktop input. Original operation01/02/03
failures remain consumed and unchanged. Next one fresh changed-artifact reference
for the missing private diagnostic; do not guess operation03's cause or weaken
confirmation. Full M1/G1 requirements and unrelated M2–M7 scope remain intact.

Final integrity audit passes500 source pins,445 unique milestone IDs and1,819
local links, preserving earlier history and all40 authority tables at$4.887796.
Private source/test/build archive2026-09-26-m1-preflight-diagnostic-source-01:
29files/2,835,191bytes, seal
b54aa40a4c57ca6e8abe1e4d6a4b8615ca355e964dfd7eb102de9d77807ba18b.
Exact bundle verifies. This pointer follows the archived documentation snapshot.
Installed client unchanged; authentic diagnostic integration and G1 not_run.
