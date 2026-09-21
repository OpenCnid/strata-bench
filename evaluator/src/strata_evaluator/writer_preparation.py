"""One-use private Java preparation through the pinned native Windows sandbox.

This candidate must prove held process ownership before copying any bytes into
the protected root. It never grants scoring, full isolation or crash recovery.
"""

import base64
import argparse
import json
import os
from pathlib import Path
import secrets
import sys
import time
from typing import Literal

from pydantic import Field, model_validator

from mcbench.contracts import Id, Strict
from mcbench.inference_transport import strict_json
from mcbench.launch_integrity import FileLease, snapshot
from mcbench.native import _toml_value
from mcbench.processes import ManagedProcess, ProcessInventoryFault
from mcbench.storage import canonical, digest, require, safe_relative

from .craft_reference import PrivateFile, check_file, check_tree, private_path, write_new
from .reference_pair import OwnedCli
from .telemetry_auth import private_read
from .windows_writer import OperatorWorkspace, WindowsSecurity, WriterTree

CODEX_SHA256 = "960c111d47afd61669954b9df9e56083e302edbfa3ef6962d81dcc14a30051dc"


class WriterPreparationPlan(Strict):
    schema_: Literal["strata/PrivateWriterPreparationPlan/1"] = Field(alias="schema")
    id: Id
    evidence_kind: Literal["synthetic", "authentic_operator_reference"]
    codex: PrivateFile
    java: PrivateFile
    helper_class: PrivateFile
    sandbox_home: str
    writer_sid: str
    source_root: str
    workspace_directory: str
    sources: dict[str, PrivateFile] = Field(min_length=1, max_length=12000)
    evidence_directory: str
    max_wall_s: int = Field(ge=25, le=60)

    @model_validator(mode="after")
    def scope(self):
        require(self.codex.sha256 == CODEX_SHA256, "WRITER_RUNTIME_PIN")
        require(Path(self.java.path).name.lower() == "java.exe"
                and Path(self.helper_class.path).name == "StrataWriterPreparation.class",
                "WRITER_HELPER_PROFILE")
        source = private_path(self.source_root)
        evidence = private_path(self.evidence_directory)
        workspace = private_path(self.workspace_directory)
        require(not source.is_relative_to(evidence) and not evidence.is_relative_to(source),
                "WRITER_SOURCE_SCOPE")
        require(all(not workspace.is_relative_to(other) and not other.is_relative_to(workspace)
                    for other in (source, evidence)), "WRITER_WORKSPACE_SCOPE")
        seen, total = set(), 0
        for relative, pin in self.sources.items():
            safe_relative(relative)
            require(relative.casefold() not in seen
                    and private_path(pin.path).is_relative_to(source)
                    and pin.bytes <= 512 * 1024**2, "WRITER_SOURCE_SCOPE")
            seen.add(relative.casefold())
            total += pin.bytes
        require(total <= 1024**3, "WRITER_BYTE_QUOTA")
        return self


def native_argv(plan, workspace, command):
    settings = {"windows.sandbox": "elevated", "default_permissions": "strata-writer-preparation",
        "permissions.strata-writer-preparation.filesystem": {":root": "deny", ":minimal": "read",
            ":workspace_roots": {".": "write"}, str(Path(plan.java.path).parent.parent): "read"},
        "permissions.strata-writer-preparation.network.enabled": False}
    argv = [plan.codex.path, "sandbox", "--include-managed-config", "--permission-profile",
            "strata-writer-preparation", "--cd", str(workspace)]
    for key, value in sorted(settings.items()):
        argv.extend(["-c", key + "=" + _toml_value(value)])
    return [*argv, "--", *command]


def grant(path, challenge):
    pending = path.with_name(path.name + ".pending")
    with pending.open("xb") as file:
        file.write(challenge.encode("ascii"))
        file.flush()
        os.fsync(file.fileno())
    pending.rename(path)  # Windows: complete publication, no replacement.


def java_identity(value, challenge, root, java, job):
    require(type(value) is dict and set(value) == {"schema", "challenge", "pid",
            "process_started_unix_ms", "executable", "requested_root"}
            and value["schema"] == "strata/WriterJavaIdentity/2"
            and value["challenge"] == challenge and type(value["pid"]) is int
            and value["pid"] > 0 and type(value["process_started_unix_ms"]) is int,
            "WRITER_JAVA_IDENTITY")
    # A Java receipt is not authority. The PID must already be retained as a
    # member of the exact held Job; never search arbitrary processes by name.
    actual = job.member_identity(value["pid"])
    require(actual["pid"] == value["pid"]
            and actual["process_started_unix_ms"] == value["process_started_unix_ms"]
            and Path(actual["executable"]).resolve() == Path(value["executable"]).resolve()
            and Path(actual["executable"]).resolve() == Path(java).resolve()
            and Path(value["requested_root"]).resolve() == root.resolve(), "WRITER_JAVA_IDENTITY")
    return actual


