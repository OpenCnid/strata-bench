# Vanilla cancellation/reconnect development

2026-09-20. M0.2b/M0.2d/M0.2k; F06/F09/F16, N01/N02/N03/N04,
T03/T07/T12, G0 item 4. The selected vanilla cancel/reconnect trajectory passes independent audit; full T07/G0 remain incomplete.

The existing vanilla mechanics world and terminal action journal continue without
reset or resource replenishment. The copied journal retains all three prior
receipts and 37 primitives; earlier independent mechanics attempts remain in their
original accounting. Microsoft authentication uses the existing protected account.
No inference or desktop input is used. Original evidence is outside the repository.

Phases 01/02 (epochs 6/7) both authenticate, then reject the requested walk with
PATH_BLOCKED before any primitive input. The checker therefore cannot claim an
in-flight cancellation. Their failed receipts and 74.062/74.344 s remain; journal
primitive count stays 37. Both stop normally with complete worker logs. The first
checker had not delivered the complete nearby map; the second delivered all pages.
No original receipt or journal row was dropped between phases.

An offline reproduction using only phase 02's delivered public block IDs exposes
a cache defect: the 2203-cell page sequence evicts a required nearby floor cell
from the 1024-cell cache. The pinned planner reports PATH_BLOCKED. Redelivering
the already-known nearest 512 cells restores the exact three-cell route, with no
new world reads. This is diagnostic evidence, not an authentic movement pass.

Vanilla minor 10 implements nearest-eye retention within the unchanged 1024-cell
limit, with a deterministic coordinate tie break. Only delivered cells enter the
map; reset clears the anchor/dimension binding, and stale-page overwrite rules
remain. TypeScript build and six focused navigation/pagination checks pass. Replaying the
same delivered public pages now yields the three-cell route without redelivering
nearby cells or reading the world.

Private evidence: `C:\Users\Darian\.strata\evidence\2026-09-20-vanilla-reconnect-01`.
The initial preparation stopped before copying a journal because its old WAL file
existed at zero bytes. A read-only SQLite backup then retained all rows and source
bytes. An unexecuted checker attribute typo was corrected before phase 01. These
preparation corrections are retained and are not game samples.

## Authentic result and retained checker failure

Phase 03 (epoch 8, vanilla minor 10) uses the same target and tolerance as phase 02.
The avatar moves; cancellation confirms local release after 23 primitives, fences
the connection and requires a new epoch. Its raw checker reports fail because it
incorrectly asserted that cancellation would not require resynchronization.
That report and exact checker are retained. The implementation's documented
conservative disconnect behavior remains unchanged; no failed sample is erased.

Phase 04 (epoch 9) passes the public sequence after restart with the complete prior
journal. It reads the original terminal cancelled receipt, obtains that same
receipt through known-ID deduplication, rejects a new stale-epoch request and
executes one fresh look action at action sequence 1. The old movement is not
re-emitted. Both client workers and servers stop normally with complete logs.

The independent saved-player/journal audit passes: all four phases preserve full
inventory NBT, saved player bytes connect each stop to the next start, the new
public position equals the preceding saved server position exactly, and looking
does not move the body. The cancelled motion changed saved x/z by approximately
0.607/-0.156 blocks. Every prior receipt and event prefix is retained byte-for-byte;
no counter decreases. Exactly one new intent exists per epoch 6–9, including the
two failed zero-emission walks. The journal totals 61 primitives: 37 inherited,
23 from cancelled movement and 1 new look. All four attempts retain 297.156 s.
Raw checker results remain fail/fail/fail/pass; the independent audit evaluates
the actual cancellation/resynchronization contract, not the erroneous no-fence
expectation. Its SHA256 is
`fbd66dd80f038469f82ebe53faf869bee54418c817a886b3bbd8e734a60636da`.

Observed implementation digest:
`0832428e4ebea74c965552103d71b9fd8482e3cecdfa2e397be59cb127bf0a94`;
dependency lock:
`e6832954bcdc7fe2380ec284b1d20c558d05c5678387639a5e52649e372f1e79`.
The authentic vanilla 1.19.2 server, Java/Node/Mineflayer pins are those of the
[mechanics sequence](2026-09-20-vanilla-mechanics.md). No model inference, shared
input, world reset or resource refill occurred. This is a narrow N=1 vanilla
result; Forge reconnect, ambiguous crash recovery, full agent/game checkpoint
sets, isolation and unchanged guardian/soak requirements remain open.
