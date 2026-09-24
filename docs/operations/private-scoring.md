# Private development scoring

## Connected D14 milestone report

The operator-only command below connects an authenticated, history-bound craft
reference to the existing private development scorer:

```text
python -m strata_evaluator.development_milestone --database <private-reference-db>
  --instance <sealed-instance> --spool <complete-authenticated-spool>
  --output <new-private-report.json>
```

Use a reference sealed as `PrivateCraftReferencePlan/3`, including its exact
native team mapping and history policy. The command recomputes the existing
import checks before every publication. It accepts neither a caller-provided
success flag nor a saved inspection as a substitute for the signed source.
Only accepted resource witnesses become derived `CraftEvent/1` records; the
signed header, actor, transaction, recipe, consumed ingredients and output are
preserved. Source digests identify the sealed plan, authority, spool and import.
They are file/content digests, not fabricated CAS object references.

The scorer uses a distinct `m0dev-` instance namespace. Identical restart or
report-write retry cannot count the craft twice; source/report conflicts fail
and retain the prior result. The output is create-exclusive, and paths inside
the game or authority directory are rejected. No command, report or predicate is
added to gameplay/helper tools or the gameplay package.

`PrivateDevelopmentMilestone/1` records the development predicate result,
derived events, rejected witnesses and declared mutation history. In its derived
event, `valid_setup=true` means the sealed development candidate checks passed.
It does **not** certify full setup authority. The original import remains
unchanged and unscorable. The report retains `scoring_eligible=false`,
`scoring_authority_qualified=false`, `isolation_qualified=false`, no scientific
claim and no campaign admission. D14 defers full isolation qualification; this
command cannot promote a development result into an authoritative benchmark
score or a G1 pass.

## Existing scorer and source registration

The evaluator package and its database stay outside gameplay-agent and helper
access. `Scorer` accepts registered development event schemas; raw Forge
callbacks, configuration snapshots and resource witnesses cannot earn credit.

Before calling `score(instance, predicate, event)`, the trusted operator calls
`register_source(instance, predicate, ScoringSource(...))`. Supply the expected
campaign, positive epoch, server boot, `synthetic` or
`authentic_operator_reference` evidence kind, and 1–32 supporting SHA256 digests.
Resolve these from the operator's run plan, not from the event being admitted.
The registration API records assertions; it does not validate the referenced
artifacts or authenticate their producer.

The [authenticated telemetry spool](forge-telemetry.md) now verifies a private
per-boot key/challenge, scope and exact event chain before inspection. It does
not change this registration API or make raw callbacks/resource witnesses
scorable. Preserve its authority/spool digests as separate private provenance;
process/key isolation, setup/team facts and authentic controls remain required.

An instance keeps one campaign and evidence kind. Its predicates keep their
complete definitions. All predicates share one immutable epoch-to-boot mapping;
a new source requires a larger epoch and a distinct boot. Repeating the exact
registration is safe. Register each legitimate restart source explicitly before
replaying its events. An unchanged transaction payload and actor list contributes
only once across those sources. A changed duplicate fails rather than silently
returning the earlier result.

Unregistered sources, changed definitions and conflicting receipts fail within
the database transaction. Historical unbound state fails
`SCORER_UNBOUND_HISTORY`; preserve the database for a separately qualified
migration. Do not delete state or start a replacement scientific instance to
conceal the missing provenance.

Telemetry 0.3.11 / startup12 adds the separately versioned
`native-e9e-setup-mutation-watch/4` history requirement. Its seventeen routes
include script-origin FTB field writes and bounded reflection-inspection
overflow. The pinned Rhino direct-field and reflective-invocation hooks must
both be present. Any observed field write remains disqualifying after restore;
missing hooks, schema/module mismatch, rollback or an altered sealed requirement
reject admission or candidate credit. Policies1–3 keep their original meanings.
These hooks do not establish coverage for arbitrary native/mod field writes,
method handles, pre-activation changes or complete custody. See the
[field-write control](../verification/2026-09-23-script-field-history.md).

Outputs always retain `scoring_authority_qualified=false`. This interface does
not admit a campaign or supply authenticated ingress, sealed setup/team
authority, telemetry parity, filesystem/process/network isolation or full T10
controls. Those are required before an authoritative benchmark score. See the
[implemented boundary and verification](../verification/2026-09-20-scorer-scope.md).

## Sealed craft reference inputs

Use `python -m strata_evaluator.craft_reference --database <private-db>` with
one of these subcommands:

```text
seal --plan <private-plan.json> --directory <fresh-private-authority-directory>
preflight --instance <registered-instance>
inspect --instance <registered-instance> --spool <signed-complete-spool> --output <new-private-report>
```

`PrivateCraftReferencePlan/1` pins the selected fixture's complete relative file
inventory (SHA256 and bytes), supporting files, instance/campaign/epoch,
synthetic or authentic-reference evidence kind, team/unique agent-to-Minecraft
UUID roster, complete craft predicate, runtime recipe digests, and inclusive
start/cutoff server ticks. The fixture directory must be within the declared
game directory. Keep the plan, database, archive, key and output outside it and
outside source checkouts. Provision operator-only permissions first; these path
checks do not create an adversarial identity boundary.

