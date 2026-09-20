# E9E 1.27.0 expert-mode verification

Operator-only. Keep these checks and their evidence outside gameplay workspaces.

The official 1.27.0 distributions contain `config/configswapper.json` with
`defaultmode: expert` and 260 expert overlay files. ConfigSwapper 3.2 initializes
the root `mode.json` from that default when its selected mode is absent/invalid.
It applies overlays in its constructor, after loading, and after server startup.
See the [reviewed source revision](https://github.com/Darkere/ConfigSwapper/tree/21ba0bfedeabcc54dec93f304e69c7e61b683330)
and [official mode-file documentation](https://www.curseforge.com/minecraft/mc-mods/config-swapper).
The JAR's 3.2 version and build timestamp agree with that source revision; this is
source correspondence evidence, not a reproducible-build attestation.

For a dedicated, stopped installation:

```powershell
uv run --frozen mcbench pack inspect-expert-mode C:\absolute\instance --role server
```

The command checks exact release fingerprints and the complete overlay inventory.
An absent `mode.json` is allowed only for setup inspection and explicitly reports
`initialized: false`. An existing normal/unknown mode fails. The command never
edits mode/config files, accepts terms, executes scripts, or starts a world.

Before baseline world creation, explicitly establish `mode: expert` through the
release-supported root `mode.json` configuration. Preserve provenance for that
operator setup. Do not rely on mod constructor ordering against KubeJS's normal
fallback, and never change mode during scored play. Bootstrap worlds are disposable
development state, not baseline or probe worlds.

After initialization, a clean stop and a cold restart, inspect the exact stopped
world's effective files:

```powershell
uv run --frozen mcbench pack inspect-expert-mode C:\absolute\instance --role server --effective --world world
```

This checks all TOML overlay values (including types) and exact replacement bytes
for other formats. World-specific `serverconfig` is resolved beneath `--world`.
Missing target files stay failures; review and pin any role-specific exclusions
instead of assuming they are irrelevant. Passing this inspection proves file
state only, and leaves the aggregate T02/G0 results `not_run`.

Private runtime and independent player/reference evidence must additionally
establish loaded expert config; furnace recipe
`enigmatica:expert/minecraft/shaped/furnace` with andesite/polished andesite;
expert quest `2CCCDD05AED3153F` complete and normal quest `0E45018D600614BA` reset
for the correct player/team; and persistence across cold restart. Sources are the
exact pinned KubeJS recipe/login scripts and hidden quest definitions. These
expectations are not runtime observations, and do not certify any machine or
Mineflayer mechanic.
