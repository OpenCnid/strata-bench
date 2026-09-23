"""Fixed private operator roundtrip; no gameplay command or scoring authority."""

import hashlib
import os
from datetime import datetime
from pathlib import Path
import re
import time
from typing import Annotated, Literal

from pydantic import StringConstraints

from mcbench.contracts import Id, Strict
from mcbench.inference_transport import strict_json
from mcbench.storage import digest, reject_links, require

from .craft_reference import Actor
from .setup_history import SetupHistory
from .telemetry_auth import private_read

POLICY = "private-operator-roundtrip/1"
Name = Annotated[str, StringConstraints(pattern=r"^[A-Za-z0-9_]{1,16}$")]


class OperatorControlPlan(Strict):
    policy: Literal["private-operator-roundtrip/1"]
    purpose: Literal["negative_control"]
    agent_id: Id
    actor_uuid: Actor
    player_name: Name
    operator_level: Literal[4]


def saved_operators(path, *, archive=None):
    raw = private_read(Path(path), 1024**2)
    value = strict_json(raw)
    require(isinstance(value, list) and len(value) <= 128, "OPERATOR_CONTROL_FILE")
    # This narrow control admits exactly an empty list or its one expected entry.
    # Validate the entry without coercing level/bypass values or ignoring fields.
    for entry in value:
        require(isinstance(entry, dict) and set(entry) == {"uuid", "name", "level", "bypassesPlayerLimit"}
                and isinstance(entry["uuid"], str) and isinstance(entry["name"], str)
                and type(entry["level"]) is int and 0 <= entry["level"] <= 4
                and type(entry["bypassesPlayerLimit"]) is bool, "OPERATOR_CONTROL_FILE")
    if archive is not None:
        reject_links(Path(archive).absolute())
        with Path(archive).open("xb") as output:
            output.write(raw)
            output.flush()
            os.fsync(output.fileno())
    return {"operators": value, "file_sha256": hashlib.sha256(raw).hexdigest()}


