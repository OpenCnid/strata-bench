"""Sealed synthetic world/pack bytes with real leases; dispatch is substituted."""

import hashlib
from pathlib import Path
import shutil
import time
from types import SimpleNamespace

import pytest

from mcbench.launch_integrity import safe, snapshot
from mcbench.pack_restore import restore_pack_instance
from mcbench.storage import Fault
from strata_evaluator.craft_reference import PrivateFile
from strata_evaluator.vanilla_writer import VanillaWriterSession, POLICY, ARGUMENTS
from strata_evaluator.writer_custody import WriterCustody
from strata_evaluator.writer_preparation import parse_preparation_plan, CODEX_SHA256
from test_pack_restore import source, inputs, candidate as base_candidate, sealed_installation
from test_vanilla_persistence import installed as base_installed

source, inputs, base_candidate, sealed_installation, base_installed = (
    source,
    inputs,
    base_candidate,
    sealed_installation,
    base_installed,
)


@pytest.fixture
def candidate(base_candidate):
    # Select this fixture's reviewed launch before sealing its synthetic pack.
    base_candidate[1].server.arguments = list(ARGUMENTS)
    return base_candidate


@pytest.fixture
def installed(base_installed):
    (base_installed / "eula.txt").write_text("eula=true\n")
    return base_installed


@pytest.fixture
def vanilla(source, tmp_path):
    fresh, reference, _ = source
    binding = restore_pack_instance(fresh, reference, tmp_path / "restored")
    original = Path(binding.instance) / "server"
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    root = workspace / "guarded"
    shutil.copytree(original, root)
    files = snapshot([], [original])["files"]

    def pin(path):
        return {
            "path": str(path),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "bytes": path.stat().st_size,
        }

    java = tmp_path / "external-java/bin/java.exe"
    helper = tmp_path / "StrataWriterLaunch.class"
    helper.write_bytes(b"synthetic held launch helper")
    plan = parse_preparation_plan(
        {
            "schema": "strata/PrivateWriterPreparationPlan/4",
            "id": "vanilla",
            "network_policy": "native-online-private-server/1",
            "staging_policy": "sequential-bundles512mib/1",
            "evidence_kind": "authentic_operator_reference",
            "codex": {"path": str(tmp_path / "codex.exe"), "sha256": CODEX_SHA256, "bytes": 8},
            "java": pin(java),
            "helper_class": {
                "path": str(tmp_path / "StrataWriterPreparation.class"),
                "sha256": "a" * 64,
                "bytes": 8,
            },
            "sandbox_home": str(tmp_path / "home"),
            "writer_sid": "S-1-5-21-1-2-3-1003",
            "source_root": str(original),
            "workspace_directory": str(workspace),
            "evidence_directory": str(tmp_path / "evidence"),
            "max_wall_s": 120,
            "sources": {safe(p["path"]).relative_to(safe(original)).as_posix(): p for p in files},
            "directories": [
                p.relative_to(original).as_posix() for p in original.rglob("*") if p.is_dir()
            ],
        }
    )
    (tmp_path / "evidence").mkdir()
    records = []
    writer = WriterCustody(
        plan,
        SimpleNamespace(path=root, group_sid="group", scope_sid="scope", verify=lambda: None),
        SimpleNamespace(path=workspace, verify_enrolled=lambda *_: None),
        [],
        time.monotonic() + 120,
        {},
        lambda *args: records.append(args),
    )
    dispatched = []

    def dispatch(p, inventory, arguments, ready, evidence, descriptor=None):
        dispatched.append((p, inventory, arguments, ready, evidence, descriptor))
        return SimpleNamespace()

    writer._dispatch = dispatch
    value = {
        "schema": "strata/PrivateVanillaWriterLaunch/1",
        "policy": POLICY,
        "binding": binding.model_dump(),
        "helper_class": pin(helper),
        "max_wall_s": 30,
    }
    yield writer, value, dispatched, records
    writer.close()


def test_sealed_restored_clone_uses_exact_launch_and_holds_software(vanilla):
    writer, value, dispatched, _ = vanilla
    session = VanillaWriterSession(writer, value)
    assert len(dispatched) == 1 and dispatched[0][2][-len(ARGUMENTS) :] == ARGUMENTS
    assert dispatched[0][5] is None and writer.broker is None
    assert not session.result["probe_admission"] and not session.result["authoritative_ticks"]
    for path in (Path(writer.plan.source_root) / "server.jar", writer.tree.path / "server.jar"):
        with pytest.raises(PermissionError):
            path.write_bytes(b"changed")
    with pytest.raises(Fault, match="WRITER_CUSTODY_ALREADY_LAUNCHED"):
        VanillaWriterSession(writer, value)


