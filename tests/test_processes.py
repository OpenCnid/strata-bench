import json
import os
import sys
import time
from pathlib import Path

import pytest

from mcbench.processes import ManagedProcess, ProcessInventoryFault, WindowsJob
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

    state = SimpleNamespace(pids=[123], member=True, member_query_ok=True, open_ok=True,
                            signaled=False, query_ok=True, api_error=5, queries=0,
                            membership_queries=0, opened=[], closed=[], assigned=None, listed=None)
    job = WindowsJob.__new__(WindowsJob)
    job.handle, job.members = 99, {}
    job.MAX_TRACKED_PROCESSES = 2

    def query(handle, kind, pointer, size, length):
        state.queries += 1
        if os.name == "nt":
            ctypes.set_last_error(state.api_error)
        assert (handle, kind, length) == (99, 3, None)
        class Members(ctypes.Structure):
            _fields_ = [("assigned", wintypes.DWORD), ("count", wintypes.DWORD),
                        ("pids", ctypes.c_size_t * 2)]
        assert size == ctypes.sizeof(Members)
        value = ctypes.cast(pointer, ctypes.POINTER(Members)).contents
        value.assigned = len(state.pids) if state.assigned is None else state.assigned
        value.count = min(value.assigned, 2) if state.listed is None else state.listed
        for index, pid in enumerate(state.pids[:2]):
            value.pids[index] = pid
        return state.query_ok

    def open_process(rights, inherit, pid):
        state.opened.append((rights, inherit, pid))
        if os.name == "nt":
            ctypes.set_last_error(state.api_error)
        return pid + 1000 if state.open_ok else None

    def is_member(handle, owner, output):
        assert owner == 99
        state.membership_queries += 1
        if os.name == "nt":
            ctypes.set_last_error(state.api_error)
        ctypes.cast(output, ctypes.POINTER(wintypes.BOOL)).contents.value = state.member
        return state.member_query_ok

    def close(handle):
        state.closed.append(handle)
        if os.name == "nt":
            ctypes.set_last_error(999)  # Must not overwrite the recorded failing API error.

    job.kernel = SimpleNamespace(QueryInformationJobObject=query, OpenProcess=open_process,
        IsProcessInJob=is_member, CloseHandle=close,
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


@pytest.mark.parametrize("stage", sorted(ProcessInventoryFault.STAGES))
def test_inventory_diagnostic_classifies_without_retry_or_partial_ownership(
    synthetic_member_job, stage
):
    job, state = synthetic_member_job
    if stage == "query":
        state.query_ok = False
    elif stage == "incomplete_list":
        state.pids = [123, 124, 125]
    elif stage == "invalid_pid":
        state.pids = [0]
    elif stage == "retained_quota":
        job.members = {121: 1121, 122: 1122}
    elif stage == "open_process":
        state.open_ok = False
    elif stage == "membership_query":
        state.member_query_ok = False
    elif stage == "foreign_member":
        state.member = False
    before = dict(job.members)
    with pytest.raises(ProcessInventoryFault) as caught:
        job.observe_members()
    error = caught.value
    expected_api_error = 5 if os.name == "nt" and stage in {
        "query", "open_process", "membership_query"} else None
    assert error.observation() == {
        "schema": "strata/ProcessInventoryObservation/1", "stage": stage,
        "assigned_processes": None if stage == "query" else len(state.pids),
        "listed_processes": None if stage == "query" else min(len(state.pids), 2),
        "retained_processes": len(before), "win32_error": expected_api_error,
    }
    assert error.code == ("PROCESS_MEMBER_QUOTA" if stage == "retained_quota"
                          else "PROCESS_MEMBER_INVENTORY_UNAVAILABLE")
    assert str(error) == error.code  # Diagnostics are operator-only structured data.
    assert state.queries == 1 and job.members == before
    assert len(state.opened) == int(stage in {"open_process", "membership_query", "foreign_member"})
    assert len(state.closed) == state.membership_queries == int(
        stage in {"membership_query", "foreign_member"})
    modified = error.observation()
    modified["stage"] = "private value"
    assert error.observation()["stage"] == stage


@pytest.mark.parametrize("arguments", [
    {"stage": "private path"}, {"assigned": "secret"}, {"listed": -1},
    {"retained": 257}, {"win32_error": 2**32}, {"retained": True},
])
def test_inventory_diagnostics_reject_unbounded_or_unstructured_fields(arguments):
    with pytest.raises(Fault, match="INVALID_ARGUMENT"):
        ProcessInventoryFault(**({"stage": "query", "retained": 0} | arguments))
