"""Private offline inspection of the Forge evidence spool, never a gameplay API.

Framing and provenance checks do not authenticate a same-user file or establish
scoring eligibility. Deployment isolation and authenticated live ingestion remain
separate gates. A missing clean-stop event or partial line is an explicit failure.
"""

import argparse
import hashlib
import json
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator

from mcbench.contracts import Digest, Id, Name, Strict, UInt
from mcbench.records import GameEvent
from mcbench.storage import Fault, reject_links, require

from .cli import write_report
from .telemetry_configs import ConfigQuery, ConfigSnapshot
from .craft_witness import CraftBegin, CraftEnd, qualify_click
from .setup_facts import SetupSnapshot, SetupSupport
from .setup_history import HistorySupport, SetupHistory, advance, qualify_history

KINDS = {
    "server_started": "strata/ServerStarted/1",
    "recipe_snapshot": "strata/RecipeSnapshot/1",
    "server_health": "strata/ServerHealth/1",
    "craft_callback": "strata/RawCraftCallback/1",
    "server_stopped": "strata/ServerStopped/1",
    "config_snapshot": "strata/ConfigSnapshot/1",
    "craft_begin": "strata/CraftBegin/1",
    "craft_end": "strata/CraftEnd/1",
    "setup_snapshot": "strata/NativeSetupSnapshot/1",
    "setup_history": "strata/NativeSetupHistory/1",
}
MAX_SPOOL_BYTES = 1024**3


class StackSnapshot(Strict):
    item_id: Name
    count: UInt
    has_nbt: bool


class ServerStarted(Strict):
    module: Literal["strata-forge1192-telemetry/0.1.0"]
    minecraft: Literal["1.19.2"]
    forge: Literal["43.4.23"]
    scoring_provenance_supported: Literal[False]
    recipe_count: UInt


class ServerStartedV2(ServerStarted):
    module: Literal["strata-forge1192-telemetry/0.2.0"]
    config_queries: list[ConfigQuery] = Field(max_length=16)

    @model_validator(mode="after")
    def unique_queries(self):
        require(len({q.file_name for q in self.config_queries}) == len(self.config_queries),
                "TELEMETRY_CONFIG_QUERY")
        return self


class ServerStartedV3(ServerStartedV2):
    module: Literal["strata-forge1192-telemetry/0.3.0"]
    craft_capture_policy: Literal["server-result-pickup-bracket/1"]


class CraftCaptureSupport(Strict):
    hook_verified: Literal[True]
    fastbench_sha256: Literal["a2ac76078734a2506dec112cf9b6ba214528ce91e99ae5553070a88690f61c12"] | None


class ServerStartedV4(ServerStartedV3):
    module: Literal["strata-forge1192-telemetry/0.3.1", "strata-forge1192-telemetry/0.3.2",
                    "strata-forge1192-telemetry/0.3.3"]
    craft_capture_policy: Literal["server-result-pickup-fastbench-bound/2"]
    craft_capture_support: CraftCaptureSupport


class LaunchIdentity(Strict):
    policy: Literal["native-server-launch-observation/1"]
    pid: int = Field(ge=1, le=4294967295)
    process_started_unix_ms: int = Field(gt=0, le=9007199254740991)
    executable: str = Field(min_length=1, max_length=32768)
    game_directory: str = Field(min_length=1, max_length=32768)
    world_directory: str = Field(min_length=1, max_length=32768)
    module_file: str = Field(min_length=1, max_length=32768)
    module_sha256: Digest
    online_mode: bool
    server_port: int = Field(ge=1, le=65535)


class ServerStartedV5(ServerStartedV4):
    module: Literal["strata-forge1192-telemetry/0.3.4"]
    launch_identity: LaunchIdentity


class ServerStartedV6(ServerStartedV5):
    module: Literal["strata-forge1192-telemetry/0.3.5"]
    setup_capture_policy: Literal["native-e9e-setup-observation/1"]
    setup_capture_support: SetupSupport


class ServerStartedV7(ServerStartedV6):
    module: Literal["strata-forge1192-telemetry/0.3.6"]
    telemetry_transport: Literal["private-file/1", "windows-owned-pipe/1"]


