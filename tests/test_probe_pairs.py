"""Actual disk preparation with synthetic game/protocol/native source fixtures."""

import json
import os
from pathlib import Path

import pytest

from mcbench.storage import Fault, Principal, canonical
from strata_evaluator.probe_pairs import POLICY, ProbeFixture, ProbePairRequest, ProbePairs
from test_native_probe_projection import selection
from test_native_selected_activation import selected_seed

OPERATOR = Principal("operator", "operator")
EVALUATOR = Principal("evaluation:test", "evaluator")


@pytest.fixture
def pair_source(database, cas, tmp_path, example, configs, request):
    def operator_put(value):
        return cas.put(OPERATOR, "operator", "operator", canonical(value))
    inference = operator_put({"is_example": True, "effort": "low"})
    capability = operator_put({"is_example": True, "profile": "synthetic-structured"})
    information = operator_put({"is_example": True, "corpus": "public-only"})
    runtime_policy = operator_put({"is_example": True, "runtime": "restricted-native"})
    def resolved_configs(*args, **kwargs):
        config, agents = configs(*args, **kwargs)
        config = config.model_copy(update={"information_policy": information, "runtime_profile": runtime_policy,
            "backend": config.backend.model_copy(update={"capability_manifest": capability})})
        return config, [a.model_copy(update={"inference_config": inference, "capability_profile": capability}) for a in agents]
    options = getattr(request, "param", False)
    zero = options.get("zero", False) if isinstance(options, dict) else options
    arm = options.get("arm", "full") if isinstance(options, dict) else "full"
    def source_example(name):
        value = example(name)
        if zero and name == "CheckpointManifest":
            value |= {"scheduled_active_s": 0, "clocks": {"active_wall_s": 0, "elapsed_wall_s": 0, "avatar_ticks": 0}}
        return value
    source, sets, ref = selected_seed(database, cas, tmp_path, source_example, resolved_configs, arm=arm)
    _, config = sets.components.load(sets.load(ref)["checkpoint_ref"])
    def put(value):
        return cas.put(OPERATOR, EVALUATOR.namespace, "evaluator", canonical(value))
    lock = cas.put(OPERATOR, EVALUATOR.namespace, "evaluator", cas.read(OPERATOR, "operator", config.pack_lock))
    keymap = put({"is_example": True, "physical_keys": []})
    blob = put({"is_example": True, "fixture": "ordinary-state"})
    for reference in (information, runtime_policy):
        cas.put(OPERATOR, EVALUATOR.namespace, "evaluator", cas.read(OPERATOR, "operator", reference))
    fixture = {"schema": "strata/ProbeFixture/1", "is_example": True, "instance_id": "i1", "pack_lock": lock,
        "world_files": {"world/level.dat": blob, "external/teams.dat": blob}, "body_states": {"a1": blob},
        "keymaps": {"a1": keymap}, "control_cards": {"a1": blob}, "public_goal": "Explore the visible area.",
        **dict.fromkeys(("backend_initialization", "tools", "observation_action_limits"), blob),
        "runtime_policy": runtime_policy, "information_policy": information}
    chosen = {"a1": selection(sets, ref,
        retained_paths=[] if zero or arm == "frozen-persistence" else ["notes/root.md"],
        skill_names=[] if zero or arm in {"frozen-skills", "frozen-persistence"} else ["learned-crafting"])}
    protocol = example("EvaluationProtocol") | {"is_example": True, "system_digests": [config.system_digest],
        "exposure_s": [0, 3600], "primary_checkpoint_s": 3600, "control_keymap": keymap,
        **dict.fromkeys(("scorer", "sample_plan", "censoring_plan", "analysis_plan", "access_log"), blob)}
    if isinstance(options, dict) and "probe_spend" in options:
        protocol["probe_limits"] = protocol["probe_limits"] | {"spend_microusd": options["probe_spend"]}
    service = ProbePairs(sets, EVALUATOR.namespace)
    def request(*, fixture_patch=None, selection_patch=None, protocol_patch=None, pair_id="p1"):
        f = fixture | (fixture_patch or {})
        fref = put(f)
        selections = chosen | (selection_patch or {})
        p = protocol | {"sealed_instances": put({"schema": "strata/ProbeInstanceIndex/1", "instances": {f["instance_id"]: fref}}),
            "artifact_projection": put({"schema": "strata/ProbeSelectionIndex/1", "selections": {pair_id: selections}}),
            "randomization_plan": put({"schema": "strata/ProbeOrderIndex/1", "orders": {pair_id: ["initial", "experienced"]}})} | (protocol_patch or {})
        return {"schema": "strata/ProbePairRequest/1", "policy": POLICY, "is_example": True, "pair_id": pair_id,
            "protocol_ref": put(p), "fixture_ref": fref, "selections": selections,
            "arm_order": ["initial", "experienced"], "max_materialized_bytes": 1024*1024}
    return service, request, put, source[0]


