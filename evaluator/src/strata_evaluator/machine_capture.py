"""Raw native furnace facts; no implicit recipe registration or scoring authority."""

from typing import Literal

from pydantic import Field, field_validator, model_validator

from mcbench.contracts import Digest, Id, Name, Strict
from mcbench.storage import require

from .craft_witness import WitnessStack
from .machine_witness import FurnaceState

POLICY = "thermal1192-native-furnace-phases/1"
PINS = {
    "thermal_expansion": "ddf119c33990e991875968c0e810583af091044a3368c28838646f30ace33f4c",
    "thermal": "20c99f015b9b3d034da1f017a14876bc6f15838d72dc450cfd0c1bdd803c10b5",
    "cofh_core": "1e47ecfa7e3bedb7043854d44c53537aacb4b75807c2f7de5df6ab2fa785203d",
}
KINDS = {"machine_completion": "strata/NativeFurnaceCompletion/1",
         "machine_capture_refused": "strata/NativeFurnaceRefusal/1"}


class FurnaceSupport(Strict):
    status: Literal["supported", "unsupported"]
    artifacts: dict[str, Digest | None]
    loaded_code_authenticated: Literal[False]

    @field_validator("loaded_code_authenticated", mode="before")
    @classmethod
    def no_authentication(cls, value):
        require(value is False, "MACHINE_CAPTURE_AUTHORITY")
        return value

    @model_validator(mode="after")
    def pins(self):
        require(self.artifacts.keys() == PINS.keys()
                and (self.status == "supported") == (self.artifacts == PINS),
                "MACHINE_CAPTURE_ARTIFACT")
        return self


class ResolvedFurnaceRecipe(Strict):
    # Thermal's manager discards the public Recipe ID when constructing this
    # internal object. Do not assign one by output identity or unverified lookup.
    runtime_class: Literal["cofh.thermal.lib.util.recipes.internal.SimpleMachineRecipe"]
    input: WitnessStack
    output: WitnessStack
    resolved_input_count: int = Field(ge=1, le=64)
    output_chance: int = Field(ge=1, le=1)
    recipe_energy_rf: int = Field(ge=1, le=2**31 - 1)

    @model_validator(mode="after")
    def plain(self):
        require(self.input.count > 0 and self.output.count > 0
                and self.input.components_empty and self.output.components_empty,
                "MACHINE_CAPTURE_RECIPE")
        return self


class NativeFurnaceBase(Strict):
    policy: Literal["thermal1192-native-furnace-phases/1"]
    transaction_id: Id
    dimension: Name
    position: list[int] = Field(min_length=3, max_length=3)
    block_id: Literal["thermal:machine_furnace"]
    score_eligible: Literal[False]
    recipe_registration_bound: Literal[False]
    loaded_code_authenticated: Literal[False]

    @field_validator("score_eligible", "recipe_registration_bound", "loaded_code_authenticated", mode="before")
    @classmethod
    def no_authority(cls, value):
        require(value is False, "MACHINE_CAPTURE_AUTHORITY")
        return value

    @model_validator(mode="after")
    def position_bounds(self):
        require(all(-(2**31) <= n < 2**31 for n in self.position), "MACHINE_CAPTURE_POSITION")
        return self


class NativeFurnaceCompletion(NativeFurnaceBase):
    resolved_recipe: ResolvedFurnaceRecipe
    states: list[FurnaceState] = Field(min_length=3, max_length=3)

    @model_validator(mode="after")
    def profile(self):
        require(all(s.process <= 0 and not any(a.count for a in s.augments)
                    and all(item.components_empty for item in s.slots + s.augments)
                    for s in self.states), "MACHINE_CAPTURE_PROFILE")
        return self


class NativeFurnaceRefusal(NativeFurnaceBase):
    reason: Literal["native_validation_failed", "native_profile_unsupported"]


PAYLOADS = {"machine_completion": NativeFurnaceCompletion,
            "machine_capture_refused": NativeFurnaceRefusal}


def require_capture_scope(event, supported):
    require(supported and event.kind in KINDS and event.payload_schema == KINDS[event.kind]
            and not event.actor_ids and not event.is_example and not event.evidence_refs,
            "MACHINE_CAPTURE_SCOPE")
    return PAYLOADS[event.kind].model_validate(event.payload)
