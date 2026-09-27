# M1 owned game lifecycle and native boundary integration

Operator-only. M1.3b.9d; F03/F04/F07/F16, N01/N04/N06,
C06/C12/C13/C20/C36, partial T01/T04/T06. M1 is in_progress and G1 not_run.
No RuntimeQualification, paid M1 authority or simultaneous-body capacity claim.

## Explicit M1 orchestration

`tools/m1_native_game.py` accepts only `strata/M1NativeBoundary/1`. It validates
the two-entry synthetic controller roster, selected Luna/native/Dovetail pins,
one helper/depth, worker scope and fresh paths. The PackLock and restored-world
baseline reference must match the actual binding. Provider metadata is
`local_scripted`; paid-pilot and agent-retention fields are rejected. The
configuration records describe actual controller execution and therefore have
`is_example=false`; controller readiness and provider responses remain synthetic.
The simulation flag is retained independently of the record example flag.

The shared M0 game lifecycle accepts an explicit validated M1 candidate through
its internal interface. Ordinary M0 entry rejects the M1 plan, and M1 cannot
enter the shared lifecycle without its candidate. All existing M0 retention,
authorization and profile checks remain on their original branches. The M1
branch uses held restored-pack/worker resources, scoped worker connection,
normal stop, saved-world custody, worker journal and zero-active-process checks.
It exports the stopped native state separately, without claiming a complete
game/agent checkpoint. The selected worker's existing360,000ms bound is retained;
the native candidate remains90s,20 scripted requests/four helper requests and64
broker calls per participant. No campaign-budget or acceptance threshold changes.

## Source checks and first authentic failure

The focused lifecycle selection first passed92 cases and failed one stale
companion test stub that omitted the now-required broker policy. Adding that
field to the stub yields93/93; production validation is unchanged.

The first fresh authentic attempt connected the licensed Mineflayer worker to
the restored local vanilla world, then failed before native launch with
`EXAMPLE_NOT_EXECUTABLE`. The initial M1 plan incorrectly marked its controller
configuration as an example. The actual controller refuses such records even
in a simulation store. No controller campaign or native job was admitted.

Run01 retains its original failure. Elapsed outer game time71.75s; initial
connected observation at60.75s. Worker preflight, worker and server process
groups all exit0 with zero active members; no forced cleanup. The worker
journal has zero actions/primitive events and the server retains its stopped
save. All40 authority tables remain unchanged. Independent failure reconstruction
passes12/12; this is verification of a failed outcome, not a conformance pass.
The initial seal precheck rejected the presence of a worker WAL; inspection
found it zero bytes with a32KiB SHM. Both sidecars remain in the full inventory,
with the initial precheck disposition recorded. No checkpoint or deletion.

Private run01 bundle has346 files/42,570,973 bytes. Seal SHA-256:
`fdc85177a9d5bd258f70b2aa32f29dfe987fc9a093ba93759118a2ee23b19002`.

The corrected M1 admission now requires executable configuration records while
retaining the simulation/provider/readiness labels. Twenty focused M1 cases
pass, including actual entry into the synthetic controller and refusal of
example campaign or agent records. Together with the unchanged earlier
companion/retention results this is95 distinct source checks. The changed fresh
attempt below uses a new world/native identity and retains the first failure.

```powershell
.venv/Scripts/python.exe -m pytest -q tests/test_m1_native_game.py tests/test_native_companions.py tests/test_native_game_retention.py --tb=short
.venv/Scripts/python.exe -m pytest -q tests/test_m1_native_game.py --tb=short
.venv/Scripts/ruff.exe check tools/m1_native_game.py tools/m0_native_game.py tests/test_m1_native_game.py tests/test_native_companions.py
git diff --check
```

## Actual integrated candidate and offline stopped export

Run02 connected the authentic worker at54.766s and passed97/97 native candidate
checks. Root7/helper4 scripted requests settled for110 input/44 output tokens
and154 synthetic fixture units, no uncertain cost. One bounded look completed
with one primitive event; its actual acknowledgment joins the native receipts
and stopped worker journal. Permitted artifact/team controls and root/helper
filesystem/process/network/credential/tool attempts execute in the same profile.
These are fixed provider responses, not learned behavior or real model inference.

