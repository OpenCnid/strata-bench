"""Private Windows writer-tree primitive, not a server/isolation certificate.

A new tree is created with its final protected DACL, without a writable-by-name
initialization window. Only the separate writer can populate it by pathname.
Ordinary processes of the controller's user have read access, not write/delete
or permission-changing access. The intended native writer must satisfy both
the sandbox group's normal check and its workspace SID's restricted check.
Retained controller handles fence the active directory names and must remain in
the protected operator process. Arbitrary process access is out of scope of this
primitive; the native broker/process boundary must enforce that seam.

Close never restores write permissions. Existing trees cannot be adopted here.
After a crash/close, parent rights can permit namespace changes: durable recovery
must quarantine the instance instead of trusting that its old path still binds it.
"""

import ctypes as c
from ctypes import wintypes as w
import os
from pathlib import Path
import re

from mcbench.launch_integrity import safe
from mcbench.storage import Fault, require


FILE_MODIFY = 0x1301BF  # Read/write/execute/delete, no WRITE_DAC or WRITE_OWNER.
FILE_ALL = 0x1F01FF
READ_CONTROL = 0x20000
SYNCHRONIZE = 0x100000


class UnicodeString(c.Structure):
    _fields_ = [("length", w.USHORT), ("maximum", w.USHORT), ("buffer", w.LPWSTR)]


class ObjectAttributes(c.Structure):
    _fields_ = [("length", w.ULONG), ("root", w.HANDLE),
               ("name", c.POINTER(UnicodeString)), ("attributes", w.ULONG),
               ("security", c.c_void_p), ("qos", c.c_void_p)]


class IoStatus(c.Structure):
    _fields_ = [("status", c.c_void_p), ("information", c.c_size_t)]


def component(name):
    # One NT path component only; reject DOS aliases, streams and normalization
    # ambiguity instead of trusting Path's host-specific interpretation.
    require(type(name) is str and 0 < len(name) <= 120
            and re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_. -]*", name)
            and not name.endswith((" ", "."))
            and name.split(".")[0].upper() not in {
                "CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(10)),
                *(f"LPT{i}" for i in range(10))}, "WRITER_COMPONENT_INVALID")
    return name


