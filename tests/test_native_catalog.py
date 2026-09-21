"""Synthetic catalog and source integrity checks; no model or metadata requests."""

import hashlib
import json

import pytest

from mcbench.native_catalog import MAX_BYTES, install_catalog, select_catalog
from mcbench.storage import Fault, canonical


def test_selected_row_is_unchanged_and_no_overwrite(tmp_path):
    selected = {"slug": "gpt-5.6-luna", "base_instructions": "Fixture instructions",
        "context_window": 272000, "use_responses_lite": True, "unknown_future_field": [1, 2]}
    raw = canonical({"models": [selected, {"slug": "sibling"}]})
    sha = hashlib.sha256(raw).hexdigest()
    source, target = tmp_path / "source.json", tmp_path / "selected.json"
    source.write_bytes(raw)
    pin = install_catalog(source, target, expected_sha256=sha, model="gpt-5.6-luna")
    assert json.loads(target.read_bytes()) == {"models": [selected]}
    assert pin["selected_sha256"] == hashlib.sha256(target.read_bytes()).hexdigest()
    assert pin["static_files"] == [str(target)] and pin["production_qualified"] is False
    with pytest.raises(Fault, match="MODEL_CATALOG_FRESH_PATH"):
        install_catalog(source, target, expected_sha256=sha, model="gpt-5.6-luna")


@pytest.mark.parametrize("value", [{}, {"models": []}, {"models": [1]},
    {"models": [{"slug": "other"}]}, {"models": [{"slug": "luna"}] * 2},
    {"models": [{"slug": "luna"}], "secret": "unaccepted"}])
def test_wrong_or_ambiguous_catalog_rejected(value):
    raw = canonical(value)
    with pytest.raises(Fault, match="MODEL_CATALOG_"):
        select_catalog(raw, hashlib.sha256(raw).hexdigest(), "luna")


def test_pin_and_size_fail_closed():
    raw = canonical({"models": [{"slug": "luna"}]})
    with pytest.raises(Fault, match="MODEL_CATALOG_CHANGED"):
        select_catalog(raw, "0" * 64, "luna")
    with pytest.raises(Fault, match="MODEL_CATALOG_SIZE"):
        select_catalog(b" " * (MAX_BYTES + 1), "0" * 64, "luna")


def test_no_patch_catalog_changes_only_declared_capability(tmp_path):
    from types import SimpleNamespace
    from mcbench.native_catalog import install_no_patch_catalog, NO_PATCH_POLICY, require_no_patch_catalog
    row = {"slug": "gpt-5.6-luna", "apply_patch_tool_type": "freeform", "base_instructions": "unchanged",
        "context_window": 1050000, "max_output_tokens": 128000, "unknown_field": [True, 2, "text"]}
    source, target = tmp_path / "source.json", tmp_path / "restricted.json"
    raw = canonical({"models": [row]})
    source.write_bytes(raw)
    result = install_no_patch_catalog(source, target, expected_sha256=hashlib.sha256(raw).hexdigest(),
                                      model="gpt-5.6-luna")
    assert json.loads(target.read_bytes()) == {"models": [row | {"apply_patch_tool_type": None}]}
    assert result["policy"] == NO_PATCH_POLICY and result["production_qualified"] is False
    assert result["changed_fields"] == {"apply_patch_tool_type": {"from": "freeform", "to": None}}
    plan = SimpleNamespace(model="gpt-5.6-luna", config_overrides=result["config_overrides"])
    require_no_patch_catalog(plan)
    target.write_bytes(raw)
    with pytest.raises(Fault, match="MODEL_CATALOG_TOOL_TYPE"):
        require_no_patch_catalog(plan)
    with pytest.raises(Fault, match="MODEL_CATALOG_FRESH_PATH"):
        install_no_patch_catalog(source, target, expected_sha256=hashlib.sha256(raw).hexdigest(),
                                 model="gpt-5.6-luna")


@pytest.mark.parametrize("patch_type", [None, "unknown", "function", False])
def test_restriction_rejects_unknown_or_already_changed_source(tmp_path, patch_type):
    from mcbench.native_catalog import install_no_patch_catalog
    source, target = tmp_path / "source.json", tmp_path / "target.json"
    raw = canonical({"models": [{"slug": "luna", "apply_patch_tool_type": patch_type}]})
    source.write_bytes(raw)
    with pytest.raises(Fault, match="MODEL_CATALOG_TOOL_TYPE"):
        install_no_patch_catalog(source, target, expected_sha256=hashlib.sha256(raw).hexdigest(), model="luna")
    assert not target.exists()
