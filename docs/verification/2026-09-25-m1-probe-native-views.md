# M1.6d native artifact and catalog preparation

D20 continuation of M1.6a/b/c. M1.6d is implemented_unverified for actual native
bootstrap/catalog/broker integration; M1.6 remains in_progress and G1 not_run.
Affected: F03/F07/F08/F16, N01/N04/N06/N08, C06/C12/C20/C22/C23/C24/C36,
T01/T04/T06/T11. Unrelated M2-M7 work and spending authority remain unchanged.

## Implemented preparation

[ProbeNativeViews](../../evaluator/src/strata_evaluator/native_probe_views.py)
reconstructs the complete prepared pair and its committed checkpoint provenance,
then creates native artifact views for both arms and every declared member.
No caller can replace the approved artifact selection, instructions or catalog
with a supplied manifest. Native catalog bodies/supporting files under
`.agents/skills/` exactly duplicate the approved `active/` bytes as separate files.
The public revision index resolves in the operator artifact store, like every
other broker input. Private pair, source and role manifests remain in evaluator
storage and outside all workspaces.

Root inventories contain the selected initial/retained cognitive artifacts and
active skills. Helper inventories contain only approved immutable initial,
documentation and supplied files plus the explicitly selected active set. They
exclude root notes, drafts, handoff and helper-private results. No-self-play
produces no helper inventory. Frozen controls preserve their registered artifact
rules; time-zero views have identical public bytes. Instructions are common to
both arms and describe scoped artifact use without evaluator identities.

Native profiles start empty. One-use PREPARING intent precedes file creation;
failed copying retains partial files and FAILED. Verification commits VERIFYING
before source/tree inspection, refuses altered/missing references, files, links,
profiles or directories, and keeps failed checks consumed. Quota/target/auth
refusals occur before a view intent. Source pairs are rechecked after copying.
No source pair, native job, grant, account, checkpoint or publication is relabelled.

These views are bootstrap inputs. They do not grant native launch, loader,
broker projection, resource, OS-isolation or disposal authority. The role maps
still need an actual scoped native consumer; directories alone enforce none of
those boundaries. No NativeLaunch purpose or native tool profile changes here.

## Executed checks

Initial view selection16 pass. Expanded controls plus pair regression54 pass.
Review then adds operator-store binding for the generated public index and
verification of every broker input's visibility/hash. Final view selection23
pass; the unchanged pair suite contributes34 passes, for **57 distinct cases**:

```text
PYTHONPATH=src;tools;evaluator/src
.venv/Scripts/python.exe -m pytest tests/test_native_probe_views.py tests/test_probe_pairs.py -q
.venv/Scripts/python.exe -m pytest tests/test_native_probe_views.py -q
```

Recorded commands also retain fresh private test directories and logs/JUnit.
Coverage includes exact root/helper catalogs and bytes, source controls,
time-zero equality, public-index resolution, missing/wrong-visibility index,
altered catalogs/private manifests, hardlinks, extra session/cache directories,
copy failure, source drift during copying, committed verification intent,
authorization, storage limits and forbidden target locations. The interruption
case injects KeyboardInterrupt; this task does not claim a new actual native or
controller-process-death experiment. Source/game/native records are synthetic.
No Codex, Minecraft or provider execution occurs.

Read-only reconstruction passes **60/60 case checks plus3/3 common checks** for
six successful preparations. It independently compares registered source/plan,
complete trees, role inventories, catalog bytes/inodes, empty profiles, controls,
time-zero equality, unchanged database/costs and absence of new native jobs.
The final23 cases comprise six PREPARED, ten FAILED, seven without a view intent.

The first archive reader refuses COST_DATABASE_NOT_FROZEN for a retained fixture
WAL. Preserve that failure, database and WAL. The corrected reader copies the
sealed database/WAL, makes one read-only SQLite backup into a separate audit
snapshot, and rechecks the original seal. No original journal is checkpointed,
deleted or ignored. Other frozen databases use the ordinary immutable reader.

Producer `2026-09-25-m1-probe-native-views-01`:9928 files,65,105,315 bytes;
seal `c2958cf8e6c243c7f83a1a40197a70c4a71be41616c963332d4b514c990c1e45`.
Audit `2026-09-25-m1-probe-native-views-audit-01`:8 files,3,776,478 bytes;
seal `101aaacef8355dc6fac10919ff338c5c8f4a725585cf3474567134c9f73d89fb`.
Ruff and whitespace pass. All40 real authority tables remain unchanged;
$4.887796/$10 exposure and all holds/consumed decisions remain. No matching owned
runtime remains, no M1 paid authority or RuntimeQualification is inferred.

## Next native integration

Bind these verified view inputs to a separate disposable native runtime identity
and evaluation account, with exact catalog admission and scoped root/helper
projection. Keep evaluator implementation/manifest contents out of gameplay and
helper contexts. Preserve campaign skill-set and publication import guards;
probe-local mutable artifacts need not become campaign publications. Complete
held launch custody, fresh sessions/backend state, live matched worlds/body/
keymap/tools, resources, N>1 positive preparation and one-way canary disposal.
Combined runtime isolation, T05 and scorer controls remain required for G1.
