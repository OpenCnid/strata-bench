# E9E startup-input review and extended snapshot

M0.3a.4k remains **in_progress**. Installed-bytecode review identifies two more
mutable inputs that affect game state. `RuntimeDataSnapshot/2` freezes those
inputs alongside the original three. **92 distinct focused tests** and **18/18 actual
offline checks** pass. Authentic changed-component execution is recorded below;
the thirteen provisioning checks and M0/G0 remain open.

Coverage: F01/F05/F06/F16, N01/N04/N06/N08, C03/C04/C24, partial T01/T02/T13,
G0 item 2. D14, D18/D19, all accounting reservations and M1–M7 remain unchanged.

## Concrete findings

A private static index verifies the exact inventory hashes for **461 client/server
mod JAR entries**, deduplicating into **266 archives**, including embedded JARs.
It inspects **57,452 class entries** and identifies **125 candidates** containing
network-related constant-pool method references. These include local resource
loading, URI formatting, optional features and inactive helper code. This is a
review index, **not** complete call-graph analysis or a network/isolation proof.
Fifty selected classes and 51 direct-reference consumers are disassembled with
the retained JDK `javap`; mod code is not initialized by disassembly.

The following findings come from exact installed bytecode, not class names alone:

| Consumer | Observed behavior and disposition |
|---|---|
| Ars Nouveau `Rewards` | Fetches `supporters.json`. Its `starbuncles` list feeds the server entity spawn method, choosing names, colors, biography and adopter fields. The contributor UUID list also affects login feedback. Freeze the actual body; do not dismiss it as informational text. |
| Supplementaries `Credits` | Fetches `credits.json`; its maps feed `GlobeBlockTile.GlobeType` and `StatueBlockTile` variant selection. Freeze the actual body. |
| Rhino `RemappingHelper` | Normal loading reads local `config/mm.jsmappings` or the packaged resource. Network generation is separately guarded by `generaterhinomappings=1`; the selected exact launch arguments do not enable it. This is not a claim that the general scripting API cannot access the network. |
| Crash Assistant `modpack_modlist.auto_update` | The title-screen callback checks the configured pack-creator identity and writes the local mod-list record. This setting is not automatic installation updating. Its separate GUI download/upload utilities are not qualified by this finding. |
| KubeJS update check | The inspected load-complete task fetches a response string and logs it. No installation path is present in that method. This does not qualify every KubeJS/script input. |
| Thermal Dynamics' bundled `requack` | The direct-reference index finds external uses of collection/cast utilities and annotations, not its download actions. This bounded static result alone cannot prove all reflective reachability. |

Forge's earlier inspected version checker likewise processes version/status
metadata, not an automatic installer. The remaining contributor/cosmetic,
optional web/helper and script/config input dispositions still require closure
before a complete update/provenance attestation. Preserve the index and reviewed
callers so that work continues from these findings rather than repeating the scan.

## Implemented change

[Preparation](../../src/mcbench/runtime_data.py) now emits
`strata/RuntimeDataSnapshot/2` with policy `e9e1270-runtime-data-snapshot/2`.
It adds two bodies and two exact class identities. The original three publisher
bodies, four compiled agent classes, vendor JARs/signatures, parser logic,
HTTP-shaped delivery, no-network-fallback behavior and journal bounds remain.
Each new class patch changes only one URL constant; every other class byte
reconstructs exactly when the replacement is reversed.

| Added input | Publisher revision | SHA-256 / bytes |
|---|---|---|
| Ars Nouveau `supporters.json` | `1d11ade5871a18ce8fef5717a778841162e24c0f` | `973daeaf77d5f43dbc3f06aac98ee138f60f3a7da5e1be71ac5cf5c96c6073fa` / 43,089 |
| Supplementaries `credits.json` | `e37617d9b1a4dce50e2f8e456e40d0223fd86691` | `1ba50e0acc5848933ea31a05993ac8a1f36aa280a2a0d95e62e566adf4f615a1` / 7,926 |

Exact commit responses, HTTP metadata and bodies are retained privately. These
include the root publisher notices at the same revisions (`license.txt` and
`LICENSE.md`), without inferring a license certificate or redistribution right.
These are new snapshots, not recovery of historical network responses. The prepared
31,055-byte agent is
`3d340874d1e44c41f67331092872408de01f2375292828045f5af0caec29a2a4`.

Historical `/1` snapshots remain readable for evidence reconstruction. The actual
previous journal-capable artifact passes that readback. The installed-profile
consumer rejects `/1` with `FORGE_RUNTIME_DATA_UNPINNED` when either added mod is
present. `/3` also rejects these known consumers without a snapshot. `/4` retains
its existing profile shape and binds the extended receipt/JAR to both roles.
The shared journal/log consumer requires all **four class bindings and five body
reads** for `/2`; `/1` reconstruction retains its original two/three contract.
Unknown policies, missing added records and cross-version relabelling reject.
Preparation also applies the consumer's aggregate archive limits before publishing
a receipt. Five individually valid bodies cannot silently produce an oversized
snapshot; a failed build remains without a preparation receipt.

