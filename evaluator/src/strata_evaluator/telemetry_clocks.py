"""Terminal native callback clocks; admission/active-time authority is separate."""

from typing import Annotated, Literal

from pydantic import Field, model_validator

from mcbench.contracts import Strict, UInt
from mcbench.storage import require

POLICY = "server-event-monotonic-cumulative/1"
AvatarUuid = Annotated[str, Field(pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")]


class ServerClock(Strict):
    policy: Literal["server-event-monotonic-cumulative/1"]
    origin: Literal["server_started_callback"]
    boundary: Literal["server_stopped_callback"]
    elapsed_wall_ns: UInt
    completed_server_ticks: UInt
    observed_tick_work_ns: UInt
    avatar_tick_events: dict[AvatarUuid, UInt] = Field(max_length=64)

    @model_validator(mode="after")
    def bounds(self):
        require(self.observed_tick_work_ns <= self.elapsed_wall_ns
                and all(0 < value <= self.completed_server_ticks for value in self.avatar_tick_events.values()),
                "TELEMETRY_CLOCK_BOUNDS")
        return self


def reconcile_clock(clock, *, final_tick, sampled_ticks, sampled_wall_ns, sampled_work_ns):
    require(clock.completed_server_ticks == final_tick >= sampled_ticks
            and clock.elapsed_wall_ns >= sampled_wall_ns
            and clock.observed_tick_work_ns >= sampled_work_ns, "TELEMETRY_CLOCK_MISMATCH")
    return {**clock.model_dump(), "ticks_after_last_health_sample": final_tick - sampled_ticks,
            "wall_outside_health_samples_ns": clock.elapsed_wall_ns - sampled_wall_ns,
            "active_time_qualified": False, "pre_startup_time_included": False,
            "post_stop_callback_time_included": False, "avatar_roster_mapping_qualified": False}
