"""Live, one-use preparation-to-native-launch custody; never reconstruct from JSON."""

import base64
from contextlib import ExitStack
import os
from pathlib import Path
import secrets
import threading
import time
from typing import Literal

from pydantic import Field

from mcbench.contracts import Strict
from mcbench.inference_transport import strict_json
from mcbench.launch_integrity import FileLease, snapshot
from mcbench.processes import ManagedProcess
from mcbench.storage import digest, require
from .craft_reference import PrivateFile, check_file, write_new
from .reference_pair import OwnedCli
from .telemetry_auth import private_read
from .writer_preparation import grant, java_identity, native_argv


class WriterLaunchPlan(Strict):
    schema_: Literal["strata/PrivateWriterLaunch/1"] = Field(alias="schema")
    # This first custody profile cannot authorize an authentic game or model.
    mode: Literal["synthetic-fixture"]
    helper_class: PrivateFile
    immutable_files: list[PrivateFile] = Field(min_length=1, max_length=12000)
    immutable_trees: list[str] = Field(max_length=16)
    arguments: list[str] = Field(min_length=1, max_length=63)
    max_wall_s: int = Field(ge=15, le=30)


class WriterCustody:
    """Borrowed only inside WriterPreparations.run's operator continuation.

    Owns the launched process, broker and added leases. Preparation retains the
    same tree/workspace/input handles until close finishes on every path.
    Serialized lifecycle operations ensure there is exactly one Job observer.
    """

    def __init__(self, plan, tree, workspace, inputs, deadline, body, record):
        self.plan, self.tree, self.workspace, self.inputs = plan, tree, workspace, inputs
        self.deadline, self.body, self.record = deadline, body, record
        self.thread = threading.get_ident()
        self.closed, self.launched = False, False
        self.completed = False
        self.native, self.broker, self.leases = None, None, []
        self.result = {"capability": "native-private-java-custody/1", "status": "held",
                       "live": True, "scoring_eligible": False, "setup_authority_qualified": False}
        body["custody"] = self.result

    def check(self):
        require(not self.closed and threading.get_ident() == self.thread, "WRITER_CUSTODY_CLOSED")
        require(time.monotonic() < self.deadline, "WRITER_CUSTODY_DEADLINE")
        self.workspace.verify_enrolled(self.tree.group_sid, self.tree.scope_sid)
        self.tree.verify()
        for lease in [*self.inputs, *self.leases]:
            lease.recheck()

    def _record(self, state, **changes):
        self.result.update(status=state.lower(), **changes)
        self.body["status"] = "custody_" + state.lower()
        self.record(self.plan.id, "CUSTODY_" + state, self.body)

    def launch(self, value, broker):
        self.check()
        require(not self.launched, "WRITER_CUSTODY_ALREADY_LAUNCHED")
        # Take responsibility for closing the endpoint even if validation fails.
        self.launched, self.broker = True, broker
        plan = WriterLaunchPlan.model_validate(value)
        require(Path(plan.helper_class.path).name == "StrataWriterLaunch.class", "WRITER_LAUNCH_HELPER")
        require(Path(broker.setup.game_directory).resolve() == self.tree.path.resolve()
                and Path(broker.plan.executable.path).resolve() == Path(self.plan.java.path).resolve()
                and (broker.writer_sid, broker.group_sid, broker.scope_sid) ==
                    (self.plan.writer_sid, self.tree.group_sid, self.tree.scope_sid)
                and broker.deadline <= self.deadline, "WRITER_LAUNCH_BROKER_SCOPE")
        # The trusted operator supplies exact Java arguments. They are never
        # interpreted by a shell; this profile admits only the compiled fixture.
        require(len(plan.arguments) == 8 and plan.arguments[0] == "-cp"
                and plan.arguments[2] == "io.github.opencnid.strata.telemetry.OwnedLaunchFixture"
                and all("\0" not in arg for arg in plan.arguments)
                and sum(len(arg) for arg in plan.arguments) < 24000, "WRITER_LAUNCH_PROFILE")
        descriptor = Path(plan.arguments[3]).resolve()
        require(all(Path(path).is_absolute() for path in
                    [*plan.arguments[1].split(os.pathsep), *plan.arguments[3:6]])
                and descriptor.is_relative_to(self.workspace.path / "control")
                and Path(plan.arguments[4]).resolve() == self.tree.path.resolve()
                and Path(plan.arguments[5]).resolve() == Path(broker.plan.module_file.path).resolve()
                and plan.arguments[6] == str(broker.plan.server_port)
                and plan.arguments[7] in ("normal", "missing-stop", "early-exit", "hang"),
                "WRITER_LAUNCH_PROFILE")
        required = {descriptor, Path(plan.arguments[5]).resolve(),
                    *(Path(path).resolve() for path in plan.arguments[1].split(os.pathsep))}
        pinned = {Path(pin.path).resolve() for pin in plan.immutable_files}
        trees = {Path(path).resolve() for path in plan.immutable_trees}
        require(required <= pinned | trees, "WRITER_LAUNCH_UNPINNED")
        require(self.deadline - time.monotonic() >= plan.max_wall_s, "WRITER_EXPOSURE_INSUFFICIENT")
        pins = [plan.helper_class, *plan.immutable_files]
        for pin in pins:
            check_file(Path(pin.path), pin)
        require(strict_json(private_read(descriptor, 4096)) == broker.descriptor, "WRITER_LAUNCH_DESCRIPTOR")
        inventory = snapshot([pin.path for pin in pins], plan.immutable_trees)
        self.leases.append(FileLease(inventory))
        for pin in pins:
            check_file(Path(pin.path), pin)
        self._record("INTENT", launch_plan_digest=digest(plan.model_dump(by_alias=True)),
                     input_inventory_digest=digest(inventory))
        evidence = Path(self.plan.evidence_directory) / "launch"
        evidence.mkdir()
        write_new(evidence / "plan.json", plan.model_dump(by_alias=True))
        write_new(evidence / "inventory.json", inventory)
        control = self.workspace.path / "control"
        classes = self.workspace.path / "launch-classes"
        classes.mkdir()
        staged_helper = classes / "StrataWriterLaunch.class"
        staged_helper.write_bytes(Path(plan.helper_class.path).read_bytes())
        check_file(staged_helper, plan.helper_class)
        command = [self.plan.java.path, "-Xms16m", "-Xmx128m", "-XX:-UsePerfData",
            "-Djava.io.tmpdir=" + str(self.workspace.path / "tmp"),
            "-Djna.tmpdir=" + str(self.workspace.path / "tmp"), *plan.arguments]
        command_file = control / "launch-command.tsv"
        with command_file.open("xb") as stream:
            stream.write(b"\n".join(base64.b64encode(arg.encode("utf-8")) for arg in command))
            stream.flush()
            os.fsync(stream.fileno())
        self.leases.append(FileLease(snapshot([str(command_file)], [str(classes)])))
        self.check()
        challenge = secrets.token_hex(32)
        environment = {name: os.environ[name] for name in ("SystemRoot", "WINDIR") if name in os.environ}
        environment["CODEX_HOME"] = self.plan.sandbox_home
        gate = [self.plan.java.path, "-Xms16m", "-Xmx128m", "-XX:-UsePerfData",
            "-Djava.io.tmpdir=" + str(self.workspace.path / "tmp"), "-cp", str(classes),
            "StrataWriterLaunch", str(self.tree.path), str(control), challenge]
        self._record("DISPATCHING", challenge=challenge)
        require(self.deadline - time.monotonic() >= plan.max_wall_s, "WRITER_EXPOSURE_INSUFFICIENT")
        process = ManagedProcess(native_argv(self.plan, self.workspace.path, gate), self.workspace.path,
                                 environment, "", interactive=True)
        try:
            self.native = OwnedCli(process, "server", evidence,
                                   min(self.deadline, time.monotonic() + plan.max_wall_s))
        except BaseException:
            process.close()  # Retained Job backstop if monitor installation itself fails.
            raise
        broker.bind(process.job)
        identity_file = control / "launch-identity.json"
        while not identity_file.exists():
            require(self.native.observe() is None, "WRITER_LAUNCH_EARLY_EXIT")
            time.sleep(0.025)
        self.native.observe()
        identity = java_identity(strict_json(private_read(identity_file, 8192)), challenge,
                                 self.tree.path, self.plan.java.path, process.job)
        token = self.tree.security.bind_process(process.job.members[identity["pid"]],
                            self.plan.writer_sid, self.tree.group_sid, self.tree.scope_sid)
        self.check()
        self._record("ADMITTED", gate_identity=identity, gate_token=token)
        grant(control / "launch.grant", challenge)
        return self.native

    def finish(self):
        self.check()
        require(self.launched and self.native is not None, "WRITER_CUSTODY_LAUNCH_MISSING")
        require(self.native.observe() is not None, "WRITER_CUSTODY_UNFINISHED")
        native, self.native = self.native, None
        terminal = native.finish()
        self.result["terminal"] = terminal
        self.result["broker"] = self.broker.close()
        require(terminal["terminal_verified"] and terminal["logs_complete"]
                and terminal["exit_code"] == 0 and not terminal["forced"]
                and self.result["broker"]["status"] == "stopped", "WRITER_CUSTODY_TERMINAL_UNCERTAIN")
        self.check()
        self._record("STOPPED")
        self.completed = True
        return dict(self.result)

    def close(self):
        if self.closed:
            return
        self.closed = True  # Invalidate first, before any cleanup can fail.
        self.result["live"] = False
        if not self.completed:
            self.result["status"] = "uncertain"
        try:
            if self.native is not None:
                self.native.shorten(time.monotonic())
                self.result["cleanup"] = self.native.finish()
                self.native = None
        finally:
            try:
                if self.broker is not None:
                    self.result["broker"] = self.broker.close()
            finally:
                with ExitStack() as cleanup:
                    for lease in self.leases:
                        cleanup.callback(lease.close)
