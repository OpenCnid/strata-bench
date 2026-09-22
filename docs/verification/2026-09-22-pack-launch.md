# Sealed-pack launch connection

September 22, 2026. Operator-only. M0.3a.3 is **implemented_unverified**:
the connection works with synthetic provisioning evidence and a disposable
Python process; the real vanilla request correctly remains blocked as unsealed.
M0 remains incomplete and G0 fails.

## Implemented behavior

[Pack launch resolution](../../src/mcbench/pack_launch.py) opens the existing
authority with SQLite `mode=ro`, takes one read transaction and reads private
CAS objects without initialization, migration or publication. It joins the
request, exact expected seal, role inventory, acquisition report and launch
profile. A simulation store cannot enter the live runner.

It verifies the materialization marker, both complete role file inventories,
directory membership, executable hash, working directory and explicit
environment. Missing/extra/changed files, empty added directories, runtime world
state, links/hardlinks, unsafe paths and mismatched seals reject. A command's
relative working directory resolves inside the selected materialized role;
its reviewed argument array and pinned absolute executable remain unchanged.
No environment values are inherited by this resolver.

[DevelopmentServer/3](../../tools/development_server.py) accepts the pack binding
instead of an independently supplied command. It checks the target before
creating evidence or a process, keeps evidence outside the pack/store, and
retains the resolved command plus its digest in the final result. The existing
bounded process, health and stop implementation executes that command. Legacy
development plans retain their original meaning and gain no PackLock credit.

This verifies a **fresh materialization at preflight**. It does not hold all
files against concurrent writers, validate every executable dependency, enforce
an OS isolation boundary, prove legal attestations, produce a canonical save or
admit a campaign. Changed runtime instances cannot be restarted through this
fresh-template check. Inventory-bound mutable-state custody/recovery needs its
own explicit policy; the previous stopped-instance policy also does not cover
the newly installed `java/` tree. Neither limitation is silently waived.

## Verification

The initial focused selection passed **113 tests**:

```powershell
python -m pytest -q tests/test_pack_launch.py tests/test_provisioning.py tests/test_server_health.py tests/test_vanilla_persistence.py
```

After adding result-digest binding and disjoint evidence paths, the affected
seven launcher cases and gameplay-package check passed **8/8**:

```powershell
python -m pytest -q tests/test_pack_launch.py::test_bound_development_server_uses_sealed_command_or_refuses_before_process tests/test_gameplay_package.py
```

That is **116 distinct focused source/process cases**, not 121 distinct tests.
The fixtures use synthetic distributions, terms and trusted operator
attestations. The successful process is Python imitating the readiness/stop
protocol, never Minecraft. Both selections report only the two existing
Typer/Click deprecation warnings. Full Ruff and whitespace checks pass.

The actual private authority audit passes **11/11** checks. Both the direct
resolver and integrated runner return `UNSEALED_PACK` for the original vanilla
request before creating an instance, run output or game process. The request
retains its verified 4,097-file inventory and no seal. Every row in all **34
tables** remains unchanged. Original accounting stays **$0.7554 held + $0.001458
settled = $0.756858**, original allowance $10, two requests, uncertainty present
and D12 consumed. No Java remains; no model or shared-desktop input was used.

Private evidence: `C:/Users/Darian/.strata/evidence/2026-09-22-pack-launch-01`.
The sealed set contains **18 files / 90,864 bytes**, with manifest SHA-256
`57b5685bf641908c8371fff5e584625632c60cb0e4b6215ed97647afeaff490c`;
all entries reverify. The documentation audit preserves all 406 old ledger IDs
and adds M0.3a.3, retains append-only history and later milestone rows, leaves
SPEC sections 3 and 15–19 unchanged, and resolves all 1,232 local links checked.
The sentinel lock in its negative plan is explicitly not an actual PackLock.
Its refusal is state evidence, not an authentic successful game launch.

Coverage: F01/F05/F16, N01/N04/N08, C03/C04/C24, partial T01/T02/T06/T13 and
G0 item 2. Canonical records and gameplay package are unchanged. D13's measured
1,000-ms pass and every legacy 500-ms failure remain intact, as do the five
effective-file failures and Mineflayer/E9E incompatibility.

Next finish the actual Mineflayer/server launch and runtime/update policy,
remaining legal/source review and bound provisioning checks, then seal and
connect the real pack to inventory-bound custody and joint recovery. Scorer/setup,
clocks and isolation remain required. No unchanged game trial is justified by
this source-only connection.
