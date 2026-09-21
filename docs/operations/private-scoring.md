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
