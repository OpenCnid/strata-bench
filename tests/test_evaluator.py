import pytest

from mcbench.records import EvaluationResult, GameEvent
from mcbench.storage import Fault, digest
from strata_evaluator.analysis import common_support_area, holm, paired_report, plan_sample
from strata_evaluator.probes import BASE_FIELDS, identity_decision, matched_pair
from strata_evaluator.scorer import Predicate, Scorer


def result(example, lineage, pair, arm, success):
    return EvaluationResult.model_validate(example("EvaluationResult") | {
        "result_id": f"{pair}:{arm}", "lineage_id": lineage, "pair_id": pair, "arm": arm,
        "outcome": "success" if success else "failure", "success": success,
        "event_observed": success, "censor_reason": None, "validity_flags": []})


def test_paired_lineage_weighting_missingness_and_replay(example):
    assignments = {f"l{i}": {"craft": [f"p{i}c"], "machine": [f"p{i}m"]} for i in range(1, 4)}
    results = []
    for i in (1, 2):
        for family in ("c", "m"):
            for arm in ("experienced", "initial"):
                results.append(result(example, f"l{i}", f"p{i}{family}", arm, arm == "experienced"))
    report = paired_report(assignments, {"craft": 1, "machine": 3}, results,
                           protocol_id="ep1", checkpoint_id="cp1", seed=9)
    assert report["gain"] == report["experienced"] == 1
    assert report["initial"] == 0 and report["complete_lineages"] == 2
    assert report["missing_lineages"] == ["l3"]
    assert report["attrition_bounds"] == [1 / 3, 1]
    assert report["percentile_95_ci"] == [1, 1]
    again = paired_report(assignments, {"craft": 1, "machine": 3}, results + [results[0]],
                          protocol_id="ep1", checkpoint_id="cp1", seed=9)
    assert digest(report) == digest(again)
    with pytest.raises(Fault, match="DUPLICATE_ARM"):
        paired_report(assignments, {"craft": 1, "machine": 3}, results + [
            EvaluationResult.model_validate(results[0].model_dump() | {"result_id": "other"})],
            protocol_id="ep1", checkpoint_id="cp1")


def test_zero_gain_sanity_common_support_holm_power(example):
    results = [result(example, "l1", "p1", arm, True) for arm in ("experienced", "initial")]
    report = paired_report({"l1": {"craft": ["p1"]}}, {"craft": 1}, results,
                           protocol_id="ep1", checkpoint_id="cp1")
    assert report["gain"] == 0 and not report["confirmatory_claim"]
    assert common_support_area({"E": {0: 0, 10: 1, 20: 1}, "I": {0: 0, 10: 0}}) == {
        "times": [0, 10], "areas": {"E": .5, "I": 0}}
    assert holm({"a": .01, "b": .04, "c": .5}) == {"a": .03, "b": .08, "c": .5}
    assert plan_sample([-.2, .2, 0])["simulation_required"]


def test_unverified_identity_qualifies_observations_without_dropping_them(example):
    results = [EvaluationResult.model_validate(result(example, "l1", "p1", arm, True).model_dump()
               | {"validity_flags": ["provider_version_unverified"]})
               for arm in ("experienced", "initial")]
    report = paired_report({"l1": {"craft": ["p1"]}}, {"craft": 1}, results,
                           protocol_id="ep1", checkpoint_id="cp1")
    assert report["complete_lineages"] == 1 and report["gain"] == 0
    assert report["validity_flags"] == ["provider_version_unverified"]
    assert not report["confirmatory_claim"]


def predicate(kind="craft"):
    return Predicate(predicate_id="p1", kind=kind, team_id="team1", actors=["a1"],
        recipes=["minecraft:planks", "minecraft:alternate"], item_id="minecraft:oak_planks",
        minimum_output=4, ingredients={"minecraft:oak_log": 1}, sustained_ticks=40,
        require_energy=True, require_fluid=True, expert_mode=True)


