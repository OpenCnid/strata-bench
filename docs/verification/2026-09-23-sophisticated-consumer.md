# Exact Sophisticated Core configuration consumer

**Result:** M0.3.2b.4 is verified for the fixed E9E consumer control. Fresh
control05 passes all 45 authentic audit checks and all 290 getter calls.
Controls01–04 remain sealed failures. The complete E9E profile and G0 remain open.

M0.3.2b.4 addresses a concrete remaining E9E configuration/provenance dependency
of G0 item 2 and private setup qualification. Coverage inherits F01/F05/F10/F16,
N01/N03/N04/N06/N08, C03/C04/C18/C24 and partial T01/T02/T10/T13.
The actual GPT-6 Luna/Mineflayer pilot and script-handle control remain verified;
this work does not replay them or advance M1–M7.

The existing authenticated craft importer deliberately cannot grant qualified
score credit. Its remaining setup/profile authority is a prerequisite to that
connection. Review of current source and retained evidence identifies the actual
Sophisticated Core consumer as a missing check behind the five effective-file
findings. The earlier loaded server/client snapshots establish raw configuration
values, but not the cached getter result.

## Implementation

The fixed operator-only producer and private parser are in
[e9e_config_consumer.py](../../evaluator/src/strata_evaluator/e9e_config_consumer.py).
Rendering requires exact hashes of Sophisticated Core 0.6.4.730 and the official
COMMON overlay. The control checks the registered COMMON source, matching loaded
spec and all 145 raw entries before querying only those IDs twice. It emits one
bounded private log record containing before/after raw lists and actual results.
The parser rejects missing/duplicate records, duplicate JSON keys, changed raw
values, missing/reordered IDs, numeric booleans, inconsistent reads and results
that disagree with the exact parser semantics. This log record does not itself
authenticate its process or grant mechanics, lock, scoring or gate authority.

Exact bytecode inspection shows that `isItemEnabled(ResourceLocation)` may
initialize its cache, and an unknown cache entry may append a default-enabled
value to the config. The control does not query absent raw IDs or clear/reset
the cache. Its after-check detects unexpected appends; a stopped-file comparison
must independently preserve the effective COMMON config hash. Cache initialization
remains a disclosed intervention, distinct from the old raw-only snapshot policy.

The current overlay contains 145 entries; the legacy SERVER overlay contains 129.
Their interpreted values differ for 14 shared IDs; 16 IDs occur only in COMMON.
The exact mod uses `Boolean.valueOf(String)`, including vendor `alse` strings
that evaluate false. No guessed migration, vendor edit, file-check exclusion or
claim of legacy/current equivalence is introduced.

Pinned inputs:

- Mod JAR: `0de1a4c730674ad9f27611fa17b866f7ca5dca15841854d64867693c2a5862fe`
- COMMON overlay: `375d814abf3b8d82a8b70e9c55ae51604034dc31ab91b1577ebf36e1e40d06e5`

## Verification

The consumer, mode-inspector and connected-client parser selection passes
40 Python tests, with two existing Typer/Click deprecation warnings:

```text
pytest tests/test_e9e_config_consumer.py tests/test_pack_modes.py tests/test_client_configs.py -q
```

Focused Ruff passes and Node's syntax check accepts the generated control.
These are synthetic/source checks; actual getter behavior requires the separately
prepared headless reference. It uses the unchanged telemetry 0.3.13 module, a fresh
original-world clone, distinct one-use authority, private output and loopback port.
No player, model request or shared-desktop input is used by that control.

The first authentic attempt, `2026-09-23-sophisticated-consumer-live-01`, is
retained as **fail**. KubeJS's existing class filter refuses direct loading of
`net.minecraftforge.fml.config.ConfigTracker`; no getter is called. Signed
startup contains a script error and baseline admission correctly rejects it.
The stopped-state audit passes 43/45 checks, failing clear startup and actual
consumer execution. All six server/ten outer processes terminate normally in
203.547/208.563 seconds. Original files, COMMON config and all 39 accounting
tables remain unchanged. The native clock records 208 ticks/31.243952 seconds,
without full active-time or avatar-clock qualification.

Failed bundle seal:
`22c432df4630318ce6620d8a51d4dca808922f227c9b6d7b9ee47a0a62fb787a`
(320 files/44,321,572 bytes); audit:
`7f815fd43eb0a97fac2af271106795367d91d6c91bfbca1582bf72df115f9ac9`.

The fixed producer obtains only the predetermined public tracker singleton
through metadata reflection, leaving the class filter unchanged. This follows
the object-wrapping route already established by the actual script-handle
control. All 14 consumer tests pass after the correction; syntax validation
also passes. A distinct control02 has fresh profile/authority/output identities.

Control02 loads successfully and has clear startup, but its source guard rejects
before getter execution. Its stopped audit is 44/45, with only consumer execution
failing. All six server/ten outer processes stop normally in 205.156/210.531
seconds; 208 callback ticks/31.0382586 seconds are retained. Files and accounting
remain unchanged. Failed seal:
`b23ef0b7a74961a58ada7eece58c6f4213931ae3c9f9f968d9402773b396fe98`
(321 files/44,339,292 bytes); audit:
`5ab0cf7262f19bf007dd6fdbacf3c1e98ae13475a97d03be20d1d5f5cdfca4d0`.