## Executed source and actual-data verification

Windows, retained Python environment and JDK 17; `-X utf8`, no Python bytecode,
project `src`, `evaluator/src`, `tools`, `tests` on PYTHONPATH:

`pytest tests/test_runtime_data.py tests/test_runtime_data_journal.py
tests/test_e9e_cold_start.py tests/test_pack_forge.py -q`:
**91 pass**, 98.70 seconds. Two existing Typer/Click deprecation warnings remain.
Cases include backward readback, rejected old-profile admission, complete extended
markers, corrupt bodies, class drift, exact-route restrictions, absent console
handles and journal quotas. Synthetic archives are explicitly not executed as
historical agents.

After adding the aggregate-expansion regression and producer check,
`pytest tests/test_runtime_data.py -q`: **24 pass**, 31.67 seconds.
The selections overlap, yielding **92 distinct cases**, not 115. Full Ruff and
diff checks pass. This final Python admission check does not change the executed
Java artifact or its publisher bodies.

The private **18/18** offline audit builds the actual five-body snapshot, reads
the authentic old receipt, verifies unchanged original inputs, delivers every
body through a real JVM with socket connections forbidden, patches both actual
new vendor classes, reverses each exact constant change and rejects changed
class bytes. Vendor JARs and all **39 authority tables** remain unchanged.
This tests delivery and patching, not execution of the complete mod parsers.

## Authentic changed-component scope

The one-use `e9e1270-five-body-loading/1` case prepares fresh client/server copies
from the original VERIFIED roles. Independent rehashes cover every original file
and directory; each role adds only the new agent (12,918 client / 8,800 server
files). It runs one server and one sequential authenticated client, no gameplay
commands, no model calls and no shared-desktop input. Existing finite file leases
remain split into three groups, each below 1 GiB. Bounds are 300 seconds for
server startup, 420 seconds for the client, 120 seconds for server drain and an
860-second outer lifetime. The client uses explicit owned Job termination after
capture; this case makes no clean-client-save, cold-restart or D13 claim.

The authentic run **passes in 369.515 seconds**. The client captures its six
config roles in **163.313 seconds**; its owned eight-process tree is terminal,
without watchdog expiry. The server stops normally, exit 0, with all three owned
processes terminal. Its authenticated spool records **3,381 server ticks**.
Both role journals bind all four exact classes and all five bodies. The shared
consumer accepts repeated reads only when every observed body/hash matches.

Independent reconstruction passes **22/22 checks**: owned identities, terminal
processes, private argument-file retirement, unchanged input desktop, exact
journals/artifacts, unchanged expert recipe and selected settings, three bounded
leases and unchanged authority. All six selected client roles match the retained
prior capture, preserving client-only and unregistered legacy dispositions.
All **39 authority tables** match both this run's start and the prior sealed
three-body checkpoint. No model or gameplay actions occur.

Original E9E remains VERIFIED, not SEALED; exposure remains **$2.831942/$10** with
every unresolved amount reserved. This verifies the added inputs' actual loading;
it does not prove all-mod mechanics equivalence or close the remaining startup
input dispositions. The older successful loading/restart results keep their
exact three-body scope. Finish the remaining dispositions, qualify the final
changed profile's cold restart and assemble the successor inventory/profile plus
thirteen bound provisioning checks. Do not repeat this successful loading case
unchanged. Full isolation remains deferred under D14.

Stopped capture preserves **22 changed/new client files / 5,552,294 bytes** and
**117 changed/new server files / 26,125,444 bytes**, with no removals. Every copied
delta is rehashed. The only existing-file changes are each role's BYG backup ZIP
and server.properties; the latter retains identical non-comment lines. No
software/mod/script/agent file changes. ZIP semantic equivalence is not asserted.

Private evidence `2026-09-24-e9e-startup-review-01` is sealed: **484 files /
58,111,352 bytes**, complete EvidenceBundle readback pass. It retains the static
index and disassembly, commit/body/notice acquisition, actual patch controls,
source/build pins, live scope and stopped deltas. Prior inputs selected for
comparison are independently checked against their retained seal.

- Seal: `82e63adc167f6054de9669152a4e952ac266c205233c9b2009240d2398daf6af`.
- Offline 18/18 audit: `027e7ce2dab8bea20d6970b02edcedbbcdf877282eb49c4f7a3a373075f8d98e`.
- Live 22/22 audit: `23554cb8b33e48a8453760f3bc9aa8f1633a348a78251b08d58df1b8ac7189a4`.
