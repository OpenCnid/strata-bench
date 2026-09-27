"""Synthetic producer/jobs plus actual Windows input/output file custody.

No native producer, Minecraft capture or isolation qualification is implied.
"""

import json
import os
from pathlib import Path
from types import SimpleNamespace
import zipfile

import pytest

from mcbench.storage import Fault, canonical
from strata_evaluator.player_body_custody import HeldBodyObserver
from strata_evaluator.player_body_evidence import MODULE_SHA, sha
from test_player_body_evidence import SCOPE, fixture, official
from test_probe_saved_bodies import PLAYER

official = official


@pytest.fixture
def held(official, tmp_path):
    module = os.environ.get("STRATA_BODY_AGENT_JAR")
    if os.name != "nt" or not module:
        pytest.skip("Windows and explicit pinned body observer required")
    source = Path(module)
    assert sha(source.read_bytes()) == MODULE_SHA
    workspace, game = tmp_path / "workspace", tmp_path / "game"
    workspace.mkdir()
    server = game / "versions/1.19.2/server-1.19.2.jar"
    server.parent.mkdir(parents=True)
    server.write_bytes(official[0])
    leases = []
    writer = SimpleNamespace(workspace=SimpleNamespace(path=workspace), tree=SimpleNamespace(path=game), leases=leases)
    writer.check = lambda: [lease.recheck() for lease in leases]
    plan = {"schema": "strata/PrivateBodyObserverLaunch/1", **SCOPE, "roster": [PLAYER],
            "module": {"path": str(source), "bytes": source.stat().st_size, "sha256": MODULE_SHA}}
    observer = HeldBodyObserver(writer, plan)
    observer.output.mkdir()
    with zipfile.ZipFile(source) as jar:
        (observer.stage / "body-observer-callbacks.jar").write_bytes(jar.read("body-observer-callbacks.jar"))
    files, records = fixture(official)
    records[0]["body"]["config_sha256"] = observer.config_sha
    (observer.output / "events.jsonl").write_bytes(canonical(records[0]) + b"\n")
    identity = {"pid": 123, "executable": "synthetic-java.exe", "process_started_unix_ms": 123456}
    state = {"exit": None, "identity": identity, "terminated": 0}
    job = SimpleNamespace(handle=object(), members={123: object()}, member_identity=lambda _: state["identity"],
        accounting=lambda: {"active_processes": int(state["exit"] is None), "terminated_processes": state["terminated"], "total_processes": 1},
        member_status=lambda: {"held_processes": 1, "signaled_processes": int(state["exit"] is not None)})
    process = SimpleNamespace(poll=lambda: state["exit"], job=job)
    try:
        yield observer, writer, process, identity, state, files, records
    finally:
        for lease in reversed(leases):
            lease.close()


def complete(held):
    observer, _, _, _, state, files, records = held
    for name, raw in files.items():
        (observer.output / name).write_bytes(raw)
    (observer.output / "events.jsonl").write_bytes(b"".join(canonical(row) + b"\n" for row in records))
    state["exit"] = 0


def test_staged_inputs_and_export_remain_held_through_owner_cleanup(held, tmp_path):
    observer, writer, process, identity, _, _, _ = held
    for path in (observer.module, observer.config, observer.server):
        with pytest.raises(PermissionError):
            path.write_bytes(b"changed")
    observer.observe(process, identity)
    with pytest.raises(PermissionError):
        (observer.stage / "body-observer-callbacks.jar").write_bytes(b"changed")
    complete(held)
    report = observer.capture(writer, process, tmp_path / "export")
    assert report["content_verified"] and report["owned_producer_verified"]
    assert not report["live_initial_state_verified"] and not report["native_probe_admission"]
    assert report["owned_jvm"] == identity
    for root in (observer.output, tmp_path / "export"):
        with pytest.raises(PermissionError):
            (root / (PLAYER + ".nbt")).write_bytes(b"changed")
    with pytest.raises(Fault, match="BODY_PROCESS_SCOPE"):
        observer.capture(writer, process, tmp_path / "second-export")


