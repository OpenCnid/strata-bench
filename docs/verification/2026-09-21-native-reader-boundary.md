# M0 restricted native reader boundary against a writer-owned file

September 21, 2026. Operator-only. M0.1c.2b.2b.1 with M0.2c.3b.2b.1;
F03/F04/F07/F16, N01/N04/N06/N08, C06/C12/C20/C24/C36,
partial T01/T04/T06/T07/T12/T13 and G0 items 1/6.
M0 is incomplete, G0 fails and G1–G5 are not run.

## Implemented enforcement

The [existing restricted native broker](2026-09-20-restricted-native-tools.md)
already supplies permitted artifacts and executor-only game access. The
[writer ACL canary](2026-09-21-writer-boundary.md) separately showed that a sibling
native sandbox process could read raw writer files. Its original failure remains;
write restrictions are not read isolation.

[Native broker settings](../../src/mcbench/native_broker_policy.py) now declare
`native-broker-closed-features-stdio/2`. The exact feature-key set is required,
including disabled legacy collaboration/remote model discovery and enabled pinned
plugins/native collaboration. Unknown feature keys, even false values, and nested
`features` tables reject. The sole MCP server accepts only its existing stdio
command/arguments/environment, required tool list, per-tool approvals and timeout
fields. Alternate URL/authentication/inherited-environment fields reject instead
of accompanying the sealed broker command. The existing bootstrap still verifies
the exact interpreter, arguments and empty environment before dispatch.

Before the change, a retained source-only check accepted three unexpected config
shapes: an additional unified-exec flag, a nested feature table and a server URL.
This proves a validator gap, **not an observed native exploit**. New tests prove
feature expansion rejects before native intent, process creation or budget change.
The same validator runs during participant admission and sealed bootstrap checks.
Current source/profile pins bind this policy; no historical receipt is rewritten.
The underlying broker/game API, selected runtime and Dovetail plugin are unchanged.

[The canary verifier](../../tools/native_broker_canaries.py) also now binds each
observed output to the native request's root/helper metadata. Missing helpers,
two distinct root outputs or conflicting caller identities cannot stand in for
both callers. Model-returned `probe` labels cannot supply caller identity.
Duplicate notifications from one caller still deduplicate by call ID.

## Changed native integration

Private `2026-09-21-native-reader-boundary-01` contains the one-use driver, source
archive, original validator observations and exact native evidence. It uses the
existing enrolled sandbox identity, not new accounts or firewall changes.

The native writer first creates/reads/updates/renames a fresh synthetic
`world/level.dat` under `WriterTree`'s scoped group/workspace policy. Exact inherited
ACLs and token scope are checked. The file contains only the fixed fixture marker;
the new target loader rejects nonmatching content, links, wrong names or size.
The tree remains held throughout the reader trial; a read-only file lease prevents
changes. This is not an authentic world or secret-bearing evaluator instance.

Then the existing sealed actual-CLI/admission/broker fixture runs one root and one
clean native helper against the local deterministic provider. Besides existing
controls, each attempts the writer file through the MCP resource route and the
artifact-read tool. Their disabled-shell attempts also name that file. Explicit
native denials are required; absence of the marker alone cannot pass.

Actual runtime: Windows, Python 3.12.14; Codex CLI `0.154.0-alpha.6.2`, SHA-256
`960c111d47afd61669954b9df9e56083e302edbfa3ef6962d81dcc14a30051dc`;
unchanged Dovetail commit `15c306ccfef28eb5f616fadcd5fd8eac0663e361`;
selected `gpt-5.6-luna` with **synthetic responses only**.
Profile `0f643abc2d0775ea5103ab1c36499ce73e907f2afe5335142b599857ff6d85b2`;
bootstrap `deebfbde47af6a2201ea1e2f852e35f8bf0b2025455b046b1e0bc3ee159ebb50`.

All **33 integration checks pass**, including 19 canary checks:

- Root and helper receive exact restricted catalogs; shell/image/direct shell
  dispatch deny. Code-mode process/require/fetch globals are absent.
- Both writer-resource attempts reject with `BROKER_REQUEST_REJECTED`; both
  absolute artifact-path attempts return `isError` and exactly `UNSAFE_PATH`.
