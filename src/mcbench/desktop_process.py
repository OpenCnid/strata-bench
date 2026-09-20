"""Operator-only non-input Windows desktop and bounded process-tree lifetime.

This is a launch primitive, not an OS/credential/network sandbox, a GUI driver,
or permission to launch a game. It never switches desktops or injects input.
Only an operator-constructed command may be used after separate authorization.
"""

import ctypes
import os
import secrets
import subprocess
import threading
import time
from ctypes import wintypes
from pathlib import Path

from .processes import WindowsJob
from .storage import Fault, reject_links, require

POLICY = "windows-noninput-desktop-suspended-job/1"


class StartupInfo(ctypes.Structure):
    _fields_ = [("cb", wintypes.DWORD), ("lpReserved", wintypes.LPWSTR),
                ("lpDesktop", wintypes.LPWSTR), ("lpTitle", wintypes.LPWSTR)] + [
                    (name, wintypes.DWORD) for name in (
                        "dwX", "dwY", "dwXSize", "dwYSize", "dwXCountChars",
                        "dwYCountChars", "dwFillAttribute", "dwFlags")] + [
                ("wShowWindow", wintypes.WORD), ("cbReserved2", wintypes.WORD),
                ("lpReserved2", ctypes.c_void_p), ("hStdInput", wintypes.HANDLE),
                ("hStdOutput", wintypes.HANDLE), ("hStdError", wintypes.HANDLE)]


class ProcessInfo(ctypes.Structure):
    _fields_ = [("hProcess", wintypes.HANDLE), ("hThread", wintypes.HANDLE),
                ("dwProcessId", wintypes.DWORD), ("dwThreadId", wintypes.DWORD)]


class DesktopApi:
    def __init__(self):
        require(os.name == "nt", "DESKTOP_LAUNCH_UNSUPPORTED")
        self.user = ctypes.WinDLL("user32", use_last_error=True)
        self.kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        for library, signatures in ((self.user, {
            "CreateDesktopW": ([wintypes.LPCWSTR, ctypes.c_void_p, ctypes.c_void_p,
                                wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p], wintypes.HANDLE),
            "CloseDesktop": ([wintypes.HANDLE], wintypes.BOOL),
            "OpenInputDesktop": ([wintypes.DWORD, wintypes.BOOL, wintypes.DWORD], wintypes.HANDLE),
            "GetProcessWindowStation": ([], wintypes.HANDLE),
            "GetUserObjectInformationW": ([wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p,
                                           wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)], wintypes.BOOL),
        }), (self.kernel, {
            "CreateProcessW": ([wintypes.LPCWSTR, wintypes.LPWSTR, ctypes.c_void_p,
                                ctypes.c_void_p, wintypes.BOOL, wintypes.DWORD,
                                ctypes.c_void_p, wintypes.LPCWSTR, ctypes.POINTER(StartupInfo),
                                ctypes.POINTER(ProcessInfo)], wintypes.BOOL),
            "ResumeThread": ([wintypes.HANDLE], wintypes.DWORD),
            "TerminateProcess": ([wintypes.HANDLE, wintypes.UINT], wintypes.BOOL),
            "WaitForSingleObject": ([wintypes.HANDLE, wintypes.DWORD], wintypes.DWORD),
            "GetExitCodeProcess": ([wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)], wintypes.BOOL),
            "CloseHandle": ([wintypes.HANDLE], wintypes.BOOL),
        })):
            for name, (arguments, result) in signatures.items():
                function = getattr(library, name)
                function.argtypes, function.restype = arguments, result

    def name(self, handle):
        value = ctypes.create_unicode_buffer(256)
        needed = wintypes.DWORD()
        require(bool(handle) and bool(self.user.GetUserObjectInformationW(
            handle, 2, value, ctypes.sizeof(value), ctypes.byref(needed))), "DESKTOP_QUERY_FAILED")
        require(0 < len(value.value) < 256, "DESKTOP_QUERY_FAILED")
        return value.value

    def input_name(self):
        handle = self.user.OpenInputDesktop(0, False, 0x0001)  # DESKTOP_READOBJECTS only
        require(bool(handle), "DESKTOP_INPUT_UNAVAILABLE")
        try:
            return self.name(handle)
        finally:
            require(bool(self.user.CloseDesktop(handle)), "DESKTOP_CLOSE_FAILED")