class WindowsSecurity:
    def __init__(self):
        require(os.name == "nt", "WRITER_PLATFORM_UNSUPPORTED")
        self.kernel = c.WinDLL("kernel32", use_last_error=True)
        self.adv = c.WinDLL("advapi32", use_last_error=True)
        self.nt = c.WinDLL("ntdll", use_last_error=True)
        vp, pp = c.c_void_p, c.POINTER(c.c_void_p)
        signatures = [
            (self.kernel, "GetCurrentProcess", [], w.HANDLE),
            (self.kernel, "CloseHandle", [w.HANDLE], w.BOOL),
            (self.kernel, "LocalFree", [vp], vp),
            (self.kernel, "CreateFileW", [w.LPCWSTR, w.DWORD, w.DWORD, vp,
                                         w.DWORD, w.DWORD, w.HANDLE], w.HANDLE),
            (self.adv, "OpenProcessToken", [w.HANDLE, w.DWORD, c.POINTER(w.HANDLE)], w.BOOL),
            (self.adv, "GetTokenInformation", [w.HANDLE, c.c_int, vp, w.DWORD,
                                               c.POINTER(w.DWORD)], w.BOOL),
            (self.adv, "ConvertSidToStringSidW", [vp, pp], w.BOOL),
            (self.adv, "ConvertStringSidToSidW", [w.LPCWSTR, pp], w.BOOL),
            (self.adv, "CheckTokenMembership", [w.HANDLE, vp, c.POINTER(w.BOOL)], w.BOOL),
            (self.adv, "LookupAccountSidW", [w.LPCWSTR, vp, w.LPWSTR, c.POINTER(w.DWORD),
                                            w.LPWSTR, c.POINTER(w.DWORD), c.POINTER(w.DWORD)], w.BOOL),
            (self.adv, "ConvertStringSecurityDescriptorToSecurityDescriptorW",
             [w.LPCWSTR, w.DWORD, pp, c.POINTER(w.DWORD)], w.BOOL),
            (self.adv, "GetNamedSecurityInfoW", [w.LPCWSTR, c.c_int, w.DWORD,
                                                pp, pp, pp, pp, pp], w.DWORD),
            (self.adv, "GetSecurityDescriptorControl", [vp, c.POINTER(w.WORD),
                                                       c.POINTER(w.DWORD)], w.BOOL),
            (self.adv, "GetAclInformation", [vp, vp, w.DWORD, c.c_int], w.BOOL),
            (self.adv, "GetAce", [vp, w.DWORD, pp], w.BOOL),
            (self.nt, "NtCreateFile", [c.POINTER(w.HANDLE), w.DWORD,
                c.POINTER(ObjectAttributes), c.POINTER(IoStatus), vp, w.ULONG,
                w.ULONG, w.ULONG, w.ULONG, vp, w.ULONG], w.LONG),
        ]
        for dll, name, arguments, result in signatures:
            api = getattr(dll, name)
            api.argtypes, api.restype = arguments, result
        self.current_sid = self.user_sid()

    def sid_text(self, sid):
        value = c.c_void_p()
        require(self.adv.ConvertSidToStringSidW(sid, c.byref(value)), "WRITER_IDENTITY_UNAVAILABLE")
        try:
            return c.wstring_at(value)
        finally:
            self.kernel.LocalFree(value)

    def user_sid(self):
        token, size = w.HANDLE(), w.DWORD()
        require(self.adv.OpenProcessToken(self.kernel.GetCurrentProcess(), 8, c.byref(token)),
                "WRITER_IDENTITY_UNAVAILABLE")
        try:
            self.adv.GetTokenInformation(token, 1, None, 0, c.byref(size))
            require(0 < size.value <= 65536, "WRITER_IDENTITY_UNAVAILABLE")
            buffer = c.create_string_buffer(size.value)
            require(self.adv.GetTokenInformation(token, 1, buffer, size, c.byref(size)),
                    "WRITER_IDENTITY_UNAVAILABLE")
            return self.sid_text(c.c_void_p.from_buffer(buffer))
        finally:
            self.kernel.CloseHandle(token)

    def check_principal(self, sid, kind_required):
        require(type(sid) is str and re.fullmatch(r"S-1-5-21-(?:\d+-){3}\d+", sid)
                and sid != self.current_sid, "WRITER_DISTINCT_USER_REQUIRED")
        pointer = c.c_void_p()
        require(self.adv.ConvertStringSidToSidW(sid, c.byref(pointer)), "WRITER_IDENTITY_UNAVAILABLE")
        try:
            name_size, domain_size, kind = w.DWORD(), w.DWORD(), w.DWORD()
            self.adv.LookupAccountSidW(None, pointer, None, c.byref(name_size),
                                      None, c.byref(domain_size), c.byref(kind))
            require(0 < name_size.value <= 1024 and domain_size.value <= 1024,
                    "WRITER_IDENTITY_UNAVAILABLE")
            name = c.create_unicode_buffer(name_size.value)
            domain = c.create_unicode_buffer(max(1, domain_size.value))
            require(self.adv.LookupAccountSidW(None, pointer, name, c.byref(name_size),
                    domain, c.byref(domain_size), c.byref(kind)) and kind.value == kind_required,
                    "WRITER_PRINCIPAL_TYPE")
            if kind_required == 4:  # SidTypeAlias: a specific local sandbox group.
                member = w.BOOL()
                require(self.adv.CheckTokenMembership(None, pointer, c.byref(member))
                        and not member.value, "WRITER_OPERATOR_IN_GROUP")
        finally:
            self.kernel.LocalFree(pointer)

    def descriptor(self, writer_sid, group_sid, scope_sid):
        self.check_principal(writer_sid, 1)
        self.check_principal(group_sid, 4)
        require(type(scope_sid) is str and re.fullmatch(r"S-1-5-21-(?:\d+-){3}\d+", scope_sid)
                and not scope_sid.startswith(self.current_sid.rsplit("-", 1)[0] + "-"),
                "WRITER_SCOPE_SID_INVALID")
        # OWNER RIGHTS overrides implicit WRITE_DAC for the owner, including
        # children created by the writer. SYSTEM is an explicit recovery principal.
        sddl = (f"O:{self.current_sid}D:P(A;OICI;FRFX;;;{self.current_sid})"
                f"(A;OICI;RC;;;OW)(A;OICI;FA;;;SY)(A;OICI;0x{FILE_MODIFY:x};;;{group_sid})"
                f"(A;OICI;0x{FILE_MODIFY:x};;;{scope_sid})")
        value = c.c_void_p()
        require(self.adv.ConvertStringSecurityDescriptorToSecurityDescriptorW(
            sddl, 1, c.byref(value), None), "WRITER_DESCRIPTOR_INVALID")
        return value

    def access(self, path):
        owner, acl, descriptor = c.c_void_p(), c.c_void_p(), c.c_void_p()
        result = self.adv.GetNamedSecurityInfoW(str(safe(path)), 1, 5, c.byref(owner),
            None, c.byref(acl), None, c.byref(descriptor))
        require(result == 0, "WRITER_ACL_UNAVAILABLE")
        try:
            require(owner.value and acl.value, "WRITER_ACL_CHANGED")
            control, revision = w.WORD(), w.DWORD()
            require(self.adv.GetSecurityDescriptorControl(descriptor, c.byref(control),
                c.byref(revision)), "WRITER_ACL_UNAVAILABLE")
            info = (w.DWORD * 3)()
            require(self.adv.GetAclInformation(acl, info, c.sizeof(info), 2)
                    and info[0] <= 32, "WRITER_ACL_CHANGED")
            entries = []
            for index in range(info[0]):
                ace = c.c_void_p()
                require(self.adv.GetAce(acl, index, c.byref(ace)), "WRITER_ACL_UNAVAILABLE")
                header = c.string_at(ace, 8)
                require(header[0] in {0, 1}, "WRITER_ACL_CHANGED")
                entries.append((header[0], header[1], self.sid_text(c.c_void_p(ace.value + 8)),
                                int.from_bytes(header[4:8], "little")))
            return self.sid_text(owner), bool(control.value & 0x1000), entries
        finally:
            self.kernel.LocalFree(descriptor)

    def verify(self, path, writer_sid, group_sid, scope_sid, *, directory, root=False):
        owner, protected, entries = self.access(path)
        require((owner == self.current_sid and protected if root
                 else owner in {self.current_sid, writer_sid}),
                "WRITER_ACL_CHANGED")
        flags = 3 if directory else 0
        require(all(kind == 0 and bits in {flags, flags | 16}
                    for kind, bits, _, _ in entries), "WRITER_ACL_CHANGED")
        expected = {(self.current_sid, 0x1200A9), ("S-1-3-4", READ_CONTROL),
                    ("S-1-5-18", FILE_ALL), (group_sid, FILE_MODIFY), (scope_sid, FILE_MODIFY)}
        require(len(entries) == len(expected) and {(sid, mask) for _, _, sid, mask in entries}
                == expected, "WRITER_ACL_CHANGED")

    def workspace_scope(self, workspace):
        """Inspect the newly enrolled, owned root of the pinned native profile.

        The subsequent native token/positive/sibling controls must still prove
        the observed ACL roles. This read is not a qualification certificate.
        """
        owner, _, entries = self.access(workspace)
        require(owner == self.current_sid, "WRITER_WORKSPACE_OWNER")
        candidates = [sid for kind, flags, sid, mask in entries if kind == 0 and flags == 3
                      and mask == FILE_MODIFY and re.fullmatch(r"S-1-5-21-(?:\d+-){3}\d+", sid)]
        prefix = self.current_sid.rsplit("-", 1)[0] + "-"
        groups = [sid for sid in candidates if sid.startswith(prefix)]
        scopes = [sid for sid in candidates if not sid.startswith(prefix)]
        require(len(groups) == len(scopes) == 1, "WRITER_SCOPE_UNAVAILABLE")
        self.check_principal(groups[0], 4)
        return groups[0], scopes[0]

    def open_directory(self, path, access=1):
        handle = self.kernel.CreateFileW(str(path), access, 3, None, 3, 0x02200000, None)
        require(handle not in (None, c.c_void_p(-1).value), "WRITER_PARENT_UNAVAILABLE")
        return handle

    def create(self, parent, name, descriptor, *, directory):
        text = c.create_unicode_buffer(component(name))
        length = len(name.encode("utf-16-le"))
        string = UnicodeString(length, length + 2, c.cast(text, w.LPWSTR))
        attributes = ObjectAttributes(c.sizeof(ObjectAttributes), parent,
                                      c.pointer(string), 0x40, descriptor, None)
        handle, status = w.HANDLE(), IoStatus()
        # FILE_CREATE (2) never opens/replaces an existing object. Synchronous,
        # no reparse traversal; directories deny replacement for this lifetime.
        # The guard needs no data-write or DELETE access. Keep its retained
        # authority narrow; ordinary server file handles must remain usable.
        # FILE_LIST_DIRECTORY participates in sharing checks. Metadata-only
        # handles do not reliably fence a directory rename on Windows.
        result = self.nt.NtCreateFile(c.byref(handle), READ_CONTROL | SYNCHRONIZE | 0x81,
            c.byref(attributes),
            c.byref(status), None, 0x10 if directory else 0x80,
            3 if directory else 1, 2, 0x200020 | (1 if directory else 0x40), None, 0)
        if result < 0:
            raise Fault("WRITER_CREATE_DENIED")
        if status.information != 2:  # FILE_CREATED, not FILE_OPENED/OVERWRITTEN.
            self.kernel.CloseHandle(handle)
            raise Fault("WRITER_CREATE_NOT_NEW")
        return handle.value


