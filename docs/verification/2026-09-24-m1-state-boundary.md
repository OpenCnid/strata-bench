# M1 selected-profile state, cells and notifications

Operator-only. M1.3b.3 inherits M1.3b's F03/F04/F07/F16, N01/N04/N06,
C06/C12/C13/C20/C36 and partial T01/T04/T06 coverage. M1 remains in_progress;
G1 remains not_run. No full isolation or RuntimeQualification claim.

[Selected state canaries](../../tools/native_state_boundary.py) reuse the
[existing native state protocol](2026-09-21-native-state-isolation.md) under
the selected GPT-6 Luna catalog and conformance-only projection /3. Both callers
initialize private values, read their own values later, attempt foreign live-cell
reads/cancellation, and retrieve their own normal completion. Both attacks occur
before the target finishes. A missing-cell control matches each native denial.
The clean helper receives no parent history; positive scoped artifacts and
synthetic game observation remain available to the appropriate caller.

Each caller also publishes its own marker through notify(). Native notifications
arrive as additional string outputs under the initializer's existing call ID.
The observer separates only the exact known notification shape, caller, phase,
marker and type. All ordinary output conflicts still fail. Both notifications
reach their own caller; neither marker appears anywhere in the other's captured
model inputs. This is a within-job root/helper test, not cross-job/team messaging
or probe-disposal qualification.

## Retained outcomes

Both native attempts use the pinned CLI0.154.0-alpha.6.2/companions and Dovetail
commit from the [first boundary report](2026-09-24-m1-native-boundary.md), local
scripted provider and synthetic game worker. No real model calls, Minecraft
launch or shared-desktop input.

| Private attempt | Actual outcome |
|---|---|
| `2026-09-24-m1-state-boundary-01` | Original15/41. STATE_OUTPUT_CHANGED: the older observer treated the additional notification as a conflicting ordinary output. Native exit1 after11.731857s; one settled and one uncertain request. The synthetic job remains UNSETTLED with its full120,000 fixture-unit reservation; no refund/replay. |
| `2026-09-24-m1-state-boundary-02` | Changed observer recognizes the exact additional notification while preserving conflict rejection. Native exit0 after51.219745s. Twelve settled requests, seven root/five helper,120 input/48 output tokens,168 synthetic units once; both participants CLOSED and job FINALIZED. Original45/46 deliberately leaves independent notification review pending. |
| Independent review of `-02` |34/34: raw CAS capture hashes, ingress/admission, exact caller catalogs, settled receipts, actor-bound18 call specifications, clean spawn and actual foreign-handle arguments, normal closure, original results and reconstructed state/notification outputs. First captured request timestamps independently put attacks before peer completion. Strict single-record checks also reject duplicate or contradictory positive markers. No rerun to replace the original45/46 report. |

Exact native profiles:

- Failed `-01`: `03c81234c93a46effe2d2c232b00dea07f03d35ff9cb7121fc30240862bf0e95`.
- Changed `-02`: `7d2b2f65e7120f077463749021b23d639e942590a777380e537788ae01e5fe69`.

All40 real authority tables remain unchanged, including $4.887796 exposure,
old holds and consumed decisions. Synthetic units are not dollars or OAuth
charges. Post-run inventory finds no matching owned fixture process. Neither
this success nor the old-model state success erases the failed original run.

Private bundles under `C:/Users/Darian/.strata/evidence/` are sealed and verified
with the independent extended-path EvidenceBundle reader:

| Bundle | Files / bytes | Seal SHA-256 |
|---|---|---|
| `2026-09-24-m1-state-boundary-01` |3,795 /74,441,941| `bd860291f3c57e60c6d312632d2c45f585355c7fb2a29a70724cd8872d6ddeba` |
| `2026-09-24-m1-state-boundary-02` |3,836 /75,640,321| `ac973876bb5f301509b9ebc434a7bae400931994c54486685285d0b8744ba98f` |

## Source checks and remaining work

41 existing state/helper cases pass;36 new selected-profile scope/parser/verifier
cases pass. These include mismatched caller/phase/marker/type, changed ordinary
or notification output, omitted helper, duplicate/contradictory positive records,
extra fields and boolean coercion. Full Ruff and whitespace checks pass.

```powershell
.venv/Scripts/python.exe -m pytest -q tests/test_native_state_canaries.py tests/test_native_helper_probe.py --tb=short
.venv/Scripts/python.exe -m pytest -q tests/test_native_state_boundary.py --tb=short
.venv/Scripts/ruff.exe check .
git diff --check
```

Next review selected-profile helper lifecycle/retirement and correct team versus
cross-team communication, then complete remaining SPEC13.5 leak routes and
actual-game/credential admission. These tests do not qualify executable skills,
two concurrent helpers, probe-created canary disposal, settings, scorer controls
or full T01/T04/T05/T06/T10/T11. D18/D19 still supply no M1 paid authority.