def launch_values(argv, cwd, environment):
    require(isinstance(argv, list) and argv and all(isinstance(x, str) and "\0" not in x
                                                 for x in argv), "INVALID_ARGUMENT")
    require(Path(argv[0]).is_absolute() and isinstance(cwd, Path) and cwd.is_absolute(),
            "UNSAFE_PATH")
    reject_links(Path(argv[0]))
    reject_links(cwd)
    require(Path(argv[0]).is_file() and cwd.is_dir(), "WORKSPACE_MISSING")
    require(isinstance(environment, dict) and all(isinstance(k, str) and isinstance(v, str)
            and k and "=" not in k and "\0" not in k + v for k, v in environment.items()),
            "INVALID_ENVIRONMENT")
    require(len({key.casefold() for key in environment}) == len(environment), "INVALID_ENVIRONMENT")
    command = subprocess.list2cmdline(argv)
    block = "\0".join(f"{key}={environment[key]}" for key in sorted(environment, key=str.casefold)) + "\0\0"
    try:
        require(len(command.encode("utf-16-le")) // 2 < 32767, "PROCESS_ARGUMENT_QUOTA")
        require(len(block.encode("utf-16-le")) <= 131072, "PROCESS_ENVIRONMENT_QUOTA")
    except UnicodeError:
        raise Fault("INVALID_ARGUMENT") from None
    return command, block


class DesktopProcess:
    """One fresh desktop and one job. No inherited handles or environment.

    A wall watchdog also stops if the owned desktop becomes the input desktop or
    input-desktop inspection fails. This cannot certify an adversarial child:
    same-user code still has that user's privileges and can deliberately escape
    desktop placement. Production credential/process isolation remains separate.
    """

    def __init__(self, argv: list[str], cwd: Path, environment: dict[str, str], *, max_wall_ms=10000):
        command, block = launch_values(argv, cwd, environment)
        require(type(max_wall_ms) is int and 1 <= max_wall_ms <= 600000, "INVALID_ARGUMENT")
        self.api = DesktopApi()
        self.lock = threading.RLock()
        self.done = threading.Event()
        self.desktop = None
        self.job = None
        self.attached = False
        self.info = ProcessInfo()
        self.reason = None
        self.closed = False
        self.monitor = None
        self.deadline = time.monotonic() + max_wall_ms / 1000
        self.name = "Strata-" + secrets.token_hex(16)
        try:
            station = self.api.name(self.api.user.GetProcessWindowStation())
            require(station.casefold() == "winsta0", "DESKTOP_STATION_UNSUPPORTED")
            self.initial_input = self.api.input_name()
            # READOBJECTS | CREATEWINDOW | WRITEOBJECTS. No SWITCHDESKTOP access.
            self.desktop = self.api.user.CreateDesktopW(self.name, None, None, 0, 0x0083, None)
            require(bool(self.desktop) and self.api.name(self.desktop) == self.name,
                    "DESKTOP_CREATE_FAILED")
            self._check_noninput()
            self.job = WindowsJob()
            startup = StartupInfo()
            startup.cb = ctypes.sizeof(startup)
            startup.lpDesktop = station + "\\" + self.name
            startup.dwFlags = 0x0001 | 0x0080  # USESHOWWINDOW | FORCEOFFFEEDBACK
            startup.wShowWindow = 0  # SW_HIDE; no foreground helper console/window
            command_buffer = ctypes.create_unicode_buffer(command)
            env_buffer = ctypes.create_unicode_buffer(block)
            # Suspended + Unicode environment + no console. No inherited handles.
            require(bool(self.api.kernel.CreateProcessW(argv[0], command_buffer, None, None,
                False, 0x00000004 | 0x00000400 | 0x08000000, env_buffer, str(cwd),
                ctypes.byref(startup), ctypes.byref(self.info))), "PROCESS_LAUNCH_FAILED")
            self.job.attach_handle(self.info.hProcess)  # before any child user code
            self.attached = True
            self._check_noninput()
            require(time.monotonic() < self.deadline, "PROCESS_START_DEADLINE")
            require(self.api.kernel.ResumeThread(self.info.hThread) == 1, "PROCESS_RESUME_FAILED")
            self.api.kernel.CloseHandle(self.info.hThread)
            self.info.hThread = None
            self.monitor = threading.Thread(target=self._watch, daemon=True)
            self.monitor.start()
        except BaseException:
            self.close()
            raise

    @property
    def pid(self):
        return self.info.dwProcessId

    def _check_noninput(self):
        require(self.api.input_name().casefold() != self.name.casefold(), "DESKTOP_BECAME_INPUT")

    def _watch(self):
        while not self.done.wait(.05):
            try:
                with self.lock:
                    if self.closed:
                        return
                    self._check_noninput()
                    require(time.monotonic() < self.deadline, "PROCESS_WALL_EXHAUSTED")
            except Exception as fault:
                self.reason = fault.code if isinstance(fault, Fault) else "DESKTOP_WATCHDOG_FAILED"
                try:
                    self.stop()
                except Fault:
                    self.reason = "PROCESS_STOP_FAILED"
                    # Closing the last non-inherited job handle is the kernel backstop.
                    with self.lock:
                        if self.job:
                            self.job.close()
                return

    def poll(self):
        with self.lock:
            require(not self.closed and bool(self.info.hProcess), "PROCESS_CLOSED")
            state = self.api.kernel.WaitForSingleObject(self.info.hProcess, 0)
            require(state in (0, 258), "PROCESS_QUERY_FAILED")
            if state == 258:
                return None
            result = wintypes.DWORD()
            require(bool(self.api.kernel.GetExitCodeProcess(self.info.hProcess, ctypes.byref(result))),
                    "PROCESS_QUERY_FAILED")
            return result.value

    def wait(self, timeout_s=10):
        require(type(timeout_s) in (int, float) and 0 <= timeout_s <= 60, "INVALID_ARGUMENT")
        deadline = time.monotonic() + timeout_s
        while True:
            result = self.poll()
            if result is not None:
                return result
            remaining = deadline - time.monotonic()
            require(remaining > 0, "PROCESS_WAIT_TIMEOUT")
            # Never wait on a HANDLE another thread might close. Each poll holds
            # the lock, while the watchdog remains free to stop between polls.
            time.sleep(min(.01, remaining))

    def stop(self):
        with self.lock:
            if self.closed:
                return
            if self.job and self.attached:
                self.job.terminate()
            # The process can exist suspended before job assignment fails.
            elif self.info.hProcess and self.api.kernel.WaitForSingleObject(self.info.hProcess, 0) == 258:
                if not self.api.kernel.TerminateProcess(self.info.hProcess, 125):
                    require(self.api.kernel.WaitForSingleObject(self.info.hProcess, 2000) == 0,
                            "PROCESS_STOP_FAILED")
            if self.info.hProcess:
                require(self.api.kernel.WaitForSingleObject(self.info.hProcess, 2000) == 0, "PROCESS_STOP_FAILED")

    def close(self):
        self.done.set()
        with self.lock:
            if self.closed:
                return
            try:
                self.stop()
            finally:
                if self.job:
                    self.job.close()
                for field in ("hThread", "hProcess"):
                    handle = getattr(self.info, field)
                    if handle:
                        self.api.kernel.CloseHandle(handle)
                        setattr(self.info, field, None)
                if self.desktop:
                    require(bool(self.api.user.CloseDesktop(self.desktop)), "DESKTOP_CLOSE_FAILED")
                    self.desktop = None
                self.closed = True
        if self.monitor and threading.current_thread() != self.monitor:
            self.monitor.join(2)

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
