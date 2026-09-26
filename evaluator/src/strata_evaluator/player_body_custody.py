"""Private body observer inputs/output under an existing protected writer.

This adds no standalone process launcher, gameplay route or probe admission.
"""

import os
from pathlib import Path
import shutil
from typing import Literal

from pydantic import Field

from mcbench.contracts import Strict
from mcbench.inference_transport import strict_json
from mcbench.launch_integrity import FileLease, safe, snapshot
from mcbench.storage import digest, require
from mcbench.vanilla_persistence import VanillaPersistence
from mcbench.worker_bundle import launch_path

from .craft_reference import PrivateFile, check_file, copy_pinned, private_path
from .player_body_evidence import (
    CALLBACK_SHA, MAX_BINDINGS, MAX_JOURNAL, MAX_TOTAL, MODULE_SHA, POLICY, SERVER_SHA,
    sha, validate_body_scope, verify_player_body_output,
)
from .telemetry_auth import private_read

STORAGE_BOUND = 2 * (MAX_TOTAL + MAX_BINDINGS + MAX_JOURNAL) + 2 * 1024**2


class BodyObserverLaunch(Strict):
    schema_: Literal["strata/PrivateBodyObserverLaunch/1"] = Field(alias="schema")
    module: PrivateFile
    campaign_id: str
    epoch: int
    run_id: str
    roster: list[str] = Field(min_length=1, max_length=64)


