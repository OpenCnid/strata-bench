"""Pair source custody with synthetic writer orchestration; native opt-in below."""

import json
import os
from pathlib import Path
import shutil
import time
import uuid
from types import SimpleNamespace

import pytest

from mcbench.controller import reserved_resources
from mcbench.storage import Fault, Principal, canonical, digest
from strata_evaluator.probe_world_copies import ProbeWorldCopies
from strata_evaluator.writer_custody import WriterCustody
from strata_evaluator.writer_preparation import CODEX_SHA256, parse_preparation_plan
from test_probe_custody import custody as _custody, pair_source as _pair_source, PER_ARM
from test_probe_pairs import EVALUATOR

custody, pair_source = _custody, _pair_source
pytestmark = [
    pytest.mark.skipif(os.name != "nt", reason="actual source Windows file custody"),
    pytest.mark.parametrize("pair_source", [{"probe_spend": 1000}], indirect=True),
]


@pytest.fixture
def copies(custody, tmp_path, request):
    prep, reserves, controller, _ = custody
    per_arm = PER_ARM | {
        "disk_bytes": 1000000
        if getattr(request.node, "callspec", SimpleNamespace(params={})).params.get("fault")
        == "storage"
        else 128 * 1024**2
    }
    capacity = {k: v * 2 for k, v in per_arm.items()}
    controller.certify(
        "probe-worker", "fixture-pins", capacity, "cas:sha256:" + "a" * 64, simulation=True
    )
    prep.acquire(
        EVALUATOR,
        "p1",
        reserves,
        worker="probe-worker",
        fingerprint="fixture-pins",
        per_arm_resources=per_arm,
        lifetime_s=300,
    )
    pair, _, target, *_ = prep._source("p1")

    def pin(path, sha="a" * 64):
        return {"path": str(path), "bytes": 8, "sha256": sha}

    plans = {}
    for index, arm in enumerate(pair["arm_order"]):
        source = target / pair["arm_directories"][arm] / "server"
        plans[arm] = {
            "schema": "strata/PrivateWriterPreparationPlan/2",
            "network_policy": "native-online-private-server/1",
            "id": "probe-copy-" + arm,
            "evidence_kind": "synthetic",
            "codex": pin(tmp_path / "codex.exe", CODEX_SHA256),
            "java": pin(tmp_path / "java.exe"),
            "helper_class": pin(tmp_path / "StrataWriterPreparation.class"),
            "sandbox_home": str(tmp_path / "enrollment"),
            "writer_sid": "S-1-5-21-1-2-3-1003",
            "source_root": str(source),
            "workspace_directory": str(tmp_path / ("writer-" + arm)),
            "evidence_directory": str(tmp_path / ("evidence-" + arm)),
            "sources": {
                name: {
                    "path": str(source / name),
                    "sha256": ref[11:],
                    "bytes": (source / name).stat().st_size,
                }
                for name, ref in pair["world_files"].items()
            },
            "max_wall_s": 120 if index == 0 else 60,
        }
    return ProbeWorldCopies(prep), plans, capacity


