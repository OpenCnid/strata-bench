# Pinned native plugin discovery and skill-body conformance

September 20, 2026. Operator-only. M0.1c.2a; F03/F07/F11/F16,
N01/N03/N04/N06, C06/C18/C20 and partial T01/T04/T07/T12.
Implemented but unverified for production. No aggregate gate is closed.

## Actual scope

The exact Codex executable and Dovetail commit from the
[dispatch report](2026-09-20-native-dispatch.md) run with fresh profiles,
workspaces and temporary directories. Each profile installs the plugin using
the actual native plugin commands. No account credentials are imported and no
remote inference is performed. A deterministic local provider drives one fixed
public skill-file read through the actual native `functions.exec` /
`tools.exec_command` loop. The separate upstream wire gateway reserves before
dispatch, records usage, deduplicates receipts and closes each fenced envelope.

The final three cases pass at private external directory
`C:\Users\Darian\.strata\evidence\2026-09-20-native-plugin-final-01`.
Its manifest pins the tested source and executable; installation reports pin
the exact plugin commit and installed bytes. Requests, journals, fixtures and
accounting stores remain external. All owned processes and listeners stopped.

| Case | Observed evidence | Synthetic accounting |
|---|---|---|
| Enabled | Six implicit top-level skills appear; no nested fixture skills appear; the exact prompt-engineering skill text returns through the shell/tool loop | Two dispatches, 28 synthetic microUSD |
| Disabled | No plugin skill entries appear; no skill-read tool call is emitted | One dispatch, 14 synthetic microUSD |
| Explicit | Both spark-steering and upsum bodies are injected into the initial request by native `$dovetail-codex:...` mentions; the six implicit entries and regular skill read also pass | Two dispatches, 28 synthetic microUSD |

The five calls all settle, receipts deduplicate, and all three envelopes finalize.
The installed plugin tree is identical before and after each case. These prices
are deliberately synthetic: actual project inference expenditure is zero.
The fixture does not establish model reasoning, effective use of skill advice,
immutable filesystem protection, helper behavior, game interaction or live
OAuth billing. Native system skills still exist in the fresh profile; the full
permitted-tool/corpus boundary has not been qualified.

## Changes and retained failures

- Windows long fixture paths exceeded ordinary Python path handling after the
  native install succeeded. Inventory I/O now uses the extended Windows path
  consistently for both link/reparse rejection and installed-byte reads.
  The Git source pin and normalized manifest names are unchanged.
- The prior installer returned a literal-quoted dotted plugin override key.
  This pinned CLI treats those quotes as part of the key. The actual enabled
  catalog appeared only after using `plugins.dovetail-codex@strata-pinned.enabled`.
  The installer also preserves the CLI's registered canonical marketplace path
  and explicitly enables its observed plugins feature.
- Native discovery exposed five public nested package-test skills in addition
  to six implicit real skills. Upstream spark-steering and upsum are explicitly
  marked `allow_implicit_invocation: false`; their absence from implicit discovery
  is correct. Discovery policy `dovetail-top-level-eight/1` disables the five
  nested fixtures through native `skills.config` while preserving all eight
  top-level skills and their upstream invocation policy. Native override
  serialization now handles proper TOML inline tables; null remains rejected.
- The first skill command was rejected by native command policy while no Windows
  sandbox implementation was selected. Explicitly configuring the documented
  `windows.sandbox="unelevated"` in this fresh fixture profile allowed the fixed
  read. No bypass flag or shared-desktop input was used. This sandbox is not a
  demonstrated private-data/process/network boundary for Strata.
- The fixture initially expected absolute catalog paths and a scalar tool result;
  the pinned runtime uses skill-root aliases and typed text chunks. Both checks
  now decode the observed wire format and compare the actual skill body.

Private attempts `2026-09-20-native-plugin-01` through `-10` retain all failures:
long-path inventory, absent catalog, alias mismatch, exposed nested fixtures,
rejected read and result-decoding failure. Unknown usage retains its reservation;
failed diagnostic calls are not converted to free successful samples. `-11`
passes enabled/disabled and `-12` passes explicit invocation. The final matrix
supersedes neither their source identities nor the failed history.

The first long-path unit fixture also failed because its setup did not enable
Git's long-path setting. After applying that setting to the real Git fixture,
the corrected focused run passes **30 tests in 4.35 seconds**, zero skips:

```powershell
.venv\Scripts\python -m pytest -q tests/test_plugins.py tests/test_native.py
.venv\Scripts\python -m ruff check src/mcbench/plugins.py src/mcbench/native.py tests/test_plugins.py tests/test_native.py tools/native_plugin_probe.py
.venv\Scripts\python tools/native_plugin_probe.py --codex (Get-Command codex).Source --output '<new external directory>'
```

The tests include actual Git inventory, nested fixture exclusion, all-eight
retention, changed-source rejection, TOML table round trips and null rejection,
plus existing native lifecycle/accounting cases. Ruff passes. The native matrix
uses real processes and the real plugin, with synthetic provider responses.

## Next gate

Continue M0.1c.2b with synthetic canaries for files, process visibility, egress,
helper boundaries and initial-skill immutability. Catalog exclusion does not
prevent a raw file read. A fresh profile or an unelevated sandbox is insufficient
evidence to admit gameplay. Preserve the existing model/OAuth/$10 project cap,
pending monetary evidence question, finite-exposure and spending-authority gates.

Primary references: [native CLI automation](https://learn.chatgpt.com/docs/non-interactive-mode),
[skill disabling and explicit invocation](https://learn.chatgpt.com/docs/build-skills),
and [Windows sandbox modes](https://learn.chatgpt.com/docs/windows/windows-sandbox).
Documentation informed the configuration; actual request/body evidence establishes
the narrow results above.
