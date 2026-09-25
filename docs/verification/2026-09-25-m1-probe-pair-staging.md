# M1.6b one-use matched pair preparation

D20 continuation of [committed artifact projection](2026-09-25-m1-probe-artifact-projection.md).
M1.6b is implemented_unverified for complete native/world probe integration;
M1.6 in_progress and G1 not_run. F02/F03/F07/F08/F11/F16,
N01/N04/N05/N06, C03/C04/C06/C12/C13/C20/C22/C23/C24/C36,
T01/T04/T06/T11 are affected. This task executes actual disk preparation with
synthetic game/native source records, never Minecraft or a native/model probe.

## Implemented boundary

[ProbePairs](../../evaluator/src/strata_evaluator/probe_pairs.py) binds private
`ProbeFixture/1` and `ProbePairRequest/1` to an EvaluationProtocol's exact
instance, artifact-selection and arm-order indices. It reconstructs every
selected native source and requires the full declared roster from one committed
checkpoint. Model, runtime/plugin, initial skills, backend/track, capabilities,
information and communication policies, common keymap/control cards, ordinary
goal, opportunity limits and handoff limits are retained in a common private
configuration. Required source references must resolve. A directory manifest
does not establish that the actual game/backend honors that configuration.

The two copies contain byte-identical fixture server/world/external files and
private body/control configuration, with separately created files. Only the
approved initial/experienced cognitive artifacts and active revision index
differ. Treatment names stay in private metadata; arm directories use `copy-0`
and `copy-1` under the registered order. Each member has fresh empty profile and
backend-cache directories. Source sessions, caches, auth/account bindings,
helper-private results and skill publication drafts are not copied into a
gameplay workspace. Private manifests remain outside those workspaces.

The authoritative staging registry reserves pair, instance, fixture reference
and world digest before the first copy. These are unique across its namespaces;
changing the pair or instance label cannot reuse the same fixture world. A
partial-copy failure leaves a durable FAILED intent and its remaining files,
with no overwrite/rearm path. A process interruption can leave PREPARING, which
also refuses verification/reuse. This is a single-registry guarantee, not a
cross-database or OS isolation boundary.

Preparation checks the declared byte ceiling and available disk space. These
checks are not capacity reservation or execution budget admission. After copying,
and on later verification, derive the original source plan again and inspect
both entire trees: exact files/directories, sizes/hashes, no reparse/symlink or
hardlink alias, no extra sessions/cache directories. Verification retains a
private event. The result always denies dispatch/feedback authority and reports
live initial-state/resource admission as unverified. A consumer must not infer
launch authorization from PREPARED or a successful byte check.

Time-zero eligibility requires scheduled and actual source exposure both zero
and identical initial/experienced cognitive surfaces. The synthetic t=0 test
also compares every copied byte and runs a deterministic seeded fixture policy
on the two inputs, giving zero designed gain. It is not authentic model play,
evidence of learning, or confirmation that a live backend cache was reset.

## Executed evidence

- Initial selection:10 pass, one test assertion fails. The fault injector copied
  `external/teams.dat` first in canonical order; the test incorrectly expected
  `level.dat`. FAILED intent/fencing already worked. Correct the assertion to
  inspect the actual first successful copy and absent second target.
- Intermediate selection:28 pass; expanded hardlink/interleaving/index/authority
  checks9 pass with25 deselected. These overlap and are not summed.
- Final `tests/test_probe_pairs.py tests/test_records.py tests/test_evaluator.py`:
  **80 pass** (34 pair cases,46 record/evaluator cases). Covers strict private
  schemas, full roster omissions, scope/order/projection mismatches, storage
  exhaustion, altered/extra files, hardlinks, interrupted copy, interleaved reuse,
  immutable registered plan, t=0 and exact source/arm differences. Ruff and
  whitespace pass. Schemas remain evaluator-only;13 canonical records unchanged.

Two independent N=1 preparations, retained and t=0, pass18/18 disk/reopen checks.
Each contains56 synthetic source units; staging adds no model/game calls and
does not alter those costs. Producer
`2026-09-25-m1-probe-pair-stage-01`:592 files/5,777,719 bytes, seal
`4576f005424dd4b57f68c11ee2bbcdcc702ab38f6c0f9eed27471f49e38a4339`.

Independent stopped reconstruction passes21/21 pair and2/2 common checks:
rederive the registered plan from immutable source, inspect both actual trees,
recompute allowed differences, prove separate equal world files and empty state
directories, reconcile prepare/reopen events and unchanged costs/database dumps.
Producer seals reverify. Audit `2026-09-25-m1-probe-pair-audit-01`:
6 files/15,275 bytes, seal
`e511eb55065e3b2aacbcb9efaf56f30a842129d890aa468443516a9d60334f3e`.

All40 WAL-aware real authority tables remain unchanged; exposure stays
$4.887796/$10 with all prior holds and consumed decisions. No owned runtime
process remains. USD0 actual inference; no M1 spending authority inferred.
Source, prepared trees and private evidence remain outside the repository and
all gameplay/helper contexts.

## Source gap and next integration

A separate read-only check of sealed matched-retention03/r11 finds five source
configuration references unresolved in its operator CAS: information policy,
runtime profile, backend capability, inference configuration and agent capability
profile. Its communication policy resolves. Preserve its named synthetic/native
retention evidence and original seal; do not backfill those records or promote
them into the stricter pair contract. The new synthetic preparation fixtures
explicitly resolve their inputs before source registration. A fresh native probe
source must do likewise.

Next implement the disposable probe runtime adapter and its launch/disposal
fence. NativeLaunch currently has no probe purpose, and campaign skill activation
requires campaign scope; do not bypass either using a conformance label or a
relabelled source. Evaluation-account publication currently refuses campaign
imports, while probes still need permitted local adaptation that cannot return
to training. Bind the prepared pair to actual matching native/world execution,
fresh contexts/backend state, development-only practice, resource/accounting
admission and one-way canary disposal. N>1 positive probe preparation, authentic
fixture/state validation and held launch custody also remain open. The existing
client/log/registry, T05 and scorer gaps continue to prevent G1 closure.
