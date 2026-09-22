# Private Mineflayer worker and authentication-helper runtime

September 22, 2026. Operator-only. M0.3a.2 remains in_progress. This prepares
and checks the relocated runtime needed for the vanilla PackLock and connected
native launch. M0 remains incomplete and G0 fails.

## Implemented behavior

[Worker preparation](../../src/mcbench/worker_bundle.py), exposed through
`mcbench pack prepare-vanilla-worker`, requires the existing live vanilla
request and its retained npm report. It copies Node, the compiled worker,
public wire schemas, exact verified npm files, the ACL helper and a private
base Python runtime. It never copies account caches, game state or operator
instructions. No installation, authentication, model request or game starts.

Every selected source is pinned and held against writes/replacement while
copying. The output has independent files and an exact inventory. Changed npm
files, links/hardlinks, overlapping or occupied destinations and traversal
reject; a failed copy remains private without a published manifest and cannot
be reused. The original 12,000-file/1-GiB limits remain unchanged.

Private `WorkerRuntimeBundle/1` records source/output inventories, dependency
evidence and explicit exclusions. Python bytecode and site-packages are
excluded. The [worker's ACL invocation](../../backends/mineflayer/src/auth_cache.ts)
uses `-I -S -B`, preventing Python environment/site hooks and bytecode writes.
The copied base interpreter retains the worker's existing `.venv/Scripts`
lookup layout; it is not a redirector to the development virtual environment.
Launch paths use ordinary DOS/UNC spelling for Node compatibility; file
inventories retain extended Windows paths for long-path reads and leases.
Preparation leaves runtime/isolation/campaign qualification false.

## Verification

Source: **14 Python checks pass** (13 bundle cases and the gameplay-package
check), including private canaries, exact copies, source mutation, traversal
and retained partial-copy failure. Validator freshness, TypeScript compilation
and **12 Node authentication/dependency tests pass**. Those Node tests use
synthetic provider replies; native Windows ACL operations are real. Focused
Ruff and whitespace checks pass.

```powershell
python -m pytest -q tests/test_worker_bundle.py tests/test_gameplay_package.py
# From backends/mineflayer:
node tools/validators.mjs --check
node node_modules/typescript/bin/tsc -p tsconfig.json
node --test dist/tests/authentication.test.js dist/tests/authentication_dependencies.test.js
```

Actual preparation through the operator CLI produces **11,722 files /
654,076,586 bytes**. The relocated check holds all those files, loads the real
worker without creating an avatar, and confirms the copied Python executable,
prefix, encodings and ctypes all resolve inside the private bundle. Python's
isolated/no-site/no-bytecode flags are active. A new synthetic cache passes
create/read/write/verify; granting Everyone read permission then causes the
expected rejection. No real account cache is read. Write opens against Node,
Python and the ACL helper are denied while held. The complete runtime still
matches afterward. The successful held check takes **18.047 s**.

Worker capability digest:
`3b3c7938b62ee0a884e7c2e3712b18bb017476024c7b0688f62bcbfa46c1d47d`.
Corrected private runtime descriptor SHA-256:
`9d1098e8780f454a9324c64a33a5e21d18642a466e1a6f14d201a17006f3d0d9`.

Two initial failures remain retained. First, the audit compared normal and
extended Windows path spellings without normalization, despite Python loading
from the copied tree. After correcting that comparison, Node rejected the
extended entrypoint spelling with `EISDIR`. The implementation now emits
Node-compatible launch paths. A separate corrected descriptor changes only
the five path fields; original descriptor, failed commands and stderr remain.
The software was reused unchanged, not recopied. Malformed-path refusal was
also tightened after initial preparation and covered by the final source tests.

All **34 durable authority tables** remain unchanged. The original $10 cap,
$0.7554 hold, $0.001458 settlement, uncertainty and consumed D12 are preserved.
The vanilla request remains VERIFIED/unsealed. No Java, Minecraft, model
request, account authentication or shared-desktop input occurred. Raw evidence
and runtime stay private at
`C:/Users/Darian/.strata/evidence/2026-09-22-worker-bundle-01`.

Independent evidence audit: **17/17 checks pass**. The sealed private set
contains **11,778 files / 674,168,430 bytes**, all reverified, with manifest
SHA-256 `fb49f8c5160a8e2169a6bbd8e7d04ae7b27d56f67f3e881d808bef99e500ed6f`.
It retains both failed checks, both runtime descriptors, actual copied software,
synthetic-cache fixture, commands, source and accounting snapshots. The
documentation audit preserves existing ledger IDs, append-only history,
M1–M7 rows and SPEC sections 3/15–19; all 1,239 checked local links resolve.

## Next integration and limits

Connect the native game runner to an expected-hash runtime descriptor and hold
the complete inventory for its worker's lifetime. The runner still selects
the checkout-local worker; preparation alone does not change that launch.
Join this with the actual sealed server/client commands and selected
configuration/update policy, then inventory-bound custody and joint recovery.
Resolve both fresh role commands before either role mutates the instance.

This proves relocated loading and synthetic-cache ACL behavior, not live
authentication, arbitrary-process isolation, canonical checkpoint custody or
scoring. Component notices/source disposition remain separate; no standalone
Node license file was found beside the installed executable and none is
claimed copied. D05 account/EULA evidence already exists. Scorer/setup,
complete clocks and isolation remain open. Preserve all five effective-file
failures, Mineflayer/E9E incompatibility, D12's original delivery failure and
every old 500-ms failure. D13's 1,000-ms policy remains unchanged.

Coverage: M0.3a.2, F01/F05/F16, N01/N04/N06/N08, C03/C04/C24,
partial T01/T02/T06/T13 and G0 item 2. No unrelated M1–M7 work.
