# Acquired vanilla server software preparation

September 22, 2026. Operator-only. M0.3a.2 remains `in_progress`; M0 is
incomplete and G0 fails. This advances F01/F05/F16, N01/N04/N08,
C03/C04/C24 and partial T01/T02/T13/G0 item 2. It does not qualify
installed client/server roles, a full PackLock or game behavior.

## Working implementation

[vanilla_runtime.py](../../src/mcbench/vanilla_runtime.py),
[PackProvider](../../src/mcbench/provisioning.py) and the operator
[pack command](../../src/mcbench/pack_commands.py) now connect the original
durable acquisition to installed and independently prepared server bytes.
`pack prepare-vanilla-server` rechecks authorized CAS/official metadata,
bundler/main-class/version, embedded hashes and coordinate paths. Exact
installed file/directory sets reject missing/changed/extra files, hardlinks
and unreviewed root content. No bootstrap or nested archive is executed.

The new private software root contains only verified bundle payloads.
Configuration has an explicit pending disposition; generated world/account
state and logs remain in their original private installation. Source and
destination checks precede the private `VanillaServerSoftware/1` publication.
Existing destinations reject; partial failed output is retained, never replayed.
No canonical record, gameplay package or acceptance threshold changes.

## Synthetic verification

Windows, Python 3.12.14, existing locked dependencies:

- `pytest -q tests/test_vanilla_runtime.py tests/test_vanilla_artifacts.py tests/test_provisioning.py`:
  initial **63 pass/one failure**, then **64 pass** in 5.23 s after fixing the
  test database filename to the actual CLI convention. The initial fixture
  used `operator.sqlite`; the CLI correctly opened `controller.sqlite` and
  refused the missing request. No acceptance evidence was involved.
- After the authentic SLF4J metadata edge case, `pytest -q tests/test_vanilla_runtime.py`:
  **27 pass** in 1.27 s, adding three sentinel/link controls. **67 distinct**
  provisioning/runtime cases pass across these selections. Two preexisting
  Typer/Click deprecation warnings remain.
- `pytest -q tests/test_gameplay_package.py`: **one pass** in 0.35 s; the
  compiled gameplay package still contains only its four allowlisted files.
  The new operator command/source and private evidence are excluded.
- Full Ruff and `git diff --check` pass.

Final documentation audit preserves all 405 previously recorded IDs, every
later milestone row and the complete existing append-only log. SPEC sections
3 and 15–19 are byte-equivalent; 1,205 local links resolve. Both new private
seals rehash completely, and successful preparation's pinned implementation
bytes match the final source.

Cases include corrupt CAS bytes, legacy receipt rejection, preserved old
acquisition-path independence, unsafe/duplicate/traversing bundle entries,
false payload hashes, extra empty directories, source mutation while copying,
preserved partial output and no overwrite/replay. These are synthetic
software contracts, not authentic gameplay or isolation qualification.

## Authentic installation evidence

The original vanilla request remains `ACQUIRED`, inventory/lock null, with
acquisition receipt
`573173402f63051cd14ecb860f57d6e8a78700a4e24487bfcee763952a38e09a`.
The official outer server remains
`b26727069ef5f61c704add9a378ac90e3d271fd7876c0bd3dcfbe9fd0bec4d96`.
The installed inner server matches its bundle declaration:
`d79def2f9aaf06d6b851e568150762b8e7ee24a898a314cf34b210cbd9ea14b6`.
All 29 installed library hashes match as well.

Actual CLI preparation and independent audit produce **31 independent files,
96,041,305 bytes** in a new private root. Every original installation file
(**63**) remains unchanged. All **32 non-artifact/journal tables**, **82 existing
objects** and the **136-event prefix** are unchanged. One operator evidence
object/event is added; neither provisioning state nor accounting changes.
The evidence reference is
`cas:sha256:e7ed8a9e72da8f97eb9b9f596d21f49b8d8ed7161fd376d130401fc7ed49df56`.
There were zero Java processes before/after, no game launch, no model request
and no shared-desktop input. This checks software bytes, not source custody.

The first attempt retains two failures: a read-only audit queried nonexistent
outbox `seq` instead of `cursor`, before dispatch; the corrected audit then
encountered an `UNSAFE_PATH` rejection before output creation. Inspection
identified three empty SLF4J metadata directories carrying `0xffff0010`.
The changed implementation accepts only that exact empty sentinel during
opaque nested metadata inspection and records all three attributes. No nested
directory is extracted, no permissions are applied, and general outer archive,
symlink and nonempty-sentinel rejection remain. A fresh second scope succeeds;
the first result is not rewritten. Its before-state equals the second's.

Private sealed bundles under `C:/Users/Darian/.strata/evidence/`:

| Bundle | Files / bytes | Manifest SHA-256 |
|---|---|---|
| `2026-09-22-vanilla-runtime-01` — retained failures | 13 / 522,873 | `4e890cadb1a01f58d5bd00a918024368e1dfd79300d197bee4810ccc81d2b31f` |
| `2026-09-22-vanilla-runtime-02` — prepared software and audit | 84 / 97,613,226 | `c9ecec5b8f3fbbb3b8ed97a5a9057aae26c6cb87cb15a8d50def691d397647af` |

Counts exclude each manifest itself. Source copies, actual command output,
before/after databases, original full installation hashes and all prepared
software remain private. Existing sealed acquisition/game evidence is untouched.

## Licensing and remaining work

The implementation retains 34 embedded POM/license/notice records. A separate
bounded HTTPS capture retains 37 published component/parent POMs from the
publisher's [Mojang library service](https://libraries.minecraft.net/com/mojang/brigadier/1.0.18/brigadier-1.0.18.pom)
and [Maven Central](https://repo.maven.apache.org/maven2/org/slf4j/slf4j-parent/1.8.0-beta4/slf4j-parent-1.8.0-beta4.pom).
Exact coordinate/hash/parent joins retain direct or inherited published license
declarations for **24 of 29** library entries. Fastutil's namespace-free POM
initially failed the capture parser after bytes were saved; independent offline
parsing resolves its declaration and preserves the initial error.

The five Mojang library POMs omit license declarations. Their exact component
licenses, shaded/native contents, Java runtime and compatible client inventory
remain under review; no blanket license or redistribution permission is inferred.
The [Minecraft EULA](https://www.minecraft.net/en-us/eula) remains a separate
retained distribution/prerequisite source, not a substitute for component evidence.
Full runtime configuration, update policy and cold restart also remain open.
Use the prepared software as input to that work; do not rerun this unchanged
preparation or promote its auxiliary receipt into a PackLock.

Original authority still totals **$0.7554 unresolved + $0.001458 settled**
within the original $10 allowance; two requests, uncertainty true, D12 consumed.
General model admission remains blocked. Every old 500-ms shutdown failure,
the five effective-file failures, Mineflayer/E9E incompatibility, scorer/setup,
isolation, client-startup and canonical recovery gaps remain. D13's 1,000-ms
normal-stop sample stays separate. Preserve M1–M7 and all later gates.
