"""Operator-pinned native wire tools; never learn an allowlist from a live request.

This checks the advertised Responses tool projection. Deferred code-mode tools,
their implementations and OS isolation still need bootstrap/canary qualification.
"""

import re
from typing import Annotated, Literal

from pydantic import Field

from .contracts import Digest, Ref, Strict
from .inference_transport import strict_json
from .native_broker_policy import TEAM_POLICY, settings_policy, validate_broker_settings
from .storage import Principal, canonical, digest, require

POLICY = "native-additional-tools-exact/1"
FUNCTIONS = {"exec", "wait", "request_user_input"}
COLLABORATION = {"followup_task", "interrupt_agent", "list_agents", "send_message",
                 "spawn_agent", "wait_agent"}
MAX_PROJECTION_BYTES = 256 * 1024


class NativeToolProjection(Strict):
    schema_: Literal["strata/NativeToolProjection/1"] = Field(alias="schema")
    policy: Literal["native-additional-tools-exact/1"]
    binary_digest: Digest
    binary_version: Annotated[str, Field(min_length=1, max_length=128)]
    dovetail_commit: Annotated[str, Field(pattern=r"^[0-9a-f]{40}$")]
    model: Annotated[str, Field(min_length=1, max_length=128)]
    settings_policy: Literal["native-broker-closed-features-stdio/2"]
    settings_digest: Digest
    executor_ref: Ref
    helper_ref: Ref


class HelperCollaborationProjection(NativeToolProjection):
    schema_: Literal["strata/NativeToolProjection/2"] = Field(alias="schema")
    policy: Literal["native-additional-tools-exact/2"]


class ConformanceHelperProjection(NativeToolProjection):
    """Selected-model conformance only; neither campaign nor M0 spending authority."""

    schema_: Literal["strata/NativeToolProjection/3"] = Field(alias="schema")
    policy: Literal["native-additional-tools-exact/3"]


class TeamConformanceProjection(ConformanceHelperProjection):
    """Explicit additional team facade; historical four-tool profiles stay closed."""

    schema_: Literal["strata/NativeToolProjection/4"] = Field(alias="schema")
    policy: Literal["native-additional-tools-exact/4"]
    settings_policy: Literal["native-broker-closed-features-stdio/3"]


class CampaignTeamProjection(TeamConformanceProjection):
    """Campaign catalog identity; a pin never supplies runtime qualification."""

    schema_: Literal["strata/NativeToolProjection/5"] = Field(alias="schema")
    policy: Literal["native-additional-tools-exact/5"]


def _projection_kind(schema, plan):
    kinds = {
        "strata/NativeToolProjection/1": NativeToolProjection,
        "strata/NativeToolProjection/2": HelperCollaborationProjection,
        "strata/NativeToolProjection/3": ConformanceHelperProjection,
        "strata/NativeToolProjection/4": TeamConformanceProjection,
        "strata/NativeToolProjection/5": CampaignTeamProjection,
    }
    require(isinstance(schema, str) and schema in kinds, "NATIVE_TOOL_PROJECTION_SHAPE")
    require((schema in {"strata/NativeToolProjection/4", "strata/NativeToolProjection/5"}) ==
            (plan.broker_policy == TEAM_POLICY)
            and (plan.broker_policy != TEAM_POLICY or plan.team_policy_ref is not None),
            "NATIVE_TOOL_PROJECTION_SCOPE")
    if schema == "strata/NativeToolProjection/2":
        require(plan.purpose == "development_piloting" and plan.helper_limit == 1
                and plan.model == "gpt-6-luna", "NATIVE_TOOL_PROJECTION_SCOPE")
    if schema in {"strata/NativeToolProjection/3", "strata/NativeToolProjection/4"}:
        require(plan.purpose == "conformance" and type(plan.helper_limit) is int
                and 1 <= plan.helper_limit <= 2 and plan.model == "gpt-6-luna",
                "NATIVE_TOOL_PROJECTION_SCOPE")
    if schema == "strata/NativeToolProjection/5":
        require(plan.purpose == "campaign" and type(plan.helper_limit) is int
                and 1 <= plan.helper_limit <= 2 and plan.model == "gpt-6-luna",
                "NATIVE_TOOL_PROJECTION_SCOPE")
    return kinds[schema]


