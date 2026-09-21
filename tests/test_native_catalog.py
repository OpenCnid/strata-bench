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
