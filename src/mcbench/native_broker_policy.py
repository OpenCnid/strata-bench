"""Declared candidate native tool policy; settings alone are not qualification."""

from .storage import require

BROKER_TOOLS = ("artifact_read", "artifact_write", "artifact_list", "game")


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
        "web_search": "disabled",
        # Sanitized initial instructions come from the frozen launch projection.
        # Do not discover operator AGENTS.md in any workspace ancestor.
        "project_doc_max_bytes": 0,
    }


def validate_broker_settings(config):
    for key, expected in restricted_settings().items():
        require(type(config.get(key)) is type(expected) and config[key] == expected,
                "BROKER_TOOL_POLICY")
    require([k for k in config if k == "mcp_servers" or k.startswith("mcp_servers.")]
            == ["mcp_servers.strata_broker"], "BROKER_SERVER_POLICY")
    server = config["mcp_servers.strata_broker"]
    require(isinstance(server, dict) and server.get("required") is True and
            server.get("enabled_tools") == list(BROKER_TOOLS) and
            server.get("tools") == {"artifact_write": {"approval_mode": "approve"},
                                     "game": {"approval_mode": "approve"}} and
            "default_tools_approval_mode" not in server, "BROKER_SERVER_POLICY")