def _validate_projection(blocks, role, *, helper_collaboration=False):
    require(role in {"executor", "helper"} and isinstance(blocks, list) and len(blocks) == 1,
            "NATIVE_TOOL_PROJECTION_SHAPE")
    block = blocks[0]
    require(isinstance(block, dict) and set(block) == {"type", "role", "tools"} and
            block["type"] == "additional_tools" and block["role"] == "developer",
            "NATIVE_TOOL_PROJECTION_SHAPE")
    namespaces = block["tools"]
    expected = {"functions": FUNCTIONS}
    if role == "executor" or helper_collaboration:
        expected["collaboration"] = COLLABORATION
    require(isinstance(namespaces, list) and len(namespaces) == len(expected),
            "NATIVE_TOOL_PROJECTION_SHAPE")
    seen = set()
    for namespace in namespaces:
        require(isinstance(namespace, dict) and set(namespace) == {
            "type", "name", "description", "tools"} and namespace["type"] == "namespace" and
            isinstance(namespace["name"], str) and namespace["name"] in expected and
            namespace["name"] not in seen and isinstance(namespace["description"], str),
            "NATIVE_TOOL_PROJECTION_SHAPE")
        seen.add(namespace["name"])
        tools, names = namespace["tools"], set()
        require(isinstance(tools, list) and len(tools) == len(expected[namespace["name"]]),
                "NATIVE_TOOL_PROJECTION_SHAPE")
        for tool in tools:
            require(isinstance(tool, dict) and isinstance(tool.get("name"), str) and
                    tool["name"] in expected[namespace["name"]] and tool["name"] not in names and
                    isinstance(tool.get("description"), str), "NATIVE_TOOL_PROJECTION_SHAPE")
            names.add(tool["name"])
            custom = namespace["name"] == "functions" and tool["name"] == "exec"
            require(tool.get("type") == ("custom" if custom else "function") and set(tool) == (
                {"type", "name", "description", "format"} if custom else
                {"type", "name", "description", "strict", "parameters"}) and
                isinstance(tool.get("format" if custom else "parameters"), dict) and
                (custom or type(tool["strict"]) is bool), "NATIVE_TOOL_PROJECTION_SHAPE")
    require(len(canonical(blocks)) <= MAX_PROJECTION_BYTES, "NATIVE_TOOL_PROJECTION_SHAPE")
    return blocks


def request_projection(body, role, *, helper_collaboration=False):
    """Drop only the runtime-generated block ID; preserve all semantic bytes/fields."""
    require(isinstance(body, dict) and "tools" not in body and "functions" not in body and
            isinstance(body.get("input"), list), "NATIVE_TOOL_PROJECTION_SHAPE")
    blocks = [item for item in body["input"] if isinstance(item, dict) and
              item.get("type") == "additional_tools"]
    require(len(blocks) == 1 and isinstance(blocks[0].get("id"), str) and
            re.fullmatch(r"at_[A-Za-z0-9_-]{1,128}", blocks[0]["id"]),
            "NATIVE_TOOL_PROJECTION_SHAPE")
    return _validate_projection([{k: v for k, v in blocks[0].items() if k != "id"}], role,
                                helper_collaboration=helper_collaboration)


def _private_json(cas, ref, limit):
    row = cas.database.connection.execute(
        "SELECT visibility FROM objects WHERE namespace='operator' AND ref=?", (ref,)).fetchone()
    require(row is not None and row[0] == "operator", "NATIVE_TOOL_PROJECTION_PRIVATE")
    return strict_json(cas.read(Principal("operator", "operator"), "operator", ref, max_bytes=limit))


