# M1.6q.11 lexical directory-prefix reuse

Status: implemented_unverified for authentic paired integration. G1-G5 not_run.

`inventory._scan_layout` now computes each walked directory's relative prefix
once and appends each entry's native name. This is pure lexical work within
one directory iteration. Every entry still passes the same portable-path policy,
case-collision, lstat/type/reparse, hardlink, quota and hash checks. Both complete
membership checks and standalone custody checks remain unchanged. No filesystem
observation or successful authorization is cached; no public API/schema changes.

```text
pytest tests/test_inventory_directories.py tests/test_held_materialization.py tests/test_held_role_scan.py tests/test_pack_launch.py tests/test_provisioning.py -q
```

114 cases pass in 50.47s, no skips/failures. These synthetic installation tests
cover exact nested and empty-directory manifests, both roles, source changes,
ancestor substitution, unexpected/private paths, malformed layouts, current
authority and held-custody refusal paths. Two existing Typer deprecation warnings
remain. Ruff and whitespace checks pass. No unchanged broad paired suite was
rerun for this lexical change.

The baseline is q10's already sealed read-only diagnostic, reused without a new
run. The clean starting commit is `a4f6c56b9308f981df843ce7bfba694ceaceb618`;
its inventory implementation was archived before editing. One changed read-only
diagnostic uses the same real profile02 binding and external Java, after source
tests terminated. Public and held resolution remain equal, and the complete
resolved digest matches q10:
`011e977b1cbb34474e8c32bb870d09820454456e184627cc66423d07610b6456`.

Profiled held resolution changes from 6.078s to 4.531s. The two core scans change
from 3.437s to 1.947s; both whole-tree membership checks remain, taking 1.136s
cumulative. The diagnostic confirms two denied write-opens and closed custody;
configuration writes, model calls and game dispatches are zero. These measured
intervals are diagnostic evidence, not campaign clocks or a complete paired pass.

All 40 real authority tables remain unchanged at $4.887796. No owned runtime
remains. D18/D19 are M0-only; no M1 paid inference is authorized. No native10
attempt was selected or run. Preserve failed native01-09, all consumed inputs,
holds, and the original parent300s/writer200-170s/server60-60s bounds.

Next profile protected-session preparation without server/worker dispatch, using
fresh diagnostic custody without reopening any consumed job. Native09 recorded
substantial time between completed imports and the two initial-state-held events;
source inspection identifies complete tree/persistence checks there. Establish
their actual costs before changing those checks or selecting a new paired trial.

Coverage inherits M1.6q.10: F01/F02/F04/F05/F07/F08/F09/F16,
N01/N02/N03/N04/N05/N06/N08, C06/C20/C23/C24/C36 and partial
T01/T02/T06/T07/T11. Full live matched-state/tool parity, native admission,
authoritative clocks/disposal, T05/T10 and full root/helper isolation remain
open. M0/G0 and unrelated M2-M7 remain unchanged.

Private evidence is sealed at
`C:/Users/Darian/.strata/evidence/2026-09-25-m1-layout-prefix-01`:
5,924 files / 17,152,579 bytes, SHA-256
`320ed4c38fb6e076dbb6fc5fccdbffa780e271b5f42496ce891f7ba458e14ff3`.
Independent bundle verification passes. The archive includes 439 source files,
the unchanged baseline source and explicitly reused diagnostic, the new profile,
all test artifacts, fresh authority/process audit and documentation snapshot.
All 422 prior milestone IDs remain, M1.6q.11 is added, 1,669 local links pass,
progress is append-only and SPEC is unchanged. This seal pointer was added after
the documentation snapshot. No sealed evidence is subsequently modified.