class OperatorControl:
    def __init__(self, plan, setup, authority_root, exposure_s):
        self.plan = plan
        require(setup.roster.get(plan.agent_id) == plan.actor_uuid, "OPERATOR_CONTROL_ROSTER")
        game = Path(setup.game_directory)
        for role, name in (("operator-roster", "ops.json"), ("profile-cache", "usercache.json")):
            pin = setup.supporting_files.get(role)
            require(pin is not None and Path(pin.path) == game / name, "OPERATOR_CONTROL_SOURCE")
        archived = Path(authority_root) / "supporting"
        baseline = saved_operators(archived / digest("operator-roster"))
        require(not baseline["operators"], "OPERATOR_CONTROL_BASELINE")
        cache = strict_json(private_read(archived / digest("profile-cache"), 1024**2))
        require(isinstance(cache, list) and len(cache) <= 128 and all(isinstance(e, dict) for e in cache),
                "OPERATOR_CONTROL_PROFILE_CACHE")
        matches = [e for e in cache if e.get("uuid") == plan.actor_uuid
                   or isinstance(e.get("name"), str) and e["name"].casefold() == plan.player_name.casefold()]
        require(len(matches) == 1 and matches[0].get("name") == plan.player_name
                and matches[0].get("uuid") == plan.actor_uuid, "OPERATOR_CONTROL_PROFILE_CACHE")
        try:
            expires = datetime.strptime(matches[0]["expiresOn"], "%Y-%m-%d %H:%M:%S %z").timestamp()
        except (KeyError, TypeError, ValueError, OverflowError):
            require(False, "OPERATOR_CONTROL_PROFILE_CACHE")
        require(expires > time.time() + exposure_s, "OPERATOR_CONTROL_PROFILE_EXPIRED")
        self.profile_expires = expires
        self.ops = game / "ops.json"
        self.expected = {"uuid": plan.actor_uuid, "name": plan.player_name,
                         "level": plan.operator_level, "bypassesPlayerLimit": False}
        self.commands = ("op " + plan.player_name, "deop " + plan.player_name)
        self.result = {"policy": POLICY, "purpose": "negative_control", "state": "waiting",
                       "target": plan.model_dump(), "baseline_saved": baseline,
                       "commands": list(self.commands), "scoring_eligible": False}
        self.attempted = self.restore_attempted = False
        self.sent_at = None

    def dispatch(self, prefix, process, record, *, deadline, exposure_s, log):
        require(not self.attempted, "OPERATOR_CONTROL_ALREADY_ATTEMPTED")
        require(time.monotonic() + exposure_s <= deadline and
                self.profile_expires > time.time() + deadline - time.monotonic(), "OPERATOR_CONTROL_DEADLINE")
        require(saved_operators(self.ops) == self.result["baseline_saved"], "OPERATOR_CONTROL_BASELINE_CHANGED")
        self.attempted = True
        self.result.update(state="dispatching", startup_prefix=prefix, intent_unix=time.time(),
                           log_offset=Path(log).stat().st_size)
        record()
        process.send_input(self.commands[0] + "\n")
        self.result.update(state="awaiting_saved_effect", sent_unix=time.time())
        record()

    def feedback(self, raw):
        # English messages come from the pinned 1.19.2 language resource.
        name = re.escape(self.plan.player_name.encode("ascii"))
        return re.findall(rb"(?m)^.*Made " + name + rb" (a server operator|no longer a server operator)\r?$", raw)

    def advance(self, process, record, *, world, log, deadline, exposure_s):
        require(self.result["state"] == "awaiting_saved_effect" and not self.restore_attempted,
                "OPERATOR_CONTROL_RESTORE_ALREADY_ATTEMPTED")
        raw = private_read(Path(log), 64 * 1024**2)[self.result["log_offset"]:]
        feedback = self.feedback(raw)
        if not feedback:
            return False
        require(feedback == [b"a server operator"], "OPERATOR_CONTROL_FEEDBACK")
        intermediate = saved_operators(self.ops, archive=Path(log).parent / "operator-control.intermediate-ops.json")
        require(intermediate["operators"] == [self.expected], "OPERATOR_CONTROL_INTERMEDIATE_UNPROVEN")
        require(time.monotonic() + exposure_s <= deadline, "OPERATOR_CONTROL_DEADLINE")
        self.restore_attempted = True
        self.result.update(state="restore_dispatching", intermediate_saved=intermediate,
                           intermediate_observed_unix=time.time(), intermediate_log_bytes=len(raw),
                           intermediate_log_sha256=hashlib.sha256(raw).hexdigest())
        record()
        process.send_input(self.commands[1] + "\n")
        self.sent_at = time.monotonic()
        self.result.update(state="sent", restore_sent_unix=time.time())
        record()
        return True

    def finish(self, inspection, world, log):
        require(self.result["state"] == "sent", "OPERATOR_CONTROL_INCOMPLETE")
        prefix = self.result["startup_prefix"]
        require(all(inspection[key] == prefix[key] for key in ("campaign_id", "epoch", "server_boot_id"))
                and inspection["setup_startup"] == prefix["startup"]
                and inspection["launch_identity"] == prefix["launch_identity"], "OPERATOR_CONTROL_INSPECTION_SCOPE")
        history = inspection.get("setup_history", {})
        terminal = SetupHistory.model_validate(history.get("terminal", {}))
        expected = dict.fromkeys(terminal.attempts, 0)
        expected.update(command_attempt=3, native_stop_command=1, operator_add=1, operator_remove=1)
        require(history.get("policy") == terminal.policy and terminal.phase == "stop"
                and terminal.attempts == expected and not terminal.off_thread_attempts and not terminal.overflowed
                and not history["observed_history_clear"]
                and set(history["reasons"]) == {"observed:" + k for k, v in expected.items() if v}
                and not inspection["avatar_ticks_at_last_sample"] and not inspection["craft_witnesses"],
                "OPERATOR_CONTROL_HISTORY_MISMATCH")
        raw = private_read(Path(log), 64 * 1024**2)[self.result["log_offset"]:]
        require(self.feedback(raw) == [b"a server operator", b"no longer a server operator"],
                "OPERATOR_CONTROL_FEEDBACK")
        require(hashlib.sha256(raw[:self.result["intermediate_log_bytes"]]).hexdigest() ==
                self.result["intermediate_log_sha256"], "OPERATOR_CONTROL_LOG_CHANGED")
        retained = saved_operators(Path(log).parent / "operator-control.intermediate-ops.json")
        require(retained == self.result["intermediate_saved"] and retained["operators"] == [self.expected],
                "OPERATOR_CONTROL_INTERMEDIATE_CHANGED")
        final = saved_operators(self.ops, archive=Path(log).parent / "operator-control.final-ops.json")
        require(not final["operators"], "OPERATOR_CONTROL_RESTORE_UNPROVEN")
        self.result.update(state="completed_negative_control", terminal_history=history, final_saved=final,
                           log_sha256=hashlib.sha256(raw).hexdigest(), native_mutation_observed=True,
                           intermediate_operator_verified=True, final_roster_matches_baseline=True,
                           full_setup_history_qualified=False)
        return self.result
