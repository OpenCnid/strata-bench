"""Native point observations, never a substitute for fixture/isolation proof."""

from typing import Annotated, Literal
from pydantic import Field, StringConstraints, model_validator
from mcbench.contracts import Digest, Id, Strict, UInt
from mcbench.storage import require

POLICY = "native-e9e-setup-observation/1"
PINS = {
    "ftbteams": "2233122cfddfccafd5f4840ae63a556edd7088ad15e177fb1288367adef142f7",
    "kubejs": "d9bc8bcca17fea536462a8471a2880adabc76ef8bdd84a93ad0b682a960ea5c7",
    "rhino": "0dc7db781fa9609d08932533661683a9686608b088a65f6b62bbd48ffd1316f8",
}
UUID = Annotated[
    str,
    StringConstraints(pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"),
]
Mode = Literal["survival", "creative", "adventure", "spectator"]


class SetupSupport(Strict):
    status: Literal["supported", "unsupported"]
    artifacts: dict[str, Digest | None]

    @model_validator(mode="after")
    def pinned(self):
        require(set(self.artifacts) == set(PINS), "SETUP_SUPPORT_INVALID")
        require((self.status == "supported") == (self.artifacts == PINS), "SETUP_SUPPORT_INVALID")
        return self


class Unavailable(Strict):
    status: Literal["unavailable"]
    error_code: Literal[
        "SETUP_ARTIFACT_UNSUPPORTED",
        "SETUP_MODE_VALUE",
        "SETUP_MODE_UNAVAILABLE",
        "SETUP_TEAM_QUOTA",
        "SETUP_TEAM_MANAGER",
        "SETUP_TEAM_MISSING",
        "SETUP_TEAM_UNAVAILABLE",
    ]


class PackMode(Strict):
    status: Literal["observed"]
    mode: Literal["normal", "expert"]
    is_expert: bool
    is_normal: bool
    startup_errors: UInt
    server_errors: UInt


class ManagerReady(Strict):
    status: Literal["manager_ready"]


class Team(Strict):
    status: Literal["observed"]
    team_id: UUID
    team_type: Literal["PLAYER", "PARTY", "SERVER"]
    actor_rank: Literal["ENEMY", "NONE", "ALLY", "INVITED", "MEMBER", "OFFICER", "OWNER"]
    member_ids: list[UUID] = Field(max_length=128)

    @model_validator(mode="after")
    def unique(self):
        require(self.member_ids == sorted(set(self.member_ids)), "SETUP_TEAM_MEMBERS_INVALID")
        return self


class Actor(Strict):
    uuid: UUID
    game_mode: Mode
    is_operator: bool


class ServerFacts(Strict):
    default_game_mode: Mode
    world_game_mode: Mode
    difficulty: Literal["peaceful", "easy", "normal", "hard"]
    hardcore: bool
    world_allows_commands: bool
    command_blocks_enabled: bool
    rcon_enabled: bool
    operator_levels: list[Annotated[int, Field(ge=0, le=4)]] = Field(max_length=128)
    command_events_seen: UInt


class SetupSnapshot(Strict):
    policy: Literal["native-e9e-setup-observation/1"]
    phase: Literal["startup", "craft_begin", "craft_end"]
    transaction_id: Id | None
    server: ServerFacts
    pack: Annotated[PackMode | Unavailable, Field(discriminator="status")]
    team: Annotated[Team | ManagerReady | Unavailable, Field(discriminator="status")]
    actor: Actor | None

    @model_validator(mode="after")
    def scoped(self):
        require(
            (self.phase == "startup") == (self.transaction_id is None and self.actor is None),
            "SETUP_SNAPSHOT_SCOPE",
        )
        if self.phase != "startup":
            require(
                self.transaction_id is not None
                and self.actor is not None
                and not isinstance(self.team, ManagerReady),
                "SETUP_SNAPSHOT_SCOPE",
            )
        else:
            require(not isinstance(self.team, Team), "SETUP_SNAPSHOT_SCOPE")
        return self


def qualify_points(startup, before, after, *, actor, expected_team, expert):
    """Return named failures; point agreement never grants setup-validity credit."""
    reasons = []
    if not isinstance(startup.team, ManagerReady):
        reasons.append("startup:team_manager_unavailable")
    for label, point in (("startup", startup), ("before", before), ("after", after)):
        if (
            not isinstance(point.pack, PackMode)
            or point.pack.mode != ("expert" if expert else "normal")
            or (
                point.pack.is_expert != expert
                or point.pack.is_normal == expert
                or point.pack.startup_errors
                or point.pack.server_errors
            )
        ):
            reasons.append(f"{label}:pack_mode_unproven")
        server = point.server
        if (
            server.default_game_mode != "survival"
            or server.world_game_mode != "survival"
            or (
                server.world_allows_commands
                or server.command_blocks_enabled
                or server.rcon_enabled
                or server.operator_levels
                or server.command_events_seen
            )
        ):
            reasons.append(f"{label}:admin_or_mode_exposure")
    for label, point in (("before", before), ("after", after)):
        if (
            point.actor.uuid != actor
            or point.actor.game_mode != "survival"
            or point.actor.is_operator
        ):
            reasons.append(f"{label}:actor_privilege")
        if (
            not isinstance(point.team, Team)
            or point.team.team_id != expected_team
            or (
                actor not in point.team.member_ids
                or point.team.actor_rank not in {"MEMBER", "OFFICER", "OWNER"}
            )
        ):
            reasons.append(f"{label}:team_unproven")
    if before.team != after.team or before.server != after.server or before.pack != after.pack:
        reasons.append("point_state_changed")
    return {
        "native_points_match": not reasons,
        "reasons": reasons,
        "continuous_history_proven": False,
        "setup_mechanics_qualified": False,
        "scoring_eligible": False,
    }
