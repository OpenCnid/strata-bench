# Continuous body ticks across repair — September 27

Private evidence sealed: 58 files / 4,293,003 bytes,
SHA-256 `61717c2c1283d35f92df46dd90635822ca0e47acf120672b776952939d849e85`.
All 40 authority tables, eight telemetry holds and two installed-file hashes
are unchanged; final matching runtime process count is 0. All 460 milestone IDs
and 2,188 local links were checked. This pointer postdates the archived snapshot.

M1.1c.3.4 remains `in_progress`; G1 and all six aggregate suites remain
`not_run`. Previous checkpoint: `c1d3055`, immutable publication evidence.

Repair-owned clock marks begin after the repair request. Their difference cannot
prove coverage of the earlier request/pause interval. The new private
`BodyTicks` service instead maintains one continuous tick window per campaign
epoch, beginning at an authenticated, held-source sample before a repair. This
origin is explicit; it is not a retroactive zero or a claim that earlier campaign
or provisioning work was covered.

All registered bodies require distinct, existing, owned tick-only reservations.
The same operations remain held through gameplay, repair, restart and publication.
Each source sample retains cumulative actual player-callback deltas from the
original origin, with the registered UUID-to-agent mapping. Per-operation budget
floors take the cumulative maximum, so duplicate notifications and overlapping
observations do not add charges. Unknown/settled, mixed-cost, foreign, reused or
incomplete-roster allocations refuse. A body operation cannot also fund a repair
tool, and a repair with an existing tick reservation or tick floor cannot claim
this separate allocation as if it had no overlapping charge.

The controller commits verified source bytes and observed consumption before the
separate CAS copy. A CAS failure leaves the real consumption retained; retry
repairs the copy without replay or double charge. Observed overruns remain above
the original reservation, and repeated reads cannot bypass their refusal.
The candidate is bounded to 128 samples per window and the existing private
source/record limits; it does not qualify indefinite monitoring or long soaks.

Repair coverage requires the window's durable opening before `repair.requested`,
the original admitted native body, and the stored typed controller publication
receipt. Only then is a causal source barrier requested. A strictly later
producer-acknowledged sample covers the publication end of the interval, while
the body operation also includes surrounding gameplay. The result deliberately
does not report an exact per-repair tick count or repost that continuous cost.
It does not settle any operation, grant campaign permission or certify complete
repair accounting. Active/reserved wall time, disconnected time, terminal tails,
complete controller completion and authentic profile qualification remain open.

Verification on Windows, Python 3.12.14 and Java 17.0.20.1+1:

- 15 new focused cases cover continuous allocation, CAS failure, duplicate reads,
  retained overruns, full roster/identity/exclusivity, pre-request origin,
  publication prerequisite, admitted body and causal closing sample.
- Together with the affected reconfiguration and budget/clock cases:
  `pytest tests/test_body_ticks.py tests/test_reconfiguration.py
  tests/test_budget_clocks.py -q --tb=short`: 51 passed in 7.17 seconds.
- `pytest tests/test_clock_barriers.py -k 'actual_jvm and body' -q --tb=short`:
  1 passed, 10 deselected in 2.05 seconds. Real Java callback counters, Windows
  held Job, private pipe, MAC/framing, durable broker and controller budget store
  advance from one measured tick to two. A one-tick reservation is exceeded;
  both ticks remain retained, replay stays refused and no tick moves to the
  repair tool. The other registered synthetic body has zero callbacks.
- Ruff and whitespace checks pass. Production Java and installed game files
  are unchanged. No Minecraft or paid model run occurred.

The initial source selection retained 14 passes and one failure. Its synthetic
closing health record claimed an acknowledgment equal to its own sequence; the
existing reader correctly rejected `TELEMETRY_CLOCK_MISMATCH`. The fixture now
adds a second post-request health/clock pair that can acknowledge the first.
No causal threshold, reservation or gate was relaxed.

The controller coverage tests use synthetic publication and native-body evidence.
The actual JVM/pipe case tests the continuous accounting path, not pre-request
repair coverage: its existing repair fixture predates the body window. Game/setup,
roster and pipe-token qualification remain synthetic. It proves no Minecraft,
N=2 capacity, isolation, complete repair or aggregate G1 outcome.

Coverage: M1.1c.3.4; F02/F06/F09/F11/F16, N01/N02/N03/N04/N08;
T01/T04/T05/T06/G1 dependency. Source: evaluator body-tick accounting,
repair-operation exclusivity and the focused/actual-pipe tests. Next connect
complete wall/disconnected-time allocation and original-lease controller
completion, then qualify the complete authentic gameplay/repair/resume path.
