"""Private development source bindings; registration is not authentication.

Only the operator/evaluator may register sources. The durable mapping prevents
cross-run credit and changed transaction replays. It cannot establish deployment
isolation, setup/team provenance or authentic scoring authority by declaration.
"""

from typing import Literal

from pydantic import Field, TypeAdapter

from mcbench.contracts import Digest, Id, Strict
from mcbench.storage import canonical, digest, require


class ScoringSource(Strict):
    campaign_id: Id
    epoch: int = Field(ge=1, le=9007199254740991)
    server_boot_id: Id
    evidence_kind: Literal["synthetic", "authentic_operator_reference"]
    evidence_sha256: list[Digest] = Field(min_length=1, max_length=32)


def create_tables(db):
    db.execute("CREATE TABLE IF NOT EXISTS scorer_scopes (instance TEXT, predicate TEXT, "
               "spec TEXT, campaign TEXT, evidence_kind TEXT, PRIMARY KEY(instance,predicate))")
    db.execute("CREATE TABLE IF NOT EXISTS scorer_sources (instance TEXT, "
               "epoch INTEGER, boot TEXT, digest TEXT, body TEXT, "
               "PRIMARY KEY(instance,epoch), UNIQUE(instance,boot))")
    db.execute("CREATE TABLE IF NOT EXISTS scored_transaction_receipts (instance TEXT, "
               "predicate TEXT, transaction_id TEXT, digest TEXT, "
               "PRIMARY KEY(instance,predicate,transaction_id))")


def register_source(database, instance, predicate, source: ScoringSource):
    """Bind before scoring; never infer an instance's authority from an event."""
    TypeAdapter(Id).validate_python(instance)
    require(predicate.actors and len(set(predicate.actors)) == len(predicate.actors),
            "SCORER_ACTORS_INVALID")
    source = ScoringSource.model_validate(source)
    spec = digest(predicate.model_dump())
    source_digest = digest(source.model_dump())
    with database.transaction() as db:
        instance_scopes = db.execute("SELECT campaign,evidence_kind FROM scorer_scopes WHERE instance=?",
                                     (instance,)).fetchall()
        require(all((row["campaign"], row["evidence_kind"]) ==
                    (source.campaign_id, source.evidence_kind) for row in instance_scopes),
                "SCORER_SCOPE_CHANGED")
        scope = db.execute("SELECT * FROM scorer_scopes WHERE instance=? AND predicate=?",
                           (instance, predicate.predicate_id)).fetchone()
        if scope:
            require(scope["spec"] == spec, "PREDICATE_CHANGED")
            require((scope["campaign"], scope["evidence_kind"]) ==
                    (source.campaign_id, source.evidence_kind), "SCORER_SCOPE_CHANGED")
        else:
            # Old state has no reliable source binding or transaction-content
            # receipt. Retain it and require explicit migration qualification.
            for table in ("predicate_state", "scored_transactions", "scored_transaction_receipts"):
                require(db.execute(f"SELECT 1 FROM {table} WHERE instance=? AND predicate=?",
                                   (instance, predicate.predicate_id)).fetchone() is None,
                        "SCORER_UNBOUND_HISTORY")
            db.execute("INSERT INTO scorer_scopes VALUES (?,?,?,?,?)",
                       (instance, predicate.predicate_id, spec, source.campaign_id, source.evidence_kind))
            database.event(db, "private.scorer_scope", {"instance": instance,
                           "predicate": predicate.predicate_id, "spec": spec,
                           "campaign": source.campaign_id, "evidence_kind": source.evidence_kind,
                           "authority": "operator_registration", "qualified": False})
        previous = db.execute("SELECT * FROM scorer_sources WHERE instance=? "
                              "AND (epoch=? OR boot=?)",
                              (instance, source.epoch, source.server_boot_id)).fetchall()
        if previous:
            require(len(previous) == 1 and previous[0]["digest"] == source_digest,
                    "SCORER_SOURCE_CHANGED")
            return {"registered": True, "duplicate": True, "source_digest": source_digest,
                    "authority": "operator_registration", "qualified": False}
        highest = db.execute("SELECT MAX(epoch) FROM scorer_sources WHERE instance=?",
                             (instance,)).fetchone()[0]
        require(highest is None or source.epoch > highest, "STALE_EPOCH")
        db.execute("INSERT INTO scorer_sources VALUES (?,?,?,?,?)",
                   (instance, source.epoch, source.server_boot_id,
                    source_digest, canonical(source.model_dump()).decode()))
        database.event(db, "private.scorer_source", {"instance": instance,
                       "predicate": predicate.predicate_id, "source": source.model_dump(),
                       "authority": "operator_registration", "qualified": False})
    return {"registered": True, "duplicate": False, "source_digest": source_digest,
            "authority": "operator_registration", "qualified": False}


def require_source(db, instance, predicate, event):
    scope = db.execute("SELECT * FROM scorer_scopes WHERE instance=? AND predicate=?",
                       (instance, predicate.predicate_id)).fetchone()
    require(scope is not None, "SCORER_SOURCE_UNREGISTERED")
    require(scope["spec"] == digest(predicate.model_dump()), "PREDICATE_CHANGED")
    require(scope["campaign"] == event.campaign_id, "SCORER_CAMPAIGN_MISMATCH")
    source = db.execute("SELECT 1 FROM scorer_sources WHERE instance=? "
                        "AND epoch=? AND boot=?",
                        (instance, event.epoch, event.server_boot_id)).fetchone()
    require(source is not None, "SCORER_SOURCE_UNREGISTERED")
    return scope["evidence_kind"]


def record_transaction(db, instance, predicate, event, transaction_id):
    """Allow a restored receipt only if its semantic content is identical.

    Boot/epoch/event sequence can change in a declared replay. Actor identities,
    event kind and complete payload cannot. No duplicate contributes twice.
    """
    content = digest({"kind": event.kind, "schema": event.payload_schema,
                      "actors": event.actor_ids, "payload": event.payload})
    previous = db.execute("SELECT digest FROM scored_transaction_receipts "
                          "WHERE instance=? AND predicate=? AND transaction_id=?",
                          (instance, predicate.predicate_id, transaction_id)).fetchone()
    if previous:
        require(previous[0] == content, "SCORER_TRANSACTION_CONFLICT")
        return True
    require(db.execute("SELECT 1 FROM scored_transactions "
                       "WHERE instance=? AND predicate=? AND transaction_id=?",
                       (instance, predicate.predicate_id, transaction_id)).fetchone() is None,
            "SCORER_UNBOUND_HISTORY")
    db.execute("INSERT INTO scored_transactions VALUES (?,?,?)",
               (instance, predicate.predicate_id, transaction_id))
    db.execute("INSERT INTO scored_transaction_receipts VALUES (?,?,?,?)",
               (instance, predicate.predicate_id, transaction_id, content))
    return False
