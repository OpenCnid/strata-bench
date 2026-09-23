"""One fixed private negative control, never an agent/admin command interface."""

import hashlib
import os
from pathlib import Path
import re
import time
from typing import Literal

from mcbench.contracts import Strict
from mcbench.inference_transport import strict_json
from mcbench.records import GameEvent
from mcbench.storage import digest, reject_links, require

from .saved_blocks import NbtReader, field, unpack_chunk
from .setup_facts import ManagerReady, PackMode, SetupSnapshot
from .setup_history import HISTORY_SCHEMAS, parse_history
from .telemetry import RecipeSnapshot, LAUNCH_STARTUP_MODELS, ServerStartedV10, ServerStartedV11, ServerStartedV12
from .telemetry_auth import MAX_WIRE_RECORD, SpoolVerifier, private_read

POLICY = "private-world-mode-roundtrip/1"
# Fixed reviewed commands, no caller-provided text, player names or substitutions.
COMMANDS = ("defaultgamemode creative", "save-all flush", "defaultgamemode survival")


class SetupControlPlan(Strict):
    policy: Literal["private-world-mode-roundtrip/1"]
    purpose: Literal["negative_control"]


def saved_mode(path, *, archive=None):
    raw = private_read(Path(path), 4 * 1024**2)
    data = field(NbtReader(unpack_chunk(raw, 1)).root(), "Data", 10)
    result = {"mode": field(data, "GameType", 3), "file_sha256": hashlib.sha256(raw).hexdigest()}
    if archive is not None:
        reject_links(Path(archive).absolute())
        with Path(archive).open("xb") as output:
            output.write(raw)
            output.flush()
            os.fsync(output.fileno())
    return result


