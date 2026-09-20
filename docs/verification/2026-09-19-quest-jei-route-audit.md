# Exact task-to-JEI route audit

2026-09-19, operator-only. M0.3b.3.2.3c.3.2b.3b.1; F01/F06/F16/N01/N04/N06,
C09. Source inspection only; no action enabled or acceptance test passed.

The exact installed ItemTask callback has three branches. A non-consuming task
with exactly one display item uses the available recipe helper. An empty display
list shows a toast. The remaining branch opens ValidItemsScreen. The current
candidate supports only that last branch, with existing source/page/widget guards.

For this pack, the recipe helper is in **FTB XMod Compat 1.2.4**, not in the
Quests JAR itself. `JEIRecipeHelper.showRecipes` delegates to
`FTBQuestsJEIIntegration.showRecipes`, which reads its public runtime field,
checks the ingredient type, creates an OUTPUT focus and calls public
`IRecipesGui.show`. The helper's availability method returns true independently
of runtime availability; the implementation must validate the actual runtime.

The exact JEI `RecipesGui.show` opens only if `logic.showFocus` succeeds. A void
callback returning normally therefore cannot prove a new recipe screen opened.
The screen captures a private parent on opening. Its ordinary `Screen.onClose`
override returns to that parent and clears recipe history. `RecipesGui.back`
only traverses recipe history: it is not equivalent to closing to the quest book.

The public `IRecipesGui` API supports showing focuses/categories/recipes and
reading the ingredient under the pointer. It does **not** expose current focus,
visible recipe-page contents, or the parent screen. The implementation must not
invent these getters, treat a recipe lookup as the current rendered page, or
read an unfiltered private recipe graph. Current recipe lookup remains separately
bounded to its declared crafting/Thermal categories.

Next implementation: validate exact XMod/helper/JEI pins and common runtime
identity before one charged TaskButton callback; retain parent/task/source and
opened-screen identity from the opening; expose an explicitly identified recipe
screen state and its ordinary close/return lifecycle, with stale/changed-source,
no-open, cancellation and uncertain-effect cases. Readable current-page content
needs its own filtered projection or qualified current-screen instrumentation.
No existing item-menu action should be silently repurposed as JEI history Back.
Loaded UI/reference/pointer/resource/isolation checks remain required.

## Evidence

Read-only `jar tf` and JDK 17.0.20.1 `javap -p -c` against the actual installed
JARs; mapped Minecraft Screen API inspected from the pinned test classpath.
No downloads, desktop input, game/server/worker launch or inference.

- FTB XMod Compat JAR SHA-256:
  `9c8c169088cf53834190cc3ac78f554a78c8b8e9c0689cf287ab1c158582fede`.
- JEI 11.8.1.1034 JAR SHA-256:
  `4ca677c4d7b8234da2071b3e93424a2e1eedd06906c20f55ff22a078cfd6e3b2`.
- FTB Quests retains `b008de3ad8ed0d331af2853f12369ec560348348fd1e62a21dbbdad6c90e5678`.
- Private raw bytecode, source snapshot and artifact hashes:
  `C:\Users\Darian\.strata\evidence\2026-09-19-quest-jei-route-01`.

This is an implementation prerequisite audit, not proof that E9E lacks an API.
The separately retained Mineflayer failure concerns exact Forge negotiation;
the current Forge bridge's remaining work concerns integration and qualification.