def test_capture_wait_preserves_live_partial_attempt_until_complete_roster(held):
    observer, _, process, identity, _, _, records = held
    observer.observe(process, identity)
    assert not observer.capture_ready(process)
    path = observer.output / "events.jsonl"
    raw = b"".join(canonical(row) + b"\n" for row in records[:3])
    path.write_bytes(raw[:-1])
    assert not observer.capture_ready(process)
    path.write_bytes(raw)
    assert observer.capture_ready(process)
    records[2]["body"]["bodies"] = []
    path.write_bytes(b"".join(canonical(row) + b"\n" for row in records[:3]))
    with pytest.raises(Fault, match="BODY_CAPTURE_ROSTER"):
        observer.capture_ready(process)


@pytest.mark.parametrize("case", ["pid", "identity", "config", "callback", "stopped"])
def test_wrong_live_producer_never_binds(held, case):
    observer, _, process, identity, state, _, _ = held
    if case == "pid":
        process.job.members = {}
    elif case == "identity":
        state["identity"] = identity | {"process_started_unix_ms": 7}
    elif case == "config":
        path = observer.output / "events.jsonl"
        value = json.loads(path.read_bytes())
        value["body"]["config_sha256"] = "b" * 64
        path.write_bytes(canonical(value) + b"\n")
    elif case == "callback":
        (observer.stage / "body-observer-callbacks.jar").write_bytes(b"changed")
    else:
        state["exit"] = 0
    with pytest.raises(Fault):
        observer.observe(process, identity)
    assert observer.identity is None


@pytest.mark.parametrize("case", ["running", "terminated", "foreign_process", "foreign_job", "closed_job", "member_handle", "missing", "extra_directory", "nbt"])
def test_incomplete_owned_output_never_captures(held, tmp_path, case):
    observer, writer, process, identity, state, _, _ = held
    observer.observe(process, identity)
    complete(held)
    if case == "running":
        state["exit"] = None
    elif case == "terminated":
        state["terminated"] = 1
    elif case == "foreign_process":
        process = SimpleNamespace(**vars(process))
    elif case == "foreign_job":
        process.job = SimpleNamespace(**vars(process.job))
    elif case == "closed_job":
        process.job.handle = None
    elif case == "member_handle":
        process.job.members[identity["pid"]] = object()
    elif case == "missing":
        (observer.output / "loaded-classes.txt").unlink()
    elif case == "extra_directory":
        (observer.output / "foreign").mkdir()
    else:
        (observer.output / (PLAYER + ".nbt")).write_bytes(b"changed")
    with pytest.raises(Fault):
        observer.capture(writer, process, tmp_path / "rejected-export")
    assert not observer.captured and not (tmp_path / "rejected-export").exists()


@pytest.mark.skipif(os.name != "nt", reason="Actual Windows process-handle continuity")
def test_live_identity_retained_through_real_normal_exit(held, tmp_path):
    import sys
    import time
    from mcbench.processes import ManagedProcess

    observer, writer, _, _, _, _, records = held
    process = ManagedProcess([sys.executable, "-I", "-c",
        "import os,sys; print(os.getpid(),flush=True); assert sys.stdin.readline().strip()=='stop'"],
        tmp_path, {}, "", interactive=True)
    try:
        pid = int(process.process.stdout.readline())
        process.job.observe_members()
        identity = process.job.member_identity(pid)
        records[0]["body"]["pid"] = pid
        (observer.output / "events.jsonl").write_bytes(canonical(records[0]) + b"\n")
        observer.observe(process, identity)
        complete(held)  # Synthetic capture bytes, authentic owned process lifetime.
        process.send_input("stop\n")
        assert process.process.wait(timeout=10) == 0
        deadline = time.monotonic() + 5
        while process.job.accounting()["active_processes"] and time.monotonic() < deadline:
            time.sleep(0.01)
        # A stopped-process image query must not be a capture prerequisite.
        def unavailable(_):
            raise AssertionError("must use the already authenticated retained handle")
        process.job.member_identity = unavailable
        report = observer.capture(writer, process, tmp_path / "real-process-export")
        assert report["owned_jvm"] == identity and report["owned_producer_verified"]
        assert report["owned_processes"]["job"]["active_processes"] == 0
        assert not report["live_initial_state_verified"]
    finally:
        process.close()
