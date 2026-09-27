"""Declared candidate native tool policy; settings alone are not qualification."""

from .storage import require

BROKER_TOOLS = ("artifact_read", "artifact_write", "artifact_list", "game")
SETTINGS_POLICY = "native-broker-closed-features-stdio/2"
POLICY = "native-stdio-projected-artifacts-executor-game/1"
TEAM_POLICY = "native-stdio-projected-artifacts-executor-game-team/1"
TEAM_SETTINGS_POLICY = "native-broker-closed-features-stdio/3"
NO_HELPER_POLICY = "native-stdio-projected-artifacts-executor-game-no-helpers/1"
NO_HELPER_TEAM_POLICY = "native-stdio-projected-artifacts-executor-game-team-no-helpers/1"
NO_HELPER_SETTINGS_POLICY = "native-broker-closed-features-stdio/4"
TEAM_POLICIES = frozenset({TEAM_POLICY, NO_HELPER_TEAM_POLICY})
NO_HELPER_POLICIES = frozenset({NO_HELPER_POLICY, NO_HELPER_TEAM_POLICY})
POLICIES = frozenset({POLICY, TEAM_POLICY, *NO_HELPER_POLICIES})


def broker_tools(policy=POLICY):
    require(policy in POLICIES, "BROKER_TOOL_POLICY")
    return BROKER_TOOLS + (("team",) if policy in TEAM_POLICIES else ())


def broker_approvals(policy=POLICY):
    return {name: {"approval_mode": "approve"} for name in broker_tools(policy)
            if name not in {"artifact_read", "artifact_list"}}


def settings_policy(policy):
    broker_tools(policy)
    return NO_HELPER_SETTINGS_POLICY if policy in NO_HELPER_POLICIES else (
        TEAM_SETTINGS_POLICY if policy == TEAM_POLICY else SETTINGS_POLICY)


def restricted_settings(*, policy=POLICY):
    require(policy in POLICIES, "BROKER_TOOL_POLICY")
    return {
        "features.shell_tool": False,
        "features.view_image": False,
        "features.apps": False,
        "features.browser_use": False,
        "features.browser_use_external": False,
        "features.computer_use": False,
        "features.image_generation": False,
        "features.tool_suggest": False,
        "features.hooks": False,
        "features.skill_mcp_dependency_install": False,
        "features.multi_agent_v2": policy not in NO_HELPER_POLICIES,
        "features.multi_agent": False,
        "features.remote_models": False,
        "features.plugins": True,
        "web_search": "disabled",
        # Sanitized initial instructions come from the frozen launch projection.
        # Do not discover operator AGENTS.md in any workspace ancestor.
        "project_doc_max_bytes": 0,
    }


def validate_broker_settings(config, *, policy=POLICY):
    required = restricted_settings(policy=policy)
    # A sealed command does not constrain an additional native tool feature.
    # Reject aliases/nested tables and unreviewed feature keys, including false
    # values: future semantics require a separately reviewed capability profile.
    require(isinstance(config, dict) and all(isinstance(key, str) for key in config)
            and {key for key in config if key == "features" or key.startswith("features.")}
            == {key for key in required if key.startswith("features.")}, "BROKER_TOOL_POLICY")
    for key, expected in required.items():
        require(type(config.get(key)) is type(expected) and config[key] == expected,
                "BROKER_TOOL_POLICY")
    require([k for k in config if k == "mcp_servers" or k.startswith("mcp_servers.")]
            == ["mcp_servers.strata_broker"], "BROKER_SERVER_POLICY")
    server = config["mcp_servers.strata_broker"]
    # Only the pinned stdio broker is allowed. A URL, inherited environment list
    # or other transport/auth field cannot ride alongside the sealed command.
    require(isinstance(server, dict) and set(server) <= {
                "command", "args", "env", "required", "enabled_tools", "tools",
                "startup_timeout_sec", "tool_timeout_sec"} and server.get("required") is True and
            server.get("enabled_tools") == list(broker_tools(policy)) and
            server.get("tools") == broker_approvals(policy) and
            "default_tools_approval_mode" not in server, "BROKER_SERVER_POLICY")
