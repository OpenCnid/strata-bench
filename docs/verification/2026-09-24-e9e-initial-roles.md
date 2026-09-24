# Initial paired E9E roles

M0.3a.4e is **verified** for independent initial client/server roles with complete per-file
copy plans and retained component notices. The actual audit passes **22/22**;
**58 distinct focused tests** pass. Both roles pass all eight initial expert
setup-file checks. E9E deliberately remains ACQUIRED: these are initial roles,
not qualified post-startup effective settings or a sealed launch profile.

| Role | Files | Bytes |
|---|---:|---:|
| Client | 13,628 | 1,208,220,163 |
| Server | 8,819 | 650,842,622 |
| Total | 22,447 | 1,859,062,785 |

Coverage: M0.3a.4/.4e; F01/F05/F16, N01/N04/N06/N08, C03/C04/C24,
partial T01/T02/T13 and G0 item 2. M0 remains in_progress and G0 fail.
D14 isolation deferral and the M1–M7 roadmap remain unchanged.

The [operator composer](../../src/mcbench/role_composition.py) and
[provisioning consumer](../../src/mcbench/provisioning.py) validate both roles
before writing either one. Inputs declare exact source paths and existing typed
FileEntry records, including origin, role, layer and notice references. Required
source/notice/exclusion reports resolve in the original acquisition namespace.
The implementation checks paths, links, hardlinks, duplicate/colliding files,
file-as-parent conflicts, quotas and every source digest; independently copies
into fresh output; rechecks sources and complete output inventories; retains
declared empty directories; and inspects initial expert setup. A mismatch
retains partial output without a successful preparation receipt. Existing
destinations cannot replay. The composer does not certify arbitrary operator
provenance assertions, licenses, effective settings or isolation.

Actual roles combine the previously verified vendor content, client software,
server library subset plus separately reproduced SRG, and 316 sealed Java files
per role. Client harness JARs and options match the retained successful
`protected-craft-heap6-05` profile. The server telemetry JAR matches the retained
`e9e-role-live-01` profile. This reuses exact retained artifacts; it does not
claim a new build from current HEAD. The server retains its authorized EULA and
development properties. Explicit initial `mode.json` selects expert mode,
matching the unchanged publisher default. No configs are migrated or silently
normalized. Played worlds, player data, logs, account caches and admin lists
are excluded. Five historical strict effective-file failures remain failures.

The private notice index retains 343 component records, 709 selected embedded
documents and 37 inherited notice records. Of those 343 components, 235 expose
explicit mod license values; other absent declarations remain explicit. Exact
artifact bytes preserve any other embedded material. Original sealed vanilla
notices retain their namespace/ref and full record through explicit wrappers.
These records document existing authorized private use and observed notices;
they assert neither a blanket license certificate nor binary redistribution
authority. Both distribution ZIPs were independently inspected by content:
neither contains a selected license/notice/POM/loader metadata member. This
supplements the preparation script's suffix-based handling of CAS filenames.

| Evidence | SHA-256 / CAS digest |
|---|---|
| Composition plan | `b3c3a50472ed88ea47f12520b333498ae17d431af88f7abde59c25143fc413f4` |
| Actual role preparation | `6d741d2274414e72ddf85c2538dc20bc7306a3f3b07190ec1fe3bcef71888a68` |
| Independent audit: 22/22 | `1d28cca88e3ed6d707a23a81e2963711f33d248c9fb1d68de6f491aa10d91489` |
| Control seal: 1,070 files / 83,766,960 bytes | `3cf55a944bc67d1892629d1db2b9963eafb983667814b7f9ff29c99361a6888c` |
| Client archive 01 seal | `4755ffdb8058cd1d95769487aeef73953f3011c9c175187a3addec09ee21fe46` |
| Client archive 02 seal | `39b899a9fee8fb8565d6198f9f72f98862113d7c4840573619a687b7f64f7e7f` |
| Client archive 03 seal | `8b641f63cec64f272cb276dbda29292eab15802a1242f98886e98b88f545a47f` |
| Client archive 04 seal | `f34f71ee902dcacfd3d1f77d9ffdb043a8dff3d0e124c553ae8308068f618fca` |
| Server archive 01 seal | `38fbd8811070c746ba2d63bee54146bce0095eddec68e05b043311b433562b97` |
| Server archive 02 seal | `35722a47396ad9f7a9f7719100873cf4b2e71a9123fafe9a67b5fe29c421941f` |

Private `2026-09-24-e9e-roles-01` retains source, exact copy plan, notice index,
newly imported notice/provenance artifacts, original authority digests and both
prepared roles. The actual command was `pack prepare-e9e-roles` against the
original `e9e-1270-20260918` request, with a fresh destination and a 600-second
outer bound. It completed once, normally. No Minecraft, mapping processor,
installer, model call or desktop input executed.

All 22,447 prepared files have full archive member/hash readback through six
bounded role bundles. The separate control bundle binds their seals and every
prepared directory, including empty vendor/native directories. No artifact or
bundle limit was raised; the original raw preparation is retained as well.

Executed `python -X utf8 -m pytest tests/test_role_composition.py tests/test_provisioning.py tests/test_pack_modes.py -q`:
57 passed in 5.90 seconds, with two existing Typer/Click deprecations. One
additional mid-copy source-change case brings the final composer selection to
10 passed in 0.44 seconds, for **58 distinct passing cases**. Tests cover both
role preflight, missing/foreign notice refs, acquisition/role mismatch, duplicate
and parent-path collisions, played-world rejection, failed initial setup,
mid-copy changes, partial retention and refusal to reuse output. Ruff passes.
Synthetic setup fixtures are separate from the actual eight checks per role.

The audit independently rehashes all prepared files, checks Java and both SRG
digests, initial expert setup, directory retention, excluded state, exact
executed source and conservation of authority. All 37 non-artifact tables and
every old artifact/event row remain unchanged. Exactly 1,044 declared notice,
provenance and preparation artifacts/events append. E9E stays ACQUIRED and
exposure stays **$2.831942/$10**, with all old holds retained.

Next create a fresh controlled instance from these initial roles and qualify
expert initialization/cold restart, generated effective configuration and the
resulting launch profile. Only then submit the complete effective inventory to
existing verify/seal admission. Preserve the successful initial preparation;
do not rebuild unchanged software or repeat the verified LLM/Mineflayer pilot.
Remaining root/helper, scorer, recovery and authoritative clock/cost joins keep
the six-item G0 gate open.
