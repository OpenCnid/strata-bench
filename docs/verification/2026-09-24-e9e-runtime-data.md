# E9E startup data snapshots and retained Forge class failure

M0.3a.4k is **in_progress**. The snapshot producer, JVM delivery consumer and
LaunchProfile/4 binding are implemented, with **204 distinct focused tests**
passing. Actual input/class inspection passes **14/14**. The changed authentic
server boot **fails** safely before readiness: Forge supplies transformed class
bytes that differ from the raw vendor class pin. E9E stays VERIFIED, not SEALED;
M0 remains in_progress and G0 fail.

Coverage: F01/F05/F06/F16, N01/N04/N06/N08, C03/C04/C24, partial T01/T02/T13,
G0 item 2. This resolves a concrete missing dependency of the thirteen-check
provisioning admission; it does not advance M1–M7 or reopen D14 isolation.

## Finding that prevents sealing

The retained installed client/server startup logs record Cable Facades downloading
11 whitelist entries and zero blacklist entries. Installed `CFConfig` bytecode
unconditionally appends those downloaded entries to its local configuration and
uses the resulting patterns/maps for allowed/disallowed block checks. Its three
declared config settings provide no switch for these downloads.

Immersive Engineering's installed contributor downloader reads another mutable
remote file into its special-revolver registries. These are gameplay inputs,
not just update notifications. A fixed Java command and file inventory cannot
prove they are frozen. The old LaunchProfile/3 candidate now explicitly rejects
the known consumers with `FORGE_RUNTIME_DATA_UNPINNED`; the earlier preflight
result remains historical evidence, not sufficient current seal admission.

The exact original JARs are retained, including Immersive Engineering's existing
signature files. No vendor JAR is rewritten, signature removed, downloaded rule
omitted or parser logic replaced.

## Implemented producer and consumers

[Preparation](../../src/mcbench/runtime_data.py) accepts exactly three bounded
files with hashes and immutable publisher URLs. It compiles the small JDK-17
[runtime component](../../java/runtime-data/README.md) and packages the exact
bodies, resource index and class files into a deterministic JAR. It verifies
inputs again after construction and retains compiler/source/output pins.

The Java agent verifies the resource index before game startup. For two exact
class identities it changes one URL constant to the custom `stratafixed`
protocol, retaining every other class byte. The custom handler serves only the
three named bodies from verified memory with the response shape expected by the
unchanged vendor consumers. Unknown routes, methods, proxy use, corrupt resources
and class drift refuse; a transformer mismatch halts the owned JVM with exit 126
rather than allowing Java's ignored-transformer-exception fallback.

Protocol discovery uses the documented JDK system-property lookup; ordinary
HTTP/HTTPS and other networking remain outside this targeted mechanism.
[Java 17 URL contract](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/net/URL.html).
This is neither full network isolation nor proof that every other mod's runtime
inputs have been frozen. Those limits remain explicit in the preparation result.

[LaunchProfile/4](../../schemas/v1/operator/FrozenE9ELaunchProfile.json) binds
the same snapshot receipt/JAR in both role inventories and exact role-relative
`-javaagent` arguments. The seal and fresh-instance launch consumers validate the
resource manifest and endpoint without dereferencing archived source paths.
Existing generic and vanilla profiles retain their behavior. The original E9E
inventory is not changed to insert this addition.

The bounded [cold-start /2 consumer](../../tools/e9e_cold_start.py) additionally
holds the snapshot JAR/receipt and requires both class-binding messages and all
three actual resource-read messages. Readiness or an agent-startup message alone
cannot pass. Existing 300-second boot, 120-second drain and 425-second outer
watchdog bounds remain; this does not change D13's emergency-stop requirement.

## Actual acquisition and offline verification

The official repository refs were resolved once, then exact commit-addressed
bytes acquired and retained privately with ref responses and HTTP metadata:

| Input | Publisher revision | SHA-256 / bytes |
|---|---|---|
| Cable Facades whitelist | `515c4ebe9ba1aa6abf04ca91fdac66ea95eb6a1d` | `1af08d8fe035da00c3eaef214503b9b963ed89dfbecc35a808cb5eea5327f832` / 285 |
| Cable Facades blacklist | same revision | `526b1210f9a3ed6ae05e76fcefc2c5e171c327b03389c592dbfc9624223e1e15` / 30 |
| IE contributor revolvers | `d3b7ef6f719e3c073f4f99d2a824ef1fb4c29d0e` | `17e312b9f069050962e227dbe7b3ead006a2288eb49cadc93246c46ad76f2a30` / 4,350 |

