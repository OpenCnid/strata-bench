"""Synthetic file fixtures; never substitutes for E9E runtime or cold-restart evidence."""

import hashlib
import json
import os

import pytest
from typer.testing import CliRunner

from mcbench import pack_modes as modes
from mcbench.cli import app
from mcbench.inventory import scan_tree
from mcbench.storage import Fault, digest


@pytest.fixture
def installation(tmp_path, monkeypatch):
    root = tmp_path / "installation"
    files = {"config/configswapper.json": b'{"defaultmode":"expert"}',
             "mods/configswapper-3.2.jar": b"synthetic, not a JAR"}
    for path, data in files.items():
        (root / path).parent.mkdir(parents=True, exist_ok=True)
        (root / path).write_bytes(data)
    monkeypatch.setattr(modes, "E9E_MODE_FILES", {
        path: hashlib.sha256(data).hexdigest() for path, data in files.items()})
    overlays = {"config/test.toml": b'["quoted.key"]\nvalue = true\nitems = [1, 2]\n',
                "config/test.json": b'{"some":"config"}',
                "serverconfig/test.toml": b"power = 40.0\n"}
    for path, data in overlays.items():
        file = root / modes.OVERLAY / path
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_bytes(data)
        target = root / ("world/" + path if path.startswith("serverconfig/") else path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    monkeypatch.setattr(modes, "E9E_OVERLAY_DIGEST", digest(scan_tree(root / modes.OVERLAY)))
    return root


def check(report, name):
    return next(item for item in report["checks"] if item["check"] == name)


def test_absent_mode_only_preparation_and_no_mutation(installation):
    def snapshot():
        return {p.relative_to(installation).as_posix(): p.read_bytes()
                for p in installation.rglob("*") if p.is_file()}
    before = snapshot()
    report = modes.inspect_e9e_mode(installation, "server")
    assert report["file_result"] == "pass"
    assert check(report, "mode_selection")["initialized"] is False
    assert report["gate_result"] == "not_run" and report["compatibility_claim"] is None
    assert not report["loaded_runtime_verified"]
    assert "cold_restart" in report["required_runtime_checks"]
    report = modes.inspect_e9e_mode(installation, "server", effective=True, world="world")
    assert check(report, "mode_selection")["code"] == "MODE_NOT_INITIALIZED"
    assert report["file_result"] == "fail"
    assert snapshot() == before


@pytest.mark.parametrize("content,code", [
    ('{"mode":"normal"}', "MODE_MISMATCH"), ('{"mode":"none"}', "MODE_MISMATCH"),
    ('{"mode":"expert","mode":"normal"}', "MODE_CONFIG_INVALID"),
    ('{"mode":', "MODE_CONFIG_INVALID"), ('[]', "MODE_CONFIG_INVALID"),
])
def test_mode_selection_fails_closed(installation, content, code):
    (installation / "mode.json").write_text(content)
    report = modes.inspect_e9e_mode(installation, "server")
    assert check(report, "mode_selection")["code"] == code
    assert report["file_result"] == "fail"


def test_pinned_files_and_complete_overlay_inventory(installation):
    (installation / "mods/configswapper-3.2.jar").write_bytes(b"new version")
    report = modes.inspect_e9e_mode(installation, "client")
    assert check(report, "mods/configswapper-3.2.jar")["code"] == "RELEASE_MISMATCH"
    (installation / modes.OVERLAY / "config/extra.toml").write_text("injected = true")
    report = modes.inspect_e9e_mode(installation, "client")
    assert check(report, "expert_overlay_inventory")["code"] == "RELEASE_MISMATCH"


def test_effective_subset_and_non_toml_replacement(installation):
    (installation / "mode.json").write_text('{"mode":"expert"}')
    with (installation / "config/test.toml").open("a") as stream:
        stream.write("unrelated = 3\n")
    report = modes.inspect_e9e_mode(installation, "server", effective=True, world="world")
    assert report["file_result"] == "pass" and report["gate_result"] == "not_run"
    assert check(report, "effective:serverconfig/test.toml")["path"] == "world/serverconfig/test.toml"
    # Semantic JSON equivalence is insufficient: the real mod replaces bytes.
    (installation / "config/test.json").write_text('{ "some": "config" }')
    report = modes.inspect_e9e_mode(installation, "server", effective=True, world="world")
    assert check(report, "effective:config/test.json")["code"] == "MODE_OVERLAY_MISMATCH"


def test_missing_invalid_and_wrong_effective_config(installation):
    (installation / "mode.json").write_text('{"mode":"expert"}')
    (installation / "config/test.json").unlink()
    (installation / "config/test.toml").write_text('[broken')
    (installation / "world/serverconfig/test.toml").write_text('power = 40\n')
    report = modes.inspect_e9e_mode(installation, "server", effective=True, world="world")
    assert check(report, "effective:config/test.json")["code"] == "AWAITING_ARTIFACT"
    assert check(report, "effective:config/test.toml")["code"] == "MODE_CONFIG_INVALID"
    assert check(report, "effective:serverconfig/test.toml")["code"] == "MODE_OVERLAY_MISMATCH"


def test_quoted_keys_lists_and_boolean_integer_distinction():
    assert modes._differences({"a.b": {"enabled": True}}, {"a": {"b": {"enabled": True}}})
    assert modes._differences({"a.b": [True]}, {"a.b": [1]}) == [["a.b", "0"]]
    assert modes._differences([1], [1, 2]) == [[]]
    assert modes._differences({"x": [1]}, {"x": [1], "y": 2}) == []


def test_unsafe_inputs_hardlinks_and_file_quota(installation, tmp_path, monkeypatch):
    with pytest.raises(Fault, match="WORLD_PATH_REQUIRED"):
        modes.inspect_e9e_mode(installation, "server", effective=True)
    for world in ("../outside", "C:/outside", "world\\outside"):
        with pytest.raises(Fault, match="UNSAFE_PATH"):
            modes.inspect_e9e_mode(installation, "server", effective=True, world=world)
    with pytest.raises(Fault, match="CONFIG_INVALID"):
        modes.inspect_e9e_mode(installation, "other")
    os.link(installation / "mods/configswapper-3.2.jar", tmp_path / "shared.jar")
    report = modes.inspect_e9e_mode(installation, "server")
    assert check(report, "mods/configswapper-3.2.jar")["code"] == "UNSAFE_PATH"
    monkeypatch.setattr(modes, "MAX_FILE_BYTES", 4)
    report = modes.inspect_e9e_mode(installation, "server")
    assert check(report, "config/configswapper.json")["code"] == "ARTIFACT_QUOTA"


def test_operator_command_reports_scope_and_failure(installation):
    args = ["pack", "inspect-expert-mode", str(installation)]
    result = CliRunner().invoke(app, args)
    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["scope"] == "setup_files"
    result = CliRunner().invoke(app, args + ["--effective", "--world", "world"])
    assert result.exit_code == 2
    assert json.loads(result.output)["gate_result"] == "not_run"
