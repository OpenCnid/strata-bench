# Authentic E9E connection and read-only observations — September 19, 2026

Operator-only; exclude this report and private evidence from gameplay contexts.

The separately identified Forge client joined the official E9E 1.27.0 server
and served authentic read-only observations, quest content and selected Thermal
recipe data. This is **partial T03 evidence**, not action, complete pack or G0
qualification. The failed Mineflayer/E9E handshake remains unchanged.

Coverage: M0.3b observation/transport and .3.2 recipe/quest children; F01/F05/F06/
F09/F16, N01/N04/N06; partial T01/T02/T03/T06/T07, C09/C15. Render-page hooks,
ordinary actions, machines, input cleanup, reference parity and isolation remain
unqualified. No inference or campaign was admitted.

## Exact deployment and procedure

- Dedicated official CurseForge E9E 1.27.0, Minecraft 1.19.2, Forge 43.4.23;
  Temurin 17.0.20.1+1, client heap 4096 MiB. Server uses the previously reviewed
  official serverstarter 2.4.0 launch and accepted EULA, online authentication,
  loopback address and port 25566. No alternate launcher or offline account route.
- The user completed the Windows Security prompt. A fresh E9E capture confirmed
  its absence. The old read-only client was closed; its JAR and log were copied
  to private evidence before deploying the tested minor-30 extension.
- Candidate SHA-256:
  `f10e7ad6ddbbf48df176183cc4e0dc60891a50d2528858ceb452b2c96a6aa625`.
  Previous JAR:
  `c2218c6c9ae2e1e4a7e6f216d9fd16f084404d38bcebf0f47ccca17a24f462ce`.
  Its [350 Java / 301 Python / 134 Node evidence](2026-09-19-jei-page-controls.md)
  remains synthetic game/render validation, distinct from this run.
- CurseForge regenerated the launcher profile without the pinned Java path or
  bridge property. With the launcher closed, restored those dedicated-profile
  settings. A direct launcher attempt used its default context and showed login;
  no authentication was automated. Relaunched using the work directory observed
  on CurseForge's actual launcher process, preserving the existing signed-in
  context. The ordinary modded-profile Play confirmation was used without changing
  its warning preference. These interventions are retained, not a sealed launch.
- Only `strata.gameBridgeDirectory` was enabled. No `game-authority.json`, native
  mutation lane, worker grant, guardian or inference dispatch was created.
  The authenticated descriptor remains private and is excluded from reports.
- Started the existing bounded server tool with a reviewed 600-second plan;
  connected through the client's ordinary multiplayer Direct Connection UI.

## Results

Executed `tools/check_forge_observations.py` against the actual running client:

| Phase | Result | Evidence |
|---|---|---|
| Before join | pass, 6 assertions | Capabilities; no action authority; unsupported lane; disconnected identity/observation errors |
| Transport negatives | pass, 10 assertions | Authentication, browser Origin, foreign Host, session, deadline and schema rejection |
| Connected world | pass, 2,745 assertions | 20 pages, 2,489 returned block records and zero entities; stable scene/core/body identity, bounds, monotonic age, distinct fresh capture, unique page/block IDs and stale-cursor rejection |
| After server stop | pass, 6 assertions | Authority remains read-only; identity and observation return disconnected errors |

The assertion count includes per-record structural checks. It does not prove that
every block is visually accessible or that hidden-state filtering passes its
complete reference/negative suite. Native client-thread reads and strict Python
decoding were exercised; a production scoped worker or model host was not.

Two additional private operator scripts exercised only existing read operations:

- Initial chapter catalog returned 20 entries. Three returned chapter IDs led
  to quest pages of 5, 23 and 32 rows, then one detail-visible quest from each.
  Their text pages returned 9, 3 and 3 lines; task/reward components decoded
  successfully. These 13 calls do not prove complete rich content, team/hidden
  cases, callbacks, claims or UI parity.
- Focused Thermal furnace query for iron returned the expert recipe
  `enigmatica:expert/enigmatica/blasting/thermal_smelting/iron_ingot_from_dust`,
  with five visible dust alternatives and 4,000 RF. The crucible lava query
  returned five recipes with amounts and energy. These are discovery data,
  not machine execution, resource conservation or rendered-reference proof.
- Unlocked recipes and a crafting-category furnace focus both returned empty
  pages. No successful craft or recipe completeness is inferred from emptiness.
- `recipe_page` without a bound task-opened screen rejected with
  `GAME_RECIPE_RENDER_UNAVAILABLE`. This supports the negative precondition only.
  Startup and successful JEI runtime registration cannot verify all six Mixins,
  completed frame capture, actual headers/buttons/slots or final overlay parity.

The server saved all dimensions and stopped normally on the operator stop file:
**532.875 s**, exit 0, no forced termination, logs complete. This was a bounded
development check, not a soak. The client remains read-only and disconnected.
Startup logs retain pack warnings and a version-check TLS certificate error;
no certificate validation was bypassed.

An optional UI reference attempt encountered an input-state change, then the
computer-use helper reported a stop. Desktop input ceased. The helper's claimed
physical-key cause was not independently verified and is not attributed to the
user. No further UI action or forced client shutdown was used to bypass it.

## Evidence and remaining work

Private deployment receipts/backups, reviewed server plan/results/logs,
observation checker sources/results, operator discovery scripts/results and
client logs are retained under:
`C:\Users\Darian\.strata\evidence\2026-09-19-jei-live-01`.
The bridge credential directory and launcher account/config backups must never
be published or mounted into gameplay contexts. Public report contains neither.

Next: prepare a fresh, explicitly bounded native authority and independent
Windows guardian, restart/rejoin the dedicated client, then run ordinary actions
through the scoped worker/CLI with real cancellation and charged evidence. Bind
task opening to recipe-page rendering and compare actual UI; retain all remaining
expert recipes/machines, input/keybinding, privacy, host, cost and reliability
gates. M0–M6 and the long-horizon goal remain open; M7 stays conditional.
