# M1.6r.2 private player-body callback observer

Status: **implemented_unverified** for authentic live capture. M1.6r remains
in_progress and G1 remains not_run. Existing clock and native11 identities are
unchanged. No game, model, new paid reservation or probe was dispatched.

[BodyAgent](../../evaluator/java/livebody/BodyAgent.java) supplies distinct exact
official 1.19.2 instrumentation. The implementation JAR is pinned to
`d79def2f9aaf06d6b851e568150762b8e7ee24a898a314cf34b210cbd9ea14b6`.
Every loaded class listed in that JAR must match its original bytes and source
path, use one game loader and have no duplicate definition. Exact server/player
methods receive receiver-preserving callbacks. Attach is disabled and additional
Java/native/bootstrap agents are refused. Changed bytes, paths or loader identity
halt the JVM; an ignored transformer exception cannot permit unobserved play.

[BodyObserver](../../evaluator/java/livebody/BodyObserver.java) verifies the
actual game caller class/method/descriptor/loader and receiver. It binds a bounded
configuration digest, module, server, PID, scope, sequence and monotonic time.
[RosterCapture](../../evaluator/java/livebody/RosterCapture.java) accepts one
initial capture only when all declared players appear within the same server
tick. Partial rosters cannot accumulate across ticks. Initial duplicate/foreign
UUIDs, replaced players, wrong server/thread, invalid order and incomplete stop
refuse. After capture, player references are released and ordinary respawn does
not become an infrastructure failure or cause recapture.

The R1 codec preserves all emitted save-format NBT in private create-once files,
with a committed capture record only after all members write and flush. Per-body
and aggregate limits are 16 MiB and 64 MiB; the declared profile supports at most
64 members and must refuse excess capacity without reducing the roster. Journal
limits are 128 records/1 MiB; callback processing caps at one million ticks.
The final class inventory closes before the stop record. Late game definitions
invalidate the process. These limits are not measured capacity certificates.

[Offline builder](../../evaluator/src/strata_evaluator/player_body_agent.py)
retains compiler/source/ASM pins and separates bootstrap-visible callbacks from
the transformer. It adds no launch, gameplay tool, native catalog or admission
path. The old clock agent cannot be combined with this observer or used as its
conformance evidence.

Nine focused checks pass on the final candidate in 7.66 seconds:

- Synthetic complete/partial/multiple-tick roster cases, sticky lifecycle and
  identity/thread failures, capacity limits, one-shot capture and later respawn.
- An actual JVM with the new agent loads and verifies the transformed official
  server/player methods without initializing Minecraft; callbacks resolve from
  bootstrap under the game's platform-parent loader arrangement.
- Actual JVM rejection of forged callbacks, changed class bytes, foreign code
  source, duplicate loader, absent attach protection, noncanonical roster UUIDs
  and oversized configuration. Refusals create no player capture.

The first five-case run and subsequent seven-case runs are retained. New source
reviews closed a class-inventory snapshot race, preserved post-capture respawn,
and bounded/digest-bound configuration reads; the final nine-case run uses the
resulting candidate. No failing game trial or lucky rerun is involved. A no-op
README patch failed its context match without modifying a file; the actual
documentation addition then succeeded. Ruff and whitespace checks pass.

Executed focused command with pinned local JDK17, ASM9.7.1 and official server
environment paths:

```powershell
$env:PYTHONPATH='src;tools;evaluator/src'
python -m pytest tests/test_player_body_agent.py -q
ruff check evaluator/src/strata_evaluator/player_body_agent.py tests/test_player_body_agent.py
git diff --check
```

These checks prove transformed-method verification and named refusal paths,
not authentic server execution, valid live callbacks or a complete snapshot.
Owned launch/exit and immutable configuration/runtime/path custody, independent
stopped-output inspection, real UUID/thread/capture behavior, capture overhead
and mechanics parity remain required. Java path checks do not establish Windows
ACL/reparse isolation. The saved NBT format still omits transient state and has
the retained signed-zero limitation. Whole-body matching, tool/budget parity,
all-N admission, campaign clocks, disposal and full T11/G1 remain open. Native
probe catalogs stay closed. No runtime qualification is issued.

Private evidence root:
`C:/Users/Darian/.strata/evidence/2026-09-25-m1-live-body-callback-01`.

Final audit: 454 source pins, all 430 milestone IDs, append-only history and
1,706 local documentation links pass. All 40 real authority tables remain
unchanged at $4.887796 exposure and no owned runtime remains. The final private
JAR is 143,995 bytes, SHA-256
`999ad44d16b5d6255963c3571e70842ec4c4c642f28d993665c513671855cba6`.
The eight actual JVM cases exit as expected: one normal method verification,
four exit-126 producer refusals and three exit-1 preflight refusals. Validly
configured cases contain only the initial journal header; none contains player
NBT, a capture record or a terminal body-witness record.

The private archive is sealed and independently verified: 230 files, 3,158,224
bytes, SHA-256
`60a824ed3aa2169df716fd34c4d449b7e6ba982bbfb9124fd0b12927335fa1eb`.
This pointer follows the archived documentation snapshot.
