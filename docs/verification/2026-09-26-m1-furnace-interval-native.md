# M1.5b.8 — native interval reference failed at telemetry capacity

Operation09 fails its native acceptance gate. The eight ordinary gameplay
actions pass, but the private telemetry broker exhausts its hard-coded8 MiB
capacity before retirement and clean-stop records. The controller reports
`REFERENCE_TELEMETRY_UNCERTAIN`, requests abort, and retains all four durable
rows as UNCERTAIN/consumed. This is not a successful native interval reference,
and no protected scoring or G1 claim follows.

Profile: source37c80a6, telemetry0.3.18/ServerStarted19,
`thermal1192-native-furnace-server-tick/1`, with the existing phases2,
registration1, processing1 and transitions1 policies. The146,855byte producer is
`061712cee52408d7514da3879c538ccb4cc496e485c378c43f23409decca2cf0`.
The client remains31facc27/minor45/policy4; compiled broker and ordinary
two-item checker are byte-identical to operation08. A fresh8,609-file source
tree changes only the telemetry jar and preserves the original tree.

The561 pinned dispatch inputs bind the new interval criteria before launch.
The predeclared selector is the unique first-start through unique final-refund
interval, exactly84 ticks, all child/state joins, no resource changes within
transfer/charge stages, no rejected ticks, and actual terminal retirement.
The V4 setup seal at cursor9 precedes reservation12. Its setup digest is
`b9f3f54b00f47052060e42bf71dfe831c546986f02d7b913c6195eb53e86a361`.
These private reference criteria do not create a registered scoring window.

The authenticated prefix has1,225 records and8,381,077bytes: startup1,
recipe1, setup history1, setup snapshot1, health207, server ticks925,
processing84, transitions3 and completions2. The next record exceeds the
8,388,608byte cap. The2,000-event cap has not been reached. Both launcher
transport branches currently hard-code these capacities in reference_launch.py;
the new per-tick record volume was not reflected in launch capacity planning.
The native writer then reports `TELEMETRY_PIPE_IO`; the server fails closed on
incomplete private evidence. This is an evidenced capacity failure, not a
random gameplay failure or a reason to rerun unchanged.

Read-only prefix diagnosis authenticates the original bytes and finds925
accepted tick traces, one lifetime, no rejected ticks or pending children. The
predeclared processing interval spans server ticks3969–4052 inclusive and has84
joined observations with no external resource change inside its stages. Both
completions and the start/refund events are present. However, there is no
lifetime-end, final clock or server-stop record. Full authenticated inspection
correctly raises `TELEMETRY_CLEAN_STOP_MISSING`; partial diagnostic continuity
does not satisfy native acceptance. Prefix SHA-256:
`63a719f5661754fb2515fb6fb71c73dbddd3ccb87bbd7ccfc2170fd51ede9351`.

The actual V4 importer refuses with `CRAFT_PROTECTED_REFERENCE_UNQUALIFIED`,
creates no receipt and leaves its outbox unchanged. The prior plan/authority
binding still verifies. All53 public CLI outputs lack the private diagnostic
marker. This narrow check is not full T06 nonleakage qualification.

Eight unique action receipts report emitted/release-confirmed actions, joining
53 public CLI calls and71 authenticated native journal frames. The action
primitive counts are3/3/3/3/4/5/4/3, totaling28; one further cleanup primitive
brings the journal total to29. The initial failure audit used a nonexistent
frame-file glob and labeled the all-primitive count as action-only. Its original
output is retained; journal-counter-audit.json records the corrected meanings
and counts without replaying gameplay or changing acceptance criteria.

The pair terminates after494.297s. All130/130 client and29/29 server parent
histories are terminal with no forced outer parent; inner custody cleanup was
forced after the telemetry failure. The session arguments are retired and the
final process inventory is empty. Guardian acceptance fails without a timing
sample; no1000ms pass or normal-stop claim is inferred from eventual cleanup.
No complete checkpoint or saved-resource equivalence is claimed.

All40 durable accounting tables remain unchanged at4,887,796microUSD. There
were no model calls, no new inference allowance, and no consumed-grant replay.
The private client failure diagnostic is not exercised; log hash
`2f77e133a8b90abbb8970ad7fdc85f12d1d48897442e822ca1a8e93748bf3dae`.
The additional client reacquisition branch remains unproven.

Executed: audit_quota_failure, audit_failed_reference, audit_diagnostic and
the supplemental journal count audit. The staged positive operation/import/
processing/transition/interval/terminal audits were not executed. A read-only
status query initially assumed a state column in craft_reference_launches and
failed; subsequent status inspection used actual column metadata. No state was
changed by that query.

M1.5b.8 remains in_progress. M1.5b.8a tracks the next concrete dependency:
explicit finite telemetry capacity in the prior launch contract, validation and
storage reservation sufficient for this producer's bounded event volume,
followed by a fresh changed-profile native reference. Preserve this failed
operation, original limits and prefix; do not append records, increase its cap,
rearm it or silently trim the required interval. Replacement/retirement,
registered windows, setup/team/loaded producer, alternate/negative controls,
parity/isolation and all other G1 contracts remain required.

Private roots: `2026-09-26-m1-furnace-operation-09` and
`2026-09-26-m1-furnace-interval-native-preparation-01`. The source candidate's
[separate checks](2026-09-26-m1-furnace-interval.md) remain285 Python passes,
four native skips and20 Java passes; no unchanged test suite was rerun.

Final integrity audit passes813 unchanged source pins,452 unique/preserved
milestone IDs and1,732 local links. All40 authority tables and the declared
source/client artifacts remain unchanged. Operation09's617-file/105,052,990byte
archive verifies under seal
`3352783fbecdf4295c137241885de17f5606e9c22b5b02912996453c48c88a15`.
The preparation/audit archive28files/3,365,908bytes verifies under seal
`e430afeb404a5023831ef6c713f9b278cee1cfa2bc37fb915841efee3ceda9ed`.
These pointers follow the archived document snapshot; both archives are unchanged.
The native reference remains failed and the M1/G1 goal remains active.
