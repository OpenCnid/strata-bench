"""Directory-bound pair identity and failure fencing with synthetic game state."""

import json

import pytest
from pydantic import ValidationError

from mcbench.storage import Fault, digest
from strata_evaluator.probe_pairs import (
    DIRECTORY_POLICY,
    ProbeFixtureV2,
    parse_pair_request,
)
from test_probe_pairs import pair_source, EVALUATOR

pair_source = pair_source


def request_v2(make, directories=None):
    value = make(
        fixture_patch={
            "schema": "strata/ProbeFixture/2",
            "world_directories": directories or ["external", "world", "world/datapacks"],
        }
    )
    return value | {"schema": "strata/ProbePairRequest/2", "policy": DIRECTORY_POLICY}


@pytest.mark.parametrize(
    "directories",
    [
        ["world"],
        ["external", "world", "world"],
        ["world", "external"],
        ["external", "world", "world/level.dat"],
        ["external", "world", "world/data/empty"],
        ["external", "world", "world/.codex"],
        ["external", "world", "world/../escape"],
        ["external", "world", "world/DATA", "world/data"],
        ["external", "private", "world"],
        ["external", "world", "world/datapacks", "world/datapacks/.aws"],
    ],
)
def test_directory_contract_refuses_missing_parents_collisions_and_private_paths(directories):
    ref = "cas:sha256:" + "a" * 64
    value = dict.fromkeys(
        (
            "pack_lock",
            "backend_initialization",
            "runtime_policy",
            "tools",
            "observation_action_limits",
            "information_policy",
        ),
        ref,
    )
    value.update(
        schema="strata/ProbeFixture/2",
        is_example=True,
        instance_id="fixture",
        world_files={"world/level.dat": ref, "external/ops.json": ref},
        world_directories=directories,
        body_states={"a1": ref},
        keymaps={"a1": None},
        control_cards={"a1": ref},
        public_goal="Explore.",
    )
    with pytest.raises(
        ValidationError, match="PROBE_WORLD_DIRECTORY_SCOPE|SECRET_IN_SNAPSHOT|UNSAFE_PATH"
    ):
        ProbeFixtureV2.model_validate(value)


def test_directories_participate_in_registered_world_identity(pair_source, tmp_path):
    service, make, _, _ = pair_source
    request = request_v2(make)
    plan = service.prepare(EVALUATOR, request, tmp_path / "pair")
    assert plan["schema"] == "strata/ProbePairStaging/2"
    assert plan["world_digest"] == digest(
        {
            "pack_lock": plan["common"]["pack_lock"],
            "files": plan["world_files"],
            "directories": plan["world_directories"],
        }
    )
    changed = request_v2(make, ["external", "world", "world/data", "world/datapacks"])
    alternative = service._derive(EVALUATOR, parse_pair_request(changed))
    assert plan["world_files"] == alternative["world_files"]
    assert plan["world_digest"] != alternative["world_digest"]
    assert service.verify(EVALUATOR, plan["pair_id"]) == plan
    for arm in plan["arm_order"]:
        assert (
            tmp_path / "pair" / plan["arm_directories"][arm] / "server/world/datapacks"
        ).is_dir()
    assert not plan["dispatch_authorized"] and not plan["live_initial_state_verified"]


@pytest.mark.parametrize("change", ["add", "remove"])
def test_changed_staged_world_directory_consumes_verification(pair_source, tmp_path, change):
    service, make, _, _ = pair_source
    target = tmp_path / "pair"
    plan = service.prepare(EVALUATOR, request_v2(make), target)
    world = target / plan["arm_directories"]["initial"] / "server/world"
    if change == "add":
        (world / "foreign").mkdir()
    else:
        (world / "datapacks").rmdir()
    with pytest.raises(Fault):
        service.verify(EVALUATOR, plan["pair_id"])
    row = service.db.connection.execute("SELECT state,plan FROM probe_pair_staging").fetchone()
    assert row["state"] == "FAILED" and json.loads(row["plan"]) == plan
    with pytest.raises(Fault, match="PROBE_PAIR_NOT_PREPARED"):
        service.verify(EVALUATOR, plan["pair_id"])


@pytest.mark.parametrize("mismatch", ["old_request", "old_fixture"])
def test_fixture_and_request_versions_cannot_silently_mix(pair_source, tmp_path, mismatch):
    service, make, _, _ = pair_source
    value = request_v2(make) if mismatch == "old_request" else make()
    if mismatch == "old_request":
        value.update(
            schema="strata/ProbePairRequest/1", policy="private-matched-probe-pair-staging/1"
        )
    else:
        value.update(schema="strata/ProbePairRequest/2", policy=DIRECTORY_POLICY)
    with pytest.raises(Fault, match="PROBE_FIXTURE_POLICY"):
        service.prepare(EVALUATOR, value, tmp_path / "pair")
    assert not service.db.connection.execute("SELECT 1 FROM probe_pair_staging").fetchall()


def test_unknown_software_policy_is_rejected_before_preparation_access():
    from strata_evaluator.probe_vanilla_inputs import VanillaProbeInputs

    with pytest.raises(Fault, match="PROBE_PACK_POLICY"):
        VanillaProbeInputs(None, {}, policy="unknown")
