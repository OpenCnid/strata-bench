# M1.5b.9: prior-bound machine operating windows

The complete operation11 stream establishes actual sampled continuity but its
V4 plan does not register an operating-window admission contract. This change
adds that missing private contract without retroactively upgrading prior runs.
M1.5b.9 is `implemented_unverified` for authentic prior-bound execution; M1
remains `in_progress`, G1 `not_run`.

## Contract and implementation

`PrivateCraftReferencePlan/5` requires
`thermal1192-private-machine-reference/2`. Each registered target has exactly
one operating-window declaration, selecting either exact inclusive ticks or
the first observed start through its first subsequent refund. Bounds and
minimum duration/net RF are finite; targets, recipes and enclosing exposure
remain bound by the sealed plan. No best-window search or fallback to a later
successful episode is permitted.

The new private `machine_window.py` joins existing complete interval traces with
their original processing, transition and completion events. It requires:

- One actual lifetime, complete consecutive ticks, exact child/state joins and
  no intervening retirement or unproven transfer/charge change.
- A complete inactive-to-inactive episode with zero boundary progress. Every
  tick must perform fully funded processing; idle padding cannot count.
- Registered recipe facts and matching observed registration/recipe identity
  throughout each cycle. Registered direct/converted alternatives remain valid.
- Completion-only input/output credit, exact endpoint resource balance, all
  processing debit and the final unclamped refund. Net endpoint RF must equal
  completed recipe energy and meet the prior minimum.

Unsupported, replaced, refused, incomplete, underfunded or mismatched evidence
returns zero window candidate output and a typed reason. Completed outputs
elsewhere cannot satisfy the selected window. Retained children have a finite
quota; existing stream duplicate, authenticity and clean-stop checks remain.

The authenticated reader can compare a supplied plan but keeps prior-registration
false. Only `CraftReferenceStore.inspect` verifies the immutable plan/authority,
consumed one-use launch, matching ordered seal/reservation outbox records and
applicable stopped pair/custody/dispatch proofs. Its new
`PrivateCraftReferenceInspection/5` retains registration cursors/digests and
marks prior registration on the selected window evidence. Reopening is
idempotent; missing, duplicate, changed or reversed registration publishes no
receipt. Old schema/report shapes remain unchanged.

Private comparison/registration is distinct from protected scoring. Loaded-code,
setup/team, fluid/automation provenance, parity and isolation flags remain false;
the development scorer gains no raw-window ingestion route. No gameplay/helper
tool or information policy changes. Wider resource requirements remain open.

## Executed verification

200 distinct focused Python cases pass; three existing native opt-in cases are
skipped. This includes45 new window cases. The main selection passes196;
four added idle/replacement cases pass separately. A strengthened nested
registration assertion passes in one overlapping case, counted once.

```text
pytest tests/test_machine_window.py tests/test_machine_reference.py tests/test_machine_interval.py tests/test_craft_reference.py tests/test_protected_reference.py tests/test_telemetry.py tests/test_telemetry_auth.py tests/test_gameplay_package.py -q
pytest tests/test_machine_window.py -q -k prior_seal
pytest tests/test_machine_window.py -q -k "complete_idle_trace or valid_replacement_trace"
```

All use the workspace `.venv/Scripts/python.exe -m pytest`. Tests exercise both
selectors, thresholds, exact resources/RF, wrong recipes, native underfunding,
mid-cycle registration changes, missing/refused/gapped evidence, three actual
wire retirement reasons, replacement without lifetime splicing, fully valid
idle traces, direct/converted alternatives, sealed authenticated integration,
prior-order failures, idempotent reopening and protected launch digest binding.
These are labeled synthetic streams and fixtures, not authentic game controls.

Initial integration results6 fail/31 pass are retained: the synthetic insertion
used ticks18/19 after an existing tick20 health record, and one assertion expected
an unwrapped fault instead of Pydantic's validation error. Correcting only those
fixtures exposes a further underfunding-fixture alias error (1 fail/40 pass): a
recursive edit changed shared state objects more than once. Visiting each object
once fixes the fixture. Initial source snapshots, all failures and41 Ruff
formatting findings remain archived. No production check was relaxed; final
focused Ruff and diff checks pass.

Read-only reconstruction authenticates all1,708 operation11 records and exactly
reproduces the original inspection. A separately labeled post-hoc V2 comparison
finds84 ticks, two complete cycles,8,064RF debit/64RF refund and8,000RF net
consumption, with all89 child joins. Its prior-registration flag correctly stays
false. The original evidence seal verifies before and after; no old database
or evidence bytes are changed.

## Remaining execution and authority

Next prepare one fresh V5 reference with the operating-window rule sealed before
launch. Keep the existing producer/client/ordinary checker/time bounds, and
verify actual prior-registration plus complete window/import/terminal joins.
Native replacement/refusal controls, full producer/setup/team authority,
alternative/negative scorer controls, overhead/parity and remaining G1
native-host/isolation/keybinding/probe criteria remain required.

All40 controller authority tables remain unchanged at4,887,796microUSD. No game
or model run, installation or spending-authority change occurred. D18/D19 remain
M0-only; all historical failures, holds and consumed grants remain. Private
evidence: `C:/Users/Darian/.strata/evidence/2026-09-26-m1-machine-window-source-01`.

Final audit passes:454 retained/added milestone IDs,1,920 local document links,
40 unchanged authority tables and the original operation10/11 seals.
Operation10's separate256 MiB reservation remains held. Source evidence sealed:
41 files/2,491,599 bytes, SHA-256
`95b9a9b51065ed547352bb1bba67dea86972aac2a51fa4fd2ac51628ceb3f7bb`.
The archived source snapshot precedes this seal-pointer addition.
