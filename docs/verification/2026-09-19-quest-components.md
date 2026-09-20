# Visible FTB task and reward displays — September 19, 2026

Status: **implemented_unverified**, M0.3b.3.2.3c.2.2a. The parent remains in
progress for item-alternative/choice/extension surfaces. SPEC v0.2.9 and Forge
minor 19 declare this D06 candidate; partial F01/F06/F16/N01/N04/N06, C09 and
T01/T03/T06 advance. No aggregate gate closes.

## Delivered behavior

`mcgame quest-components` takes one chapter/quest, `--part tasks|rewards` and a
cursor. The scoped broker and private native route validate exact query fields,
own caller/lease/body identity and response structure. Native source checks
retain the catalog's three exact FTB artifact hashes, current player's team,
non-editing mode, parent visibility/detail access and stable file/context.

Blocked and invisible-auto-claim rewards are removed before IDs or display
readers run. Visible entries expose title, ordinary tooltip lines and separate
task/reward status. Task completion/optional flags and formatted progress follow
the normal UI branch; hidden numeric progress exposes only its displayed percent,
and the current display clamps to the formatted maximum when appropriate. Raw
counts are absent. Rewards use `TeamData.getClaimType` with the current player's
UUID privately; only claim state and the team-reward flag are returned.

`FtbQuestDisplays` captures public task header/body and reward display calls
through a bounded `TooltipList` subclass overriding `add`, `reset` and
`shouldRender`. It never reads the private backing list. Normal item tooltips
are selected; Shift/Control/Alt must be released before/after display capture.
The debug/time-info tooltip path is not invoked. Unknown task/reward class
namespaces reject. Plain/unsupported text handling reuses the bounded quest
text projector; raw components, commands, NBT and selectors have no response
field. No button callback, submission, claim, rendering or texture binding runs.

The page inspects at most 512 components and returns at most 32 rows/32 KiB.
Each entry has at most 64 tooltip lines and 16 KiB; aggregate projected content
is bounded to 4 MiB. Title/line/progress-string limits and a cooperative 100-ms
timer reject overflow. Upstream callback blocking remains unqualified. Entries
sort by ID; query/part/source/content changes advance revision. Source/visibility
is rechecked and private body/connection identity is stripped by the broker.

This is a tooltip/status adapter, not complete quest interaction support.
Item alternatives, choice menus, extension task/reward types and full rich
content retain named work. A client `can_claim` display is not server proof of
a successful claim. Actual callbacks, tooltip parity and team transitions are
still unverified.

## Exact dependency and source evidence

FTB Quests/Library/Teams runtime pins are unchanged from the
[catalog report](2026-09-19-quest-catalog.md). Installed `javap -c -p` output
for task/reward display methods, claim state, visibility and TooltipList is
retained privately. The public API supplies no tooltip-list getter; capture
uses its supported virtual `add` extension point, not private reflection.
The [upstream TaskButton source](https://raw.githubusercontent.com/FTBTeam/FTB-Quests/1.19/main/common/src/main/java/dev/ftb/mods/ftbquests/gui/quests/TaskButton.java)
was cross-checked September 19 for normal progress formatting and hidden-number
behavior. Installed bytes govern the implementation.

The exact official FTB Maven POM and JAR requests returned **403 Forbidden**;
acquisition results are retained. The authorized official E9E installation
already contains the required Library bytes. The build now takes
`STRATA_FTB_LIBRARY_JAR` or Gradle property `strataFtbLibraryJar` and requires
SHA-256 `1ba0d7fa626ddb2e3c31e77e20b573ca79eb92e7667cca5b9a3e985fc22d1592`.
It is compile-only and external to the repository; no FTB classes are bundled
in the candidate. Missing/wrong bytes are typed build failures. Other machines
must supply that exact officially acquired artifact; no alternate version or
invented API is substituted. Runbooks record the new build prerequisite.

## Executed checks

Private bundle: `.strata/evidence/2026-09-19-quest-components-01/`, outside
the repository/gameplay workspaces. It retains installed bytecode, Maven
denials, logs, JUnit XML, source snapshots and `verification.json`.

| Procedure | Result |
|---|---|
| `gradlew.bat :forge1192-client:test :forge1192-client:build :forge1192-client:writeTestClasspath --no-daemon --console plain`, pinned Java and exact external FTB Library | **228 Java pass**, zero failures/errors/skips; build 26 s |
| `npm test`, pinned Java/classpath and guardian Python | **120 Node pass**, zero failures/skips; 51.148 s |
| `uv run --frozen pytest tests/test_native_game.py tests/test_contracts.py tests/test_records.py tests/test_native_game_jvm.py tests/test_machine_recipe_query.py tests/test_quest_catalog.py tests/test_quest_text.py tests/test_quest_components.py -q`, pinned Java/classpath | **187 Python pass**, zero failures/skips; 25.88 s |
| `compileJava` with a different installed FTB JAR | Expected `FTB_LIBRARY_API_HASH_MISMATCH`, nonzero exit |
| `compileJava` without the external artifact setting | Expected `FTB_LIBRARY_API_REQUIRED`, nonzero exit |
| Candidate ZIP inventory | No `dev/ftb/` classes bundled |
| Schema export, TypeScript generation/build, changed-Python Ruff | Pass |
| Tracked `git diff --check` and changed-document local-link check | Pass; only Git line-ending warnings |

Eight new Java cases cover parent/entry hiding canaries, task/reward separation,
unknown claim states, source/visibility changes, duplicate IDs, stable paging,
UTF-8/row/page/candidate bounds, timeout and normal progress-format branches.
Twenty Python cases and a Node HTTP case reject private/raw fields, wrong roles,
invalid Unicode/cursors, unsupported rich payloads and extra selectors without
invalid dispatch/replay. The actual JVM/scoped CLI fixture tests both task and
reward pages and private identity stripping. **Game/FTB effects are synthetic.**

An earlier compile-only attempt failed because it used `TooltipFlag.NORMAL`;
the pinned 1.19.2 API requires `TooltipFlag.Default.NORMAL`. This was corrected
before the successful build. Its log remains alongside final and expected
negative checks. Gradle/Forge deprecation warnings remain recorded.

Built candidate SHA-256:
`ca3493f0fda699822b81c5e6f2d6ca6bec4303751bc626ea4cd2b2be1af12cd2`.
It is **uninstalled**. No game server/worker, model inference, capacity test,
soak or study was started. Strata inference remains **$0 dispatched** against
the authorized $10 ceiling.

A fresh read-only desktop capture still shows the Windows Security prompt over
E9E. No input was sent; the existing operator handoff remains pending under the
computer-use skill. Desktop authorization itself remains active.

## Remaining qualification

Real E9E class loading, optional-library behavior, public callback effects,
normal-tooltip/claim/team parity, modifier handling, blocking-call timing and
isolation require authentic evidence. Fixtures and source inspection cannot
close those gates. Choice/item-alternative/extension displays, quest mutations,
other machine adapters, complete pack locks, keybinding effects, native host/
accounting/isolation, team capacity, soaks and scientific gates remain open.
T03/G0 retain the actual Mineflayer/E9E handshake failure and the separately
unqualified Forge candidate.
