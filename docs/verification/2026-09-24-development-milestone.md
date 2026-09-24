# Connected private development milestone

M0.2c.3b.4 connects the authenticated craft importer to the private development
scorer and report. M0.2c.3b.4a qualifies the corresponding history-bound authentic
negative. Both pass their bounded contracts. G0 item 5 is now evidenced for the
named D14 development scope; full private-scoring/nonleakage qualification is
not asserted. M0 remains in_progress and G0 fail, with remaining item 4/6 work.
Coverage: F04/F09/F10/F13/F16, N01/N02/N04/N06/N08, C18/C24,
partial T01/T06/T07/T10/T13 and G0 item 5. M1–M7 are unchanged.

## Implementation

[development_milestone.py](../../evaluator/src/strata_evaluator/development_milestone.py)
requires a sealed version-3 reference. It invokes the existing importer, which
checks recipe/resource evidence, actor/team/mode, tick window, complete declared
history and tracked launch closure. Only accepted witnesses become derived
events for the existing private `Scorer`. A second authenticated pass preserves
the actual signed header and detects changed wire bytes before scoring.

The event retains its original timestamp, sequence, server tick, actor and
transaction. Counts and ingredients come from the verified resource witness.
`valid_setup` is explicitly scoped to the bounded development candidate checks;
it grants no complete setup, process or scoring authority. Plain source digests
bind the plan, authority, spool and inspection; no nonexistent CAS refs are
invented. A distinct `m0dev-` namespace and durable report table prevent mixing
these results with other scorer instances. Exact replay is idempotent; changed
source/report content is rejected. A failed output write can retry without
double credit. Original reference imports remain unchanged.

The command is evaluator-only. It publishes a create-exclusive private report,
rejects game/authority output directories and exposes no new gameplay/helper
tool. Results retain all isolation/scoring/scientific/admission flags as false.
This is a D14 development predicate, not an authoritative scientific score or
complete T10/G1 qualification. [Operator command](../operations/private-scoring.md).

## Executed checks

```text
python -m pytest tests/test_development_milestone.py tests/test_craft_reference.py
  tests/test_setup_history.py tests/test_setup_facts.py tests/test_scorer_scope.py
  tests/test_evaluator.py tests/test_gameplay_package.py -q -rs
158 passed, 3 skipped in 21.36s
```

Fifteen new cases cover source-to-report integration, persistent restart,
reverted mode, wrong team/mode/operator, tick window, insufficient consumption,
wrong output, legacy refusal, corrupt wire/stored import, changed bytes between
reads, private output paths, output-write retry and durable report conflict.
The compiled gameplay package test verifies the exact allowed client files and
an ungranted request's FORBIDDEN result. This is package/tool exposure evidence,
not full filesystem/process/network isolation.

The three existing skips require explicit pinned-JVM opt-ins for synthetic
fixtures; no new JVM coverage is claimed. The earlier 155-test run overlaps and
is not added. One initial new test expected only `Fault` for malformed trailing
JSON; the parser correctly raised `ValueError`. The test now accepts both refusal
types. One fixture-name lint issue was also corrected. Ruff passes.

## Authentic retained captures

Private `2026-09-24-development-milestone-01` verifies the original bundles and
uses new writable database copies. It never alters or relaunches a source run.

| Capture | New consumer result |
|---|---|
| `2026-09-23-protected-craft-heap6-05` | Pass: one completed development craft, exact five andesite/three polished andesite consumption, one furnace, one derived event and original signed header |
| `2026-09-23-protected-craft-heap6-04` | Refused with CRAFT_PROTECTED_REFERENCE_UNQUALIFIED; no report or scorer state |
| `2026-09-23-script-handle-history-live-02` | Refused with DEVELOPMENT_HISTORY_REQUIRED because its setup was sealed as version 1; no report or scorer state |

The independent audit passes **26/26**, including the actual CLI restart with
identical report and unchanged database rows, every original reference row
preserved, exact source/header/witness/digest joins, private-only journal events,
no key/path disclosure in the result, and both typed refusals. All **40** original
accounting tables remain unchanged at **$4.849167/$10** exposure; zero new game or
model launches. Prior failed captures remain failed.

Source seals, in table order:

```text
e26f01bec4a9cd2f20bdb4ea3662865ab9384126ab83dc8e6cd251ad53cb9fde
b1b3c5381c19d44f5aaef69f7ab6687660285227eb152c67b203685752029d34
05bb13b2c550c12d0ab42b4d5e1341ee820e0b89cc47e41ac5b67dd55beede13
```

The offline consumer/audit archive contains **165 files / 25,084,291 bytes**,
including 136 source files and separate writable reference database copies.
The three original captures remain external, separately sealed dependencies;
no game distribution or private signing-key copy is included. Full readback
passes with seal:
`c8eee854b28d0c449808077e6cbb6922ee428b0c12ce77e9d61b7273989196cc`.

## Fresh authenticated negative

The legacy refusal is not counted as an authentic history-based zero-credit
report. Fresh `2026-09-24-development-negative-01` seals version 3, exact history6
and native team mapping before launch. It uses the prior six-invocation control
script and unchanged telemetry 0.3.13, E9E/Forge/JRE, loopback port and bounded
headless runtime. This changes the preregistered report contract and connects
the new consumer; it does not repeat an unchanged successful profile.

Preparation rechecks **18,225** source files, **1,542** immutable inputs and the
**104-file** fixture. Native team registration is taken from the sealed positive
reference and matches the existing actor. Original files and all **40** live
accounting tables remain unchanged throughout preparation, execution and audit.

The fresh control and report pass **49/49 independent checks**. The actual
MethodHandle setter/restoration, getter, rejected bad value and converted
VarHandle setter/restoration leave exactly six signed unresolved attempts.
Startup is clear; the terminal history remains tainted after restoration.
The new private report retains that history, zero development output, no derived
craft event and all qualification flags false. Identical reimport appends no
event; consumed authority and relaunch attempts reject.

No player joins and no craft occurs in this headless negative. Consequently,
its zero output alone cannot establish the causal effect of history rejection
on an otherwise valid craft. The signed synthetic valid-craft/reverted-history
control exercises that distinction; it is not relabeled an authentic trajectory.
The actual negative qualifies the connected preregistered history/report path.

Server lifetime **165.922 s**, outer owner **170.063 s**; six server processes
and ten outer processes are terminal, with no forced cleanup. Nested counts
overlap. The authentic callback clock records **208 ticks / 14.8091348 s**, with
two ticks after the last health sample. It remains distinct from full active
time and records no avatar events. Zero paid requests, zero player connections,
no shared-desktop input; exposure remains **$4.849167/$10** with all holds intact.

The complete **329-file / 44,442,854-byte** archive verifies. SQLite is
checkpointed into DELETE mode before sealing. Seal:
`6743b2fc6f2945965eab54c9c2c37f0eb22bc75108dccf741813b30213d89e82`.
Audit digest:
`4f8d9ccc7e6ad38216d5fcb9866ba6b2273442d5b9d9d62f0388018d10e501b6`.

This closes the bounded development producer/scorer/private-report connection
and selected positive/negative controls under D14. It does not establish full
setup-history coverage, mechanical parity, adversarial nonleakage or scientific
scoring authority. Those original requirements remain visible and unqualified;
full isolation/nonleakage stays deferred to M1/G1 under D14. No broader T10 or
aggregate G0 pass is claimed. Next address the remaining applicable recovery and
time/cost evidence; in particular, native/vanilla reports still lack authoritative
server/avatar ticks and performance measurements.
