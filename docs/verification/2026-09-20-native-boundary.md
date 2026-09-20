# Native Windows boundary canaries: failed qualification

September 20, 2026. Operator-only. M0.1c.2b; F03/F07/F09/F11/F16,
N01/N04/N06/N08, C06/C18/C20 and partial T04/T07/T12.
This report records failures. It issues no production or release qualification.

## Scope and outcome

The pinned Codex executable from the [native dispatch report](2026-09-20-native-dispatch.md)
executes a fixed probe against newly created synthetic files and a temporary
loopback listener. The permitted workspace contains read/write controls; a
sibling directory represents operator-private state; a separate file represents
an immutable initial skill. No real operator document, account cache, evaluator
fixture, installation or unrelated endpoint is targeted. All owned listeners
and processes are stopped after each sample.

The [public probe](../../tools/native_boundary_probe.py) retains raw evidence
only under external `C:\Users\Darian\.strata\evidence\2026-09-20-native-boundary-*`.
Each manifest hashes the source and executable used for that sample.

| Sample | Actual execution | Result |
|---|---|---|
| `-01` | Real native CLI/tool loop, fresh credential-free profile, unelevated Windows sandbox and legacy workspace-write mode | Workspace read/write pass; dummy operator file **read succeeds**; initial-file write denied; unapproved loopback **succeeds**, independently confirmed by listener. Qualification fails. Two synthetic calls settle, 28 synthetic microUSD; zero real inference spend. |
| `-02` | Same native loop with a named filesystem profile denying reads outside minimal/workspace roots and networking disabled | Native startup refuses to run: the unelevated implementation cannot enforce split filesystem read restrictions. No provider requests occur. Safe refusal is not a positive isolation pass. |
| `-03` | Non-model `codex sandbox` command using existing administrator-provisioned enrollment and the named profile | Fixture failed: constrained PowerShell disallows the probe's .NET object creation. No positive controls are established; retained as a failed fixture. |
| `-04` | Same sandbox command; use ordinary file cmdlets and the system curl executable for the canary request | Workspace controls pass; operator read and initial-file write denied; unapproved loopback **succeeds** and is independently confirmed. Qualification fails. |
| `-05` | Same as `-04`, with process identity observed | Native command runs as the existing `CodexSandboxOffline` account; the same loopback violation remains. Qualification fails. |

The direct sandbox cases create no agent/model session and dispatch no provider
requests. They use the existing protected sandbox enrollment through the native
command, without copying its secrets, modifying user config, invoking setup,
creating accounts or changing firewall rules. They are a distinct execution
surface from the agent loop and cannot qualify its fresh-profile bootstrap.
The first fixture's direct socket call was replaced by curl because the stronger
PowerShell language mode rejects .NET object creation; both target only the
owned listener. No denied command was rerun without its sandbox.

## Enforcement inspection

Read-only Windows inspection finds the existing offline account SID matches the
Codex outbound rules' local-user filter. The TCP loopback rule covers ports
1–65535, the UDP rule covers any port, and the general outbound rule remains
present. All three rules are enabled in ActiveStore, with `Enforced` among
their enforcement statuses. Domain/private/public firewall profiles and local
rule merging are enabled; BFE and MpsSvc are running. These settings do not
override the observed connection success. The precise enforcement failure is
unresolved; no firewall policy is changed or threshold relaxed.

Only Docker Desktop's WSL distribution was listed; the Docker daemon was not
running. No container, alternate Linux CLI, game installation or VM was started.
The presence of those executables is not evidence of an isolated worker.

## Reproduction and remaining work

```powershell
# Actual native CLI/tool loop, synthetic provider
.venv\Scripts\python tools/native_boundary_probe.py --codex (Get-Command codex).Source --output '<new external directory>'
# Stronger named profile: unelevated runtime refuses unsupported read isolation
.venv\Scripts\python tools/native_boundary_probe.py --codex (Get-Command codex).Source --output '<new external directory>' --permissions-profile
# Non-model sandbox only, existing private enrollment required; never creates it
.venv\Scripts\python tools/native_boundary_probe.py --codex (Get-Command codex).Source --output '<new external directory>' --permissions-profile --sandbox-home '<already enrolled operator home>'
```

Each failed run exits nonzero. Ruff passes for the probe. These are actual
process/OS interactions with synthetic canaries, not mocked denials. File
positives in the last two samples cover only these files; adversarial process
access, inherited handles, alternate paths, sibling helpers, catalog access,
game bridge permissions, all egress routes and restart remain required.

M0.1c.2b remains in progress with a typed native-network compatibility blocker.
Owner: AR/SI. Resolution requires an enforceable boundary that denies the owned
unapproved endpoint while preserving scoped authorized IPC, then the remaining
adversarial suite on the exact launch/helper profile. A question about an already
prepared isolated worker/VM is pending; continue independent authorized work.
The separate OAuth USD, finite-exposure and historical project-spending gates
also remain open. No live inference is admitted.

References: [native permission profiles](https://learn.chatgpt.com/docs/permissions)
and [Windows sandbox implementations](https://learn.chatgpt.com/docs/windows/windows-sandbox).
The runtime's actual rejection and the independent listener are the evidence
for the failures, rather than configuration labels or documentation promises.