- Writer bytes, private canary and ancestor instructions do not enter captured
  requests; files remain unchanged. The separate loopback positive control works,
  and unauthorized tool attempts produce zero visits.
- Allowed own artifacts still work; helper parent-artifact/identity/game attempts
  deny, while the executor reaches the synthetic worker exactly once.
- All eight distinct requests are admitted and settled, both participant envelopes
  close and the native job becomes FINALIZED. Total **80 input / 32 output / 112
  synthetic fixture units**, not actual charges or OAuth usage. No live inference.

Native execution lasts 49.2799 s under the unchanged 90-second bound; final
accounting closure occurs afterward. The report retains its pre-closure UNSETTLED
snapshot separately from the FINALIZED closure and current database state.
An independent process query finds zero Python/Codex/command-runner processes
for this private scope. No Minecraft or shared-desktop input occurred.

## Focused source checks and limits

Executed with `PYTHONPATH=src;evaluator/src`:

| Check | Result |
|---|---|
| Broker tests plus new pre-intent feature rejection and existing changed-bootstrap test | 39 pass / 1.37 s |
| Canary output/caller/target verifier tests | 4 pass / 0.69 s |
| Native admission plus authenticated pre-dispatch/revocation regression | 27 pass / 2.57 s |

These are **70 distinct checks**. Focused Ruff and whitespace checks pass; two
initial test-file style findings were corrected without changing behavior. No
broad accounting/retry/compaction matrix or unchanged live trial was repeated.

The first command selected `tests/test_native_broker.py` plus
`tests/test_native.py::test_unreviewed_broker_feature_rejects_before_intent_budget_or_process`
and `tests/test_native.py::test_changed_bootstrap_rejects_before_budget_or_process`.
The second selected `tests/test_native_broker_canaries.py`; the third selected
`tests/test_native_admission.py` and
`tests/test_native_ingress.py::test_authenticated_request_required_before_budget_and_rechecked_at_dispatch`.
All ran with `.venv/Scripts/python.exe -m pytest -q`; private JUnit files retain
the exact cases and results.

This evidence advances the selected **restricted tool/broker path** against the
tested writer target. It does not repair the unrestricted sibling sandbox's read
access or its historical loopback leaks, and does not issue RuntimeQualification.
Real provider ingress/usage remains unresolved, as do native capability drift,
complete helper lifecycle/descendant admission, skill supporting files and learned
activation/export, authentic evaluator secrecy and complete game/runtime joins.

Next bind the actual native tool projection to request admission, so an unexpected
tool catalog rejects before provider forwarding rather than relying only on
configuration and post-run canaries. Use this captured root/helper evidence to
define the pinned shapes; keep the native loop and plugin. Further authentic game
trials require a relevant change or named evidence gap. Preserve every 500-ms
shutdown failure, five effective-file failures, Mineflayer/E9E incompatibility,
scorer/provenance/recovery work and all required M0–M6/conditional M7 scope.

The original durable authority remains $10 with one unresolved $0.7554 hold.
No live model call, replay, refund, settlement or allowance reset occurred.

The independent checkpoint audit passes **22/22** after a separate retained
correction: the initial process-name query counted its own verifier as a live
scope process (21/22). The corrected query checks the actual native/writer
execution subtrees, and includes the writer fixture executable. The original
audit remains; the native run was never repeated or changed.
The manifest verifies **8,794 files / 421,866,407 bytes**, SHA-256
`4db3135147bfbdb7b92cb9541823dfd92744c3d2b46c711072486d47626769bf`.
It includes sealed runtime/source and raw evidence outside public source.
Read-only accounting at Unix ms `1789998830941` confirms schema 2, one migration
and unchanged original cap/digest/hold. All 295 prior milestone IDs plus the new
child, append-only history and 1,119 local links are checked.

The OpenAI Docs skill was used to recheck official
[shell-feature configuration](https://learn.chatgpt.com/docs/config-file/config-reference)
and [Windows sandbox behavior](https://learn.chatgpt.com/docs/windows/windows-sandbox).
The documents describe controls; actual pinned-runtime canaries determine this
candidate's results. They do not substitute for an observed denial.
