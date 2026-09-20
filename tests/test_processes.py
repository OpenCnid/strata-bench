import json
import os
import sys
import time
from pathlib import Path

import pytest

from mcbench.processes import ManagedProcess, WindowsJob
from mcbench.storage import Fault


def test_managed_real_child_exact_arguments_stdin_environment(tmp_path):
    script = tmp_path / "child.py"
    script.write_text("import sys,os,json\nprint(json.dumps([sys.argv[1:],sys.stdin.buffer.read().decode('utf-8'),"
                      "os.environ.get('ALLOWED'),os.environ.get('STRATA_PRIVATE_CANARY')]))",
                      encoding="utf-8")
    original = os.environ.get("STRATA_PRIVATE_CANARY")
    os.environ["STRATA_PRIVATE_CANARY"] = "must-not-inherit"
    proc = None
    try:
        proc = ManagedProcess([sys.executable, "-I", str(script), "a b", 'literal\" quote',
                               "$(not-a-command)"], tmp_path, {"ALLOWED": "yes"}, "ordinary goal\né")
        line = proc.process.stdout.readline()
        assert json.loads(line) == [["a b", 'literal\" quote', "$(not-a-command)"],
                                    "ordinary goal\né", "yes", None]
        assert proc.process.wait(timeout=10) == 0
    finally:
        if proc:
            proc.stop()
            proc.close()
        if original is None:
            os.environ.pop("STRATA_PRIVATE_CANARY", None)
        else:
            os.environ["STRATA_PRIVATE_CANARY"] = original


def test_stop_kills_grandchild_and_no_late_mutation(tmp_path):
    child = tmp_path / "child.py"
    marker = tmp_path / "late-effect"
    grandchild = tmp_path / "grandchild.py"
    grandchild.write_text("import time,pathlib,sys\nprint('ready',flush=True)\ntime.sleep(0.8)\n"
                          "pathlib.Path(sys.argv[1]).write_text('late mutation')\ntime.sleep(30)",
                          encoding="utf-8")
    child.write_text("import subprocess,sys,time\nsubprocess.Popen([sys.executable,'-I',"
                     "sys.argv[1],sys.argv[2]])\ntime.sleep(30)", encoding="utf-8")
    proc = ManagedProcess([sys.executable, "-I", str(child), str(grandchild), str(marker)],
                          tmp_path, {}, "")
    try:
        assert proc.process.stdout.readline().strip() == b"ready"
        before = time.monotonic()
        proc.stop()
        assert time.monotonic() - before < 2.1
        time.sleep(1)
        assert not marker.exists()
        assert proc.process.stdout.read() == b""
    finally:
        proc.close()


def test_normal_exit_close_reaps_lingering_grandchild(tmp_path):
    marker = tmp_path / "late"
    code = "import time,pathlib; time.sleep(0.8); pathlib.Path(" + repr(str(marker)) + ").touch()"
    parent = "import subprocess,sys; subprocess.Popen([sys.executable,'-I','-c',sys.argv[1]])"
    proc = ManagedProcess([sys.executable, "-I", "-c", parent, code], tmp_path, {}, "")
    assert proc.process.wait(timeout=10) == 0
    proc.close()
    time.sleep(1)
    assert not marker.exists()


def test_invalid_paths_and_oversize_prompt_fail_before_start(tmp_path):
    with pytest.raises(Fault, match="UNSAFE_PATH"):
        ManagedProcess(["relative.exe"], tmp_path, {}, "")
    with pytest.raises(Fault, match="RUNTIME_INPUT_QUOTA"):
        ManagedProcess([sys.executable], tmp_path, {}, "x" * (2 * 1024 * 1024))
    with pytest.raises(Fault, match="UNSAFE_PATH"):
        ManagedProcess([sys.executable], Path("relative"), {}, "")


def test_interactive_console_can_stop_cleanly_without_stdin_eof(tmp_path):
    script = tmp_path / "console.py"
    script.write_text("import sys\nprint('ready',flush=True)\n"
                      "for line in sys.stdin:\n"
                      " print(line.strip(),flush=True)\n"
                      " if line.strip() == 'stop': break\n", encoding="utf-8")
    proc = ManagedProcess([sys.executable, "-I", str(script)], tmp_path, {}, "", interactive=True)
    try:
        assert proc.process.stdout.readline().strip() == b"ready"
        proc.send_input("status\n")
        assert proc.process.stdout.readline().strip() == b"status"
        with pytest.raises(Fault, match="PROCESS_INPUT_QUOTA"):
            proc.send_input("x" * 4097)
        proc.send_input("stop\n")
        assert proc.process.stdout.readline().strip() == b"stop"
        assert proc.process.wait(timeout=5) == 0
        with pytest.raises(Fault, match="PROCESS_NOT_RUNNING"):
            proc.send_input("stop\n")
    finally:
        proc.stop()
        proc.close()


