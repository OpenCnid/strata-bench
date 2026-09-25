"""Opt-in actual paired workers/worlds; synthetic native-agent/protocol sources.

No model inference, gameplay actions, native probe admission or G1 claim.
"""

import hashlib
import json
import os
import re
import time
from pathlib import Path
import uuid

import pytest

from mcbench.controller import reserved_resources
from mcbench.storage import Fault, canonical, require
from strata_evaluator.probe_saved_bodies import saved_body
from strata_evaluator.probe_vanilla_runtime import BODY_POLICY
from strata_evaluator.probe_worker_runtime import PairedWorkerReference, POLICY
from strata_evaluator.probe_world_copies import ProbeWorldCopies
from test_probe_pairs import EVALUATOR
from test_probe_vanilla_runtime_native import configs, base_pair_source, custody, source, pin, pair_source as source_pair

configs, base_pair_source, custody, source, source_pair = configs, base_pair_source, custody, source, source_pair

pytestmark = [pytest.mark.skipif(os.name != "nt", reason="native Windows writer required"),
    pytest.mark.skipif(not os.environ.get("STRATA_PROBE_WORKER_REFERENCE"), reason="explicit pinned real worker inputs required"),
    pytest.mark.parametrize("base_pair_source", [{"probe_spend": 1000}], indirect=True),
    pytest.mark.parametrize("directory_fixture", [True])]


@pytest.fixture
def actual_inputs():
    raw = Path(os.environ["STRATA_PROBE_WORKER_REFERENCE"]).read_bytes()
    require(hashlib.sha256(raw).hexdigest() == os.environ.get("STRATA_PROBE_WORKER_REFERENCE_SHA256"), "NATIVE_REFERENCE_INPUT_CHANGED")
    body = json.loads(raw)
    require(body["scope"] == "actual-vanilla-workers-synthetic-agent-protocol-reference/1"
            and body["model_calls"] == 0, "NATIVE_REFERENCE_SCOPE")
    require(isinstance(body.get("player_uuid"), str) and re.fullmatch(r"[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}", body["player_uuid"]), "NATIVE_REFERENCE_PLAYER")
    parent = Path(body["writer_evidence_parent"])
    require(parent.is_absolute() and not parent.exists(), "NATIVE_REFERENCE_EVIDENCE_REUSED")
    parent.mkdir(parents=True)
    return body


@pytest.fixture
def pair_source(source_pair, source, actual_inputs):
    pairs, make, put, runtime = source_pair
    raw = (Path(source[1]["snapshot"]) / "state/world/playerdata" / (actual_inputs["player_uuid"] + ".dat")).read_bytes()
    body = saved_body(raw)
    require(body["player_uuid"] == actual_inputs["player_uuid"], "NATIVE_REFERENCE_PLAYER")

    def registered(**kwargs):
        return make(**kwargs, fixture_patch={"body_states": {"a1": put(body)}})
    return pairs, registered, put, runtime


