# Opening-bound choice-reward menus

2026-09-19. Operator-only. M0.3b.3.2.3c.2.2b.2a and the choice-opening portion of
.3.2b.3; F01/F06/F09/F16, N01/N02/N04/N05/N06, C09/C15;
partial T01/T03/T06/T07/T12. No aggregate gate closes.

The candidate opens an eligible visible choice-reward button with `quest_reward/open`
and projects the resulting current choice menu through `quest-menu`. SPEC v0.2.15 /
Forge minor 25 / native eighteen-action policy pins
`ftb-visible-choice-reward-menu-open/1` and
`ftb-current-item-choice-clipped-pages32/3`. Stock Mineflayer rejects the action.

## Native route and boundaries

[GameQuestRewardOpen](../../java/forge1192-client/src/main/java/io/github/opencnid/strata/client/GameQuestRewardOpen.java)
requires a current rewards components page with `can_claim`, current selected
chapter/quest, source/screen generations and revision. The exact button/reward/layout
are checked again inside charged dispatch. One ordinary LEFT callback opens the
menu, confirmed immediately and next tick. Deduplication, cancellation and uncertain
outcome fencing retain effects and costs without replay.

[NativeQuestRewardOpen](../../java/forge1192-client/src/main/java/io/github/opencnid/strata/client/NativeQuestRewardOpen.java)
requires exact ChoiceReward and RewardButton classes, visible/enabled clipped widget
ancestry, own-player eligibility, own-team non-editing source, released inputs and
modifiers, idle survival context and empty carried/crafting/result state. It checks
only the table's count (maximum 512) after eligible visible selection, before the
ordinary callback allocates buttons; it does not read or return table entries.
Other reward callback types reject. The exact callback opens a choice screen and
does not send a claim; selection/claim is a different callback and remains disabled.

[NativeQuestChoiceMenu](../../java/forge1192-client/src/main/java/io/github/opencnid/strata/client/NativeQuestChoiceMenu.java)
retains parent/reward/source identity from that opening. This is ephemeral private
context, not a client-supplied selector, raw-table lookup or private-field reflection.
Screen/source changes invalidate it; manually opened unbound choice screens reject.
Each read rechecks membership, own-team/source identity, visibility, claim eligibility,
actual parent book, current quest, and the exact public widget tree. Identifiers and
display content are read after visibility/eligibility checks. Unknown/search/offset/
overlapping contexts reject. The exact panel and scrollbar are found through public
children; their private fields are not inspected.

The shared [menu projector](../../java/forge1192-client/src/main/java/io/github/opencnid/strata/client/GameQuestMenu.java)
supports a distinct `reward_choices` response: chapter/quest/reward context, visible
ordinal/title/enabled/normal-tooltip rows and empty controls. Existing item rows stay
unchanged. Hidden/off-screen widgets are never asked for display content. Limits
remain 512 inspected entries, 32 rows/32 KiB per page, 16 KiB per row, 64 tooltip
lines and cooperative 100 ms. No weights, raw table indexes, commands, NBT or raw
definitions are exported. A visible ordinal grants no selection/claim authority.
Item Back/wheel actions continue to reject choice screens.

Exact installed FTB bytecode confirms the native opening permission, private choice
parent, list-order button creation, public title/tooltip route, and separate
claim-and-close callback. FTB Library confirms the two-child panel/scrollbar layout
and clipping defaults. The same three exact artifact hashes are required. Source
inspection and compilation do not establish loaded-mod/UI behavior.

## Verification

Windows, Python 3.12.14, Node 24.19.0, JDK 17.0.20.1+1, Forge 43.4.23 compile
target and exact installed FTB Library compile-only dependency.

- Full Java build/tests: 285 pass, zero failures/errors/skips. Final build 25 s;
  earlier successful builds are retained. Final pass includes the stricter
  visibility-before-ID read ordering and strengthened binding checks.
- Fourteen Python suites covering native/JVM/contracts/records/machine query and
  nine quest suites: 254 pass, zero skips, 34.70 s.
- Full Node suite with explicit JVM/classpath and Windows guardian Python:
  130 pass, zero failures/skips, 54.367 s. The scoped CLI opens the synthetic
  eligible reward, observes its choice shape and verifies deduplicated charges.
  The prior fixture's two-second lease renewal remains in place.
- Changed-Python Ruff, schema export, TypeScript generation/build and tracked
  `git diff --check` pass (CRLF warnings only).

Eight new opening tests cover one-shot behavior, ineligible/off-page/hidden/stale
selection, replaced native target/layout/book, refusal/post-effect change, strict
requests, durable deduplication/reopen and cancellation/unknown outcomes. Four new
menu/binding tests cover hidden-reader rejection, separate choice shape, ordering/
paging/revisions, mixed/control/raw/rich/size rejection, and binding replacement or
source expiry. Python and Node validate strict cross-language shapes and reject
claim/table selectors. Real JVM/HTTP and CLI transports use **synthetic game/UI
authority**; this is not authentic E9E qualification.

Candidate JAR SHA-256:
`43ab8799484bc8ce4b2737ab318185102a08b98d18bf9f2f1fc256d127016e74`.
Built, **uninstalled**. Private logs/bytecode/JUnit/source hashes:
`C:\Users\Darian\.strata\evidence\2026-09-19-quest-choice-01`.

## Remaining work

Exact choice opening/projection is implemented but unverified. Choice Back/scroll,
other extensions/task/JEI/UI contexts, occupied crafting-state conservation,
choice selection/claims with server-resource feedback, rich displays and full
callback/viewport/reference/timing/isolation qualification remain required.
T03/G0 retain the Mineflayer/E9E handshake failure; all aggregate gates are open.

The earlier fresh desktop capture in this task showed Windows Security over E9E;
operator handling remains pending. No desktop input or new real client/server/
worker, inference, soak, capacity test or study was started. Strata inference
remains $0 dispatched; goal active, M7 conditional.
