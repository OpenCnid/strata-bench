# Private development scoring

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