class WriterPreparations:
    def __init__(self, database):
        private_path(database.path)
        self.database = database
        with database.transaction() as db:
            db.execute("CREATE TABLE IF NOT EXISTS writer_preparations (id TEXT PRIMARY KEY, "
                       "evidence TEXT UNIQUE NOT NULL, plan TEXT NOT NULL, state TEXT NOT NULL, body TEXT NOT NULL)")

    def record(self, id, state, body):
        with self.database.transaction() as db:
            db.execute("UPDATE writer_preparations SET state=?,body=? WHERE id=?",
                       (state, canonical(body).decode(), id))
            self.database.event(db, "private.writer_preparation", {"id": id, "state": state, **body})

    def run(self, value):
        plan = WriterPreparationPlan.model_validate(value)
        value = plan.model_dump(by_alias=True)
        require(os.name == "nt", "WRITER_PLATFORM_UNSUPPORTED")
        require(plan.evidence_kind == "synthetic", "WRITER_PROFILE_UNQUALIFIED")
        evidence = private_path(plan.evidence_directory)
        workspace = private_path(plan.workspace_directory)
        require(not evidence.exists() and not workspace.exists(), "WRITER_OUTPUT_EXISTS")
        marker = json.loads(private_read(Path(plan.sandbox_home) / ".sandbox/setup_marker.json", 65536))
        require(marker.get("version") == 5, "SANDBOX_ENROLLMENT_REQUIRED")
        pins = [plan.codex, plan.java, plan.helper_class, *plan.sources.values()]
        for pin in pins:
            check_file(Path(pin.path), pin)
        body = {"schema": "strata/PrivateWriterPreparationResult/1", "plan_digest": digest(value),
                "evidence_kind": plan.evidence_kind,
                "capability": "native-private-java-preparation/1",
                "status": "intent", "setup_authority_qualified": False, "scoring_eligible": False,
                "model_calls": 0, "game_launched": False, "stages": {}}
        with self.database.transaction() as db:
            require(db.execute("SELECT 1 FROM writer_preparations WHERE id=? OR evidence=?",
                    (plan.id, str(evidence))).fetchone() is None, "WRITER_ALREADY_RESERVED")
            db.execute("INSERT INTO writer_preparations VALUES(?,?,?,?,?)",
                       (plan.id, str(evidence), canonical(value).decode(), "INTENT", canonical(body).decode()))
            self.database.event(db, "private.writer_preparation", {"id": plan.id, **body})
        lease, tree, active, workspace_lease = None, None, None, None
        staged_leases = []
        until = time.monotonic() + plan.max_wall_s
        try:
            evidence.mkdir()
            workspace_lease = OperatorWorkspace(workspace)
            write_new(evidence / "plan.json", value)
            # Pin every input plus the actual Java runtime and bootstrap.
            bootstrap = Path(__file__).resolve().parents[3] / "src/mcbench/process_bootstrap.py"
            lease = FileLease(snapshot([*(pin.path for pin in pins), sys.executable, bootstrap],
                                       [str(Path(plan.java.path).parent.parent)]))
            # Close the interval between initial pin validation and acquisition
            # of the deny-write handles; persist the whole runtime inventory.
            for pin in pins:
                check_file(Path(pin.path), pin)
            write_new(evidence / "input-inventory.json", lease.inventory)
            body["input_inventory_digest"] = digest(lease.inventory)
            control, classes, staging = (workspace / name for name in ("control", "classes", "staging"))
            for directory in (control, classes, staging):
                directory.mkdir()
            (workspace / "tmp").mkdir()
            (classes / "StrataWriterPreparation.class").write_bytes(Path(plan.helper_class.path).read_bytes())
            check_file(classes / "StrataWriterPreparation.class", plan.helper_class)
            lines = []
            for number, (relative, pin) in enumerate(sorted(plan.sources.items())):
                staged = staging / str(number)
                # Copy while original file handles deny writes/replacement.
                with Path(pin.path).open("rb") as source, staged.open("xb") as target:
                    while chunk := source.read(65536):
                        require(time.monotonic() < until, "WRITER_STAGING_TIMEOUT")
                        target.write(chunk)
                    target.flush()
                    os.fsync(target.fileno())
                check_file(staged, pin)
                lines.append("\t".join([base64.b64encode(relative.encode()).decode(),
                    base64.b64encode(str(staged).encode()).decode(), pin.sha256, str(pin.bytes)]))
            manifest = "\n".join(lines).encode("utf-8")
            require(len(manifest) <= 8 * 1024**2, "WRITER_MANIFEST_QUOTA")
            (control / "files.tsv").write_bytes(manifest)
            environment = {key: os.environ[key] for key in ("SystemRoot", "WINDIR") if key in os.environ}
            environment["CODEX_HOME"] = plan.sandbox_home
            def start(stage, command, deadline):
                logs = evidence / stage
                logs.mkdir()
                self.record(plan.id, stage.upper(), body | {"status": stage})
                process = ManagedProcess(native_argv(plan, workspace, command), workspace, environment, "")
                return OwnedCli(process, "server", logs, deadline)

            # Lease staged helper/manifest/input bytes before native enrollment.
            # Never let the writer replace its own preparation program.
            staged_leases.append(FileLease(snapshot([], [str(classes), str(staging)])))
            staged_leases.append(FileLease(snapshot([str(control / "files.tsv")], [])))
            require(until - time.monotonic() >= 22, "WRITER_EXPOSURE_INSUFFICIENT")
            challenge = secrets.token_hex(32)
            body["challenge"] = challenge
            command = [plan.java.path, "-Xms16m", "-Xmx128m", "-XX:-UsePerfData",
                "-Djava.io.tmpdir=" + str(workspace / "tmp"), "-cp", str(classes),
                "StrataWriterPreparation", str(workspace / "guarded"), str(control), challenge]
            active = start("preparation", command, min(until, time.monotonic() + 22))
            while not (control / "identity.json").exists():
                require(active.observe() is None, "WRITER_JAVA_EARLY_EXIT")
                time.sleep(0.025)
            active.observe()
            security = WindowsSecurity()
            group, scope = security.workspace_scope(workspace)
            workspace_lease.verify_enrolled(group, scope)
            body["java_identity"] = java_identity(strict_json(private_read(control / "identity.json", 8192)),
                challenge, workspace / "guarded", plan.java.path, active.process.job)
            body["writer_token"] = security.bind_process(
                active.process.job.members[body["java_identity"]["pid"]], plan.writer_sid, group, scope)
            tree = WriterTree(workspace / "guarded", plan.writer_sid, group, scope)
            body.update(writer_sid=plan.writer_sid, group_sid=group, scope_sid=scope, root=str(tree.path))
            self.record(plan.id, "BOUND", body | {"status": "bound"})
            for held_lease in staged_leases:
                held_lease.recheck()
            lease.recheck()
            grant(control / "prepare.grant", challenge)
            while not (control / "copied.json").exists():
                require(active.observe() is None, "WRITER_JAVA_EARLY_EXIT")
                time.sleep(0.025)
            copied = strict_json(private_read(control / "copied.json", 8192))
            require(copied == {"schema": "strata/WriterJavaCopied/2", "challenge": challenge,
                "files": len(plan.sources), "bytes": sum(pin.bytes for pin in plan.sources.values()),
                "root": str(tree.path)},
                "WRITER_COPY_RECEIPT")
            tree.verify()
            check_tree(tree.path, plan.sources)
            for path in tree.path.rglob("*"):
                tree.security.verify(path, plan.writer_sid, group, scope, directory=path.is_dir())
            for held_lease in staged_leases:
                held_lease.recheck()
            body["copied"] = copied
            self.record(plan.id, "COPIED", body | {"status": "copied"})
            grant(control / "finish.grant", challenge)
            while active.observe() is None:
                time.sleep(0.025)
            body["stages"]["preparation"] = active.finish()
            active = None
            final = body["stages"]["preparation"]
            require(final["terminal_verified"] and final["logs_complete"]
                    and final["exit_code"] == 0 and not final["forced"], "WRITER_TERMINAL_UNCERTAIN")
            workspace_lease.verify_enrolled(group, scope)
            tree.verify()
            lease.recheck()
            body["status"] = "prepared_reference"
            self.record(plan.id, "STOPPED", body)
        except BaseException as error:
            body.update(status="uncertain", error=getattr(error, "code", type(error).__name__))
            if isinstance(error, ProcessInventoryFault):
                body["process_observation"] = error.observation()
            self.record(plan.id, "UNCERTAIN", body)  # First failure precedes cleanup.
            if active is not None:
                active.shorten(time.monotonic())
                body["cleanup"] = active.finish()
                self.record(plan.id, "UNCERTAIN", body)
        finally:
            for staged_lease in reversed(staged_leases):
                staged_lease.close()
            if tree is not None:
                tree.close()
            if lease is not None:
                lease.close()
            if workspace_lease is not None:
                workspace_lease.close()
            if evidence.exists():
                write_new(evidence / "result.json", body)
        return body


def main():
    from mcbench.storage import Database
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--plan", type=Path, required=True)
    args = parser.parse_args()
    value = strict_json(private_read(private_path(args.plan), 32 * 1024**2))
    database = Database(private_path(args.database))
    try:
        result = WriterPreparations(database).run(value)
        print(json.dumps({"status": result["status"], "error": result.get("error"),
                          "setup_authority_qualified": False, "scoring_eligible": False}))
        return 0 if result["status"] == "prepared_reference" else 1
    finally:
        database.connection.close()


if __name__ == "__main__":
    raise SystemExit(main())
