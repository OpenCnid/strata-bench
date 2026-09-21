"""Private aggregate metadata from an identity-bound read-only Windows process handle.

No memory contents, mapped filenames, command lines, environment or foreign process
enumeration. A walk is non-atomic; quotas/time checks apply between native calls.
This module has no termination authority and must stay outside the stop path.
"""

import ctypes as c
import copy
from ctypes import wintypes as w
import time

from .process_guard import HeldProcess, ProcessIdentity
from .storage import Fault, digest, require

REGION_QUOTA = 8192
QUERY_BUDGET_MS = 25
CENSUS_MAX_SEGMENTS = 8
CENSUS_MAX_NS = 8_000_000_000


class RegionQueryFault(Fault):
    def __init__(self, returned, win32_error):
        self.returned, self.win32_error = returned, win32_error
        super().__init__("RESOURCE_REGION_QUERY_FAILED")


class BasicMemory(c.Structure):
    _fields_ = [("base", c.c_void_p), ("allocation", c.c_void_p), ("allocation_protect", w.DWORD),
                ("partition", w.WORD), ("size", c.c_size_t), ("state", w.DWORD),
                ("protect", w.DWORD), ("kind", w.DWORD)]


class SystemInfo(c.Structure):
    _fields_ = [("architecture", w.DWORD), ("page_size", w.DWORD), ("minimum", c.c_void_p),
                ("maximum", c.c_void_p), ("processor_mask", c.c_size_t), ("processors", w.DWORD),
                ("processor_type", w.DWORD), ("granularity", w.DWORD),
                ("level", w.WORD), ("revision", w.WORD)]


class Io(c.Structure):
    _fields_ = [(name, c.c_ulonglong) for name in (
        "read_operations", "write_operations", "other_operations", "read_bytes", "write_bytes", "other_bytes")]


class Memory(c.Structure):
    _fields_ = [("cb", w.DWORD), ("page_faults", w.DWORD)] + [
        (name, c.c_size_t) for name in ("peak_working_set", "working_set", "peak_paged_pool",
            "paged_pool", "peak_nonpaged_pool", "nonpaged_pool", "pagefile", "peak_pagefile", "private")]


def walk_regions(query, limit, deadline_ns, *, quota=REGION_QUOTA, clock=time.perf_counter_ns, _progress=None):
    """Aggregate only; coalesced regions cannot double count previously covered bytes."""
    require(type(limit) is int and 0 < limit < 2**53, "RESOURCE_ADDRESS_SPACE_UNSUPPORTED")
    require(type(quota) is int and 0 < quota <= REGION_QUOTA, "RESOURCE_REGION_QUOTA")
    initial = {"status": "partial", "regions_observed": 0, "allocation_bases_observed": 0,
              "committed_bytes": {"private": 0, "mapped": 0, "image": 0},
              "committed_regions": {"private": 0, "mapped": 0, "image": 0},
              "reserved_bytes": 0, "free_bytes": 0, "non_atomic": True}
    progress = {} if _progress is None else _progress
    result = copy.deepcopy(progress.get("result", initial))
    result["status"] = "partial"
    result.pop("error_code", None)
    cursor, allocations = progress.get("cursor", 0), progress.get("allocations", set())
    try:
        while cursor < limit:
            require(clock() < deadline_ns, "RESOURCE_QUERY_BUDGET")
            require(result["regions_observed"] < quota, "RESOURCE_REGION_QUOTA")
            value = query(cursor)
            base, size = value["base"], value["size"]
            require(type(base) is int and type(size) is int and 0 <= base <= cursor
                    and size > 0 and cursor < base + size <= 2**64, "RESOURCE_REGION_INVALID")
            end = min(base + size, limit)
            amount = end - cursor
            state = value["state"]
            if state != 0x10000:
                allocation = value["allocation"]
                require(type(allocation) is int and 0 <= allocation <= base, "RESOURCE_REGION_INVALID")
            if state == 0x1000:  # MEM_COMMIT; COW still has its original mapped/image classification.
                kinds = {0x20000: "private", 0x40000: "mapped", 0x1000000: "image"}
                require(value["kind"] in kinds, "RESOURCE_REGION_TYPE")
                key = kinds[value["kind"]]
                result["committed_bytes"][key] += amount
                result["committed_regions"][key] += 1
            elif state == 0x2000:
                result["reserved_bytes"] += amount
            elif state == 0x10000:
                # Allocation/type/protection fields are undefined for MEM_FREE.
                result["free_bytes"] += amount
            else:
                raise Fault("RESOURCE_REGION_STATE")
            if state != 0x10000:
                allocations.add(allocation)
            cursor = end
            result["regions_observed"] += 1
            result["allocation_bases_observed"] = len(allocations)
        require(clock() <= deadline_ns, "RESOURCE_QUERY_BUDGET")
        result["status"] = "complete"
    except Fault as error:
        result["error_code"] = error.code
        if isinstance(error, RegionQueryFault):
            result.update(returned_bytes=error.returned, win32_error=error.win32_error)
    progress.update(cursor=cursor, allocations=allocations, result=copy.deepcopy(result))
    return result


