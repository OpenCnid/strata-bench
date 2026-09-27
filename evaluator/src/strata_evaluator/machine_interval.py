"""Native per-object tick traces. Fixture/team/loaded-code authority is separate."""

from typing import Annotated, Literal

from pydantic import Field, model_validator

from mcbench.contracts import Id, Positive, Strict, UInt
from mcbench.storage import Fault, digest, require

from .machine_capture import NativeFurnaceBase
from .machine_energy import qualify_tick
from .machine_transitions import TransitionState, qualify_transition
from .machine_witness import require_furnace_deltas

POLICY = "thermal1192-native-furnace-server-tick/1"
KINDS = {
    "machine_server_tick": "strata/NativeFurnaceServerTick/1",
    "machine_server_tick_refused": "strata/NativeFurnaceServerTickRefusal/1",
    "machine_lifetime_end": "strata/NativeFurnaceLifetimeEnd/1",
}
MAX_TICKS = 16384
MAX_LIFETIMES = 64


class Child(Strict):
    kind: Literal["child"]
    transaction_id: Id


class Stage(Strict):
    kind: Literal["stage"]
    stage: Literal["transfer_input", "transfer_output", "charge", "off", "activate"]
    states: list[TransitionState] = Field(min_length=2, max_length=2)


class LifetimeBase(NativeFurnaceBase):
    policy: Literal["thermal1192-native-furnace-server-tick/1"]
    lifetime_id: Id
    ordinal: Positive
    world_tick: UInt


class TickBase(LifetimeBase):
    child_ids: list[Id] = Field(max_length=4)

    @model_validator(mode="after")
    def unique(self):
        require(len(set(self.child_ids)) == len(self.child_ids), "MACHINE_INTERVAL_DUPLICATE_CHILD")
        return self


class ServerTick(TickBase):
    states: list[TransitionState] = Field(min_length=2, max_length=2)
    steps: list[Annotated[Child | Stage, Field(discriminator="kind")]] = Field(
        min_length=1, max_length=10
    )

    @model_validator(mode="after")
    def references(self):
        require(
            [s.transaction_id for s in self.steps if isinstance(s, Child)] == self.child_ids,
            "MACHINE_INTERVAL_CHILD_ORDER",
        )
        require(
            isinstance(self.steps[-1], Stage)
            and self.steps[-1].stage == "charge"
            and sum(isinstance(s, Stage) and s.stage == "charge" for s in self.steps) == 1,
            "MACHINE_INTERVAL_CHARGE_BOUNDARY",
        )
        return self


class TickRefusal(TickBase):
    reason: Literal["native_profile_unsupported"]


class LifetimeEnd(LifetimeBase):
    reason: Literal["removed", "unloaded", "reactivated"]


def parse_interval(event, supported):
    require(
        supported
        and event.kind in KINDS
        and event.payload_schema == KINDS[event.kind]
        and not event.is_example
        and not event.actor_ids
        and not event.evidence_refs,
        "MACHINE_INTERVAL_SCOPE",
    )
    model = {
        "machine_server_tick": ServerTick,
        "machine_server_tick_refused": TickRefusal,
        "machine_lifetime_end": LifetimeEnd,
    }[event.kind]
    return model.model_validate(event.payload)


def scope(event, captured):
    return (
        event.campaign_id,
        event.epoch,
        event.server_boot_id,
        captured.dimension,
        tuple(captured.position),
        captured.block_id,
    )


