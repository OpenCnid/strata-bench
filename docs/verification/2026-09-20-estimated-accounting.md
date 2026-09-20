# D11 versioned estimated usage

September 20, 2026. Operator-only. Source and synthetic verification for
M0.1c.1c.2a; parent M0.1c.1c.2 remains in progress. Coverage: F03/F11/F16,
N01/N02/N04/N06, C06/C12/C20, partial T01/T04/T07/T12, G0 items 1/6.
M0 is incomplete, G0 fails, and G1–G5 are not run.

## Implemented behavior

`ApiEquivalentEstimateBasis/1` pins Luna, source URLs/date, currency, a fixed
standard API reference tier, context threshold and limits, cache-write treatment,
reasoning inclusion, rounding and unsupported categories. This estimates
subscription usage at the declared API schedule. It does not identify the
subscription's service tier, invoice, quota conversion or immutable model weights.

The September 20 official [Luna model page](https://developers.openai.com/api/docs/models/gpt-5.6-luna)
and [price schedule](https://developers.openai.com/api/docs/pricing) give standard
short-context input/cache-read/cache-write/output rates of $0.20/$0.02/$0.25/$1.20
per million tokens; above 272,000 input tokens the entire request uses
$0.40/$0.04/$0.50/$1.80. The record pins these integer rates. Cache reads and
writes are disjoint input subsets; reasoning is included in output. Missing
cache-write telemetry conservatively prices all uncached input as writes.
Unknown token categories and hosted tool charges are unsupported and block.
Round up once per distinct request to whole micro-USD, never per token.

`UsageValuation/1` distinguishes API-equivalent estimates, actual charges and
synthetic fixture units. D11 dispatch accepts only the estimate kind with
matching raw token counters, basis and amount; it cannot relabel an estimate as
a reported monetary charge. The legacy `BudgetLedger/1` amount field retains
its wire name; `pricing_ref`, the authorization and durable valuation supply
its explicit semantics. Existing records are retained without repricing.

`InferenceDispatchBound/2` requires a typed finite exposure with profile-bound
private enforcement evidence. Timers and process kills are not accepted output
bounds. Conservative full-model maxima give $0.755400 equivalent per request;
smaller bounds need request-specific enforcement evidence. Arithmetic is tested;
actual OAuth enforcement/all-request ingress is still unqualified. The native
profile binds the accounting-basis digest, requires per-dispatch envelopes, and
caps each job in the initial stage at $1 within the original $10 aggregate.

The existing dispatch-intent, receipt deduplication, unknown-hold, restart and
nested-envelope implementation is reused. Four distinct synthetic root/helper/
retry/summary requests at 289 micro-USD each settle at 1,156 total after envelope
closure; the envelope is not an additional charge. Duplicate notifications do
not add usage. Invalid/missing valuation retains the reservation and blocks
further admission. Synthetic stores cannot migrate to live authority; migrated
live stores cannot be opened for simulated native dispatch.

A receipt exceeding its qualified token or spend exposure is still charged in
full. A durable exposure fault quarantines new requests and native jobs,
including after restart; settlement cannot erase the violation merely because
the monetary amount fits a larger envelope.

## Durable migration and observed baseline

Fetched `origin/main` matched PR #2 merge
`542a77ac760fb305b26941085e33447f392f8ba8`. Main and this new worktree were clean;
implementation uses `codex/strata-estimated-usage`. Earlier worktrees are retained.
Read-only process metadata found no Java game/server or Python experiment
process. No game or shared-desktop input was launched.

A fresh read-only inventory inspected known private operator/evidence/worker/host
SQLite stores: 97 accounting stores, 88 containing model/helper operations,
all 88 explicitly synthetic, and no installed execution authorization. D11's
user statement resolves experiments outside those roots. Synthetic unresolved
holds remain in their original stores; none was erased or treated as paid usage.

The existing private project store at
`C:/Users/Darian/.strata/operator/provisioning/controller.sqlite` contained
provisioning state and no spending authority. Installed the exact archived D04
record and explicitly migrated it in place to `ExecutionAuthorization/2`, with
the same `validation-2026-09-18` ID, parent account and 10,000,000-micro-USD cap.
The audit binds the store path, exact source authorization, accounting snapshot,
private inventory and D11 statement. This initializes the never-installed
original authority; it is not an additional allowance. Opening experimental
consumption is zero. Existing provisioning records are preserved.

Migration refuses missing/incompatible audits, changed snapshots, changed model,
provider, scope or allowance, synthetic profiles and fresh v2 installation.
The transaction preserves every account, operation, ledger receipt, envelope
and unknown hold byte-for-byte. A synthetic nonempty migration preserves
2,000,000 settled plus 3,000,000 unresolved micro-USD, including after restart.
Interrupted writes roll back. Repeating migration cannot reset usage.

Private evidence: `C:/Users/Darian/.strata/evidence/2026-09-20-estimated-accounting-01`
contains `inventory.json`, `migration-audit.json`, `migration-status.json` and
the operator journal. None belongs in public source or gameplay access.

## Verification and limits

Focused Python checks cover estimator arithmetic/unknowns, migration/races,
dispatch/deduplication/holds, envelopes, wire receipt parsing, native lifecycle
and operator commands. The initial combined run passed 114 tests. Two added
migration-audit checks and the new native basis guard exposed one stale proof
fixture (115 passed, 1 failed); that fixture was corrected. The affected
accounting/dispatch/native-proof run then passed 30 tests. The final overrun and
native/dispatch regression run passed 60 tests in 6.91 seconds. Ruff passes.
These are synthetic/source checks, not authentic OAuth or game qualification.

One affected pinned-CLI fixture was executed, without repeating the completed
accounting matrix:

```powershell
python tools/native_dispatch_probe.py --codex '<pinned codex.exe>' --output '<new private directory>' --wire --cases success --estimate-authorization configs/operator/live-validation.json
```

CLI `0.154.0-alpha.6.2`, executable SHA256
`960c111d47afd61669954b9df9e56083e302edbfa3ef6962d81dcc14a30051dc`, actual local
HTTP/SSE provider, no credentials or external inference. Result: pass. One
request with 10 input / 2 cached / 4 output tokens values at 7 micro-USD equivalent
on synthetic counts. Duplicate receipt deduplicates, no provider errors, exact
inventory seals, and the job finalizes after closure. No experimental subscription
usage is charged. Raw source pins/journals/requests remain under
`C:/Users/Darian/.strata/evidence/2026-09-20-estimated-accounting-native-01`.

Next: qualify the smallest enforceable native tool/helper boundary and actual
OAuth ingress before a first trial of at most $1. Do not dispatch based on a
budget status alone. Preserve all earlier loopback-canary, 500-ms shutdown,
effective-file and Mineflayer/E9E failures, scorer provenance and recovery gaps.