def test_distinct_body_observer_plan_composes_before_dispatch(vanilla, monkeypatch):
    from strata_evaluator import vanilla_writer
    writer, value, dispatched, _ = vanilla
    value.update(schema="strata/PrivateVanillaWriterLaunch/2", policy=vanilla_writer.BODY_POLICY,
        body_observer={"schema": "strata/PrivateBodyObserverLaunch/1", "campaign_id": "c", "epoch": 1,
            "run_id": "r", "roster": ["00000000-0000-0000-0000-000000000001"], "module": value["helper_class"]})
    observer = SimpleNamespace(arguments=["-XX:+DisableAttachMechanism", "-javaagent:synthetic"],
        binding={"synthetic_binding": True}, inventory={"files": [{"synthetic_module": True}]})
    monkeypatch.setattr(vanilla_writer, "HeldBodyObserver", lambda *_: observer)
    session = VanillaWriterSession(writer, value)
    assert session.observer is observer and dispatched[0][2][:2] == observer.arguments
    assert dispatched[0][1]["files"][-1] == {"synthetic_module": True}
    assert writer.result["capability"] == "native-private-vanilla-custody/2"
    assert session.result["policy"] == vanilla_writer.BODY_POLICY and not session.result["probe_admission"]


@pytest.mark.parametrize("field,value", [("campaign_id", "foreign"), ("epoch", 2), ("expected_player_uuid", "foreign")])
def test_observed_single_worker_scope_refuses_before_import(vanilla, tmp_path, monkeypatch, field, value):
    from strata_evaluator import vanilla_writer
    writer, launch, dispatched, _ = vanilla
    player = "00000000-0000-0000-0000-000000000001"
    launch.update(schema="strata/PrivateVanillaWriterLaunch/2", policy=vanilla_writer.BODY_POLICY,
        body_observer={"schema": "strata/PrivateBodyObserverLaunch/1", "campaign_id": "c", "epoch": 1,
            "run_id": "r", "roster": [player], "module": launch["helper_class"]})
    invocation = {"campaign_id": "c", "epoch": 1, "expected_player_uuid": player, field: value}
    monkeypatch.setattr(vanilla_writer, "HeldPackWorker", lambda *_: pytest.fail("unexpected worker import"))
    with pytest.raises(Fault, match="BODY_WORKER_SCOPE"):
        vanilla_writer.run_vanilla_worker(writer, launch, invocation, tmp_path)
    assert not writer.launched and not dispatched


@pytest.mark.parametrize("failure", [None, "body", "terminal"])
def test_body_capture_precedes_job_close_and_cannot_promote_failed_stop(vanilla, monkeypatch, failure):
    from strata_evaluator import vanilla_writer
    writer, value, _, _ = vanilla
    session = VanillaWriterSession(writer, value)
    events = []
    session.result.update(ready=True, stop_requested=True)
    monkeypatch.setattr(session.persistence, "capture", lambda *a, **kw: {"synthetic_snapshot": True})
    monkeypatch.setattr(vanilla_writer, "inspect_server_log", lambda *_: {"result": "pass"})
    def capture(*_):
        events.append("capture")
        if failure == "body":
            raise Fault("BODY_SYNTHETIC_FAILURE")
        return {"synthetic_body": True}
    def finish():
        events.append("job_close")
        return {"terminal_verified": failure != "terminal", "logs_complete": True, "exit_code": 0, "forced": False}
    session.observer = SimpleNamespace(capture=capture)
    session.native = SimpleNamespace(observe=lambda: 0, finish=finish, process=object())
    if failure:
        with pytest.raises(Fault):
            session.finish()
        assert not writer.completed and "body_observer" not in session.result
    else:
        session.finish()
        assert writer.completed and session.result["body_observer"] == {"synthetic_body": True}
    assert events == (["capture"] if failure == "body" else ["capture", "job_close"])


@pytest.mark.parametrize(
    "change,code",
    [
        ("synthetic", "VANILLA_WRITER_PROFILE"),
        ("source", "VANILLA_WRITER_SOURCE"),
        ("missing_directory", "VANILLA_WRITER_SOURCE"),
        ("java", "VANILLA_WRITER_PROFILE"),
        ("pack", "PACK_BINDING_MISMATCH"),
        ("extra_world", "CRAFT_FIXTURE_INVENTORY_CHANGED"),
    ],
)
def test_wrong_scope_or_changed_clone_never_dispatches(vanilla, change, code):
    writer, value, dispatched, _ = vanilla
    if change == "synthetic":
        writer.plan.evidence_kind = "synthetic"
    elif change == "source":
        original = writer.plan.sources["world/level.dat"]
        writer.plan.sources["world/level.dat"] = PrivateFile(
            **(original.model_dump() | {"sha256": "a" * 64})
        )
    elif change == "missing_directory":
        (writer.tree.path / "world/datapacks").rmdir()
    elif change == "java":
        writer.plan.java = PrivateFile(**(writer.plan.java.model_dump() | {"sha256": "a" * 64}))
    elif change == "pack":
        value["binding"]["lock"] = "cas:sha256:" + "b" * 64
    else:
        (writer.tree.path / "foreign.txt").write_text("unreviewed")
    with pytest.raises(Fault, match=code):
        VanillaWriterSession(writer, value)
    assert not dispatched and writer.launched and not writer.completed


