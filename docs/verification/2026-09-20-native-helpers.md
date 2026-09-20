# Native collaboration and session storage — September 20, 2026

Operator-only. M0.1c.2c/.2c.1; F03/F07/F09/F11/F16,
N01/N03/N04/N06/N08, C06/C14/C18/C20; partial T01/T04/T07/T12.
Implemented but unverified for production. No full helper/self-play, isolation,
model-reasoning, resume or aggregate gate pass.

## Actual surface and implementation

The pinned CLI advertises `multi_agent` and `multi_agent_v2` in its local feature
inventory. Merely setting `features.multi_agent=true`, or additionally setting
documented `agents.enabled=true` and a one-child concurrency limit, does not
advertise collaboration in this `exec` profile. Enabling
`features.multi_agent_v2=true` exposes the actual `collaboration` namespace:
spawn, wait, list, message, follow-up and interruption operations. Tool schemas
were captured from native request input before invoking any helper operation.

The [new fixture](../../tools/native_helper_probe.py) installs the exact unchanged
Dovetail plugin in fresh external profiles and serves deterministic responses
through the existing durable local gateway and separate upstream. It invokes
the native `spawn_agent` and `wait_agent` tools directly. It does not simulate a
child with a second top-level CLI process. Parent and child use the same pinned
`gpt-5.6-luna` name and local credential-free provider. The provider returns fixed
text only; no generated shell command, game interaction or paid model occurs.

Two native context cases are observed: `fork_turns="none"` excludes a synthetic
parent marker from the child request, while `fork_turns="all"` includes it when
the parent session is persistent. Child replies arrive as native `agent_message`
items with the expected author, recipient and FINAL_ANSWER payload. Native
request metadata links distinct child/parent thread IDs to the same root turn.
These metadata are observations, not trusted production admission credentials.

Full-history delegation fails with an ephemeral parent: native spawn reports
that the parent thread cannot be found. A fresh persistent-profile experiment
resolves this specific failure. [NativeLaunch](../../src/mcbench/native.py) now
has explicit `session_storage`: `ephemeral` remains default; `private_profile`
omits `--ephemeral`. Storage mode is included in the profile digest and private
schema. Tests reject reusing ephemeral qualification after changing that mode.
No sandbox, billing or live-admission condition is bypassed. Session files are
private artifacts, not gameplay exports or a complete checkpoint by themselves.

Public documentation describes [subagent configuration](https://learn.chatgpt.com/docs/agent-configuration/subagents)
and [agent defaults](https://learn.chatgpt.com/docs/config-file/config-sample).
Those documents guide configuration; the pinned binary's observed v2 surface,
exact context/event behavior and retained failures determine this result.

## Accounting and limits of the result

Each successful delegation has three parent requests and one child request.
The durable gateway admits, settles and deduplicates all **four** under the one
parent envelope: 40 synthetic input tokens, 16 output tokens and 56 synthetic
microUSD. There is no second whole-job reservation for the native child and no
double charge. The CLI's root turn total reports only 30 input, six cached and
12 output tokens, excluding the child's request. The discrepancy directly
demonstrates why turn totals cannot establish all-call accounting.

This proves inclusion in the aggregate fixture ledger. Per-helper enforceable
sub-budgets, helper-specific permission principals and trusted admission identity
are not implemented by this fixture; entries remain calls of the owning root
runtime. The existing separately launched helper-envelope tests are distinct
evidence, not proof of those controls for native collaboration. The shared native
workspace/profile is not a security boundary. Preserve the failed file/network
canaries and require enforceable isolation before live admission.

## Samples and verification

Private roots `C:\Users\Darian\.strata\evidence\2026-09-20-native-helper-01`
through `-09` retain request bytes, manifests, schemas, ledgers, journals and
results. Binary: `codex-cli 0.154.0-alpha.6.2`, SHA256
`960c111d47afd61669954b9df9e56083e302edbfa3ef6962d81dcc14a30051dc`;
Dovetail `15c306ccfef28eb5f616fadcd5fd8eac0663e361`, version 0.4.1.

- Discovery `-01`/`-02`: fixture checks pass, native helper capability absent.
  `-03`: v2 namespace appears. Each settles one synthetic request, 14 microUSD.
  Discovery is not an invocation pass. Separate feature-inventory evidence keeps
  the initial rejected placement of `--ignore-user-config` at the root CLI;
  the corrected read-only command uses a fresh profile and no model.
- `-04`: native clean-context child executes, but the fixture initially expects
  an ordinary role message instead of actual `agent_message` delivery. The last
  provider response aborts; its unresolved reservation remains. Parser corrected
  from captured native evidence, not by inventing a tool/event format.
- `-05`: corrected clean-context invocation passes. `-06`: full-history spawn
  fails with the ephemeral parent; wait times out and the fixture's final
  response aborts. That sample and its uncertain hold are retained.
- `-07`: full-history invocation passes in the explicit synthetic persistent
  argv experiment. This motivates the declared storage mode.
- Final `-08` and `-09`: clean-context/ephemeral and full-history/private-profile
  both pass using ordinary `NativeExec.start`, without fixture argv overrides.
  Each records distinct native thread lineage, expected canary presence, four
  settled/deduplicated calls, final envelope closure and unchanged plugin bytes.
  `-09` leaves the two native rollout artifacts in its private profile.
- Relevant Python: **77 pass**, zero skips, 5.23 seconds, across native runtime,
  dispatch, record schemas and gameplay-package exclusion. Full Ruff, schema
  regeneration, TypeScript build and diff checks pass. No broad game/pilot suite
  was rerun. The fixture upstream's request indexing now uses its existing lock
  so concurrent parent/child requests cannot share an index.

Reproduce with README's Python environment and the pinned `--codex` path:

```text
python tools/native_helper_probe.py --codex PINNED_EXE --output NEW_PRIVATE_ROOT --variant v2 --mode fork_none
python tools/native_helper_probe.py --codex PINNED_EXE --output NEW_PRIVATE_ROOT --variant v2 --mode fork_all --persistent
```

Every root must be fresh and outside the repository. No real USD is spent.
Next: trusted helper admission/lineage, full lifecycle and nested/grandchild
accounting, per-helper permission enforcement, interruption and admitted complete
session export/resume. A persistent rollout file alone satisfies none of those
gates. Live OAuth pricing/exposure/spending authority and isolation remain blocked.
