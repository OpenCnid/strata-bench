# Stopped vanilla instance capture

September 21, 2026. Operator-only. M0.1d.4; partial F01/F03/F04/F09/F11/F16,
N01/N02/N04/N06/N08, C04/C06/C12/C16/C17/C20, T01/T03/T06/T07/T12/T13
and G0 items 1/4/6. Source/process verification; authentic changed-profile
integration remains pending.

The existing [development server](../../tools/development_server.py) has a
separate `strata/DevelopmentServer/2` profile adding
`persistence_policy: vanilla1192-stopped-instance/1`. It pins the inspected
vanilla 1.19.2 bundler and inner server, fixed 1–2 GiB/nogui arguments and
normal world name, retaining online loopback and disabling RCON/command blocks.
No password, caller-defined command or alternate pack is accepted by this profile.

[VanillaPersistence](../../src/mcbench/vanilla_persistence.py) holds immutable
server inputs with existing Windows deny-write file leases throughout execution.
The changed runner explicitly uses the base Python bootstrap, tracks owned
processes during execution and retains the Job and process handles through
capture. Before copying, zero active/forced-terminated processes and exact
lifetime/held/signaled equality are required. A root exit alone cannot pass.
Normal stop and critical-log checks remain prerequisites. v1 behavior and its
unqualified evidence remain available.

After stop, the capture leases all actual files and copies every classified
world file and mutable root configuration into a fresh private directory.
Empty world directories are retained. Distribution inputs, diagnostic logs and
the transient session lock receive explicit hashed dispositions; none silently
disappears. The snapshot excludes those files from mutable restoration. Unknown
external roots, files, secrets, hardlinks/reparse points, incomplete layouts or
changed pinned inputs reject. Size/count and disk reserve bounds remain finite.

The manifest is written last. Partial destinations remain occupied, with no
automatic overwrite or replay. `verify_snapshot` requires the original manifest
digest from outside the directory, then verifies its supported scope, exact
state bytes, file/directory membership and stop-record consistency. It cannot
prove an arbitrary caller's historical stop assertion. Runtime capture obtains
that observation directly from the still-held owned Job. Capture downtime is
recorded separately from the stopped-server interval.

Every snapshot keeps clean-save, full-checkpoint, writer-custody and dispatch
qualification false. Termination and file capture are necessary evidence, not
proof of the game's entire persistence contract or exclusion of every writer.
Nothing is exposed through gameplay packages/tools or used to refund costs.

Actual verification, Windows/Python 3.12.14:

- Initial persistence plus server-health selection: 40 pass/one test failure,
  10.56 s. The owned Python fixture retained three processes, while the test
  incorrectly assumed two. The corrected assertion checks the actual complete
  held/signaled history; no process-count requirement was relaxed.
- Corrected persistence selection: 20 pass, 4.64 s.
- Final persistence/profile/publication-fault, server-health, gameplay-package
  and canonical-record selection: **80 pass**, 12.25 s; full Ruff passes.
  Coverage includes actual file write denial, live/incomplete/forced stop
  rejection, an owned Python process ending before capture, unknown/secret/
  aliased input rejection, byte/inventory corruption, new files during capture,
  disk failure before manifest publication and fixed-profile negative cases.
  Synthetic saves and pinned test substitutions are explicitly labeled.

Read-only inspection of the existing stopped `vanilla-native-03` instance
accounts for all **68 files**: 28 mutable state, 32 immutable inputs, seven
diagnostic logs and one session lock. Two full inventories are identical.
Private `2026-09-21-vanilla-persistence-source-01/existing-layout.json` SHA-256:
`b6f4b08059c3970a9d29b242076e66e8e99cd4b1f1f3a4797153430252afe266`.
No new snapshot, process-termination reconstruction, game/model run or desktop
input occurred. No Java process remains. This is layout evidence only.

M0.1d.4 is implemented but unverified authentically. Next preregister native
retention before the changed connected trial, then exercise the combined
stopped-game/native component and fresh-epoch assertions. Old runs without
retention policy or a held capture boundary cannot acquire those facts afterward.
Preserve all prior shutdown, effective-file, Mineflayer/E9E, scoring/isolation
and accounting failures. M0 remains incomplete; G0 fails.
