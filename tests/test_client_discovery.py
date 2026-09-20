"""Synthetic diagnostic fixtures; these are not live Forge settings evidence."""

import copy
import hashlib
import json

import pytest
from pydantic import ValidationError

from mcbench.client_discovery import inspect_discovery, stable_id
from mcbench.storage import Fault


def fixture():
    key = {"backend": "glfw", "representation": "keysym", "code": 69,
           "name": "key.keyboard.e", "modifiers": [], "persisted": "key.keyboard.e"}
    return {
        "schema": "strata/ForgeBindingDiscovery/1", "backend": "glfw",
        "module": "strata-forge1192-client/0.1.0", "supported": False,
        "discovery_supported": True, "atomic_cas": False, "restart_tested": False,
        "layout_verified": False, "revision": 1, "keymap_digest": "a" * 64,
        "options_file_sha256": None, "persisted_file_present": False,
        "tested_pool": [], "operator_development_only": True,
        "bindings": {"minecraft:key.inventory:0": {
            "translation_id": "key.inventory", "registration_occurrence": 0,
            "label": "Inventory", "category": "key.categories.inventory",
            "owner_mod": "minecraft", "owner_basis": "minecraft:Options.keyInventory",
            "owner_evidence": None, "ambiguous_occurrence": False,
            "persisted_ambiguous": False, "persisted_value": None,
            "key": key, "default_key": copy.deepcopy(key), "contexts": ["UNIVERSAL"],
            "context_confidence": "known", "protected": True,
            "consumer_tested": False, "mutation_supported": False}},
    }


def audit(tmp_path, value, options=None):
    path = tmp_path / "snapshot.json"
    path.write_text(json.dumps(value), encoding="utf-8")
    return inspect_discovery(path, options)


def test_first_launch_is_parseable_but_persistence_and_effects_stay_unknown(tmp_path):
    report = audit(tmp_path, fixture(), tmp_path / "missing-options.txt")
    assert report["format_result"] == "pass"
    assert report["unknown_persisted_values"] == ["minecraft:key.inventory:0"]
    assert report["options_file_match_at_audit"] is True
    assert report["persisted_file_present_at_snapshot"] is False
    assert report["gate_result"] == "not_run"
    assert report["keybinding_capability_qualified"] is False
    assert report["producer_authenticated"] is False
    assert report["effects_verified"] is False
    assert report["restart_verified"] is False


def test_persistence_mismatch_and_concurrent_file_change_remain_visible_without_private_options(tmp_path):
    value = fixture()
    options = tmp_path / "options.txt"
    raw = b"lastServer:private.example\r\nkey_key.inventory:key.keyboard.i\r\n"
    options.write_bytes(raw)
    value["options_file_sha256"] = hashlib.sha256(raw).hexdigest()
    value["persisted_file_present"] = True
    value["bindings"]["minecraft:key.inventory:0"]["persisted_value"] = "key.keyboard.i"
    report = audit(tmp_path, value, options)
    assert report["runtime_persistence_mismatches"] == ["minecraft:key.inventory:0"]
    assert report["options_file_match_at_audit"] is True
    assert "private.example" not in json.dumps(report)
    options.write_bytes(raw + b"renderDistance:8\r\n")
    assert audit(tmp_path, value, options)["options_file_match_at_audit"] is False


@pytest.mark.parametrize("flag", ["supported", "atomic_cas", "restart_tested", "layout_verified"])
def test_unqualified_export_cannot_promote_its_own_capability(tmp_path, flag):
    value = fixture()
    value[flag] = True
    with pytest.raises(ValidationError, match="UNQUALIFIED_CAPABILITY_CLAIM"):
        audit(tmp_path, value)


@pytest.mark.parametrize("corruption,error", [
    ("id", "BINDING_ID_MISMATCH"), ("occurrence", "AMBIGUOUS_OCCURRENCE_MISMATCH"),
    ("owner", "OWNER_BASIS_MISMATCH"), ("backend", "BACKEND_MISMATCH"),
    ("mutable", "UNQUALIFIED_CAPABILITY_CLAIM"),
])
def test_binding_identity_and_authority_corruptions_are_rejected(tmp_path, corruption, error):
    value = fixture()
    binding = next(iter(value["bindings"].values()))
    if corruption == "id":
        value["bindings"] = {"forged-id": binding}
    elif corruption == "occurrence":
        binding["ambiguous_occurrence"] = True
    elif corruption == "owner":
        binding["owner_mod"] = "unknown"
    elif corruption == "backend":
        binding["key"]["backend"] = "lwjgl2"
    else:
        binding["protected"] = False
    with pytest.raises(ValidationError, match=error):
        audit(tmp_path, value)


def test_duplicate_translation_keeps_each_occurrence_and_stays_ambiguous(tmp_path):
    value = fixture()
    binding = next(iter(value["bindings"].values()))
    binding["owner_mod"] = "unknown"
    binding["owner_basis"] = "unresolved"
    binding["translation_id"] = "控制" * 50
    binding["ambiguous_occurrence"] = True
    binding["contexts"] = ["CUSTOM"]
    binding["context_confidence"] = "unknown"
    second = copy.deepcopy(binding)
    second["registration_occurrence"] = 1
    names = [stable_id("unknown", binding["translation_id"], n) for n in range(2)]
    value["bindings"] = dict(zip(names, [binding, second], strict=True))
    report = audit(tmp_path, value)
    assert report["ambiguous_occurrences"] == names
    assert report["unknown_contexts"] == names
    assert report["owner_counts"] == {"unknown": 2}


def test_duplicate_json_unknown_fields_and_unbounded_input_are_rejected(tmp_path):
    path = tmp_path / "snapshot.json"
    path.write_text('{"schema":"a","schema":"b"}', encoding="utf-8")
    with pytest.raises(Fault, match="DUPLICATE_JSON_FIELD"):
        inspect_discovery(path)
    value = fixture() | {"lastServer": "private.example"}
    with pytest.raises(ValidationError, match="Extra inputs"):
        audit(tmp_path, value)
    path.write_bytes(b" " * 524289)
    with pytest.raises(Fault, match="DISCOVERY_FILE_TOO_LARGE"):
        inspect_discovery(path)
