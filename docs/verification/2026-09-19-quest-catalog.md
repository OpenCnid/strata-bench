# Player-visible FTB quest catalog — September 19, 2026

Status: **implemented_unverified**, M0.3b.3.2.3c.1. SPEC v0.2.7 and Forge
capability minor 17 declare the initial catalog within D06's existing scope.
F01/F06/F16/N01/N04/N06, C09 and partial T01/T03/T06 are affected. No milestone
or aggregate test/release gate closes.

## Delivered behavior

`mcgame quests --after 0 --json` lists visible chapters. Add `--chapter` with a
returned uppercase 16-digit code to list that chapter's visible quests. Java,
Python, generated public schemas, TypeScript and the broker carry the exact
`ftb_quests` query. Policy `ftb-visible-chapters-quests-own-team-pages32/1` pins
the three FTB artifacts below before optional classes are loaded.

`NativeQuests` uses fixed public reflection over the installed client API. It
requires a connected client thread, the current file's `self` team, verified
player membership, editing disabled and stable file/team/player/connection.
`getVisibleChapters` supplies chapter candidates; each entry's `isVisible`
runs before its ID/title/progress readers. Hidden or unknown chapter selectors
fail. Own-team progress is the ordinary FTB integer percentage/completion state;
it is not a benchmark score. There is no other-team selector or evaluator route.

The seven-field row contains kind, ID, plain title, progress, completion,
startability and detail-access flags. Chapter flags are null. Quest details
can be inaccessible even while the quest is visible. Source generation,
query/focus and projected content participate in revision checks. The broker
checks native body/connection identity and strips it from public results.

Bounds are 4,096 inspected entries, 32 rows/32 KiB per page, 1,024 Unicode code
points/4 KiB per title, 4 MiB aggregate projected content and a cooperative
100-ms deadline. Unknown fields, invalid Unicode, duplicate IDs, inconsistent
progress/flags, stale source and invalid cursors reject the whole page.
Upstream blocking calls cannot be preempted by this cooperative timer.

Descriptions, tasks, rewards, dependencies and ordinary submission/claim
interactions remain explicit .3c.2/.3c.3 work. Catalog visibility grants none of
those capabilities. Stock Mineflayer still rejects the absent FTB capability.
No quest writes, administrative completion or direct progress changes were added.

## Exact source evidence

Installed JDK `javap -c -p` output is retained privately. QuestFile delegates
visible chapters to ChapterGroup; the non-editing branch checks lazy visibility
and `Chapter.isVisible`. The native bridge also rejects editing mode. Quest
visibility, `hideDetailsUntilStartable`, own-team `canStartTasks`, progress and
membership methods were inspected in the installed classes. Native reflection
has not yet been exercised against a connected loaded E9E client.

| Artifact | SHA-256 |
|---|---|
| FTB Quests 1902.5.10-build.497 | `b008de3ad8ed0d331af2853f12369ec560348348fd1e62a21dbbdad6c90e5678` |
| FTB Library 1902.4.1-build.236 | `1ba0d7fa626ddb2e3c31e77e20b573ca79eb92e7667cca5b9a3e985fc22d1592` |
| FTB Teams 1902.2.14-build.123 | `2233122cfddfccafd5f4840ae63a556edd7088ad15e177fb1288367adef142f7` |

The upstream [quest view source](https://raw.githubusercontent.com/FTBTeam/FTB-Quests/1.19/main/common/src/main/java/dev/ftb/mods/ftbquests/gui/quests/ViewQuestPanel.java)
was cross-checked September 19. Its separate text and reward hiding rules inform
the retained follow-on work; installed bytes govern the adapter's guards.

Custom-recipe investigation also inspected KubeJS 1902.6.2-build.73
(`d9bc8bcca17fea536462a8471a2880adabc76ef8bdd84a93ad0b682a960ea5c7`).
Its client shaped/shapeless recipe decoding sets the modify-result callback to
null, while server construction can resolve a callback. A null client callback
therefore cannot establish ordinary fixed-output semantics. No plain-recipe
allowlist bypass was added. Stage, callback and ingredient-remainder behavior
remain required .3b work. See the primary [serializer](https://raw.githubusercontent.com/kube-mods/kubejs/1902/common/src/main/java/dev/latvian/mods/kubejs/recipe/special/ShapedKubeJSRecipe.java)
and [crafting interface](https://raw.githubusercontent.com/kube-mods/kubejs/1902/common/src/main/java/dev/latvian/mods/kubejs/recipe/special/KubeJSCraftingRecipe.java);
private installed bytecode is retained. This is not evidence that the already
observed expert furnace recipe uses a KubeJS custom serializer.

## Executed checks

Private bundle: `.strata/evidence/2026-09-19-custom-discovery-01/`, outside the
repository/gameplay workspaces. It includes logs, JUnit XML, source snapshots,
installed bytecode inspection, artifact hashes and `verification.json`.

| Procedure | Result |
|---|---|
| `gradlew.bat :forge1192-client:test :forge1192-client:build :forge1192-client:writeTestClasspath --no-daemon --console plain` | **214 Java pass**, zero failures/errors/skips; build 27 s |
| `npm test`, pinned Java/classpath and Windows guardian Python environment | **118 Node pass**, zero failures/skips; 46.918 s |
| `uv run --frozen pytest tests/test_native_game.py tests/test_contracts.py tests/test_records.py tests/test_native_game_jvm.py tests/test_machine_recipe_query.py tests/test_quest_catalog.py -q`, pinned Java/classpath | **148 Python pass**, zero failures/skips; 23.48 s |
| Earlier local Python contract selection | 113 pass; 1.04 s |
| Schema export, TypeScript generation/build, Ruff on changed Python | Pass |

Seven new Java tests include hidden-entry reader canaries, separate chapter and
quest flags, bounded sorting/pagination, source/content/focus changes, missing
or wrong artifact hashes, invalid progress/Unicode and timeout/bounds failures.
Seventeen Python cases and a Node HTTP case test strict response/query validation
and no invalid dispatch or replay. The existing real JVM/CLI fixture now covers
both chapter and quest queries, malformed selectors, caller scope and private
identity stripping. **FTB/game data and effects in all these tests are synthetic.**

Final contract review found that Python/JavaScript end-of-string regex semantics
could accept a newline after a 16-digit ID. Explicit length bounds now agree with
Java's exact matcher. Added request/response newline negatives, regenerated the
schemas and rebuilt TypeScript. Focused follow-up: **75 Python / 1 Node pass**,
zero failures/skips; Java source/JAR is unchanged. `git diff --check` passes for
tracked changes (ordinary line-ending warnings only).

Built candidate SHA-256:
`2fb018e989c06d29510d6321619925473dac5c3e45e51e0701ce8faef21b734a`.
The candidate remains **uninstalled**; the running disconnected client uses the
earlier read-only JAR. A fresh read-only window capture confirmed Windows Security
still covers the multiplayer screen. No desktop input was sent; the existing
operator handoff remains pending under the computer-use skill. No game server,
gameplay worker or model inference was started. Strata inference remains **$0
dispatched** against the authorized $10 ceiling.

## Remaining qualification

Actual loaded API calls, UI/visibility parity, own-team transitions, readable
quest detail/task/reward adapters, resource effects, timing and isolation remain
unverified. Candidate build and fixture success do not establish these. T03/G0
retain the actual Mineflayer/E9E handshake failure and the separate Forge
candidate's unqualified status. Keybinding effects, native host/accounting,
complete pack seals, capacity/soaks and scientific gates also remain open.
