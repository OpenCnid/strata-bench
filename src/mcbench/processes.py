"""Bounded process-tree lifetime, separate from filesystem/network isolation.

On Windows, children inherit a no-breakaway kill-on-close Job Object. A trusted
bootstrap waits for assignment before spawning the native host. This eliminates
the usual Popen/AssignProcessToJobObject race where an early child escapes.
"""

import json
import os
import signal
import subprocess
import sys
import threading
from pathlib import Path

from .storage import Fault, reject_links, require


class ProcessInventoryFault(Fault):
    """Bounded operator diagnostics; no process names, paths, arguments or PIDs."""

    STAGES = {"query", "incomplete_list", "invalid_pid", "retained_quota",
              "open_process", "membership_query", "foreign_member"}

    def __init__(self, stage, *, assigned=None, listed=None, retained, win32_error=None):
        require(stage in self.STAGES, "INVALID_ARGUMENT")
        require(all(value is None or type(value) is int and 0 <= value <= 0xFFFFFFFF
                    for value in (assigned, listed, win32_error)), "INVALID_ARGUMENT")
        require(type(retained) is int and 0 <= retained <= 256, "INVALID_ARGUMENT")
        self._observation = (stage, assigned, listed, retained, win32_error)
        super().__init__("PROCESS_MEMBER_QUOTA" if stage == "retained_quota"
                         else "PROCESS_MEMBER_INVENTORY_UNAVAILABLE")

    def observation(self):
        stage, assigned, listed, retained, win32_error = self._observation
        return {"schema": "strata/ProcessInventoryObservation/1", "stage": stage,
                "assigned_processes": assigned, "listed_processes": listed,
                "retained_processes": retained, "win32_error": win32_error}


