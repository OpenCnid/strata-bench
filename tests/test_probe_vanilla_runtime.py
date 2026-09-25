"""Real pair/file/export custody with synthetic process, JVM and token results."""

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from mcbench.storage import Fault
from mcbench.vanilla_persistence import verify_snapshot
from strata_evaluator.probe_vanilla_runtime import POLICY
from strata_evaluator.vanilla_writer import ARGUMENTS
from test_probe_vanilla_inputs import (
    source,
    inputs,
    candidate as base_candidate,
    installed as base_installed,
    sealed_installation,
    copies,
    custody,
    configs,
    base_pair_source,
    pair_source,
    software_plans,
)
from test_probe_world_copies import fake_writers

(
    source,
    inputs,
    base_candidate,
    base_installed,
    sealed_installation,
    copies,
    custody,
    configs,
    base_pair_source,
    pair_source,
    software_plans,
    fake_writers,
) = (
    source,
    inputs,
    base_candidate,
    base_installed,
    sealed_installation,
    copies,
    custody,
    configs,
    base_pair_source,
    pair_source,
    software_plans,
    fake_writers,
)
pytestmark = [
    pytest.mark.parametrize("directory_fixture", [True]),
    pytest.mark.parametrize("source", [True], indirect=True),
    pytest.mark.parametrize("base_pair_source", [{"probe_spend": 1000}], indirect=True),
]


@pytest.fixture
def candidate(base_candidate):
    base_candidate[1].server.arguments = list(ARGUMENTS)
    return base_candidate


@pytest.fixture
def installed(base_installed):
    (base_installed / "eula.txt").write_text("eula=true\n")
    return base_installed


@pytest.fixture
def runtime(software_plans, tmp_path):
    service, plans, capacity, binding = software_plans
    helper = tmp_path / "StrataWriterLaunch.class"
    helper.write_bytes(b"synthetic JVM gate class")
    pin = {
        "path": str(helper),
        "bytes": helper.stat().st_size,
        "sha256": hashlib.sha256(helper.read_bytes()).hexdigest(),
    }
    launches = {}
    for index, (arm, plan) in enumerate(plans.items()):
        plan["max_wall_s"] = 240 if index == 0 else 180
        launches[arm] = {
            "schema": "strata/PrivateProbeVanillaLaunch/1",
            "policy": POLICY,
            "pair_id": "p1",
            "arm": arm,
            "helper_class": pin,
            "max_wall_s": 30,
            "max_stopped_state_bytes": 1024**2,
        }
    return service, plans, launches, binding, capacity


@pytest.fixture
def process_fixture(fake_writers, monkeypatch):
    from strata_evaluator import vanilla_writer
    from strata_evaluator.writer_custody import WriterCustody

    launched = []
    fail = {"history": False, "early_exit": False}

    def dispatch(writer, plan, inventory, arguments, ready, evidence, descriptor=None):
        launched.append(plan.arm)
        evidence.mkdir()
        (evidence / "server.stdout.log").write_text('Done (0.01s)! For help, type "help"\n')
        (evidence / "server.stderr.log").write_text("")
        (writer.tree.path / "world/session.lock").write_bytes(b"new synthetic game lock")
        status = {"stopped": fail["early_exit"], "forced": False}

        def terminal():
            return {
                "terminal_verified": not fail["history"],
                "logs_complete": True,
                "exit_code": 0,
                "forced": status["forced"],
            }

        job = SimpleNamespace(
            members={22: object()},
            accounting=lambda: {
                "total_processes": 2,
                "active_processes": 0,
                "terminated_processes": 0,
            },
            member_status=lambda: {
                "held_processes": 2,
                "signaled_processes": 1 if fail["history"] else 2,
            },
        )

        def send(text):
            assert text == "stop\n" and not status["stopped"]
            status["stopped"] = True

        process = SimpleNamespace(
            poll=lambda: 0 if status["stopped"] else None, job=job, send_input=send
        )
        native = SimpleNamespace(
            process=process,
            observe=process.poll,
            finish=terminal,
            shorten=lambda _: status.update(stopped=True, forced=True),
        )
        writer.native = native
        writer.result.update(challenge="synthetic", gate_identity={"pid": 11})
        writer.tree.security = SimpleNamespace(
            bind_process=lambda *args: {
                "held_token_verified": True,
                "read_isolation_qualified": False,
            }
        )
        ready.set()
        return native

    monkeypatch.setattr(WriterCustody, "_dispatch", dispatch)
    monkeypatch.setattr(vanilla_writer, "private_read", lambda *args: b"{}")
    monkeypatch.setattr(vanilla_writer, "java_identity", lambda *args: {"pid": 22})
    return launched, fail


