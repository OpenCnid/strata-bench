# Settings write-boundary crash fixture

2026-09-20. Operator-only. M1.1a.2.3c.2a, F06/F09/F16,
N01/N02/N03/N04/N06/N08, C10/C11/C14/C18, partial T05/T07/T13.
Implemented with synthetic JVM evidence; authentic exact-artifact qualification
remains M1.1a.2.3c.2b. No aggregate gate changes.

The existing settings store now accepts a package-private observer at six
explicit write boundaries: after durable prepared receipt, native setter plus
readback, and confirmed options replacement, separately for apply and rollback.
Ordinary store constructors install a no-op observer. The private protocol,
gameplay tool catalog, thirteen canonical records and game contract minor 34
are unchanged. A rebuilt artifact nevertheless has a new runtime fingerprint.

`SettingsCrashProbe` consumes only the bounded exact-schema six-value plan in
a fresh private root outside the game profile. It verifies the existing mutable
target is unbound and uses the same protected store. It forces original options
and an armed snapshot before apply. At the chosen point it forces actual runtime,
persisted state and options, then halts the JVM with code 86. No finally cleanup,
shutdown hook, rollback or missing transaction receipt is synthesized. Existing
output/journal files fence rearming. Unknown/extra plan fields reject.

`ClientSettingsCrashProbe` invokes that fixture only on the client thread after
mod loading, at the title screen with no player/world, using the exact Curios
artifact and registered-object owner. It is inactive without its explicit JVM
property. Combining it with settings/game bridges, discovery, frames or collision
diagnostics rejects before listener installation. There is no endpoint or
physical event and no gameplay settings capability. Source/usage is documented
in the [settings runbook](../operations/forge-client-settings.md); SPEC v0.2.39
records the development-only contract without relaxing T05.

## Executed checks

Windows, pinned Temurin 17.0.20.1, Forge 43.4.23, official exact FTB Library,
CPython 3.12.14; the existing immutable build-input checks run.

- Focused Gradle store/HTTP/crash tests: **33 pass**, zero failures/errors/skips.
  Six separate JVMs halt at the specified point; six newly launched recovery
  JVMs query status and roll back without an apply branch. Each checks the
  expected partial runtime/disk combination, preserved unrelated bytes,
  original journal prefix, exactly one prepared transaction, restored map,
  final rolled_back status and absence of a clean-shutdown hook marker.
  Two additional tests cover invalid/reused plans and diagnostic-mode conflicts.
- Full `:forge1192-client:test :forge1192-client:build
  :forge1192-client:writeTestClasspath`: **448 pass**, zero failures/errors/skips;
  build successful in 28 s. Existing deprecation warnings remain.
- `pytest -q tests/test_native_settings.py tests/test_native_settings_jvm.py
  tests/test_client_discovery.py tests/test_gameplay_package.py`, with the current
  compiled classpath and pinned JVM opt-ins: **33 pass**, zero skips, 5.40 s.
  Actual HTTP/JVM transport here still uses synthetic runtime bindings.

Built candidate SHA256:
`6332576ea722a9ab49255cb0187851b22e4e9f4fb8e42f70dbbdc19eb723f051`.
Full/focused XML results, build/Python logs and source/artifact manifest remain
external under
`C:\Users\Darian\.strata\evidence\2026-09-20-settings-crash-implementation-01`.
No live inference, Minecraft launch or desktop input occurs in these checks.

These tests use real abrupt process death and files but deliberately synthetic
bindings. Authentic partial-state crashes, new-session recovery and independently
observed terminal identity on the exact new artifact remain required. Missing
phase reports or unexpected exit codes cannot pass a sample. Preserve each
failed state and old artifact; do not replay apply or reuse an old fingerprint.
The six points are between writes, not interruption inside an arbitrary setter
or power-loss/directory-metadata durability. Physical effects, native writer
exclusion, repair accounting and full T05/G1 remain open.