def startup_prefix(directory, authority, expected_boot):
    """Authenticate a bounded complete startup prefix; an unfinished write waits."""
    files = list(Path(directory).glob("*.authenticated.jsonl"))
    require(len(files) <= 1, "SETUP_CONTROL_MULTIPLE_SPOOLS")
    if not files:
        return None
    reject_links(files[0].absolute())
    require(files[0].is_file() and files[0].stat().st_nlink == 1
            and files[0].stat().st_size <= 8 * 1024**2, "SETUP_CONTROL_PREFIX_QUOTA")
    previous_tick, history, boot = 0, None, None
    total = 0
    with files[0].open("rb") as stream, SpoolVerifier(authority) as verifier:
        for seq in range(1, 65):
            wire = stream.readline(MAX_WIRE_RECORD + 1)
            total += len(wire)
            require(len(wire) <= MAX_WIRE_RECORD and total <= 8 * 1024**2, "SETUP_CONTROL_PREFIX_QUOTA")
            if not wire or not wire.endswith(b"\n"):
                return None
            event = GameEvent.model_validate(strict_json(verifier.verify(wire)))
            require(not event.is_example and event.visibility == "evaluator"
                    and event.server_boot_id == expected_boot == verifier.boot
                    and (event.campaign_id, event.epoch) == (authority.campaign_id, authority.epoch)
                    and event.seq == event.server_event_seq == seq
                    and event.server_tick >= previous_tick and not event.actor_ids,
                    "SETUP_CONTROL_PREFIX_SCOPE")
            previous_tick = event.server_tick
            if seq == 1:
                require(event.kind == "server_started" and event.payload_schema in
                        {"strata/ServerStarted/8", "strata/ServerStarted/9", "strata/ServerStarted/10", "strata/ServerStarted/11", "strata/ServerStarted/12", "strata/ServerStarted/13"}
                        and event.server_tick == 0, "SETUP_CONTROL_MODULE_REQUIRED")
                model = LAUNCH_STARTUP_MODELS[event.payload_schema]
                boot = model.model_validate(event.payload)
                require(boot.setup_capture_support.status == "supported"
                        and boot.setup_history_support.vanilla_hooks_verified
                        and boot.setup_history_support.team_hooks_verified and
                        (not isinstance(boot, ServerStartedV10) or boot.setup_history_support.global_map_hooks_verified) and
                        (not isinstance(boot, ServerStartedV11) or boot.setup_history_support.team_map_hooks_verified) and
                        (not isinstance(boot, ServerStartedV12) or boot.setup_history_support.script_field_hooks_verified),
                        "SETUP_CONTROL_HOOKS_REQUIRED")
            elif history is not None:
                require(event.kind == "setup_snapshot" and event.payload_schema == "strata/NativeSetupSnapshot/1"
                        and event.server_tick == 1, "SETUP_CONTROL_PREFIX_ORDER")
                point = SetupSnapshot.model_validate(event.payload)
                require(point.phase == "startup" and point.transaction_id is None and point.actor is None,
                        "SETUP_CONTROL_PREFIX_SCOPE")
                server = point.server
                require(isinstance(point.team, ManagerReady) and isinstance(point.pack, PackMode)
                        and point.pack.mode == "expert" and point.pack.is_expert and not point.pack.is_normal
                        and not point.pack.startup_errors and not point.pack.server_errors
                        and server.default_game_mode == server.world_game_mode == "survival"
                        and not (server.world_allows_commands or server.command_blocks_enabled
                                 or server.rcon_enabled or server.operator_levels or server.command_events_seen),
                        "SETUP_CONTROL_BASELINE_UNQUALIFIED")
                return {"server_boot_id": expected_boot, "campaign_id": event.campaign_id,
                        "epoch": event.epoch, "last_event_seq": seq,
                        "startup": point.model_dump(), "history": history.model_dump(),
                        "launch_identity": boot.launch_identity.model_dump(),
                        "module_sha256": boot.launch_identity.module_sha256,
                        "prefix_binding_digest": digest([boot.model_dump(), history.model_dump(), point.model_dump()])}
            elif event.kind == "setup_history":
                require(event.payload_schema == HISTORY_SCHEMAS[boot.setup_history_support.policy] and event.server_tick == 1,
                        "SETUP_CONTROL_PREFIX_ORDER")
                history = parse_history(event.payload)
                require(history.policy == boot.setup_history_support.policy, "SETUP_HISTORY_MODULE")
                require(history.phase == "startup" and not any(history.attempts.values())
                        and not history.off_thread_attempts and not history.overflowed,
                        "SETUP_CONTROL_BASELINE_TAINTED")
            else:
                require(event.kind == "recipe_snapshot" and event.payload_schema == "strata/RecipeSnapshot/1"
                        and event.server_tick == 0, "SETUP_CONTROL_PREFIX_ORDER")
                RecipeSnapshot.model_validate(event.payload)
        require(False, "SETUP_CONTROL_PREFIX_QUOTA")


