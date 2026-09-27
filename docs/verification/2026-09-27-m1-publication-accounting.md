# Repair publication accounting boundary — September 27

M1.1c.3.4 remains `in_progress`. This fixes one reproduced resume defect; M1 and
all six aggregate G1 suites remain incomplete. No Minecraft or inference run was
performed, and the retained native-health failure is unchanged.

The worker previously checked primitive consumption before its final asynchronous
observation. That observation could discover another charge, yet publication still
released the gameplay hold against the old measurement. A second negative case
showed that unchanged totals could conceal changed native-source attribution.
Both tests failed with "Missing expected rejection" before the fix.

[Journal publication](../../backends/mineflayer/src/journal.ts) now validates the
original owned hold and worker clock, measured receipt, exact total and per-source
counts in the same SQLite transaction that saves the publication observation.
The immutable private `WorkerControlPublicationCommit/1` event stores the actual
boundary, clock identity and measurement digest. There is no new public tool,
wire schema, privilege, lease or spending authorization. Existing historical
publication events remain historical; they do not acquire this new witness.

A mismatch refuses publication and the existing worker abort path fences input.
Charges and the old measurement remain retained. A failure writing the boundary
rolls back publication and requires recovery. Later gameplay does not alter the
committed boundary. This is a worker primitive-accounting check, not complete
repair settlement, actual body clocks, inferred model usage or a qualification of
the supplied verification/settlement references.

Executed checks on Windows, Node 24.19.0, Python 3.12.14 and the existing Java
17.0.20.1+1 client fixture classpath:

- `npm run build`: pass, including generated validator consistency and TypeScript.
- `node --test dist/tests/worker_resume.test.js`: 20 passes after the two reproduced
  failures were fixed. The later added boundary-storage failure case was selected
  independently and passed: 21 distinct source test cases total. Native transport
  and game observations in these tests are synthetic.
- `pytest tests/test_controller_restart_jvm.py -k publish -q`: 1 pass, 6 deselected.
  Actual Python/controller, Node worker, Windows guardian and replacement JVM;
  synthetic game body, effect verification and settlement producer. The test joins
  the persisted publication boundary to the measured source counters and then
  executes the next scoped action, preserving the original receipt and boundary.
- `ruff check tests/test_controller_restart_jvm.py`: pass.

The initial added-test build failed because TypeScript correctly treated an
indexed source name as possibly undefined; the fixture now asserts its existence.
That failed build and both pre-fix behavioral failures are retained privately.
No production threshold changed and no unchanged paid/game suite was rerun.

Coverage: F06/F09/F11/F16, N01/N02/N03/N04/N08; the T01/T04/T05/T06 G1 dependency
tracked by M1.1c.3.4. Private evidence remains outside gameplay/helper contexts.
The live authority database, eight telemetry reservations and installed client/
options remained unchanged; the final audit and sealed bundle are recorded below.

Next work remains the connected gameplay/repair workflow: reconcile original
gameplay, repair body/model/helper costs and the full publication interval, complete
the original controller lease, then qualify actual effects and restoration on the
integrated runtime. The worker's `complete_repair_accounting` claim stays false.
The native-health failure, remaining isolation/scorer/probe cases and missing M1
paid-model authority remain explicit blockers to full G1 evidence.

Private evidence sealed:84 files/4,242,093 bytes,
SHA-256 `1b20009ffda21e3bb7ecb8cb5524b8902c1b94007cb684f45f912e341d85305c`.
All40 authority tables, eight telemetry holds and both installed-file hashes are
unchanged; final matching runtime process count0. All460 milestone IDs and2,159
local links were checked. This pointer postdates the archived source snapshot.
