# M1.6r.4 paired private save-format comparison

Status: implemented_unverified for authentic paired capture. M1.6r.4a's first
actual attempt fails before admission; M1/G1 remain in_progress/not_run.

The distinct `PrivateProbeVanillaLaunch/3` and worker-reference policy/2 compose
the already verified private observer with both registered worker arms. Require
the same module and complete registered UUID roster, pair/epoch/run scope, held
input/output bytes and authenticated owned producers. Workers remain alive
until their arm's capture is ready and then drain before normal server exit.
Old profile identities and their results remain unchanged.

The private comparator checks every emitted typed NBT field, including unknown
fields, nested item tags, list order, integer types and exact float bits. Compound
insertion order is not state. Original raw bytes and their digests remain
retained; no state fields are ignored or rewritten. Diagnostic field names are
bounded ASCII, with complete comparisons even when the displayed list truncates.
The pair reserves both full observer bounds plus 8 MiB for the comparison report.
An unequal result is flushed to private evidence before the pair refuses with
`PROBE_BODY_SAVE_STATE_MISMATCH`. Custody loss or changed capture digests refuse
separately. Even an equal result does not assert full initial/transient state,
native probe admission, instrumentation parity, clocks or disposal.

Source changes: [comparator](../../evaluator/src/strata_evaluator/player_body_match.py),
[paired server](../../evaluator/src/strata_evaluator/probe_vanilla_runtime.py),
[paired worker](../../evaluator/src/strata_evaluator/probe_worker_runtime.py),
[comparator cases](../../tests/test_player_body_match.py),
[paired custody cases](../../tests/test_probe_body_capture.py), and the
[opt-in authentic driver](../../tests/test_probe_worker_runtime_native.py).
Source fixtures use synthetic game/worker/observer evidence and actual private
file custody; they are not authentic Minecraft matching evidence.

The original saved baseline has `XpSeed=0`. Inspection of the pinned official
1.19.2 Player load bytecode confirms that zero is replaced from RNG. This
explains one retained divergence without normalizing it away. Standalone
body-native02 also retains zero. Native11's later stopped `/3` probe exports
are not training inputs: the existing `/2` source restriction stays in place.
Any positive matching fixture needs its own properly initialized authentic
source and scope; no historical input or consumed attempt is edited.

## Executed checks

Private JUnit and pytest outputs record the actual case identities and results
for the two new test files and the retained
`test_complete_pair_imports_before_servers_then_workers_drain_before_save` case.
The first
comparator run has 28 passes and one failure: uppercasing an all-numeric UUID
does not make it invalid. The corrected alphabetic UUID case passes; its original
source/output remain. Initial Ruff formatting findings are retained in the work
history. Corrected comparator29 and initial paired15 pass. Review then bounded
diagnostic output; the final comparator/paired selection passes45 in116.93s,
plus the unchanged legacy-route case from the earlier run: **46 distinct current
source cases**. Two existing Typer warnings remain. Ruff and whitespace pass.

Actual `2026-09-26-m1-body-pair-native-01` uses scope
`actual-vanilla-workers-synthetic-agent-protocol-reference/2`, the unchanged
zero-seed baseline and an expected unequal-state refusal. It preserves
parent300s, writers200/170s and servers60/60s, with zero model calls/actions.
The test fails in146.60s with `PROBE_WORLD_DEADLINE`, before imports, world-row
admission, writer preparation, servers or workers. First/second worker input
entries take98.891s/1.906s; the preparation interval is133.609s. Remaining parent
time cannot admit the first200s writer. The guard is retained. The cause inside
the first entry is not established; do not attribute it to caching or antivirus.
No unchanged rerun is selected and no acceptance limit is increased.

Independent failure audit passes: all461 source pins and all40 real authority
tables unchanged at$4.887796, parentFENCED/resources held, no world row, writer
table or owned runtime. The initial audit wrongly required the writer evidence
parent to be absent; fixture setup creates an empty parent. The corrected audit
requires it to be empty. Both scripts and the failed audit disposition remain;
no game run followed that correction. **The intended mismatch refusal was not
reached and remains unverified.**

Private native evidence is sealed:236 files/39,726,406 bytes, SHA-256
`bf2df15cbe1a06431aac114a4eebd3880245c5400eda94a633eacb19a32743d7`.
Source evidence root:
`C:/Users/Darian/.strata/evidence/2026-09-25-m1-body-matching-source-01`.
Native evidence root:
`C:/Users/Darian/.strata/evidence/2026-09-26-m1-body-pair-native-01`.

Next resolve preparation latency with bounded phase evidence before another
changed authentic dispatch. Complete full initial/transient state and parity,
tool/clock/disposal boundaries and the remaining T01/T04/T05/T06/T10/T11 cases.
Coverage inherits M1.6r: F01/F02/F04/F07/F08/F16, N01/N03/N04/N06/N08,
C06/C20/C23/C24/C36. M0/G0, historical failures, all holds, consumed decisions
and unrelated M2-M7 remain unchanged. D18/D19 do not authorize M1 paid inference.


R4 final audit passes:461 source pins,434 unique milestone IDs,1,724 local links,
46 distinct source cases, append-only history and all40 real authority tables
preserved. Source archive3,504 files/12,406,745 bytes, seal
b8c8d1ceaf75c10514feef09630405882bba4f44efd0da6c16fe63c2a84bb0a2.
This pointer follows the archived documentation snapshot; authentic body-pair01
remains failed and G1 not_run.
