# Causal clock boundary for an owned repair

M1.1c.3.4 now records a durable repair clock request and verifies that a later
server sample was generated after that request. The existing native telemetry
protocol supplies the causal signal; no new command channel, module identity,
installation or inference run is needed. Full repair settlement and G1 remain open.

## Why the existing receipt proves the ordering

The production pipe broker signs/fsyncs each event, commits its durable cursor
with SQLite `BEGIN IMMEDIATE`, then sends its sequence/hash receipt. The Java
`PipeTelemetry` validates that receipt before `EventSpool` advances its volatile
durable cursor. On the server owner thread, health captures that cursor before
the immediately adjacent complete callback-clock sample is generated.

`BoundClockSource.begin_barrier` records a request while holding the same SQLite
writer lock used by the broker. It reads the committed cursor under that lock and
persists the original source/boot, scope, threshold and finite deadline. A sample
must report a producer-acknowledged cursor strictly greater than this threshold.
That newer cursor could only have committed, been acknowledged, and been observed
by the producer after the request transaction. Equal, stale, future or non-pipe
receipts cannot establish this ordering. This replaces the earlier proposal to
send a new single-use marker; it preserves the required causal guarantee using
already implemented protocol behavior.

Requests are immutable and bounded (512 per source, 32 per repair). Retries keep
the original threshold/deadline, even after later telemetry or a failed controller
CAS write. Waiting for a database writer cannot renew the supplied time window.
The broker retains the latest durable clock-sample cursor, allowing a nonblocking
completion check. An unavailable sample remains pending; no process restart,
input dispatch, reservation refund or request renewal follows from that result.

`RepairClockEvidence.request_barrier` binds the request to the original repair,
controller clock/owner/epoch, worker plan, registered roster and reserved budget.
`capture` consumes the authenticated source, actual native body join and requested
boundary, retaining `RepairClockWitness/2` with
`sample_generation_after_request_proven=true`. Its existing read-freshness,
complete-accounting, settlement and campaign-permission claims remain false.
The ordinary `/1` receipt path and historical evidence remain unchanged.

## Executed verification

Environment: Windows, Python3.12.14, Java17.0.20.1+1; unchanged production telemetry
0.3.19/ServerStarted20. Only the test Java fixture was added/compiled. The existing
CodexSandboxUsers local group was selected explicitly; no accounts/groups changed.

- `pytest tests/test_clock_barriers.py tests/test_bound_clocks.py tests/test_live_clocks.py -q`
  with explicit Java/classpath/group environment: **43 passed**, including actual
  JVM and pipe cases. Ruff and `git diff --check` pass.
- New controller/source cases verify strict receipt ordering, immutable retry,
  changed scope/request refusal, non-pipe/future receipt rejection, expiration
  before/during read, no deadline extension during a delayed source read, actual
  SQLite writer-lock ordering, and recovery after a simulated controller CAS
  failure without replacing the already durable request. Budget/input holds persist. A final focused controller check (1 pass/8 deselected)
  also rejects a valid request reference substituted from a different mark.
- Actual `CausalClockFixture` uses production `EventSpool`, `PipeTelemetry`,
  `LaunchIdentity` and `ServerClock`, a real Windows named pipe, the Python broker,
  actual fsync/SQLite state, and the original held JVM process. At request cursor1,
  sample cursor3 with producer receipt1 is refused. Sample cursor5 with producer
  receipt3 is accepted while the same process is alive. The process exits0 and the
  broker records normal stopped state. Game/setup data and server callbacks are
  synthetic; the test explicitly bypasses restricted-token qualification. This
  does not qualify Minecraft, gameplay isolation or the final integrated profile.
- Initial run:8 passed/1 failed before Java launch because the operator supplied
  the builtin Windows Users group. The existing principal gate correctly refused
  it (`WRITER_DISTINCT_USER_REQUIRED`). The corrected existing sandbox-group run
  passed1/8 deselected. The failure log is retained; no boundary was weakened.
- Offline `:forge1192-telemetry:writeTestClasspath` succeeded. Production Java
  classes/resources were up-to-date; no new production JAR was installed.

Private evidence: `C:/Users/Darian/.strata/evidence/2026-09-27-m1-repair-clock-barrier-01`.

## Remaining workflow

An after-request sample is a conservative causal boundary, not a sample exactly
at the repair transition or fresh at any later read. Complete consumption still
requires continuous, nonoverlapping prior-gameplay/repair allocation, every body
and model/helper cost, and the publication tail before original-lease resume.
Do not infer zero costs or avatar ticks from absent sources. The native-health
failure, essential-control/qualification producer, public skill, rollback and
repeated-repair workflow remain unresolved. M1 stays `in_progress` and all six
G1 suites plus G1 stay `not_run`. Coverage: F06/F09/F11/F16,
N01/N02/N03/N04/N06/N08; T01/T04/T05/T06 and necessary T12 dependencies.

## Evidence preservation

The private evidence bundle verifies:52files/2,691,898bytes,
SHA-256 `7c3db279f9a2882616614499ed348f60db8ff169f041a3a029b43bd5ae942fc7`. It includes the actual pipe stream, fresh fixture authority,
WAL-aware database backup, process receipt, test/build/failure logs, source snapshot
and classpath pins. All40 authority tables/eight holds and installed client/options
are unchanged; all460 milestone IDs remain and2,147 local links resolve. Final
runtime inventory0. This public pointer postdates the archived document snapshot.
