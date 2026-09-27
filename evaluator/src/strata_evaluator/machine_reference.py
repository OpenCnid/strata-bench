"""Private prelaunch machine expectations and candidate resource inspection.

Registration binds intended bytes, not loaded code, actual setup or team control.
The craft-reference seal supplies scope, file custody and one-use launch binding.
"""

from typing import Literal

from pydantic import Field, model_validator

from mcbench.contracts import Id, Name, Positive, Strict, UInt
from mcbench.storage import Fault, digest, require

from .machine_resource import qualify_native_furnace_completion
from .machine_witness import FurnaceRecipe
from .machine_window import ExactWindow, OperatingWindow, inspect_operating_windows
from .machine_interval import MAX_TICKS


class FurnaceTarget(Strict):
    dimension: Name
    position: list[int] = Field(min_length=3, max_length=3)
    block_id: Literal["thermal:machine_furnace"]
    registration_origin: Literal["direct", "converted_cooking"]
    machine_recipe_ids: dict[Name, Name] = Field(min_length=1, max_length=128)
    recipes: dict[Name, FurnaceRecipe] = Field(min_length=1, max_length=128)
    minimum_output: Positive

    @model_validator(mode="after")
    def consistent(self):
        require(all(-(2**31) <= v < 2**31 for v in self.position), "MACHINE_TARGET_POSITION")
        require(set(self.machine_recipe_ids) == set(self.recipes)
                and all(k == v.recipe_id for k, v in self.recipes.items())
                and len({v.output.item_id for v in self.recipes.values()}) == 1,
                "MACHINE_TARGET_RECIPES")
        require(all((source == machine if self.registration_origin == "direct"
                     else machine.startswith("thermal:"))
                    for source, machine in self.machine_recipe_ids.items()),
                "MACHINE_TARGET_REGISTRATION")
        return self


class MachineReference(Strict):
    policy: Literal["thermal1192-private-machine-reference/1"]
    start_server_tick: UInt
    cutoff_server_tick: Positive
    targets: dict[Id, FurnaceTarget] = Field(min_length=1, max_length=16)

    @model_validator(mode="after")
    def consistent(self):
        require(self.start_server_tick < self.cutoff_server_tick, "MACHINE_REFERENCE_WINDOW")
        locations = [(v.dimension, tuple(v.position)) for v in self.targets.values()]
        require(len(set(locations)) == len(locations), "MACHINE_REFERENCE_OVERLAP")
        return self


class MachineReferenceV2(MachineReference):
    policy: Literal["thermal1192-private-machine-reference/2"]
    operating_windows: dict[Id, OperatingWindow] = Field(min_length=1, max_length=16)

    @model_validator(mode="after")
    def windows(self):
        require(set(self.operating_windows) == set(self.targets), "MACHINE_OPERATING_TARGETS")
        for window in self.operating_windows.values():
            if isinstance(window, ExactWindow):
                require(self.start_server_tick <= window.start_server_tick <= window.end_server_tick
                        <= self.cutoff_server_tick, "MACHINE_OPERATING_BOUNDS")
        return self


def parse_machine_reference(value):
    if isinstance(value, MachineReference):
        return value
    model = (MachineReferenceV2 if value.get("policy") == "thermal1192-private-machine-reference/2"
             else MachineReference)
    return model.model_validate(value)


class MachineReferenceInspection:
    """Private accumulator, returned only after the entire stream is verified."""

    def __init__(self, plan):
        self.plan = parse_machine_reference(plan)
        self.accepted = []
        self.rejected = []
        self.output = {key: 0 for key in self.plan.targets}
        self.children = {}

    def child(self, event, captured):
        if isinstance(self.plan, MachineReferenceV2):
            require(len(self.children) < MAX_TICKS * 4
                    and captured.transaction_id not in self.children, "MACHINE_OPERATING_CHILD_QUOTA")
            self.children[captured.transaction_id] = (event, captured)

    def observe(self, event, captured):
        # Stream parser has already validated producer profile, ordering, schema,
        # transaction uniqueness, generation monotonicity and enclosing scope.
        target_id = next((key for key, value in self.plan.targets.items()
                          if value.dimension == captured.dimension
                          and value.position == captured.position
                          and value.block_id == captured.block_id), None)
        reason, witness = None, None
        if target_id is None:
            reason = "MACHINE_UNREGISTERED_LOCATION"
        elif not self.plan.start_server_tick <= event.server_tick <= self.plan.cutoff_server_tick:
            reason = "MACHINE_OUTSIDE_TICK_WINDOW"
        elif event.kind == "machine_capture_refused":
            reason = "MACHINE_NATIVE_REFUSED"
        else:
            target = self.plan.targets[target_id]
            registration = captured.registration
            recipe = target.recipes.get(registration.source_recipe_id)
            if recipe is None:
                reason = "MACHINE_UNREGISTERED_RECIPE"
            elif (registration.origin != target.registration_origin
                  or registration.machine_recipe_id != target.machine_recipe_ids[recipe.recipe_id]):
                reason = "MACHINE_REGISTRATION_MISMATCH"
            else:
                try:
                    witness = qualify_native_furnace_completion(event, recipe.model_dump())
                except Fault as error:
                    reason = error.code
        if reason:
            self.rejected.append({"transaction_id": captured.transaction_id,
                "target_id": target_id, "reason": reason,
                "source_event_digest": digest(event.model_dump())})
        else:
            self.accepted.append({"target_id": target_id, "witness": witness})
            self.output[target_id] += sum(witness["produced"].values())

    def report(self, intervals=None):
        result = {"policy": self.plan.policy, "plan_digest": digest(self.plan.model_dump()),
            "targets": {key: {"candidate_output": value,
                "candidate_complete": value >= self.plan.targets[key].minimum_output}
                for key, value in self.output.items()},
            "accepted_resource_witnesses": self.accepted,
            "rejected_resource_witnesses": self.rejected,
            "setup_team_qualified": False, "loaded_code_authenticated": False,
            "sustained_operation_verified": False, "scoring_eligible": False}
        if isinstance(self.plan, MachineReferenceV2):
            windows = inspect_operating_windows(self.plan, intervals, self.children, self.accepted)
            result["operating_windows"] = windows
            result["completion_candidates"] = result["targets"]
            result["targets"] = {key: {name: value[name] for name in ("candidate_output", "candidate_complete")}
                                 for key, value in windows["targets"].items()}
        return result
