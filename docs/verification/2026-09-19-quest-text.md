# Readable FTB quest text — September 19, 2026

Status: **implemented_unverified**, M0.3b.3.2.3c.2.1. This adds one-quest plain
text under D06, SPEC v0.2.8 and Forge capability minor 18. Partial
F01/F06/F16/N01/N04/N06, C09 and T01/T03/T06 advance; no aggregate gate closes.

## Delivered behavior

`mcgame quest-text --chapter CODE --quest CODE --after 0 --json` reaches the
native `quest_text` operation through the scoped broker. Codes are exactly
sixteen uppercase hexadecimal characters from the visible catalog. Generated
schemas, Python and TypeScript reject extra fields, other-team selectors,
invalid cursors and final-newline IDs before dispatch.

`GameQuestText` selects one visible quest within a visible chapter and checks
detail access before title/subtitle reads. The shared `NativeQuests` source
retains exact FTB artifact pins, editing disabled, verified own-team membership
and stable client/file/team/body context. The description reader is invoked
only after its separate native text-visibility rule succeeds. Locked text
returns an explicit false flag, empty lines and no cursor; an accessible
subtitle remains independent of description visibility. Unknown/hidden or
detail-locked targets reject the request.

Plain text retains ordinary localization and keybinding labels, with formatting
reduced to text. Native page breaks remain explicit entries. Image, interactive
and unknown components produce `unsupported` lines with no raw content. Rich
subtitles fail explicitly. Component traversal has depth/node/argument/sibling
bounds and rejects repeated component identities. No image is rendered or
texture bound by this adapter; actual parser/mod-hook behavior is unqualified.

The query is limited to 512 description lines, 32 lines/32 KiB per page,
1,024 Unicode code points/4 KiB per title/subtitle, 4,096 code points/16 KiB
per line, 2 MiB aggregate projected lines and a cooperative 100-ms timer.
That timer cannot preempt blocked source calls. Visibility and generation are
rechecked before delivery. Query/focus/content/source changes affect revision;
page cursor alone does not. The broker checks private body/connection identity
and omits it from public results, with existing lease and caller-scope checks.

Required task/reward definitions, dependency/link/guide/rich surfaces and
ordinary submissions/claims remain .3c.2.2/.2.3/.3. No quest progress mutation,
server/admin route, raw NBT, hidden graph or evaluator data was added.

## Source evidence

The exact FTB Quests/Library/Teams hashes are unchanged from the
[catalog report](2026-09-19-quest-catalog.md). Installed `javap -c -p` output
confirms the subtitle/description getters, native detail/text gates and parser
component behavior. `URLImageIcon` construction stores its URI; loading is
associated with texture binding, which this adapter does not call. The source
inspection is not a live network-isolation test.

The [upstream quest view](https://raw.githubusercontent.com/FTBTeam/FTB-Quests/1.19/main/common/src/main/java/dev/ftb/mods/ftbquests/gui/quests/ViewQuestPanel.java)
was cross-checked September 19: subtitle display precedes the separate
description visibility gate, and description page breaks are native content.
Installed bytes, rather than the moving branch, govern the implementation.

## Executed checks

Private bundle: `.strata/evidence/2026-09-19-quest-text-01/`, outside the
repository and gameplay workspaces. Logs, installed API/parser bytecode, JUnit
XML, source snapshots, artifact hashes and `verification.json` are retained.

| Procedure | Result |
|---|---|
| `gradlew.bat :forge1192-client:test :forge1192-client:build :forge1192-client:writeTestClasspath --no-daemon --console plain` | **220 Java pass**, no failures/errors/skips; build 27 s |
| `npm test`, explicit pinned Java/classpath and guardian Python | Final **119 Node pass**, no failures/skips; 45.935 s |
| `uv run --frozen pytest tests/test_native_game.py tests/test_contracts.py tests/test_records.py tests/test_native_game_jvm.py tests/test_machine_recipe_query.py tests/test_quest_catalog.py tests/test_quest_text.py -q`, explicit pinned Java/classpath | **167 Python pass**, no failures/skips; 23.36 s |
| Schema export, TypeScript generation/build, Ruff on changed Python | Pass |
| Tracked `git diff --check` and changed-document local-link check | Pass; line-ending warnings only |

Six new Java tests exercise visibility/detail/text reader canaries, subtitle
independence, rich-content disposition, ordered pagination/revisions, source
change, ambiguity, UTF-8/aggregate limits, invalid fields and timeout. Eighteen
Python cases and a Node HTTP case validate strict text responses, hidden-content
and unsupported-line rejection, and no invalid dispatch/replay. The real
JVM/CLI fixture tests the new route and private identity stripping. **All
game/FTB effects in these fixtures are synthetic.**

The first setup command used the wrong relative fixture path and stopped before
the build ran; it was corrected. The first Node suite had **118 pass / 1 fail**:
`quest-text` was missing from the CLI command allowlist. The allowlist and help
were corrected, and the final full Node run passed. Both Node logs are retained;
the failed attempt is not discarded or reported as a pass.

Built candidate SHA-256:
`04720ab93d81c0136d3a44e29b73c21948d48833a2e17b97ce89e39943e95079`.
It remains **uninstalled**. A second fresh read-only capture after verification confirmed that the E9E
client still awaits the operator's Windows Security choice; no new desktop input, game server/worker, model call,
soak, capacity run or experiment was started. Strata inference remains **$0
dispatched** against the authorized $10 ceiling.

## Remaining qualification

Native loaded reflection, parser/localization/rich-content behavior, UI hiding,
own-team changes, timing and actual isolation need authentic E9E evidence.
Compilation and synthetic fixtures cannot establish those properties. T03/G0
retain the actual Mineflayer/E9E handshake failure and the separate Forge
candidate's unqualified status. Other quest/machine adapters, complete pack
seals, native host/accounting/isolation, keybinding effects, capacity/soaks and
scientific gates remain open.
