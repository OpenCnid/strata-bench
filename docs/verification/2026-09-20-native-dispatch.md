# Native CLI synthetic dispatch integration

Operator-only. M0.1c.1b is **implemented_unverified** for production.
F03/F11/F16, N01/N03/N04/N06, C06/C20; partial T01/T04/T07/T12 and
G0/G1. SPEC v0.2.34 preserves D04's OAuth/model/$10 total authorization.
No authentic model call, game launch, desktop input or paid inference occurred.

## Verified starting state

`git fetch origin`, `git rev-parse origin/main` and
`gh pr view 1 --json state,mergedAt,mergeCommit,url` confirm
[PR #1](https://github.com/OpenCnid/strata-bench/pull/1) merged at
`579796da40eeb9e6063196462767f60e9c87eac7`. The supplied worktree and main
checkout were clean. Implementation uses the fresh
`codex/strata-native-dispatch` branch from that main revision.

The actual CLI reports `codex-cli 0.154.0-alpha.6.2`; SHA-256 is
`960c111d47afd61669954b9df9e56083e302edbfa3ef6962d81dcc14a30051dc`, matching
the existing pin. No Java process was present during initial inspection.
The prior credential-free probe source and results were inspected outside the
repository. Credentials and game installations were not opened or copied.

The inspected private provisioning database has no accounting tables. Inventory
of the known operator/evidence/worker/host roots found game action stores,
synthetic stores and CLI caches, not an installed live D04 inference ledger.
The prior handoff reports $0 dispatched; this inspection finds no contrary
record but does **not** prove a complete prior-spend audit or create a new $10
allowance. Establish the durable project accounting authority before live use.

## Implementation

[Budgets](../../src/mcbench/budgets.py) registers explicit job envelopes under
`nested-envelope/1`. While open, an envelope contributes the maximum of its
bound and its descendant exposure for each budget dimension. Thus a root job,
helper job and individual requests share capacity without counting the same
reservation several times. Ordinary parent-linked operations stay additive.
Every ancestor envelope/account limit is checked transactionally. Actual
overruns are retained. Open/closed envelope events remain in the audit journal.

[NativeLaunch](../../src/mcbench/native.py) pins `budget_mode` in the profile
digest. Whole-job mode remains the default for existing callers; per-dispatch
mode explicitly enables envelopes, including helpers. The private generated
JSON/TypeScript schemas match. No gameplay record/tool/affordance changed.

After process and ingress fencing, `close_dispatch_budget` requires a private,
profile-bound seal with the exact attempt inventory. All requests and helper
jobs must be settled. It releases unused envelope capacity with zero duplicate
job usage and finalizes the native job in the **same transaction**. Missing
usage, live processes, incomplete/mismatched inventories and storage faults
cannot release the hold. The supervisor's evidence assertions still require
independent qualification for production; these local fixtures cannot grant it.

[The repeatable provider fixture](../../tools/native_dispatch_probe.py) starts
the actual CLI through `NativeExec`/`ManagedProcess`, with a fresh profile,
workspace, explicit environment and loopback provider. Every distinct HTTP
request obtains a new operation ID. An independent database connection verifies
the committed reservation/intent before the deterministic provider executes.
The provider supplies synthetic receipts; it never calls an external model.
Neither a body digest nor a CLI turn summary is used as a billing identity.

The fixture has bounded request sizes/counts, process time/output and handler
waits. Unknown routes/models/credentials/encodings reject. The synthetic provider
never emits shell commands or file/network tool operations. Compaction uses a
fixed JavaScript `text` call in the actual native tool loop. Raw request bodies,
native events, journals, receipts and recovery output stay in private evidence.
These are engineering process controls, not an adversarial OS sandbox.

## Executed verification

Windows, pinned Python 3.12.14, Node 24.19.0 and the CLI above. The final matrix
is private `C:\Users\Darian\.strata\evidence\2026-09-20-native-dispatch-08`.
Its manifest hashes the tested source and binary. All eight cases pass:

| Case | Actual result and accounting |
|---|---|
| Successful stream | CLI exits 0; one request/receipt; duplicate receipt changes nothing; closed job totals one call and 14 synthetic microusd. |
| HTTP retry | First synthetic 503 has an authoritative fixture receipt. CLI retries with the same body digest; two distinct operations/receipts total two calls and 24 synthetic microusd. No generic zero-cost assumption for HTTP errors. |
| Missing final usage | CLI exits 0, but accounting remains UNSETTLED; full 80,000-unit job reservation stays held and closure fails. |
| Lost stream | CLI attempts another request after EOF. The first request stays unresolved; the retry is rejected with METERING_UNKNOWN before provider execution. Only one dispatch exists. |
| Process interruption | Owned CLI process tree stops during a stream. One unresolved request remains; no replay or refunded reservation. |
| Native compaction | Actual compacting request contains the native context-checkpoint prompt, and CLI emits its compaction notice. Three receipts reconcile to 9,020 input / 12 output tokens, three calls, 9,032 synthetic microusd. |
| Helper job | Two actual CLI processes have distinct profiles/workspaces and one parent budget. Helper closes first; root remains reserved until its own fence/settlement. Final totals are two calls, 20 input / eight output tokens, 28 synthetic microusd. This is the separate-job helper seam, not Dovetail/native-collaboration qualification. |
| Supervisor restart | A new Python supervisor process reopens durable accounting after interruption. Duplicate request/native-job intents cause no forwarding/relaunch. New work is rejected with METERING_UNKNOWN; the full hold remains. This case restarts an already classified interruption; abrupt supervisor-crash coverage remains a separate extension. |

There are 13 received HTTP requests, 12 admitted dispatches, eight settled
dispatches and four intentionally unresolved dispatches across nine CLI jobs.
Every amount above is **synthetic**; real inference spending is $0 for these
procedures. No OAuth price/exposure qualification is issued.

Run explicitly, using a new private output directory:

```powershell
.venv\Scripts\python tools/native_dispatch_probe.py --codex (Get-Command codex).Source --output C:\path\outside-repository\new-probe
```

The relevant Python regression suite passes **130 tests**, no skips, in 8.45 s:
budget envelopes/clocks, dispatch, native host, authorization, storage/controller,
records, checkpoints/artifacts, operator commands and actual compiled gameplay
package exclusion. Two Typer/Click deprecation warnings remain. Envelope tests
cover nested capacities, unknown holds, closed-parent denial, ordinary additive
lineage, retained overrun and failed reservation rollback. Native tests reject
live/mismatched/unfenced/incomplete seals and retain the envelope when a trigger
injects a finalization write failure.

`tools/export_schemas.py`, `npm run generate --prefix backends/mineflayer` and
`npm run build --prefix backends/mineflayer` succeed. The schema writer now
preserves LF on Windows, consistent with source fingerprint policy. Ruff across
`src evaluator/src tests tools` and `git diff --check` pass. Unchanged full
Java/Node/game suites were not rerun to claim broader coverage.

Retained development failures: the first fixture used the wrong timestamp field
and failed schema validation before any CLI launch; early compaction fixtures
expected a top-level plan tool and failed with PLAN_TOOL_MISSING, retaining
their reservations. Inspecting the actual request revealed `additional_tools`
with the native JavaScript tool namespace; the corrected fixture uses that
observed contract. The first broader regression had 128 pass / one failure for
the stale NativeLaunch schema, then passed after regeneration. An earlier test
command named nonexistent test files and collected no tests. None is counted
as passing evidence. Private `native-dispatch-01` through `-07` retain earlier
attempts, including successful narrow cases.

## Remaining gates

No authenticated proxy or production ingress fence has been qualified. Real
OAuth monetary conversion, finite provider exposure, project spending history,
credential/process/network isolation and provider receipt coverage remain open.
The [official configuration documentation](https://learn.chatgpt.com/docs/config-file/config-advanced)
describes custom providers/retry controls; those controls do not prove a hard
OAuth dollar bound. The [earlier investigation](2026-09-19-native-budget.md)
retains its unresolved findings. No private proof flag is treated as independent
evidence of pricing or isolation.

Actual Dovetail skill/helper invocation, authenticated usage reconciliation,
complete host interruption/restore and adversarial isolation still require
their own evidence. All aggregate T01–T17/G0–G5 results and required M0–M6 scope
remain unchanged. M7 stays conditional.

## Follow-up: upstream wire receipts and abrupt supervisor loss

M0.1c.1c.1 adds [Responses transport](../../src/mcbench/inference_transport.py).
It accepts only permanently simulated stores and a literal `127.0.0.1` HTTP
endpoint. It makes one upstream POST per admitted intent, with a finite deadline,
one-MiB request and 256-KiB response bounds, no redirect/authentication/encoding
fallback or internal retry. A separate upstream fixture independently observes
the committed intent before receiving the request. This is still not a live
OAuth proxy or a security qualification.

Incremental SSE and JSON parsing bind the response/model/event, require terminal
usage, validate total/subset semantics, reject duplicate JSON keys, nonfinite
numbers, conflicting receipts, unsupported accounting fields and events after
terminal usage. The exact bounded response bytes are stored privately and linked
to the operation. Cached input and reasoning output are subsets, not additional
tokens. Rates are explicitly synthetic integer fixtures. Missing usage, malformed
streams, redirection, deadline or downstream writer failure retain uncertainty.
Incomplete/failed responses settle only when an explicit authoritative usage
receipt exists; HTTP errors alone never imply zero cost. JSON compaction receipt
parsing has unit evidence; the native CLI exercises its actual local compaction
path over `/responses`, not a claim about OAuth's remote compaction endpoint.

The final `--wire` matrix has **nine passing cases**, including all eight above
plus abrupt supervisor death, in private
`2026-09-20-native-dispatch-wire-final-01`. Fifteen HTTP requests reach ingress;
thirteen are forwarded and admitted, eight settle and five remain intentionally
unresolved. Two retries following unknown usage are blocked before upstream
dispatch. Ten actual CLI jobs run; no external model is called. Earlier
`native-dispatch-wire-01`, `-02` and `native-dispatch-crash-01`, `-02` are retained.
The stricter wire adapter rejects the missing-usage terminal frame, causing CLI
exit 1 with a fenced retry; the earlier direct-provider exit-0 result remains
valid evidence that CLI success alone cannot settle accounting.

The abrupt test waits for an upstream stream prefix to be flushed, then exits
the supervisor with `os._exit(79)`, bypassing all Python cleanup. Durable state
is RUNNING/DISPATCHING. An independently held outer Windows Job Object records
13 active processes before the crash and zero afterwards. Only then does a fresh
supervisor classify the pending request, retain the full envelope and refuse
native-job and request replay. No receipt is invented for the interrupted call.
The [job accounting query](../../src/mcbench/processes.py) follows Microsoft's
[QueryInformationJobObject contract](https://learn.microsoft.com/en-us/windows/win32/api/jobapi2/nf-jobapi2-queryinformationjobobject).
This process-count proof does not certify adversarial filesystem/network isolation.

The expanded relevant regression run passes **165 tests**, no skips, in 15.24 s,
with the same two dependency warnings. After the final parser checks for
post-terminal events and explicit live-store/request-digest rejection, all
**30 transport tests** pass in 3.51 s. Seven real process tests pass, including
whole-tree counts before/after stopping an owned grandchild. Envelope admission
also has a concurrent-consumer test: one of two competing 60-unit requests fits
a 100-unit preallocation; the other is rejected atomically. Ruff passes. The
initial transport test lint found one unused import, removed before final checks.

Run the complete current matrix explicitly:

```powershell
.venv\Scripts\python tools/native_dispatch_probe.py --codex (Get-Command codex).Source --output C:\path\outside-repository\new-wire-probe --wire --cases success retry missing_usage stream_loss interrupt compaction helpers restart crash
```

This advances partial F03/F09/F11/F16, N01/N02/N03/N04/N05/N06/N08 and
T01/T04/T07/T12. M0.1c.1c remains in progress: production transport/ingress
qualification, OAuth bounds/pricing, historical spending authority and isolation
are still open. Continue native pinned plugin/skill/helper conformance while
those external/live prerequisites remain unresolved; do not reset D04's cap.