def trace_tick(event, captured, children):
    """Join every sampled stage; validate child math without inventing a recipe plan."""
    labels = []
    for step in captured.steps:
        if isinstance(step, Stage):
            labels.append(step.stage)
        else:
            e, c = children[step.transaction_id]
            labels.append(
                "process_tick"
                if e.kind == "machine_process_tick"
                else "completion"
                if e.kind == "machine_completion"
                else c.operation
                if e.kind == "machine_process_transition"
                else "refused"
            )
    if captured.states[0].active:
        allowed = [
            ["process_tick", "charge"],
            ["process_tick", "off", "charge"],
            ["process_tick", "completion", "transfer_output", "transfer_input", "start", "charge"],
            [
                "process_tick",
                "completion",
                "transfer_output",
                "transfer_input",
                "refund",
                "off",
                "charge",
            ],
        ]
    else:
        allowed = [
            prefix + suffix
            for prefix in ([], ["transfer_output", "transfer_input"])
            for suffix in (["charge"], ["start", "process_tick", "activate", "charge"])
        ]
    require(labels in allowed, "MACHINE_INTERVAL_NATIVE_ORDER")
    state = captured.states[0].model_dump()
    external = False
    for step in captured.steps:
        if isinstance(step, Stage):
            before, after = (s.model_dump() for s in step.states)
            require(before == state, "MACHINE_INTERVAL_TRACE_GAP")
            if step.stage in {"activate", "off"}:
                expected = before | (
                    {"active": True}
                    if step.stage == "activate"
                    else {"process": 0, "active": False}
                )
                require(after == expected, "MACHINE_INTERVAL_CONTROL_CHANGE")
            elif after != before:
                external = True
        else:
            child_event, child = children[step.transaction_id]
            require(not child_event.kind.endswith("_refused"), "MACHINE_INTERVAL_CHILD_REFUSED")
            if child_event.kind == "machine_process_tick":
                qualify_tick(child_event, child)
            elif child_event.kind == "machine_process_transition":
                qualify_transition(child_event, child)
            else:
                require(
                    child_event.kind == "machine_completion"
                    and child.resolved_recipe.resolved_input_count
                    == child.resolved_recipe.input.count,
                    "MACHINE_INTERVAL_COMPLETION",
                )
                # Shared resource arithmetic only, against the native resolved
                # facts. The independent prelaunch recipe plan is still required.
                require_furnace_deltas(tuple(child.states), child.resolved_recipe)
            before, after = child.states[0].model_dump(), child.states[-1].model_dump()
            require(all(state[k] == v for k, v in before.items()), "MACHINE_INTERVAL_TRACE_GAP")
            after = state | after
        state = after
    require(state == captured.states[-1].model_dump(), "MACHINE_INTERVAL_TRACE_GAP")
    return {
        "source_seq": event.seq,
        "source_event_digest": digest(event.model_dump()),
        "server_tick": event.server_tick,
        "world_tick": captured.world_tick,
        "lifetime_id": captured.lifetime_id,
        "ordinal": captured.ordinal,
        "transaction_id": captured.transaction_id,
        "scope": [
            event.campaign_id,
            event.epoch,
            event.server_boot_id,
            captured.dimension,
            captured.position,
            captured.block_id,
        ],
        "before": captured.states[0].model_dump(),
        "after": captured.states[-1].model_dump(),
        "child_ids": captured.child_ids,
        "external_resource_changes": external,
        "tick_trace_complete": True,
        "scoring_eligible": False,
    }