def read_tool_projection(cas, plan):
    require(plan.tool_projection_ref is not None and plan.broker_policy is not None,
            "NATIVE_TOOL_PROJECTION_REQUIRED")
    validate_broker_settings(plan.config_overrides, policy=plan.broker_policy)
    body = _private_json(cas, plan.tool_projection_ref, 16384)
    require(isinstance(body, dict), "NATIVE_TOOL_PROJECTION_SHAPE")
    kind = _projection_kind(body.get("schema"), plan)
    helper_collaboration = kind is not NativeToolProjection
    pin = kind.model_validate(body)
    require(all(getattr(pin, k) == getattr(plan, k) for k in (
        "binary_digest", "binary_version", "dovetail_commit", "model")) and
        pin.settings_policy == settings_policy(plan.broker_policy) and pin.settings_digest == digest(plan.config_overrides),
        "NATIVE_TOOL_PROJECTION_SCOPE")
    return {role: _validate_projection(_private_json(cas, getattr(pin, role + "_ref"),
        MAX_PROJECTION_BYTES), role, helper_collaboration=helper_collaboration) for role in ("executor", "helper")}


def pin_tool_projection(cas, plan, reviewed_projections, *, helper_collaboration=False,
                        conformance_helpers=False, campaign_team=False):
    """Operator setup from previously reviewed projections, before native startup.

    This is deliberately absent from the HTTP/tool interfaces. It must not be
    called with the request being admitted or used as trust on first request.
    """
    require(isinstance(reviewed_projections, dict) and set(reviewed_projections) == {
        "executor", "helper"} and plan.broker_policy is not None, "NATIVE_TOOL_PROJECTION_SHAPE")
    validate_broker_settings(plan.config_overrides, policy=plan.broker_policy)
    modes = (helper_collaboration, conformance_helpers, campaign_team)
    require(all(type(mode) is bool for mode in modes) and sum(modes) <= 1,
            "NATIVE_TOOL_PROJECTION_SCOPE")
    version = 5 if campaign_team else 3 if conformance_helpers else 2 if helper_collaboration else 1
    if conformance_helpers and plan.broker_policy == TEAM_POLICY:
        version = 4
    schema = f"strata/NativeToolProjection/{version}"
    kind = _projection_kind(schema, plan)
    for role, blocks in reviewed_projections.items():
        _validate_projection(blocks, role,
                             helper_collaboration=any(modes))
    refs = {role + "_ref": cas.put(Principal("operator", "operator"), "operator", "operator",
        canonical(blocks), max_object_bytes=MAX_PROJECTION_BYTES)
        for role, blocks in reviewed_projections.items()}
    pin = kind.model_validate({"schema": schema,
        "policy": f"native-additional-tools-exact/{version}",
        **{k: getattr(plan, k) for k in (
            "binary_digest", "binary_version", "dovetail_commit", "model")},
        "settings_policy": settings_policy(plan.broker_policy), "settings_digest": digest(plan.config_overrides), **refs})
    return cas.put(Principal("operator", "operator"), "operator", "operator", canonical(pin.model_dump()))


def require_tool_projection(cas, plan, body, role):
    expected = read_tool_projection(cas, plan)
    pin = _private_json(cas, plan.tool_projection_ref, 16384)
    projection = request_projection(body, role,
        helper_collaboration=pin["schema"] in {
            "strata/NativeToolProjection/2", "strata/NativeToolProjection/3",
            "strata/NativeToolProjection/4", "strata/NativeToolProjection/5"})
    # Canonical hashes distinguish booleans from numbers as well as all schemas,
    # descriptions, grammars, ordering and namespace fields. Dict equality does not.
    fingerprint = digest(projection)
    require(fingerprint == digest(expected[role]), "NATIVE_TOOL_PROJECTION_MISMATCH")
    return fingerprint