class ServerStartedV8(ServerStartedV7):
    module: Literal["strata-forge1192-telemetry/0.3.7"]
    setup_history_support: HistorySupport


LAUNCH_STARTUP_MODELS = {"strata/ServerStarted/5": ServerStartedV5,
                        "strata/ServerStarted/6": ServerStartedV6,
                        "strata/ServerStarted/7": ServerStartedV7,
                        "strata/ServerStarted/8": ServerStartedV8}


class RecipeSnapshot(Strict):
    recipe_id: Name
    present: bool
    serializer: Name | None = None
    output: StackSnapshot | None = None
    ingredients: list[list[StackSnapshot]] | None = Field(default=None, max_length=128)
    width: UInt | None = None
    height: UInt | None = None

    @model_validator(mode="after")
    def present_fields(self):
        expected = {"serializer", "output", "ingredients"}
        supplied = self.model_fields_set
        require((expected <= supplied and all(getattr(self, key) is not None for key in expected))
                if self.present else not expected & supplied,
                "TELEMETRY_PAYLOAD_INVALID")
        require((self.width is None) == (self.height is None), "TELEMETRY_PAYLOAD_INVALID")
        if self.width is not None:
            require(self.present and self.width > 0 and self.height > 0
                    and self.width * self.height == len(self.ingredients),
                    "TELEMETRY_PAYLOAD_INVALID")
        if self.ingredients is not None:
            require(all(len(items) <= 512 for items in self.ingredients),
                    "TELEMETRY_PAYLOAD_INVALID")
        return self


class ServerHealth(Strict):
    interval_wall_ns: UInt
    interval_server_ticks: UInt
    observed_tick_work_ns: UInt
    server_average_mspt: float = Field(ge=0)
    heap_used_bytes: UInt
    gc_count: UInt
    gc_time_ms: UInt
    durable_event_seq_before_sample: UInt
    avatar_ticks_since_boot: dict[Id, UInt]


class RawCraftCallback(Strict):
    score_eligible: Literal[False]
    reason: Literal["consumption_team_recipe_and_setup_provenance_unverified"]
    output_at_callback: StackSnapshot
    matrix_at_callback: list[StackSnapshot] = Field(max_length=128)


PAYLOADS = dict(zip(KINDS, (ServerStarted, RecipeSnapshot, ServerHealth,
                          RawCraftCallback, Strict, ConfigSnapshot, CraftBegin, CraftEnd, SetupSnapshot,
                          SetupHistory), strict=True))


def unique_object(pairs):
    value = {}
    for key, item in pairs:
        require(key not in value, "TELEMETRY_DUPLICATE_FIELD")
        value[key] = item
    return value


