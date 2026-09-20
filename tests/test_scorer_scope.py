"""Synthetic trust-boundary controls; no authentic telemetry authority claim."""

import pytest

from mcbench.records import GameEvent
from mcbench.storage import Fault, canonical, digest
from strata_evaluator.scorer import Scorer
from strata_evaluator.scoring_scope import ScoringSource
from test_evaluator import craft, predicate, register


def change(event, **updates):
    return GameEvent.model_validate(event.model_dump() | updates)


def counts(database):
    with database.transaction() as db:
        return {name: db.execute(f"SELECT count(*) FROM {name}").fetchone()[0]
                for name in ("game_events", "predicate_state", "scored_transactions",
                             "scored_transaction_receipts", "scorer_scopes", "scorer_sources")}


def test_no_implicit_registration_from_first_event(example, database):
    scorer = Scorer(database)
    before = counts(database)
    with pytest.raises(Fault, match="SCORER_SOURCE_UNREGISTERED"):
        scorer.score("i", predicate(), craft(example))
    assert counts(database) == before


@pytest.mark.parametrize("changed,code", [
    ({"campaign_id": "unrelated"}, "SCORER_CAMPAIGN_MISMATCH"),
    ({"server_boot_id": "unregistered"}, "SCORER_SOURCE_UNREGISTERED"),
    ({"epoch": 2}, "SCORER_SOURCE_UNREGISTERED"),
])
def test_foreign_sources_cannot_complete_or_modify_partial_score(example, database, changed, code):
    scorer = Scorer(database)
    p = predicate().model_copy(update={"minimum_output": 8})
    event = craft(example)
    register(scorer, "i", p, event)
    assert not scorer.score("i", p, event)["complete"]
    before = counts(database)
    with pytest.raises(Fault, match=code):
        scorer.score("i", p, change(craft(example, 2), **changed))
    assert counts(database) == before
    assert scorer.score("i", p, craft(example, 2))["output"] == 8


@pytest.mark.parametrize("patch", [{"count": 8}, {"source": "gift"}, {"consumed": {}},
                                  {"team_id": "other"}])
def test_changed_transaction_conflicts_after_restart_even_when_complete(example, database, patch):
    scorer = Scorer(database)
    event, p = craft(example), predicate()
    register(scorer, "i", p, event)
    state = scorer.score("i", p, event)
    restored = change(event, epoch=2, server_boot_id="restart")
    register(scorer, "i", p, restored)
    assert Scorer(database).score("i", p, restored) == state
    before = counts(database)
    with pytest.raises(Fault, match="SCORER_TRANSACTION_CONFLICT"):
        scorer.score("i", p, change(restored, server_event_seq=2, payload=event.payload | patch))
    assert counts(database) == before
    assert state["output"] == 4 and state["evidence_kind"] == "synthetic"
    assert state["scoring_authority_qualified"] is False


def test_completed_score_still_records_later_receipt_conflicts(example, database):
    scorer, p = Scorer(database), predicate()
    register(scorer, "i", p, craft(example))
    scorer.score("i", p, craft(example))
    assert scorer.score("i", p, craft(example, 2))["output"] == 4
    changed = change(craft(example, 2, count=8), server_event_seq=3)
    with pytest.raises(Fault, match="SCORER_TRANSACTION_CONFLICT"):
        scorer.score("i", p, changed)


def test_instance_scope_and_boot_are_shared_across_predicates(example, database):
    scorer, p, event = Scorer(database), predicate(), craft(example)
    register(scorer, "i", p, event)
    other = p.model_copy(update={"predicate_id": "other"})
    before = counts(database)
    with pytest.raises(Fault, match="SCORER_SCOPE_CHANGED"):
        register(scorer, "i", other, change(event, campaign_id="foreign"))
    with pytest.raises(Fault, match="SCORER_SOURCE_CHANGED"):
        register(scorer, "i", other, change(event, server_boot_id="other"))
    assert counts(database) == before
    assert register(scorer, "i", other, event)["duplicate"]
    assert scorer.score("i", other, event)["complete"]


def test_source_registration_is_immutable_and_monotone(example, database):
    scorer, p, event = Scorer(database), predicate(), craft(example)
    receipt = register(scorer, "i", p, event)
    assert receipt["qualified"] is False
    assert register(scorer, "i", p, event)["duplicate"]
    later = change(event, epoch=3, server_boot_id="third")
    register(scorer, "i", p, later)
    with pytest.raises(Fault, match="STALE_EPOCH"):
        register(scorer, "i", p, change(event, epoch=2, server_boot_id="second"))
    with pytest.raises(Fault, match="SCORER_SOURCE_CHANGED"):
        register(scorer, "i", p, change(event, epoch=4))
    source = ScoringSource(campaign_id=event.campaign_id, epoch=event.epoch,
        server_boot_id=event.server_boot_id, evidence_kind="synthetic", evidence_sha256=["b" * 64])
    with pytest.raises(Fault, match="SCORER_SOURCE_CHANGED"):
        scorer.register_source("i", p, source)
    with pytest.raises(Fault, match="SCORER_SCOPE_CHANGED"):
        scorer.register_source("i", p, source.model_copy(update={"evidence_kind": "authentic_operator_reference"}))


def test_predicate_cannot_change_after_registration_before_any_score(example, database):
    scorer, p, event = Scorer(database), predicate(), craft(example)
    register(scorer, "i", p, event)
    changed = p.model_copy(update={"minimum_output": 1})
    with pytest.raises(Fault, match="PREDICATE_CHANGED"):
        scorer.score("i", changed, event)
    with pytest.raises(Fault, match="PREDICATE_CHANGED"):
        register(scorer, "i", changed, event)


def test_legacy_unbound_history_is_preserved_and_cannot_be_relabelled(example, database):
    scorer, p = Scorer(database), predicate()
    with database.transaction() as db:
        db.execute("INSERT INTO predicate_state VALUES (?,?,?,?)",
                   ("i", p.predicate_id, digest(p.model_dump()), canonical({"complete": True}).decode()))
        db.execute("INSERT INTO scored_transactions VALUES (?,?,?)", ("i", p.predicate_id, "old"))
    before = counts(database)
    with pytest.raises(Fault, match="SCORER_UNBOUND_HISTORY"):
        register(scorer, "i", p, craft(example))
    assert counts(database) == before


def test_public_style_text_and_raw_native_callback_remain_unscorable(example, database):
    scorer, p, event = Scorer(database), predicate(), craft(example)
    register(scorer, "i", p, event)
    for schema, kind, payload in [("text", "success", {"complete": True}),
                                  ("strata/RawCraftCallback/1", "craft_callback", {})]:
        with pytest.raises(Fault, match="SCHEMA_UNSUPPORTED"):
            scorer.score("i", p, change(event, payload_schema=schema, kind=kind, payload=payload))
    assert counts(database)["game_events"] == 0
