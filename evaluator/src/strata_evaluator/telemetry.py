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

from mcbench.contracts import Id, Name, Strict, UInt
from mcbench.records import GameEvent
from mcbench.storage import Fault, reject_links, require

from .cli import write_report
from .telemetry_configs import ConfigQuery, ConfigSnapshot
from .craft_witness import CraftBegin, CraftEnd, qualify_click

KINDS = {
    "server_started": "strata/ServerStarted/1",
    "recipe_snapshot": "strata/RecipeSnapshot/1",
    "server_health": "strata/ServerHealth/1",
    "craft_callback": "strata/RawCraftCallback/1",
    "server_stopped": "strata/ServerStopped/1",
    "config_snapshot": "strata/ConfigSnapshot/1",
    "craft_begin": "strata/CraftBegin/1",
    "craft_end": "strata/CraftEnd/1",
}


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
    module: Literal["strata-forge1192-telemetry/0.3.1"]
    craft_capture_policy: Literal["server-result-pickup-fastbench-bound/2"]
    craft_capture_support: CraftCaptureSupport


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
                          RawCraftCallback, Strict, ConfigSnapshot, CraftBegin, CraftEnd), strict=True))


def unique_object(pairs):
    value = {}
    for key, item in pairs:
        require(key not in value, "TELEMETRY_DUPLICATE_FIELD")
        value[key] = item
    return value


def inspect_spool(path: Path, campaign_id: str, epoch: int):
    """Require a complete single-boot stream and return private inspection evidence."""
    reject_links(path.absolute())
    require(path.is_file() and path.stat().st_nlink == 1, "UNSAFE_PATH")
    require(path.stat().st_size <= 1024**3, "TELEMETRY_QUOTA_EXHAUSTED")
    hasher = hashlib.sha256()
    boot, previous_tick, count, health_tick = None, 0, 0, 0
    recipes, avatars, kinds, configs, config_queries = {}, {}, {}, {}, {}
    stopped = False
    startup_model = ServerStarted
    craft_policy = None
    craft_stack, witnesses, craft_ids = [], [], set()
    health_wall_ns, health_ticks = 0, 0
    with path.open("rb") as stream:
        while line := stream.readline(1048577):
            require(len(line) <= 1048576 and line.endswith(b"\n"), "TELEMETRY_PARTIAL_RECORD")
            require(not stopped, "TELEMETRY_AFTER_STOP")
            hasher.update(line)
            raw = json.loads(line, object_pairs_hook=unique_object)
            event = GameEvent.model_validate(raw)
            require(not event.is_example, "EXAMPLE_NOT_EXECUTABLE")
            require(event.campaign_id == campaign_id and event.epoch == epoch,
                    "TELEMETRY_SCOPE_MISMATCH")
            version2 = event.kind == "server_started" and event.payload_schema == "strata/ServerStarted/2"
            version3 = event.kind == "server_started" and event.payload_schema == "strata/ServerStarted/3"
            version4 = event.kind == "server_started" and event.payload_schema == "strata/ServerStarted/4"
            require(event.kind in KINDS and (KINDS[event.kind] == event.payload_schema or version2 or version3 or version4),
                    "SCHEMA_UNSUPPORTED")
            require(event.seq == event.server_event_seq == count + 1, "TELEMETRY_SEQUENCE_GAP")
            require(event.server_tick >= previous_tick, "TELEMETRY_TICK_ROLLBACK")
            if boot is None:
                require(event.kind == "server_started" and event.server_tick == 0,
                        "TELEMETRY_START_MISSING")
                boot = event.server_boot_id
                startup_model = ServerStartedV4 if version4 else ServerStartedV3 if version3 else ServerStartedV2 if version2 else ServerStarted
                module = ("strata-forge1192-telemetry/0.3.1" if version4 else
                          "strata-forge1192-telemetry/0.3.0" if version3 else
                          "strata-forge1192-telemetry/0.2.0" if version2 else
                          "strata-forge1192-telemetry/0.1.0")
                require(event.payload.get("module") == module
                        and event.payload.get("minecraft") == "1.19.2"
                        and event.payload.get("forge") == "43.4.23"
                        and event.payload.get("scoring_provenance_supported") is False,
                        "TELEMETRY_MODULE_MISMATCH")
            else:
                require(event.server_boot_id == boot, "TELEMETRY_BOOT_MISMATCH")
                require(event.kind != "server_started", "TELEMETRY_DUPLICATE_START")
            data = event.payload
            parsed = (startup_model if event.kind == "server_started" else PAYLOADS[event.kind]).model_validate(data)
            if version2 or version3 or version4:
                config_queries = {q.file_name: q.paths for q in parsed.config_queries}
            if version3 or version4:
                craft_policy = parsed.craft_capture_policy
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
                require(startup_model in (ServerStartedV3, ServerStartedV4)
                        and parsed.policy == craft_policy, "TELEMETRY_MODULE_MISMATCH")
                require(len(craft_stack) < 16, "TELEMETRY_CRAFT_QUOTA")
                require(parsed.transaction_id not in craft_ids, "TELEMETRY_CRAFT_DUPLICATE")
                craft_ids.add(parsed.transaction_id)
                craft_stack.append((event, []))
            elif event.kind == "craft_end":
                require(startup_model in (ServerStartedV3, ServerStartedV4)
                        and parsed.policy == craft_policy and craft_stack, "TELEMETRY_CRAFT_UNPAIRED")
                begin, callbacks = craft_stack.pop()
                require(begin.payload["transaction_id"] == parsed.transaction_id, "TELEMETRY_CRAFT_UNPAIRED")
                try:
                    require(len(callbacks) == 1, "CRAFT_CALLBACK_UNPROVEN")
                    witness = qualify_click(begin, callbacks[0], event, recipes.get(begin.payload["recipe_id"], {}))
                except Fault as error:
                    witness = {"transaction_id": parsed.transaction_id, "resource_witness": "fail",
                               "error_code": error.code, "score_eligible": False}
                witnesses.append(witness)
            stopped = event.kind == "server_stopped"
            kinds[event.kind] = kinds.get(event.kind, 0) + 1
            previous_tick = event.server_tick
            count += 1
            require(count <= 1000000, "TELEMETRY_QUOTA_EXHAUSTED")
    require(stopped, "TELEMETRY_CLEAN_STOP_MISSING")
    require(not craft_stack, "TELEMETRY_CRAFT_INCOMPLETE")
    require(set(configs) == set(config_queries), "TELEMETRY_CONFIG_MISSING")
    return {"schema": "strata/PrivateTelemetryInspection/1", "visibility": "evaluator",
            "file_sha256": hasher.hexdigest(), "campaign_id": campaign_id, "epoch": epoch,
            "server_boot_id": boot, "records": count, "kind_counts": kinds,
            "last_server_tick": previous_tick, "sampled_server_ticks": health_ticks,
            "sampled_wall_ns": health_wall_ns, "avatar_ticks_at_last_sample": avatars,
            "recipe_snapshots": recipes, "clean_stop": True, "scoring_eligible": False,
            "config_queries": config_queries, "config_snapshots": configs,
            "craft_witnesses": witnesses,
            "transport_identity_verified": False, "mechanics_parity_verified": False,
            "gate_result": "not_run"}


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