@pytest.mark.parametrize("pair_source", [True], indirect=True)
def test_time_zero_requires_zero_exposure_and_actual_equal_artifact_trees(pair_source, tmp_path):
    service, request, _, _ = pair_source
    target = tmp_path / "pair"
    plan = service.prepare(EVALUATOR, request(), target)
    assert plan["at_t0"]
    def state(arm):
        root = target / plan["arm_directories"][arm]
        return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file()}
    assert state("experienced") == state("initial")
    # A seeded deterministic fixture policy depends only on its admitted bytes.
    # Equal inputs produce zero designed gain; no model/scientific claim.
    import random
    from mcbench.storage import digest
    def policy(surface):
        return random.Random(digest({p: b.hex() for p, b in surface.items()})).choice([False, True])
    assert int(policy(state("experienced"))) - int(policy(state("initial"))) == 0
    assert service.verify(EVALUATOR, "p1") == plan


@pytest.mark.parametrize("pair_source", [True], indirect=True)
def test_zero_schedule_cannot_admit_learned_skills(pair_source, tmp_path):
    service, request, _, _ = pair_source
    base = request()
    chosen = base["selections"]["a1"] | {"skill_names": ["learned-crafting"]}
    with pytest.raises(Fault, match="T0_NOT_MATCHED"):
        service.prepare(EVALUATOR, request(selection_patch={"a1": chosen}), tmp_path / "pair")


def test_two_complete_disk_trees_match_except_admitted_artifacts(pair_source, tmp_path):
    service, request, _, runtime = pair_source
    before = runtime.budgets.status("a1")
    target = tmp_path / "pair"
    plan = service.prepare(EVALUATOR, request(), target)
    assert service.verify(EVALUATOR, "p1") == plan
    for part in ("server/world/level.dat", "server/external/teams.dat", "private/common.json",
                 "private/body-0/body_state.json", "private/body-0/keymap.json", "private/body-0/control_card.json"):
        a, b = target / plan["arm_directories"]["initial"] / part, target / plan["arm_directories"]["experienced"] / part
        assert a.read_bytes() == b.read_bytes() and not os.path.samefile(a, b)
    assert not plan["at_t0"] and not plan["dispatch_authorized"]
    assert not plan["live_initial_state_verified"] and not plan["resource_admission_verified"]
    assert plan["common"]["members"]["a1"]["helper_practice_namespace"] == "development"
    for arm in ("initial", "experienced"):
        root = target / plan["arm_directories"][arm] / "agents/body-0"
        assert not list((root / "profile").iterdir()) and not list((root / "backend-cache").iterdir())
        assert not (root / "workspace/pair.json").exists()
        assert not (root / "workspace/skills/publish.json").exists()
    assert (target / plan["arm_directories"]["experienced"] / "agents/body-0/workspace/active/learned-crafting/scripts/check.js").is_file()
    assert not (target / plan["arm_directories"]["initial"] / "agents/body-0/workspace/active/learned-crafting").exists()
    assert runtime.budgets.status("a1") == before
    assert service.db.connection.execute("SELECT state FROM probe_pair_staging").fetchone()[0] == "PREPARED"