def test_native_noninteractive_process_cannot_receive_later_console_input(tmp_path):
    proc = ManagedProcess([sys.executable, "-I", "-c", "import time; time.sleep(30)"],
                          tmp_path, {}, "")
    try:
        with pytest.raises(Fault, match="PROCESS_INPUT_DISABLED"):
            proc.send_input("unexpected extra prompt\n")
    finally:
        proc.stop()
        proc.close()


@pytest.mark.skipif(os.name != "nt", reason="Windows Job Object query")
def test_job_accounting_observes_whole_owned_tree_stop(tmp_path):
    proc = ManagedProcess([sys.executable, "-I", "-c",
        "import subprocess,sys,time; subprocess.Popen([sys.executable,'-I','-c',"
        "'import time; time.sleep(30)']); print('ready',flush=True); time.sleep(30)"],
        tmp_path, {}, "")
    try:
        assert proc.process.stdout.readline().strip() == b"ready"
        live = proc.job.accounting()
        assert live["total_processes"] >= 3 and live["active_processes"] >= 3
        proc.job.observe_members()
        assert proc.job.member_status()["held_processes"] == live["total_processes"]
        proc.stop()
        deadline = time.monotonic() + 2
        while (proc.job.accounting()["active_processes"]
               or proc.job.member_status()["signaled_processes"] != live["total_processes"]) and time.monotonic() < deadline:
            time.sleep(0.01)
        assert proc.job.accounting()["active_processes"] == 0
        assert proc.job.member_status()["signaled_processes"] == live["total_processes"]
    finally:
        proc.close()
    with pytest.raises(Fault, match="PROCESS_FENCING_UNAVAILABLE"):
        proc.job.accounting()


@pytest.fixture
def synthetic_member_job():
    """Exercise handle/ownership failure paths without targeting outside processes."""
    import ctypes
    from ctypes import wintypes
    from types import SimpleNamespace

    state = SimpleNamespace(pids=[123], member=True, signaled=False, query_ok=True,
                            opened=[], closed=[])
    job = WindowsJob.__new__(WindowsJob)
    job.handle, job.members = 99, {}
    job.MAX_TRACKED_PROCESSES = 2

    def query(handle, kind, pointer, size, length):
        assert (handle, kind, length) == (99, 3, None)
        class Members(ctypes.Structure):
            _fields_ = [("assigned", wintypes.DWORD), ("count", wintypes.DWORD),
                        ("pids", ctypes.c_size_t * 2)]
        assert size == ctypes.sizeof(Members)
        value = ctypes.cast(pointer, ctypes.POINTER(Members)).contents
        value.assigned = len(state.pids)
        value.count = min(value.assigned, 2)
        for index, pid in enumerate(state.pids[:2]):
            value.pids[index] = pid
        return state.query_ok

    def open_process(rights, inherit, pid):
        state.opened.append((rights, inherit, pid))
        return pid + 1000

    def is_member(handle, owner, output):
        assert owner == 99
        ctypes.cast(output, ctypes.POINTER(wintypes.BOOL)).contents.value = state.member
        return True

    job.kernel = SimpleNamespace(QueryInformationJobObject=query, OpenProcess=open_process,
        IsProcessInJob=is_member, CloseHandle=state.closed.append,
        WaitForSingleObject=lambda handle, timeout: 0 if state.signaled else 258)
    return job, state


def test_member_observation_holds_read_only_identity_and_closes_handles(synthetic_member_job):
    job, state = synthetic_member_job
    job.observe_members()
    job.observe_members()
    assert state.opened == [(0x1000 | 0x100000, False, 123)]  # No terminate/attach rights.
    assert job.member_status() == {"held_processes": 1, "signaled_processes": 0}
    state.signaled = True
    assert job.member_status() == {"held_processes": 1, "signaled_processes": 1}
    job.close()
    assert state.closed == [99, 1123] and not job.members
    job.close()
    assert state.closed == [99, 1123]


@pytest.mark.parametrize("failure", ["foreign", "query", "truncated", "quota"])
def test_member_inventory_failures_cannot_claim_owned_processes(synthetic_member_job, failure):
    job, state = synthetic_member_job
    if failure == "foreign":
        state.member = False
    elif failure == "query":
        state.query_ok = False
    elif failure == "truncated":
        state.pids = [123, 124, 125]
    else:
        job.members = {121: 1121, 122: 1122}
    with pytest.raises(Fault, match="PROCESS_MEMBER_(INVENTORY_UNAVAILABLE|QUOTA)"):
        job.observe_members()
    assert state.opened == ([(0x1000 | 0x100000, False, 123)] if failure == "foreign" else [])
    assert state.closed == ([1123] if failure == "foreign" else [])
    assert 123 not in job.members
