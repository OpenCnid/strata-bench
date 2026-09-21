"""Declared candidate native tool policy; settings alone are not qualification."""

from .storage import require

BROKER_TOOLS = ("artifact_read", "artifact_write", "artifact_list", "game")
SETTINGS_POLICY = "native-broker-closed-features-stdio/2"


def restricted_settings():
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
        "features.multi_agent_v2": True,
        "features.multi_agent": False,
        "features.remote_models": False,
        "features.plugins": True,
        "web_search": "disabled",
        # Sanitized initial instructions come from the frozen launch projection.
        # Do not discover operator AGENTS.md in any workspace ancestor.
        "project_doc_max_bytes": 0,
    }


def validate_broker_settings(config):
    required = restricted_settings()
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
            server.get("enabled_tools") == list(BROKER_TOOLS) and
            server.get("tools") == {"artifact_write": {"approval_mode": "approve"},
                                     "game": {"approval_mode": "approve"}} and
            "default_tools_approval_mode" not in server, "BROKER_SERVER_POLICY")
