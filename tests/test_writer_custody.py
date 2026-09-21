"""Custody lifecycle/fault controls; actual native gate evidence is separate."""

import threading
import time
from types import SimpleNamespace

import pytest

from mcbench.storage import Fault
from strata_evaluator.writer_custody import WriterCustody, WriterLaunchPlan


@pytest.fixture
def held():
    order, records = [], []
    tree = SimpleNamespace(group_sid="group", scope_sid="scope", verify=lambda: order.append("tree"))
    workspace = SimpleNamespace(verify_enrolled=lambda *_: order.append("workspace"))
    original = SimpleNamespace(recheck=lambda: order.append("original"))
    custody = WriterCustody(SimpleNamespace(id="one", schema_="strata/PrivateWriterPreparationPlan/1",
                                            evidence_kind="synthetic"), tree, workspace, [original],
                            time.monotonic() + 10, {}, lambda *args: records.append(args))
    return custody, order, records


def test_closed_or_foreign_thread_cannot_reuse_live_custody(held):
    custody, order, _ = held
    custody.check()
    assert order == ["workspace", "tree", "original"]
    errors = []
    def foreign():
        try:
            custody.check()
        except Fault as error:
            errors.append(error.code)
    thread = threading.Thread(target=foreign)
    thread.start()
    thread.join()
    assert errors == ["WRITER_CUSTODY_CLOSED"]
    custody.close()
    assert not custody.result["live"] and custody.result["status"] == "uncertain"
    with pytest.raises(Fault, match="WRITER_CUSTODY_CLOSED"):
        custody.check()


def test_no_native_process_or_unfinished_process_cannot_be_success(held):
    custody, _, _ = held
    with pytest.raises(Fault, match="WRITER_CUSTODY_LAUNCH_MISSING"):
        custody.finish()
    custody.launched = True
    custody.native = SimpleNamespace(observe=lambda: None)
    with pytest.raises(Fault, match="WRITER_CUSTODY_UNFINISHED"):
        custody.finish()
    assert custody.result["status"] == "held"


@pytest.mark.parametrize("fault", ["native", "broker"])
def test_cleanup_keeps_added_leases_until_native_and_broker_cleanup_attempted(held, fault):
    custody, order, _ = held
    def finish():
        assert custody.closed
        order.append("native")
        if fault == "native":
            raise Fault("INJECTED_NATIVE")
        return {"terminal_verified": True}
    def close():
        order.append("broker")
        if fault == "broker":
            raise Fault("INJECTED_BROKER")
        return {"status": "uncertain"}
    custody.native = SimpleNamespace(shorten=lambda _: None, finish=finish)
    custody.broker = SimpleNamespace(close=close)
    custody.leases = [SimpleNamespace(close=lambda: order.append("added_lease"))]
    with pytest.raises(Fault, match="INJECTED"):
        custody.close()
    assert order == ["native", "broker", "added_lease"]
    custody.close()
    assert order == ["native", "broker", "added_lease"]


@pytest.mark.parametrize("fault", ["history", "broker"])
def test_uncertain_broker_or_process_history_cannot_close_custody(held, fault):
    custody, _, records = held
    custody.launched = True
    terminal = {"terminal_verified": fault != "history", "logs_complete": True, "exit_code": 0, "forced": False}
    custody.native = SimpleNamespace(observe=lambda: 0, finish=lambda: terminal)
    custody.broker = SimpleNamespace(close=lambda: {"status": "uncertain" if fault == "broker" else "stopped"})
    with pytest.raises(Fault, match="WRITER_CUSTODY_TERMINAL_UNCERTAIN"):
        custody.finish()
    assert not custody.completed and not records and custody.result["terminal"] == terminal


def test_launch_profile_cannot_label_a_game_as_an_admitted_fixture():
    with pytest.raises(ValueError):
        WriterLaunchPlan.model_validate({"schema": "strata/PrivateWriterLaunch/1",
                                        "mode": "e9e-serverstarter"})


@pytest.mark.parametrize("change,code", [("relative_classpath", "WRITER_LAUNCH_PROFILE"),
    ("private_descriptor", "WRITER_LAUNCH_PROFILE"), ("foreign_world", "WRITER_LAUNCH_PROFILE"),
    ("unpinned_classpath", "WRITER_LAUNCH_UNPINNED")])
def test_changed_launch_paths_reject_before_reading_or_dispatch(held, tmp_path, monkeypatch, change, code):
    from strata_evaluator import writer_custody
    custody, _, _ = held
    workspace = tmp_path / "workspace"
    game, descriptor, classes = workspace / "guarded", workspace / "control/config.json", workspace / "classes"
    module, java = game / "module.jar", tmp_path / "java.exe"
    custody.workspace.path, custody.tree.path = workspace, game
    custody.plan.java = SimpleNamespace(path=str(java))
    custody.plan.writer_sid = "writer"
    broker = SimpleNamespace(setup=SimpleNamespace(game_directory=str(game)),
        plan=SimpleNamespace(executable=SimpleNamespace(path=str(java)),
                             module_file=SimpleNamespace(path=str(module)), server_port=25569),
        writer_sid="writer", group_sid="group", scope_sid="scope", deadline=custody.deadline)
    def pin(path):
        return {"path": str(path), "bytes": 1, "sha256": "a" * 64}
    plan = {"schema": "strata/PrivateWriterLaunch/1", "mode": "synthetic-fixture",
        "helper_class": pin(tmp_path / "StrataWriterLaunch.class"),
        "immutable_files": [pin(descriptor), pin(module)], "immutable_trees": [str(classes)],
        "arguments": ["-cp", str(classes), "io.github.opencnid.strata.telemetry.OwnedLaunchFixture",
                      str(descriptor), str(game), str(module), "25569", "normal"], "max_wall_s": 15}
    if change == "relative_classpath":
        plan["arguments"][1] = "classes"
    elif change == "private_descriptor":
        plan["arguments"][3] = str(tmp_path / "private-config.json")
    elif change == "foreign_world":
        plan["arguments"][4] = str(tmp_path / "foreign-world")
    else:
        plan["immutable_trees"] = []
    def forbidden(*_):
        raise AssertionError("Must reject before any read or dispatch")
    monkeypatch.setattr(writer_custody, "check_file", forbidden)
    monkeypatch.setattr(writer_custody, "ManagedProcess", forbidden)
    with pytest.raises(Fault, match=code):
        custody.launch(plan, broker)