@pytest.mark.parametrize("path", ["initial/server/world/level.dat", "experienced/private/common.json",
    "initial/private/body-0/keymap.json", "experienced/agents/body-0/workspace/notes/root.md",
    "initial/agents/body-0/profile/session.json", "experienced/agents/body-0/backend-cache/map.json",
    "initial/agents/body-0/workspace/foreign.md"])
def test_actual_drift_or_extra_state_refuses_verification(pair_source, tmp_path, path):
    service, request, _, _ = pair_source
    target = tmp_path / "pair"
    plan = service.prepare(EVALUATOR, request(), target)
    arm, path = path.split("/", 1)
    (target / plan["arm_directories"][arm] / path).write_text("changed or imported state", encoding="utf-8")
    with pytest.raises(Fault, match="CORRUPT_EVIDENCE|MIXED_SNAPSHOT"):
        service.verify(EVALUATOR, "p1")


@pytest.mark.parametrize("case", ["hardlink", "empty_cache_directory"])
def test_equal_bytes_do_not_hide_shared_world_files_or_extra_directories(pair_source, tmp_path, case):
    service, request, _, _ = pair_source
    target = tmp_path / "pair"
    plan = service.prepare(EVALUATOR, request(), target)
    if case == "hardlink":
        path = target / plan["arm_directories"]["initial"] / "server/world/level.dat"
        path.unlink()
        os.link(target / plan["arm_directories"]["experienced"] / "server/world/level.dat", path)
    else:
        (target / plan["arm_directories"]["initial"] / "agents/body-0/profile/old-session").mkdir()
    with pytest.raises(Fault, match="UNSAFE_PATH|MIXED_SNAPSHOT"):
        service.verify(EVALUATOR, "p1")


def test_fixture_is_reserved_before_first_copy_and_caller_plan_is_not_authority(pair_source, tmp_path, monkeypatch):
    service, request, _, _ = pair_source
    original, attempted = service.cas.copy_to, []
    other = request(pair_id="p2", fixture_patch={"instance_id": "i2"})
    def interleaved(*args, **kwargs):
        if not attempted:
            attempted.append(True)
            with pytest.raises(Fault, match="PROBE_INSTANCE_CONSUMED"):
                service.prepare(EVALUATOR, other, tmp_path / "overlap")
        return original(*args, **kwargs)
    monkeypatch.setattr(service.cas, "copy_to", interleaved)
    plan = service.prepare(EVALUATOR, request(), tmp_path / "pair")
    assert attempted == [True] and not (tmp_path / "overlap").exists()
    plan["common"]["public_goal"] = "forged"
    assert service.verify(EVALUATOR, "p1")["common"]["public_goal"] == "Explore the visible area."


@pytest.mark.parametrize("kind", ["instance_alias", "pair_alias"])
def test_consumed_fixture_cannot_be_rearmed_by_relabeling(pair_source, tmp_path, kind):
    service, request, _, _ = pair_source
    service.prepare(EVALUATOR, request(), tmp_path / "first")
    next_request = request(pair_id="p2", fixture_patch={"instance_id": "i2"} if kind == "instance_alias" else {})
    with pytest.raises(Fault, match="PROBE_INSTANCE_CONSUMED"):
        service.prepare(EVALUATOR, next_request, tmp_path / "second")
    assert not (tmp_path / "second").exists()


def test_interrupted_copy_keeps_failed_intent_and_never_rearms(pair_source, tmp_path, monkeypatch):
    service, request, _, _ = pair_source
    original = service.cas.copy_to
    calls = []
    def failed(*args, **kwargs):
        calls.append(args)
        if len(calls) == 2:
            raise OSError("synthetic disk failure")
        return original(*args, **kwargs)
    monkeypatch.setattr(service.cas, "copy_to", failed)
    r = request()
    with pytest.raises(OSError, match="synthetic disk failure"):
        service.prepare(EVALUATOR, r, tmp_path / "failed")
    assert service.db.connection.execute("SELECT state FROM probe_pair_staging").fetchone()[0] == "FAILED"
    assert calls[0][3].is_file() and not calls[1][3].exists()
    with pytest.raises(Fault, match="PROBE_INSTANCE_CONSUMED"):
        service.prepare(EVALUATOR, r, tmp_path / "again")
    with pytest.raises(Fault, match="PROBE_PAIR_NOT_PREPARED"):
        service.verify(EVALUATOR, "p1")


