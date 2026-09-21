"""Private independent exit/resource observation; no game or termination authority.

Exit waits and resource queries use separate threads and separately held handles.
Slow/unavailable metadata stays incomplete; neither thread is in the guardian path.
"""

import json
import os
from pathlib import Path
import threading
import time

from .native_settings import strict_json
from .process_guard import HeldProcess
from .process_resources import ResourceProcess
from .storage import Fault, reject_links, require


class Journal:
    def __init__(self, path, *, byte_limit=1048576):
        require(path.is_absolute() and path.parent.is_dir(), "UNSAFE_PATH")
        reject_links(path)
        self.stream = path.open("xb")
        self.byte_limit = byte_limit
        self.bytes = self.records = 0

    def emit(self, kind, **value):
        raw = (json.dumps({"seq": self.records + 1, "qpc_ns": time.perf_counter_ns(),
                           "kind": kind, **value}, separators=(",", ":"), allow_nan=False) + "\n").encode()
        require(self.bytes + len(raw) <= self.byte_limit, "OBSERVER_QUOTA")
        require(self.stream.write(raw) == len(raw), "OBSERVER_WRITE_FAILED")
        self.stream.flush()
        self.bytes += len(raw)
        self.records += 1

    def close(self):
        try:
            self.stream.flush()
            os.fsync(self.stream.fileno())
        finally:
            self.stream.close()


class ResourceCollector:
    """One Hz, finite journal and lifetime; its thread exclusively owns its handle."""

    def __init__(self, identity, path, stop, deadline_ns):
        self.identity, self.path, self.stop, self.deadline = identity, path, stop, deadline_ns
        self.summary = {"status": "fail", "samples": 0, "complete_counter_samples": 0,
                        "complete_region_censuses": 0, "partial_region_samples": 0, "records": 0, "bytes": 0}
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.started = False

    def start(self):
        self.thread.start()
        self.started = True

    def observe(self, reader, journal, kind):
        require(self.summary["samples"] < 512, "RESOURCE_SAMPLE_QUOTA")
        value = reader.snapshot()
        journal.emit(kind, observation=value)
        self.summary["samples"] += 1
        live = not value["signaled_before"] and not value["signaled_after"]
        self.summary["complete_counter_samples"] += (live and value["counter_elapsed_ns"] <= 25_000_000
            and not any(key.endswith("_error") for key in value["counters"]))
        complete = (live
            and value["regions"]["status"] == "complete" and value["within_query_budget"]
            and not any(key.endswith("_error") for key in value["counters"]))
        self.summary["complete_region_censuses" if complete else "partial_region_samples"] += 1
        return value["signaled_after"]

    def run(self):
        reader = journal = None
        try:
            journal = Journal(self.path, byte_limit=2097152)
            reader = ResourceProcess(self.identity)
            saw_exit = False
            while not self.stop.is_set():
                require(time.perf_counter_ns() < self.deadline, "OBSERVER_DEADLINE")
                next_sample = time.perf_counter_ns() + 1_000_000_000
                saw_exit = self.observe(reader, journal, "resources")
                if saw_exit:
                    break
                self.stop.wait(max(0, (next_sample - time.perf_counter_ns()) / 1_000_000_000))
            if not saw_exit and reader.held.exited():
                self.observe(reader, journal, "terminal_resources")
            self.summary["status"] = "pass"
        except Exception as error:
            self.summary["error_code"] = error.code if isinstance(error, Fault) else type(error).__name__
        finally:
            if reader:
                try:
                    reader.close()
                except Exception:
                    self.summary.update(status="fail", error_code="RESOURCE_HANDLE_CLOSE_FAILED")
            if journal:
                try:
                    journal.close()
                except Exception:
                    self.summary.update(status="fail", error_code="OBSERVER_WRITE_FAILED")
                self.summary.update(records=journal.records, bytes=journal.bytes)


