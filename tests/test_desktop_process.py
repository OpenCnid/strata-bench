"""Real disposable Windows desktop/process lifetime tests, not Minecraft qualification."""

import json
from contextlib import closing
import ctypes
from ctypes import wintypes
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

from mcbench.desktop_process import DesktopApi, DesktopProcess, launch_values
from mcbench.process_guard import HeldProcess
from mcbench.processes import WindowsJob
from mcbench.storage import Fault

CHILD = Path(__file__).parent / "fixtures" / "desktop_child.py"
WINDOWS = pytest.mark.skipif(os.name != "nt", reason="Windows desktop/process APIs required")


def environment():
    return {**{key: os.environ[key] for key in ("SystemRoot", "WINDIR") if key in os.environ}, "ALLOWED": "é exact"}


def launch(tmp_path, mode="hold", **kwargs):
    target = tmp_path / "result.json"
    proc = DesktopProcess([sys.executable, "-I", str(CHILD), str(target), mode,
                           "space argument", 'quote"', "$(not-a-command)", "😀"],
                          tmp_path, environment(), **kwargs)
    return proc, target


def read_result(path, process, timeout=5):
    deadline = time.monotonic() + timeout
    while not path.exists() and time.monotonic() < deadline:
        assert process.poll() is None, "Fixture exited before writing evidence"
        time.sleep(.01)
    assert path.is_file(), "Fixture evidence timed out"
    return json.loads(path.read_text(encoding="utf-8"))


def in_job(process, pid):
    with closing(HeldProcess(pid)) as held:
        query = process.api.kernel.IsProcessInJob
        query.argtypes = [wintypes.HANDLE, wintypes.HANDLE, ctypes.POINTER(wintypes.BOOL)]
        query.restype = wintypes.BOOL
        result = wintypes.BOOL()
        assert query(held.handle, process.job.handle, ctypes.byref(result))
        return bool(result.value)


def test_launch_validation_and_no_implicit_environment(tmp_path):
    command, block = launch_values([sys.executable, "a b", 'literal"', "é"], tmp_path, {"z": "two", "A": "one"})
    assert command == subprocess.list2cmdline([sys.executable, "a b", 'literal"', "é"])
    assert block == "A=one\0z=two\0\0"
    for argv, cwd, env, error in [
        ([], tmp_path, {}, "INVALID_ARGUMENT"),
        (["relative.exe"], tmp_path, {}, "UNSAFE_PATH"),
        ([sys.executable], Path("relative"), {}, "UNSAFE_PATH"),
        ([sys.executable, "\0"], tmp_path, {}, "INVALID_ARGUMENT"),
        ([sys.executable], tmp_path, {"a": "1", "A": "2"}, "INVALID_ENVIRONMENT"),
        ([sys.executable], tmp_path, {"A=B": "1"}, "INVALID_ENVIRONMENT"),
        ([sys.executable], tmp_path, {"A": "\0"}, "INVALID_ENVIRONMENT"),
        ([sys.executable, "a" * 32767], tmp_path, {}, "PROCESS_ARGUMENT_QUOTA"),
        ([sys.executable], tmp_path, {"A": "x" * 65536}, "PROCESS_ENVIRONMENT_QUOTA"),
    ]:
        with pytest.raises(Fault, match=error):
            launch_values(argv, cwd, env)


@WINDOWS
def test_real_hidden_window_uses_fresh_desktop_with_exact_arguments_and_environment(tmp_path, monkeypatch):
    before = DesktopApi().input_name()
    monkeypatch.setenv("STRATA_PRIVATE_CANARY", "do-not-inherit")
    proc, target = launch(tmp_path)
    with proc:
        value = read_result(target, proc)
        # The Windows venv redirector may create the actual Python interpreter
        # as a descendant. Both must be contained before fixture code executes.
        assert in_job(proc, proc.pid) and in_job(proc, value["pid"])
        assert value == {"pid": value["pid"], "desktop": proc.name, "created_hidden_window": True,
                         "arguments": ["space argument", 'quote"', "$(not-a-command)", "😀"],
                         "allowed": "é exact", "private_canary": None, "child_pid": None}
        assert value["desktop"] != before
        assert DesktopApi().input_name() == before
        assert proc.poll() is None
    assert DesktopApi().input_name() == before
    proc.close()  # idempotent
    with pytest.raises(Fault, match="PROCESS_CLOSED"):
        proc.poll()