@pytest.mark.parametrize("patch,fault", [
    ({"body_states": {}}, "PROBE_COMPLETE_ROSTER"), ({"control_cards": {}}, "PROBE_COMPLETE_ROSTER"),
    ({"keymaps": {"a1": None}}, "PROBE_KEYMAP_SCOPE"),
    ({"world_files": {"world/../x": "cas:sha256:"+"a"*64}}, "UNSAFE_PATH"),
    ({"world_files": {"world/auth.json": "cas:sha256:"+"a"*64}}, "SECRET_IN_SNAPSHOT"),
])
def test_incomplete_or_forbidden_fixture_has_no_intent(pair_source, tmp_path, patch, fault):
    service, request, _, _ = pair_source
    with pytest.raises(Fault, match=fault):
        service.prepare(EVALUATOR, request(fixture_patch=patch), tmp_path / "pair")
    assert not (tmp_path / "pair").exists()
    assert service.db.connection.execute("SELECT count(*) FROM probe_pair_staging").fetchone()[0] == 0


@pytest.mark.parametrize("change,fault", [("order", "PROBE_ORDER_SCOPE"), ("selection", "PROBE_SELECTION_SCOPE"),
    ("budget", "PROBE_STORAGE_LIMIT"), ("exposure", "PROBE_PROTOCOL_SCOPE"), ("mode", "PROBE_PAIR_SCOPE")])
def test_private_preregistration_and_resource_limits_are_binding(pair_source, tmp_path, change, fault):
    service, request, _, _ = pair_source
    r = request(protocol_patch={"exposure_s": [0], "primary_checkpoint_s": 0}) if change == "exposure" else request()
    if change == "order":
        r["arm_order"].reverse()
    elif change == "selection":
        r["selections"]["a1"]["retained_paths"] = []
    elif change == "budget":
        r["max_materialized_bytes"] = 1
    elif change == "mode":
        r["is_example"] = False
    with pytest.raises(Fault, match=fault):
        service.prepare(EVALUATOR, r, tmp_path / "pair")


@pytest.mark.parametrize("principal", [Principal("evaluation:foreign", "evaluator"),
    Principal("evaluation:test", "executor"), Principal("evaluation:test", "helper")])
def test_gameplay_and_foreign_evaluator_cannot_prepare(pair_source, tmp_path, principal):
    service, request, _, _ = pair_source
    with pytest.raises(Fault, match="FORBIDDEN"):
        service.prepare(principal, request(), tmp_path / "pair")
    with pytest.raises(Fault, match="FORBIDDEN"):
        service.verify(principal, "unknown")


@pytest.mark.parametrize("value", [[], {"schema": "unknown", "selections": {}},
    {"schema": "strata/ProbeSelectionIndex/1", "selections": []}])
def test_malformed_private_selection_index_fails_closed(pair_source, tmp_path, value):
    service, request, put, _ = pair_source
    with pytest.raises(Fault, match="PROBE_INDEX_SCHEMA"):
        service.prepare(EVALUATOR, request(protocol_patch={"artifact_projection": put(value)}), tmp_path / "pair")


@pytest.mark.parametrize("model", [ProbeFixture, ProbePairRequest])
def test_pair_schemas_stay_private(model):
    root = Path(__file__).resolve().parents[1] / "schemas/v1"
    name = model.__name__ + ".json"
    assert json.loads((root / "evaluator" / name).read_bytes()) == model.model_json_schema() | {
        "$schema": "https://json-schema.org/draft/2020-12/schema"}
    assert not (root / "public" / name).exists()
