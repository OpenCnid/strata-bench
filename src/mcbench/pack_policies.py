"""Reviewed vendor data with misleading runtime-state path names.

Operator-only release policy, never inferred from names alone. E9E 1.27.0's
official client/server archives both ship these JEI directories and one bookmark.
It is part of the immutable initial distribution, not imported player knowledge.
The content hash is required on every archive/installed-template verification.
"""

E9E_INITIAL_JEI = {
    "config/jei/world": None,
    "config/jei/world/local": None,
    "config/jei/world/local/Creative": None,
    "config/jei/world/local/New_World": None,
    "config/jei/world/local/New_World/bookmarks.ini":
        "5e7d6cda8873a16651e84c1306716b53eff5ccb7aa95139796a7f1552e485448",
    "config/jei/world/local/New_World__1": None,
    "config/jei/world/server": None,
    "config/jei/world/server/Minecraft_Server_67692a96": None,
}


def reviewed_vendor_paths(target: str, *, archive=False):
    if target != "e9e":
        return {}
    return {("overrides/" if archive else "") + path: sha
            for path, sha in E9E_INITIAL_JEI.items()}
