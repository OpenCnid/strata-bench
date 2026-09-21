"""Local, one-instance Windows pipe with finite overlapped I/O and OS peer IDs."""

import ctypes as c
from ctypes import wintypes as w
import os
import re
import secrets
import threading
import time

from mcbench.storage import require
from .windows_writer import WindowsSecurity


class PrivatePipe:
    def __init__(self, group_sid, scope_sid, deadline):
        require(os.name == "nt" and 0 < deadline - time.monotonic() <= 720,
                "TELEMETRY_PIPE_PROFILE")
        self.security = WindowsSecurity()
        self.security.check_principal(group_sid, 4)
        require(isinstance(scope_sid, str) and re.fullmatch(r"S-1-5-21-(?:\d+-){3}\d+", scope_sid)
                and not scope_sid.startswith(self.security.current_sid.rsplit("-", 1)[0] + "-"),
                "TELEMETRY_PIPE_SCOPE")
        self.deadline, self.handle = deadline, None
        self.lock, self.active, self.closing = threading.RLock(), 0, False
        self.name = "\\\\.\\pipe\\strata-telemetry-" + secrets.token_hex(32)
        self.kernel = self.security.kernel
        self.kernel.CreateNamedPipeW.argtypes = [w.LPCWSTR, w.DWORD, w.DWORD, w.DWORD,
                                                w.DWORD, w.DWORD, w.DWORD, c.c_void_p]
        self.kernel.CreateNamedPipeW.restype = w.HANDLE
        self.kernel.GetNamedPipeClientProcessId.argtypes = [w.HANDLE, c.POINTER(w.ULONG)]
        self.kernel.GetNamedPipeClientProcessId.restype = w.BOOL
        self.kernel.CancelIoEx.argtypes = [w.HANDLE, c.c_void_p]
        self.kernel.CancelIoEx.restype = w.BOOL
        class Attributes(c.Structure):
            _fields_ = [("length", w.DWORD), ("descriptor", c.c_void_p), ("inherit", w.BOOL)]
        descriptor = c.c_void_p()
        # Specific rights exclude FILE_CREATE_PIPE_INSTANCE (bit 4). Generic
        # write would accidentally grant that right to the client principal.
        rights = "0x100183"  # read/write data/attributes, synchronize; no create-instance
        sddl = (f"O:{self.security.current_sid}D:P(A;;GA;;;{self.security.current_sid})(A;;GA;;;SY)"
                f"(A;;{rights};;;{group_sid})(A;;{rights};;;{scope_sid})")
        require(self.security.adv.ConvertStringSecurityDescriptorToSecurityDescriptorW(
                sddl, 1, c.byref(descriptor), None), "TELEMETRY_PIPE_DESCRIPTOR")
        try:
            attributes = Attributes(c.sizeof(Attributes), descriptor, False)
            handle = self.kernel.CreateNamedPipeW(self.name,
                3 | 0x40000000 | 0x80000, 4 | 2 | 8, 1, 65536, 65536, 0, c.byref(attributes))
            require(handle not in (None, c.c_void_p(-1).value), "TELEMETRY_PIPE_CREATE")
            self.handle = handle
        finally:
            self.kernel.LocalFree(descriptor)

    def _start(self, function, *args, **kwargs):
        # Cancel and submission share a lock. Close cannot miss a newly queued
        # operation, or recycle its HANDLE while native code still uses it.
        with self.lock:
            require(not self.closing and self.handle is not None, "TELEMETRY_PIPE_CLOSED")
            result = function(self.handle, *args, **kwargs)
            self.active += 1
            return result

    def _release_handle(self):
        if self.handle is not None:
            handle, self.handle = self.handle, None
            self.kernel.CloseHandle(handle)

    def _complete(self, operation, *, read=False):
        import _winapi
        try:
            remaining = self.deadline - time.monotonic()
            require(remaining > 0 and _winapi.WaitForSingleObject(operation.event,
                    max(1, int(remaining * 1000))) == 0, "TELEMETRY_PIPE_DEADLINE")
            count, error = operation.GetOverlappedResult(True)
            require(error == 0, "TELEMETRY_PIPE_IO")
            return operation.getbuffer() if read else count
        except BaseException:
            try:
                operation.cancel()
                operation.GetOverlappedResult(True)
            except OSError:
                pass  # Preserve the first fault if concurrent close canceled I/O.
            raise
        finally:
            with self.lock:
                self.active -= 1
                if self.closing and self.active == 0:
                    self._release_handle()

    def accept(self):
        import _winapi
        self._complete(self._start(_winapi.ConnectNamedPipe, overlapped=True))
        with self.lock:
            require(not self.closing and self.handle is not None, "TELEMETRY_PIPE_CLOSED")
            pid = w.ULONG()
            require(self.kernel.GetNamedPipeClientProcessId(self.handle, c.byref(pid)) and pid.value > 0,
                    "TELEMETRY_PIPE_PEER")
            return pid.value

    def receive(self, limit):
        import _winapi
        require(0 < limit <= 1048576, "TELEMETRY_PIPE_QUOTA")
        operation, _ = self._start(_winapi.ReadFile, limit + 1, overlapped=True)
        value = bytes(self._complete(operation, read=True))
        require(0 < len(value) <= limit, "TELEMETRY_PIPE_QUOTA")
        return value

    def send(self, value):
        import _winapi
        require(0 < len(value) <= 65536, "TELEMETRY_PIPE_QUOTA")
        operation, _ = self._start(_winapi.WriteFile, value, overlapped=True)
        require(self._complete(operation) == len(value), "TELEMETRY_PIPE_IO")

    def close(self):
        with self.lock:
            self.closing = True
            if self.handle is not None:
                self.kernel.CancelIoEx(self.handle, None)
                if self.active == 0:
                    self._release_handle()