class ResourceProcess:
    """Own a second identity-verified read-only handle; never borrow a guard handle."""

    def __init__(self, identity: ProcessIdentity):
        self.held = HeldProcess(identity.pid, query_information=True)
        try:
            require(self.held.identity == identity, "PROCESS_IDENTITY_MISMATCH")
            require(c.sizeof(c.c_void_p) == 8 and c.sizeof(BasicMemory) == 48,
                    "RESOURCE_ARCHITECTURE_UNSUPPORTED")
            self.kernel = self.held.kernel
            signatures = {
                "GetNativeSystemInfo": ([c.POINTER(SystemInfo)], None),
                "IsWow64Process2": ([w.HANDLE, c.POINTER(w.WORD), c.POINTER(w.WORD)], w.BOOL),
                "VirtualQueryEx": ([w.HANDLE, c.c_void_p, c.POINTER(BasicMemory), c.c_size_t], c.c_size_t),
                "GetProcessIoCounters": ([w.HANDLE, c.POINTER(Io)], w.BOOL),
                "GetProcessHandleCount": ([w.HANDLE, c.POINTER(w.DWORD)], w.BOOL),
                "K32GetProcessMemoryInfo": ([w.HANDLE, c.POINTER(Memory), w.DWORD], w.BOOL),
            }
            for name, (args, result) in signatures.items():
                method = getattr(self.kernel, name)
                method.argtypes, method.restype = args, result
            process_machine, native_machine = w.WORD(), w.WORD()
            require(self.kernel.IsWow64Process2(self.held.handle, c.byref(process_machine), c.byref(native_machine))
                    and process_machine.value == 0 and native_machine.value == 0x8664,
                    "RESOURCE_ARCHITECTURE_UNSUPPORTED")
            system = SystemInfo()
            self.kernel.GetNativeSystemInfo(c.byref(system))
            self.limit = (system.maximum or 0) + 1
            require(0 < self.limit < 2**53, "RESOURCE_ADDRESS_SPACE_UNSUPPORTED")
            self.identity = digest(identity.model_dump())
            self.census = None
        except BaseException:
            self.held.close()
            raise

    def region(self, address):
        value = BasicMemory()
        returned = self.kernel.VirtualQueryEx(self.held.handle, address, c.byref(value), c.sizeof(value))
        if returned != c.sizeof(value):
            raise RegionQueryFault(returned, c.get_last_error() if returned == 0 else None)
        return {"base": value.base or 0, "size": value.size, "state": value.state,
                "kind": value.kind, "allocation": value.allocation or 0}

    def counters(self):
        result = {}
        created, exited, kernel, user = (w.FILETIME() for _ in range(4))
        if self.kernel.GetProcessTimes(self.held.handle, c.byref(created), c.byref(exited),
                                       c.byref(kernel), c.byref(user)):
            result["cpu_100ns"] = {"kernel": str(kernel.dwHighDateTime << 32 | kernel.dwLowDateTime),
                                   "user": str(user.dwHighDateTime << 32 | user.dwLowDateTime)}
        else:
            result["cpu_error"] = c.get_last_error()
        io = Io()
        if self.kernel.GetProcessIoCounters(self.held.handle, c.byref(io)):
            result["io"] = {name: str(getattr(io, name)) for name, _ in Io._fields_}
        else:
            result["io_error"] = c.get_last_error()
        count = w.DWORD()
        if self.kernel.GetProcessHandleCount(self.held.handle, c.byref(count)):
            result["handles"] = count.value
        else:
            result["handles_error"] = c.get_last_error()
        memory = Memory()
        memory.cb = c.sizeof(memory)
        if self.kernel.K32GetProcessMemoryInfo(self.held.handle, c.byref(memory), memory.cb):
            result["memory"] = {name: getattr(memory, name) for name in (
                "page_faults", "working_set", "peak_working_set", "private")}
        else:
            result["memory_error"] = c.get_last_error()
        return result

    def snapshot(self):
        require(bool(self.held.handle), "RESOURCE_OBSERVER_CLOSED")
        start, cpu = time.perf_counter_ns(), time.thread_time_ns()
        before = self.held.exited()
        values = self.counters()
        counter_elapsed = time.perf_counter_ns() - start
        regions = self.census_step(start, before)
        after = self.held.exited()
        elapsed = time.perf_counter_ns() - start
        return {"schema": "strata/PrivateProcessResources/2", "process_identity": self.identity,
                "started_qpc_ns": str(start), "elapsed_ns": elapsed,
                "observer_thread_cpu_ns": time.thread_time_ns() - cpu,
                "region_quota": REGION_QUOTA, "query_budget_ms": QUERY_BUDGET_MS,
                "within_query_budget": elapsed <= QUERY_BUDGET_MS * 1_000_000,
                "counter_elapsed_ns": counter_elapsed,
                "signaled_before": before, "signaled_after": after,
                "counters": values, "regions": regions, "snapshot_is_atomic": False}

    def census_step(self, start, signaled):
        if signaled and self.census is None:
            return {"status": "not_run", "reason": "process_signaled"}
        if self.census is None:
            self.census = {"started": start, "segments": 0, "progress": {}}
        current = self.census
        expired = start - current["started"] >= CENSUS_MAX_NS or current["segments"] >= CENSUS_MAX_SEGMENTS
        if signaled or expired:
            result = copy.deepcopy(current["progress"].get("result", {}))
            result.update(status="partial", error_code="RESOURCE_PROCESS_SIGNALED" if signaled else "RESOURCE_CENSUS_DEADLINE")
        else:
            current["segments"] += 1
            result = walk_regions(self.region, self.limit, start + QUERY_BUDGET_MS * 1_000_000,
                                  clock=time.perf_counter_ns, _progress=current["progress"])
        elapsed = time.perf_counter_ns() - current["started"]
        if elapsed > CENSUS_MAX_NS:
            result.update(status="partial", error_code="RESOURCE_CENSUS_DEADLINE")
        result.update(census_started_qpc_ns=str(current["started"]), census_elapsed_ns=elapsed,
                      segments=current["segments"], census_max_ms=CENSUS_MAX_NS // 1_000_000,
                      census_max_segments=CENSUS_MAX_SEGMENTS)
        if result["status"] == "complete" or result.get("error_code") != "RESOURCE_QUERY_BUDGET":
            self.census = None
        return result

    def close(self):
        self.held.close()