These are new snapshots. They do not recover or prove equality with historical
network responses. Source repositories are
[Cable Facades](https://github.com/Porting-Dead-Mods/Cable-Facades/tree/515c4ebe9ba1aa6abf04ca91fdac66ea95eb6a1d/configs)
and [Immersive Engineering](https://github.com/BluSunrize/ImmersiveEngineering/blob/d3b7ef6f719e3c073f4f99d2a824ef1fb4c29d0e/contributorRevolvers.json).

Actual prepared inputs pass the private 14/14 audit: resource validation, real
JVM delivery with Java socket connections denied by the fixture, both original
class pins, reversible single-constant transformation, unchanged vendor JARs,
rejection of the old unpinned profile and unchanged original authority. The first
snapshot JAR is retained; adding read/refusal diagnostics produces the executed
9,569-byte JAR:
`56156bcc302d92b45ca02958d7d1a7c18ffbbcfe5badfb500b56ab3bd877bbef`.
The original 9,222-byte preparation is
`76f987c3a86ff945f8081e74aa23c98800fb308e81287d08367933b9272716e2`.

## Authentic changed boot and retained failure

Fresh server `e9e-frozen-data-01` independently copies and verifies all 8,799
original files, adds only the snapshot JAR, and preserves the source inventory.
The original Java, Forge arguments, telemetry, expert settings and online port
remain pinned. No client, player action, shared-desktop input or model is used.

The changed boot stops after **24.922 seconds**, exit **126**, before readiness.
The agent's resource index initializes, then it refuses Cable Facades:

- Raw JAR class: `601b70c83a14debbb5e4679196a319c1a31eab4d4b008cd33b1feca2551bda0d`.
- Actual Forge-loaded class: `1ab0dee01c531ff6a89fd85aee2109f5e8036d342e0c283e76a9101b0aab8092`.

All **3/3** retained process handles are signaled, the owned Job is empty, and
no forced parent cleanup occurs. The lifecycle result remains fail. Raw runtime
class bytes were not captured, so the observed hash is not added to an allowlist.
An offline six-case ASM 9.7.1 serialization probe does not explain it: four
non-frame-recomputing cases reproduce the original hash; two frame-recomputing
cases cannot resolve a required type. This negative is retained without a game
replay or an invented equivalence claim.

All **39 original authority tables** remain exactly unchanged. Original exposure
remains **$2.831942/$10**, with every unresolved amount reserved. No model calls.

## Executed source checks and evidence

Windows/JDK 17, retained Python virtual environment, `-X utf8` and project
`src`, `evaluator/src`, `tools`, `tests` on PYTHONPATH:

| Executed selection | Result |
|---|---|
| `pytest tests/test_runtime_data.py tests/test_pack_forge.py -q -x` | 47 pass, 65.79 s |
| `pytest tests/test_pack_launch.py tests/test_provisioning.py tests/test_records.py tests/test_pack_worker.py -q` | 137 pass, 41.75 s |
| `pytest tests/test_runtime_data.py tests/test_e9e_cold_start.py -q` | 33 pass, 20.62 s |
| final `pytest tests/test_runtime_data.py -q` | 15 pass, 10.87 s |

Accounting for overlap, **204 distinct cases pass**. JVM tests use synthetic
bodies; the private audit separately exercises actual snapshots/classes. Retain
the two corrected unused-import lint findings and one imported-fixture name
collision. Full Ruff and diff checks pass. The final receipt validator tightens
the nine-entry class/resource allowlist; actual prepared bytes pass that check
without rebuilding or replaying the game.

Private evidence `2026-09-24-e9e-runtime-data-01`: **83 files / 1,215,462 bytes**,
complete EvidenceBundle readback pass. Seal:
`8c3176a432da6c463e4d6be4fa64181daf2bab1aa26b91c3009e0bd73ec3a488`.
Offline audit: `a1e61b3a200f9deb9b94c540cbf2f0e2174f021fbb447ed7fe665c5f993f9680`.
Live failure audit: `cb204380d9a565921da3475721fba4eaab8d542c33ed47ee55f7d8b7556018d7`.
The used server copy remains outside the archive; do not replay it.

Next capture and inspect the actual post-Forge class bytes under bounded private
diagnostics, prove the transformation relationship and bind the correct loading
phase. Then qualify the changed server/client snapshot profile, review remaining
startup inputs and assemble a distinct inventory/lock preserving the original
VERIFIED inventory and all historical failures. The thirteen checks and all
remaining G0 outcomes stay open; no milestone or release claim is promoted.
