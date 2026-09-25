# M1 selected-profile helper retirement

Operator-only. M1.3b.4 inherits M1.3b coverage plus F11/C18. M1 remains
in_progress, G1 not_run; no full lifecycle or RuntimeQualification claim.

The existing [retirement protocol](2026-09-21-native-retirement.md) now has a
narrow selected GPT-6 Luna conformance fixture using exact helper catalog /3.
Revocation retains the one helper slot until settled native status evidence
proves retirement. An old helper follow-up is rejected before forwarding;
a fresh replacement has a distinct thread, namespace and envelope.

The actual pinned CLI/companion/Dovetail run uses a local scripted provider,
fake OAuth and synthetic worker. Zero real model requests, Minecraft launches
or shared input. Profile:
`57ff7e592d8c1784c8f0415dc5528c1f87c840802b14b7f2b7d448ead0eeff10`.
Fifteen admitted/settled requests (11 root,2 original helper,2 replacement),
one rejected resume,150 input/60 output tokens,210 synthetic units counted once.
Native job FINALIZED exit0 after42.035235s; three participants/envelopes CLOSED.

Original33/34 is preserved. Its upstream-credential count incorrectly expected
forwarding for the rejected request as well. The corrected verifier joins only
forwarded operations and request digests, rejects missing/extra/duplicate upstream
requests, and separately leaves rejection/admission/closure proof mandatory.
A received-only entry is not, by itself, proof of refusal. No rerun was used.

Independent16/16 reconstruction verifies all15 raw CAS captures, authenticated
ingress/admission, exact tool projections, settled usage, three distinct closed
identities/envelopes and aggregate accounting. It reads the actual settled raw
provider response issuing list_agents, then its caller-bound native result:
revocation fence6, issuance7, first observation8. Replacement begins afterward.
The old helper has no new admitted/forwarded request. Source-bound cell-drain
reconstruction confirms its one completed exec and zero yielded/pending cells.
This completed-helper sample does not prove interruption of live background work.

All40 real authority tables, exposure/holds and consumed decisions remain
unchanged. No matching fixture process remains. Private bundle
`C:/Users/Darian/.strata/evidence/2026-09-24-m1-retirement-boundary-01`
contains3,854 files/76,104,979 bytes. Independently verified seal:
`4cad49ee5b8d51dbf5074acdbeab392f48b8ac66807a6027e4730b56faf6e4b1`.

40 existing retirement tests and66 selected scope/notification/credential-join
tests pass; the latter include30 new retirement-scope and credential cases.
Full Ruff and whitespace checks pass.

```powershell
.venv/Scripts/python.exe -m pytest -q tests/test_native_retirement.py --tb=short
.venv/Scripts/python.exe -m pytest -q tests/test_native_state_boundary.py --tb=short
.venv/Scripts/ruff.exe check .
git diff --check
```

Review found a further G1 dependency: source-bound cell drain currently treats
notify's additional same-ID output as a duplicate, and must never mistake
notification text resembling a terminal status for actual completion. Resolve
that path with authentic output-envelope evidence and negative spoofing tests,
preserving the existing pending-cell/uncertainty holds. Cross-team communication,
other SPEC13.5 routes, actual-game/credential admission and wider G1 remain open.
