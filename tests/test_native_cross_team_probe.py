"""Bounded separate-job probe controls; actual native evidence is separate."""

import importlib
import json
from pathlib import Path

import pytest

from mcbench.storage import Fault


@pytest.fixture
def m(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / "tools"))
    return importlib.import_module("native_cross_team_probe")


def request(actor, thread):
    return {
        "client_metadata": {
            "x-codex-turn-metadata": json.dumps(
                {
                    "agent_name": actor,
                    "thread_id": thread,
                    "session_id": "root-session",
                    "turn_id": "turn-one",
                }
            )
        },
        "input": [],
    }


def ready(m):
    c = m.CrossTeamCoordinator()
    for team in m.TEAMS:
        for actor in m.ACTORS:
            c.record(team, actor, request(actor, team + "-" + actor.rsplit("/", 1)[-1]))
        c.mark("ready", team, m.ROOT)
    return c


def test_known_foreign_targets_require_both_ready_jobs(m):
    c = m.CrossTeamCoordinator()
    with pytest.raises(Fault, match="CROSS_TEAM_NOT_READY"):
        c.targets("alpha")
    c = ready(m)
    assert c.targets("alpha") == {
        "foreign_root": "beta-root",
        "foreign_helper": "beta-identity_child",
        "absent": m.MISSING,
    }


@pytest.mark.parametrize("change", ["changed", "collision", "absent"])
def test_identity_cannot_change_collide_or_equal_missing_control(m, change):
    c = ready(m)
    thread = {"changed": "new", "collision": "beta-root", "absent": m.MISSING}[change]
    with pytest.raises(Fault):
        c.record("alpha", m.ROOT, request(m.ROOT, thread))


def test_matrix_uses_actual_foreign_ids_and_absent_control_for_all_methods(m):
    c = ready(m)
    p = m.CrossTeamProbe(c, "alpha")
    calls = p.attacks(m.ROOT, "one")
    assert len(calls) == 9 and len({x["call_id"] for x in calls}) == 9
    for call in calls:
        args = json.loads(call["arguments"])
        assert args["target"] in c.targets("alpha").values()
        assert call["name"] in m.METHODS
        assert ("message" in args) is (call["name"] != "interrupt_agent")
    with pytest.raises(Fault, match="CROSS_TEAM_OUTPUT_MISSING"):
        p.require_attempt_outputs(m.ROOT)


def test_all_four_actual_actors_required_before_release(m):
    c = ready(m)
    for team, actor in [("alpha", m.ROOT), ("alpha", m.CHILD), ("beta", m.ROOT)]:
        c.mark("attempts_observed", team, actor)
    assert not c.all_attempts_observed()
    c.mark("attempts_observed", "beta", m.CHILD)
    assert c.all_attempts_observed()


def test_unknown_denial_is_never_automatic_pass(m):
    p = m.CrossTeamProbe(ready(m), "alpha")
    assert p.report()["checks"]["cross_exact_denials_reviewed"] is False


def test_wrong_peer_canary_in_any_request_fails(m):
    c = ready(m)
    p = m.CrossTeamProbe(c, "alpha")
    p.requests = [{"body": {"payload": c.canaries["beta"]}, "actor": m.ROOT}]
    assert p.report()["checks"]["cross_private_peer_marker_absent"] is False


def test_no_unbounded_wait(m):
    p = m.CrossTeamProbe(ready(m), "alpha")
    for i in range(5):
        p.wait(m.ROOT, str(i))
    with pytest.raises(Fault, match="CROSS_TEAM_DELIVERY_BOUND"):
        p.wait(m.ROOT, "six")


def test_nonselected_scope_refuses_before_creating_files(m, tmp_path):
    from native_mcp_identity_probe import run

    p = m.CrossTeamProbe(ready(m), "alpha")
    with pytest.raises(Fault, match="CROSS_TEAM_PROFILE_REQUIRED"):
        run(tmp_path / "missing", tmp_path / "new", cross_team_probe=p)
    assert not (tmp_path / "new").exists()


def review_fixture(m):
    ids = {team: {actor: str(m.uuid.uuid4()) for actor in m.ACTORS} for team in m.TEAMS}
    expected = {
        "foreign_root": ids["beta"][m.ROOT],
        "foreign_helper": ids["beta"][m.CHILD],
        "absent": m.MISSING,
    }
    report = {
        "team": "alpha",
        "targets": dict.fromkeys(m.ACTORS, expected),
        "calls": {},
        "outputs": {},
    }
    for actor in m.ACTORS:
        for kind, target in expected.items():
            for method in m.METHODS:
                key = actor + kind + method
                report["calls"][key] = {"actor": actor, "phase": kind + "_" + method}
                report["outputs"][key] = "agent with id " + target + " not found"
    return report, ids


def test_exact_denial_review_still_has_no_campaign_team_authority(m):
    result = m.review_denials(*review_fixture(m))
    assert (
        result["checked"] == 18
        and result["foreign_denials"] == 12
        and result["absent_controls"] == 6
    )
    assert result["campaign_team_api_qualified"] is False


@pytest.mark.parametrize(
    "change",
    ["unknown", "success", "missing", "duplicate", "actor", "target", "identity", "colliding"],
)
def test_exact_review_rejects_weak_or_mismatched_evidence(m, change):
    report, ids = review_fixture(m)
    key = next(iter(report["calls"]))
    if change == "unknown":
        report["outputs"][key] = "unrelated failure"
    if change == "success":
        report["outputs"][key] = "message delivered"
    if change == "missing":
        report["calls"].pop(key)
    if change == "duplicate":
        report["calls"]["duplicate"] = report["calls"][key]
    if change == "actor":
        report["calls"][key]["actor"] = "/wrong"
    if change == "target":
        report["targets"][m.ROOT] = {}
    if change == "identity":
        ids["alpha"][m.ROOT] = "malformed"
    if change == "colliding":
        ids["alpha"][m.ROOT] = ids["beta"][m.ROOT]
    with pytest.raises(Fault):
        m.review_denials(report, ids)


def test_coordinator_times_fit_canonical_json_domain(m):
    from mcbench.storage import canonical

    c = ready(m)
    assert canonical(c.timeline) and all(type(x["at_unix_ms"]) is int for x in c.timeline)