def inspect_spool(path: Path, campaign_id: str, epoch: int, *, authentication=None):
    """Require a complete single-boot stream and return private inspection evidence."""
    reject_links(path.absolute())
    require(path.is_file() and path.stat().st_nlink == 1, "UNSAFE_PATH")
    require(path.stat().st_size <= MAX_SPOOL_BYTES, "TELEMETRY_QUOTA_EXHAUSTED")
    if authentication is not None:
        authentication.require_scope(campaign_id, epoch)
    from .telemetry_auth import MAX_WIRE_RECORD
    limit = 1048576 if authentication is None else MAX_WIRE_RECORD
    hasher = hashlib.sha256()
    boot, previous_tick, count, health_tick = None, 0, 0, 0
    recipes, avatars, kinds, configs, config_queries = {}, {}, {}, {}, {}
    stopped = False
    startup_model = ServerStarted
    craft_policy = None
    craft_stack, witnesses, craft_ids = [], [], set()
    startup_setup, pending_setup, setup_support = None, None, None
    craft_setups = {}
    end_observations = {}
    end_histories = {}
    last_command_count = 0
    history_support, previous_history, pending_history, terminal_history = None, None, None, None
    health_wall_ns, health_ticks, wire_bytes = 0, 0, 0
    with path.open("rb") as stream:
        while line := stream.readline(limit + 1):
            require(len(line) <= limit and line.endswith(b"\n"), "TELEMETRY_PARTIAL_RECORD")
            require(not stopped, "TELEMETRY_AFTER_STOP")
            wire_bytes += len(line)
            require(wire_bytes <= MAX_SPOOL_BYTES, "TELEMETRY_QUOTA_EXHAUSTED")
            hasher.update(line)
            if authentication is not None:
                line = authentication.verify(line)
            raw = json.loads(line, object_pairs_hook=unique_object)
            event = GameEvent.model_validate(raw)
            if authentication is not None:
                require(event.server_boot_id == authentication.boot, "TELEMETRY_AUTH_BOOT")
            require(not event.is_example, "EXAMPLE_NOT_EXECUTABLE")
            require(event.campaign_id == campaign_id and event.epoch == epoch,
                    "TELEMETRY_SCOPE_MISMATCH")
            version2 = event.kind == "server_started" and event.payload_schema == "strata/ServerStarted/2"
            version3 = event.kind == "server_started" and event.payload_schema == "strata/ServerStarted/3"
            version4 = event.kind == "server_started" and event.payload_schema == "strata/ServerStarted/4"
            version5 = event.kind == "server_started" and event.payload_schema == "strata/ServerStarted/5"
            version6 = event.kind == "server_started" and event.payload_schema == "strata/ServerStarted/6"
            version7 = event.kind == "server_started" and event.payload_schema == "strata/ServerStarted/7"
            version8 = event.kind == "server_started" and event.payload_schema == "strata/ServerStarted/8"
            require(event.kind in KINDS and (KINDS[event.kind] == event.payload_schema or version2 or version3 or version4 or version5 or version6 or version7 or version8),
                    "SCHEMA_UNSUPPORTED")
            require(event.seq == event.server_event_seq == count + 1, "TELEMETRY_SEQUENCE_GAP")
            require(event.server_tick >= previous_tick, "TELEMETRY_TICK_ROLLBACK")
            if boot is None:
                require(event.kind == "server_started" and event.server_tick == 0,
                        "TELEMETRY_START_MISSING")
                boot = event.server_boot_id
                if authentication is not None:
                    require((version4 and event.payload.get("module") == "strata-forge1192-telemetry/0.3.3")
                            or (version5 and event.payload.get("module") == "strata-forge1192-telemetry/0.3.4")
                            or (version6 and event.payload.get("module") == "strata-forge1192-telemetry/0.3.5")
                            or (version7 and event.payload.get("module") == "strata-forge1192-telemetry/0.3.6")
                            or (version8 and event.payload.get("module") == "strata-forge1192-telemetry/0.3.7"),
                            "TELEMETRY_AUTH_MODULE")
                startup_model = ServerStartedV8 if version8 else ServerStartedV7 if version7 else ServerStartedV6 if version6 else ServerStartedV5 if version5 else ServerStartedV4 if version4 else ServerStartedV3 if version3 else ServerStartedV2 if version2 else ServerStarted
                module = ("strata-forge1192-telemetry/0.3.7" if version8 else "strata-forge1192-telemetry/0.3.6" if version7 else "strata-forge1192-telemetry/0.3.5" if version6 else "strata-forge1192-telemetry/0.3.4" if version5 else ("strata-forge1192-telemetry/0.3.1", "strata-forge1192-telemetry/0.3.2",
                           "strata-forge1192-telemetry/0.3.3") if version4 else
                          "strata-forge1192-telemetry/0.3.0" if version3 else
                          "strata-forge1192-telemetry/0.2.0" if version2 else
                          "strata-forge1192-telemetry/0.1.0")
                require(event.payload.get("module") in (module if isinstance(module, tuple) else (module,))
                        and event.payload.get("minecraft") == "1.19.2"
                        and event.payload.get("forge") == "43.4.23"
                        and event.payload.get("scoring_provenance_supported") is False,
                        "TELEMETRY_MODULE_MISMATCH")
            else:
                require(event.server_boot_id == boot, "TELEMETRY_BOOT_MISMATCH")
                require(event.kind != "server_started", "TELEMETRY_DUPLICATE_START")
            data = event.payload
            parsed = (startup_model if event.kind == "server_started" else PAYLOADS[event.kind]).model_validate(data)
            if version5 or version6 or version7 or version8:
                startup_identity = parsed.launch_identity.model_dump()
            if version7 or version8:
                startup_transport = parsed.telemetry_transport
            if version6 or version7 or version8:
                setup_support = parsed.setup_capture_support.model_dump()
            if version8:
                history_support = parsed.setup_history_support
            if version2 or version3 or version4 or version5 or version6 or version7 or version8:
                config_queries = {q.file_name: q.paths for q in parsed.config_queries}
            if version3 or version4 or version5 or version6 or version7 or version8:
                craft_policy = parsed.craft_capture_policy
            if pending_setup is not None:
                observed_event, point = pending_setup
                require(event.kind == point.phase and parsed.transaction_id == point.transaction_id
                        and event.server_tick == observed_event.server_tick
                        and event.actor_ids == observed_event.actor_ids, "SETUP_POINT_NOT_ADJACENT")
                pending_setup = None
            elif issubclass(startup_model, ServerStartedV6) and event.kind in {"craft_begin", "craft_end"}:
                require(False, "SETUP_POINT_MISSING")
            if pending_history is not None:
                history_event, history = pending_history
                if history.phase == "stop":
                    require(event.kind == "server_stopped" and not event.actor_ids,
                            "SETUP_HISTORY_NOT_ADJACENT")
                    terminal_history = history
                else:
                    require(event.kind == "setup_snapshot" and parsed.phase == history.phase
                            and parsed.transaction_id == history.transaction_id,
                            "SETUP_HISTORY_NOT_ADJACENT")
                    if history.phase == "craft_end":
                        end_histories[history.transaction_id] = history_event
                require(event.server_tick == history_event.server_tick
                        and event.actor_ids == history_event.actor_ids, "SETUP_HISTORY_NOT_ADJACENT")
                pending_history = None
            elif issubclass(startup_model, ServerStartedV8) and event.kind in {"setup_snapshot", "server_stopped"}:
                require(False, "SETUP_HISTORY_MISSING")
            if event.kind == "setup_history":
                require(issubclass(startup_model, ServerStartedV8), "SETUP_HISTORY_MODULE")
                require((previous_history is None) == (parsed.phase == "startup"), "SETUP_HISTORY_START")
                require(parsed.phase not in {"startup", "stop"} or not event.actor_ids,
                        "SETUP_HISTORY_SCOPE")
                require(parsed.phase == "stop" or parsed.attempts["native_stop_command"] == 0,
                        "SETUP_HISTORY_EARLY_STOP")
                advance(previous_history, parsed)
                previous_history = parsed
                pending_history = (event, parsed)
            if event.kind == "setup_snapshot":
                require(issubclass(startup_model, ServerStartedV6), "SETUP_MODULE_UNSUPPORTED")
                require(parsed.server.command_events_seen >= last_command_count, "SETUP_COMMAND_COUNTER_ROLLBACK")
                last_command_count = parsed.server.command_events_seen
                if parsed.phase == "startup":
                    require(startup_setup is None and event.server_tick == 1 and not event.actor_ids
                            and not craft_ids, "SETUP_START_INVALID")
                    startup_setup = parsed.model_dump()
                else:
                    require(startup_setup is not None and event.actor_ids == [parsed.actor.uuid], "SETUP_ACTOR_MISMATCH")
                    tx = parsed.transaction_id
                    if parsed.phase == "craft_begin":
                        require(tx not in craft_setups and tx not in craft_ids, "SETUP_POINT_DUPLICATE")
                        craft_setups[tx] = {"before": parsed.model_dump()}
                    else:
                        require(tx in craft_setups and "after" not in craft_setups[tx], "SETUP_POINT_UNPAIRED")
                        craft_setups[tx]["after"] = parsed.model_dump()
                        end_observations[tx] = event
                    pending_setup = (event, parsed)
            if event.kind == "config_snapshot":
                name = parsed.file_name
                require(name in config_queries and name not in configs, "TELEMETRY_CONFIG_SCOPE")
                require(event.server_tick == 1 and not any(k in kinds for k in
                        ("server_health", "craft_callback")), "TELEMETRY_CONFIG_ORDER")
                if parsed.status == "snapshot":
                    require([v.path for v in parsed.values] == config_queries[name], "TELEMETRY_CONFIG_SCOPE")
                configs[name] = data
            if event.kind == "recipe_snapshot":
                recipe_id = data.get("recipe_id")
                require(isinstance(recipe_id, str) and recipe_id not in recipes,
                        "TELEMETRY_DUPLICATE_RECIPE")
                require(type(data.get("present")) is bool, "TELEMETRY_PAYLOAD_INVALID")
                recipes[recipe_id] = data
            elif event.kind == "server_health":
                ticks = data.get("interval_server_ticks")
                wall = data.get("interval_wall_ns")
                require(type(ticks) is int and ticks == event.server_tick - health_tick
                        and type(wall) is int and wall > 0, "TELEMETRY_CLOCK_MISMATCH")
                durable = data.get("durable_event_seq_before_sample")
                require(type(durable) is int and 0 <= durable < event.seq,
                        "TELEMETRY_CURSOR_INVALID")
                exposures = data.get("avatar_ticks_since_boot")
                require(isinstance(exposures, dict) and set(avatars) <= set(exposures),
                        "TELEMETRY_AVATAR_TICKS_INVALID")
                require(all(type(v) is int and avatars.get(k, 0) <= v <= event.server_tick
                            for k, v in exposures.items()), "TELEMETRY_AVATAR_TICKS_INVALID")
                avatars = exposures
                health_tick = event.server_tick
                health_ticks += ticks
                health_wall_ns += wall
            elif event.kind == "craft_callback":
                require(data.get("score_eligible") is False, "TELEMETRY_UNPROVEN_SCORE")
                if craft_stack:
                    craft_stack[-1][1].append(event)
                    require(len(craft_stack[-1][1]) <= 16, "TELEMETRY_CRAFT_QUOTA")
            elif event.kind == "craft_begin":
                require(issubclass(startup_model, ServerStartedV3)
                        and parsed.policy == craft_policy, "TELEMETRY_MODULE_MISMATCH")
                require(len(craft_stack) < 16, "TELEMETRY_CRAFT_QUOTA")
                require(parsed.transaction_id not in craft_ids, "TELEMETRY_CRAFT_DUPLICATE")
                craft_ids.add(parsed.transaction_id)
                craft_stack.append((event, []))
            elif event.kind == "craft_end":
                require(issubclass(startup_model, ServerStartedV3)
                        and parsed.policy == craft_policy and craft_stack, "TELEMETRY_CRAFT_UNPAIRED")
                begin, callbacks = craft_stack.pop()
                require(begin.payload["transaction_id"] == parsed.transaction_id, "TELEMETRY_CRAFT_UNPAIRED")
                try:
                    require(len(callbacks) == 1, "CRAFT_CALLBACK_UNPROVEN")
                    witness = qualify_click(begin, callbacks[0], event, recipes.get(begin.payload["recipe_id"], {}),
                                            end_observation=end_observations.get(parsed.transaction_id),
                                            end_history=end_histories.get(parsed.transaction_id))
                except Fault as error:
                    witness = {"transaction_id": parsed.transaction_id, "resource_witness": "fail",
                               "error_code": error.code, "score_eligible": False}
                if issubclass(startup_model, ServerStartedV6):
                    points = craft_setups.pop(parsed.transaction_id)
                    end_observations.pop(parsed.transaction_id)
                    end_histories.pop(parsed.transaction_id, None)
                    require(set(points) == {"before", "after"}, "SETUP_POINT_MISSING")
                    witness["setup_points"] = points
                witnesses.append(witness)
            stopped = event.kind == "server_stopped"
            kinds[event.kind] = kinds.get(event.kind, 0) + 1
            previous_tick = event.server_tick
            count += 1
            require(count <= 1000000, "TELEMETRY_QUOTA_EXHAUSTED")
    require(stopped, "TELEMETRY_CLEAN_STOP_MISSING")
    require(not craft_stack, "TELEMETRY_CRAFT_INCOMPLETE")
    require(pending_setup is None and not craft_setups and not end_observations and not end_histories,
            "SETUP_POINT_UNPAIRED")
    require(not issubclass(startup_model, ServerStartedV6) or startup_setup is not None, "SETUP_START_MISSING")
    require(pending_history is None and (not issubclass(startup_model, ServerStartedV8)
            or terminal_history is not None), "SETUP_HISTORY_STOP_MISSING")
    require(set(configs) == set(config_queries), "TELEMETRY_CONFIG_MISSING")
    report = {"schema": "strata/PrivateTelemetryInspection/1", "visibility": "evaluator",
            "file_sha256": hasher.hexdigest(), "campaign_id": campaign_id, "epoch": epoch,
            "server_boot_id": boot, "records": count, "kind_counts": kinds,
            "last_server_tick": previous_tick, "sampled_server_ticks": health_ticks,
            "sampled_wall_ns": health_wall_ns, "avatar_ticks_at_last_sample": avatars,
            "recipe_snapshots": recipes, "clean_stop": True, "scoring_eligible": False,
            "config_queries": config_queries, "config_snapshots": configs,
            "craft_witnesses": witnesses,
            "transport_identity_verified": False, "mechanics_parity_verified": False,
            "gate_result": "not_run"}
    if authentication is not None:
        report["authentication"] = authentication.receipt(boot, count)
    if issubclass(startup_model, ServerStartedV5):
        report["launch_identity"] = startup_identity
    if issubclass(startup_model, ServerStartedV6):
        report.update(setup_startup=startup_setup, setup_capture_support=setup_support)
    if issubclass(startup_model, ServerStartedV7):
        report["telemetry_transport"] = startup_transport
    if issubclass(startup_model, ServerStartedV8):
        report["setup_history"] = qualify_history(history_support, terminal_history)
    return report


