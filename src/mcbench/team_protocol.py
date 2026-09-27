"""Public scoped team requests and private declared communication policy."""

from typing import Annotated, Literal

from pydantic import Field, field_validator

from .contracts import Id, Positive, Strict, UInt, Utc


class TeamPolicy(Strict):
    schema_: Literal["strata/CommunicationPolicy/1"] = Field(alias="schema")
    is_example: bool
    mode: Literal["disabled", "campaign_roster"]
    max_body_bytes: Literal[4096]
    sends_per_minute: Literal[10]
    queue_limit: Literal[100]
    max_ttl_s: Literal[600]
    helper_access: Literal[False]

    @field_validator(
        "max_body_bytes", "sends_per_minute", "queue_limit", "max_ttl_s", mode="before"
    )
    @classmethod
    def exact_integer(cls, value):
        if type(value) is not int:
            raise ValueError("policy limits must be integers")
        return value

    @field_validator("helper_access", mode="before")
    @classmethod
    def no_helper_access(cls, value):
        if value is not False:
            raise ValueError("helper access must be false")
        return value


class TeamSend(Strict):
    kind: Literal["send"]
    message_id: Id
    recipients: list[Id] = Field(min_length=1, max_length=128)
    body: str = Field(min_length=1, max_length=4096)
    ttl_s: Annotated[int, Field(ge=1, le=600)]

    @field_validator("body")
    @classmethod
    def utf8_size(cls, value):
        if len(value.encode("utf-8")) > 4096:
            raise ValueError("message exceeds UTF-8 byte limit")
        return value

    @field_validator("recipients")
    @classmethod
    def unique_recipients(cls, value):
        if len(set(value)) != len(value):
            raise ValueError("duplicate recipients")
        return value


class TeamReceive(Strict):
    kind: Literal["receive"]
    after: UInt
    limit: Annotated[int, Field(ge=1, le=100)]
    acknowledge: list[Id] = Field(max_length=100)

    @field_validator("acknowledge")
    @classmethod
    def unique_acknowledgements(cls, value):
        if len(set(value)) != len(value):
            raise ValueError("duplicate acknowledgements")
        return value


class TeamRequest(Strict):
    schema_: Literal["strata/TeamRequest/1"] = Field(alias="schema")
    request_id: Id
    campaign_id: Id
    agent_id: Id
    epoch: Positive
    deadline_at: Utc
    operation: Annotated[TeamSend | TeamReceive, Field(discriminator="kind")]


class TeamSent(Strict):
    kind: Literal["sent"]
    message_id: Id
    sender_seq: Positive
    expires_unix_ms: UInt


class TeamMessage(Strict):
    id: Id
    sender: Id
    sender_seq: Positive
    body: str = Field(min_length=1, max_length=4096)
    expires_unix_ms: UInt
    cursor: Positive

    @field_validator("body")
    @classmethod
    def utf8_size(cls, value):
        return TeamSend.utf8_size(value)


class TeamReceived(Strict):
    kind: Literal["received"]
    messages: list[TeamMessage] = Field(max_length=100)
    next_cursor: UInt
    has_more: bool


class TeamResponse(Strict):
    schema_: Literal["strata/TeamResponse/1"] = Field(alias="schema")
    request_id: Id
    result: Annotated[TeamSent | TeamReceived, Field(discriminator="kind")]
