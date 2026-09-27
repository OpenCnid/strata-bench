"""Opt-in actual paired vanilla references with synthetic agent/protocol sources.

No native gameplay agent or provider runs. Explicit externally pinned operator
inputs select the genuine server/software/save state; no production pins change.
"""

import hashlib
import json
import os
from pathlib import Path
import sqlite3
from types import SimpleNamespace
import uuid

import pytest

from mcbench.controller import reserved_resources
from mcbench.inventory import file_hash
from mcbench.pack_launch import PackLaunchBinding, resolve_pack_launch
from mcbench.storage import CAS, Fault, Principal, canonical, require
from mcbench.vanilla_persistence import verify_snapshot
from strata_evaluator.evidence_bundle import EvidenceBundle
from strata_evaluator.probe_vanilla_runtime import POLICY
from strata_evaluator.probe_world_copies import ProbeWorldCopies
from test_probe_custody import custody
from test_probe_pairs import EVALUATOR
from test_probe_vanilla_inputs import configs, base_pair_source

configs, base_pair_source, custody = configs, base_pair_source, custody

pytestmark = [
    pytest.mark.skipif(os.name != "nt", reason="native Windows writer required"),
    pytest.mark.skipif(not os.environ.get("STRATA_PROBE_VANILLA_REFERENCE"),
                       reason="explicit pinned real vanilla inputs required"),
    pytest.mark.parametrize("base_pair_source", [{"probe_spend": 1000}], indirect=True),
    pytest.mark.parametrize("directory_fixture", [True]),
]


@pytest.fixture
def actual_inputs():
    raw = Path(os.environ["STRATA_PROBE_VANILLA_REFERENCE"]).read_bytes()
    require(hashlib.sha256(raw).hexdigest() == os.environ.get("STRATA_PROBE_VANILLA_REFERENCE_SHA256"),
            "NATIVE_REFERENCE_INPUT_CHANGED")
    body = json.loads(raw)
    require(body["scope"] == "actual-vanilla-synthetic-agent-protocol-reference/1"
            and body["model_calls"] == 0, "NATIVE_REFERENCE_SCOPE")
    parent = Path(body["writer_evidence_parent"])
    require(parent.is_absolute() and not parent.exists(), "NATIVE_REFERENCE_EVIDENCE_REUSED")
    parent.mkdir(parents=True)
    return body


@pytest.fixture
def source(actual_inputs):
    source = actual_inputs["world_source"]
    archive = EvidenceBundle(source["directory"], source["seal_sha256"])
    snapshot = archive.path(source["manifest"]).parent
    pin = archive.files[source["manifest"]].sha256
    captured = verify_snapshot(snapshot, pin)
    fresh = PackLaunchBinding.model_validate(actual_inputs["binding"])
    resolved = resolve_pack_launch(fresh, "server")
    require(captured["schema"] == "strata/StoppedVanillaSnapshot/2"
            and captured["pack"]["lock"] == fresh.lock, "NATIVE_REFERENCE_SOURCE")
    require(resolved["target"] == "vanilla", "NATIVE_REFERENCE_SOURCE")
    # Read the existing provisioning store without schema initialization or CAS
    # directory creation. Its live WAL, if any, remains part of the read snapshot.
    db = sqlite3.connect((Path(fresh.store) / "controller.sqlite").as_uri()+"?mode=ro", uri=True)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA query_only=ON")
    db.execute("BEGIN")
    cas = object.__new__(CAS)
    cas.database, cas.root = SimpleNamespace(connection=db), Path(fresh.store) / "objects"
    try:
        yield fresh, {"snapshot": str(snapshot), "sha256": pin}, SimpleNamespace(cas=cas)
    finally:
        db.close()
        archive.verify()


@pytest.fixture
def pair_source(base_pair_source, source, cas, request):
    pairs, make_request, put, runtime = base_pair_source
    snapshot = Path(source[1]["snapshot"])
    body = verify_snapshot(snapshot, source[1]["sha256"])
    files = {}
    for path, entry in body["files"].items():
        if entry["disposition"] != "state":
            continue
        name = path if path.startswith("world/") else "external/"+path
        require(entry["bytes"] <= 64*1024**2, "NATIVE_REFERENCE_SOURCE_QUOTA")
        files[name] = cas.put(Principal("operator", "operator"), EVALUATOR.namespace,
            "evaluator", (snapshot / "state" / path).read_bytes(),
            quota_bytes=128*1024**2, max_object_bytes=64*1024**2)
    patch = {"schema": "strata/ProbeFixture/2", "world_files": files,
             "world_directories": sorted({"external"} | {p for p in body["directories"]
                 if p == "world" or p.startswith("world/")})}

    def bounded_request(**kwargs):
        override = kwargs.pop("fixture_patch", {})
        return make_request(**kwargs, fixture_patch=patch | override) | {
            "schema": "strata/ProbePairRequest/2", "policy": "private-matched-probe-pair-staging/2",
            "max_materialized_bytes": 128 * 1024**2}

    return pairs, bounded_request, put, runtime


