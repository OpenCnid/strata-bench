# Acquired vanilla client software and Java source inventory

September 22, 2026. Operator-only. M0.3a.2 remains `in_progress`; M0 is
incomplete, G0 fails and G1–G5 are not run. This advances F01/F05/F16,
N01/N04/N08, C03/C04/C24, partial T01/T02/T13 and G0 item 2. It prepares
the actual runtime software needed by the full role inventory; it does not
close the full PackLock, scorer, isolation or recovery gates.

## Working implementation

[vanilla_client.py](../../src/mcbench/vanilla_client.py) and the operator
[pack command](../../src/mcbench/pack_commands.py) now prepare the exact
Windows client from its durable acquired artifact, retained version metadata,
explicit library roots and cached assets. The shared
[PackProvider source join](../../src/mcbench/provisioning.py) rechecks the
original receipt/CAS/metadata for either client or server without reopening
old acquisition paths. Server semantics remain unchanged.

The command validates supported OS rules, Maven paths, official source URLs,
sizes and hashes; preserves all selected libraries in classpath order; and
records other-OS exclusions. Asset aliases resolve to unique hash-named files,
with exact index digest/logical size and conflicting-alias rejection. Logging
configuration and raw version metadata are included. No arbitrary cache tree,
account files, personal instance state or credentials are copied.

Output is independent, has a complete verified inventory and retains embedded
license/POM/notice metadata. Missing inputs, bad hashes, unknown rules, unsafe
paths, links/hardlinks, occupied/overlapping destinations and source changes
reject. A corrupt preferred library cannot silently fall back. Partial output
is retained for diagnosis and cannot be reused. No downloads, authentication,
Java/Minecraft startup or settings changes occur in this command.

## Focused source verification

Windows, Python 3.12.14, existing locked dependencies:

- `pytest -q tests/test_vanilla_client.py tests/test_vanilla_runtime.py`:
  **51 pass**, 2.42 s: 24 new client cases plus 27 server/source-join regression
  cases. Two existing Typer/Click deprecation warnings remain.
- `pytest -q tests/test_gameplay_package.py`: **one pass**, 0.35 s; the compiled
  four-file gameplay package excludes the new operator source and private data.
- Full Ruff and whitespace pass. An initial Ruff-only unnecessary semicolon
  in a test was removed; no behavior or acceptance evidence changed.

Tests cover exact selection/order, preserved aliases, independent copies,
missing and corrupt preferred inputs, alternate source verification, unsupported
rules/layouts, changed logging/index/Java/main class, hardlinks, late source
mutation, refused partial-output replay and actual CLI/CAS publication while
provisioning remains ACQUIRED. These are synthetic software tests, not game
or isolation acceptance evidence.

Final documentation audit preserves all 406 existing IDs and the append-only
history; later milestone rows and SPEC sections 3/15–19 are unchanged. All
1,211 checked local links resolve. The new 3,770-file seal and previous
84-file server bundle rehash completely, and current implementation bytes
match the successful client preparation's source pins.

## Actual software preparation

One real operator command prepared **3,432 files / 638,236,232 bytes**.
Its 65 classpath entries contain the exact client and 64 libraries. All
3,364 distinct asset objects, 3,390 logical asset names, version/index and
logging configuration reconcile; 24 other-OS libraries are explicitly excluded.
The metadata's Windows rules select the native classifiers; this does not
claim native-loading or rendering conformance on every represented architecture.

Four required libraries were absent from the shared client cache: JNA and
JNA-platform 5.10.0, Log4j API and Core 2.17.0. Their exact metadata-matching
copies came from the previously verified server software. All remaining
selected cache inputs match. The command does not replace missing shared files.

The independently prepared client has SHA-256
`e1ac65de9b471b6916cc457fdcff00c1bafac17027aa79100c4df893b3d956db`.
The previously rejected shared client stays unchanged at
`14ac8adb372c63c6bba59394b89d02f675f3423e926c7906a2fc6abcb2c2f4fb`;
its failure is not reclassified. The private software evidence is
`cas:sha256:d3f6e9079f5db94e8fc70ebace5049e95f874c910cd74a37a7837c08e889999a`.
The preparation retains 48 embedded metadata records across 27 JARs; it
does not infer licenses for JARs whose publishers omit those records.

The independent audit preserves **3,432 selected/original source files**,
including the shared client and CurseForge profile. All **32 durable
non-artifact/journal tables**, **83 existing objects** and the **137-event
prefix** remain unchanged. One private operator evidence object/event is added;
the original request stays ACQUIRED with inventory/lock null. Preparation plus
audit ran from 05:35:28.807 to 05:37:02.794 UTC. No Java existed before/after;
no game/model dispatch or shared-desktop input occurred.

## Java distribution and installed bytes

The official [Adoptium release](https://github.com/adoptium/temurin17-binaries/releases/tag/jdk-17.0.20.1%2B1)
and retained API metadata identify Windows x64 Hotspot JRE 17.0.20.1+1.
The metadata-selected publisher ZIP was downloaded privately, without install
or execution, and matches its declared size and SHA-256:

- ZIP: **43,780,109 bytes**,
  `bc21a93923103cdaac93ee337b0ae4365e739fde36df823dd456bc67c8a9d352`.
- Captured API metadata SHA-256:
  `e15a6c72e5ac0924c40e514b07d3890c8f52ab3b389623b8260b0fbad099e199`.
- All **316 installed JRE files** match archive bytes: zero missing, extra or
  changed files. `java.exe` remains
  `1977f302375adbb920d41dac65c7e22eb9c2ed8e1e8d6258964154ff16f14406`.
- A fresh independent private Java software copy contains those **316 files /
  130,895,997 bytes**, including **183 legal/notice files**. Complete scans of
  original and copied roots match; no hardlinks or replaced installation.

This verifies metadata/TLS/hash and file ancestry. It does not claim upstream
signature verification, license completion, native execution or cold restart.
Both original Java installation and previously prepared server remain unchanged.

## Private custody and next action

The sealed bundle is
`C:/Users/Darian/.strata/evidence/2026-09-22-vanilla-client-01`.
It contains **3,770 files / 818,151,036 bytes**, excluding its manifest.
Manifest SHA-256:
`7aafbc2c8456e7b2fddec670fa594866140d58e81a42552378635505e3fb77fa`.
It retains actual CLI output, before/after authority snapshots, source hashes,
pinned implementation, prepared client/Java bytes, publisher metadata/archive
and independent audit scripts/results. Keep all bytes outside public source
and gameplay access. Preparation is not an isolation boundary.

Next assemble compatible role inventories from the prepared client/server/Java
software, complete component/shaded/native license provenance, and pin runtime
configuration/update policy before authentic cold-restart qualification and
sealing. No unchanged software preparation or game trial is needed. The original
$10 authority, $0.7554 unresolved hold, $0.001458 settlement, two requests and
consumed D12 remain unchanged; general model admission is still blocked.
Preserve every earlier 500-ms/effective-file/Mineflayer/E9E failure and all
scorer/setup, isolation, startup and canonical recovery requirements.
