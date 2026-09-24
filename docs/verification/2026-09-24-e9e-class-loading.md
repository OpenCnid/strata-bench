# E9E runtime-data class loading

M0.3a.4k remains **in_progress**. The retained Cable Facades class mismatch is
explained and reproduced byte-for-byte using the installed Forge EventBus
transformer. Exact admission now includes that reviewed representation; arbitrary
class drift still refuses. The changed authentic server startup and cold restart
both pass, with **21/21 reconstruction checks**. Client qualification and complete
provisioning remain open. M0 remains in_progress and G0 fail.

Coverage: F01/F05/F06/F16, N01/N04/N06/N08, C03/C04/C24, partial T01/T02/T13,
G0 item 2. This continues the [runtime-data finding](2026-09-24-e9e-runtime-data.md)
without changing D14 isolation deferral, spending authority or M1–M7.

## Authentic capture and exact reproduction

Fresh server `e9e-class-capture-01` copies and verifies the original 8,799 server
files, then adds only the capture-enabled snapshot agent. Its changed boot again
refuses the class before readiness: **30.937 seconds**, exit **126**, no forced
cleanup, **3/3** held processes terminal and an empty owned Job. This is a
retained failed boot, not a startup pass.

The agent now retains base64 bytes for either of its two named target classes
on refusal, limited to **64 KiB** in the private startup log. Larger inputs still
halt without a byte capture. This adds no gameplay tool or automatic admission.

Captured Cable Facades `CFConfig` is 10,861 bytes with SHA-256
`1ab0dee01c531ff6a89fd85aee2109f5e8036d342e0c283e76a9101b0aab8092`.
It differs from the raw vendor class
`601b70c83a14debbb5e4679196a319c1a31eab4d4b008cd33b1feca2551bda0d`
at exactly **byte offset 8925: 8 → 9**. Full ASM text comparison identifies that
byte as the access flag for `onLoad(ModConfigEvent)`: package-visible static
becomes public static. Its `SubscribeEvent` annotation is unchanged.

The installed `net.minecraftforge.eventbus.EventAccessTransformer` from EventBus
6.0.3 performs precisely that annotated-method conversion. Executing the real
transformer offline against the raw class, then serializing through installed
ASM 9.7.1, reproduces **every captured byte**. The EventBus JAR is pinned to
`4bc0d5eaa086a4aecc613771fd02ad04373a06e83359185ee87f5caae4f29897`.
Both the full disassembly and exact reproduction inputs/outputs are retained
privately. This supersedes the inconclusive plain-serialization probe, whose
original negative results remain preserved.

## Corrected admission and checks

[Agent.java](../../java/runtime-data/src/io/github/opencnid/strata/fixed/Agent.java)
admits the raw vendor hash for offline inspection and the exact reviewed Forge
hash. It preserves Forge's access conversion and changes only the existing URL
constant. The [cold-start consumer](../../tools/e9e_cold_start.py) requires the
post-Forge binding; an offline raw-class binding cannot pass the game evidence
check. No vendor JAR or signature changes.

The actual three-input patch audit proves exact reversible single-URL changes
for raw Cable Facades, captured Cable Facades and raw IE. A different access-flag
change fails with `FIXED_DATA_CLASS_PIN` and produces no patched output.
Source snapshots for both prepared agents match their preparation receipts.

On Windows/JDK 17, retained Python environment, `-X utf8` and project
`src`, `evaluator/src`, `tools`, `tests` on PYTHONPATH:

- Capture implementation: `pytest tests/test_runtime_data.py -q` — **16 pass**,
  12.93 seconds.
- Corrected implementation: `pytest tests/test_runtime_data.py
  tests/test_e9e_cold_start.py -q` — **36 pass**, 24.73 seconds. This includes the
  capture quota and rejection of a raw-class binding as authentic Forge evidence.

The first selection is contained in the second; **36 distinct cases** pass.
Fixture bodies remain synthetic; the separate private audit uses actual vendor
and captured bytes.

Capture agent: `23fa99f78fd316fe9db2efc91389f0b0d7d4854c7949d746e58cb05070c47619`
(9,700 bytes). Corrected agent:
`adb3da6e2170143fb0edcf059661290ece621c65db73942c3185a53720f9d9f5`
(9,779 bytes). Both retain the exact previously acquired three publisher bodies.

All **39 original authority tables** remain unchanged after capture and analysis.
Exposure remains **$2.831942/$10**, all unresolved reservations retained, zero
model calls. Original E9E remains VERIFIED, not SEALED. The thirteen provisioning
checks, client snapshot qualification and other G0 outcomes remain open.

Private capture/reproduction evidence `2026-09-24-e9e-class-capture-01` contains
**73 files / 1,154,536 bytes**, with complete EvidenceBundle readback passing.
Seal: `8c49176b7de3823465b0f893a246e0f82a3909ab8f84079234bf8508272fa695`.
Reproduction report:
`86689cb0808810841cec8dd2fe4181fff024321a27dbde1972c8a308db400138`.
Actual patch audit:
`be44e21aab18a97f16e2eb339304157a121f1fe7cfa9a61a81d27929eb9eea04`.
The earlier failure and this capture remain sealed; neither used server is a
fresh baseline. Full Ruff and diff checks pass.

## Changed server startup and cold restart

Fresh `e9e-frozen-boot-02` separately verifies the original 8,799-file server
inventory, adds only the corrected agent, and executes cold-start `/2` twice.
The second boot deliberately uses the normally stopped first world and epoch 2;
it is cold-restart qualification of the changed snapshot profile, not a fresh
world or a replay of either failed case.

| Evidence | Initial boot | Cold restart |
|---|---:|---:|
| Elapsed seconds | 206.797 | 150.828 |
| Authenticated records / server ticks | 18 / 202 | 18 / 202 |
| Normally terminated owned processes | 3 | 3 |
| Expected class bindings / snapshot reads | 2 / 3 | 2 / 3 |

Both report expert mode, zero KubeJS startup/server errors, the exact expert
furnace recipe, selected Create values 8/400/10 and 145 Sophisticated Core COMMON
entries. Selected loaded configurations and recipe snapshots are identical
across the two distinct authenticated boot authorities. Both reach readiness,
receive normal `stop`, exit 0 and leave no active or forcibly terminated Job
members. Each log contains exactly the expected resource-index record, two
class bindings and three body-hash read records. IE's raw class pin remains
valid at this Forge loading phase.

Separate reconstruction passes **21/21 checks**, including preservation of all
five historical effective-file findings and all 39 original authority tables.
These named config checks do not assert that every configuration file is
identical or erase the retained BYG ZIP differences. No player, client, desktop
input or inference is used. All **nine** game-process handles across the failed
capture and successful pair are terminal; a final process query finds no Java
process remaining.

Private server evidence `2026-09-24-e9e-frozen-boot-02`: **50 files / 6,361,374
bytes**, complete EvidenceBundle readback pass. Seal:
`3202f526d5b9fed6cb886852acd4e93b3ac5569ca6b8da3f20b2aa33fdc81a51`.
Reconstruction:
`144fbdb6a5e2d737e4ca10c2ad6690ab2775279690fb99c3b9dfc6898e7e993b`.

Next qualify the same corrected snapshot through the installed client loading
path and restart, finish the remaining startup-input review and join the
thirteen provisioning checks to a distinct successor inventory/profile. Reuse
this successful server evidence; do not repeat the pair unchanged. Preserve the
original VERIFIED inventory and every failed or superseded case. This freezes
the three named inputs; full networking/isolation, all-mod runtime inputs,
client mechanics, seal/materialization and complete G0 remain unqualified.
