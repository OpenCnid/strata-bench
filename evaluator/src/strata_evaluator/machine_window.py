"""Prior-declared private operating windows; producer/setup/team authority is separate."""

from typing import Annotated, Literal

from pydantic import Field, model_validator

from mcbench.contracts import Strict, UInt
from mcbench.storage import Fault, digest, require

from .machine_energy import qualify_tick
from .machine_interval import MAX_TICKS, qualify_window
from .machine_transitions import qualify_transition


class WindowBase(Strict):
    minimum_ticks: int = Field(ge=1, le=MAX_TICKS)
    minimum_net_energy_rf: int = Field(ge=1, le=2**63 - 1)


class FirstEpisode(WindowBase):
    selector: Literal["first-start-through-first-refund/1"]


class ExactWindow(WindowBase):
    selector: Literal["exact-inclusive-ticks/1"]
    start_server_tick: UInt
    end_server_tick: UInt

    @model_validator(mode="after")
    def bounded(self):
        require(
            0 < self.end_server_tick - self.start_server_tick + 1 <= MAX_TICKS
            and self.minimum_ticks <= self.end_server_tick - self.start_server_tick + 1,
            "MACHINE_OPERATING_BOUNDS",
        )
        return self


OperatingWindow = Annotated[FirstEpisode | ExactWindow, Field(discriminator="selector")]


def registered_recipe(captured, target):
    registration = captured.registration
    recipe = target.recipes.get(registration.source_recipe_id)
    require(recipe is not None, "MACHINE_UNREGISTERED_RECIPE")
    require(
        registration.origin == target.registration_origin
        and registration.machine_recipe_id == target.machine_recipe_ids[recipe.recipe_id],
        "MACHINE_REGISTRATION_MISMATCH",
    )
    resolved = captured.resolved_recipe
    require(
        resolved.input == recipe.input
        and resolved.output == recipe.output
        and resolved.resolved_input_count == recipe.input.count
        and resolved.output_chance == recipe.output_chance
        and resolved.recipe_energy_rf == recipe.recipe_energy_rf,
        "MACHINE_REGISTERED_RECIPE_MISMATCH",
    )
    return recipe


