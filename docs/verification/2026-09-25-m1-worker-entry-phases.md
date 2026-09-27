# M1.6q.14 worker preparation phase diagnosis

Status: in_progress investigation. G1-G5 remain not_run. Production code,
acceptance limits and profile identities are unchanged.

Native10 remains a failed, consumed attempt: its first worker input entry took
148.437 seconds before world admission. Fresh diagnostics use the same profile02
binding and runtime manifest without replaying that job or launching Minecraft.

The first read-only diagnostic retains two deferred workers together under a
fresh materialization lease. Each runtime has 11,725 files totaling 654,090,742
bytes, with manifest SHA-256
`7ca5ff3d4df7f3e86485aab112db12ed6abf196b488ddef91da2f12348afa511`.
Entries take 14.327 and 13.865 seconds with cProfile enabled; CPU times are
13.984 and 13.516 seconds. Four attempted write-opens are denied. No configuration
is written, both state directories stay empty and all leases close. All 379
captured Python source pins and 40 real authority tables remain unchanged.

A new opt-in diagnostic then exercises the complete registered-pair input path:
[preparation test](../../tests/test_probe_worker_preparation_native.py). Its
separate `actual-vanilla-worker-preparation-only/1` input contains the pinned
software/save binding and player identity, with no writer launch plan. Source
fixtures read authentic sealed software/save data; agent/protocol/capacity and
budget records remain synthetic. Fresh private configurations are permitted.
ManagedProcess is guarded against dispatch, and the test never enters world-copy,
import, server or worker execution. There are no model calls or game actions.

```text
STRATA_PROBE_WORKER_PREPARATION=<private preparation-input.json>
STRATA_PROBE_WORKER_PREPARATION_SHA256=<exact input SHA-256>
pytest tests/test_probe_worker_preparation_native.py -q --basetemp=<fresh private directory> --junitxml=<fresh private report>
```

The initial collection fails because the diagnostic omitted its parametrized
`directory_fixture` argument. Its source and output are retained. Adding that
argument fixes collection. The corrected single case passes in 73.46 seconds,
with two existing Typer warnings and no skipped cases. Preparation through
cleanup spans 59.711 seconds under the original 300-second parent limit.

| Phase | First worker wall / CPU seconds | Second worker wall / CPU seconds |
|---|---|---|
| Complete entry | 14.499 / 13.750 | 14.629 / 14.266 |
| Materialization scan | 2.195 / 1.984 | 2.190 / 2.125 |
| Bundle manifest validation | 2.885 / 2.672 | 3.047 / 3.031 |
| Bundle acquisition | 7.999 / 7.719 | 7.959 / 7.734 |

These nested intervals overlap; do not sum them as independent campaign time.
cProfile adds overhead, and neither diagnostic is an authentic gameplay timing
certificate. The full-context case checks both configurations/account bindings,
empty worker states, no process dispatch, closed runtime/config leases, no world
or writer tables, parent FENCED and retained complete resource and synthetic
budget reservations. Source fixture teardown verifies the original archive.

Neither diagnostic reproduces native10's delay. Its cause remains unknown;
there is no evidence here attributing it to cache, antivirus or a particular
production function. Profiling does identify repeated complete acquisition of
the same immutable runtime as the largest routine entry cost. Next inspect
whether one continuously held, exact-reference runtime can safely serve both
members while retaining independent configurations, accounts, processes and
cleanup ownership. Any change requires negative custody tests and authentic
preparation verification before selecting a new paired game attempt. No native11
is selected on the strength of these faster unchanged diagnostics.

Coverage inherits M1.6q.13: F01/F02/F04/F05/F07/F08/F09/F16,
N01/N02/N03/N04/N05/N06/N08, C06/C20/C23/C24/C36 and partial
T01/T02/T06/T07/T11. Full matched live state/tool policy, native probe admission,
authoritative clocks/disposal, T05/T10 and root/helper isolation remain open.
M0/G0 and unrelated M2-M7 are unchanged. D18/D19 remain M0-only; all historical
holds and consumed decisions persist. Real exposure remains $4.887796.

Private evidence root:
`C:/Users/Darian/.strata/evidence/2026-09-25-m1-worker-entry-phases-01`.

Final audit confirms442 source pins (all441 prior pins unchanged),426 unique
milestone IDs preserving all425 prior IDs,1,685 local links, append-only history,
unchanged SPEC content, Ruff and whitespace checks. An initial audit compared
Windows CRLF worktree bytes against Git LF bytes and failed SPEC_CHANGED; both
that script/output and the corrected normalized-text check are retained. The
independent existing source hash check passes in both audits. All40 authority
tables remain unchanged at$4.887796; no owned runtime remains.

Q14 diagnostic evidence is sealed and independently verified:688 files,
46,737,787 bytes, SHA-256
`022401e06fb38ee1703a90ef3b50f941972c95c3ab15a66525ba0f15d237d453`.
This pointer follows the archived documentation snapshot. Preserve this root
and native01-10 unchanged; use fresh storage for subsequent implementation.
