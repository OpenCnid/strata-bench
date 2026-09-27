# Controller retrieval of the publication boundary — September 27

Private evidence sealed: 151 files / 6,305,414 bytes,
SHA-256 `96e14ce9f863bd9e6f4796685e03cc16c72e177710b76a1deda02d20a2c179fe`.
All 40 authority tables, eight telemetry holds and two installed-file hashes
are unchanged; final matching runtime process count is 0. All 460 milestone IDs
and 2,182 local links were checked. This pointer postdates the archived snapshot.

M1.1c.3.4 remains `in_progress`; G1 and all six aggregate suites remain
`not_run`. This continues the committed inference integration at `b483f4d`.

The existing worker publication commit was previously available only through its
private SQLite journal. The controller's status response contained a cumulative
counter that could include subsequent gameplay. It could not use that moving
counter to establish the historical repair boundary.

The private publication endpoint now accepts
`WorkerPublicationAccountingRequest/1`, under the same operator credential and
strict request limits. It reads the original measurement and exactly one stored
`WorkerControlPublicationCommit/1`. Missing or duplicate commits, changed
decisions, observations, source counters, clock identities or measurement joins
refuse. It neither invokes native input nor reads current counters to reconstruct
history. Historical reads after stop do not confer current permission.

The strict Python consumer validates the complete decision, observation, original
worker plan, measurement digest, clock, source allocation and boundary ordering.
`NativeRepairResume.capture_publication` joins this receipt to the owned repair,
confirmed resume, existing measurement, committed keymap and frozen inference
audit. It stores one immutable private reference and rechecks inference within
the final writer transaction. Repeated reads preserve that reference. Full
accounting, budget settlement and campaign permission remain explicitly false.
The supplied settlement reference is bound to the original decision; this read
does not certify that its producer has performed complete settlement.

Executed on Windows with Python 3.12.14, Node 24.19.0 and Java 17.0.20.1+1:

- 55 focused Python cases pass across publication validation, resume evidence and
  consumption floors. Twelve new substitution/false-claim cases and one exact
  decision-binding case cover the new reader. The eight resume tests also pass
  after adding an explicit existing-writer-transaction check.
- TypeScript build passes; the selected `worker_resume` file passes 23 cases,
  including historical boundary stability after later usage and stop, missing/
  duplicate records, foreign scope, exact decision binding, private endpoint
  credentials, origin and unknown-field refusal. Existing publication fault
  cases remain covered.
- The selected actual Python controller → Node worker → Windows guardian →
  replacement JVM publication case passes (1 passed, 6 deselected). It retrieves
  the boundary through the real HTTP endpoint, matches the private journal,
  injects a failed controller evidence store without completing the repair,
  captures one reference, then verifies that subsequent gameplay leaves both
  the worker receipt and controller reference unchanged. Controller input
  authority stays suspended and the original repair reservation stays held.
- Ruff and whitespace checks pass. No production Java or installed game file
  changes, Minecraft launch, paid inference or spending-authority extension.

Retained failures: the first Python run had 53 passes and two failures because
the new fixture independently generated time-sensitive resume decisions for its
measurement and publication. They now share one decision identity. The first
process attempt failed when the new final transaction called an audit that tried
to open another transaction. The fix uses the existing transaction-aware audit;
the failed attempt is retained alongside the corrected 10.63-second passing run.
No deadline, reservation, native-health threshold or acceptance gate changed.

Process lifecycle, transport and persistence are real; game body, helper usage,
effect verification and settlement producer remain synthetic. These results do
not prove authentic Minecraft behavior, complete repair accounting, helper
isolation or T05/G1 qualification. The pre-pause/request interval, complete body
allocation, original-lease controller completion, restored rollback and native
health failure remain open, as do the remaining G1 contracts/scorer/probe cases.

Coverage: M1.1c.3.4; F03/F06/F09/F11/F16, N01/N02/N03/N04/N08;
T01/T04/T05/T06 G1 dependency. Source: private worker journal/lane/publication
endpoint and Python publication/controller readers; focused and process tests.
Next: join complete consumption allocation to controller completion without
using this historical receipt as current authority or a full settlement.
