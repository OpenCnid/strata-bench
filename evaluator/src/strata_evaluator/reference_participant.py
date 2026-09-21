"""Private operator coordination only; receipts do not certify client execution."""

import hashlib
import os
from pathlib import Path
import secrets
import time
from typing import Literal

from pydantic import Field

from mcbench.contracts import Digest, Id, Positive, Strict
from mcbench.inference_transport import strict_json
from mcbench.launch_integrity import FileLease
from mcbench.storage import Fault, digest, require

from .craft_reference import private_path, write_new
from .telemetry_auth import private_read

REPORT_LIMIT = 8 * 1024**2


class ParticipantPlan(Strict):
    participant_id: Id
    window_s: int = Field(ge=1, le=420)
    report_path: str


class ParticipantReady(Strict):
    schema_: Literal["strata/ReferenceParticipantReady/1"] = Field(alias="schema")
    instance_id: Id
    setup_digest: Digest
    launch_plan_digest: Digest
    server_boot_id: Id
    participant_id: Id
    challenge: Digest
    window_ms: Positive
    # Advisory for the external operator driver. Launcher admission uses monotonic time.
    expires_unix_ms: Positive


class ParticipantCompletion(Strict):
    schema_: Literal["strata/ReferenceParticipantCompletion/1"] = Field(alias="schema")
    participant_id: Id
    readiness_digest: Digest
    outcome: Literal["completed", "failed"]
    report_sha256: Digest
    report_bytes: int = Field(ge=2, le=REPORT_LIMIT)


def publish(path, value):
    """Publish a complete file once, without replacement, on the Windows profile."""
    require(os.name == "nt", "REFERENCE_PLATFORM_UNQUALIFIED")
    path = private_path(path)
    temporary = path.with_name(path.name + "." + secrets.token_hex(16) + ".pending")
    write_new(temporary, value)
    # Windows rename rejects an existing destination. A failed publication retains
    # its private pending file; callers must not infer permission to retry a run.
    temporary.rename(path)


def validate_paths(plan, evidence, game, authority_directory):
    report = private_path(plan.report_path)
    require(not report.exists() and report.parent.is_dir()
            and all(not report.is_relative_to(root) and not root.is_relative_to(report)
                    for root in (evidence, game, authority_directory)), "REFERENCE_PARTICIPANT_PATH")
    return report


def submit_completion(evidence, ready, report_path, outcome):
    """Operator driver calls this only after its report is durably closed."""
    ready = ParticipantReady.model_validate(ready)
    raw = private_read(report_path, REPORT_LIMIT)
    strict_json(raw)
    value = ParticipantCompletion.model_validate({
        "schema": "strata/ReferenceParticipantCompletion/1", "participant_id": ready.participant_id,
        "readiness_digest": digest(ready.model_dump(by_alias=True)), "outcome": outcome,
        "report_sha256": hashlib.sha256(raw).hexdigest(), "report_bytes": len(raw)})
    publish(Path(evidence) / "participant-completion.json", value.model_dump(by_alias=True))


class ParticipantWindow:
    def __init__(self, plan, evidence, launch, boot, now, wall, server_deadline, clock=time.monotonic):
        require(now + plan.window_s <= server_deadline, "REFERENCE_PARTICIPANT_EXPOSURE")
        self.plan, self.evidence = plan, evidence
        self.deadline = now + plan.window_s
        self.clock = clock
        self.lease = None
        self.result = {"status": "pending", "participant_execution_verified": False}
        self.ready = ParticipantReady.model_validate({
            "schema": "strata/ReferenceParticipantReady/1", "instance_id": launch.instance_id,
            "setup_digest": launch.setup_digest, "launch_plan_digest": digest(launch.model_dump(by_alias=True)),
            "server_boot_id": boot, "participant_id": plan.participant_id, "challenge": secrets.token_hex(32),
            "window_ms": plan.window_s * 1000, "expires_unix_ms": int((wall + plan.window_s) * 1000)})

    def publish(self):
        publish(self.evidence / "participant-ready.json", self.ready.model_dump(by_alias=True))

    def poll(self, now):
        if self.result["status"] != "pending":
            return True
        try:
            require(now < self.deadline, "REFERENCE_PARTICIPANT_TIMEOUT")
            path = self.evidence / "participant-completion.json"
            if not path.exists():
                return False
            receipt_raw = private_read(path, 8192)
            receipt = ParticipantCompletion.model_validate(strict_json(receipt_raw))
            require(receipt.participant_id == self.plan.participant_id
                    and receipt.readiness_digest == digest(self.ready.model_dump(by_alias=True)),
                    "REFERENCE_PARTICIPANT_SCOPE")
            report = Path(self.plan.report_path)
            raw = private_read(report, REPORT_LIMIT)
            require(len(raw) == receipt.report_bytes and hashlib.sha256(raw).hexdigest() == receipt.report_sha256,
                    "REFERENCE_PARTICIPANT_REPORT")
            # Deny writes through completion/stop, and preserve the exact report bytes.
            self.lease = FileLease({"schema": "strata/LaunchFileInventory/1", "trees": [], "files": [
                {"path": str(file), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
                for file, data in ((path, receipt_raw), (report, raw))]})
            strict_json(raw)
            with (self.evidence / "participant-report.json").open("xb") as output:
                output.write(raw)
                output.flush()
                os.fsync(output.fileno())
            self.lease.recheck()
            require(self.clock() < self.deadline, "REFERENCE_PARTICIPANT_TIMEOUT")
            self.result.update(status=receipt.outcome, receipt=receipt.model_dump(by_alias=True))
            require(receipt.outcome == "completed", "REFERENCE_PARTICIPANT_FAILED")
        except Exception as error:
            self.result.update(status="uncertain", error=error.code if isinstance(error, Fault) else type(error).__name__)
        return True

    def finish(self):
        require(self.result["status"] == "completed", self.result.get("error", "REFERENCE_PARTICIPANT_MISSING"))
        self.lease.recheck()

    def close(self):
        if self.lease:
            self.lease.close()
