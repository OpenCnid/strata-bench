import json
import subprocess

import pytest

from mcbench.plugins import inspect_plugin_tree, pinned_marketplace
from mcbench.runtime import DOVETAIL_COMMIT
from mcbench.storage import Fault


def test_plugin_source_is_pinned_not_just_marketplace():
    source = pinned_marketplace()["plugins"][0]["source"]
    assert source["ref"] == DOVETAIL_COMMIT
    assert source["url"] == "https://github.com/OpenCnid/dovetail-codex.git"


def test_actual_git_tree_pin_content_and_extra_files(tmp_path):
    def git(*args):
        return subprocess.run(["git", "-C", str(tmp_path), *args], capture_output=True,
                               check=True).stdout.decode().strip()
    git("init")
    manifest = tmp_path / ".codex-plugin/plugin.json"
    manifest.parent.mkdir()
    manifest.write_text(json.dumps({"name": "dovetail-codex", "version": "0.4.1",
                                    "skills": "./skills/"}), encoding="utf-8")
    for index in range(8):
        skill = tmp_path / f"skills/skill-{index}/SKILL.md"
        skill.parent.mkdir(parents=True)
        skill.write_text("synthetic skill fixture\n", encoding="utf-8")
    git("add", ".")
    git("-c", "user.name=Strata Test", "-c", "user.email=strata@example.invalid", "commit", "-m", "fixture")
    commit = git("rev-parse", "HEAD")
    inspection = inspect_plugin_tree(tmp_path, expected_commit=commit)
    assert len(inspection["skills"]) == 8
    assert not inspection["native_invocation_verified"]
    with pytest.raises(Fault, match="PLUGIN_REVISION_MISMATCH"):
        inspect_plugin_tree(tmp_path)
    (tmp_path / "extra-file").write_text("unexpected")
    with pytest.raises(Fault, match="PLUGIN_TREE_MODIFIED"):
        inspect_plugin_tree(tmp_path, expected_commit=commit)
