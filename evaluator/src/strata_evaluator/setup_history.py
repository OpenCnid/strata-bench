"""Private sticky mutation observations; incomplete route coverage earns no score."""

from typing import ClassVar, Literal

from pydantic import model_validator

from mcbench.contracts import Id, Strict, UInt
from mcbench.storage import require

POLICY = "native-e9e-setup-mutation-watch/1"
POLICY_V2 = "native-e9e-setup-mutation-watch/2"
POLICY_V3 = "native-e9e-setup-mutation-watch/3"
POLICY_V4 = "native-e9e-setup-mutation-watch/4"
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
    routes: ClassVar[frozenset[str]] = ROUTES
    policy: Literal["native-e9e-setup-mutation-watch/1"]
    phase: Literal["startup", "craft_begin", "craft_end", "stop"]
    transaction_id: Id | None
    attempts: dict[str, UInt]
    off_thread_attempts: UInt
    overflowed: bool

    @model_validator(mode="after")
    def scoped(self):
        require(set(self.attempts) == self.routes, "SETUP_HISTORY_ROUTES")
        require((self.phase in {"startup", "stop"}) == (self.transaction_id is None),
                "SETUP_HISTORY_SCOPE")
        require(self.off_thread_attempts <= sum(self.attempts.values()), "SETUP_HISTORY_COUNTER")
        return self


class HistorySupportV2(HistorySupport):
    policy: Literal["native-e9e-setup-mutation-watch/2"]
    global_map_hooks_verified: bool


class SetupHistoryV2(SetupHistory):
    policy: Literal["native-e9e-setup-mutation-watch/2"]
    routes: ClassVar[frozenset[str]] = ROUTES | {"global_mode_write"}


class HistorySupportV3(HistorySupportV2):
    policy: Literal["native-e9e-setup-mutation-watch/3"]
    team_map_hooks_verified: bool


class SetupHistoryV3(SetupHistoryV2):
    policy: Literal["native-e9e-setup-mutation-watch/3"]
    routes: ClassVar[frozenset[str]] = SetupHistoryV2.routes | {"team_map_write"}


class HistorySupportV4(HistorySupportV3):
    policy: Literal["native-e9e-setup-mutation-watch/4"]
    script_field_hooks_verified: bool


class SetupHistoryV4(SetupHistoryV3):
    policy: Literal["native-e9e-setup-mutation-watch/4"]
    routes: ClassVar[frozenset[str]] = SetupHistoryV3.routes | {"team_script_field_write", "script_reflection_overflow"}


HISTORY_MODELS = {POLICY: SetupHistory, POLICY_V2: SetupHistoryV2, POLICY_V3: SetupHistoryV3, POLICY_V4: SetupHistoryV4}
HISTORY_SCHEMAS = {POLICY: "strata/NativeSetupHistory/1", POLICY_V2: "strata/NativeSetupHistory/2",
                   POLICY_V3: "strata/NativeSetupHistory/3", POLICY_V4: "strata/NativeSetupHistory/4"}


def parse_history(value):
    return HISTORY_MODELS.get(value.get("policy"), SetupHistory).model_validate(value)


def advance(previous, current):
    if previous is not None:
        require(previous.policy == current.policy and
                all(current.attempts[key] >= previous.attempts[key] for key in current.routes)
                and current.off_thread_attempts >= previous.off_thread_attempts
                and (not previous.overflowed or current.overflowed), "SETUP_HISTORY_ROLLBACK")


def qualify_history(support, terminal):
    """Any observed attempt taints the whole reference, even if later reversed."""
    normal_stop = (terminal.attempts["command_attempt"] == terminal.attempts["native_stop_command"] == 1)
    require(support.policy == terminal.policy, "SETUP_HISTORY_POLICY")
    reasons = [f"observed:{key}" for key in sorted(terminal.routes) if terminal.attempts[key]
               and not (normal_stop and key in {"command_attempt", "native_stop_command"})]
    if not support.vanilla_hooks_verified or not support.team_hooks_verified:
        reasons.append("mutation_hooks_unavailable")
    if isinstance(support, HistorySupportV2) and not support.global_map_hooks_verified:
        reasons.append("global_map_hook_unavailable")
    if isinstance(support, HistorySupportV3) and not support.team_map_hooks_verified:
        reasons.append("team_map_hook_unavailable")
    if isinstance(support, HistorySupportV4) and not support.script_field_hooks_verified:
        reasons.append("script_field_hook_unavailable")
    if terminal.off_thread_attempts:
        reasons.append("off_thread_mutation_attempt")
    if terminal.overflowed:
        reasons.append("mutation_counter_overflow")
    return {"policy": terminal.policy, "observed_history_clear": not reasons, "reasons": reasons,
            "single_native_stop_command": normal_stop,
            "terminal": terminal.model_dump(), "support": support.model_dump(),
            "continuous_history_proven": False, "scoring_eligible": False}
