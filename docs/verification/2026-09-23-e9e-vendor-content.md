# Paired E9E vendor-content preparation

M0.3a.4b is **verified** for initial vendor-content preparation. The corrected
actual run passes 12/12 integration checks and prepares 18,233 files across
client/server roles. **100 focused tests pass.** E9E remains ACQUIRED;
complete role inventory, sealing and G0 remain open.

Coverage inherits M0.3a.4: F01/F05/F16, N01/N04/N06/N08, C03/C04/C24,
partial T01/T02/T13 and G0 item 2. M0 stays in_progress/G0 fail; M1–M7 and
D14's isolation deferral remain unchanged.

## Implementation

[e9e_content.py](../../src/mcbench/e9e_content.py), the existing
[provisioning consumer](../../src/mcbench/provisioning.py) and operator
`pack prepare-e9e-content` command now work together. The provider resolves
both archives from the original durable acquisition namespace and validates
its request, target, role, origin and digest bindings. The preparer verifies
the exact official archive and initial mod-capture pins, then publishes the
original captures and result back into that namespace without changing state.

Both archives have identical vendor overrides and project/file manifests.
The retained mod captures supply exact intake hashes and manifest relations;
these are operator observations, not signed publisher hashes. File IDs and
download origins must agree, and encoded/decoded filename variants are retained
as actually installed. Server content uses the pinned publisher ignore-project
list and exact ServerStarter glob behavior. Reviewed initial JEI bookmarks and
vendor directories remain initial distribution data.

Both source mod directories must match completely before output creation.
Added Strata instrumentation requires explicit exact path/hash/size exclusions;
it cannot replace or omit a vendor mod. Archive metadata/bootstrap files and
server-excluded overrides are inventoried, with no bootstrap execution.
The preparer verifies independent copies and unchanged source bytes; occupied
or failed destinations cannot be replayed. All license and effective-settings
qualification flags stay false.

## Actual results and retained failures

| Role | Vendor overrides | Mods | Total files | Bytes |
|---|---:|---:|---:|---:|
| Client | 9,606 | 232 | 9,838 | 375,427,271 |
| Server | 8,169 | 226 | 8,395 | 360,810,155 |

The client preserves 957 vendor directory entries; the corrected server
preserves 815. The server omits six present projects under the publisher's
eleven-project ignore list. Existing client and server Strata JARs are retained
in the exclusion audit, not copied into the vendor layer.

The first preparation copied all file bytes correctly but its independent
audit failed **11/12**. An actual Java 17 `PathMatcher` comparison over every
server override entry showed that `Paths.get` strips directory trailing
slashes before matching. Four empty parent directories (`kubejs/assets`,
`kubejs/client_scripts`, `local`, `packmenu`) should remain. The correction
normalizes paths, adds four regression cases and prepares a fresh destination.
The second audit passes **12/12**, including exact agreement with the retained
Java matcher output for all files and directories. No game run was repeated.

All 37 non-artifact authority tables remain unchanged in both attempts.
Existing artifact/event rows are preserved: attempt 1 adds two capture objects
and its result, while attempt 2 reuses those captures and adds one new result.
Only the corresponding private artifact-created events are added. E9E stays
ACQUIRED; original accounting/exposure stays **$2.831942 of $10**, with every
unresolved hold retained. No model, Minecraft, installer or shared input runs.
The Java glob comparator is fixed operator instrumentation.

Durable result references:

- Retained first attempt: `cas:sha256:ffedba0b80eb855bf3557c2ad0dce9341dc784cd949dcfe90a3e07ebcd3b1991`
- Corrected attempt: `cas:sha256:87dac24d58de4920accb437e3e0e73e57ad72421829715a915aba1aa6cdae493`

The first combined evidence-seal attempt exceeded existing count/byte limits
and remains invalid and retained. Evidence is preserved as separate bounded
control and per-role archive bundles. Each role archive uses ordered tar
parts no larger than 128 MiB; every archived member is read back and compared
with the exact prepared file/directory inventory without extraction. The
original prepared trees remain untouched. No evidence quota is relaxed.

| Retained bundle | Seal SHA-256 |
|---|---|
| Attempt 1 control, fail 11/12 | `5cb8b4422d1d13cb2282dc92372a4865c72c2fc85465c3a4cf0ffe624b6b795a` |
| Attempt 1 client archive | `a9e160e240a4d8552ad017262753002a0ff3e9e7627a650f8a522616c4114df1` |
| Attempt 1 server archive | `0730ef69e7ef8b6e6272aa9ac09140eade956037678120ba0f9b66e26f9ccd16` |
| Attempt 2 control, pass 12/12 | `64c4f1c74e638af01a9cab2219940b78a4f756b8ace6f169c0924cb214c761c8` |
| Attempt 2 client archive | `2f65623d59a4963dcb7170d8fdff5b793202a39cbbc0c5483c17febbae7461ef` |
| Attempt 2 server archive | `0dfb74f47ba3e5ae568627647d2161977e03a4437c5bf10d9be5fa71a6011230` |

Attempt 1 audit SHA-256 is
`bd1759a7a3b3b29380c4840fe051dba0d5657e003f7ab5f32f872856f157d651`;
attempt 2 is `751240b0174ed5ef4c9e532fc00ed0ab90bb7a5f0332bc8fba91d193314c994b`.
The control bundles bind their two respective role archive seals. Their
private base names are `2026-09-23-e9e-vendor-content-01` and `-02`, with
`-control`, `-client-archive` and `-server-archive` suffixes.

## Verification and remaining work

Executed `python -X utf8 -m pytest tests/test_e9e_content.py tests/test_provisioning.py tests/test_forge_runtime.py tests/test_vanilla_runtime.py -q`:
**100 passed in 17.62 seconds**, two existing Typer/Click deprecations.
Twenty-one new cases cover both roles, source/installed corruption,
manifest/filename mismatches, exclusions, copy changes, occupied outputs,
Java directory semantics and real provisioning/CAS integration with synthetic
archives. Ruff passes; its initial imported-fixture alias warning was corrected
before actual preparation.

This result supplies the vendor layer for complete role assembly. Still join
the exact client Forge/Minecraft/Java/assets software, server runtime, harness
layer, generated/effective expert settings and component license dispositions;
then feed complete roles to the existing inventory/seal consumer and bind
launch evidence. The old config/legacy findings and all original game failures
remain. Do not repeat successful controls or the verified LLM/Mineflayer pilot
unchanged. Private scoring/recovery/clock/cost requirements remain in G0.
