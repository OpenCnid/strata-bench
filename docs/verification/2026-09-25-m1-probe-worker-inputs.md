# M1.6p complete registered worker input custody

Status: **implemented_unverified for authentic registered runtime integration**.
The input-only contract passes nine distinct focused source cases on Windows.
No worker, game, provider or model executes. G1 remains not_run.

`VanillaProbeInputs.hold_worker_inputs` connects the existing complete-roster
compiler to private `held-complete-probe-worker-inputs/1` custody. Resolve every
member of both registered arms before writing the first configuration. Require
DevelopmentWorker/2, scoped operator stop, and the selected sealed profile's
account declaration to match each saved-body UUID. Read only bounded, strict
`account.json`, never token files. A single-account profile cannot silently admit
part of a roster requiring different accounts. This does not supply multi-account
assignment or authentic N=2 evidence.

Hold account declarations with actual Windows deny-write/delete file leases,
then hold every exact worker configuration and sealed runtime. Recheck live
parent preparation, complete committed bindings, declarations and runtime/config
leases. Return private copies of the resolved inputs. The object is one-use;
failure closes its own resources and leaves existing configuration evidence.
It neither releases parent capacity/cost holds nor grants any dispatch authority.
Token-refresh sibling files remain writable. Account declaration equality is not
entitlement, authenticated-session or server-login verification.

Changed files: `evaluator/src/strata_evaluator/probe_worker_inputs.py`, the entry
point in `probe_vanilla_inputs.py`, and focused tests in
`tests/test_probe_worker_inputs.py` and `tests/test_probe_worker_accounts.py`.
Public gameplay catalogs, observations, provider routes, schemas and launch gates
are unchanged. Private configuration paths/account identities remain operator-only.

Verification used actual registered-pair construction, private binding validation,
resolver and Windows file custody with synthetic pack/account/world fixtures.
Process creation is forbidden in dispatch-sensitive cases. The late-arm mismatch,
missing-stop profile and runtime failure deliberately substitute internal results
to exercise their failure boundaries; they are not authentic runtime evidence.

Executed with `PYTHONPATH=src;tools;evaluator/src` and fresh private basetemp/XML:

```text
pytest tests/test_probe_worker_inputs.py tests/test_probe_worker_accounts.py -q
pytest tests/test_probe_worker_inputs.py::test_authority_and_roster_changes_close_worker_custody tests/test_probe_worker_accounts.py -q
pytest tests/test_probe_worker_inputs.py::test_custody_failures_never_dispatch_or_release_parent -q
pytest tests/test_probe_worker_inputs.py::test_custody_failures_never_dispatch_or_release_parent -k changed_account -q
```

The first collected run passes three cases and has two test setup/assertion
failures: duplicate binding refs hit the database uniqueness constraint before
the intended custody check, and equivalent Windows paths differ by the extended
path prefix. The corrected two cases pass in16.90s. The four additional negative
cases pass three; the race correctly raises `BOOTSTRAP_FILE_CHANGED` but the test
expected a different exception family. Its corrected selection passes in16.18s.
The original three-pass run takes65.62s; the added negative run takes64.96s.
All nine distinct final cases pass without rerunning unchanged successful cases.
An earlier collection error from a module-wide fixture parameter is retained too.

Coverage includes complete both-arm custody, actual config/account write denials,
token sibling write allowance, returned-data independence, close/reentry refusal,
late-arm account mismatch before any config, partial config failure cleanup,
helper denial, committed-roster loss, strict/duplicate account JSON rejection,
missing normal stop, account mutation between snapshot and lease acquisition,
closed parent and runtime recheck failure. Parent reservations remain intact.

Coverage maps to F01/F02/F04/F07/F08/F09/F16, N01/N02/N04/N06,
C06/C20/C23/C24/C36 and partial T01/T06/T11, inherited from M1.6o.
Next connect custody to the registered runtime's bounded lifecycle and all-N live
state matching. This component has no start method and does not qualify native
admission, authoritative clocks, disposal, scorer controls or capable T05.
Preserve all original failures, source identities and missing native configuration
references; use fresh declarations rather than backfilling sealed evidence.

The WAL-aware final audit matches all40 authority tables to the pre-task snapshot
and the preceding sealed checkpoint. Exposure remains$4.887796/$10, including the
old$0.7554 hold and four$1 failed-job envelopes; consumed decisions remain consumed.
No owned runtime remains.426 source/test/tool/lock files are retained with hashes.
D18/D19 does not extend paid inference authority to M1.

Private evidence `2026-09-25-m1-probe-worker-inputs-01` is sealed and independently
verified:3,477 files/15,619,247 bytes, SHA-256
`e8200784ad3b22b3167b7408443b157f8ff06af335155c79aef9dda2dc6dc7ae`. It retains source, failures, passing logs/XML,
accounting and process snapshots, documentation and audit scripts/results.
Documentation QA preserves410 prior IDs, adds M1.6p, keeps append-only progress
and prior SPEC text, and resolves1,607 local links. Focused Ruff/whitespace pass.
The final seal pointer is appended after the archived documentation snapshot.