class IntervalInspection:
    def __init__(self):
        self.pending = {}
        self.lifetimes = {}
        self.locations = {}
        self.accepted, self.rejected, self.ends = [], [], []
        self.ticks = 0

    def child(self, event, captured):
        require(
            len(self.pending) < 4 and captured.transaction_id not in self.pending,
            "MACHINE_INTERVAL_CHILD_QUOTA",
        )
        self.pending[captured.transaction_id] = (event, captured)

    def observe(self, event, captured):
        key, identity = captured.lifetime_id, scope(event, captured)
        prior = self.lifetimes.get(key)
        if isinstance(captured, LifetimeEnd):
            require(
                not self.pending
                and prior is not None
                and not prior[3]
                and prior[0] == identity
                and prior[1].ordinal == captured.ordinal
                and event.server_tick >= prior[2]
                and captured.world_tick >= prior[1].world_tick,
                "MACHINE_LIFETIME_END",
            )
            self.lifetimes[key] = (*prior[:3], True)
            self.locations.pop(identity)
            self.ends.append(
                {
                    "source_seq": event.seq,
                    "lifetime_id": key,
                    "reason": captured.reason,
                    "server_tick": event.server_tick,
                    "world_tick": captured.world_tick,
                    "ordinal": captured.ordinal,
                    "source_event_digest": digest(event.model_dump()),
                }
            )
            return
        require(self.ticks < MAX_TICKS, "MACHINE_INTERVAL_QUOTA")
        self.ticks += 1
        if prior is None:
            require(
                len(self.lifetimes) < MAX_LIFETIMES
                and captured.ordinal == 1
                and identity not in self.locations,
                "MACHINE_LIFETIME_START",
            )
        else:
            require(
                not prior[3]
                and prior[0] == identity
                and captured.ordinal == prior[1].ordinal + 1
                and event.server_tick > prior[2]
                and captured.world_tick > prior[1].world_tick,
                "MACHINE_LIFETIME_SEQUENCE",
            )
        require(captured.child_ids == list(self.pending), "MACHINE_INTERVAL_UNJOINED_CHILD")
        for child_event, child in self.pending.values():
            require(
                scope(child_event, child) == identity
                and child_event.server_tick == event.server_tick
                and child_event.seq < event.seq,
                "MACHINE_INTERVAL_CHILD_SCOPE",
            )
        reason = None
        try:
            require(not isinstance(captured, TickRefusal), "MACHINE_INTERVAL_NATIVE_REFUSED")
            witness = trace_tick(event, captured, self.pending)
            if prior is not None:
                require(
                    event.server_tick == prior[2] + 1
                    and captured.world_tick == prior[1].world_tick + 1,
                    "MACHINE_INTERVAL_TICK_GAP",
                )
            self.accepted.append(witness)
        except Fault as error:
            reason = error.code
        if reason:
            self.rejected.append(
                {
                    "source_seq": event.seq,
                    "source_event_digest": digest(event.model_dump()),
                    "lifetime_id": key,
                    "server_tick": event.server_tick,
                    "reason": reason,
                }
            )
        self.pending.clear()
        self.locations[identity] = key
        self.lifetimes[key] = (identity, captured, event.server_tick, False)

    def report(self):
        require(not self.pending, "MACHINE_INTERVAL_ORPHAN_CHILD")
        return {
            "policy": POLICY,
            "accepted": self.accepted,
            "rejected": self.rejected,
            "lifetime_ends": self.ends,
            "lifetimes": len(self.lifetimes),
            "registered_window_qualified": False,
            "setup_team_qualified": False,
            "loaded_code_authenticated": False,
            "scoring_eligible": False,
        }


def qualify_window(report, lifetime_id, start_tick, end_tick):
    """Exact requested bounds only. Caller must separately prove prior registration."""
    require(
        type(start_tick) is int
        and type(end_tick) is int
        and 0 <= start_tick <= end_tick
        and end_tick - start_tick < MAX_TICKS,
        "MACHINE_WINDOW_BOUNDS",
    )
    rows = [
        v
        for v in report["accepted"]
        if v["lifetime_id"] == lifetime_id and start_tick <= v["server_tick"] <= end_tick
    ]
    require(
        not any(
            v["lifetime_id"] == lifetime_id and start_tick <= v["server_tick"] <= end_tick
            for v in report["rejected"]
        ),
        "MACHINE_WINDOW_REJECTED_TICK",
    )
    require(
        not any(
            v["lifetime_id"] == lifetime_id and start_tick <= v["server_tick"] <= end_tick
            for v in report["lifetime_ends"]
        ),
        "MACHINE_WINDOW_RETIRED",
    )
    require(
        [v["server_tick"] for v in rows] == list(range(start_tick, end_tick + 1)),
        "MACHINE_WINDOW_INCOMPLETE",
    )
    for before, after in zip(rows, rows[1:]):
        require(
            after["ordinal"] == before["ordinal"] + 1
            and after["world_tick"] == before["world_tick"] + 1
            and before["scope"] == after["scope"]
            and before["after"] == after["before"],
            "MACHINE_WINDOW_STATE_GAP",
        )
    return {
        "policy": POLICY,
        "lifetime_id": lifetime_id,
        "start_server_tick": start_tick,
        "end_server_tick": end_tick,
        "observed_ticks": len(rows),
        "source_event_digests": [v["source_event_digest"] for v in rows],
        "sampled_lifetime_continuity_verified": True,
        "prior_registration_verified": False,
        "external_resource_changes": any(v["external_resource_changes"] for v in rows),
        "setup_team_qualified": False,
        "loaded_code_authenticated": False,
        "scoring_eligible": False,
    }
