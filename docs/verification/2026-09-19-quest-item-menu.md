# Current FTB item-alternatives menu — September 19, 2026

Status: **implemented_unverified**, M0.3b.3.2.3c.2.2b.1. SPEC v0.2.10 and Forge
minor 20 declare this D06 candidate. F01/F06/F16/N01/N04/N06, C09 and partial
T01/T03/T06 advance; no aggregate gate closes. Choice/extension menus and all
ordinary quest actions retain their separate required children.

## Delivered behavior

`mcgame quest-menu --after 0 --json` observes the current exact FTB
`ValidItemsScreen`; it cannot open, scroll or act on a menu. `GameQuestMenu`
projects bounded visible items and controls. `NativeQuestItemMenu` obtains only
public widget/context fields and APIs from the three exact pinned FTB artifacts.
Strict Python/TypeScript/Java contracts, generated RPC schemas, scoped broker,
private native transport and CLI are connected end to end.

The current player's non-editing file/team, chapter/quest visibility and detail
access, task membership and active screen identity must remain valid. Context
menus, unknown wrapper/widget layouts, unexpected parent/children relations,
active render offsets, overlapping control/item panels and changed clipping
flags reject. Shift/Control/Alt must be released and advanced item tooltips off.
No private fields, raw quest predicates, server messages or UI callbacks are used.

Installed FTB Panel bytecode applies truncated negative scroll offsets only
temporarily while drawing and handling pointer state. Reading `getX/getY`
outside that interval would miss scrolling. The adapter computes the current
root/panel/item rectangles from public fields and scroll values, intersects
them with the panel/root/canvas viewport, and never changes offsets or hover.
An off-screen item is filtered before its stack, ID, name or tooltip is read.
Partially visible widgets are included only when their rectangle intersects
the viewport. The exact loaded clipping/hover behavior remains unverified.

Visible rows return native-order projected indices, item IDs, displayed counts,
names and normal plain/unsupported tooltip lines. Current chapter/quest/task
IDs and the menu title are included only after the visibility gates. Visible
Back/Submit controls expose their title, normal tooltip and displayed enabled
state. Submit's native disabled-widget check is preserved as display data;
this does not authorize an action or prove server eligibility/completion.

Source, observed screen replacement, layout, context and projected content bind
generation/revision. Source/context/screen/layout are rechecked before delivery.
Private body/connection identity is checked at the broker and removed from the
public result; raw screen identity and geometry never leave the native source.
The broker checks the lease before/after the query and journals private evidence.
Stock Mineflayer has no menu provider and rejects the scoped method.

Bounds: 512 inspected item widgets, 32 rows/32 KiB per page, 64 tooltip lines and
16 KiB per item, two controls/8 KiB total, 4 MiB aggregate item projection and a
cooperative 100-ms deadline. Cursors enumerate only visible projected rows.
Unknown fields, wrong query echo, IDs, roles, indices, counts, Unicode, byte
bounds and cursor identity reject. A read never sends mutation authority.

## Executed verification

Private bundle: `.strata/evidence/2026-09-19-quest-item-menu-01/`, outside the
repository/gameplay workspaces. It retains installed UI bytecode, logs, source
snapshots, JUnit XML, artifact hashes and `verification.json`.

| Procedure | Result |
|---|---|
| Pinned Java/external Library; `gradlew.bat :forge1192-client:test :forge1192-client:build :forge1192-client:writeTestClasspath --no-daemon --console plain` | **236 Java pass**, zero failures/errors/skips; final build 26 s |
| `npm test`, pinned Java/classpath and guardian Python | **121 Node pass**, zero failures/skips; 46.022 s |
| Selected native/contracts/records/JVM/recipe/catalog/text/components/menu pytest suites, pinned Java/classpath | **212 Python pass**, zero failures/skips; 23.72 s |
| Four quest-focused Python suites and changed-Python Ruff | **80 pass**, Ruff pass |
| Schema export and TypeScript generation/build | Pass after correcting an out-of-scope validator reference |
| Final focused menu HTTP/scoped CLI/JVM checks after native guard/context and transport whitespace review | **2 Node / 1 Python pass**, no failures/skips |
| Final changed-Python Ruff, tracked whitespace and changed-document local links | Pass; only Git line-ending warnings |

Eight new Java tests exercise hidden/off-screen reader canaries, disabled
controls, screen/source/layout/context changes, native scroll truncation and
clipping boundaries, paging/order/revisions, candidate/tooltip/byte limits,
ambiguous roles, query validation and timeouts. Twenty-four new Python cases
and a Node HTTP case exercise strict projection and no-retry behavior. Actual
JVM/Python and scoped Node CLI routes use synthetic menu sources and verify
identity stripping and wrong-scope rejection. **FTB/game effects are synthetic.**

The first standalone TypeScript build found an item-ID helper outside its scope;
the menu validator now owns its explicit check. The first Node suite attempt
stopped at compilation because the new fixture used `endpoint` instead of the
real host/port connection contract. It was corrected before the passing run;
the failed attempt is retained. Final Java review additionally rejects advanced
tooltip mode, overlapping control/item panels and null source contexts; the
full Java suite passed again after those changes. Gradle/Forge deprecation
warnings remain recorded.

Final JAR SHA-256:
`2e8c620529c02c15d8378f3da2c6faf9d0f5dd183dab3b1732fc4634e335fae8`.
It is **uninstalled**. No new game server/worker, inference, soak, capacity test
or study started; Strata inference remains **$0 dispatched**. A fresh read-only
desktop capture still shows Windows Security over E9E; no input was sent and
the existing operator handoff remains pending.

The final JAR contains no bundled `dev/ftb/` classes. The exact installed Library
remains an external compile-only prerequisite, as documented in the build runbook.

## Remaining work

Qualify the exact loaded menu, source/team transitions, native tooltip callbacks,
viewport/scroll/GUI geometry, modifier/options handling and blocking-call timing.
Complete choice/extension menus, ordinary opening/navigation/submission/claim
actions with resource/feedback/cancellation semantics, and full rich content.
Keybinding effects, authentic machine/recipe/reference checks, complete pack
locks, native host/accounting/isolation, capacity, soaks and scientific gates
remain required. T03/G0 retain the failed Mineflayer/E9E path and independently
unqualified Forge fallback; this report does not change those results.