def test_actual_registered_workers_join_initial_projection_and_stop_before_save(
    custody, source, actual_inputs, tmp_path, directory_fixture, monkeypatch,
):
    prep, reservations, controller, _ = custody
    per_arm = {"bodies": 1, "model_slots": 3, "memory_mib": 4096, "disk_bytes": 3 * 1024**3}
    capacity = {k: v * 2 for k, v in per_arm.items()}
    controller.certify("probe-worker", "fixture-pins", capacity, "cas:sha256:" + "a" * 64, simulation=True)
    started = time.monotonic()
    prep.acquire(EVALUATOR, "p1", reservations, worker="probe-worker", fingerprint="fixture-pins",
                 per_arm_resources=per_arm, lifetime_s=300)
    phases = [{"phase": "parent_acquire", "start_s": 0, "end_s": time.monotonic() - started}]

    def timed(name, method):
        def call(*args, **kwargs):
            start = time.monotonic() - started
            try:
                return method(*args, **kwargs)
            finally:
                phases.append({"phase": name, "start_s": start, "end_s": time.monotonic() - started})
        return call

    # Diagnostic intervals may overlap. They do not replace campaign clocks or
    # alter deadlines; write only after the attempt, including failed preparation.
    from mcbench.pack_worker import HeldPackWorker
    from strata_evaluator.probe_vanilla_inputs import VanillaProbeInputs
    monkeypatch.setattr(prep, "check", timed("parent_check", prep.check))
    for cls, method, name in ((HeldPackWorker, "__enter__", "worker_inputs"),
                              (VanillaProbeInputs, "__enter__", "software_inputs"),
                              (VanillaProbeInputs, "check", "software_check")):
        monkeypatch.setattr(cls, method, timed(name, getattr(cls, method)))
    pair = prep._source("p1")[0]
    launches = {arm: {"schema": "strata/PrivateProbeVanillaLaunch/2", "policy": BODY_POLICY,
        "pair_id": "p1", "arm": arm, "helper_class": actual_inputs["launch_helper"],
        "max_wall_s": 60, "max_stopped_state_bytes": 64 * 1024**2} for arm in pair["arm_order"]}
    invocations = {arm: {} for arm in pair["arm_order"]}
    for row in prep.db.connection.execute("SELECT * FROM native_probe_bindings").fetchall():
        state = tmp_path / ("worker-" + row["arm"])
        state.mkdir()
        invocations[row["arm"]][row["source_agent"]] = {"campaign_id": row["campaign"], "agent_id": row["agent"],
            "epoch": 1, "lease_id": "worker-" + row["arm"] + "-" + uuid.uuid4().hex,
            "state_directory": str(state), "configuration_path": str(tmp_path / ("worker-" + row["arm"] + ".json"))}

    def plans(software):
        result = {}
        for index, arm in enumerate(pair["arm_order"]):
            result[arm] = actual_inputs["writer"] | {
                "schema": "strata/PrivateWriterPreparationPlan/4", "evidence_kind": "synthetic",
                "network_policy": "native-online-private-server/1", "staging_policy": "sequential-bundles512mib/1",
                "id": "native-workers-" + arm, "source_root": software.roots[arm], "sources": software.sources[arm],
                "directories": software.directories, "java": pin(software.resolved["launch"]["executable_path"]),
                "workspace_directory": str(Path("C:/Users/Public") / ("strata-worker-pair-" + uuid.uuid4().hex)),
                "evidence_directory": str(Path(actual_inputs["writer_evidence_parent"]) / arm),
                "max_wall_s": 200 if index == 0 else 170}
        (tmp_path / "runtime-inputs.json").write_bytes(canonical({"plans": result, "launches": launches,
            "worker_invocations": invocations, "synthetic_agent_and_protocol_source": True,
            "authentic_vanilla_worker_inputs": True, "model_calls": 0, "native_probe_admission": False}))
        return result

    original = PairedWorkerReference.event
    checks = []
    def event(owner, arm, phase):
        phases.append({"phase": arm + ":" + phase, "at_s": time.monotonic() - started})
        if phase == "server_ready":
            session = owner.sessions[arm]
            assert session.result["jvm_token"]["held_token_verified"]
            for path in (Path(session.writer.plan.sources["world/level.dat"].path),
                         session.writer.tree.path / "world/level.dat", session.writer.tree.path / "server.jar"):
                with pytest.raises(PermissionError):
                    with path.open("ab"):
                        pass
            if arm == pair["arm_order"][1]:
                first_state = Path(invocations[pair["arm_order"][0]]["a1"]["state_directory"])
                with pytest.raises(PermissionError):
                    with (first_state / "actions.sqlite").open("ab"):
                        pass
            with pytest.raises(Fault, match="PROBE_GAME_REFERENCE_INTENT"):
                prep.release_undispatched_resources()
            checks.append({"arm": arm, "owned_jvm": True, "source_copy_software_denials": 3,
                           "prior_worker_export_held": len(checks) == 1, "early_release_refused": True})
        original(owner, arm, phase)
    monkeypatch.setattr(PairedWorkerReference, "event", event)
    service = ProbeWorldCopies(prep)
    try:
        result = service.run_vanilla_worker_reference(EVALUATOR, plans, launches, invocations,
                                                     pack_binding=source[0].model_dump())
    finally:
        (tmp_path / "preparation-timing.json").write_bytes(canonical({
            "diagnostic_only": True, "intervals_may_overlap": True, "phases": phases,
            "elapsed_since_parent_acquire_s": time.monotonic() - started}))
    assert result["policy"] == POLICY and set(result["runtime"]["workers"]) == set(pair["arm_order"])
    assert len(checks) == 2
    for group in result["runtime"]["workers"].values():
        assert group["complete_roster_observed_connected"] and not group["live_initial_state_verified"]
        assert group["members"]["a1"]["own_state_projection_verified"]
    assert reserved_resources(service.db.connection, "probe-worker") == capacity
    assert prep.runtime.budgets.status("probe-total")["committed_and_reserved"]["spend_microusd"] == 200
    (tmp_path / "native-worker-pair-result.json").write_bytes(canonical({"result": result, "checks": checks}))