@WINDOWS
def test_natural_exit_preserves_real_code(tmp_path):
    proc, target = launch(tmp_path, "exit")
    with proc:
        assert proc.wait(5) == 23
        assert json.loads(target.read_text())["created_hidden_window"] is True
        assert proc.reason is None


@WINDOWS
def test_whole_tree_is_placed_on_desktop_and_stopped(tmp_path):
    proc, target = launch(tmp_path, "descendant")
    with proc:
        parent = read_result(target, proc)
        child = read_result(target.with_suffix(".child.json"), proc)
        assert child["desktop"] == parent["desktop"] == proc.name
        assert in_job(proc, parent["pid"]) and in_job(proc, child["pid"])
        with closing(HeldProcess(parent["child_pid"])) as held:
            proc.stop()
            assert proc.wait(1) == 125
            assert held.exited(2000)
        assert not target.with_suffix(".late").exists()


@WINDOWS
def test_wall_deadline_stops_without_polling_and_retains_reason(tmp_path):
    proc, target = launch(tmp_path, max_wall_ms=1500)
    with proc:
        read_result(target, proc)
        assert proc.wait(5) == 125
        assert proc.reason == "PROCESS_WALL_EXHAUSTED"


@WINDOWS
def test_input_desktop_change_or_query_failure_fences_owned_child(tmp_path, monkeypatch):
    proc, target = launch(tmp_path)
    with proc:
        read_result(target, proc)
        monkeypatch.setattr(proc.api, "input_name", lambda: proc.name)
        assert proc.wait(3) == 125
        assert proc.reason == "DESKTOP_BECAME_INPUT"
    # No desktop is actually switched; inject a failed observation separately.
    other = tmp_path / "other"
    other.mkdir()
    proc, target = launch(other)
    with proc:
        read_result(target, proc)
        def denied():
            raise Fault("DESKTOP_INPUT_UNAVAILABLE")
        monkeypatch.setattr(proc.api, "input_name", denied)
        assert proc.wait(3) == 125
        assert proc.reason == "DESKTOP_INPUT_UNAVAILABLE"


@WINDOWS
def test_job_assignment_failure_never_runs_child(tmp_path, monkeypatch):
    # Record the kernel handle while it is suspended. No child marker can exist.
    seen = []
    def fail(self, handle):
        pid = self.kernel.GetProcessId
        pid.argtypes, pid.restype = [wintypes.HANDLE], wintypes.DWORD
        seen.append(HeldProcess(pid(handle)))
        raise Fault("INJECTED_JOB_ASSIGNMENT")
    monkeypatch.setattr(WindowsJob, "attach_handle", fail)
    with pytest.raises(Fault, match="INJECTED_JOB_ASSIGNMENT"):
        launch(tmp_path)
    assert seen and not (tmp_path / "result.json").exists()
    with closing(seen[0]) as held:
        assert held.exited(2000)


@WINDOWS
def test_constructor_failure_and_invalid_deadline_do_not_dispatch(tmp_path):
    for limit in (True, 0, -1, 600001):
        with pytest.raises(Fault, match="INVALID_ARGUMENT"):
            launch(tmp_path, max_wall_ms=limit)
    bad = tmp_path / "invalid.exe"
    bad.write_bytes(b"not executable")
    with pytest.raises(Fault, match="PROCESS_LAUNCH_FAILED"):
        DesktopProcess([str(bad)], tmp_path, environment())
    assert not (tmp_path / "result.json").exists()


@WINDOWS
def test_pre_resume_context_failure_cannot_execute_child(tmp_path, monkeypatch):
    checks = 0
    original = DesktopProcess._check_noninput
    def changed(self):
        nonlocal checks
        checks += 1
        if checks == 2:
            raise Fault("INJECTED_PRE_RESUME_CHANGE")
        original(self)
    monkeypatch.setattr(DesktopProcess, "_check_noninput", changed)
    with pytest.raises(Fault, match="INJECTED_PRE_RESUME_CHANGE"):
        launch(tmp_path)
    assert checks == 2 and not (tmp_path / "result.json").exists()