Native profile:
`88adebd2e3aec639198862bd969d202dff0cc7a6bd49fd26252a80cdf0469ecb`.
Native duration50.0267523s; outer167.766s. Native FINALIZED/exit0 and both
participants CLOSED. All three owned outer groups exit0/zero active; no forced
cleanup, and the server retains its normal stopped save. Full checkpoint,
simultaneous body capacity and campaign readiness remain unqualified.

The original outer result is **fail**: `NATIVE_CELL_UNKNOWN_TOOL`. Export's
cell reader rejected the deliberately issued unsupported shell/patch tools.
The native97/97 result is retained separately; it does not erase the outer
failure. Original producer seal:3,999 files/116,659,953 bytes,
`11fb7582ab82269cc6f00a5135818681d4f6f1681936215a84f3cce49b959b7e`.
The initial blanket empty-WAL precheck failure remains recorded. Nonempty native
logs/queue cache WALs stay sealed and are not read as immutable databases;
controller and worker WALs are empty. No original file was checkpointed/deleted.

`native-process-fenced-cell-disposal/2` now handles unfamiliar functions calls
only during stopped-job reconstruction. It validates issued call type/name/
payload, exact returned call scope and duplicate/conflicting evidence, retains
all uninterpreted IDs as unresolved, and requires the existing whole-job process
fence. It does not parse even an exact unsupported-tool string as success or
proof of isolation. Early retirement still rejects these calls. Existing /1
disposal and framed-drain /2 results retain their exact identities.

108 focused lifecycle/process/export cases pass, including malformed source,
missing results, forged completion, duplicate/change/reuse and no-fence refusal.
The95 orchestration checks above are disjoint:203 distinct source checks total.
Changed-file Ruff and whitespace pass. Verification command:

```powershell
.venv/Scripts/python.exe -m pytest -q tests/test_native_cell_lifecycle.py tests/test_native_process_disposal.py tests/test_native_process_drain.py tests/test_native_export.py --tb=short
```

An independent consumer changes only the cell-reader module among244 archived
source/cache files. It reads the original sealed producer and creates the export
only in an exact stopped controller/CAS copy.26/26 independent checks reconstruct
capture/ingress/catalog/receipt joins, clean helper context, team controls, actual
boundary/tool denials, worker credential exclusion, real game action/stop,
process disposal and idempotent component export. Each participant retains three
uninterpreted call IDs with `tool_success_inferred=false`. Source digest:
`03707d7805933333a368e122cc831fd021f47f03c8c997b14170b6fb38583db5`.
Another3/3 checks reconstruct both retained team exports unchanged and check the
extracted private module marker against captured requests. No runtime/game rerun.

Private consumer `2026-09-24-m1-native-game-audit-01`:326 files/5,940,237 bytes,
seal `ce2800d9e88603dcdb86d7adced8e87b7dfb76827ad415c9dc4b23e28affcb77`.
Retain its initial source-inventory comparison failure (17 already sealed native
bytecode files) and initial worker-query column error; both corrected readers
use the same original capture. All40 real authority tables remain unchanged,
exposure$4.887796 and all holds preserved. No paid M1 authority or model request.

Next complete the selected executable skill/fresh-handoff routes and reconcile
remaining client/registry/log/probe boundaries before a RuntimeQualification.
Use this capture for unchanged routes; a later combined case must be justified
by an actual changed profile or missing contract, not the desire to turn the
original outer fail into pass. .9d/M1 remain in_progress; G1 remains not_run.

Complete G1 still requires the unresolved routes in the
[profile reconciliation](2026-09-24-m1-profile-reconciliation.md), selected
skills/handoff, capable settings, protected scorer controls and matched probe
disposal. Neither an authentic connection nor a passing candidate can replace
those contracts or authorize paid M1 inference.
