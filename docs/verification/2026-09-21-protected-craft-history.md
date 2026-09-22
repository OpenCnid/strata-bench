# History-required protected craft

September 21, 2026. Operator-only. M0.2c.3b.3c.2; partial F04/F09/F10/F13/F16,
N01/N02/N04/N06/N08, C12/C18/C24, T01/T06/T07/T10/T13 and G0 item 5.
M0 remains incomplete, G0 fails, and G1–G5 are not run.

The successful D13 protected craft used telemetry 0.3.6. It supplied native
setup points but no mutation history. The 0.3.7 monitor had separate headless
startup and world-mode-control evidence. This change connects those components
under an explicit requirement, rather than inferring history from a successful
craft or relabelling the earlier stream.

`PrivateCraftReferencePlan/3` requires the registered mutation-history policy
alongside the existing roster/team binding. The protected launcher authenticates
the complete clear startup/history prefix, checks its retained-process launch
identity, and journals it before publishing participant readiness. Partial
writes wait within the original deadline. Legacy modules, missing hooks,
tainted baselines and changed identities cannot admit the client. Import rejects
a valid point-only stream with `CRAFT_NATIVE_HISTORY_MISSING`; version-3 reports
retain the required policy. Existing taint, resource-witness, stopped custody,
one-use launch and exact-byte checks still apply. Legacy plans remain readable.

Implementation is in `craft_reference.py`, `protected_reference.py` and
`reference_launch.py`; the existing signed-prefix parser is shared with private
mutation controls. No game operation, command interface or public observation
was added. Complete route coverage, setup continuity, mechanical parity,
isolation and scoring remain unqualified.

Focused source verification on Windows / Python 3.12.14:

- `pytest -q tests/test_setup_history.py tests/test_setup_control.py
  tests/test_protected_reference.py`: 94 pass, four JVM opt-in cases skipped.
- With pinned Temurin 17 and the telemetry test-classpath **file path** supplied,
  the four signer/owned-JVM cases pass. An initial invocation mistakenly supplied
  the classpath contents instead of the file path and failed before the fixtures
  ran; that setup error is retained here. These are synthetic event/control tests.
- `pytest -q tests/test_craft_reference.py tests/test_setup_facts.py
  tests/test_reference_client.py`: 98 pass, two unchanged native opt-in cases
  skipped. This checks legacy import and client binding compatibility.
- Changed-file Ruff and whitespace checks pass.

## Changed-profile authentic integration

One fresh reference is registered in the private
`2026-09-21-protected-craft-history-01` bundle. It uses an independent copy of
the original unplayed pinned fixture, telemetry 0.3.7
(`ea112c9e2cd9d5573a407a5e7a35cb075425ba7b1408e24ecc5a6c219cd2a93e`),
history-required plan 3, and the unchanged D13/CPU4/bundled-preparation profile.
Original source and old evidence stay untouched. The original authority was
rechecked: $0.7554 held plus $0.001458 settled, D12 consumed, zero new model
calls planned. Shared-desktop input remains paused.

Case 01 failed `REFERENCE_PARTICIPANT_EXPOSURE` after 406.219 seconds overall.
Its complete authenticated clear startup prefix matches the retained-process
identity and telemetry 0.3.7. Startup left insufficient room for the registered
420-second participant window, so no readiness or client process was admitted.
All 29 held outer-tree processes exited; no Java remained. Unused prepared
credentials were retired. The retention audit passes 16/16 checks, including
independent signed-prefix reconstruction, unchanged source/input pins, rejected
candidate import and unchanged original accounting. This is a **failed trial**,
not a craft, shutdown or scoring pass. An initial retention-audit assertion
expected a null client result; the actual outer cleanup records a missing
client-result diagnostic. The original audit script is retained beside the
corrected assertion. No game was replayed.

Case 01 seal: 8,943 files / 633,266,197 bytes; manifest SHA-256
`fdebae626e3df4b49c60933859113366fae473819918162675aa577bf8828de6`.

Fresh case 02 registers a smaller client reservation: 335 seconds plus 10 seconds
terminal reserve, within a 360-second participant window. The 600-second server,
120-second server cleanup, 900-second outer custody and D13 limits remain
unchanged. This is a prospective allocation within existing caps, not a relaxed
acceptance threshold. It uses the same verified, unplayed source bytes from the
sealed failed case.

Case 02 passed the new signed startup admission and published the full registered
360-second window. The client failed `GAME_BRIDGE_STARTUP_TIMEOUT` at 271.078
seconds, before native identity/bootstrap, worker startup or world join. The
preserved client log ends during JEI recipe registration; it includes a Nomadic
Tents/JEI class-loading error, whose causal role is unproven. No craft or guardian
sample exists for this case. The registered startup bound was not increased.

The pair stays uncertain/failed at 694.344 seconds. Its server stopped after the
client failure and retains `REFERENCE_OUTER_ABORTED`. The independent failure
audit passes 19/19 checks: exact signed startup/terminal history with clear
counters and one native stop, no craft witness, unchanged source pins, rejected
candidate import, retired client credentials, unchanged input desktop and
complete retained outer process trees (server 29/29, client 13/13, zero active).
No Java remains; accounting and consumed D12 are unchanged. These checks verify
failure retention and partial behavior; they do not turn either trial into a pass.
The prepared success/guardian audit scripts were not executed for these failed
cases.

Case 02 seal: 362 files / 75,217,987 bytes; manifest SHA-256
`1e3162f0b4fc0c6b7541762b1b77047c9e7330a4540dd19b6a9cd3a24d2a01c3`.
Both complete sealed inventories and every listed file were rechecked. The
unchanged D13 bundle also rechecks at 609 files and its original manifest hash;
an initial inventory comparison needed normalization of its Windows separators.

M0.2c.3b.3c.2 remains **implemented_unverified**: authenticated history admission
works in the protected path, but the integrated craft/history result is still
missing. Do not repeat either consumed scope or rerun the unchanged client merely
to obtain a passing sample. Continue independent M0 provenance/lock and recovery
work; return to this integration after a relevant client-startup/resource fix.
The original D13 normal-stop pass and all older 500-ms failures keep their exact
scope. Full scorer controls, route coverage, isolation and G0 remain open.