@WINDOWS
def test_wait_timeout_does_not_relaunch_or_cancel_and_desktop_closes(tmp_path):
    proc, target = launch(tmp_path)
    with proc:
        read_result(target, proc)
        with pytest.raises(Fault, match="PROCESS_WAIT_TIMEOUT"):
            proc.wait(.01)
        assert proc.poll() is None
        assert proc.reason is None
    user = proc.api.user
    user.OpenDesktopW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    user.OpenDesktopW.restype = wintypes.HANDLE
    handle = user.OpenDesktopW(proc.name, 0, False, 1)
    if handle:
        user.CloseDesktop(handle)
        pytest.fail("Owned desktop survived complete process/handle cleanup")
    assert ctypes.get_last_error() == 2


@WINDOWS
def test_normal_parent_exit_does_not_leave_a_descendant_after_close(tmp_path):
    proc, target = launch(tmp_path, "orphan")
    child_path = target.with_suffix(".child.json")
    held = None
    try:
        assert proc.wait(5) == 0
        deadline = time.monotonic() + 5
        while not child_path.exists() and time.monotonic() < deadline:
            time.sleep(.01)
        child = json.loads(child_path.read_text(encoding="utf-8"))
        assert child["desktop"] == proc.name and in_job(proc, child["pid"])
        held = HeldProcess(child["pid"])
        proc.close()
        assert held.exited(2000)
    finally:
        proc.close()
        if held:
            held.close()


@WINDOWS
def test_owner_crash_closes_noninherited_job_and_kills_owned_tree(tmp_path):
    # Use the base executable, so the Popen HANDLE is the owner itself, rather
    # than a venv redirector whose child could outlive a redirector-only kill.
    script = tmp_path / "owner.py"
    sources = Path(__file__).resolve().parents[1] / "src"
    site = Path(sys.prefix) / "Lib" / "site-packages"
    script.write_text(
        "import sys,json,os,time\n"
        f"sys.path[:0] = {[str(sources), str(site)]!r}\n"
        "from mcbench.desktop_process import DesktopProcess\n"
        "from pathlib import Path\n"
        "plan=json.loads(sys.stdin.readline())\n"
        "proc=DesktopProcess(plan['argv'],Path(plan['cwd']),plan['environment'],max_wall_ms=20000)\n"
        "print(json.dumps({'owner':os.getpid(),'root':proc.pid,'desktop':proc.name}),flush=True)\n"
        "time.sleep(30)\n", encoding="utf-8")
    target = tmp_path / "crash-result.json"
    before = DesktopApi().input_name()
    owner = subprocess.Popen([sys._base_executable, "-I", str(script)], stdin=subprocess.PIPE,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=subprocess.CREATE_NO_WINDOW,
        env=environment(), close_fds=True)
    held = None
    try:
        plan = {"argv": [sys.executable, "-I", str(CHILD), str(target), "descendant"],
                "cwd": str(tmp_path), "environment": environment()}
        owner.stdin.write(json.dumps(plan).encode() + b"\n")
        owner.stdin.close()
        # Bound the readiness wait by the child's evidence file; never block on
        # an unbounded pipe read from an unconfirmed process.
        deadline = time.monotonic() + 5
        child_path = target.with_suffix(".child.json")
        while not child_path.exists() and time.monotonic() < deadline:
            assert owner.poll() is None, owner.stderr.read().decode(errors="replace")
            time.sleep(.01)
        assert child_path.is_file()
        child = json.loads(child_path.read_text(encoding="utf-8"))
        held = HeldProcess(child["pid"])
        owner.kill()
        owner.wait(5)
        assert held.exited(2000)
        ready = json.loads(owner.stdout.readline())
        assert ready["owner"] == owner.pid and ready["desktop"] == child["desktop"]
        assert DesktopApi().input_name() == before
    finally:
        if owner.poll() is None:
            owner.kill()
            owner.wait(5)
        if held:
            held.close()
        for stream in (owner.stdin, owner.stdout, owner.stderr):
            stream.close()