def test_both_registered_servers_stop_export_and_keep_sibling_capture_immutable(
    runtime, process_fixture, directory_fixture
):
    service, plans, launches, binding, capacity = runtime
    from test_probe_pairs import EVALUATOR

    sessions = {}

    def observe(arm, session):
        from mcbench.launch_integrity import snapshot

        assert session.inputs == snapshot([launches[arm]["helper_class"]["path"]], [binding.instance])
        for path in (Path(launches[arm]["helper_class"]["path"]),
                     Path(binding.instance) / "server/server.jar"):
            with pytest.raises(PermissionError):
                with path.open("ab"):
                    pass
        with pytest.raises(Fault, match="PROBE_GAME_REFERENCE_INTENT"):
            service.preparation.release_undispatched_resources()
        if sessions:
            previous = next(iter(sessions.values()))
            path = Path(previous.result["snapshot"]["path"]) / "state/world/level.dat"
            with pytest.raises(PermissionError):
                path.write_bytes(b"change prior probe export")
        sessions[arm] = session
        (session.writer.tree.path / "world/level.dat").write_bytes(("outcome-" + arm).encode())
        return {"synthetic_observation": arm}

    result = service.run_vanilla_reference(
        EVALUATOR, plans, launches, continuation=observe, pack_binding=binding.model_dump()
    )
    assert process_fixture[0] == ["initial", "experienced"]
    assert [(e["arm"], e["phase"]) for e in result["runtime"]["events"][:2]] == [
        ("initial", "initial_state_held"),
        ("experienced", "initial_state_held"),
    ]
    assert (
        service.db.connection.execute("SELECT state FROM probe_world_copies").fetchone()[0]
        == "STOPPED_REFERENCE"
    )
    assert result["runtime"]["observations"] == {
        arm: {"synthetic_observation": arm} for arm in sessions
    }
    assert (
        not result["runtime"]["all_bodies_ready"]
        and not result["runtime"]["probe_disposal_verified"]
    )
    assert not result["native_launch_authorized"] and not result["live_initial_state_verified"]
    for arm, session in sessions.items():
        receipt = session.result["snapshot"]
        body = verify_snapshot(Path(receipt["path"]), receipt["manifest_sha256"])
        assert body["schema"] == "strata/StoppedVanillaSnapshot/3"
        assert body["probe_world"]["arm"] == arm
        assert not result["results"][arm]["custody"]["live"]
    from mcbench.controller import reserved_resources

    assert reserved_resources(service.db.connection, "probe-worker") == capacity
    assert (
        service.preparation.runtime.budgets.status("probe-total")["committed_and_reserved"][
            "spend_microusd"
        ]
        == 200
    )
    with pytest.raises(Fault, match="PROBE_GAME_REFERENCE_INTENT"):
        service.preparation.release_undispatched_resources()
    with pytest.raises(Fault, match="PROBE_WORLD_COPIES_CONSUMED|PROBE_WORLD_NAMESPACE"):
        service.run_vanilla_reference(
            EVALUATOR, plans, launches, continuation=observe, pack_binding=binding.model_dump()
        )


@pytest.mark.parametrize("failure", ["callback", "history", "early_exit"])
def test_failed_first_server_fences_pair_and_never_starts_sibling(
    runtime, process_fixture, directory_fixture, failure
):
    service, plans, launches, binding, _ = runtime
    from test_probe_pairs import EVALUATOR

    if failure != "callback":
        process_fixture[1][failure] = True

    def fail(*args):
        if failure == "callback":
            raise RuntimeError("synthetic callback failed")

    with pytest.raises((Fault, RuntimeError)):
        service.run_vanilla_reference(
            EVALUATOR, plans, launches, continuation=fail, pack_binding=binding.model_dump()
        )
    assert process_fixture[0] == ["initial"]
    row = service.db.connection.execute("SELECT state,body FROM probe_world_copies").fetchone()
    assert row["state"] == "FAILED" and "failure" in json.loads(row["body"])
    assert (
        service.db.connection.execute("SELECT state FROM probe_pair_custody").fetchone()[0]
        == "FENCED"
    )
    assert (
        service.preparation.runtime.budgets.status("probe-total")["committed_and_reserved"][
            "spend_microusd"
        ]
        == 200
    )


@pytest.mark.parametrize("failure", ["roster", "identity", "storage", "window"])
def test_pair_runtime_reserves_whole_scope_before_any_server(
    runtime, process_fixture, directory_fixture, failure
):
    service, plans, launches, binding, _ = runtime
    from test_probe_pairs import EVALUATOR

    if failure == "roster":
        del launches["experienced"]
    elif failure == "identity":
        launches["initial"]["arm"] = "experienced"
    elif failure == "storage":
        for plan in launches.values():
            plan["max_stopped_state_bytes"] = 1024**3
    else:
        for plan in launches.values():
            plan["max_wall_s"] = 120
    with pytest.raises(
        Fault,
        match="PROBE_WORLD_ROSTER|PROBE_WORLD_IDENTITY|PROBE_STORAGE_LIMIT|PROBE_WORLD_DEADLINE",
    ):
        service.run_vanilla_reference(
            EVALUATOR,
            plans,
            launches,
            continuation=lambda *_: None,
            pack_binding=binding.model_dump(),
        )
    assert not process_fixture[0]


