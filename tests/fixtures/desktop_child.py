"""Disposable test child. No Minecraft, input injection, desktop switch or visible UI."""

import ctypes
import json
import os
import subprocess
import sys
import time
from ctypes import wintypes
from pathlib import Path


def main():
    target = Path(sys.argv[1])
    mode = sys.argv[2]
    user = ctypes.WinDLL("user32", use_last_error=True)
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.GetCurrentThreadId.restype = wintypes.DWORD
    user.GetThreadDesktop.argtypes = [wintypes.DWORD]
    user.GetThreadDesktop.restype = wintypes.HANDLE
    user.GetUserObjectInformationW.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p,
                                               wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]
    user.GetUserObjectInformationW.restype = wintypes.BOOL
    desktop = user.GetThreadDesktop(kernel.GetCurrentThreadId())
    name = ctypes.create_unicode_buffer(256)
    needed = wintypes.DWORD()
    assert user.GetUserObjectInformationW(desktop, 2, name, ctypes.sizeof(name), ctypes.byref(needed))
    assert name.value.startswith("Strata-")  # No fixture window on the operator's desktop.
    user.CreateWindowExW.argtypes = [wintypes.DWORD, wintypes.LPCWSTR, wintypes.LPCWSTR,
        wintypes.DWORD, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
        wintypes.HANDLE, wintypes.HANDLE, wintypes.HANDLE, ctypes.c_void_p]
    user.CreateWindowExW.restype = wintypes.HANDLE
    user.DestroyWindow.argtypes = [wintypes.HANDLE]
    user.DestroyWindow.restype = wintypes.BOOL
    window = user.CreateWindowExW(0, "STATIC", "Strata disposable fixture", 0, 0, 0, 16, 16,
                                  None, None, None, None)
    assert window
    assert user.DestroyWindow(window)
    child = None
    if mode in ("descendant", "orphan"):
        child = subprocess.Popen([sys.executable, "-I", __file__, str(target.with_suffix(".child.json")), "hold"],
                                 creationflags=subprocess.CREATE_NO_WINDOW, close_fds=True)
    record = {"pid": os.getpid(), "desktop": name.value, "created_hidden_window": True,
              "arguments": sys.argv[3:], "allowed": os.environ.get("ALLOWED"),
              "private_canary": os.environ.get("STRATA_PRIVATE_CANARY"),
              "child_pid": child.pid if child else None}
    temporary = target.with_suffix(".pending")
    temporary.write_text(json.dumps(record), encoding="utf-8")
    temporary.replace(target)
    if mode == "exit":
        return 23
    if mode == "orphan":
        return 0
    time.sleep(30)
    target.with_suffix(".late").write_text("late effect", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
