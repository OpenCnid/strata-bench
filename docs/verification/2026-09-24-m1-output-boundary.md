# M1 native media-output boundary

Operator-only. M1.3b.2 inherits M1.3b's F03/F04/F07/F16, N01/N04/N06,
C06/C12/C13/C20/C36 and partial T01/T04/T06 coverage. M1 remains in_progress;
G1 remains not_run. No RuntimeQualification is issued.

[Output canaries](../../tools/native_output_boundary.py) extend the
[first boundary fixture](2026-09-24-m1-native-boundary.md) with native code-mode
output helpers. Root and clean helper each supply a known inline PNG successfully,
then attempt an owned private PNG through local path/file URL, owned listener
URLs through image/generatedImage, and owned local/remote audio targets. Actual
native errors reject all six private routes. The listener sees no unauthorized
request; the private PNG and other canaries remain unchanged. This tests output
helpers separately from the disabled view_image tool.

The strict verifier requires both caller identities, consistent repeated context,
all eight exact probe results, and precisely one matching public image output per
actor. Missing, duplicate, contradictory, foreign or unrecognized outcomes and
substituted media fail. Merely reporting that image() returned is insufficient.
notify is present in the catalog of globals but its behavior is **not tested**
by this slice. It and other output encodings remain open.

The actual native run uses CLI0.154.0-alpha.6.2 and the same pinned companions,
Dovetail commit and selected GPT-6 Luna metadata as the first slice, with
conformance-only catalog policy /3. Its exact profile is
`e1553b02e2dde26f941c72b7ea60a924d9ee9cdadca86e3bb10597eaf3d02e20`.
The local scripted provider and synthetic game worker issue **zero real model
requests and launch no Minecraft**. Eleven requests settle to110 input/44 output
tokens and154 synthetic fixture units; native job FINALIZED exit0, both
participants CLOSED. This is native runtime evidence, not model-selected play.

The original report passes75/76, deliberately leaving independent output review
pending. It is preserved unchanged. Offline reconstruction passes33/33, joining
all11 raw CAS captures to ingress/admission/catalog/settled receipts, checking
both caller outputs, exact image bytes, closure and aggregate accounting.
No rerun was used to replace the original report. All40 real authority tables
remain unchanged, including every historical hold and consumed decision;
post-run inventory finds no owned fixture process.

Private bundle `C:/Users/Darian/.strata/evidence/2026-09-24-m1-output-boundary-01`
contains3,788 files/74,138,164 bytes. Verified seal SHA-256:
`c469406786e2747ed8739d6f02823249e7b99dbb60f52fecd9556a0dc4163a25`.
The first manifest was rejected with EVIDENCE_INVENTORY because ordinary Windows
path enumeration omitted long plugin paths. That failed manifest is retained
inside the final bundle; all its originally listed bytes were checked unchanged.
The corrected extended-path inventory passes the independent EvidenceBundle
reader, including the original result digest. Use the `.verified-seal.json`
external pin, not the retained rejected `.seal.json` sidecar.

49 corruption/owned-target tests pass:

```powershell
.venv/Scripts/python.exe -m pytest -q tests/test_native_output_boundary.py --tb=short
.venv/Scripts/ruff.exe check tools/native_output_boundary.py tests/test_native_output_boundary.py tools/native_mcp_identity_probe.py
```

Next test notification and cross-agent state/communication/lifecycle surfaces
under the selected profile. Full authentic-game, credential, executable-skill,
two-helper, settings, scorer and matched-probe acceptance remains open in the
[G1 audit](2026-09-24-g1-coverage-audit.md). Historical failures and profile
identities remain intact; no M1 paid authority is inferred from M0 decisions.