class ExitObserver:
    """Drop-in private driver observer with separate bounded aggregate resources.

    The caller must already own the process. Pass its expected identity when
    available. A successful observation never grants stop/scoring authority.
    """

    def __init__(self, pid, journal, path, *, expected_identity=None):
        self.held = HeldProcess(pid)
        try:
            require(expected_identity is None or self.held.identity == expected_identity,
                    "PROCESS_IDENTITY_MISMATCH")
            self.journal, self.path = Path(journal), Path(path)
            for target in (self.journal, self.path):
                require(target.is_absolute(), "UNSAFE_PATH")
                reject_links(target)
            self.stop = threading.Event()
            self.finish_fault = None
            self.bytes = self.records = self.last_seq = self.source_offset = 0
            self.max_wait_span_ns = 0
            self.summary = {"policy": "held-process-qpc-exit-resources/3", "status": "fail",
                "exited": False, "termination_authority": False, "guardian_verdict_unchanged": True}
            clock = time.get_clock_info("perf_counter")
            require(clock.monotonic and not clock.adjustable and clock.resolution <= .000001,
                    "OBSERVER_CLOCK_UNSUPPORTED")
            self.deadline = time.perf_counter_ns() + 480_000_000_000
            resource_path = self.path.with_name(self.path.stem + "-resources.jsonl")
            self.resources = ResourceCollector(self.held.identity, resource_path, self.stop, self.deadline)
            self.thread = threading.Thread(target=self.run, daemon=True)
            self.thread.start()
        except BaseException:
            self.held.close()
            raise
        try:
            self.resources.start()
        except BaseException:
            self.finish()
            raise

    def journal_events(self):
        if not self.journal.exists():
            return
        reject_links(self.journal)
        with self.journal.open("rb") as source:
            size = os.fstat(source.fileno()).st_size
            require(self.source_offset <= size <= 1048576, "SUPERVISOR_QUOTA")
            source.seek(self.source_offset)
            raw = source.read(1048577 - self.source_offset)
        require(self.source_offset + len(raw) <= 1048576, "SUPERVISOR_QUOTA")
        for line in raw.splitlines(keepends=True):
            if not line.endswith(b"\n"):
                break
            record = strict_json(line)
            require(type(record["seq"]) is int and record["seq"] == self.last_seq + 1
                    and record["schema"] == "strata/SupervisorEvent/1",
                    "SUPERVISOR_SEQUENCE")
            self.sink.emit("supervisor_record_seen", source_seq=record["seq"], source_kind=record["kind"],
                source_clock_id=record["source_clock_id"], source_mono_ms=record["mono_ms"],
                source_utc=record["at"], source_hash=record["hash"])
            self.last_seq = record["seq"]
            self.source_offset += len(line)

    def run(self):
        self.sink = None
        try:
            self.sink = Journal(self.path)
            self.sink.emit("started", process=self.held.identity.model_dump(mode="json"),
                clocks={n: vars(time.get_clock_info(n)) for n in ("perf_counter", "monotonic", "time")},
                wall_unix_ns=time.time_ns(), wait_timeout_ms=10, resource_interval_ms=1000,
                resource_policy="aggregate-metadata-region-census/2")
            last_alive = None
            while not self.stop.is_set():
                require(time.perf_counter_ns() < self.deadline, "OBSERVER_DEADLINE")
                self.journal_events()
                began = time.perf_counter_ns()
                exited = self.held.exited(10)
                ended = time.perf_counter_ns()
                self.max_wait_span_ns = max(self.max_wait_span_ns, ended - began)
                if exited:
                    self.summary.update(exited=True, exit_wait={"began_ns": began,
                        "returned_ns": ended, "last_alive_wait": last_alive})
                    self.sink.emit("exit_seen", **self.summary["exit_wait"])
                    self.summary["status"] = "pass"
                    break
                last_alive = {"began_ns": began, "returned_ns": ended}
            if self.summary["exited"]:
                until = time.perf_counter_ns() + 200_000_000
                while not self.stop.is_set() and time.perf_counter_ns() < until:
                    self.journal_events()
                    self.stop.wait(.01)
            self.journal_events()
            self.sink.emit("finished", status=self.summary["status"], max_wait_span_ns=self.max_wait_span_ns)
        except Exception as error:
            self.summary.update(status="fail", error_code=error.code if isinstance(error, Fault) else type(error).__name__)
        finally:
            try:
                self.held.close()
            except Exception:
                self.summary.update(status="fail", error_code="OBSERVER_HANDLE_CLOSE_FAILED")
            self.stop.set()
            if self.sink:
                try:
                    self.sink.close()
                except Exception:
                    self.summary.update(status="fail", error_code="OBSERVER_WRITE_FAILED")
                self.bytes, self.records = self.sink.bytes, self.sink.records

    def finish(self):
        # Two seconds total; never close a handle still used by its owning thread.
        self.stop.set()
        until = time.monotonic() + 2
        self.thread.join(max(0, until - time.monotonic()))
        if self.resources.started:
            self.resources.thread.join(max(0, until - time.monotonic()))
        if self.thread.is_alive() or (self.resources.started and self.resources.thread.is_alive()):
            self.finish_fault = self.finish_fault or "OBSERVER_JOIN_TIMEOUT"
        elif self.resources.summary["status"] != "pass":
            self.finish_fault = self.finish_fault or "RESOURCE_OBSERVER_FAILED"
        value = {**self.summary, "records": self.records, "bytes": self.bytes,
                 "max_wait_span_ns": self.max_wait_span_ns, "resources": dict(self.resources.summary)}
        if self.finish_fault:
            value.update(status="fail", error_code=self.finish_fault)
        return value