def qualify_operating_window(plan, target_id, intervals, children, accepted_resources):
    """Recompute from complete-stream verified traces, never caller score counters.

    The raw inspector proves selection and resource math only. The sealed store
    must independently bind this plan before launch; neither API grants a score.
    """
    target, window = plan.targets[target_id], plan.operating_windows[target_id]
    selected = [
        (e, c)
        for e, c in children.values()
        if (c.dimension, c.position, c.block_id)
        == (target.dimension, target.position, target.block_id)
        and plan.start_server_tick <= e.server_tick <= plan.cutoff_server_tick
    ]
    starts = [(e, c) for e, c in selected if getattr(c, "operation", None) == "start"]
    require(starts, "MACHINE_OPERATING_START_MISSING")
    if isinstance(window, FirstEpisode):
        first_event, first_start = starts[0]  # Never search for a later successful episode.
        refunds = [
            (e, c)
            for e, c in selected
            if e.seq > first_event.seq and getattr(c, "operation", None) == "refund"
        ]
        require(refunds, "MACHINE_OPERATING_REFUND_MISSING")
        start_tick, end_tick = first_event.server_tick, refunds[0][0].server_tick
    else:
        start_tick, end_tick = window.start_server_tick, window.end_server_tick
        starts = [(e, c) for e, c in starts if start_tick <= e.server_tick <= end_tick]
        require(starts, "MACHINE_OPERATING_START_MISSING")
        first_event, first_start = starts[0]
    origins = [v for v in intervals["accepted"] if first_start.transaction_id in v["child_ids"]]
    require(len(origins) == 1, "MACHINE_OPERATING_START_UNJOINED")
    lifetime = origins[0]["lifetime_id"]
    sampled = qualify_window(intervals, lifetime, start_tick, end_tick)
    require(not sampled["external_resource_changes"], "MACHINE_OPERATING_EXTERNAL_RESOURCE")
    rows = [
        v
        for v in intervals["accepted"]
        if v["lifetime_id"] == lifetime and start_tick <= v["server_tick"] <= end_tick
    ]
    require(len(rows) >= window.minimum_ticks, "MACHINE_OPERATING_DURATION")
    before, after = rows[0]["before"], rows[-1]["after"]
    require(
        not before["active"]
        and before["process"] == 0
        and not after["active"]
        and after["process"] == 0,
        "MACHINE_OPERATING_PARTIAL_EPISODE",
    )
    joined = [cid for row in rows for cid in row["child_ids"]]
    scoped = [(e, c) for e, c in selected if start_tick <= e.server_tick <= end_tick]
    require(
        joined == [c.transaction_id for _, c in scoped] and len(joined) == len(set(joined)),
        "MACHINE_OPERATING_CHILD_SCOPE",
    )
    resources = {
        v["witness"]["transaction_id"]: v["witness"]
        for v in accepted_resources
        if v["target_id"] == target_id
    }
    debit = refund = output = recipe_energy = starts_count = completions = refunds_count = 0
    current = None
    consumed, produced, receipts = {}, {}, []
    by_id = {c.transaction_id: (e, c) for e, c in scoped}
    for row in rows:
        tick_work = 0
        for cid in row["child_ids"]:
            event, captured = by_id[cid]
            require(not event.kind.endswith("_refused"), "MACHINE_OPERATING_NATIVE_REFUSED")
            if event.kind == "machine_process_transition" and captured.operation == "refund":
                require(
                    current is None and completions > 0 and cid == joined[-1],
                    "MACHINE_OPERATING_CYCLE_ORDER",
                )
                witness = qualify_transition(event, captured)
                require(
                    witness["requested_refund_rf"] == witness["energy_refunded_rf"],
                    "MACHINE_OPERATING_REFUND_CLAMPED",
                )
                refund += witness["energy_refunded_rf"]
                refunds_count += 1
            else:
                recipe = registered_recipe(captured, target)
                identity = (
                    captured.registration.model_dump(),
                    captured.resolved_recipe.model_dump(),
                )
                if event.kind == "machine_process_transition":
                    require(
                        captured.operation == "start" and current is None,
                        "MACHINE_OPERATING_CYCLE_ORDER",
                    )
                    qualify_transition(event, captured)
                    current = identity
                    starts_count += 1
                else:
                    require(current == identity, "MACHINE_OPERATING_RECIPE_CONTINUITY")
                    if event.kind == "machine_process_tick":
                        witness = qualify_tick(event, captured)
                        require(
                            witness["did_work"] and witness["fully_funded"],
                            "MACHINE_OPERATING_UNFUNDED_TICK",
                        )
                        debit += witness["energy_debited_rf"]
                        tick_work += 1
                    else:
                        require(
                            event.kind == "machine_completion" and cid in resources,
                            "MACHINE_OPERATING_RESOURCE_UNPROVEN",
                        )
                        witness = resources[cid]
                        require(
                            witness["source_event_digests"] == [digest(event.model_dump())],
                            "MACHINE_OPERATING_RESOURCE_CHANGED",
                        )
                        for name, amount in witness["consumed"].items():
                            consumed[name] = consumed.get(name, 0) + amount
                        for name, amount in witness["produced"].items():
                            produced[name] = produced.get(name, 0) + amount
                        output += sum(witness["produced"].values())
                        recipe_energy += recipe.recipe_energy_rf
                        completions += 1
                        current = None
            receipts.append(digest(event.model_dump()))
        require(tick_work == 1, "MACHINE_OPERATING_IDLE_TICK")
    require(
        current is None and starts_count == completions and refunds_count == 1,
        "MACHINE_OPERATING_PARTIAL_EPISODE",
    )
    net = debit - refund
    require(
        net == recipe_energy == before["energy_rf"] - after["energy_rf"]
        and net >= window.minimum_net_energy_rf,
        "MACHINE_OPERATING_NET_ENERGY",
    )
    require(output >= target.minimum_output, "MACHINE_OPERATING_OUTPUT")
    # No existing/gifted contents are credited: endpoint deltas must equal only
    # the joined, independently registered completion witnesses.
    for slot, expected, sign in ((0, consumed, 1), (1, produced, -1)):
        deltas = {}
        for state, factor in ((before, sign), (after, -sign)):
            stack = state["slots"][slot]
            if stack["count"]:
                deltas[stack["item_id"]] = deltas.get(stack["item_id"], 0) + factor * stack["count"]
        require(
            {k: v for k, v in deltas.items() if v} == expected, "MACHINE_OPERATING_RESOURCE_BALANCE"
        )
    return {
        "policy": "thermal1192-private-operating-window/1",
        "target_id": target_id,
        "selection_digest": digest(window.model_dump()),
        "sampled_window": sampled,
        "candidate_output": output,
        "completed_cycles": completions,
        "energy_debited_rf": debit,
        "energy_refunded_rf": refund,
        "net_energy_consumed_rf": net,
        "consumed": consumed,
        "produced": produced,
        "child_event_digests": receipts,
        "prior_registration_verified": False,
        "setup_team_qualified": False,
        "loaded_code_authenticated": False,
        "fluid_provenance_qualified": False,
        "scoring_eligible": False,
    }


def inspect_operating_windows(plan, intervals, children, accepted_resources):
    require(intervals is not None, "MACHINE_OPERATING_PROFILE")
    result = {}
    for target in plan.targets:
        try:
            witness = qualify_operating_window(
                plan, target, intervals, children, accepted_resources
            )
            result[target] = {
                "candidate_complete": True,
                "candidate_output": witness["candidate_output"],
                "witness": witness,
                "reason": None,
            }
        except Fault as error:
            result[target] = {
                "candidate_complete": False,
                "candidate_output": 0,
                "witness": None,
                "reason": error.code,
            }
    return {
        "policy": "thermal1192-private-operating-window/1",
        "targets": result,
        "prior_registration_verified": False,
        "scoring_eligible": False,
    }