class WindowsJob:
    MAX_TRACKED_PROCESSES = 256

    def __init__(self):
        import ctypes
        from ctypes import wintypes

        class Basic(ctypes.Structure):
            _fields_ = [("process_time", ctypes.c_int64), ("job_time", ctypes.c_int64),
                        ("flags", wintypes.DWORD), ("min_working", ctypes.c_size_t),
                        ("max_working", ctypes.c_size_t), ("active_processes", wintypes.DWORD),
                        ("affinity", ctypes.c_size_t), ("priority", wintypes.DWORD),
                        ("scheduling", wintypes.DWORD)]

        class Io(ctypes.Structure):
            _fields_ = [(name, ctypes.c_uint64) for name in (
                "read_ops", "write_ops", "other_ops", "read_bytes", "write_bytes", "other_bytes")]

        class Extended(ctypes.Structure):
            _fields_ = [("basic", Basic), ("io", Io), ("process_memory", ctypes.c_size_t),
                        ("job_memory", ctypes.c_size_t), ("peak_process", ctypes.c_size_t),
                        ("peak_job", ctypes.c_size_t)]

        self.kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        signatures = {
            "CreateJobObjectW": ([ctypes.c_void_p, wintypes.LPCWSTR], wintypes.HANDLE),
            "SetInformationJobObject": ([wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p,
                                         wintypes.DWORD], wintypes.BOOL),
            "AssignProcessToJobObject": ([wintypes.HANDLE, wintypes.HANDLE], wintypes.BOOL),
            "TerminateJobObject": ([wintypes.HANDLE, wintypes.UINT], wintypes.BOOL),
            "CloseHandle": ([wintypes.HANDLE], wintypes.BOOL),
            "OpenProcess": ([wintypes.DWORD, wintypes.BOOL, wintypes.DWORD], wintypes.HANDLE),
            "IsProcessInJob": ([wintypes.HANDLE, wintypes.HANDLE, ctypes.POINTER(wintypes.BOOL)], wintypes.BOOL),
            "WaitForSingleObject": ([wintypes.HANDLE, wintypes.DWORD], wintypes.DWORD),
        }
        for name, (arguments, result) in signatures.items():
            function = getattr(self.kernel, name)
            function.argtypes, function.restype = arguments, result
        self.members = {}  # Optional observation handles; never used to terminate by PID.
        self.handle = self.kernel.CreateJobObjectW(None, None)
        require(bool(self.handle), "PROCESS_FENCING_UNAVAILABLE")
        limits = Extended()
        limits.basic.flags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE; no BREAKAWAY flags
        if not self.kernel.SetInformationJobObject(self.handle, 9, ctypes.byref(limits),
                                                   ctypes.sizeof(limits)):
            self.close()
            raise Fault("PROCESS_FENCING_UNAVAILABLE")

    def attach(self, process):
        self.attach_handle(int(process._handle))

    def attach_handle(self, process_handle):
        """Attach an already opened, identity-validated operator process handle."""
        require(bool(self.kernel.AssignProcessToJobObject(self.handle, process_handle)),
                "PROCESS_FENCING_UNAVAILABLE")

    def terminate(self):
        if self.handle:
            require(bool(self.kernel.TerminateJobObject(self.handle, 125)), "PROCESS_STOP_FAILED")

    def accounting(self):
        """Read the held job's whole-tree process counts without PID rediscovery."""
        import ctypes
        from ctypes import wintypes

        class Accounting(ctypes.Structure):
            _fields_ = [(name, ctypes.c_int64) for name in (
                "user_time", "kernel_time", "period_user_time", "period_kernel_time")] + [
                (name, wintypes.DWORD) for name in (
                    "page_faults", "total_processes", "active_processes", "terminated_processes")]

        require(bool(self.handle), "PROCESS_FENCING_UNAVAILABLE")
        query = self.kernel.QueryInformationJobObject
        query.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p,
                          wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]
        query.restype = wintypes.BOOL
        value, returned = Accounting(), wintypes.DWORD()
        require(bool(query(self.handle, 1, ctypes.byref(value), ctypes.sizeof(value),
                           ctypes.byref(returned))) and returned.value == ctypes.sizeof(value),
                "PROCESS_STATE_UNAVAILABLE")
        return {key: getattr(value, key) for key in (
            "total_processes", "active_processes", "terminated_processes")}

    def observe_members(self, *, reconcile_history=False):
        """Retain handles only to members of this held job, within a fixed quota.

        A missed short-lived member is not guessed dead: final total-process
        accounting must equal the retained count. Holding handles prevents PID
        reuse from aliasing an earlier member. The optional private-reference
        policy can reconcile an incomplete list only against independently
        complete retained history; it never opens an unlisted process or retries.
        """
        import ctypes
        from ctypes import wintypes

        class Members(ctypes.Structure):
            _fields_ = [("assigned", wintypes.DWORD), ("count", wintypes.DWORD),
                        ("pids", ctypes.c_size_t * self.MAX_TRACKED_PROCESSES)]

        require(bool(self.handle), "PROCESS_FENCING_UNAVAILABLE")
        query = self.kernel.QueryInformationJobObject
        query.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p,
                          wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]
        query.restype = wintypes.BOOL
        value = Members()

        def failed(stage, api_error=False):
            # Read the calling thread's last-error slot before another Win32 call.
            # A successful API/failed predicate must not attach a stale API error.
            last_error = ctypes.get_last_error() if api_error and os.name == "nt" else None
            raise ProcessInventoryFault(
                stage, assigned=None if stage == "query" else value.assigned,
                listed=None if stage == "query" else value.count,
                retained=len(self.members), win32_error=last_error)

        if not query(self.handle, 3, ctypes.byref(value), ctypes.sizeof(value), None):
            failed("query", api_error=True)
        if not 0 <= value.count <= value.assigned <= self.MAX_TRACKED_PROCESSES:
            failed("incomplete_list")
        pids = list(value.pids[:value.count])
        if len(set(pids)) != len(pids) or any(not 0 < pid <= 0xFFFFFFFF for pid in pids):
            failed("invalid_pid")
        if value.count != value.assigned:
            if reconcile_history and set(pids) <= self.members.keys():
                # TotalProcesses includes every association during this Job's
                # lifetime, including exited/failed-limit processes. Equality
                # with our distinct, already membership-validated held handles
                # proves no missing history at this independent observation.
                # A fresh list, a PID guess or active-count equality cannot.
                accounting = self.accounting()
                held = self.member_status()  # Invalid handles still fail closed.
                if (accounting["total_processes"] == len(self.members)
                        <= self.MAX_TRACKED_PROCESSES
                        and value.assigned <= len(self.members)
                        and 0 <= accounting["active_processes"] <= len(self.members)
                        and accounting["terminated_processes"] == 0):
                    return {"schema": "strata/ProcessInventoryReconciliation/1",
                        "policy": "complete-retained-job-history/1",
                        "assigned_processes": value.assigned, "listed_processes": value.count,
                        "retained_processes": len(self.members), "job": accounting, "held": held}
            failed("incomplete_list")
        for pid in pids:
            if pid in self.members:
                continue
            if len(self.members) >= self.MAX_TRACKED_PROCESSES:
                failed("retained_quota")
            handle = self.kernel.OpenProcess(0x1000 | 0x100000, False, pid)
            if not handle:
                failed("open_process", api_error=True)
            try:
                member = wintypes.BOOL()
                if not self.kernel.IsProcessInJob(handle, self.handle, ctypes.byref(member)):
                    failed("membership_query", api_error=True)
                if not member.value:
                    failed("foreign_member")
                self.members[pid] = handle
            except BaseException:
                self.kernel.CloseHandle(handle)
                raise

    def member_status(self):
        require(bool(self.handle), "PROCESS_FENCING_UNAVAILABLE")
        signaled = 0
        for handle in self.members.values():
            result = self.kernel.WaitForSingleObject(handle, 0)
            require(result in (0, 258), "PROCESS_STATE_UNAVAILABLE")
            signaled += result == 0
        return {"held_processes": len(self.members), "signaled_processes": signaled}

    def member_identity(self, pid):
        """Describe a retained job-member handle, never trust a reused PID alone."""
        import ctypes
        from ctypes import wintypes
        require(pid in self.members, "PROCESS_MEMBER_UNOBSERVED")
        handle = self.members[pid]
        query = self.kernel.QueryFullProcessImageNameW
        query.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
        query.restype = wintypes.BOOL
        size = wintypes.DWORD(32768)
        name = ctypes.create_unicode_buffer(size.value)
        require(bool(query(handle, 0, name, ctypes.byref(size))), "PROCESS_IDENTITY_UNAVAILABLE")
        times = self.kernel.GetProcessTimes
        times.argtypes = [wintypes.HANDLE, *([ctypes.POINTER(wintypes.FILETIME)] * 4)]
        times.restype = wintypes.BOOL
        created, exited, kernel, user = (wintypes.FILETIME() for _ in range(4))
        require(bool(times(handle, ctypes.byref(created), ctypes.byref(exited),
                           ctypes.byref(kernel), ctypes.byref(user))), "PROCESS_IDENTITY_UNAVAILABLE")
        ticks = created.dwHighDateTime << 32 | created.dwLowDateTime
        return {"pid": pid, "executable": str(Path(name.value).resolve()),
                "process_started_unix_ms": ticks // 10000 - 11644473600000}

    def close(self):
        if self.handle:
            self.kernel.CloseHandle(self.handle)
            self.handle = None
        for handle in self.members.values():
            self.kernel.CloseHandle(handle)
        self.members.clear()


class ManagedProcess:
    """Start only operator-constructed arrays after durable dispatch authorization.

    This class does not grant that authorization. POSIX process groups support
    engineering tests but are not an adversarial sandbox/cgroup certification.
    """

    def __init__(self, argv: list[str], cwd: Path, environment: dict[str, str], prompt: str,
                 *, interactive=False, bootstrap_python=None, bootstrap_script=None):
        require(bool(argv) and all(isinstance(x, str) and "\x00" not in x for x in argv),
                "INVALID_ARGUMENT")
        require(Path(argv[0]).is_absolute() and cwd.is_absolute(), "UNSAFE_PATH")
        reject_links(Path(argv[0]))
        reject_links(cwd)
        require(cwd.is_dir(), "WORKSPACE_MISSING")
        require(all(isinstance(k, str) and isinstance(v, str) and k and "=" not in k
                    and "\x00" not in k + v for k, v in environment.items()), "INVALID_ENVIRONMENT")
        plan = json.dumps({"argv": argv, "cwd": str(cwd), "env": environment,
                           "prompt": prompt, "interactive": interactive},
                          ensure_ascii=True).encode() + b"\n"
        require(len(plan) <= 2 * 1024 * 1024, "RUNTIME_INPUT_QUOTA")
        self.job = WindowsJob() if os.name == "nt" else None
        self.process = None
        self.interactive = interactive
        self.input_lock = threading.Lock()
        # Bootstrap does not inherit provider tokens, agent grants, PYTHONPATH or
        # user profile variables. Child receives exactly the separately built env.
        boot_env = {k: os.environ[k] for k in ("SystemRoot", "WINDIR") if k in os.environ}
        options = {"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {
            "start_new_session": True}
        bootstrap = Path(bootstrap_script) if bootstrap_script else Path(__file__).with_name("process_bootstrap.py")
        reject_links(bootstrap)
        interpreter = Path(bootstrap_python) if bootstrap_python else Path(sys.executable)
        require(interpreter.is_absolute() and bootstrap.is_absolute(), "UNSAFE_PATH")
        reject_links(interpreter)
        try:
            self.process = subprocess.Popen([str(interpreter), "-I", "-S", "-B", str(bootstrap)],
                cwd=bootstrap.parent, env=boot_env, stdin=subprocess.PIPE,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False, **options)
            if self.job:
                self.job.attach(self.process)
            self.process.stdin.write(plan)
            self.process.stdin.flush()
            if not interactive:
                self.process.stdin.close()
        except BaseException:
            self.stop()
            self.close()
            raise

    def poll(self):
        return self.process.poll()

    def send_input(self, text: str, *, timeout_s=1):
        """Bounded operator console input, never a gameplay-agent command surface.

        A timeout may have partially delivered bytes: kill the process tree and
        report uncertainty. Callers must not replay the input into another process.
        """
        require(self.interactive and self.process is not None, "PROCESS_INPUT_DISABLED")
        require(isinstance(text, str) and "\x00" not in text
                and 0 < len(text.encode("utf-8")) <= 4096, "PROCESS_INPUT_QUOTA")
        require(0 < timeout_s <= 5, "INVALID_ARGUMENT")
        require(self.input_lock.acquire(blocking=False), "PROCESS_INPUT_BUSY")
        try:
            require(self.process.poll() is None, "PROCESS_NOT_RUNNING")
            errors = []

            def write():
                try:
                    self.process.stdin.write(text.encode("utf-8"))
                    self.process.stdin.flush()
                except (OSError, ValueError):
                    errors.append(True)

            sender = threading.Thread(target=write, daemon=True)
            sender.start()
            sender.join(timeout_s)
            if sender.is_alive():
                self.stop()
                sender.join(2)
                raise Fault("PROCESS_INPUT_UNCERTAIN")
            require(not errors, "PROCESS_INPUT_UNCERTAIN")
        finally:
            self.input_lock.release()

    def stop(self):
        if self.job:
            self.job.terminate()
        elif self.process is not None:
            try:
                os.killpg(self.process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        if self.process is not None:
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                raise Fault("PROCESS_STOP_FAILED") from None

    def close(self):
        # Closing a completed parent still kills any lingering grandchildren.
        if self.job:
            self.job.close()
        elif self.process is not None:
            self.stop()
        if self.process is not None:
            for stream in (self.process.stdout, self.process.stderr, self.process.stdin):
                if stream and not stream.closed:
                    stream.close()
