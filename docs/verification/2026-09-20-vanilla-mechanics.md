# Authentic vanilla mechanics continuation

M0.2i/M0.2j; F01/F06/F09/F16, N01/N02/N03/N04; T01/T03/T07,
G0 item 3. This is operator-driven integration evidence, not an isolated
gameplay-agent run, scientific sample or complete T03/G0 pass.

## Implemented behavior

- Recipe execution binds the selected declaration and its authorization;
  unrelated recipe unlocks no longer interrupt a partial craft. Revocation,
  revoke/regrant, reset and declaration replacement still invalidate it.
- Mineflayer minor 9 supports registry-known fresh damageable outputs carrying
  exactly integer `Damage=0`, count one. Ingredients remain plain; custom tags,
  names, enchantments, nonzero damage and remainders remain unsupported. The
  motor checks exact server output metadata before pickup, on the cursor and
  at its reserved destination, plus existing tagged stacks and item totals.
- Terminal connection/authentication failure before first spawn fences the
  epoch with a sanitized supervisor reason. A pending connection remains
  pending. Cache locks are never automatically removed.

TypeScript build passes. Nine focused recipe tests pass; four focused
connection/fencing tests pass, including the actual pinned backend against a
synthetic held cache lock without provider traffic. These checks are separate
from the real game evidence below.

## Authentic operations and independent saved references

Official vanilla 1.19.2 server JAR
`b26727069ef5f61c704add9a378ac90e3d271fd7876c0bd3dcfbe9fd0bec4d96`,
Java 17.0.20.1+1, Node 24.19.0, Mineflayer 4.39.0 and protocol 1.68.0.
An external copy preserves the original instance. Nine recorded server-only
setup commands supplied two oak logs, an empty chest, a crafting table and
flat ground; these are fixture grants. Setup stopped in 24.625 s. All gameplay
used the scoped public HTTP API consumed by `mcgame`, with Microsoft online
authentication, finite worker limits and no shared-desktop input or inference.

| Attempt | Actual result | Retained costs |
|---|---|---|
| 01 | Readiness checked before spawn; zero actions, forced worker cleanup. Its log-drain completeness claim is superseded by the retained audit. | 20.203 s |
| 02 | Connection timeout; the prior interrupted authentication left a lock. Zero actions. | 35.110 s |
| 03 | Joined; mined both logs. Private checker omitted movement tolerance and failed schema validation before dispatch. Saved blocks are air and player gained exactly two logs. | 2 primitives, 134.016 s |
| 04 | Walked, deposited/retrieved both logs through the chest, crafted eight planks and four sticks. Saved player: six planks, four sticks, original seed; chest empty. Pickaxe was unlocked but unsupported under the previous NBT restriction. No pickaxe action dispatched. | 11 actions, 59 primitives, 133.719 s |
| 05 | With fresh-tool support, opened the table, crafted one wooden pickaxe and closed the menu. Independent stopped-save audit passes exact item/metadata deltas. | 3 actions, 37 primitives, 74.157 s |

The stale lock's PID 42696 was independently absent from Win32 process inventory
before the operator retained and retired that exact lock. Cached authentication
then passed in 1358.3601 ms. No credentials were printed or reset.

Attempt 05's saved player contains exactly **one wooden pickaxe with Damage=0,
three oak planks, two sticks and the original wheat seed**. The source chest is
empty, both mined blocks remain air, and the crafting table remains present.
Player continuity matches attempt 04's final save byte for byte before joining.
All three final receipts confirm release, with no resync requirement; journal
primitive totals match the receipts. All five attempts retain **98 primitives
and 397.205 s**, excluding setup. No conversion or mining action was replayed,
and no resources were replenished between attempts.

Raw evidence, configurations, journals and frozen selected region/player files
remain outside the public repository under private evidence
`2026-09-20-vanilla-mechanics-01`. Authoritative narrow reports are
`operation-03/mining-audit.json`, `operation-04/conversion-audit.json`, and
`operation-05/tool-craft-audit.json`; the last has a reproducible private audit
script. Original failed checker reports remain. Attempt 04's checker labels
the unsupported recipe `RECIPE_NOT_UNLOCKED`; its actual public recipe row
shows it was unlocked but unsupported.

## Remaining acceptance work

This closes the listed vanilla mechanics sequence's narrow authentic evidence
gap, not M0. An unrelated wheat-seed drop near the fixture lacks a frozen
pre-join entity baseline; the initial broad resource reconciliation failed and
no complete world-resource conservation claim is made. Full action coverage,
reconnect/resynchronization, isolation, private causal scoring, complete host
integration and locks remain open. E9E expert crafting remains a separate
failure. Aggregate T03 is incomplete, T07/G0 remain fail, and all later gates
and conditional extensions remain represented in the ledger.