def craft(example, seq=1, **patch):
    return GameEvent.model_validate(example("GameEvent") | {"is_example": False,
        "server_event_seq": seq, "kind": "craft", "actor_ids": ["a1"],
        "payload_schema": "strata/CraftEvent/1", "payload": {"transaction_id": f"tx{seq}",
            "team_id": "team1", "recipe_id": "minecraft:planks", "item_id": "minecraft:oak_planks",
            "count": 4, "consumed": {"minecraft:oak_log": 1}, "source": "craft", "expert_mode": True,
            "valid_setup": True} | patch})


@pytest.mark.parametrize("patch", [{"source": "gift"}, {"source": "admin"}, {"consumed": {}},
    {"expert_mode": False}, {"team_id": "other"}, {"valid_setup": False},
    {"recipe_id": "minecraft:wrong"}, {"item_id": "minecraft:wrong"}])
def test_private_scorer_negative_controls(example, database, patch):
    assert not Scorer(database).score("instance1", predicate(), craft(example, **patch))["complete"]


def test_scorer_alternates_dedup_restore_and_schema_rejection(example, database):
    scorer = Scorer(database)
    p = predicate()
    event = craft(example, recipe_id="minecraft:alternate")
    assert scorer.score("i", p, event)["complete"]
    assert scorer.score("i", p, event)["output"] == 4
    restored = GameEvent.model_validate(event.model_dump() | {"server_boot_id": "new-boot", "epoch": 2})
    assert scorer.score("i", p, restored)["output"] == 4
    with pytest.raises(Fault, match="IDEMPOTENCY_CONFLICT"):
        scorer.score("i", p, craft(example))
    with pytest.raises(Fault, match="SCHEMA_UNSUPPORTED"):
        scorer.score("i", p, GameEvent.model_validate(event.model_dump() | {"payload_schema": "fake/v1"}))


def test_machine_requires_contiguous_operating_window(example, database):
    scorer = Scorer(database)
    def event(seq, start, end, **patch):
        return GameEvent.model_validate(example("GameEvent") | {"is_example": False,
            "server_event_seq": seq, "server_tick": end, "actor_ids": ["a1"], "kind": "machine",
            "payload_schema": "strata/MachineEvent/1", "payload": {
                "transaction_id": f"tx{seq}", "team_id": "team1", "machine_id": "machine1",
                "recipe_id": "minecraft:planks", "item_id": "minecraft:oak_planks",
                "interval_start": start, "interval_end": end, "output_count": 2,
                "energy_consumed": 10, "fluid_consumed": 1, "source": "machine",
                "expert_mode": True, "valid_setup": True} | patch})
    assert not scorer.score("i", predicate("machine"), event(1, 0, 20))["complete"]
    assert not scorer.score("i", predicate("machine"), event(2, 20, 40, energy_consumed=0))["complete"]
    assert not scorer.score("i", predicate("machine"), event(3, 40, 60))["complete"]
    assert scorer.score("i", predicate("machine"), event(4, 60, 80))["complete"]


def test_matched_clones_probe_taint_and_drift_quarantine():
    base = dict.fromkeys(BASE_FIELDS, "same-ref")
    initial = {"notes": {"content": "initial-ref", "origin": "initial"}}
    experienced = {"notes": {"content": "learned-ref", "origin": "campaign"}}
    pair = matched_pair(base, initial, experienced, allowed_kinds={"notes"})
    assert not pair["campaign_feedback_allowed"] and not pair["executed"]
    with pytest.raises(Fault, match="T0_NOT_MATCHED"):
        matched_pair(base, initial, experienced, allowed_kinds={"notes"}, t0=True)
    with pytest.raises(Fault, match="PROBE_IMPORT"):
        matched_pair(base, initial, {"notes": {"content": "probe-ref", "origin": "probe"}},
                     allowed_kinds={"notes"})
    drift = identity_decision("s", "s", "old", "new", immutable=True,
                              last_verified_cursor=10, current_cursor=20)
    assert drift["quarantine_after"] == 10 and drift["retain_costs"] and drift["revoke_grants"]
    unknown = identity_decision("s", "s", None, None, immutable=False,
                               last_verified_cursor=0, current_cursor=20)
    assert not unknown["fixed_model_claim"]
