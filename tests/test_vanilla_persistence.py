"""Synthetic saves with actual Windows file leases and one owned Python process."""

import hashlib
import os
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

from mcbench import vanilla_persistence as persistence
from mcbench.launch_integrity import IntegrityError
from mcbench.processes import ManagedProcess
from mcbench.storage import Fault

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from development_server import validate_persistence_profile


@pytest.fixture
def installed(tmp_path, monkeypatch):
    root = tmp_path / "synthetic-instance"
    root.mkdir()
    files = {p: b"[]" for p in persistence.MUTABLE}
    files |= {"eula.txt": b"synthetic fixture", "server.jar": b"synthetic bundler",
              "versions/1.19.2/server-1.19.2.jar": b"synthetic game",
              "libraries/library.jar": b"synthetic dependency", "world/level.dat": b"synthetic world",
              "world/session.lock": b"synthetic lock", "logs/latest.log": b"diagnostic log"}
    for name, raw in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    (root / "world/datapacks").mkdir()
    # Only tests substitute artifact pins. The operator profile has no override.
    monkeypatch.setattr(persistence, "PINNED_JARS", {p: hashlib.sha256(files[p]).hexdigest()
                                                   for p in persistence.PINNED_JARS})
    return root


def stopped():
    return SimpleNamespace(poll=lambda: 0, job=SimpleNamespace(
        accounting=lambda: {"total_processes": 2, "active_processes": 0, "terminated_processes": 0},
        member_status=lambda: {"held_processes": 2, "signaled_processes": 2}))


def test_layout_accepts_normal_and_extended_windows_paths(installed):
    assert persistence.layout(installed)[1:] == persistence.layout(persistence.safe(installed))[1:]


def capture(root, target, process=None):
    service = persistence.VanillaPersistence(root)
    try:
        return service.capture(target, process or stopped(), plan_digest="a" * 64)
    finally:
        service.close()


@pytest.mark.skipif(os.name != "nt", reason="Windows file lease qualification")
def test_complete_explicit_disposition_and_actual_immutable_lease(installed, tmp_path):
    service = persistence.VanillaPersistence(installed)
    target = tmp_path / "stopped"
    try:
        with pytest.raises(OSError):
            (installed / "server.jar").write_bytes(b"changed")
        result = service.capture(target, stopped(), plan_digest="a" * 64)
        body = persistence.verify_snapshot(target, result["manifest_sha256"])
        assert not body["clean_save_proven"] and not body["complete_checkpoint"]
        assert not body["writer_custody_qualified"] and not body["dispatch_authorized"]
        assert body["owned_processes"]["complete_owned_process_history"]
        assert body["files"]["world/session.lock"]["disposition"] == "transient_session_lock"
        assert body["files"]["logs/latest.log"]["disposition"] == "diagnostic_log"
        assert body["files"]["server.jar"]["disposition"] == "immutable"
        assert (target / "state/world/datapacks").is_dir()
        assert not (target / "state/world/session.lock").exists()
        assert not (target / "state/logs").exists() and not (target / "state/server.jar").exists()
        for path, entry in body["files"].items():
            if entry["disposition"] == "state":
                assert (target / "state" / path).read_bytes() == (installed / path).read_bytes()
        with pytest.raises(Fault, match="VANILLA_CAPTURE_TARGET"):
            service.capture(target, stopped(), plan_digest="a" * 64)
    finally:
        service.close()


@pytest.mark.parametrize("kind", ["unexpected_file", "unexpected_empty_directory", "secret", "hardlink", "missing", "jar"])
def test_unrecognized_incomplete_aliased_or_changed_sources_reject(installed, tmp_path, kind):
    code = "VANILLA_PERSISTENCE_LAYOUT_UNSUPPORTED"
    if kind == "unexpected_file":
        (installed / "external-state.dat").write_bytes(b"not omitted")
    elif kind == "unexpected_empty_directory":
        (installed / "mods").mkdir()
    elif kind == "secret":
        (installed / "world/data/auth.json").parent.mkdir(exist_ok=True)
        (installed / "world/data/auth.json").write_bytes(b"not a secret")
        code = "SECRET_IN_SNAPSHOT"
    elif kind == "hardlink":
        os.link(installed / "server.jar", tmp_path / "other-write-route")
        code = "UNSAFE_PATH"
    elif kind == "missing":
        (installed / "ops.json").unlink()
        code = "VANILLA_PERSISTENCE_INCOMPLETE"
    else:
        (installed / "server.jar").write_bytes(b"changed")
        code = "VANILLA_PIN_MISMATCH"
    with pytest.raises(Fault, match=code):
        persistence.layout(persistence.safe(installed))


@pytest.mark.parametrize("kind", ["live", "no_job", "missing_handle", "unsignaled", "forced"])
def test_process_claim_without_complete_normal_termination_rejects(kind):
    process = stopped()
    if kind == "live":
        process.poll = lambda: None
    elif kind == "no_job":
        process.job = None
    elif kind == "missing_handle":
        process.job.member_status = lambda: {"held_processes": 1, "signaled_processes": 1}
    elif kind == "unsignaled":
        process.job.member_status = lambda: {"held_processes": 2, "signaled_processes": 1}
    else:
        process.job.accounting = lambda: {"total_processes": 2, "active_processes": 0, "terminated_processes": 1}
    with pytest.raises(Fault, match="VANILLA_STOP_UNPROVEN"):
        persistence.VanillaPersistence.terminal_processes(process)


