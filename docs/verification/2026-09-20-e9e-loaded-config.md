# Private loaded-config evidence on exact E9E

Date: 2026-09-20. M0.3.2b.1 / M3.1a; partial F01/F05/F10/F16,
N01/N03/N04/N06/N08, C03/C04/C18/C24 and T01/T02/T10/T13.
Full mode, consumer, client-role, mechanics, isolation and G0 qualification
remain incomplete. The five strict effective-file failures are retained.

Telemetry **0.2.0** adds explicit private config queries and startup plan binding.
At the first server tick END, it reads public Forge registration/spec/raw data
without invoking config-value getters, mutation, correction, reload, saving or
reflection. Selected values must survive two identical copies with unchanged
registration/spec/data identity and loaded status. This establishes matching
consecutive reads, not an atomic watcher-thread transaction or consumer-cache
equivalence. Failed/unsupported/quota outcomes contain no partial values.

The strict producer/consumer contracts and quotas are in
[SPEC section 7](../../SPEC.md) and the [telemetry runbook](../operations/forge-telemetry.md).
Historical 0.1.0 streams and input config schema 1 remain separately accepted.
The new private payloads cannot earn a craft/machine score and have no gameplay
transport. Public GameEvent structure and all 13 top-level record types remain
unchanged; these are versioned evaluator-only payloads.

## Actual server evidence

The existing dedicated E9E 1.27.0 / Forge 43.4.23 server used its reviewed
ServerStarter 2.4.0 path and Temurin 17.0.20.1+1, with existing expert world,
online authentication, loopback binding, 2–5 GiB heap and no player client.
Each run was bounded to 240 seconds plus the existing 120-second normal-stop
grace. No forced stop occurred. No shared-desktop input or inference was used.

The candidate JAR is
`edae85eface9d77d441ca1a19fa76dec235f653590977b00acdee76c0accff6f`.
Only the telemetry JAR changed in the complete top-level mod-file comparison;
the old 0.1.0 JAR is preserved in private evidence. The dedicated server now has
0.2.0 installed, so future profiles must pin this instrumented environment.
Vendor overlays were not edited and no pack support stage was promoted.

The first boot produced a complete 32-record spool and normal stop in
145.672 s, but three initial placeholder query paths were not source-backed.
That plan qualification is **fail**, retained with its raw evidence. It is not
part of the matched restart pair. The operator corrected those selectors to the
exact pinned overlay keys before launching either subsequent run.

| Corrected sample | Clean records | Server runner elapsed | Result |
|---|---:|---:|---|
| boot-02 | 34 | 149.438 s | Exit 0, normal stop, six requested snapshots, complete spool |
| boot-03 | 32 | 145.016 s | Exit 0, normal stop, same selectors/values, distinct boot ID |

The two corrected boots have identical selected config observations:

| File | Observed state |
|---|---|
| `bhmenu-client.toml` | Unregistered on the dedicated server |
| `nomoreworldsettings-client.toml` | Unregistered on the dedicated server |
| `inventorysorter-server.toml` | Unregistered on the dedicated server |
| `sophisticatedcore-server.toml` | Unregistered on the dedicated server |
| `sophisticatedcore-common.toml` | COMMON, loaded; all 145 `common.enabledItems` strings match the exact common overlay |
| `create-server.toml` | SERVER, loaded; three legacy paths are both undeclared and absent. Current extraction timer is 8, cannon shots per gunpowder 400 and delay 10. |

Requested startup selectors match each private input config. Both corrected
boots also pass all six existing expert furnace assertions (including absence
of the vanilla recipe). No player crafting, quest/team marker, machine outcome,
client reference or protected predicate was certified.

Stopped-file inspections still pass **263/268** checks: the same four missing
files and Create key mismatch fail. ConfigSwapper's clean pinned source revision
`21ba0bfedeabcc54dec93f304e69c7e61b683330`, cross-checked against the installed
3.2 bytecode, returns on a missing target file and warns/skips a missing key;
it does not invent the missing entries. See its
[ModeConfig implementation](https://github.com/Darkere/ConfigSwapper/blob/21ba0bfedeabcc54dec93f304e69c7e61b683330/src/main/java/com/darkere/configswapper/ModeConfig.java).
This explains the observed behavior; it neither makes the legacy settings
equivalent nor authorizes a file-check exclusion or guessed migration.

## Verification and limits

`uv run --frozen python -m pytest -q tests/test_telemetry.py
tests/test_telemetry_configs.py tests/test_gameplay_package.py` passes
**51 tests**, zero skips, 0.51 s. Typed values, exact selectors, absent versus
unloaded/unsupported cases, quotas, malformed/late/duplicate/
missing records, old schema compatibility and scorer rejection are covered.
Full repository Ruff and `git diff --check` pass.

The pinned offline `:forge1192-telemetry:test :forge1192-telemetry:build` passes
**11 Java tests**, zero failures/skips, with an 18-second final build and the
existing Gradle deprecation notice. These additionally exercise source/data/spec
replacement, immutable copying and bounded native failure outcomes. Initial test compilation failed on an old
constructor and an incorrect fixture copy call; both were corrected. The initial
test-only Ruff formatting failures and one operator import attempt without the
documented evaluator PYTHONPATH are also retained. None alters a game sample.

Private source/JAR/config/spool hashes, complete logs, XML checks, original plan
failure and corrected pair report are in
`C:\Users\Darian\.strata\evidence\2026-09-20-e9e-loaded-config-01`.
The pair result is a narrow selected-config persistence pass. Aggregate T02/T10
and G0 remain incomplete, with G0 still fail in the ledger. Per-mod cache effects,
loaded client role, full artifact seals, authoritative legacy disposition,
instrumentation overhead/mechanics parity, private transport identity and
adversarial isolation remain unqualified.

Next: finish exact role/consumer and acquisition evidence, preserve the five
findings until resolved on evidence, and advance independent authentic expert
craft/container/machine and recovery work. Do not use these six snapshots as
whole-pack configuration or gameplay acceptance.