class HeldBodyObserver:
    def __init__(self, writer, value):
        writer.check()
        self.writer = writer
        self.plan = plan = BodyObserverLaunch.model_validate(value)
        self.scope = {key: getattr(plan, key) for key in ("campaign_id", "epoch", "run_id")}
        validate_body_scope(self.scope, plan.roster, "0" * 64, 1)
        require(plan.module.sha256 == MODULE_SHA and 0 < plan.module.bytes <= 1024**2, "BODY_MODULE_PIN")
        source = private_path(plan.module.path)
        workspace, game = safe(writer.workspace.path), safe(writer.tree.path)
        require(not safe(source).is_relative_to(workspace) and not safe(source).is_relative_to(game), "BODY_MODULE_SCOPE")
        check_file(source, plan.module)
        self.server = game / "versions/1.19.2/server-1.19.2.jar"
        self.identity = None
        self.process = None
        self.captured = False
        self.stage = Path(writer.workspace.path) / "body-observer"
        self.output = self.stage / "output"
        self.config = self.stage / "body.properties"
        self.module = self.stage / "observer.jar"
        require(shutil.disk_usage(workspace).free >= STORAGE_BOUND + 5 * 1024**3, "DISK_RESERVE_LOW")
        # Source custody bridges copying into the existing enrolled writer
        # workspace. The writer owns both leases through native cleanup.
        source_lease = FileLease(snapshot([source, self.server], []))
        writer.leases.append(source_lease)
        check_file(source, plan.module)
        require(sha(private_read(self.server, 64 * 1024**2)) == SERVER_SHA, "BODY_SERVER_PIN")
        self.stage.mkdir()
        copy_pinned(source, self.module, plan.module)
        values = self.scope | {"roster": ",".join(plan.roster), "server_jar": launch_path(self.server),
                               "output": launch_path(self.output)}
        require(not any("\n" in str(v) or "\r" in str(v) for v in values.values()), "BODY_CONFIG")
        raw = "".join(f"{key}={value}\n" for key, value in values.items()).encode()
        require(len(raw) <= 16384, "BODY_CONFIG")
        with self.config.open("xb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        self.config_sha = sha(raw)
        self.inventory = snapshot([self.module, self.config], [])
        self.lease = FileLease(self.inventory)
        writer.leases.append(self.lease)
        self.arguments = ["-XX:+DisableAttachMechanism",
                          f"-javaagent:{launch_path(self.module)}={launch_path(self.config)}"]
        self.binding = {"schema": "strata/PrivateBodyObserverBinding/1", "policy": POLICY,
            **self.scope, "roster": list(plan.roster), "module_sha256": MODULE_SHA,
            "callbacks_sha256": CALLBACK_SHA, "server_sha256": SERVER_SHA,
            "configuration_sha256": self.config_sha, "inventory": self.inventory,
            "arguments_prefix": self.arguments, "storage_bound": STORAGE_BOUND,
            "original_pack_profile_unchanged_claim": False, "native_probe_admission": False}
        self.binding["digest"] = digest(self.binding)
        writer.check()

    def observe(self, process, identity):
        """Bind the header only after the parent authenticates a live Java child."""
        require(self.identity is None and process.poll() is None, "BODY_PROCESS_SCOPE")
        pid = identity["pid"]
        require(pid in process.job.members and process.job.member_identity(pid) == identity, "BODY_PROCESS_SCOPE")
        path = safe(self.output / "events.jsonl")
        with path.open("rb") as stream:
            raw = stream.readline(16385)
        require(len(raw) <= 16384 and raw.endswith(b"\n"), "BODY_START_INCOMPLETE")
        record = strict_json(raw)
        require(isinstance(record, dict) and set(record) == {"seq", "elapsed_ns", "body"}
                and type(record["seq"]) is int and record["seq"] == 1
                and type(record["elapsed_ns"]) is int and 0 <= record["elapsed_ns"] <= 9_007_199_254_740_991,
                "BODY_START_INVALID")
        expected = {"schema": "strata/PrivateBodyStart/1", "policy": POLICY, **self.scope,
            "pid": pid, "config_sha256": self.config_sha, "module_sha256": MODULE_SHA,
            "server_sha256": SERVER_SHA, "roster": self.plan.roster}
        require(record["body"] == expected and type(record["body"].get("epoch")) is int
                and type(record["body"].get("pid")) is int, "BODY_PRODUCER_SCOPE")
        callbacks = self.stage / "body-observer-callbacks.jar"
        callback_lease = FileLease(snapshot([callbacks], []))
        self.writer.leases.append(callback_lease)
        require(sha(private_read(callbacks, 262144)) == CALLBACK_SHA, "BODY_CALLBACK_PIN")
        self.lease.recheck()
        self.start_record = record
        self.identity, self.process = dict(identity), process
        self.job, self.member_handle = process.job, process.job.members[pid]

    def check_process_custody(self, process):
        # QueryFullProcessImageNameW may be unavailable after normal exit.
        # Authenticate while alive, then retain the exact Job/member handle;
        # never reopen a PID or treat an absent handle as equivalent evidence.
        require(process is self.process and process.job is self.job
                and bool(self.job.handle)
                and self.job.members.get(self.identity["pid"]) == self.member_handle,
                "BODY_PROCESS_SCOPE")

    def capture_ready(self, process):
        """A private wait barrier only; stopped verification remains mandatory."""
        require(self.identity is not None and process is self.process and process.poll() is None, "BODY_PROCESS_SCOPE")
        self.check_process_custody(process)
        raw = private_read(self.output / "events.jsonl", MAX_JOURNAL)
        if not raw.endswith(b"\n"):
            return False  # A partial write is still the same live attempt.
        lines = raw.splitlines()
        require(1 <= len(lines) <= 3, "BODY_CAPTURE_EARLY_STOP")
        records = [strict_json(line) for line in lines]
        require(records[0] == self.start_record, "BODY_START_CHANGED")
        for index, record in enumerate(records, 1):
            require(isinstance(record, dict) and set(record) == {"seq", "elapsed_ns", "body"}
                    and type(record["seq"]) is int and record["seq"] == index
                    and type(record["elapsed_ns"]) is int and record["elapsed_ns"] >= records[0]["elapsed_ns"],
                    "BODY_JOURNAL_ORDER")
        if len(records) < 3:
            return False
        body = records[2]["body"]
        require(isinstance(body, dict) and body.get("schema") == "strata/PrivateBodyCapture/1"
                and isinstance(body.get("bodies"), list)
                and all(isinstance(member, dict) for member in body["bodies"])
                and [member.get("uuid") for member in body["bodies"]] == self.plan.roster, "BODY_CAPTURE_ROSTER")
        return True

    def capture(self, writer, process, destination):
        """Called after normal process drain, before retained Job handles close."""
        writer.check()
        require(not self.captured and self.identity is not None and process is self.process, "BODY_PROCESS_SCOPE")
        self.check_process_custody(process)
        stopped = VanillaPersistence.terminal_processes(process)
        self.lease.recheck()
        require(sha(private_read(self.stage / "body-observer-callbacks.jar", 262144)) == CALLBACK_SHA, "BODY_CALLBACK_PIN")
        paths = []
        for path in self.output.iterdir():
            require(len(paths) < 66 and path.is_file(), "BODY_OUTPUT_INVENTORY")
            paths.append(path)
        names = sorted(path.name for path in paths)
        require(set(names) == {"events.jsonl", "loaded-classes.txt", *(v + ".nbt" for v in self.plan.roster)},
                "BODY_OUTPUT_INVENTORY")
        require(all(path.stat().st_size <= (MAX_JOURNAL if path.name == "events.jsonl" else
                    MAX_BINDINGS if path.name == "loaded-classes.txt" else 16 * 1024**2) for path in paths),
                "BODY_OUTPUT_QUOTA")
        inputs = snapshot([], [self.output])
        require(sum(entry["bytes"] for entry in inputs["files"]) <= MAX_TOTAL + MAX_BINDINGS + MAX_JOURNAL,
                "BODY_OUTPUT_QUOTA")
        lease = FileLease(inputs)
        writer.leases.append(lease)
        def read(name, limit):
            return private_read(self.output / name, limit)
        report = verify_player_body_output(read, names, server_bytes=private_read(self.server, 64 * 1024**2),
            scope=self.scope, roster=self.plan.roster, config_sha256=self.config_sha, pid=self.identity["pid"])
        destination = private_path(destination)
        require(not safe(destination).is_relative_to(safe(writer.workspace.path))
                and not safe(writer.workspace.path).is_relative_to(safe(destination)), "BODY_EXPORT_SCOPE")
        destination.mkdir()
        for entry in inputs["files"]:
            pin = PrivateFile.model_validate(entry)
            copy_pinned(Path(entry["path"]), destination / Path(entry["path"]).name, pin)
        exported = FileLease(snapshot([], [destination]))
        writer.leases.append(exported)
        require(report == verify_player_body_output(lambda name, limit: private_read(destination / name, limit), names,
            server_bytes=private_read(self.server, 64 * 1024**2), scope=self.scope, roster=self.plan.roster,
            config_sha256=self.config_sha, pid=self.identity["pid"]), "BODY_EXPORT_CHANGED")
        lease.recheck()
        self.check_process_custody(process)
        require(VanillaPersistence.terminal_processes(process) == stopped, "BODY_PROCESS_SCOPE")
        writer.check()
        self.captured = True
        return report | {"owned_producer_verified": True, "owned_jvm": self.identity,
            "owned_processes": stopped, "launch_binding": self.binding, "export": str(destination),
            "source_inventory_sha256": digest(inputs), "export_inventory_sha256": digest(exported.inventory)}