@pytest.mark.skipif(os.name != "nt", reason="Windows file lease qualification")
@pytest.mark.parametrize("kind", ["state", "missing", "extra", "empty_directory", "receipt", "external_digest"])
def test_archive_bytes_receipt_and_inventory_are_rechecked(installed, tmp_path, kind):
    target = tmp_path / "stopped"
    result = capture(installed, target)
    expected = result["manifest_sha256"]
    if kind == "state":
        (target / "state/world/level.dat").write_bytes(b"changed")
    elif kind == "missing":
        (target / "state/ops.json").unlink()
    elif kind == "extra":
        (target / "state/credentials.json").write_bytes(b"extra")
    elif kind == "empty_directory":
        (target / "state/future").mkdir()
    elif kind == "receipt":
        with (target / "manifest.json").open("ab") as stream:
            stream.write(b" ")
    else:
        expected = "b" * 64
    with pytest.raises(Fault, match="VANILLA_CAPTURE_CHANGED"):
        persistence.verify_snapshot(target, expected)


@pytest.mark.skipif(os.name != "nt", reason="Windows file lease qualification")
def test_new_file_during_capture_leaves_uncommitted_output(installed, tmp_path, monkeypatch):
    original = persistence.FileLease.recheck
    def changed(self):
        if any(p.endswith("level.dat") for p in self.paths):
            (installed / "world/data").mkdir(exist_ok=True)
            (installed / "world/data/later.dat").write_bytes(b"later state")
        return original(self)
    monkeypatch.setattr(persistence.FileLease, "recheck", changed)
    target = tmp_path / "partial"
    with pytest.raises(IntegrityError, match="BOOTSTRAP_TREE_CHANGED"):
        capture(installed, target)
    assert not (target / "manifest.json").exists()


@pytest.mark.skipif(os.name != "nt", reason="Windows Job Object and file lease qualification")
def test_owned_process_must_finish_before_native_leased_capture(installed, tmp_path):
    script = tmp_path / "owned.py"
    script.write_text('import time\ntime.sleep(1.5)\n', encoding="utf-8")
    environment = {k: os.environ[k] for k in ("SystemRoot", "WINDIR") if k in os.environ}
    base = Path(sys._base_executable)
    proc = ManagedProcess([str(base), "-I", str(script)], tmp_path, environment, "", bootstrap_python=base)
    target = tmp_path / "owned-snapshot"
    try:
        with pytest.raises(Fault, match="VANILLA_STOP_UNPROVEN"):
            capture(installed, target, proc)
        assert not target.exists()
        deadline = time.monotonic() + 8
        while proc.poll() is None:
            assert time.monotonic() < deadline
            proc.job.observe_members()
            time.sleep(.01)
        result = capture(installed, target, proc)
        body = persistence.verify_snapshot(target, result["manifest_sha256"])
        # Windows may create an additional console host. Count the actual held
        # history rather than assuming the number of bootstrap descendants.
        assert body["owned_processes"]["job"]["total_processes"] == len(proc.job.members) >= 2
        assert body["owned_processes"]["held"]["signaled_processes"] == len(proc.job.members)
        assert not body["clean_save_proven"]
    finally:
        proc.close()


@pytest.mark.skipif(os.name != "nt", reason="Windows capture profile")
@pytest.mark.parametrize("case", ["valid", "pack", "policy", "arguments", "world", "rcon", "password", "command", "duplicate"])
def test_fixed_capture_profile_has_no_arbitrary_launch_or_admin_override(case):
    plan = {"target": "vanilla", "persistence_policy": persistence.POLICY}
    launch = SimpleNamespace(arguments=["-Xms1G", "-Xmx2G", "-jar", "server.jar", "nogui"])
    text = "level-name=world\nenable-rcon=false\nrcon.password=\nenable-command-block=false\n"
    if case == "pack":
        plan["target"] = "e9e"
    elif case == "policy":
        plan["persistence_policy"] = "unreviewed"
    elif case == "arguments":
        launch.arguments.append("--unreviewed")
    elif case == "world":
        text = text.replace("level-name=world", "level-name=../sibling")
    elif case == "rcon":
        text = text.replace("enable-rcon=false", "enable-rcon=true")
    elif case == "password":
        text = text.replace("rcon.password=", "rcon.password=synthetic-secret")
    elif case == "command":
        text = text.replace("enable-command-block=false", "enable-command-block=true")
    elif case == "duplicate":
        text += "level-name=world\n"
    if case == "valid":
        validate_persistence_profile(plan, launch, text)
    else:
        with pytest.raises(Fault, match="VANILLA_PERSISTENCE_PROFILE_UNSUPPORTED"):
            validate_persistence_profile(plan, launch, text)


@pytest.mark.skipif(os.name != "nt", reason="Windows file lease qualification")
def test_failed_manifest_publication_retains_partial_output_without_replay(installed, tmp_path, monkeypatch):
    target = tmp_path / "interrupted"
    def fail(*_):
        raise OSError("synthetic disk-full at manifest publication")
    monkeypatch.setattr(persistence, "write_new", fail)
    with pytest.raises(OSError, match="synthetic disk-full"):
        capture(installed, target)
    assert target.is_dir() and (target / "state/world/level.dat").exists()
    assert not (target / "manifest.json").exists()
    with pytest.raises(Fault, match="VANILLA_CAPTURE_TARGET"):
        capture(installed, target)
