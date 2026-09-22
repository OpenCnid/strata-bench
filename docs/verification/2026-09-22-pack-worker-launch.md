# Sealed vanilla worker launch and per-run configuration

September 22, 2026. Operator-only. M0.3a.3 is `implemented_unverified`;
M0 remains incomplete, G0 fails, G1–G5 are not run. Coverage: F01/F05/F16,
N01/N04/N06/N08, C03/C04/C24, partial T01/T02/T06/T13 and G0 item 2.

The fixed-argument launch format could not represent the working Mineflayer
client without freezing a run's lease/epoch/state path or admitting an arbitrary
configuration override. [LaunchProfile/2](../../src/mcbench/provisioning.py)
now pins the exact worker descriptor, Node/entrypoint, settings, explicit
environment and local-software update policy. Only typed run identity and fresh
output paths vary. Endpoint checks join the actual server properties.

[The launcher](../../src/mcbench/pack_worker.py) resolves the sealed profile,
generates the worker configuration, holds its bytes and the complete runtime,
and owns process cleanup before releasing either lease. Full mode performs the
fixed import preflight and starts the worker; import-only performs no account
authentication or game connection. Both have bounded output and process waits,
retained timing and explicit unqualified results. The
[operator command](../operations/provisioning.md) reads existing authority
without initialization/migration. It cannot admit an unsealed request.

This is fresh-instance launch support. It does not yet replace the existing
native development runner's server/capture path, qualify mutable restoration,
hold the server's transitive runtime, establish isolation or produce a score.
The generated private NativeLaunch schema was also refreshed to include the
already implemented M0 recovery `resume_component_ref`; no runtime behavior or
canonical record count changed.

Executed on Windows, Python 3.12.14:

```text
pytest -q tests/test_pack_worker.py tests/test_pack_launch.py tests/test_provisioning.py
pytest -q tests/test_pack_worker.py tests/test_records.py tests/test_gameplay_package.py
pytest -q tests/test_pack_worker.py
```

There are **127 distinct passing focused cases** across these selections:
63 existing provisioning/launch cases, 34 worker-launch cases, 29 record/schema
cases and the actual gameplay-package exclusion check. The final affected
selection passes **34/34 in 15.53 s**; the preceding schema/package selection
passes **64/64 in 16.15 s**. New process behavior uses controlled synthetic
processes with real Windows file leases. Existing launch tests include a
disposable Python server; neither is Minecraft acceptance evidence.

Retained development failures: the first combined selection had 86 passes and
five failures because the new overlap rule incorrectly excluded siblings of
the runtime manifest. The correction separates exact protected paths and the
actual runtime tree. Two unused-import lint findings and a later indentation
collection error were corrected. Final focused Ruff and whitespace checks pass.
Two existing Typer/Click deprecation warnings remain.

The private actual-file audit prepares a version-2 candidate from the existing
11,722-file runtime descriptor, installed vanilla server configuration and
pinned Java executable. Its first check rejected the legitimate serialized
`level-type=minecraft\:normal`. That failed candidate remains retained.
The parser now supports the inspected value escapes while rejecting escaped
key aliases, duplicate assignments and continued lines. Corrected and final
checks pass; the selected files and all **34 original authority tables** remain
unchanged. The original request remains **VERIFIED, unsealed**, and an attempted
resolution still refuses `UNSEALED_PACK` before creating a config or instance.
No game/model process, account authentication or shared-desktop input occurred.

Evidence is private under
`C:/Users/Darian/.strata/evidence/2026-09-22-pack-worker-launch-01`.
The corrected candidate and review are local preparation artifacts; their new
review references have **not** been published into the original operator CAS.
They are not substitute provisioning attestations or an executable authority.
The final audit retains exact changed source bytes and original-authority hashes.
The separately retained execution candidate changes only both commands' TEMP/TMP
paths to a prepared private scratch directory outside the evidence archive;
future execution must not mutate sealed evidence. Its SHA-256 is
`448929cf91e607f3ba552e81c1258ff984ae00b4cae3040148cfadb9fd8b4eae`.
The inspection invocation is not reusable execution state; use fresh run paths
after the actual seal exists. The operator command's help also executes successfully.

The private evidence set is sealed and independently reverified: **38 files /
1,529,085 bytes**, seal SHA-256
`46b1cc86adc21853e1595897560adf420f62c92ca6f8568b9d36b537f6b6506a`.
The documentation audit preserves all previous ledger IDs and the complete
append-only prefix, leaves M1–M7 and SPEC sections 3/15–19 unchanged, and checks
1,255 resolving local links. All 34 original tables still match at sealing;
the last process inspection finds zero Java processes.

Original accounting remains the $10 total cap with **$0.7554 unresolved hold +
$0.001458 settled = $0.756858**. D12 remains consumed. D05 account/EULA evidence
already exists; this creates no new user approval prerequisite or requirement
for a standalone license certificate. Complete remaining source/component and
runtime provisioning review, publish bound checks and seal the actual pack;
then connect the joint native launch, server custody/capture and restoration.
Scorer/setup, complete clocks and isolation remain open. D13 stays at the
approved 1,000 ms; old 500-ms failures, five effective-file failures,
Mineflayer/E9E incompatibility and the later roadmap are preserved.
