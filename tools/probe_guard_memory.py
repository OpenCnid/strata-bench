"""Finite operator-only heap/guardian diagnostic, never a Minecraft qualification.

At most three distinct allocations, sequentially. No retries or input desktop use.
The original guardian measures its own unchanged 500 ms criterion. Later cleanup
is recorded separately and cannot convert a late sample into a pass.
"""

import argparse
import ctypes
import hashlib
import json
import os
from pathlib import Path
import queue
import threading
import time

from mcbench import process_guard, processes
from mcbench.process_guard import AttachedJava, inspect_process
from mcbench.processes import ManagedProcess
from mcbench.storage import Fault, canonical, reject_links, require

MIB = 1024 * 1024
HEADROOM = 8192 * MIB
WALL_SECONDS = 45


def memory_status():
    from ctypes import wintypes
    class Memory(ctypes.Structure):
        _fields_ = [("length", wintypes.DWORD), ("load", wintypes.DWORD)] + [
            (name, ctypes.c_ulonglong) for name in ("total", "available", "page_total",
                "page_available", "virtual_total", "virtual_available", "extended")]
    value = Memory()
    value.length = ctypes.sizeof(value)
    query = ctypes.WinDLL("kernel32", use_last_error=True).GlobalMemoryStatusEx
    query.argtypes, query.restype = [ctypes.POINTER(Memory)], wintypes.BOOL
    require(bool(query(ctypes.byref(value))), "MEMORY_OBSERVATION_UNAVAILABLE")
    return {"available_physical_bytes": value.available,
            "available_commit_bytes": value.page_available}


def process_memory(held):
    from ctypes import wintypes
    class Counters(ctypes.Structure):
        _fields_ = [("cb", wintypes.DWORD), ("faults", wintypes.DWORD)] + [
            (name, ctypes.c_size_t) for name in ("peak", "working", "paged_peak", "paged",
                "nonpaged_peak", "nonpaged", "pagefile", "peak_pagefile", "private")]
    query = held.kernel.K32GetProcessMemoryInfo
    query.argtypes = [wintypes.HANDLE, ctypes.c_void_p, wintypes.DWORD]
    query.restype = wintypes.BOOL
    value = Counters()
    value.cb = ctypes.sizeof(value)
    require(bool(query(held.handle, ctypes.byref(value), value.cb)), "MEMORY_OBSERVATION_UNAVAILABLE")
    return {"working_set_bytes": value.working, "peak_working_set_bytes": value.peak,
            "private_bytes": value.private}


def admit(samples, memory):
    require(1 <= len(samples) <= 3 and len(set(samples)) == len(samples)
            and all(type(n) is int and 16 <= n <= 3072 and n % 16 == 0 for n in samples),
            "MEMORY_PROFILE_INVALID")
    # Heap plus a separate conservative native overhead allowance and desktop margin.
    needed = (max(samples) + 512 + 2048) * MIB + HEADROOM
    require(all(type(memory.get(key)) is int and memory[key] >= needed for key in (
        "available_physical_bytes", "available_commit_bytes")), "DESKTOP_MEMORY_HEADROOM")


def publish(path, value):
    with path.open("xb") as stream:
        stream.write(canonical(value) + b"\n")
        stream.flush()
        os.fsync(stream.fileno())


def wait_line(output, owned, deadline):
    while time.monotonic() < deadline:
        owned.job.observe_members()
        require(owned.poll() is None, "FIXTURE_EARLY_EXIT")
        require(min(memory_status().values()) >= HEADROOM, "DESKTOP_MEMORY_HEADROOM")
        try:
            value = output.get(timeout=.05)
        except queue.Empty:
            continue
        require(value and len(value) <= 128 and value.endswith(b"\n"), "FIXTURE_PROTOCOL")
        return value.decode("ascii").strip()
    raise Fault("FIXTURE_DEADLINE")