def pin(path):
    path = Path(path)
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": file_hash(path)}


def test_actual_registered_pair_servers_stop_and_preserve_private_exports(
    custody, source, actual_inputs, tmp_path, directory_fixture
):
    prep, reservations, controller, _ = custody
    per_arm = {"bodies": 1, "model_slots": 3, "memory_mib": 4096, "disk_bytes": 3 * 1024**3}
    capacity = {k: v * 2 for k, v in per_arm.items()}
    controller.certify("probe-worker", "fixture-pins", capacity,
                       "cas:sha256:" + "a" * 64, simulation=True)
    # This certificate is synthetic. The operator separately records current
    # host capacity before opting in; no capacity-qualification claim follows.
    prep.acquire(EVALUATOR, "p1", reservations, worker="probe-worker", fingerprint="fixture-pins",
                 per_arm_resources=per_arm, lifetime_s=300)
    fresh = source[0]
    plans, launches = {}, {}
    pair = prep._source("p1")[0]
    for arm in pair["arm_order"]:
        launches[arm] = {"schema": "strata/PrivateProbeVanillaLaunch/1", "policy": POLICY,
            "pair_id": "p1", "arm": arm, "helper_class": actual_inputs["launch_helper"],
            "max_wall_s": 60, "max_stopped_state_bytes": 64 * 1024**2}

    def plan_factory(software):
        for index, arm in enumerate(pair["arm_order"]):
            plans[arm] = actual_inputs["writer"] | {
                "schema": "strata/PrivateWriterPreparationPlan/4", "evidence_kind": "synthetic",
                "network_policy": "native-online-private-server/1",
                "staging_policy": "sequential-bundles512mib/1", "id": "native-pair-"+arm,
                "source_root": software.roots[arm], "sources": software.sources[arm],
                "directories": software.directories,
                "java": pin(software.resolved["launch"]["executable_path"]),
                "workspace_directory": str(Path("C:/Users/Public") / ("strata-pair-"+uuid.uuid4().hex)),
                "evidence_directory": str(Path(actual_inputs["writer_evidence_parent"]) / arm),
                "max_wall_s": 200 if index == 0 else 170,
            }
        (tmp_path / "runtime-inputs.json").write_bytes(canonical({"plans": plans, "launches": launches,
            "synthetic_agent_and_protocol_source": True, "authentic_vanilla_inputs": True,
            "server_execution_required": True,
            "native_probe_admission": False, "capacity_hold": capacity, "model_calls": 0}))
        return plans
    sessions = {}

    def observe(arm, session):
        sessions[arm] = session
        assert session.result["ready"] and session.result["jvm_token"]["held_token_verified"]
        source_path = Path(plans[arm]["sources"]["world/level.dat"]["path"])
        for path in (source_path, session.writer.tree.path / "world/level.dat",
                     session.writer.tree.path / "server.jar"):
            with pytest.raises(PermissionError):
                with path.open("ab"):
                    pass
        if len(sessions) == 2:
            first = sessions[pair["arm_order"][0]]
            path = Path(first.result["snapshot"]["path"]) / "state/world/level.dat"
            with pytest.raises(PermissionError):
                with path.open("ab"):
                    pass
        with pytest.raises(Fault, match="PROBE_GAME_REFERENCE_INTENT"):
            prep.release_undispatched_resources()
        return {"owned_server_ready": True, "original_copy_software_write_denials": 3,
                "prior_export_held": len(sessions) == 2, "worker_bodies": 0}

    service = ProbeWorldCopies(prep)
    result = service.run_vanilla_reference(EVALUATOR, plan_factory, launches, continuation=observe,
                                           pack_binding=fresh.model_dump())
    for arm in pair["arm_order"]:
        server = result["results"][arm]
        assert server["status"] == "stopped_reference" and not server["custody"]["live"]
        assert server["game_launched"] and server["game_launch_attempted"]
        receipt = server["custody"]["vanilla"]["snapshot"]
        body = verify_snapshot(Path(receipt["path"]), receipt["manifest_sha256"])
        assert body["probe_world"]["arm"] == arm and body["schema"] == "strata/StoppedVanillaSnapshot/3"
    assert reserved_resources(service.db.connection, "probe-worker") == capacity
    assert prep.runtime.budgets.status("probe-total")["committed_and_reserved"]["spend_microusd"] == 200
    with pytest.raises(Fault, match="PROBE_GAME_REFERENCE_INTENT"):
        prep.release_undispatched_resources()
    (tmp_path / "native-pair-result.json").write_bytes(canonical(result))