@pytest.fixture
def fake_writers(monkeypatch):
    """Only coordinator unit tests substitute native writer/token ownership."""
    from strata_evaluator import probe_world_copies
    from mcbench.launch_integrity import snapshot

    # Synthetic coordinator tests replace native pins along with native launch.
    monkeypatch.setattr(probe_world_copies, "runtime_inventory", lambda plans:
        snapshot([next(iter(next(iter(plans.values())).sources.values())).path], []))

    events = []

    def run(self, value, *, continuation):
        plan = parse_preparation_plan(value)
        root = Path(plan.workspace_directory) / "guarded"
        root.mkdir(parents=True)
        for name in getattr(plan, "directories", []):
            (root / name).mkdir(parents=True, exist_ok=True)
        for name, pin in plan.sources.items():
            destination = root / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(pin.path, destination)
        body = {
            "stages": {
                "preparation": {
                    "terminal_verified": True,
                    "logs_complete": True,
                    "exit_code": 0,
                    "forced": False,
                }
            }
        }
        writer = WriterCustody(
            plan,
            SimpleNamespace(path=root, group_sid="group", scope_sid="scope", verify=lambda: None),
            SimpleNamespace(verify_enrolled=lambda *_: None),
            [],
            time.monotonic() + plan.max_wall_s,
            body,
            lambda *args: events.append(args),
        )
        events.append((plan.id, "ENTER"))
        try:
            continuation(writer)
            assert writer.completed and writer.result["status"] == "discarded"
        finally:
            writer.close()
            events.append((plan.id, "CLOSE"))
        return {"status": "discarded_preparation", "custody": writer.result}

    monkeypatch.setattr(probe_world_copies.WriterPreparations, "run", run)
    return events


def test_both_exact_worlds_borrowed_together_without_releasing_source_holds(copies, fake_writers):
    service, plans, capacity = copies
    saved = []

    def continuation(held):
        saved.append(held)
        result = held.check()
        assert len(set(result["roots"].values())) == 2 and not result["native_launch_authorized"]
        for plan in plans.values():
            path = Path(plan["sources"]["world/level.dat"]["path"])
            with pytest.raises(PermissionError):
                path.write_bytes(b"changed")

    result = service.run(EVALUATOR, plans, continuation=continuation)
    assert len(result["results"]) == 2 and not result["live_initial_state_verified"]
    assert [e[1] for e in fake_writers].count("ENTER") == 2 and [e[1] for e in fake_writers].count(
        "CLOSE"
    ) == 2
    assert (
        service.db.connection.execute("SELECT state FROM probe_world_copies").fetchone()[0]
        == "DISCARDED"
    )
    assert reserved_resources(service.db.connection, "probe-worker") == capacity
    assert (
        service.preparation.runtime.budgets.status("probe-total")["committed_and_reserved"][
            "spend_microusd"
        ]
        == 200
    )
    with pytest.raises(Fault, match="PROBE_WORLD_CUSTODY_CLOSED"):
        saved[0].check()


@pytest.mark.parametrize(
    "fault",
    [
        "missing_arm",
        "foreign_source",
        "wrong_hash",
        "extra_file",
        "same_identity",
        "overlap",
        "deadline",
        "storage",
    ],
)
def test_preflight_rejects_partial_or_unmatched_writer_copy_before_native_work(
    copies, fake_writers, fault
):
    service, plans, _ = copies
    arms = list(plans)
    first = plans[arms[0]]
    if fault == "missing_arm":
        del plans[arms[1]]
    elif fault == "foreign_source":
        first["source_root"] = plans[arms[1]]["source_root"]
        first["sources"] = plans[arms[1]]["sources"]
    elif fault == "wrong_hash":
        first["sources"]["world/level.dat"]["sha256"] = "a" * 64
    elif fault == "extra_file":
        first["sources"]["world/extra.dat"] = first["sources"]["world/level.dat"]
    elif fault == "same_identity":
        plans[arms[1]]["id"] = first["id"]
    elif fault == "overlap":
        plans[arms[1]]["workspace_directory"] = first["workspace_directory"]
    elif fault == "deadline":
        first["max_wall_s"] = 900
    else:
        assert service.preparation.plan["resources"]["disk_bytes"] == 2000000
    with pytest.raises(Fault):
        service.run(EVALUATOR, plans, continuation=lambda _: None)
    assert not fake_writers
    assert not service.db.connection.execute("SELECT 1 FROM probe_world_copies").fetchone()