def sample(java, classes, root, mib):
    admit([mib], memory_status())
    argv = [str(java), "-Xms64m", f"-Xmx{mib + 512}m", "-XX:+UseG1GC",
            "-cp", str(classes), "GuardianMemoryFixture", str(mib)]
    result = {"allocation_mib": mib, "arguments": argv[1:], "status": "incomplete",
              "stop_result": "not_run", "cleanup_confirmed": False}
    publish(root / f"intent-{mib}.json", {**result, "max_wall_seconds": WALL_SECONDS,
            "memory_before": memory_status(), "started_unix_ms": time.time_ns() // 1_000_000})
    environment = {key: os.environ[key] for key in ("SystemRoot", "WINDIR") if key in os.environ}
    owned = ManagedProcess(argv, root, environment, "", interactive=True)
    watchdog_fired = threading.Event()
    def expire():
        watchdog_fired.set()
        owned.stop()
    timer = threading.Timer(WALL_SECONDS, expire)
    timer.daemon = True
    timer.start()
    deadline = time.monotonic() + WALL_SECONDS
    guard = None
    output = queue.Queue(maxsize=4)
    def read():
        try:
            for _ in range(3):
                line = owned.process.stdout.readline(129)
                output.put_nowait(line)
                if not line:
                    break
        except (OSError, ValueError, queue.Full):
            pass
    reader = threading.Thread(target=read, daemon=True)
    reader.start()
    try:
        ready = wait_line(output, owned, deadline).split()
        require(len(ready) == 2 and ready[0] == "ready" and ready[1].isdigit(), "FIXTURE_PROTOCOL")
        pid = int(ready[1])
        owned.job.observe_members()
        require(pid in owned.job.members, "FIXTURE_NOT_OWNED")
        guard = AttachedJava(inspect_process(pid), deadline=deadline)
        owned.send_input("allocate\n")
        require(wait_line(output, owned, deadline) == f"allocated {mib}", "FIXTURE_PROTOCOL")
        result["memory_loaded"] = process_memory(guard.process)
        require(result["memory_loaded"]["private_bytes"] >= mib * MIB, "FIXTURE_ALLOCATION_MISSING")
        result["memory_available_loaded"] = memory_status()
        require(time.monotonic() < deadline, "FIXTURE_DEADLINE")
        try:
            guard.terminate()
            result["stop_result"] = "pass"
        except Fault as error:
            result["stop_result"] = "fail"
            result["stop_error_code"] = error.code
        result["termination_timing"] = guard.termination_timing
        # This extra observation is cleanup evidence, never part of the 500 ms proof.
        require(guard.process.exited(5000), "FIXTURE_CLEANUP_UNCONFIRMED")
        owned.process.wait(timeout=5)
        result["status"] = "measured"
    except Exception as error:
        result["error_code"] = error.code if isinstance(error, Fault) else type(error).__name__
    finally:
        result["cleanup_errors"] = []
        def cleanup(operation):
            try:
                operation()
            except Exception as error:
                result["cleanup_errors"].append(
                    error.code if isinstance(error, Fault) else type(error).__name__)
        def observe_cleanup():
            owned.process.wait(timeout=5)
            until = time.monotonic() + 5
            while time.monotonic() < until:
                counts, handles = owned.job.accounting(), owned.job.member_status()
                result["outer_job"], result["outer_handles"] = counts, handles
                if (counts["active_processes"] == 0 and counts["total_processes"] > 0
                        and counts["total_processes"] == handles["held_processes"]
                        == handles["signaled_processes"]):
                    result["cleanup_confirmed"] = True
                    return
                time.sleep(.01)
            raise Fault("FIXTURE_CLEANUP_UNCONFIRMED")
        cleanup(owned.stop)
        cleanup(observe_cleanup)
        if guard:
            cleanup(guard.close)
        # Closing the Job still happens if explicit kill/wait/accounting fails.
        cleanup(owned.close)
        timer.cancel()
        timer.join(2)
        reader.join(2)
        result["watchdog_fired"] = watchdog_fired.is_set()
        if result["watchdog_fired"] or result["cleanup_errors"] or timer.is_alive() or reader.is_alive():
            result["status"] = "incomplete"
        try:
            result["memory_after"] = memory_status()
        except Fault as error:
            result["status"], result["memory_error_code"] = "incomplete", error.code
        publish(root / f"result-{mib}.json", result)
    return result


def run(java, classes, root, samples):
    require(os.name == "nt", "WINDOWS_REQUIRED")
    repository = Path(__file__).resolve().parents[1]
    for path in (java, classes, root):
        require(path.is_absolute(), "UNSAFE_PATH")
        reject_links(path)
    require(not root.is_relative_to(repository) and not root.exists(), "PRIVATE_FRESH_OUTPUT_REQUIRED")
    require(java.name.casefold() == "java.exe" and java.is_file(), "PREREQUISITE_MISSING")
    fixture = classes / "GuardianMemoryFixture.class"
    reject_links(fixture)
    require(fixture.is_file(), "PREREQUISITE_MISSING")
    admit(samples, memory_status())
    root.mkdir()
    paths = [Path(__file__), Path(process_guard.__file__), Path(processes.__file__), java,
             java.parent.parent / "bin/server/jvm.dll", java.parent.parent / "lib/modules", fixture,
             repository / "tests/fixtures/GuardianMemoryFixture.java"]
    pins = {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
    plan = {"schema": "strata/PrivateGuardianMemoryProbe/1", "policy": "g1-touched-heap/1",
            "classification": "synthetic-workload-native-process", "samples_mib": samples,
            "minecraft": False, "model_calls": 0, "physical_input": False,
            "scoring_eligible": False, "guardian_wait_bound_ms": 500,
            "max_sample_wall_seconds": WALL_SECONDS, "desktop_headroom_bytes": HEADROOM,
            "source_sha256": pins}
    publish(root / "plan.json", plan)
    results = []
    for mib in samples:
        result = sample(java, classes, root, mib)
        results.append(result)
        if result["status"] != "measured" or not result["cleanup_confirmed"]:
            break
    unchanged = all(hashlib.sha256(Path(path).read_bytes()).hexdigest() == sha for path, sha in pins.items())
    summary = {**plan, "sources_unchanged": unchanged, "results": results,
               "status": "measured" if unchanged and len(results) == len(samples)
               and all(r["status"] == "measured" and r["cleanup_confirmed"] for r in results)
               else "incomplete"}
    publish(root / "summary.json", summary)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--java", type=Path, required=True)
    parser.add_argument("--classes", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--mib", nargs="+", type=int, required=True)
    args = parser.parse_args()
    result = run(args.java, args.classes, args.output, args.mib)
    print(json.dumps({"status": result["status"], "scoring_eligible": False,
        "samples": [{"mib": r["allocation_mib"], "stop_result": r["stop_result"],
                     "cleanup_confirmed": r["cleanup_confirmed"]} for r in result["results"]]}))
    return 0 if result["status"] == "measured" else 1


if __name__ == "__main__":
    raise SystemExit(main())
