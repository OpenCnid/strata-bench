# JEI input provenance and cleanup foundation — September 19, 2026

Operator-only; exclude this report and its evidence from gameplay contexts.

M0.3b.3.2.3c.3.2b.3b.1b.3b remains **in_progress**. Its new child .1 is
**implemented_unverified**: ordinary input provenance and cleanup ownership.
The charged motor, fresh-page fencing and public action remain child .2,
not_started. History Back remains .3c and authentic qualification remains .1b.4.
No navigation action is advertised or reachable from the action lane yet.

Subsequent work connects this foundation to the
[bounded navigation motor](2026-09-19-jei-navigation-motor.md). This report
retains the earlier phase's scope and evidence; use the later report and ledger
for current integration status.

Affected coverage: F01/F06/F09, N01/N02/N04/N05/N06, C09/C15 and partial
T03/T06/T07. SPEC v0.2.22, Forge minor 30, the eighteen action kinds and all
public schemas remain unchanged. This implements internal prerequisites of
SPEC 8.1's existing two-phase navigation requirement, without changing an
affordance, experiment or acceptance threshold.

## Implementation

[GameRecipeInput](../../java/forge1192-client/src/main/java/io/github/opencnid/strata/client/GameRecipeInput.java)
records private object identities from ordinary GuiIconButton handler factories
and the exact seven-handler RecipesGui router constructor. Match its last four
handlers to the four ordered, previously captured button objects. Retain weak
bindings for at most sixteen live routers and at most thirty-two pending
factories. Missing, malformed, duplicate, ambiguous or excess records cannot
authorize an input sequence. No private field lookup or handler replacement is
used, and nothing from this registry is exported to gameplay observations.

Three additional optional exact-target Mixins observe those factories,
constructors, router calls and button results. The candidate now contains nine
JEI Mixins. During a gesture, exactly one complete ordinary router call must
select the intended button in SIMULATE, then in EXECUTE. Screen/router/input
identity, callback ordering and returned handler must agree. Incomplete,
repeated, nested, competing or wrong-phase callbacks permanently invalidate
that gesture; a failed confirmation cannot be retried as input.

[JeiRecipeInput](../../java/forge1192-client/src/main/java/io/github/opencnid/strata/client/JeiRecipeInput.java)
provides internal helpers for ordinary Screen mouseClicked/mouseReleased and
the pinned public router handleGuiChange reset. Ownership is acquired before
preview, so cleanup remains possible when confirmation hooks are absent.
Cancellation invalidates the gesture before attempting reset, retains the
known router if reset throws, and releases ownership only after reset returns.
Cleanup never synthesizes a release click over the button. These helpers are
not connected to NativeGameRuntime or exposed as an action in this phase.

## Verification and limits

Windows, pinned JDK 17.0.20.101 and Forge 1.19.2-43.4.23. Ran:

```powershell
$env:JAVA_HOME='C:/Program Files/Eclipse Adoptium/jdk-17.0.20.101-hotspot'
$env:STRATA_FTB_LIBRARY_JAR='C:/Users/Darian/curseforge/minecraft/Instances/Enigmatica9Expert/mods/ftb-library-forge-1902.4.1-build.236.jar'
# From java/
.\gradlew.bat :forge1192-client:test :forge1192-client:build :forge1192-client:writeTestClasspath --no-daemon --console plain
```

Final build: **368 Java tests pass**, zero failures/errors/skips, 32 s.
The eighteen new synthetic tests cover identity selection, constructor bounds,
ambiguous/missing callbacks, event ordering, competing input, immutable records,
cancel-before-execution, failed-reset ownership and no replay. They do not
execute Minecraft input or the actual Mixin transformer. Unchanged Python and
Node suites were not rerun or counted as new evidence.

Audited the five exact FTB/JEI artifact hashes and installed JEI bytecode.
The native router's public reset unfocuses its handlers and clears pending
clicks; button unfocus clears the pressed flag without executing onClick.
Confirmed native SIMULATE/EXECUTE routing and compiled injection selectors.
The Mixin 0.8.5 audit caught an initial array-to-Object coercion mismatch;
the constructor callback now preserves array rank with Object[]. The first
34-second Java build passed before that static finding; it did not prove
runtime injection. The corrected candidate was rebuilt and retested above.
Diagnostic audit attempts used an incorrect CombinedInputHandler package,
a PowerShell scalar-indexed classpath, and named rather than SRG method/field
labels; corrected audits and their limitations are retained privately.

Final candidate SHA-256:
`8e41322e4acfa4108b8ebca5af4f91c701bab8bb299e0893343cb1076b27586f`.
It is **not installed**. The dedicated profile retains the previously tested
minor-30 `f10e7ad6…` read-only candidate, whose
[authentic connected checks](2026-09-19-forge-connected.md) remain separate.

Private evidence:
`C:\Users\Darian\.strata\evidence\2026-09-19-jei-navigation-01`.
This contains build/JUnit output, exact installed and compiled bytecode audits,
source snapshots, hashes and the verification manifest. Actual injection,
current-page/geometry checks, action-lane charges/deadlines, fresh rendered
results, real cancellation/timing, UI reference parity and isolation remain
required. No desktop operation, inference, soak, capacity test or study ran;
the long-horizon goal remains active and no aggregate gate closes.
