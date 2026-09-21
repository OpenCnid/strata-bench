# Read-only connected native/game evidence reconciliation

September 21, 2026. M0.1d.1; F03/F09/F11/F16, N01/N02/N03/N06,
partial T01/T07/T12, G0 items 1/4/6. M0 is incomplete; G0 fails.
The current user request and active long-horizon goal cover M0/G0 only.
Required later milestones and conditional extensions remain in the ledger.

The reusable evaluator command is:

```text
python -m strata_evaluator.native_game_evidence --plan PRIVATE_PLAN.json --output NEW_PRIVATE_REPORT.json
```

Use `PYTHONPATH=src;evaluator/src`. `NativeGameEvidencePlan/1` requires an
absolute private `bundle`, independently retained `seal_sha256`, and expected
`campaign_id`, `agent_id`, `epoch`, `job_id`. It accepts only the stopped
vanilla/native smoke format with the explicitly scripted local provider. It
launches no process and never constructs a writable controller, runtime or CAS.
Output is create-exclusive and forbidden inside the input bundle or source tree.

`evidence_bundle.py` checks exact bounded file inventories, external and
transitive hashes, safe paths and links. SQLite opens query-only and immutable
only after the stopped WAL/journal checks; it checks integrity and bounded
tables/queries. Final verification detects input changes. Archived absolute
paths are mapped lexically into the archive, never followed to installations.
`native_export.inspect_native_source` shares the stopped participant, envelope,
ledger, private artifact and drained-call checks with native export, without
installing tables or changing runtime state.

The verifier reparses every wire usage receipt, checks bound pricing and receipt
hashes, and counts each root/helper request once. Fixture units, estimates and
actual charges remain distinct. It joins worker acceptance/terminal events,
observation revisions, scope/epoch/lease, primitive counters, native broker
responses, stop intent/result, archived source/bootstrap pins, server logs,
saved player orientation and available lifecycle clocks. Old summary totals are
cross-checks, not the input used to calculate totals.

## Existing authentic game evidence

No new Minecraft, native CLI, model or desktop run occurred. Fetched main and
merged PRs #3/#4 matched `c2161a6e79cea0c668ab993df149ab1ed5af119b`; work began
on fresh `codex/strata-m0-g0`. Both relevant checkouts were initially clean.
The private original authority was read in place: $10 cap, $0.7554 unresolved
hold counted once, $0.001458 settled, $0.756858 aggregate, uncertainty true,
two distinct requests and one valuation. D12 remains consumed. No mutation,
replay, model dispatch or allowance change occurred.

Input is the retained `2026-09-21-m0-native-game-02` bundle, external seal
`866250d9c903c7d9183349b7a6b3a164aa3f0cdd173def627f1677ee95c4006d`.
The **flat manifest inventory fails**: it lists 4,128 files but omits 105 deep
plugin fixture files. All 105 have matching size/hash entries in the already
sealed, prelaunch bootstrap manifest. The complete 4,233-file transitive
inventory passes without replacing the original seal or changing original
bytes. Unlisted files without that existing hash chain still reject. An initial
manifest-only projection correctly failed the complete bootstrap check; its
audit is retained, not presented as a repaired authentic archive.

The reconstructed private report passes this reconciliation scope:

| Evidence | Reconstructed result |
|---|---|
| Scripted provider | 6 calls; 60 input tokens including 12 cached; 24 output; 84 fixture units |
| Native participants | Root and helper envelopes closed; no uncertain dispatch or undrained call |
| Worker | One terminal bounded look; one charged primitive; matching broker/journal receipt |
| Stop | Native FINALIZED, worker binding STOPPED; server stopped_unqualified, no forced cleanup |
| Saved reference | Changed orientation agrees within 0.01 degrees; position agrees |
| Recorded wall intervals | Native 25.8371837 s; outer 194.906 s; server 193.344 s |
| Other intervals | 747 provider-request ms and 219,000,000 broker-call ns; overlapping intervals are not summed |

Final report content digest:
`7ebd908afb1c8a72b9d5d7f1d63ed45744d0e0de784bddb7d7d13349bf5bd40c`.
Private verifier artifacts are in `2026-09-21-m0-native-game-verifier-01`.
The first report is retained; the final report additionally makes unarchived
worker dependency-lock/schema bytes explicit instead of treating reported
digests as independent byte verification.

## Executed checks and limits

With Python 3.12.14 and current source on `PYTHONPATH`:

```text
pytest -q tests/test_native_game_evidence.py tests/test_native_export.py
```

**52 pass / 9.19 s.** Focused Ruff passes. Synthetic cases cover read-only
database/no-sidecar behavior, live WAL rejection, inventory/hash/path/size
faults, deep transitive integrity, missing/duplicate/foreign worker receipts,
counter conflicts, helper misuse and uncertain actions. Existing native-export
tests exercise the shared validation and preserved accounting/no-replay rules.

The private derived-copy mutation audit adds **16/16 passing rejection checks**:
missing/duplicate/foreign settlement; uncertainty; missing helper grant;
unfinished broker call; wire-capture conflict; pending/mismatched stop;
foreign action; conflicting/missing worker terminal; primitive undercount;
clock rollback; changed archived source; and zeroed legacy summary. Copies are
explicitly synthetic and re-anchored solely to exercise semantic joins. Audit
digest `b9060f83350cfb046ebf367831ba287046ae4f0454c337c043bc4c93255176f5`.
A harness rowid-alias error after the first six cases was retained and corrected;
the remaining ten ran afterward. The original archive was never changed.

This verifies the existing game run's recorded evidence, **not full M0.1d or G0**.
Authoritative ticks/active time/TPS/MSPT/worker lag, performance series, private
scorer/setup authority, full runtime/helper isolation, complete role/pack locks,
external runtime bytes, broker request preimages, per-primitive worker traces,
500-ms shutdown measurement and joint game/agent recovery remain gaps. Absent
clocks are null, actual charges are unknown, and scoring/production qualification
are false. Every earlier failed shutdown, five effective-file failures,
Mineflayer/E9E incompatibility and D12 native-delivery failure remain unchanged.