class SetupControl:
    """Journal before a single write; no retry, replay, free text or resumed dispatch."""

    def __init__(self, baseline):
        require(baseline["mode"] == 0, "SETUP_CONTROL_BASELINE_MODE")
        self.result = {"policy": POLICY, "purpose": "negative_control", "state": "waiting",
                       "baseline_saved": baseline, "commands": list(COMMANDS),
                       "scoring_eligible": False}
        self.attempted = False
        self.restore_attempted = False
        self.sent_at = None

    def dispatch(self, prefix, process, record, *, deadline, exposure_s, log):
        require(not self.attempted, "SETUP_CONTROL_ALREADY_ATTEMPTED")
        require(time.monotonic() + exposure_s <= deadline, "SETUP_CONTROL_DEADLINE")
        self.attempted = True
        self.result.update(state="dispatching", startup_prefix=prefix, intent_unix=time.time(),
                           log_offset=Path(log).stat().st_size)
        record()
        process.send_input("\n".join(COMMANDS[:2]) + "\n")
        self.result.update(state="awaiting_saved_effect", sent_unix=time.time())
        record()

    def advance(self, process, record, *, world, log, deadline, exposure_s):
        require(self.result["state"] == "awaiting_saved_effect" and not self.restore_attempted,
                "SETUP_CONTROL_RESTORE_ALREADY_ATTEMPTED")
        raw = private_read(Path(log), 64 * 1024**2)[self.result["log_offset"]:]
        # Read observations again if incomplete; never resend either command.
        feedback = re.findall(rb"(?m)^.*(?:The default game mode is now (Creative Mode|Survival Mode)|(Saved the game))\r?$", raw)
        if not any(saved for _, saved in feedback):
            return False
        require(feedback == [(b"Creative Mode", b""), (b"", b"Saved the game")],
                "SETUP_CONTROL_SAVE_FEEDBACK")
        intermediate = saved_mode(Path(world) / "level.dat",
                                  archive=Path(log).parent / "setup-control.intermediate-level.dat")
        require(intermediate["mode"] == 1, "SETUP_CONTROL_INTERMEDIATE_UNPROVEN")
        require(time.monotonic() + exposure_s <= deadline, "SETUP_CONTROL_DEADLINE")
        self.restore_attempted = True
        self.result.update(state="restore_dispatching", intermediate_saved=intermediate,
                           intermediate_observed_unix=time.time(),
                           intermediate_log_bytes=len(raw),
                           intermediate_log_sha256=hashlib.sha256(raw).hexdigest())
        record()
        process.send_input(COMMANDS[2] + "\n")
        self.sent_at = time.monotonic()
        self.result.update(state="sent", restore_sent_unix=time.time())
        record()
        return True

    def finish(self, inspection, world, log):
        require(self.result["state"] == "sent", "SETUP_CONTROL_INCOMPLETE")
        prefix = self.result["startup_prefix"]
        require(all(inspection[key] == prefix[key] for key in ("campaign_id", "epoch", "server_boot_id"))
                and inspection["setup_startup"] == prefix["startup"]
                and inspection["launch_identity"]["module_sha256"] == prefix["module_sha256"],
                "SETUP_CONTROL_INSPECTION_SCOPE")
        history = inspection.get("setup_history", {})
        terminal = history.get("terminal", {})
        expected = dict.fromkeys(parse_history(terminal).attempts, 0)
        expected.update(command_attempt=4, native_stop_command=1, world_mode=2)
        require(terminal["attempts"] == expected and not terminal["off_thread_attempts"]
                and not terminal["overflowed"] and not history["observed_history_clear"]
                and set(history["reasons"]) == {"observed:command_attempt", "observed:native_stop_command",
                                                "observed:world_mode"}
                and not inspection["avatar_ticks_at_last_sample"] and not inspection["craft_witnesses"],
                "SETUP_CONTROL_HISTORY_MISMATCH")
        raw_log = private_read(Path(log), 64 * 1024**2)[self.result["log_offset"]:]
        feedback = re.findall(rb"(?m)^.*The default game mode is now (Creative Mode|Survival Mode)\r?$", raw_log)
        require(feedback == [b"Creative Mode", b"Survival Mode"], "SETUP_CONTROL_FEEDBACK_MISSING")
        retained = saved_mode(Path(log).parent / "setup-control.intermediate-level.dat")
        require(retained == self.result["intermediate_saved"] and retained["mode"] == 1,
                "SETUP_CONTROL_INTERMEDIATE_CHANGED")
        require(hashlib.sha256(raw_log[:self.result["intermediate_log_bytes"]]).hexdigest()
                == self.result["intermediate_log_sha256"], "SETUP_CONTROL_LOG_CHANGED")
        final = saved_mode(Path(world) / "level.dat", archive=Path(log).parent / "setup-control.final-level.dat")
        require(final["mode"] == self.result["baseline_saved"]["mode"] == 0,
                "SETUP_CONTROL_RESTORE_UNPROVEN")
        self.result.update(state="completed_negative_control", terminal_history=history,
            final_saved=final, command_feedback=[v.decode("ascii") for v in feedback],
            log_sha256=hashlib.sha256(raw_log).hexdigest(), native_mutation_observed=True,
            intermediate_mode_verified=self.result["intermediate_saved"]["mode"] == 1,
            final_mode_matches_baseline=True, full_setup_history_qualified=False)
        return self.result
