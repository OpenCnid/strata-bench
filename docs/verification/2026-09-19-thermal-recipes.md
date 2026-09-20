# Focused Thermal recipe discovery — September 19, 2026

Status: **implemented_unverified** for M0.3b.3.2.3a. This extends D08 under
SPEC v0.2.6 and Forge capability minor 16. It does not close M0, T03 or G0.
F01/F06/F16/N01/N04/N06, C09 and the T01/T03/T06 contract surfaces are affected.

## Delivered behavior

The scoped `mcgame recipe-query` route accepts exact Thermal furnace/crucible
categories and one item or fluid focus. It retains the original crafting query
shape. Java, Python, generated public schemas and TypeScript agree on the query;
the private native response remains bound to body/connection/source generation,
query echo and revision. The broker removes private body/connection identifiers
before returning a public page.

Policy `jei-visible-crafting-thermal-item-fluid-focus-pages32/2` requires the exact
four installed JEI/Thermal artifact hashes. Machine candidates come only from
default non-hidden JEI category and focused-recipe lookups. The bridge reads
the public layout's two input/output slots, checks every alternative's visibility,
and projects plain item counts or fluid amounts in mB. It accepts only exact
recipe/category classes and vanilla simple input predicates. Custom/counted
predicates, tagged ingredients, unknown layouts/types, duplicate alternatives
and hidden ingredients remain unsupported.

Only displayed metadata is projected: positive energy in RF and the furnace's
integer chance/additional-chance tooltip. The projection follows the installed
tooltip's absolute value, fractional part and truncated percent. Raw sign,
additional precision, undisplayed XP and arbitrary recipe properties are absent.
Null energy/tooltip denotes an absent display, not zero energy or guaranteed
output. Machine discovery never reads recipe-book membership, grants execution
authority, invokes a transfer hook or performs processing.

Existing limits remain 512 candidates, 32 rows/32 KiB per page, and a cooperative
100-ms projection bound. Category and ingredient kind now participate in focus
revision identity. `craft.recipe_selection` remains crafting-only in both public
schema and native validation. Other categories and quests remain explicit .3b/.3c
work; authentic client/reference qualification remains .4.

## Exact dependency evidence

Installed bytecode was inspected with the pinned JDK 17.0.20.1+1 `javap -c -p`.
The private evidence bundle retains that output and artifact hashes. No game or
mod JAR was placed in the source repository.

| Installed artifact | SHA-256 |
|---|---|
| JEI 11.8.1.1034 | `4ca677c4d7b8234da2071b3e93424a2e1eedd06906c20f55ff22a078cfd6e3b2` |
| Thermal Expansion 10.3.1.25 | `ddf119c33990e991875968c0e810583af091044a3368c28838646f30ace33f4c` |
| Thermal Core 10.3.0.9, nested official JAR | `20c99f015b9b3d034da1f017a14876bc6f15838d72dc450cfd0c1bdd803c10b5` |
| CoFH Core 10.3.1.48 | `1e47ecfa7e3bedb7043854d44c53537aacb4b75807c2f7de5df6ab2fa785203d` |

The installed JEI API provides `getRecipeType`, default focused lookup,
`createRecipeLayoutDrawable`, `getRecipeSlotsView`, typed ingredients and the
platform fluid helper. No invented API or new runtime dependency was added.
Thermal's JEI furnace registration includes converted cooking recipes, so this
adapter does not incorrectly require those JEI objects to equal recipe-manager
objects. It also does not enumerate that manager to discover recipes.

Primary source cross-checks, read September 19:
[furnace layout](https://raw.githubusercontent.com/CoFH/ThermalExpansion/1.19.x/src/main/java/cofh/thermal/expansion/compat/jei/machine/FurnaceRecipeCategory.java),
[crucible layout](https://raw.githubusercontent.com/CoFH/ThermalExpansion/1.19.x/src/main/java/cofh/thermal/expansion/compat/jei/machine/CrucibleRecipeCategory.java),
and [energy display](https://raw.githubusercontent.com/CoFH/ThermalCore/1.19.x/src/main/java/cofh/thermal/lib/compat/jei/ThermalRecipeCategory.java).
These moving branches support inspection; the installed bytes govern guards.

## Actual checks

Private bundle: `.strata/evidence/2026-09-19-thermal-recipes-01/`, outside the
repository and gameplay workspaces. It contains source snapshots, JUnit XML,
logs, installed bytecode inspection and `verification.json`.

| Executed procedure | Result |
|---|---|
| `gradlew.bat :forge1192-client:test :forge1192-client:build :forge1192-client:writeTestClasspath --no-daemon --console plain` | **207 Java pass**, no failures/errors/skips; final build 25 s |
| `npm test`, with pinned Java/classpath and Windows Python guardian environment | **117 Node pass**, no failures/skips; 46.197 s |
| `uv run --frozen pytest tests/test_native_game.py tests/test_contracts.py tests/test_records.py tests/test_native_game_jvm.py tests/test_machine_recipe_query.py -q`, with pinned Java/classpath | **131 Python pass**, no failures/skips; 23.51 s |
| Schema export, TypeScript generation/build, Ruff on changed Python | Pass |
| `git diff --check` for tracked edits | Pass; ordinary line-ending warnings only |

Seven new Java tests cover exact artifact omissions/mismatches, fluid units,
tooltip semantics and nonfinite values, malformed layouts/counts/duplicates,
bounded sorting, absent energy display, no recipe-book read, rejection of machine
craft selections, and category/kind revision separation. Seventeen Python cases
exercise typed response and query failures without retries. The Node HTTP test
checks machine result integrity and no dispatch for invalid query arguments;
the existing real JVM/CLI fixture test now covers both Thermal categories and
private identity stripping. **All game/JEI effects in those fixtures are synthetic.**

The first full Java run passed before the final exact-four-artifact guard was
added; the final run passed 207 tests. No test failure was observed in this batch.
Deprecation warnings from the pinned Forge/Minecraft build remain in the logs.

Built candidate SHA-256:
`19eb090569302a5dce18cede266bc4d1343f17444216180948f638f886ff698e`.
It is **uninstalled**. The running disconnected E9E client still has the earlier
read-only candidate. A fresh read-only desktop capture showed the Windows
Security network prompt; no input was sent. The existing operator handoff remains
pending under the computer-use skill. No game server, gameplay worker, model
inference, capacity run, soak or experiment was started. Strata inference remains
**$0 dispatched** against the authorized $10 ceiling.

## Remaining qualification

Actual JEI visible/hidden parity, output amounts/tooltips, runtime changes,
blocking-call timing, expert crafting, machine controls/energy/fluid operation,
server evidence and reference comparison remain unrun. Compile success and
synthetic transport do not establish these properties. T03/G0 retain the actual
Mineflayer/E9E failure and the separate Forge candidate's unqualified status.
Complete pack seals, host/accounting/isolation, keybinding effects, team accounts,
soaks and scientific gates remain open.
