# Vanilla role assembly and explicit-environment cold restart

September 22, 2026. Operator-only. M0.3a.2 remains `in_progress`; M0 is
incomplete, G0 fails and G1â€“G5 are not run. Coverage: F01/F05/F16,
N01/N04/N08, C03/C04/C24, partial T01/T02/T13 and G0 item 2.

## Working implementation

[Provisioning](../../src/mcbench/provisioning.py) now preflights both complete
role inventories before importing any installed file. Missing second-role
provenance, origin or files cannot leave thousands of first-role objects in
storage. Copy-time hash checks and final rescans remain required; this is not
a claim that every possible interrupted import is transactional.

The launch contract now accepts explicit `SystemRoot`, `WINDIR`, `TEMP` and
`TMP` alongside the existing four settings. Directory values must be absolute,
existing and free of links/reparse points; supplied aliases must agree. Unknown
names and NUL values reject. Both template sealing and the
[bounded development server](../../tools/development_server.py) use that
validator. No environment is filled from inherited account/provider state.
Temporary-directory privacy and runtime isolation still require their own
evidence; a validated path alone does not establish that boundary.

## Source and process verification

Windows, Python 3.12.14, existing locked dependencies:

- `pytest -q tests/test_provisioning.py tests/test_vanilla_artifacts.py`:
  **51 pass**, 3.56 s. Includes three preflight negatives and eight explicit
  environment cases. Two existing Typer/Click deprecation warnings remain.
- The existing exact argument/stdin/environment process test and gameplay
  package test: **two pass**, 0.55 s. Real local child process; synthetic
  contents, no model. Undeclared environment canaries do not reach the child;
  operator source remains outside the four-file gameplay package.
- Full Ruff passes. The earlier 43-case preflight run is a subset of these
  checks, not another 43 distinct cases. No broad unchanged matrix ran.

## Actual private installation and admission

The existing acquired client/server software and publisher-matching Java copy
were assembled into **3,748 client files and 349 server files**: 4,097 files,
996,071,013 bytes. Server configuration and prior EULA acceptance were copied
from the existing authorized installation without new acceptance. All 27
shared client/server library paths have identical hashes.

The real `pack verify` command rejects `PROVENANCE_MISSING`: 41 file references
across 36 distinct coordinates lacked component license evidence at dispatch.
The rejection adds **zero objects and zero events**. The four intentionally
retained operator provenance objects precede verification. The original
request remains ACQUIRED with no installed-inventory or sealed-lock ref.

Subsequent read-only collection retains ten exact published POMs and eight
license texts bound to publisher source-tree blobs. Seven LWJGL module POMs
cover 28 role artifacts; Brigadier's exact release source covers two more.
The remaining seven Mojang coordinates affect eleven role entries. No revised
role inventory was admitted; shaded/native content and complete legal/setup
review remain open. Source license evidence is not a blanket assignment to
every transitive binary. A raw license URL's HTTP 404 is retained; the exact
Git tree/blob route subsequently supplied the bytes with verified Git hashes.

## Authentic bounded server lifecycle

The first copy, using an empty launch environment, failed before readiness:
JNA could not extract its native DLL into the default temporary location.
Minecraft returned exit code zero, but retained critical log signatures caused
`SERVER_RUNTIME_FAILURE`; the result remains failed. Its second round never
started. All 357 failure files remain unchanged.

A separately preregistered copy used explicit Windows directories and a new
private temporary directory. The executable and all software stayed pinned;
`-XX:ActiveProcessorCount=2`, 1â€“2 GiB heap, localhost binding, online mode and
the existing configuration remained fixed. Readiness stayed bounded at 80 s,
each server exposure at 90 s and normal-stop allowance at 120 s.

Both fresh start and same-instance cold restart reached readiness and stopped
normally, without forced cleanup: **67.312 s and 26.282 s** including their
wrappers. Exact software/EULA hashes and semantic server configuration match
before and after. Independently retained `level.dat` files preserve version,
Survival mode and seed; saved world time advances from 2 to 5 and LastPlayed
increases. No avatar, client, model or shared-desktop input was used. No Java
process remains.

These are authentic server lifecycle/configuration observations. The existing
development launcher correctly retains `stopped_unqualified`, no campaign
admission and no canonical clean-save claim. This does not qualify complete
process history, the D13 shutdown gate, client/native loading, clocks, a
canonical checkpoint or game-plus-agent recovery.

## Conservation and next action

The independent offline audit passes **34/34 checks**, preserving all 32
non-artifact tables, 3,781 original source files and 4,097 role files. It checks
original tables, objects/event prefix,
costs, source/role files, retained failure and both bounded runs. Its initial
SQLite row-factory error and the legacy list-versus-mapping manifest-reader
error are retained; correcting these offline readers requires no game rerun. Original accounting stays **$0.7554 held + $0.001458 settled =
$0.756858**, under the original $10 authority; D12 remains consumed and general
model admission remains blocked. No new model request or refund occurs.

Private bundle: `C:/Users/Darian/.strata/evidence/2026-09-22-vanilla-roles-01`: **4,917 files / 1,468,304,523 bytes**, manifest SHA-256
`3c152dad6e2dbc5681eb6512886818b795bf4a2f24dd87148854fe41d574d1cf`.
Every file and the complete file set were reverified after sealing. Previous
acquisition, server-software and client/Java seals also verify unchanged.
Continue remaining component/native provenance, client launch/update-policy
evidence and the actual PackLock, then canonical custody/recovery integration.
Do not repeat the unchanged successful server pair. Scorer/setup controls,
isolation, Mineflayer/E9E incompatibility, five effective-file failures and all
old 500-ms failures remain explicit. D13's separate 568.994-ms normal-stop pass
under 1,000 ms does not change these gaps. M1â€“M7 remain preserved.