@pytest.mark.parametrize(
    "fault", [None, "not_ready", "no_stop", "running", "capture", "history", "forced", "logs"]
)
def test_finish_requires_ready_owned_normal_stop_and_saved_state(vanilla, monkeypatch, fault):
    from strata_evaluator import vanilla_writer

    writer, value, _, records = vanilla
    session = VanillaWriterSession(writer, value)
    session.result.update(ready=fault != "not_ready", stop_requested=fault != "no_stop")
    native = SimpleNamespace(
        observe=lambda: None if fault == "running" else 0,
        finish=lambda: {
            "terminal_verified": fault != "history",
            "logs_complete": True,
            "exit_code": 0,
            "forced": fault == "forced",
        },
        shorten=lambda _: None,
        process=object(),
    )
    session.native = writer.native = native

    def capture(*args, **kwargs):
        if fault == "capture":
            raise Fault("SYNTHETIC_CAPTURE_FAILURE")
        return {"synthetic_saved_state": True}

    monkeypatch.setattr(session.persistence, "capture", capture)
    monkeypatch.setattr(
        vanilla_writer,
        "inspect_server_log",
        lambda _: {"result": "fail" if fault == "logs" else "pass"},
    )
    if fault:
        with pytest.raises(
            Fault,
            match="VANILLA_WRITER_UNFINISHED|SYNTHETIC_CAPTURE_FAILURE|WRITER_CUSTODY_TERMINAL_UNCERTAIN|SERVER_RUNTIME_FAILURE",
        ):
            session.finish()
        assert not writer.completed
    else:
        result = session.finish()
        assert (
            result["status"] == "stopped"
            and writer.completed
            and records[-1][1] == "CUSTODY_STOPPED"
        )
        assert result["vanilla"]["snapshot"] == {"synthetic_saved_state": True}


@pytest.mark.parametrize("preflight_exit", [0, 1])
def test_worker_import_precedes_server_and_failed_import_never_launches(
    vanilla, tmp_path, monkeypatch, preflight_exit
):
    from strata_evaluator import vanilla_writer

    writer, value, _, _ = vanilla
    events = []
    output = tmp_path.parent / (tmp_path.name + "-pipeline")
    output.mkdir()

    class Worker:
        resolved = {"worker_configuration": {}}

        def __enter__(self):
            events.append("worker_inputs")
            return self

        def __exit__(self, *_):
            events.append("worker_close")

        def start(self, *, preflight=False):
            assert preflight
            events.append("import")
            return SimpleNamespace(poll=lambda: preflight_exit)

    monkeypatch.setattr(vanilla_writer, "HeldPackWorker", lambda *_: Worker())
    monkeypatch.setattr(
        vanilla_writer,
        "_ProcessOutput",
        lambda *_: SimpleNamespace(finish=lambda: events.append("import_logs")),
    )

    def server(*_):
        events.append("server")
        raise Fault("SYNTHETIC_SERVER_SENTINEL")

    monkeypatch.setattr(vanilla_writer, "VanillaWriterSession", server)
    with pytest.raises(
        Fault, match="WORKER_PREFLIGHT_FAILED" if preflight_exit else "SYNTHETIC_SERVER_SENTINEL"
    ):
        vanilla_writer.run_vanilla_worker(writer, value, {}, output)
    assert events == [
        "worker_inputs",
        "import",
        "import_logs",
        *(["server"] if preflight_exit == 0 else []),
        "worker_close",
    ]


@pytest.mark.parametrize("running", [True, False])
def test_parent_game_flag_requires_owned_ready_child(vanilla, monkeypatch, running):
    from strata_evaluator import vanilla_writer

    writer, value, _, _ = vanilla
    session = VanillaWriterSession(writer, value)
    assert writer.body["game_launch_attempted"] is True
    assert not writer.body.get("game_launched", False)
    session.ready.set()
    session.native = SimpleNamespace(
        observe=lambda: None if running else 0,
        process=SimpleNamespace(job=SimpleNamespace(members={22: object()})),
    )
    writer.result["challenge"] = "challenge"
    writer.result["gate_identity"] = {"pid": 11}
    writer.tree.security = SimpleNamespace(bind_process=lambda *args: {"held_token_verified": True})
    monkeypatch.setattr(vanilla_writer, "private_read", lambda *args: b"{}")
    monkeypatch.setattr(vanilla_writer, "java_identity", lambda *args: {"pid": 22})
    if running:
        result = session.verify_ready()
        assert writer.body["game_launched"] is True and result["ready"]
        assert writer.result["scoring_eligible"] is False
        assert writer.result["setup_authority_qualified"] is False
    else:
        with pytest.raises(Fault, match="VANILLA_WRITER_NOT_READY"):
            session.verify_ready()
        assert not writer.body.get("game_launched", False)