def assert_e9e_furnace(report):
    """Exact E9E 1.27.0 expert script assertion; does not assert a player crafted it."""
    snapshots = report["recipe_snapshots"]
    expert = snapshots.get("enigmatica:expert/minecraft/shaped/furnace", {})
    normal = snapshots.get("minecraft:furnace", {})
    def stack(name):
        return {"item_id": "minecraft:" + name, "count": 1, "has_nbt": False}
    ingredients = [[stack(name)] if name else [] for name in
                   ("andesite", "andesite", "andesite", "andesite", None, "andesite",
                    "polished_andesite", "polished_andesite", "polished_andesite")]
    expectations = {
        "expert_recipe_present": (expert.get("present"), True),
        "shaped_serializer": (expert.get("serializer"), "minecraft:crafting_shaped"),
        "three_by_three": ([expert.get("width"), expert.get("height")], [3, 3]),
        "single_furnace_output": (expert.get("output"), stack("furnace")),
        "expert_ingredients": (expert.get("ingredients"), ingredients),
        "vanilla_recipe_absent": (normal.get("present"), False),
    }
    checks = [{"check": name, "result": "pass" if actual == expected else "fail",
               "actual": actual, "expected": expected}
              for name, (actual, expected) in expectations.items()]
    return {"schema": "strata/E9EFurnaceRuntimeAssertion/1", "pack": "e9e/1.27.0",
            "spool_sha256": report["file_sha256"], "checks": checks,
            "result": "pass" if all(c["result"] == "pass" for c in checks) else "fail",
            "player_crafting_verified": False, "quest_state_verified": False,
            "mechanics_parity_verified": False, "gate_result": "not_run"}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spool", type=Path)
    parser.add_argument("--campaign", required=True)
    parser.add_argument("--epoch", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--e9e-furnace", action="store_true")
    args = parser.parse_args(argv)
    report = inspect_spool(args.spool, args.campaign, args.epoch)
    if args.e9e_furnace:
        report["e9e_furnace_assertion"] = assert_e9e_furnace(report)
    receipt = write_report(args.output, report)
    print(json.dumps({"status": "inspected", "visibility": "evaluator", **receipt}))


if __name__ == "__main__":
    main()
