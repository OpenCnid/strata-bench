"""Opt-in authentic input preparation only; no game, copier, provider or imports.

Use fresh synthetic pair/account reservations and authentic pinned software/save
inputs. The diagnostic stops before world admission and leaves reservations
fenced. It cannot pass paired runtime or native gameplay acceptance.
"""

import cProfile
import hashlib
import io
import json
import os
from pathlib import Path
import pstats
import time

import pytest

from mcbench import pack_launch, pack_worker
from mcbench.controller import reserved_resources
from mcbench.launch_integrity import FileLease
from mcbench.storage import canonical, require
from mcbench.worker_bundle import HeldWorkerBundle
from strata_evaluator.probe_vanilla_inputs import BODY_POLICY, VanillaProbeInputs
from test_probe_pairs import EVALUATOR
from test_probe_worker_runtime_native import (
    base_pair_source, configs, custody, pair_source, source, source_pair,
)

base_pair_source, configs, custody, pair_source, source, source_pair = (
    base_pair_source, configs, custody, pair_source, source, source_pair,
)

pytestmark = [
    pytest.mark.skipif(os.name != "nt", reason="actual Windows file custody required"),
    pytest.mark.skipif(not os.environ.get("STRATA_PROBE_WORKER_PREPARATION"),
                       reason="explicit pinned preparation-only inputs required"),
    pytest.mark.parametrize("base_pair_source", [{"probe_spend": 1000}], indirect=True),
    pytest.mark.parametrize("directory_fixture", [True]),
]


@pytest.fixture
def actual_inputs():
    raw = Path(os.environ["STRATA_PROBE_WORKER_PREPARATION"]).read_bytes()
    require(hashlib.sha256(raw).hexdigest() == os.environ.get("STRATA_PROBE_WORKER_PREPARATION_SHA256"),
            "PREPARATION_INPUT_CHANGED")
    body = json.loads(raw)
    require(set(body) == {"scope", "model_calls", "binding", "world_source", "player_uuid"}
            and body["scope"] == "actual-vanilla-worker-preparation-only/1"
            and type(body["model_calls"]) is int and body["model_calls"] == 0,
            "PREPARATION_INPUT_SCOPE")
    return body


def test_registered_preparation_without_dispatch(custody, source, tmp_path, monkeypatch, directory_fixture):
    prep, reservations, controller, _ = custody
    per_arm = {"bodies": 1, "model_slots": 3, "memory_mib": 4096, "disk_bytes": 3 * 1024**3}
    capacity = {key: value * 2 for key, value in per_arm.items()}
    controller.certify("probe-worker", "fixture-pins", capacity, "cas:sha256:" + "a" * 64, simulation=True)
    started = time.perf_counter()
    phases = []
    entries = 0

    def no_dispatch(*args, **kwargs):
        raise AssertionError("preparation-only diagnostic attempted process dispatch")

    def timed(name, original):
        def call(*args, **kwargs):
            start, cpu = time.perf_counter(), time.process_time()
            try:
                return original(*args, **kwargs)
            finally:
                phases.append({"phase": name, "start_s": start - started,
                    "wall_s": time.perf_counter() - start, "cpu_s": time.process_time() - cpu})
        return call

    original_entry = pack_worker.HeldPackWorker.__enter__

    def profile_entry(*args, **kwargs):
        nonlocal entries
        entries += 1
        profiler = cProfile.Profile()
        profiler.enable()
        try:
            return original_entry(*args, **kwargs)
        finally:
            profiler.disable()
            profiler.dump_stats(str(tmp_path / f"worker{entries}.prof"))
            out = io.StringIO()
            pstats.Stats(profiler, stream=out).strip_dirs().sort_stats("cumulative").print_stats(70)
            (tmp_path / f"worker{entries}-profile.txt").write_text(out.getvalue(), encoding="utf-8")

    monkeypatch.setattr(pack_worker, "ManagedProcess", no_dispatch)
    monkeypatch.setattr(pack_worker.HeldPackWorker, "__enter__", timed("worker_entry", profile_entry))
    monkeypatch.setattr(pack_launch, "_scan_held_materialization",
                        timed("materialization_scan", pack_launch._scan_held_materialization))
    for cls, method, name in ((HeldWorkerBundle, "__init__", "bundle_manifest"),
                              (HeldWorkerBundle, "__enter__", "bundle_acquire"),
                              (FileLease, "__init__", "lease_acquire"),
                              (FileLease, "recheck", "lease_recheck"),
                              (VanillaProbeInputs, "__enter__", "software_inputs")):
        monkeypatch.setattr(cls, method, timed(name, getattr(cls, method)))
    try:
        prep.acquire(EVALUATOR, "p1", reservations, worker="probe-worker", fingerprint="fixture-pins",
                     per_arm_resources=per_arm, lifetime_s=300)
        invocations = {arm: {} for arm in ("initial", "experienced")}
        for row in prep.db.connection.execute("SELECT * FROM native_probe_bindings").fetchall():
            state = tmp_path / ("worker-" + row["arm"])
            state.mkdir()
            invocations[row["arm"]][row["source_agent"]] = {
                "campaign_id": row["campaign"], "agent_id": row["agent"], "epoch": 1,
                "lease_id": "preparation-" + row["arm"], "state_directory": str(state),
                "configuration_path": str(tmp_path / ("worker-" + row["arm"] + ".json")),
            }
        with VanillaProbeInputs(prep, source[0].model_dump(), policy=BODY_POLICY) as software:
            with software.hold_worker_inputs(EVALUATOR, invocations) as holder:
                proof = holder.check()
                assert proof["whole_roster_held"] and not proof["worker_dispatch_authorized"]
                assert entries == 2
                assert all(not w.processes for group in holder._workers.values() for w in group.values())
                assert all(not any(Path(v["state_directory"]).iterdir())
                           for group in invocations.values() for v in group.values())
                (tmp_path / "input-custody.json").write_bytes(canonical(proof))
            assert all(w.runtime.lease.closed and w.config_lease.closed
                       for group in holder._workers.values() for w in group.values())
        prep.check()
        assert reserved_resources(prep.db.connection, "probe-worker") == capacity
        assert prep.runtime.budgets.status("probe-total")["committed_and_reserved"]["spend_microusd"] == 200
        assert not prep.db.connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('writer_preparations','probe_world_copies')"
        ).fetchall()
    finally:
        prep.close()
        (tmp_path / "preparation-timing.json").write_bytes(canonical({
            "diagnostic_only": True, "intervals_overlap": True, "phases": phases,
            "elapsed_since_parent_acquire_s": time.perf_counter() - started,
            "game_dispatches": 0, "model_calls": 0,
        }))
    assert prep.db.connection.execute("SELECT state FROM probe_pair_custody").fetchone()[0] == "FENCED"
    assert reserved_resources(prep.db.connection, "probe-worker") == capacity
