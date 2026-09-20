# Restricted native tools: partial boundary evidence

September 20, 2026. Operator-only. M0.1c.2b.2, F03/F04/F07, N01/N04,
C06/C20, partial T04/T06/T07 and G0 item 1. M0 remains incomplete; G0 fails;
G1–G5 are not run. This candidate does not supersede the earlier loopback leaks.

The actual pinned CLI was run with a fresh private profile and unchanged pinned
Dovetail, against the existing credential-free local synthetic wire provider.
Supported feature settings disabled shell, image, app/browser/computer tools,
hooks, automatic skill-MCP installation and web search. Native collaboration
remained enabled. This is an explicit candidate capability change, not a claim
that a setting name establishes an access boundary.

`tools/native_restricted_tools_probe.py` emitted four fixed requests. The actual
code-mode catalog contained only `apply_patch`; `process`, `require` and `fetch`
were undefined. The deliberately invoked disabled `exec_command` returned
`TypeError: tools.exec_command is not a function`. An `apply_patch` attempt to a
fixed operator-owned canary outside the workspace was rejected by the native
read-only sandbox/approval policy. Neither shell nor patch canary was written.

Four distinct synthetic receipts settled (40 input, 16 output, 56 fixture units),
with no provider errors and a finalized envelope. No account credentials,
subscription inference, Minecraft process or desktop input was used.

Private raw evidence and source/config hashes:
`C:/Users/Darian/.strata/evidence/2026-09-20-native-restricted-tools-01`.
CLI `0.154.0-alpha.6.2`, executable SHA256
`960c111d47afd61669954b9df9e56083e302edbfa3ef6962d81dcc14a30051dc`;
candidate profile digest
`62fcb68864c2d994e1e1275da9fcb0c266eb2caed9526f4f89eb2d684bb3369e`.

These observations establish only two negative tool operations and a positive
code-mode control. Remaining requirements include permitted scoped game/own
artifact access, immutable skill reading, forbidden read paths, process/network
canaries, helper-specific grants, trusted lineage, nested admission, complete
tool/catalog checks and restart/revocation. The broker must derive permissions
from authenticated native transport identity, never a model-supplied role or
namespace. Separate profiles/conversations remain insufficient by themselves.

## Native caller identity and implemented broker

The next experiment used a stdio MCP server with the same restricted native
profile and Dovetail. It recorded the pinned CLI's actual outer `_meta.threadId`,
`callId` and `x-codex-turn-metadata` fields. Root and native helper had distinct
thread IDs. The helper's forged root `threadId` and `_meta` remained inside
model-supplied arguments; native outer metadata continued identifying the child.
Each agent launched a separate stdio server process. Six synthetic requests
settled at 84 fixture units; no provider errors. Private evidence:
`C:/Users/Darian/.strata/evidence/2026-09-20-native-mcp-identity-01`.

This observation informed [NativeBroker](../../src/mcbench/broker.py) and its
[stdio/worker adapter](../../src/mcbench/broker_stdio.py):

- Operator-only enrollment binds runtime/profile/session/thread, parent/depth,
  model, role, epoch, expiry, tool quota, separate artifact namespace and an
  admission-evidence reference. A call cannot enroll itself or supply its role.
  An unregistered child is denied; parent expiry/revocation applies to children.
- Each caller sees only explicitly copied immutable initial/docs/supplied text
  and its own drafts. Logical paths never resolve filesystem paths or arbitrary
  CAS references. Helpers write only their own `results/`; executor writes are
  limited to notes, skill drafts and handoffs. Compare-and-set updates, byte/file
  quotas and existing CAS integrity checks apply. Draft writes do not activate
  skills, import probe artifacts or establish executable-script support.
- Game forwarding uses the existing strict `GameRequest/1` surface and a fixed
  operator-owned worker descriptor. Helpers cannot use game tools. The endpoint
  is exactly loopback `/v1/game`; no caller URLs, arbitrary methods, shell, raw
  native bridge or admin endpoints. The transport never retries. Durable request
  intents retain an unknown result across restart instead of forwarding again.
- MCP implements only its bounded initialization/tool-list/tool-call/ping
  surface. Resource reads and other methods are rejected. Errors do not echo
  rejected arguments, private paths or transport exception contents.

This is capability `native-stdio-projected-artifacts-executor-game/1`, a candidate
use of the optional C36 MCP facade to address the demonstrated native shell
boundary problem. Codex remains the native loop with the selected plugin; the
underlying game request contract and backend identity do not change. The
[official config schema](https://developers.openai.com/codex/config-schema.json)
documents MCP allowlists and per-tool approval modes. Only the two owned broker
write/game tools receive explicit approval; shell and other disabled capabilities
remain absent. The actual configuration/profile and source bytes are pinned in
each private manifest, independently of current upstream documentation.

The first broker run (`2026-09-20-native-broker-01`) failed: metadata carries
`0.154.0-alpha.6.2`, whereas the CLI version banner includes `codex-cli`; default
MCP approval also rejected writes/game. Both failures remain recorded. Corrected
version handling and explicit approval for those exact broker tools produced a
passing second fixture (`2026-09-20-native-broker-02`), profile digest
`05cbf440982a3f8cb41ab72024f06db69de7652fe4df8e47ee9b6a107b10167a`:

| Caller | Positive control | Negative controls |
|---|---|---|
| Root | Reads its supplied plan, writes its own note, receives one synthetic game observation over actual local HTTP | Initial skill write denied |
| Native helper | Reads its explicit plan and writes only its own result namespace | Game access, root-only artifact read, parent note write and forged-identity arguments denied |

The exact native tool output records were inspected for each operation. Root-only
canary text and worker credential were absent from returned outputs. The private
worker saw exactly one executor request and no child request. Six distinct
synthetic receipts settled at 84 fixture units and the envelope finalized.
The fake worker tests actual brokerage/transport, not a Minecraft observation.
No real evaluator secret was placed in the test; all canaries were owned fixtures.

Focused source checks passed 28 tests in 1.10 s after the version fix, covering
projection isolation, path negatives, helper privileges, metadata mismatch,
revocation/expiry/replay, immutable artifacts, CAS writes, bounds, game no-replay
and error redaction. The broker plus existing storage/controller,
checkpoint/artifact and contract regression checks then passed 94 tests in
4.83 s. Full Ruff and whitespace checks pass. These tests do not qualify the
entire native environment.

Still required: independent adversarial file/process/network/resource canaries
on this exact profile; actual immutable Dovetail skill-body loading and learned
revision activation/export; protected launch/config integrity; trusted live
root/child registration linked to pre-dispatch budgets (the provider fixture's
explicit enrollment is synthetic only); concurrency/depth controls; cancellation
and revocation through the worker; actual OAuth ingress/exposure; then the
authorized at-most-$1 trial inside the existing $10. No production qualification
record was issued. Earlier loopback, shutdown, effective-file and pack failures
remain unresolved in their stated scopes.
