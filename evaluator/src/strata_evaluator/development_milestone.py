"""Private D14 development predicates from authenticated, sealed craft imports.

No gameplay tool exposes this module. Development credit is not an authoritative
benchmark score, an isolation qualification or permission to admit a campaign.
"""

import argparse
import hashlib
import json
from pathlib import Path

from mcbench.records import GameEvent
from mcbench.storage import Database, canonical, digest, require

from .craft_reference import CraftReferencePlanV3, CraftReferenceStore, private_path, write_new
from .scorer import Scorer
from .scoring_scope import ScoringSource
from .telemetry_auth import MAX_WIRE_RECORD, SpoolVerifier

POLICY = "d14-private-development-craft/1"


def authenticated_begins(path, authority, inspection):
    """Retain actual signed headers, never invent a timestamp or event sequence."""
    begins, count, hasher = {}, 0, hashlib.sha256()
    with Path(path).open("rb") as stream, SpoolVerifier(authority) as verifier:
        while line := stream.readline(MAX_WIRE_RECORD + 1):
            hasher.update(line)
            event = GameEvent.model_validate_json(verifier.verify(line))
            count += 1
            require(count <= 1_000_000, "TELEMETRY_QUOTA_EXHAUSTED")
            require((event.campaign_id, event.epoch, event.server_boot_id) ==
                    (inspection["campaign_id"], inspection["epoch"], inspection["server_boot_id"]),
                    "DEVELOPMENT_SOURCE_CHANGED")
            if event.kind == "craft_begin":
                tx = event.payload["transaction_id"]
                require(tx not in begins, "TELEMETRY_CRAFT_DUPLICATE")
                begins[tx] = event
        verifier.receipt(inspection["server_boot_id"], count)
    require(hasher.hexdigest() == inspection["spool_sha256"], "DEVELOPMENT_SOURCE_CHANGED")
    return begins


def build_report(database, instance, spool):
    """Recompute private source admission before every idempotent publication.

    The existing importer remains unscorable. This explicit development adapter
    feeds only its accepted witnesses to the existing development scorer in a
    distinct instance namespace. Neither operator booleans nor report JSON are
    accepted as an alternative input to the authenticated spool and sealed plan.
    """
    store = CraftReferenceStore(database)
    _, plan, authority, _ = store._load(instance)
    require(isinstance(plan, CraftReferencePlanV3), "DEVELOPMENT_HISTORY_REQUIRED")
    inspection = store.inspect(instance, spool)
    begins = authenticated_begins(spool, authority, inspection)
    accepted = inspection["accepted_resource_witnesses"]
    require(not accepted or inspection["native_mutation_history"]["observed_history_clear"],
            "DEVELOPMENT_HISTORY_TAINTED")
    source_refs = [inspection["setup_digest"], inspection["authority_digest"],
                   inspection["spool_sha256"], digest(inspection)]
    events = []
    for witness in accepted:
        tx = witness["transaction_id"]
        begin = begins.get(tx)
        require(begin is not None and begin.actor_ids == [witness["actor_id"]]
                and begin.server_tick == witness["server_tick"]
                and begin.payload["recipe_id"] == witness["recipe_id"], "DEVELOPMENT_SOURCE_CHANGED")
        # This means the sealed development candidate checks passed, not that
        # complete setup authority/isolation was established. Both remain false.
        payload = {k: witness[k] for k in ("transaction_id", "recipe_id", "item_id", "count", "consumed")}
        payload.update(team_id=plan.team_id, source="craft", expert_mode=plan.predicate.expert_mode,
                       valid_setup=True)
        events.append(GameEvent.model_validate(begin.model_dump(by_alias=True) | {
            "kind": "craft", "payload_schema": "strata/CraftEvent/1", "payload": payload}))

    scorer = Scorer(database)
    scoped = "m0dev-" + digest({"instance": instance, "policy": POLICY})
    scorer.register_source(scoped, plan.predicate, ScoringSource(
        campaign_id=plan.campaign_id, epoch=plan.epoch, server_boot_id=inspection["server_boot_id"],
        evidence_kind=plan.evidence_kind, evidence_sha256=source_refs))
    state = {"complete": False, "output": 0, "scoring_authority_qualified": False}
    for event in events:
        state = scorer.score(scoped, plan.predicate, event)
    require(state["complete"] == inspection["candidate_complete"], "DEVELOPMENT_PREDICATE_MISMATCH")
    result = {"schema": "strata/PrivateDevelopmentMilestone/1", "policy": POLICY,
        "scope_decision": "D14", "visibility": "evaluator", "instance_id": instance,
        "scorer_instance": scoped, "campaign_id": plan.campaign_id, "epoch": plan.epoch,
        "server_boot_id": inspection["server_boot_id"], "evidence_kind": plan.evidence_kind,
        "source_digests": {key: inspection[key] for key in
            ("setup_digest", "authority_digest", "spool_sha256")} | {"inspection_sha256": digest(inspection)},
        "predicate_digest": inspection["predicate_digest"],
        "development_predicate_complete": state["complete"], "development_output": state["output"],
        "derived_events": [event.model_dump(by_alias=True) for event in events],
        "rejected_resource_witnesses": inspection["rejected_resource_witnesses"],
        "declared_history": inspection["native_mutation_history"],
        "required_history_policy": plan.required_history_policy,
        "scoring_eligible": False, "scoring_authority_qualified": False,
        "setup_mechanics_qualified": False, "isolation_qualified": False,
        "scientific_claim": False, "campaign_admission": False, "G0": "fail"}
    with database.transaction() as db:
        db.execute("CREATE TABLE IF NOT EXISTS development_milestone_reports "
                   "(instance TEXT PRIMARY KEY, digest TEXT, body TEXT)")
        old = db.execute("SELECT digest,body FROM development_milestone_reports WHERE instance=?",
                         (scoped,)).fetchone()
        if old:
            require(old["digest"] == digest(result) and old["body"] == canonical(result).decode(),
                    "DEVELOPMENT_REPORT_CONFLICT")
        else:
            db.execute("INSERT INTO development_milestone_reports VALUES (?,?,?)",
                       (scoped, digest(result), canonical(result).decode()))
            database.event(db, "private.development_milestone", result)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--instance", required=True)
    parser.add_argument("--spool", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    database = Database(private_path(args.database))
    try:
        _, plan, _, authority = CraftReferenceStore(database)._load(args.instance)
        output = private_path(args.output)
        require(not output.is_relative_to(private_path(plan.game_directory))
                and not output.is_relative_to(authority.parent), "CRAFT_PRIVATE_PATH")
        require(not output.exists(), "CRAFT_REPORT_EXISTS")
        report = build_report(database, args.instance, private_path(args.spool))
        write_new(output, {"schema": "strata/ReportArtifact/1", "content_digest": digest(report), "report": report})
        print(json.dumps({"status": "built", "visibility": "evaluator", "digest": digest(report),
                          "scoring_authority_qualified": False}))
    finally:
        database.close()


if __name__ == "__main__":
    main()
