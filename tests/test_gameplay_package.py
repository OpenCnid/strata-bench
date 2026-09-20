import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from mcbench.packaging import package_gameplay
from mcbench.storage import Fault


def test_real_compiled_gameplay_client_bundle_excludes_operator_material(tmp_path):
    root = Path(__file__).resolve().parents[1]
    output = tmp_path / "gameplay"
    manifest = package_gameplay(root, output)
    assert set(manifest["files"]) == {"cli.js", "errors.js", "package.json",
                                      "skills/minecraft-keybindings/SKILL.md"}
    assert not manifest["proves_runtime_isolation"]
    assert not any(p.name in {"SPEC.md", "AGENTS.md", "MILESTONES.md", "worker.js", "adapter.js",
                             "desktop_process.py", "desktop_client.py", "saved_blocks.py"}
                   for p in output.rglob("*"))
    environment = dict(os.environ)
    environment.pop("STRATA_GAME_GRANT", None)
    help_result = subprocess.run([shutil.which("node"), str(output / "cli.js"), "--help"],
                                 capture_output=True, text=True, env=environment, timeout=10)
    assert help_result.returncode == 0, help_result.stderr
    assert "wait-events" in help_result.stdout and "recipes" in help_result.stdout
    assert "recipe-query [--category minecraft:crafting|thermal:furnace|thermal:crucible] " in help_result.stdout
    assert "--item ITEM_ID|--fluid FLUID_ID --role input|output --after CURSOR --json" in help_result.stdout
    denied = subprocess.run([shutil.which("node"), str(output / "cli.js"), "observe"],
                             capture_output=True, text=True, env=environment, timeout=10)
    assert denied.returncode == 4
    assert json.loads(denied.stdout)["error"]["code"] == "FORBIDDEN"
    assert str(root) not in denied.stdout
    with pytest.raises(Fault, match="TARGET_EXISTS"):
        package_gameplay(root, output)
