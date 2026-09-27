# Same-worker repair resume through a replacement client

M1.1c.3.4 now connects the native resume decision to the existing worker and its
replacement process guardian. This is a manual conformance candidate with a
synthetic game body. Controller completion, public keymap/skill integration and
authentic Minecraft qualification remain required. No complete G1 suite closes.

## Runtime behavior

`ForgeDevelopmentWorker/5` explicitly adds
`resume_policy: operator-owned-settings-resume/1`. It retains the repair and
restart policies and publishes a separate private `WorkerResumeGrant/1`, bound
to both existing private grants. The public gameplay grant and capability
catalog do not acquire native settings or resume operations. Older worker
profiles retain their existing behavior.

Replacement clients use `ForgeProcessGuardGrant/4`. Before resume, the guardian
requires the exact prepared replacement checkpoint and a live, fenced repair.
After resume, it reads the native receipt and checks the original full worker
plan, replacement instance, generation, epoch and primitive limit. Further reads
must retain the identical consumed decision. A stale, foreign, stopped or
reopened receipt cannot authorize input. The 750 ms health policy, 1,000 ms
Java-tree stop policy and original process/worker lifetime bounds are unchanged.
Guardian/3 still requires input to remain fenced.

The worker durably records one resume intent before dispatch. A duplicate call
or uncertain native reply uses status; it never sends another resume mutation.
The native receipt must match the entire intent. The worker retains its epoch,
lease identity, action sequences, receipts and primitive high-water counters.
It clears old observation deliveries and obtains a fresh observation before
recording completion and opening its public action lane. Its monotonic resume
deadline is captured before I/O and cannot be refreshed by reconciliation.

The additive `repair_resumes` table preserves consumed intents and receipts;
historical `repair_holds` are retained. An unfinished intent or recovery hold
still prevents reopening through a new executor epoch. Journal completion
failure stops native input. A concurrent stop prevents a late resume response
from opening the worker. Closing drains the outstanding resume task before
disposing of the journal. Completed status reads retain native consumption.

The Python `WorkerResumeClient` checks strict grant/receipt schemas, both private
transport bindings, the full decision, avatar scope, observation and consumption.
It sends one POST and reports uncertain outcomes without replay. Its receipt
does not itself settle controller budgets or publish campaign permission.

## Verification and limitations

Actual Python → Node worker → Windows guardian → replacement JVM tests exercise
commit/resume, rollback/resume and a lost worker reply recovered by status. They
use the same executor and epoch, preserve the pre-repair action receipt, and
execute the next scoped CLI action after resume. Native and public receipts
report `emitted` with confirmed release; the synthetic body changes yaw. Both
Java processes become terminal. These are production process/transport paths,
but the game body, settings qualification and verification decision are synthetic.

Focused negative tests cover foreign/inactive native receipts, unchanged legacy
replacement fencing, strict worker proof/grant validation, public-token/browser
refusal, durable-write failures, native reply loss and stop/resume races. No
Minecraft or model run was launched, and the installed game JAR was not changed.

Executed results: three final worker resume/history process cases pass; the two
unchanged legacy replacement cases and 39 guardian checks pass in the connected
run. The 22 new worker consumer cases and 34 existing restart consumer cases
pass. Six worker resume journal/HTTP/race cases and seven shared Node repair/
restart cases pass. The Node build, Java test-class compilation and Ruff pass.
The initial guardian-only run skipped four Windows cases without its explicit
environment; the connected run subsequently executed all four. These counts
describe the listed checks, not accepted G1 requirements.

Initial connected tests retained a `CAPABILITY_MISSING` refusal because the
settings fixture lacked gameplay observations. Its test-only runtime now has an
explicit synthetic observation/action surface. Later failed assertions used
`completed` where the declared native/public action contract uses `emitted`;
those logs remain retained. The test now checks actual emission, release and
body change. Initial Node cleanup ordering, a test syntax error and an invalid
synthetic observation-age fixture were also corrected, with failures retained.

## Remaining acceptance work

`Reconfigurations.finish` still refuses worker-backed repairs with
`REPAIR_WORKER_RESUME_REQUIRED`. Its generic path creates a new lease, whereas
this worker correctly retains the original lease. Join controller verification,
complete consumption settlement, fresh observation and permission publication
to this actual receipt before claiming campaign repair/resume.

The public keymap/control card and selected skill remain unfinished. Current
Forge observations retain the structured-action epoch revision and null keymap;
they are not yet the qualified settings observation required by controller
completion. The adapter qualification issuer and complete effect/context/failure
matrix also remain open. The replacement owner currently represents one repair
chain; repeated repairs need explicit lifecycle handling, not cleared history.

Preserve essential-native04's real health failure. This candidate has not
resolved or rerun it. Full T01/T04/T05/T06/T10/T11 and G1 remain `not_run`.

Private evidence bundle `2026-09-27-m1-worker-resume-01` is sealed:47 files,
2,800,647 bytes, SHA-256
`9d903789ce04219cbc6e77dc93b58ec81bf03930901cca62301e6b998f0bc79c`.
It preserves changed source, original failed/passing logs, compiled hashes and
read-only authority/hold audits. All40 authority tables and eight holds match
before/after. Installed JAR/options are unchanged; no owned runtime remains.
All460 ledger IDs survive and2,109 local links in the five reviewed documents
resolve. This is a candidate component checkpoint, not a G1 pass.