class WriterTree:
    """New-only protected root for one enrolled native workspace scope.

    This is not wired to ReferenceLauncher yet. A writer SID is a Windows
    principal, not proof of the owned server's token or exclusive account use.
    Server launch must bind that identity and its whole process lifetime before
    this primitive can support protected setup/scoring authority.
    """

    def __init__(self, path, writer_sid, group_sid, scope_sid):
        self.security = WindowsSecurity()
        self.parents, self.root_handle, self.descriptor = [], None, None
        self.closed = False
        self.path, self.writer_sid = Path(path), writer_sid
        self.group_sid, self.scope_sid = group_sid, scope_sid
        require(self.path.is_absolute(), "WRITER_PATH_INVALID")
        component(self.path.name)
        self.descriptor = self.security.descriptor(writer_sid, group_sid, scope_sid)
        try:
            parent = safe(self.path.parent)
            require(parent.is_dir(), "WRITER_PARENT_UNAVAILABLE")
            # Hold every ancestor against deletion/replacement before creation.
            for ancestor in reversed((parent, *parent.parents)):
                self.parents.append(self.security.open_directory(ancestor))
            parent_handle = self.security.open_directory(parent, 4 | SYNCHRONIZE)
            self.parents.append(parent_handle)
            self.root_handle = self.security.create(parent_handle, self.path.name,
                                                    self.descriptor, directory=True)
            # The separate list-access ancestor handle continues to deny
            # replacement. No need to retain parent directory creation rights.
            self.security.kernel.CloseHandle(self.parents.pop())
            self.verify()
        except BaseException:
            self.close()
            raise

    def verify(self):
        require(not self.closed, "WRITER_PREPARATION_CLOSED")
        self.security.verify(self.path, self.writer_sid, self.group_sid, self.scope_sid,
                             directory=True, root=True)

    def close(self):
        # No ACL reset/refund/reuse, including exceptions. Windows ACLs survive
        # a controller crash; only live retained handles disappear.
        if self.root_handle:
            self.security.kernel.CloseHandle(self.root_handle)
            self.root_handle = None
        for handle in reversed(self.parents):
            self.security.kernel.CloseHandle(handle)
        self.parents.clear()
        if self.descriptor:
            self.security.kernel.LocalFree(self.descriptor)
            self.descriptor = None
        self.closed = True

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
