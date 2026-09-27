"""Synthetic scenario/verifier tests, never authentic game or runtime evidence."""

import importlib
import json

import pytest

from mcbench.storage import Fault
from test_native_team_channel_probe import m, store, complete
from test_native_broker_canaries import deferred_fixture
from test_native_runtime_boundary import output_fixture

__all__ = ["m", "store"]


@pytest.fixture
def candidate(m, store, tmp_path):
    module = importlib.import_module("native_campaign_boundary_probe")
    output = tmp_path / "native"
    output.mkdir()
    descriptor = {"url": "http://127.0.0.1:12345/v1/game", "token": "owned-worker-canary",
                  "campaign_id": store.campaign_id, "agent_id": "a1", "epoch": 1}
    probe = module.CampaignBoundaryProbe(store, "sender", descriptor, "owned-lease", output)
    try:
        yield probe
    finally:
        probe.boundary.close()


def fill_positive(probe, m, store, monkeypatch):
    team = complete(m, store, "sender")
    probe.calls, probe.outputs, probe.finished = team.calls, team.outputs, team.finished
    probe.boundary_phases = dict.fromkeys(m.ACTORS, 2)
    outputs, direct = deferred_fixture()
    for item in outputs[:2]:
        for part in item["output"]:
            value = json.loads(part["text"])
            if value["probe"] == "catalog":
                value["names"].remove("apply_patch")
                value["names"].append("mcp__strata_broker__team")
            if value["probe"].startswith("patch_") or value["probe"] == "outside_patch":
                value["error"] = "TypeError: tools.apply_patch is not a function"
            part["text"] = json.dumps(value)
    probe.direct["shell"] = direct
    for item in output_fixture(monkeypatch):
        item["call_id"] += "-runtime"
        outputs.append(item)
    for actor in m.ACTORS:
        for kind, output in (("patch", "unsupported custom tool call: apply_patch"),
                             ("patch_function", "unsupported call: apply_patch")):
            key = actor + "-" + kind
            probe.direct[kind].append(key)
            outputs.append({"call_id": key, "native_agent": actor, "output": output})
    for item in outputs:
        key = item["call_id"]
        probe.calls[key] = {"actor": item["native_agent"], "phase": "boundary"}
        probe.outputs[key] = item["output"]
    path = probe.boundary.credential_path
    path.parent.mkdir()
    path.write_text('STRATA_SYNTHETIC_OAUTH_ACCESS', encoding='utf-8')


def test_combined_positive_and_real_game_label_stays_separate(candidate, m, store, monkeypatch):
    fill_positive(candidate, m, store, monkeypatch)
    report = candidate.report()
    assert all(report["checks"].values()), report["checks"]
    assert report["controller_readiness"] == "synthetic" and report["runtime_qualified"] is False
    assert report["simultaneous_body_capacity_qualified"] is False
    assert report["provider"] == "scripted"


@pytest.mark.parametrize("mutation", ["missing-helper", "tool-widening", "shell-success", "patch-success",
    "worker-leak", "private-leak", "network-hit", "missing-auth-target", "changed-private-file", "missing-private-file", "phase-skipped"])
def test_integration_report_cannot_hide_missing_or_failed_routes(candidate, m, store, monkeypatch, mutation):
    fill_positive(candidate, m, store, monkeypatch)
    if mutation == "missing-helper":
        key = next(k for k, c in candidate.calls.items() if c["actor"] == m.CHILD and k.endswith("-runtime"))
        del candidate.outputs[key]
    elif mutation == "tool-widening":
        value = json.loads(candidate.outputs["root"][0]["text"])
        value["names"].append("mcp__strata_broker__admin")
        candidate.outputs["root"][0]["text"] = json.dumps(value)
    elif mutation in {"shell-success", "patch-success"}:
        candidate.outputs[candidate.direct["shell" if mutation == "shell-success" else "patch"][0]] = "executed"
    elif mutation in {"worker-leak", "private-leak"}:
        candidate.requests.append({"actor": m.ROOT, "body": candidate.game.descriptor["token"] if
            mutation == "worker-leak" else candidate.boundary.secrets["module"]})
    elif mutation == "network-hit":
        candidate.boundary.unauthorized.append("/unexpected")
    elif mutation == "missing-auth-target":
        candidate.boundary.credential_path.unlink()
    elif mutation == "changed-private-file":
        candidate.boundary.protected.write_text("changed", encoding="utf-8")
    elif mutation == "missing-private-file":
        candidate.boundary.protected.unlink()
    else:
        candidate.boundary_phases[m.CHILD] = 1
    assert not all(candidate.report()["checks"].values())


def test_missing_heartbeat_closes_owned_listener_and_cannot_rearm(candidate):
    with pytest.raises(Fault, match="TEAM_FIXTURE_HEARTBEAT"):
        candidate.__enter__()
    assert not candidate.boundary.thread.is_alive()
    with pytest.raises(Fault, match="CAMPAIGN_BOUNDARY_REARM"):
        candidate.__enter__()


def test_sequence_preserves_canary_identity_and_helper_wait_bound(candidate, m):
    for actor in m.ACTORS:
        first = candidate.next(actor, 1, actor + "-boundary")
        assert json.dumps(str(candidate.boundary.credential_path)) in first[0]["input"]
        assert candidate.game.descriptor["token"] not in first[0]["input"]
        direct = candidate.next(actor, 2, actor + "-direct")
        assert [c["name"] for c in direct] == ["exec_command", "apply_patch", "apply_patch"]
    assert candidate.next(m.ROOT, 3, "spawn")[0]["name"] == "spawn_agent"
    for index in range(4):
        assert candidate.next(m.ROOT, index + 4, "wait" + str(index))[0]["name"] == "wait_agent"
    with pytest.raises(Fault, match="TEAM_FIXTURE_DELIVERY_BOUND"):
        candidate.next(m.ROOT, 8, "excess")


@pytest.mark.parametrize("change", [{"agent_id": "a2"}, {"campaign_id": "other"}, {"epoch": 2}])
def test_worker_scope_must_match_declared_roster_before_canary_creation(candidate, store, tmp_path, change):
    module = importlib.import_module("native_campaign_boundary_probe")
    with pytest.raises(Fault, match="CAMPAIGN_BOUNDARY_GAME_SCOPE"):
        module.CampaignBoundaryProbe(store, "sender", candidate.game.descriptor | change,
                                     "owned-lease", tmp_path / "absent")


@pytest.mark.parametrize("changes", [{"model": "gpt-5.6-luna"}, {"gateway_mode": True}, {"game_probe": object()},
    {"job_id": "wrong"}, {"team_channel_probe": object()}, {"runtime_boundary": True}, {"oauth_mode": False}])
def test_combined_mode_rejects_ambiguous_profiles_before_launch(candidate, changes):
    module = importlib.import_module("native_mcp_identity_probe")
    args = dict(broker_mode=True, admission_mode=True, bootstrap_mode=True, ingress_mode=True, oauth_mode=True,
        campaign_boundary_probe=candidate, model="gpt-6-luna", job_id=candidate.job_id,
        tool_projections={}, no_patch_catalog=candidate.output / "missing-catalog.json") | changes
    with pytest.raises(Fault, match="CAMPAIGN_BOUNDARY_PROFILE_REQUIRED"):
        module.run(candidate.output / "absent.exe", candidate.output, **args)