def test_second_arm_missing_launch_helper_refuses_before_either_server(
    runtime, process_fixture, directory_fixture
):
    from test_probe_pairs import EVALUATOR

    service, plans, launches, binding, _ = runtime
    old = Path(launches["experienced"]["helper_class"]["path"])
    launches["experienced"]["helper_class"]["path"] = str(
        old.parent / "missing" / "StrataWriterLaunch.class"
    )
    with pytest.raises(Fault):
        service.run_vanilla_reference(
            EVALUATOR,
            plans,
            launches,
            continuation=lambda *_: None,
            pack_binding=binding.model_dump(),
        )
    assert not process_fixture[0]
    assert (
        service.db.connection.execute("SELECT state FROM probe_world_copies").fetchone()[0]
        == "FAILED"
    )


@pytest.mark.parametrize("change", ["empty_directory", "account", "expiry", "software_lease"])
def test_joint_preflight_revalidates_after_first_session_before_either_dispatch(
    runtime, process_fixture, directory_fixture, monkeypatch, change
):
    from strata_evaluator.probe_vanilla_runtime import ProbeVanillaSession
    from mcbench.launch_integrity import IntegrityError
    from test_probe_pairs import EVALUATOR

    service, plans, launches, binding, capacity = runtime
    original = ProbeVanillaSession.__init__
    constructed = []

    def changed(session, owner, arm):
        original(session, owner, arm)
        constructed.append(arm)
        if len(constructed) == 1:
            if change == "empty_directory":
                (Path(binding.instance) / "server/libraries/unbound").mkdir()
            elif change == "account":
                service.db.connection.execute("UPDATE accounts SET category='training' WHERE id='initial-account'")
            elif change == "expiry":
                service.preparation.deadline = service.preparation.monotonic() - 1
            else:
                owner.held.software.lease.close()

    monkeypatch.setattr(ProbeVanillaSession, "__init__", changed)
    with pytest.raises((Fault, IntegrityError),
                       match="MATERIALIZATION_CHANGED|NATIVE_PROBE_ACCOUNT|PROBE_CUSTODY_EXPIRED|BOOTSTRAP_LEASE_CLOSED"):
        service.run_vanilla_reference(EVALUATOR, plans, launches, continuation=lambda *_: None,
                                     pack_binding=binding.model_dump())
    assert constructed and not process_fixture[0]
    assert service.db.connection.execute("SELECT state FROM probe_pair_custody").fetchone()[0] == "FENCED"
    row = service.db.connection.execute("SELECT resources,released FROM probe_pair_resources").fetchone()
    assert not row['released'] and json.loads(row['resources']) == capacity
    assert service.preparation.runtime.budgets.status("probe-total")["committed_and_reserved"]["spend_microusd"] == 200


@pytest.mark.parametrize("phase", ["launch_intent", "stopped_export_held"])
def test_changed_authority_at_launch_boundary_never_dispatches_next_server(
    runtime, process_fixture, directory_fixture, monkeypatch, phase
):
    from strata_evaluator.probe_vanilla_runtime import PairedVanillaRuntime
    from test_probe_pairs import EVALUATOR

    service, plans, launches, binding, capacity = runtime
    original = PairedVanillaRuntime.event

    def changed(owner, arm, current):
        original(owner, arm, current)
        if arm == "initial" and current == phase:
            service.db.connection.execute("UPDATE accounts SET category='training' WHERE id='initial-account'")

    monkeypatch.setattr(PairedVanillaRuntime, "event", changed)
    with pytest.raises(Fault, match="NATIVE_PROBE_ACCOUNT"):
        service.run_vanilla_reference(EVALUATOR, plans, launches, continuation=lambda *_: None,
                                     pack_binding=binding.model_dump())
    assert process_fixture[0] == ([] if phase == "launch_intent" else ["initial"])
    assert service.db.connection.execute("SELECT state FROM probe_pair_custody").fetchone()[0] == "FENCED"
    row = service.db.connection.execute("SELECT resources,released FROM probe_pair_resources").fetchone()
    assert not row['released'] and json.loads(row['resources']) == capacity
    assert service.preparation.runtime.budgets.status("probe-total")["committed_and_reserved"]["spend_microusd"] == 200


@pytest.mark.parametrize("changed_source", [False, True])
def test_held_plan_factory_keeps_custody_and_full_source_validation(
    runtime, process_fixture, directory_fixture, changed_source
):
    from test_probe_pairs import EVALUATOR

    service, plans, launches, binding, _ = runtime
    called = []

    def factory(software):
        called.append(software)
        software.check()
        with pytest.raises(PermissionError):
            with Path(binding.instance, "server/server.jar").open("ab"):
                pass
        if changed_source:
            plans["initial"]["sources"]["world/level.dat"]["sha256"] = "0" * 64
        return plans

    if changed_source:
        with pytest.raises(Fault, match="PROBE_WORLD_SOURCE"):
            service.run_vanilla_reference(EVALUATOR, factory, launches,
                continuation=lambda *_: None, pack_binding=binding.model_dump())
        assert process_fixture[0] == []
    else:
        result = service.run_vanilla_reference(EVALUATOR, factory, launches,
            continuation=lambda *_: None, pack_binding=binding.model_dump())
        assert set(result["runtime"]["servers"]) == {"initial", "experienced"}
        assert process_fixture[0] == ["initial", "experienced"]
    assert len(called) == 1 and called[0].closed
