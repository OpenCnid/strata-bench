# Complete restored-set publication and verification

September 21, 2026. Operator-only. M0.1d.3; partial F03/F04/F09/F11/F16,
N01/N02/N04/N06/N08, C06/C12/C16/C17/C20, T01/T06/T07/T12/T13 and G0
items 1/4/6. Implementation and synthetic/recorded-native evidence only.

[Checkpoints](../../src/mcbench/checkpoints.py) now publishes a durable
`RestoredCheckpoint/2` receipt alongside the complete private set. Its inventory
is derived from the committed checkpoint and native retention records, including
world/external state, all roster members, workspace/skills, backend/keymap/runtime
records and active/candidate provenance. A destination receipt cannot supply its
own expected inventory. Existing v1 outputs remain historical unregistered data.

The new verifier requires the exact registered directory, checkpoint and epoch,
then checks current campaign/configuration, native source, every file's size and
hash, exact directory membership, and absence of hardlinks/reparse points.
Open-handle metadata is checked against path metadata. Unknown extra files and
empty directories reject, as do mixed, stale, missing or altered components.
All costs and unresolved holds remain outside the restored set.

The directory is renamed before the database publication commits. An interrupted
publication leaves occupied evidence without a restoration record; verification
and overwrite reject. A copied receipt cannot register another directory. The
verifier emits no accounting/event changes or gameplay data. This is a
point-in-time check, not a guarantee against later writes or a game launch grant.

The [operator command](../../tools/checkpoint_set.py) obtains configuration from
the durable campaign. It accepts no caller-provided replacement configuration:

```text
python tools/checkpoint_set.py --materialize --database <private-controller.sqlite> --objects <private-CAS> --checkpoint <id> --epoch <new-epoch> --directory <new-private-directory>
python tools/checkpoint_set.py --verify --database <private-controller.sqlite> --objects <private-CAS> --checkpoint <id> --epoch <new-epoch> --directory <registered-directory>
```

Run with `PYTHONPATH=src;evaluator/src`. Neither command launches Minecraft or
Codex, grants capabilities, resets budgets or qualifies a confirmatory rollback.
The output keeps `dispatch_authorized: false` and
`requires_restore_assertions: true`.

Verification on Windows/Python 3.12.14:

- Initial checkpoint regression selection: 36 pass/eight failures, 24.43 s.
  Windows cached DirEntry metadata omits link/inode counts; querying actual path
  metadata corrects the implementation while retaining hardlink rejection.
  All four arm materializations then pass, 7.69 s.
- Restored-set, native checkpoint, general checkpoint and native activation
  selection: **104 pass**, 195.10 s. Initial fixture-import Ruff findings were
  corrected with explicit fixture aliases.
- Additional fresh operator-process verification, before/after-rename process
  exits, and typed epoch checks: **four pass**, 12.75 s (three new cases plus
  one expanded case). **107 distinct cases** across the final selections.
  Synthetic world data and injected process loss are explicitly labeled.
- After making child-process import paths explicit, all three fresh-process
  cases pass again, 14.46 s. Gameplay package and canonical records: 29 pass,
  1.08 s; full Ruff and whitespace checks pass. Source audit preserves all 312
  prior milestone IDs, adds M0.1d.3, keeps the prior append-only log and SPEC
  sections 3/16–19 unchanged, and resolves 1,147 local links. No sensitive
  source artifacts or high-confidence secret patterns were found.

An offline derived copy of the existing actual native activation checkpoint
passes **17/17 audit checks**. Its sealed source is
`2026-09-21-native-activation-exec-04`, manifest SHA-256
`417b25d6feb1959591ddcda4e81fda7269f0bf336fdd717d97d3199bf25f7ce9`.
All 103 selected database/CAS source files verify unchanged before and after.
New materialization at epoch 3 retains both active skill support and private
candidate provenance; a fresh operator process verifies it. Copied receipt,
legacy output and later-knowledge controls reject. Account limits and every
ledger row remain unchanged: 10 historical calls, 100 input/40 output tokens and
140 synthetic fixture units. No new native/model/game call occurred.

The private audit is `2026-09-21-restored-set-01/audit.json`, SHA-256
`4b6e6dce0e2a28820b5ee5084d905f6609c5a0e6de0c67f649a32f6c2d6889e2`.
Its native history is authentic CLI execution with scripted inference; its world
and clean-stop checkpoint components remain synthetic. This does not establish
authentic Minecraft checkpoint or restoration. The retained original OAuth
authority is separate and unchanged.

M0.1d.3 remains implemented but unverified for authentic joint recovery. Next
bind authoritative stopped vanilla persistence, preregistered native retention,
fresh backend grants/observations and restored state assertions into the connected
path. Missing policy must not be retroactively assigned to old native runs.
Preserve scorer/setup/isolation gaps, all failed 500-ms samples, five effective-file
failures and Mineflayer/E9E incompatibility. M0 remains incomplete and G0 fails.
