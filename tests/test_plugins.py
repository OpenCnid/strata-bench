import json
import subprocess

import pytest

from mcbench.plugins import (
    CORE_SKILLS,
    EXPLICIT_SKILLS,
    _extended_path,
    discovery_policy,
    inspect_plugin_tree,
    pinned_marketplace,
)
from mcbench.runtime import DOVETAIL_COMMIT
from mcbench.storage import Fault


def test_plugin_source_is_pinned_not_just_marketplace():
    source = pinned_marketplace()["plugins"][0]["source"]
    assert source["ref"] == DOVETAIL_COMMIT
    assert source["url"] == "https://github.com/OpenCnid/dovetail-codex.git"


def test_actual_git_tree_pin_content_and_extra_files(tmp_path):
    def git(*args):
        return subprocess.run(["git", "-c", "core.longpaths=true", "-C", str(tmp_path), *args], capture_output=True,
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
    # Real pinned plugins include long fixture paths. Verify both installed-byte
    # inventory and reparse checks use the extended path, not a missing-file bypass.
    long_file = _extended_path(tmp_path / ("deep" * 15) / ("more" * 15) /
                               ("leaf" * 15) / "readme.txt")
    long_file.parent.mkdir(parents=True)
    long_file.write_bytes(b"long-path inventory fixture\n")
    git("add", ".")
    git("-c", "user.name=Strata Test", "-c", "user.email=strata@example.invalid", "commit", "-m", "fixture")
    commit = git("rev-parse", "HEAD")
    inspection = inspect_plugin_tree(tmp_path, expected_commit=commit)
    assert len(inspection["skills"]) == 8
    assert any(e["path"].endswith("readme.txt") and e["bytes"] == 28
               for e in inspection["files"])
    assert not inspection["native_invocation_verified"]
    with pytest.raises(Fault, match="PLUGIN_REVISION_MISMATCH"):
        inspect_plugin_tree(tmp_path)
    (tmp_path / "extra-file").write_text("unexpected")
    with pytest.raises(Fault, match="PLUGIN_TREE_MODIFIED"):
        inspect_plugin_tree(tmp_path, expected_commit=commit)


def test_discovery_excludes_nested_fixtures_and_preserves_all_core_skills(tmp_path):
    nested = "skills/better-skill-creator/tests/fixture/SKILL.md"
    inventory = {"source_commit": DOVETAIL_COMMIT, "skills": list(CORE_SKILLS),
                 "files": [{"path": p} for p in [*CORE_SKILLS, nested, "docs/probe/SKILL.md"]]}
    policy = discovery_policy(tmp_path, inventory)
    assert policy["core"] == list(CORE_SKILLS)
    assert policy["explicit_only"] == list(EXPLICIT_SKILLS)
    assert policy["excluded_nested"] == [nested]
    assert policy["config_overrides"]["skills.config"] == [
        {"path": str(tmp_path / nested), "enabled": False}]
    for change in ({"source_commit": "other"}, {"skills": list(CORE_SKILLS)[:-1]}):
        with pytest.raises(Fault, match="PLUGIN_SKILL_INVENTORY_MISMATCH"):
            discovery_policy(tmp_path, inventory | change)
