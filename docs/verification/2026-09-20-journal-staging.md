# Reusable stopped-journal staging

M0.2k.2a; F06/F09/F11/F16, N01/N02/N03/N04/N06/N08;
C15/C18/C20; partial T07/T12/T13 and G0 items 4/6.

`evaluator/src/strata_evaluator/journal_restart.py` replaces the one-off journal
transfer mechanics with a typed private operation. It validates complete source
cost reconciliation, exact stop-attestation pins, unchanged authority, increasing
epochs, remaining lifetime and input headroom. It copies exact frozen database
and native-journal bytes, preserves unknown receipts and performs no replay,
refund, renewal or launch. Publication uses an exclusive new directory and a
manifest committed last; interrupted publication retains an incomplete directory
which subsequent calls refuse to overwrite. [Operator contract](../operations/journal-restart.md).

Initial focused run: `python -m pytest -q tests/test_journal_restart.py` passes
15 synthetic cases in 1.37 s. After strengthening interrupted publication,
the affected single/multi-epoch success, CLI and interruption cases pass:
four passed/12 deselected in 0.73 s. Targeted Ruff passes. Coverage includes
expired/renewed authority, changed scope/pins, stale epoch, active WAL, source
changes and expiration during copy, strict terminal flags, retained unknowns,
complete byte equality, existing destinations and interrupted publication.

Actual retained Forge restart evidence is also checked without launching a
game. Its complete cumulative source reconciles, then staging correctly rejects
the expired original authority with `RESTART_AUTHORITY_EXPIRED`. No destination
is published, authority renewed or inference dispatched. Private plan,
source-bound terminal attestation and result are under
`C:\Users\Darian\.strata\evidence\2026-09-20-forge-reconnect-02\reusable-staging-01`.
That observation used the initial source digest
`5625cedb457c1b2b84fa71749cb3af3b2ece7c6b4282e51e217e78fccc4d55ed`;
the subsequent publication change has digest
`8406710ef83606937c28104f36706e2afa07aa06662dbeab30310b2d1b101d74`.

Successful staging is synthetically verified; the new operation has not yet
fed an authentic restarted client. The preceding authentic restart used the
retained one-off staging script. Its two guardian failures remain unchanged.
An operator attestation does not establish authenticated process isolation,
complete checkpoint consistency or safe campaign admission. M0.2k.2a remains
implemented_unverified for its authentic success path; G0 remains fail.
