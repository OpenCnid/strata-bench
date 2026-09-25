# Selected native episode checkpoint and fresh activation

Operator-only. M1.4a, F03/F04/F07/F11/F16, N01/N04/N06,
C06/C07/C12/C14/C20/C36; partial T01/T04/T06/T11. M1 in_progress,
G1 not_run. Continues [selected script execution](2026-09-24-m1-active-script-native.md)
without changing or replaying that sealed run.

## Implementation

`ActivationController.begin_checkpoint` requires a live owned controller,
matching scope, FINALIZED native job, exit0/native_exit, no live owned job,
exact held-process drain proof and zero forced terminations. Only then use the
normal Controller transition to CHECKPOINTING. It is one-use and does not itself
claim a complete checkpoint. Failures preserve the original state/holds.

The identity fixture's explicit `activation_checkpoint=True` option requires
the selected activation profile. After native return, ingress/provider and worker
cleanup, settle the native budget once, enter CHECKPOINTING while the heartbeat
is held, and call the existing synthetic checkpoint builder. It publishes the
stopped native revision, seals the retention component, commits the complete
synthetic world/agent checkpoint and creates the next active set. Controller
ownership/state is checked before and after checkpoint work. Exceptions still
drain the owned heartbeat; pre-return failures cannot reach checkpoint creation.
Historical fixture defaults and original evidence remain unchanged.

The fresh seed's JavaScript now looks up its existing artifact reference before
writing, supporting a later episode through the same bounded broker. It also
reports an initially absent private code-mode value, stores an owner value and
successfully reads it. The provider copies exact active source into native exec;
operator Python never evaluates that JavaScript.

## Actual native continuation

One new source and two sequential native jobs use the pinned CLI/Dovetail,
selected `gpt-6-luna` metadata, campaign projection /5 and scoped team broker.
The provider, world, worker and readiness remain **synthetic**. There is no real
model inference, game body, paid request, or RuntimeQualification.

| Episode | Native profile | Result |
|---|---|---|
| `handoff-1`, epoch2 | `20ff3473cab73b198842de85e3511620607330ed7ee5d212178e570aec6e5e7b` | 37/37;8 requests; normal stop; complete checkpoint activates executable revision2 |
| `handoff-2`, epoch3 | `adf4e4e26d798ff3b5ba6e7db0643a9517e7db822fa0dd5108ae79215c22d890` | 37/37;8 requests; exact prior checkpoint supplies revision2; normal stop/checkpoint activates revision3 |

Each episode uses root5/helper3 requests and settles112 fixture units. Total is
280 including the source's56, with20 calls/200 input/80 output tokens and no
uncertainty or allowance change. Root writes succeed, helper writes reject;
helper inventories contain no root notes/drafts/handoff. Both jobs and all their
participants close. Both synthetic controllers remain at the correct
CHECKPOINTING epoch after the owner drains; no lease/state rewrite is needed.

Episode2 receives episode1's exact active-set reference and body. It has a fresh
root thread, workspace and native profile, no prior assistant/tool history in its
first root input, and clean helper enrollment. Each root/helper execution starts
without the prior private code-mode value and successfully reads its own new
value. Admitted notes and exact JavaScript survive through the checkpoint;
SKILL.md and publication lineage advance through actual root write receipts.
This proves the named runtime continuation, not a restored authentic game or
hidden model state, and not adaptation or learning.

## Checks and custody

91 focused tests pass in161.58s across controller, selected seed, native skill
activation and checkpoint contracts. Three additional strict-option guards pass
in0.28s;94 distinct cases total. Earlier24/9.30s overlap and are not added again.
Negative cases include missing drain, forced termination, failed/interrupted/
unsettled/live jobs, owner already drained and incomplete checkpoint profile.
Controller unit cases explicitly stub drain evidence; authentic proof joins are
verified separately below. Ruff and whitespace pass.

```powershell
.venv/Scripts/python.exe -m pytest -q tests/test_native_activation_controller.py tests/test_native_selected_activation.py tests/test_native_skill_activation.py tests/test_native_checkpoint.py --tb=short
.venv/Scripts/python.exe -m pytest -q tests/test_native_activation_controller.py -k checkpoint_option --tb=short
```

Independent read-only reconstruction passes **42/42**, checking raw request and
settlement bytes, ingress/projection, exact script read/issuance/completion,
private-state controls, normal held-process drain, complete native component/
checkpoint/activation lineage, source-bound publication, scoped effects,
root/helper inventory, synthetic world/stop references and actual budget totals.
The two source databases are opened immutable only after their frozen WAL checks
and externally pinned full inventory. No old job is dispatched by the audit.

Private evidence under `C:/Users/Darian/.strata/evidence/`:

| Bundle | Inventory | Seal SHA-256 |
|---|---|---|
| `2026-09-24-m1-active-handoff-01` (prepared September24, continued September25) | 7,976 files /153,051,314 bytes | `68a94c894938fcb7e304049f40c75de1bdcc8c6d96af1200c803d36774cb74d7` |
| `2026-09-25-m1-active-handoff-audit-01` | 3 files /19,845 bytes | `8d5da4b962a38b4c57ee4ac0958097e98abb777b36a53c2cf3bd246114ca9a39` |

Nested stopped DB/CAS pins are epoch2
`cf5e473c9335c89f88e8c059c18be184fe22229057c5193c34a76f8191c4b0f0`
and epoch3
`44386e18e16dee33b606e300422cee74606279bdcbfcfa8def87946e8babf69d`.
Their subset manifests are activation-copy inputs; the outer seal additionally
covers all native captures, profiles/cache files, frozen source and metadata.
The three extra option tests were added after native source capture; runtime
implementation bytes stayed unchanged. Historical failures remain retained.

All40 real authority table hashes and$4.887796 exposure/holds remain unchanged.
Scoped post-job observations find no owned native/game fixture process. One-use
scripts are sealed history, not resume commands. D18/D19 remain M0-only spending.

## Remaining gate work

Next verify matched selected frozen/no-self-play controls and complete their
session/cache reset and artifact boundary evidence. The full arm's fresh state
result cannot substitute for those controls. Carry executable/handoff source and
profile evidence into complete root/helper boundary qualification, including
actual game macros/local charges where claimed. Native interruption variants,
full T01/T04/T05/T06/T10/T11 and G1 retain their complete contracts. T04 runtime
continuation is G1; canonical game recovery/fault/soak qualification remains G2.
