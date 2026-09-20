"""Native Windows ACL creation/verification for an operator-owned credential cache.

Standalone stdlib helper invoked with the pinned operator Python in isolated mode.
Creates the directory with its final ACL atomically; does not change PowerShell or
system security policy. It is not an adversarial gameplay sandbox certificate.
"""

import ctypes as c
import json
import os
import stat
import sys
from ctypes import wintypes as w
from pathlib import Path


def require(condition):
    if not condition:
        raise ValueError("AUTH_CACHE_PROTECTION_FAILED")


class Security:
    def __init__(self):
        self.adv = c.WinDLL("advapi32", use_last_error=True)
        self.kernel = c.WinDLL("kernel32", use_last_error=True)
        vp, pp = c.c_void_p, c.POINTER(c.c_void_p)
        signatures = {
            "OpenProcessToken": ([w.HANDLE, w.DWORD, c.POINTER(w.HANDLE)], w.BOOL),
            "GetTokenInformation": ([w.HANDLE, c.c_int, vp, w.DWORD, c.POINTER(w.DWORD)], w.BOOL),
            "ConvertSidToStringSidW": ([vp, pp], w.BOOL),
            "ConvertStringSecurityDescriptorToSecurityDescriptorW":
                ([w.LPCWSTR, w.DWORD, pp, c.POINTER(w.DWORD)], w.BOOL),
            "GetFileSecurityW": ([w.LPCWSTR, w.DWORD, vp, w.DWORD, c.POINTER(w.DWORD)], w.BOOL),
            "GetSecurityDescriptorOwner": ([vp, pp, c.POINTER(w.BOOL)], w.BOOL),
            "GetSecurityDescriptorControl": ([vp, c.POINTER(w.WORD), c.POINTER(w.DWORD)], w.BOOL),
            "GetSecurityDescriptorDacl": ([vp, c.POINTER(w.BOOL), pp, c.POINTER(w.BOOL)], w.BOOL),
            "GetAclInformation": ([vp, vp, w.DWORD, c.c_int], w.BOOL),
            "GetAce": ([vp, w.DWORD, pp], w.BOOL),
        }
        for name, (args, result) in signatures.items():
            function = getattr(self.adv, name)
            function.argtypes, function.restype = args, result
        for name, args, result in [
            ("GetCurrentProcess", [], w.HANDLE),
            ("CloseHandle", [w.HANDLE], w.BOOL),
            ("LocalFree", [vp], vp),
            ("CreateDirectoryW", [w.LPCWSTR, vp], w.BOOL),
        ]:
            function = getattr(self.kernel, name)
            function.argtypes, function.restype = args, result
        self.sid = self.current_sid()

    def sid_string(self, sid):
        text = c.c_void_p()
        require(self.adv.ConvertSidToStringSidW(sid, c.byref(text)))
        try:
            return c.wstring_at(text)
        finally:
            self.kernel.LocalFree(text)

    def current_sid(self):
        token = w.HANDLE()
        require(self.adv.OpenProcessToken(self.kernel.GetCurrentProcess(), 8, c.byref(token)))
        try:
            needed = w.DWORD()
            self.adv.GetTokenInformation(token, 1, None, 0, c.byref(needed))
            require(0 < needed.value < 65536)
            buffer = c.create_string_buffer(needed.value)
            require(self.adv.GetTokenInformation(token, 1, buffer, needed, c.byref(needed)))
            return self.sid_string(c.c_void_p.from_buffer(buffer))
        finally:
            self.kernel.CloseHandle(token)

    def create(self, path):
        class Attributes(c.Structure):
            _fields_ = [("length", w.DWORD), ("descriptor", c.c_void_p), ("inherit", w.BOOL)]

        descriptor = c.c_void_p()
        sddl = f"O:{self.sid}D:P(A;OICI;FA;;;{self.sid})(A;OICI;FA;;;SY)"
        require(self.adv.ConvertStringSecurityDescriptorToSecurityDescriptorW(
            sddl, 1, c.byref(descriptor), None))
        try:
            attributes = Attributes(c.sizeof(Attributes), descriptor, False)
            require(self.kernel.CreateDirectoryW(str(path), c.byref(attributes)))
        finally:
            self.kernel.LocalFree(descriptor)

    def verify(self, path, directory):
        needed = w.DWORD()
        self.adv.GetFileSecurityW(str(path), 5, None, 0, c.byref(needed))  # OWNER | DACL
        require(0 < needed.value < 1024 * 1024)
        descriptor = c.create_string_buffer(needed.value)
        require(self.adv.GetFileSecurityW(str(path), 5, descriptor, needed, c.byref(needed)))
        owner, defaulted = c.c_void_p(), w.BOOL()
        require(self.adv.GetSecurityDescriptorOwner(descriptor, c.byref(owner), c.byref(defaulted)))
        require(self.sid_string(owner) == self.sid)
        control, revision = w.WORD(), w.DWORD()
        require(self.adv.GetSecurityDescriptorControl(descriptor, c.byref(control), c.byref(revision)))
        require(not directory or control.value & 0x1000)  # SE_DACL_PROTECTED
        present, acl = w.BOOL(), c.c_void_p()
        require(self.adv.GetSecurityDescriptorDacl(descriptor, c.byref(present),
                                                   c.byref(acl), c.byref(defaulted)))
        require(present.value and acl.value)  # Missing and NULL DACLs allow everyone.
        # ACL_SIZE_INFORMATION: AceCount, AclBytesInUse, AclBytesFree.
        info = (w.DWORD * 3)()
        require(self.adv.GetAclInformation(acl, info, c.sizeof(info), 2))
        require(info[0] == 2)
        seen = set()
        for index in range(info[0]):
            ace = c.c_void_p()
            require(self.adv.GetAce(acl, index, c.byref(ace)))
            header = c.string_at(ace, 8)
            require(header[0] == 0)  # ACCESS_ALLOWED_ACE_TYPE, never conditional/object ACEs.
            flags = header[1]
            require(flags == 3 if directory else flags in (0, 16))
            require(int.from_bytes(header[4:8], "little") == 0x1F01FF)  # FILE_ALL_ACCESS
            seen.add(self.sid_string(c.c_void_p(ace.value + 8)))
        require(seen == {self.sid, "S-1-5-18"})


def no_links(path):
    for part in (path, *path.parents):
        try:
            details = part.lstat()
        except FileNotFoundError:
            continue
        require(not details.st_file_attributes & 0x400)  # Every reparse point, not only symlinks.
        require(not stat.S_ISREG(details.st_mode) or details.st_nlink == 1)


def main():
    require(os.name == "nt" and sys.version_info[:3] == (3, 12, 14))
    require(len(sys.argv) == 3 and sys.argv[2] in {"Create", "Verify"})
    path = Path(sys.argv[1])
    require(path.is_absolute())
    no_links(path)
    security = Security()
    if sys.argv[2] == "Create":
        require(not path.exists() and path.parent.is_dir())
        security.create(path)
    require(path.is_dir())
    children = list(path.iterdir())
    require(len(children) <= 32)
    for child in children:
        no_links(child)
        require(child.is_file())
        security.verify(child, False)
    security.verify(path, True)
    print(json.dumps({"status": "protected", "scope": "current-operator-and-SYSTEM",
                      "proves_gameplay_isolation": False}))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print(json.dumps({"status": "rejected", "code": "AUTH_CACHE_PROTECTION_FAILED"}))
        sys.exit(1)
