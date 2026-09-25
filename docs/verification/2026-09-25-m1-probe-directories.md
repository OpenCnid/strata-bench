# M1.6k — directory-bound matched pair preparation

September 25, 2026. D20 authorizes this required M1/G1 state-preservation work.
M0/G0 and unrelated M2-M7 remain unchanged; full G1 remains not_run. No native,
game or model execution and no paid inference occur in this verification.

## Implemented behavior

The earlier pair contract records world files but cannot declare empty world
directories. Preserving only sealed empty software directories would leave that
gap. `ProbeFixture/2` and `ProbePairRequest/2` now select the distinct
`private-matched-probe-pair-staging/2` contract. Require a sorted, unique,
case-unambiguous directory list, every file/directory parent, safe world/external
roots and no file collision or private credential/instruction path. Include the
directory list in the committed world identity and both staged trees. Existing
verification consumes a failed check; repairing files/directories cannot rearm
it. A /1 request cannot accept a /2 fixture or vice versa. Native views parse
the exact versioned request and keep their original source/digest checks.

`held-pair-sealed-vanilla-inputs/2` requires that directory-bound pair and writer
preparation /4. Compile the complete sealed software directories plus registered
world directories, including empty paths. The declared `external` namespace
root disappears only because its six permitted mutable files map to the server
root. Reject unsupported external subdirectories and world layouts. Validate
exact directory inventories in both writer plans and both copied trees before
borrowing and after the callback. Legacy policy, writer and file-only copying
cannot silently downgrade the directory-bound pair. Legacy /1 identities and
its explicit unsupported-empty-software refusal remain intact.

All prior source/file/native-runtime custody, whole-pair resource/cost holds,
finite deadlines and explicit unlaunched close remain. Serialized results and
surviving paths grant no authority. This change does not launch either arm or
claim live initial-state equivalence, actual catalog loading, isolation or
one-way post-probe disposal.

## Verification scope

Tests use synthetic sealed game bytes and synthetic checkpoint/protocol/native
records. Pair preparation, native views/bindings, Windows file leases, budget
reservations and the coordinator are real. Native writer execution and copied
tree ACLs are substituted; actual Java copying belongs to the separate M1.6j
profile and is not silently promoted to a native paired-game result.

New cases cover both legacy-directory and explicitly empty-software layouts,
world-directory identity, exact copies, private/colliding/missing directory
rejection, policy mismatch/downgrade, staged/copy tampering and retained failure
holds. A declared empty world directory changes the world digest even when all
file bytes match. Both copied worlds retain the exact declared empty directories.
Directory mutation leaves FAILED/FENCED and retains200 synthetic units plus the
whole-pair capacity reservation. No costs are settled or refunded.

The initial validator test expects an unwrapped `Fault`; Pydantic correctly
wraps model-validator failures in `ValidationError`. Correct only the assertion
type; preserve the failing output and unchanged rejection behavior.

Commands use `PYTHONPATH=src;tools;evaluator/src` and `.venv/Scripts/python.exe`:

```text
-m pytest tests/test_probe_vanilla_inputs.py -q -x -k "directory_bound or directory_mutation or legacy_pair_cannot"
-m pytest tests/test_probe_directory_contract.py -q -x
-m pytest tests/test_probe_directory_contract.py tests/test_probe_pairs.py tests/test_native_probe_views.py -q -x
-m pytest tests/test_probe_vanilla_inputs.py tests/test_probe_world_copies.py tests/test_probe_directory_contract.py -q -x -k "not directory_bound and not directory_mutation and not legacy_pair_cannot and not actual_native_pair and not directory_contract and not directories_participate and not changed_staged and not fixture_and_request"
-m pytest "tests/test_probe_directory_contract.py::test_directory_contract_refuses_missing_parents_collisions_and_private_paths[directories9]" -q
-m pytest tests/test_probe_directory_contract.py::test_unknown_software_policy_is_rejected_before_preparation_access -q
```

The first command passes10 in314.96s. The second retains the one assertion
failure. The corrected contract/pair/native-view command passes71 in272.58s.
The remaining affected routes pass28 in624.52s. Two later focused checks pass1
each: nested credential-cache directories and unknown software policy. These
are111 distinct passes:27 new and84 affected existing cases. Ruff and whitespace
checks pass. No unchanged native or paid execution is repeated.

All40 real durable authority tables remain unchanged before/after; exposure is
$4.887796/$10 with every original hold and consumed decision. No owned runtime
remains. The completed71-case contract archive is moved once into a separate
private evidence bundle to keep each bundle within the reader's16,384-file
limit. An explicit original-to-archive path mapping is sealed in both bundles;
file bytes and stored absolute paths are unchanged. Archived paths are data,
never permission to read unsealed original locations. Directory inventories
are sealed explicitly so read-only verification can check empty directories
as well as every recorded file byte.

Sealed read-only reconstruction passes66/66. It verifies both producer file and
directory inventories, the archive mapping, versioned fixture/request/writer
chain, directory-bearing world identity, source/pack joins, complete directory
sets and every copied file byte for both layouts. It also verifies both source
native-view records, unlaunched dispositions, both mutation failures/fences,
retained200-unit/capacity holds and unchanged real authority. Both producer
seals remain unchanged. This is an audit of synthetic preparation evidence;
it does not create or qualify a native/game run.

| Private evidence store | Files / bytes | SHA-256 seal |
|---|---|---|
| `2026-09-25-m1-probe-directories-01` |9,846 /38,410,824|`96d4e65198ec400dcc4a8ed0658155fbe5693dcb8e78fce656f99a73adae3f09`|
| `2026-09-25-m1-probe-directories-contract-01` |5,861 /38,731,509|`20e30ebb8f47e915c62cc67372724e5da665cdbd35dbc5ec14433325b378d70a`|
| `2026-09-25-m1-probe-directories-audit-01` |3 /9,700|`de5c4fec108bf722042a9f633d988c711bfe689d0176239b5127914dc9545a72`|

## Remaining acceptance

M1.6k is implemented_unverified for authentic paired/native probe integration.
Next bind these exact registered states to a reviewed held server/worker
coordinator. The M1.6j restored-baseline session cannot be relabeled as a pair
launch: it expects its own sealed restoration identity, while this pair combines
registered evaluator state with fresh software. Both original input/hold owners
must remain live through readiness, stopped export and one-way disposal. Keep
native probe admission closed until complete scoped runtime and live initial
state checks exist. T05, scorer controls and remaining combined runtime routes
still block full G1. No M1 inference allowance is inferred from D18/D19.
