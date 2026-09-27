# Native furnace resource verification

M1.5b.4 continues M1.5b/.1/.2/.3b and the G1-required M3.1b dependency.
Mappings remain F04/F10/F16, N01/N04/N06/N08, C12/C18/C24 and T01/T06/T10.
Protected scorer admission remains incomplete; G1 remains not_run.

The existing completion verifier accepted three separate boundary events. The
native producer actually emits one event containing three ordered states. The
new [native verifier](../../evaluator/src/strata_evaluator/machine_resource.py)
checks that actual V2 format without inventing events, sequence numbers or player
attribution. It shares unchanged arithmetic with the original
[boundary verifier](../../evaluator/src/strata_evaluator/machine_witness.py).

An independently supplied recipe expectation must match the observed source
registration ID, input/output full stack identities and counts, resolved input
count, deterministic output chance and recipe energy. Converted recipes retain
both IDs; their machine ID cannot substitute for the source ID. The witness
retains generation, complete registration, original scope/sequence and exactly
one original event digest. Ordered consumption/output and unchanged unrelated
resources remain mandatory. The verifier does not deduplicate or ingest events;
its caller must authenticate the complete stream and bind scope/recipe beforehand.

Focused verification:

- `python -m pytest tests/test_machine_resource.py tests/test_machine_witness.py tests/test_machine_registration.py -q`: **105 passed**, including 23 new cases. Gift/no-consumption, wrong/reordered effects, changed energy/charge/progress, mismatched recipe/resolved count, legacy/refusal/partial payloads and false authority are rejected. The scorer still rejects a resource-verified raw event without creating predicate state.
- Ruff passes on the three changed Python files. Initial lint reported five imported-pytest-fixture F811 diagnostics; explicit fixture annotations resolve them without behavior changes. No failing pytest cases occurred.
- Read-only reconstruction verifies operation04's original sealed inventory and authenticates all **230** signed records. All **three** actual completions pass the new verifier at ticks3780/3822/3863, preserving three distinct transactions and three original event digests. No game or model run was repeated.

The reconstruction's explicit expected recipe is a **post-hoc audit expectation**,
not pre-registered fixture authority. It demonstrates the verifier on retained
authentic records; it does not close protected fixture registration. Raw payloads
and witness outputs remain unscorable. Producer/loaded-code authentication,
setup/team, full RF/fluid/window history, parity, isolation and authentic T10
negative/alternate-strategy controls remain open. Recipe energy4000 is not a
measurement of RF consumption. Operation01/02/03 failures and all consumed
decisions/holds remain unchanged.

The next protected admission work must bind a prior machine recipe/fixture plan
to actual protected launch/setup/team and authenticated transformed producer,
then exercise its required controls. No existing false authority flag may be
promoted merely because this resource comparison passes. Selected-model M1
verification still requires authority beyond D18/D19's M0-only allowance.

Private evidence: `2026-09-26-m1-native-resource-01` contains source snapshots,
test XML/log, replay procedure/result and authority/process checks. The source
operation04 seal remains `f0963cc8d19fcb2ba763901c4ac2880c7043161a0929b316cd72d108c19b537c`.

Final audit passes:502 source pins,446 preserved/unique milestone IDs,
1,835 local documentation links, all40 authority tables unchanged at4,887,796
microUSD and no owned runtime. Archive seal:
`e252304dd5a92b54f880e6b1769c5ee59af8b644903a0c5bccd9583c16850342`
(21 files,2,168,443 bytes). This seal pointer is added after the archived document
snapshot; the archive is not rewritten.
