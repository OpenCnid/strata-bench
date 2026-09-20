# Native helper messaging, interruption and retained accounting

Date: 2026-09-20. M0.1c.2c.2a; partial F03/F07/F09/F11/F16,
N01/N03/N04/N06/N08, C06/C14/C18/C20 and T01/T04/T07/T12.
Actual pinned CLI and native collaboration; all provider responses and currency
are synthetic. No production helper/isolation/model-reasoning or aggregate pass.

The [helper fixture](../../tools/native_helper_probe.py) extends the previously
captured v2 schemas with actual `send_message`, `followup_task`, `list_agents`
and `interrupt_agent` calls. No shell, file or game action is generated. It uses
the same unchanged pinned Dovetail plugin, fresh private profiles and separate
loopback upstream through the durable accounting gateway. Model name remains
`gpt-5.6-luna`; no OAuth credentials or real inference are used.

## Idle and follow-up lifecycle

The child returns its fixed result, then the parent sends an idle message.
Native send/follow-up acknowledgements are empty. The message alone starts no
child request; `list_agents` still reports the completed original result.
Follow-up starts a new turn in the same child thread and includes both the queued
message and new task. The child returns the second fixed result. Interrupting
that completed child reports its prior completed status and leaves the child
listed with the same result. This does not claim cancellation of active work.

Final `native-helper-lifecycle-03` validates exact native response shapes,
including both terminal messages, unchanged child thread/new turn IDs, common
root-turn lineage and canary exclusion. It records **12 settled/deduplicated
requests**: ten parent plus two child calls. The envelope closes to 120 synthetic
input tokens, 48 output tokens and 168 synthetic microUSD. The CLI's root totals
contain only 100 input/40 output tokens. Both child turns are included in the
gateway ledger without a second whole-job charge.

This fixture explicitly reserves a **16-request, 45-second** case within the
unchanged 80,000 synthetic microUSD envelope. Existing fixtures retain their
eight-request default; a new constructor guard permits only integer limits
1–32. These are declared test bounds, not a change to the live $10 ceiling or
benchmark acceptance thresholds. Native child concurrency is one in this case;
the full two-helper/default-depth contract remains unqualified.

## Active stream interruption and restart

Final `native-helper-active-02` flushes an upstream child stream prefix before
the parent invokes the real interruption tool. Native reports previous status
`running`, then lists the child as `interrupted`. The upstream intentionally
ends without authoritative usage after cancellation; no replacement receipt or
zero-cost claim is manufactured.

Exactly five requests were forwarded: four parent calls settle and deduplicate,
one child call stays **UNSETTLED** with `AUTHORITATIVE_USAGE_REQUIRED`. The root
CLI exits 0, but monetary closure is rejected with `METERING_UNKNOWN`. The full
800,000-input/80,000-output/eight-call/80,000-synthetic-microUSD envelope remains
reserved, uncertainty remains true and dispatch is denied. Native cancellation
does not imply provider cancellation or complete metering.

A fresh supervisor process opens the same durable store and attempts the
idempotent admission paths with a callback that would fail on any forwarding.
It observes four settled/one ambiguous attempt, **zero replay**, unchanged
accounting and rejected new admission. This is a restart of already classified
uncertainty, not another abrupt-supervisor-crash or full session/game resume test.
The shared recovery fixture now distinguishes settled from ambiguous counts and
checks that replay checks change neither totals nor the attempt inventory.

## Retained samples and verification

All private directories below are beneath
`C:\Users\Darian\.strata\evidence\2026-09-20-`:

- `native-helper-lifecycle-01`: fail. The fixture initially tries to parse the
  empty send-message acknowledgement as JSON. Four requests settle; one remains
  unresolved. Its complete 16-call/80,000-synthetic-microUSD envelope is retained
  and dispatch remains blocked. Correcting a fixture does not replay or erase it.
- `native-helper-lifecycle-02`: corrected flow/count/accounting checks pass;
  observed list/interruption result shapes are preserved. `-03` additionally
  enforces those exact shapes and rejects coerced/duplicate/wrong-state results.
- `native-helper-active-01`: observed active interruption/accounting case passes.
  `-02` adds exact running-to-interrupted/error validation and fresh recovery.
- `native-helper-regression-01`: original clean-context/ephemeral case still
  passes with four settled calls, 56 synthetic microUSD and final closure.
- `native-restart-regression-01`: original wire restart case still passes with
  one ambiguous request, full reservation, denied admission and no replay.

`uv run --frozen python -m pytest -q tests/test_native_helper_probe.py
tests/test_native.py tests/test_inference_dispatch.py tests/test_inference_transport.py
tests/test_gameplay_package.py` passes **96 tests**, zero skips, 8.24 s. Full Ruff
and diff checks pass. One temporary strict-verdict patch indentation error was
caught by Ruff before any run and corrected. Raw requests, tool schemas, source
hashes, plugin digests, native events, receipt evidence, journals, failed samples
and recovery records remain external. No Minecraft process or desktop input was
used in this helper work; real USD dispatched is zero.

The binary remains `codex-cli 0.154.0-alpha.6.2`, SHA-256
`960c111d47afd61669954b9df9e56083e302edbfa3ef6962d81dcc14a30051dc`;
Dovetail revision `15c306ccfef28eb5f616fadcd5fd8eac0663e361`, version 0.4.1.
This code adds fixture coverage and verdict checks; it does not implement trusted
native-child admission, authenticated lineage, per-child permission principals,
enforced child sub-budgets, grandchild/depth handling or complete state export/
resume. Metadata is observational. Persisted profiles and fresh contexts are
not security isolation; prior canary failures and live monetary/exposure gates
remain. Continue those required work items without promoting full T04/T12/G0.