def test_continuation_fault_closes_both_writers_and_fences_without_refunds(copies, fake_writers):
    service, plans, capacity = copies

    def fail(held):
        held.check()
        raise OSError("synthetic continuation failure")

    with pytest.raises(OSError):
        service.run(EVALUATOR, plans, continuation=fail)
    assert [e[1] for e in fake_writers].count("CLOSE") == 2
    assert (
        service.db.connection.execute("SELECT state FROM probe_world_copies").fetchone()[0]
        == "FAILED"
    )
    assert (
        service.db.connection.execute("SELECT state FROM probe_pair_custody").fetchone()[0]
        == "FENCED"
    )
    assert reserved_resources(service.db.connection, "probe-worker") == capacity
    assert (
        service.preparation.runtime.budgets.status("probe-total")["committed_and_reserved"][
            "spend_microusd"
        ]
        == 200
    )


def test_foreign_principal_cannot_begin_world_copy(copies, fake_writers):
    service, plans, _ = copies
    before = list(service.db.connection.iterdump())
    with pytest.raises(Fault, match="FORBIDDEN"):
        service.run(Principal("a1", "helper"), plans, continuation=lambda _: None)
    assert list(service.db.connection.iterdump()) == before and not fake_writers


@pytest.mark.skipif(
    not os.environ.get("STRATA_PROBE_WRITER_RUNTIME"),
    reason="explicit existing native writer pins required",
)
def test_actual_native_pair_copy_and_unlaunched_close(copies, tmp_path):
    service, plans, capacity = copies
    native = json.loads(Path(os.environ["STRATA_PROBE_WRITER_RUNTIME"]).read_bytes())
    for plan in plans.values():
        plan.update(native)
        # The existing lower-privilege writer must traverse the parent. The
        # production OperatorWorkspace creates this leaf with its final DACL;
        # no private evidence/ancestor permissions are broadened.
        plan["workspace_directory"] = str(Path("C:/Users/Public") / ("strata-probe-world-" + uuid.uuid4().hex))
    observed = []

    def inspect(held):
        result = held.check()
        checks = {}
        hashes = []
        for arm, writer in held.writers.items():
            source = Path(plans[arm]["sources"]["world/level.dat"]["path"])
            target = writer.tree.path / "world/level.dat"
            hashes.append(digest(target.read_bytes().hex()))
            for label, path in [("original", source), ("copy", target)]:
                with pytest.raises(PermissionError):
                    path.write_bytes(b"foreign-writer")
                checks[arm + "_" + label + "_write_denied"] = True
            checks[arm + "_native_token_bound"] = bool(writer.body["writer_token"])
            checks[arm + "_copier_stopped"] = writer.body["stages"]["preparation"][
                "terminal_verified"
            ]
        assert len(set(hashes)) == 1
        observed.append(result | {"checks": checks, "matching_hashes": hashes})

    result = service.run(EVALUATOR, plans, continuation=inspect)
    assert reserved_resources(service.db.connection, "probe-worker") == capacity
    assert (
        service.preparation.runtime.budgets.status("probe-total")["committed_and_reserved"][
            "spend_microusd"
        ]
        == 200
    )
    assert all(
        r["status"] == "discarded_preparation" and not r["custody"]["live"]
        for r in result["results"].values()
    )
    assert (
        service.db.connection.execute(
            "SELECT count(*) FROM writer_preparations WHERE state='DISCARDED'"
        ).fetchone()[0]
        == 2
    )
    fresh = {arm: value | {"workspace_directory": value["workspace_directory"] + "-unused",
                          "evidence_directory": value["evidence_directory"] + "-unused"}
             for arm, value in plans.items()}
    with pytest.raises(Fault, match="PROBE_WORLD_COPIES_CONSUMED"):
        service.run(EVALUATOR, fresh, continuation=lambda _: pytest.fail("Consumed pair was replayed"))
    (tmp_path / "native-world-copy-result.json").write_bytes(
        canonical(
            {
                "observed": observed,
                "result": result,
                "synthetic_source": True,
                "model_calls": 0,
                "game_launched": False,
                "same_pair_reacquisition_refused": True,
                "budget_hold": 200,
                "capacity_hold": capacity,
            }
        )
    )