`seal` preserves private copies and publishes the database binding last. It
issues `TelemetrySpoolAuthority/2`, whose fingerprint includes the setup digest;
use its `producer-authentication.json` in the existing Forge configuration 3.
`preflight` rechecks the baseline and consumes a durable one-launch reservation.
It is not a read-only status command. Repeating it or using a consumed grant
rejects. Keep a partial seal or ambiguous reservation; do not renew automatically.

`inspect` recomputes the authenticated native witness and resource/roster/recipe/
tick-window join. It preserves rejected candidates and deduplicates a complete
identical import after restart. A changed import fails. Reports are private and
create-exclusive; they do not write scorer state or grant credit. The benchmark
roster does not assert FTB Teams membership, and checked supporting bytes do not
automatically prove setup semantics. See [verification and remaining launch/
setup gates](../verification/2026-09-20-craft-reference-seal.md).

`PrivateCraftReferencePlan/2` additionally requires `native_team_ids`: a mapping
from every registered agent ID to its expected FTB team UUID, fixed before
sealing. It must have exactly the roster's keys. Do not infer this mapping from
arriving telemetry or amend a consumed version-1 seal. A version-2 import needs
telemetry 0.3.5 / `ServerStarted/6`, supported pinned native observation artifacts,
the first-tick setup point and the correctly adjacent before/after points for
each craft. The resulting `PrivateCraftReferenceInspection/2` records named
native-point failures and excludes those candidates.

Native mode/admin/team point agreement remains unscorable. Command counters
cover observed Forge command attempts, not every possible mutation route;
matching snapshots do not prove continuous history or fixture validity. Preserve
unavailable observations and prior failed profiles. See the [native setup
implementation and evidence](../verification/2026-09-20-native-setup.md).

Telemetry 0.3.7 / startup 8 adds private sticky mutation counters immediately
before each setup snapshot and final stop. The importer rejects the entire
reference's candidates for any observed mode/operator/team mutation, including
a reversed change or an attempt after the craft. Counters cannot roll back;
missing/reordered/foreign history or incomplete termination rejects the stream.
One exact terminal native stop command is distinguished through its actual
handler, source and thread; its counters remain visible. It cannot excuse an
extra command or establish the declared shutdown gate (D13 uses 1,000 ms;
legacy 500-ms failures remain failed). Legacy streams remain
readable without retroactive history credit. Public mutable FTB fields/maps,
KubeJS globals and other direct writes remain uncovered, so clear observed
history still earns no score. [Implementation and exact limits](../verification/2026-09-21-setup-history.md).

Telemetry 0.3.9 / startup 10 / NativeSetupHistory/2 adds a separate runtime
check of the observed KubeJS GLOBAL map and a fourteenth sticky route for writes
to its three pack-mode keys, including map methods and retained collection
views. The inherited callback clock contract remains mandatory. Reflection,
direct FTB state, pre-activation changes, custody and mechanical parity remain
unqualified. Keep complete-history and scoring flags false. The changed-profile
headless roundtrip qualifies only its observed route; it does not qualify an
unchanged pack. [Current source and authentic evidence](../verification/2026-09-23-global-history.md).

Telemetry 0.3.10 / startup 11 / NativeSetupHistory/3 additionally observes the
FTB rank, player, team and name-cache maps. Require its runtime map-support bit
and fifteen-route history. Linked maps preserve insertion order; initial lazy
name-cache population is excluded before the returned map is armed. Direct
scalar fields and reflection remain uncovered, so this does not enable scoring
or full continuity. [Source and control evidence](../verification/2026-09-23-team-map-history.md).

Use `PrivateCraftReferencePlan/3` for a history-required protected craft.
Alongside the version-2 native roster, explicitly register
`required_history_policy: native-e9e-setup-mutation-watch/1`, `/2`, `/3` or `/4`, matching
the selected module and sealed requirement exactly. Participant
readiness requires a complete authenticated clear startup/history prefix whose
native identity matches the owned server. Import requires the complete history;
an older valid point-only stream fails with `CRAFT_NATIVE_HISTORY_MISSING`.
Version-3 inspections retain this requirement. Do not upgrade consumed older
plans or infer complete route coverage from clear counters. [Admission contract
and integration evidence](../verification/2026-09-21-protected-craft-history.md).

`PrivateReferenceLaunch/7` is the separate headless operator grant/revoke
diagnostic. Its `setup_control` declares policy `private-operator-roundtrip/1`,
purpose `negative_control`, the registered `agent_id`, `actor_uuid`, exact
`player_name` and `operator_level: 4`. The setup seal must include supporting
roles `operator-roster` and `profile-cache`, pointing respectively to the game
directory's `ops.json` and `usercache.json`. The roster starts empty, and the
cache must bind the exact target throughout the bounded reference. Arbitrary
command text and participant fields are rejected.

The ordinary private `reference_launch` CLI owns startup, one grant/revoke and
normal stop. It preserves the actual intermediate operator file before any
revocation, then joins the final empty roster to permanently tainted signed
history. Uncertain effects or writes consume the reference without replay.
Do not use the private clone as a clean gameplay baseline or interpret this
negative control as full setup/scoring qualification. Version-6 world-mode
behavior remains unchanged. [Control contract and evidence](../verification/2026-09-22-operator-control.md).