A local JVM test with the actual pinned ForgeConfigSpec and Rhino reproduces
the faulty guard: native `spec.equals(spec)` and the corresponding Rhino call
both return false. The wrapper's equality is unsuitable for source identity.
Rhino strict identity accepts the same native spec/data object and rejects
distinct objects with equal contents. The production guard now uses strict
identity for spec, registration and raw-data objects. The local fixture uses
synthetic in-memory configs; its setup writes are not game interventions.
Control03 passes the corrected identity guard but fails on Rhino's ambiguous
`getRaw(List)` versus `getRaw(String)` overload, before getter execution. Its
stopped audit is 44/45, with only consumer execution failing. All six server/ten
outer processes stop normally in 197.953/203.313 seconds; 209 callback ticks and
30.2406721 seconds are retained. Original files, COMMON config and accounting
remain unchanged. Failed seal:
`f8e6fd34bb0e8bf91ce719900839c4c6d3ae2570cab211fb1bba6d974ba73804`
(326 files/44,363,822 bytes); audit:
`0f9b4b883717fdc2e4ace2db327c1b5745391eeeff0ef490c94369db76ca7d84`.

The producer now selects `getRaw(java.util.List)` explicitly. A complete local
preflight executes the unchanged generated production script using the actual
Forge, Rhino and Sophisticated Core classes, with synthetic in-memory config
registration and tick events. All 145 items return the expected value twice;
the private parser confirms 290 calls and unchanged raw configuration. Its first
fixture startup lacked FMLConfig initialization; the corrected fixture initializes
Forge paths/config only inside the private probe directory. Neither fixture is
a game run or source-authenticated scoring evidence. The corrected consumer's
14 tests, focused Ruff and generated-JavaScript syntax check pass again.

Control04 reaches the getter but KubeJS's runtime conversion rules make its
`isItemEnabled(ResourceLocation)` and `isItemEnabled(Item)` overloads ambiguous.
The standalone Rhino fixture did not reproduce that KubeJS behavior. The audit
retains 44/45 checks, failing only consumer execution, with zero getter calls.
All six server/ten outer processes stop normally in 195.859/200.922 seconds;
209 callback ticks/16.3340094 seconds are retained. Files and accounting remain
unchanged. Failed seal:
`c6abf5fbce5bfa8a7c1ffda6cf7fd29137db4ef409d8d9a408c39dc833920946`
(329 files/44,426,256 bytes); audit:
`cd1a15a89e9fb920f98ea1b6290ef7faae5acf356534325840ee1d1d0f4f466b`.

Both getter calls now select the full ResourceLocation signature explicitly.
The complete standalone preflight again verifies all 290 calls and unchanged
raw configuration; all 14 consumer tests, Ruff and syntax validation pass.
That remains a local interop check, not a substitute for KubeJS integration.

## Authentic corrected result

Fresh `2026-09-23-sophisticated-consumer-live-05` passes **45/45** independent
audit checks. All 145 pinned IDs return the expected boolean twice in the real
KubeJS/server runtime. Raw before/after lists and the stopped COMMON file match;
the registered source and complete control/runtime pins are bound. Signed
startup is clear, only the normal stop command appears in setup history, and
the consumed reference grant rejects replay. The private craft candidate remains
incomplete and unscorable, as expected for a headless configuration control.

All six retained server processes and ten outer processes terminate normally;
server elapsed time is 202.313 seconds and outer time 207.437 seconds. The native
callback clock records 209 ticks/15.5288068 seconds. It excludes startup and
post-callback time and does not qualify full active time or an avatar clock.
All 18,225 original source files, 1,542 immutable runtime files, 104 sealed fixture
files and 39 original accounting tables pass their unchanged checks. No player,
shared-desktop input or model request was used. Committed/reserved experimental
exposure stays **$2.831942 / $10**, including every unresolved amount under D19.

Successful bundle seal:
`72dcdc10cebad6305a5e527966ef60a2f720ff00a10089f56485d500d839acb7`
(326 files/44,466,563 bytes); audit:
`6522f3884453a3d7951debec3bcf2e3bb4f99f67cc02384e1a1c366f98b9e17a`.
Each bundle is private under `C:/Users/Darian/.strata/evidence/`; complete sealed
inventories are verified independently of the public report. Proprietary
artifacts, generated vendor-value controls and raw observations remain private.

All five historical strict file findings remain retained. Complete Create and
other legacy-consumer disposition, loaded-mod/provenance reconciliation, role
qualification, instrumentation parity and full scoring remain open. D14 isolation
qualification remains deferred to M1/G1. M0 is in_progress and G0 fail.

Next resolve the remaining E9E legacy/role/distribution findings, particularly
Create and Inventory Sorter, against the retained acquisition, exact-artifact
and loaded-role evidence before profile admission and qualified scorer credit.
Do not repeat this successful consumer or the successful LLM pilot unchanged.
