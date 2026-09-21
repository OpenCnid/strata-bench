"""Private sticky mutation observations; incomplete route coverage earns no score."""

from typing import Literal

from pydantic import model_validator

from mcbench.contracts import Id, Strict, UInt
from mcbench.storage import require

POLICY = "native-e9e-setup-mutation-watch/1"
ROUTES = frozenset({
    "command_attempt", "actor_mode_change", "operator_add", "operator_remove", "operator_reload",
    "allow_cheats", "world_mode", "world_difficulty", "team_deserialize", "party_change",
    "team_create", "team_reload", "native_stop_command",
})


class HistorySupport(Strict):
    policy: Literal["native-e9e-setup-mutation-watch/1"]
    vanilla_hooks_verified: bool
    team_hooks_verified: bool
    all_mutation_routes_covered: Literal[False]


class SetupHistory(Strict):
    policy: Literal["native-e9e-setup-mutation-watch/1"]
    phase: Literal["startup", "craft_begin", "craft_end", "stop"]
    transaction_id: Id | None
    attempts: dict[str, UInt]
    off_thread_attempts: UInt
    overflowed: bool

    @model_validator(mode="after")
    def scoped(self):
        require(set(self.attempts) == ROUTES, "SETUP_HISTORY_ROUTES")
        require((self.phase in {"startup", "stop"}) == (self.transaction_id is None),
                "SETUP_HISTORY_SCOPE")
        require(self.off_thread_attempts <= sum(self.attempts.values()), "SETUP_HISTORY_COUNTER")
        return self


def advance(previous, current):
    if previous is not None:
        require(all(current.attempts[key] >= previous.attempts[key] for key in ROUTES)
                and current.off_thread_attempts >= previous.off_thread_attempts
                and (not previous.overflowed or current.overflowed), "SETUP_HISTORY_ROLLBACK")


def qualify_history(support, terminal):
    """Any observed attempt taints the whole reference, even if later reversed."""
    normal_stop = (terminal.attempts["command_attempt"] == terminal.attempts["native_stop_command"] == 1)
    reasons = [f"observed:{key}" for key in sorted(ROUTES) if terminal.attempts[key]
               and not (normal_stop and key in {"command_attempt", "native_stop_command"})]
    if not support.vanilla_hooks_verified or not support.team_hooks_verified:
        reasons.append("mutation_hooks_unavailable")
    if terminal.off_thread_attempts:
        reasons.append("off_thread_mutation_attempt")
    if terminal.overflowed:
        reasons.append("mutation_counter_overflow")
    return {"policy": POLICY, "observed_history_clear": not reasons, "reasons": reasons,
            "single_native_stop_command": normal_stop,
            "terminal": terminal.model_dump(), "support": support.model_dump(),
            "continuous_history_proven": False, "scoring_eligible": False}
