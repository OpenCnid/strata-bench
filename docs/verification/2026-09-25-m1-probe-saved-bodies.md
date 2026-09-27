# M1.6n — registered saved-player body binding

G1/T11 requires matched body state before either arm starts. The existing pair
staging validates complete roster references but treats each body-state object
as opaque. An identical world copy alone cannot prove those declarations refer
to its saved players. This change adds a private saved-state join; live roster,
authenticated account assignment, backend cache reset and live initial-state
matching remain separate required contracts.

## Implementation and profile identity

`probe_saved_bodies.py` defines strict `PrivateVanillaProbeBody/1`. Its declaration
binds a canonical UUID, exact compressed player-file CAS reference, complete
uncompressed NBT digest, position/rotation, dimension, health, food, selected
slot and game mode. The bounded existing NBT decoder requires data version3120,
valid UUID length, finite coordinates, distinct inventory slot ranges and
syntactically valid item IDs/counts; it does not validate registry semantics.
The full NBT digest preserves item tags, equipment, effects, abilities, respawn,
recipes, ender inventory and all unprojected state. It does not turn unknown
custom semantics into a live-state equivalence claim.

The verifier requires exactly the declared N members and distinct saved UUIDs.
Each record must match its registered `world/playerdata/<uuid>.dat` file and
the embedded UUID/state. Extra historical saves can remain, but do not become
admitted executors. Private records and raw saved data never enter gameplay
artifacts or tools. World reads use bounded evaluator-only CAS references.

Explicit `held-pair-sealed-vanilla-inputs/3` adds this check before writer
preparation and during held source validation. Paired-reference /2 requires
launch schema /2 and that software policy; mixed arm policies and mismatches
refuse. The legacy /1 server reference and /1-/2 software retain their identities
and claims. Only the new profile includes private `saved_bodies` evidence.
No deadline, budget, input guarantee, information policy or scoring rule changes.

Held preparation already reconstructs and checks the registered pair on every
call. The saved-body branch checks its pinned pair identity against that result
and rereads declarations/player bytes; it does not reconstruct the whole source
chain a second time or cache filesystem validation. Final negatives cover both
policy-downgrade directions and altered pinned pair identity. Public fixtures
use synthetic player UUIDs; authentic identity remains private.


## Executed verification

The focused selection passes35 cases in77.05s: strict record/UUID/file/state
failures, complete N=2 declared roster, duplicate identity, malformed inventory,
NBT extensions, compressed trailing data, new held runtime integration, pre-writer
mismatch refusal and mixed-profile refusal, plus existing runtime contracts.
These integration cases use actual CAS/registration/file leases with synthetic
player/software/native checkpoint fixtures and substituted process/JVM results.
The initial fixture's missing brace caused a collection failure; its original
source and error output remain retained. No production native attempt failed
or was repeated to correct the fixture.

Read-only authentic reconstruction passes12 checks against the sealed M1.6j
player save in `2026-09-25-m1-protected-vanilla-02`, pinned by
`a67e212b440d0b1cb94a52713520eee90bb10414f83b40f996bb80fc7b23a0eb`.
The audit derives a **new private declaration** from the genuine stopped bytes,
checks UUID/file pins and refuses altered health, food, position, slot and full
NBT digest. It does not backfill a historical registered body, reinterpret the
case09 fixtures, launch Minecraft or prove live initial state. The original
source seal remains unchanged. All40 live authority tables still match the
prior checkpoint at$4.887796/$10; no M1 paid allowance is inferred.

Use `PYTHONPATH=src;tools;evaluator/src` and fresh private basetemp/XML/log paths:

```text
pytest tests/test_probe_saved_bodies.py tests/test_probe_saved_body_runtime.py tests/test_probe_vanilla_runtime_contract.py -q
pytest tests/test_probe_vanilla_inputs.py tests/test_probe_vanilla_runtime.py tests/test_probe_world_copies.py -q
```

After synthetic identity selection,30 new cases pass in66.02s. Final recheck/
downgrade changes pass30 in59.50s; preserving the strict body record nested in
the evidence wrapper passes30 in59.72s, including a schema round trip. An extra
unknown-schema case passes in0.19s. The affected legacy-policy selection passes
55 in876.35s with one explicit opt-in native copier skip. Across all selections,
91 distinct cases pass. No native game/model execution this task.

## Remaining acceptance

M1.6n is implemented_unverified for authentic launch integration. The saved-body
join is exercised on genuine stopped data and in synthetic registered launch
integration. Full T11 requires actual account-to-body admission, all-N live
readiness, complete matched initial state, authoritative clocks and one-way
session/artifact disposal. T05 capable keybindings, protected T10 controls and
combined runtime isolation remain open. G1-G5 remain not_run, M0/G0 unchanged.

Coverage: F01/F02/F04/F07/F08/F16, N01/N04/N06, C06/C20/C23/C24/C36,
partial T01/T06/T11. Unrelated M2-M7 remains untouched; all old failures and
accounting holds remain retained.

## Sealed evidence and final checks

| Private evidence store | Files / bytes | SHA-256 seal |
|---|---|---|
| `2026-09-25-m1-probe-saved-bodies-01` |413 /4,395,456|`77178a73bbdd86f270b5a3c93f444130b30004801f18a62f6cbb070c82982307`|
| `2026-09-25-m1-probe-saved-bodies-fixtures-01` |3,920 /12,253,749|`b362f5eebd05726b0e9cb96d9e2e4b12108d1ec92d2fead3d7e2c801129c231d`|
| `2026-09-25-m1-probe-saved-bodies-legacy-01` |14,768 /49,707,629|`9228d35cbd9c6e19a70712e0fdf1ad98ea1b6530e3c8da2d69b0b7488bafaae0`|

The main store contains complete current Python source/tests, specification,
locks, XML/logs, original collection failure, authentic audit, source equality,
final WAL-aware40-table authority comparison and empty owned-process snapshot.
Completed test trees have explicit archive mappings and separate seals to keep
each bundle within existing file limits. Old absolute paths are data only.
The first final reader expected an unparameterized skip name; preserve its script
and UNEXPECTED_SKIP diagnostic. The corrected reader accepts exactly the actual
opt-in native skip with its `[pair_source0]` suffix. Test results are unchanged;
no test/native rerun was used to repair that reader.

Focused Ruff and whitespace checks pass. Documentation QA preserves all406 prior
milestone IDs, adds only M1.6n, preserves the append-only history and all prior
SPEC text, and resolves1,588 local links. The SPEC addition only describes this
explicit private profile. Subsequent public seal pointers do not change verified
source or test bytes. No inference/job authority was added or consumed.
