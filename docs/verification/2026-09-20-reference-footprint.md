# Public cancellation-reference start footprint

M0.2k.2b; F06/F09, N01/N02/N04/N06; partial T03/T07 and G0 item 4.

The retained [restart pair 03](2026-09-20-forge-restart-staging.md) failed before
movement because its reference selector assumed a near-centered player. The
prior cancellation had stopped safely off-center. Native movement was never
dispatched, so that result cannot establish a native geometry failure.

`src/mcbench/reference_routes.py` extracts the fixed public-reference selector
and replaces that fixture assumption with stronger geometric evidence. For the
declared ordinary standing 0.6-wide/1.8-high player, it verifies observed full-cube
support and two air cells above every cell in the bounding rectangle swept from
the current footprint to the starting cell center. Edge and corner starts must
prove the adjacent support too. Unknown cells, slabs and obstructions reject.
Exact upper-edge contact is excluded with nextafter; tiny real overlap still
requires the adjacent cell. The native motor independently checks actual body
dimensions, collision shapes and live state before and during input.

This operator-reference utility has no game/world/file access or input authority.
It does not become an agent pathfinding tool. The same 640-cell quota, flat-start
condition, three-to-six cardinal steps, minimum two-block displacement, page
freshness rules and cancellation/guardian criteria remain. It neither invents
cells nor centers the player with an uncharged setup action.

Ten focused geometry checks pass in 0.10 s; targeted Ruff passes. They cover
centered/edge/corner/negative-coordinate starts, exact versus tiny boundary
overlap, missing support, unsupported floor shape, feet/head obstructions,
unchanged inputs and rejection of routes that are too short.

Read-only reconstruction of the actual retained public pages and final fresh
observation also passes: 384 delivered cells, two support cells, four cardinal
steps and 2.541177393 blocks endpoint displacement. The prior 1900-ms page and
1000-ms final-observation checks are preserved. This is authentic retained-data
planning evidence, not a new game action or cancellation pass. Its private
inspection remains beside the original failed report. Source SHA256:
`54a6f16e7955d9ac32488f4d2d459df6fcde0dc3776c0e3c5159c5e0b7ac0fc4`.

Next: apply this exact selector in a new prepared reference pair with the
unchanged native motor and 3 GiB resource profile. Preserve all old failures,
saved resources and costs. Successful live cancellation/staging/restart and
consistent shutdown remain unverified for this combined candidate.
