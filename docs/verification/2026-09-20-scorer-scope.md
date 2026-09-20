# Private scorer source and receipt binding

M0.2c.2 / M3.1; F04/F09/F10/F13/F16, N01/N02/N04/N06/N08,
C18/C24; partial T01/T06/T07/T10/T13 and G0 item 5.

The retained synthetic reproduction shows the defect: four units from the
expected campaign plus four from an unrelated campaign completed an eight-unit
predicate when actor, team and recipe labels matched. The original scorer
source SHA256 is `1dc3b8a3ec45094878b50a31f10f7eb56fc84b47cbab512c8fbb6932c0d3e62d`.
The reproduction is private under
`C:/Users/Darian/.strata/evidence/2026-09-20-scorer-scope-01/before.json`.
The first invocation lacked the evaluator import path and failed before execution;
the corrected invocation retained the demonstrated false completion.

`Scorer.register_source` now binds a private instance to a campaign and evidence
kind, each predicate to its complete definition, and each permitted epoch to
one server boot. Registration precedes scoring; received events cannot establish
their own authority. A later source must use a strictly greater epoch and a new
boot. Exact repeated registration is idempotent. Historical registered sources
remain available for offline replay. All predicates in an instance share its
campaign/evidence kind and boot mapping.

The transaction receipt also pins the complete payload, kind, schema and actor
list. An unchanged receipt can be deduplicated across explicitly registered
restart sources. Changed content under that ID fails, including after completion;
later events still receive conflict-detecting receipts without adding output.
Rejected scope/receipt changes roll back without altering score or event tables.
Existing unbound score history is retained and blocks automatic registration;
there is no guessed migration or relabelling of previous results.

Verification: `python -m pytest -q tests/test_scorer_scope.py
tests/test_evaluator.py tests/test_craft_witness.py tests/test_telemetry.py
tests/test_telemetry_configs.py` passes **112 cases in 1.70 s**. These include 14
new boundary cases plus existing alternate-strategy, gift/admin/wrong-team,
machine-window and raw-telemetry rejection controls. Targeted Ruff passes. The real compiled gameplay package exclusion check also passes (one case, 0.26 s); this proves only the allowlisted bundle, not runtime isolation.

Registration records operator assertions and supporting digests; it does not
authenticate a process, verify referenced artifacts, establish setup/team
provenance or prove isolation. Every returned score retains its evidence kind
and `scoring_authority_qualified=false`. Raw Forge callbacks and resource witnesses
remain unscorable. Authentic admission, positive/negative controls and nonleakage
remain open; this fixes the private calculation boundary without passing G0/T10.
