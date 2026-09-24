"""Synthetic role evidence, catalog integrity and consumer rejection controls."""

import hashlib
import io
import json
import zipfile

import pytest

from mcbench.storage import Fault
from strata_evaluator import e9e_role_control as control


def catalog():
    return [{"file": name + ".jar", "path": "mods/" + name + ".jar",
             "sha256": "a" * 64, "mod_ids": [name]}
            for name in ("create", "sophisticatedcore")]


def record():
    raw = [{"path": path, "declared": True, "present": True, "value": value}
           for path, value in control.CURRENT] + [
               {"path": path, "declared": False, "present": False, "value": None}
               for path in control.LEGACY]
    configs = []
    for name, source in control.CONFIGS.items():
        row = {"file": name, "registered": source is not None}
        if source:
            row.update(mod=source[0], type=source[1], loaded=True)
        configs.append(row)
    return {"schema": "strata/E9ERoleObservation/1", "configs": configs,
            "mods": [{"id": name, "file": name + ".jar", "path": "/fixture/" + name + ".jar",
                      "version": "fixture", "loaded": True}
                     for name in ("create", "forge", "minecraft", "sophisticatedcore")],
            "create": {"before": raw, "after": json.loads(json.dumps(raw)), "rows": [
                {"path": path, "first": value, "second": value}
                for path, value in control.CURRENT]}}


def inspect(value, inputs=None):
    return control.inspect_control(control.MARKER + json.dumps(value),
                                   catalog() if inputs is None else inputs)


def test_selected_getters_absence_and_catalog_binding_leave_authority_unqualified():
    result = inspect(record())
    assert result["getter_calls"] == 6 and result["loaded_mod_count"] == 4
    assert len(result["bindings"]) == 2 and not result["inventorysorter_loaded"]
    assert result["cache_initialization_possible"] and result["selected_raw_unchanged"]
    assert all(result[key] is False for key in (
        "source_authentication_qualified", "transitive_provenance_qualified",
        "mechanics_qualified", "scoring_eligible"))


@pytest.mark.parametrize("change", [
    lambda r: r["create"]["rows"][0].update(first=9),
    lambda r: r["create"]["rows"][0].update(second=8.5),
    lambda r: r["create"]["rows"][0].update(first=True),
    lambda r: r["create"]["before"][0].update(value="8"),
    lambda r: r["create"]["after"][0].update(declared=1),
    lambda r: r["create"]["after"][3].update(present=True),
    lambda r: r["configs"][2].update(registered=True),
    lambda r: r["configs"][-1].update(loaded=1),
    lambda r: r["mods"][0].update(file="different.jar"),
    lambda r: r["mods"][0].update(loaded=False),
    lambda r: r["mods"].reverse(),
    lambda r: r["mods"].append(dict(r["mods"][-1])),
    lambda r: r.update(scoring_eligible=True),
])
def test_changed_values_roles_sources_shapes_or_order_reject(change):
    value = record()
    change(value)
    with pytest.raises(Fault):
        inspect(value)


def test_newly_loaded_inventorysorter_and_ambiguous_catalog_reject():
    value = record()
    value["mods"].insert(2, {"id": "inventorysorter", "version": "fixture",
                            "file": "sorter.jar", "path": "/fixture/sorter.jar", "loaded": True})
    inputs = catalog() + [{"file": "sorter.jar", "path": "mods/sorter.jar", "sha256": "b" * 64,
                           "mod_ids": ["inventorysorter"]}]
    with pytest.raises(Fault, match="ROLE_CONTROL_MODS"):
        inspect(value, inputs)
    with pytest.raises(Fault, match="ROLE_CONTROL_CATALOG"):
        inspect(record(), catalog() * 2)


def test_rhino_integral_decimal_encoding_preserves_exact_numeric_values():
    value = record()
    for snapshot in (value["create"]["before"], value["create"]["after"]):
        for row in snapshot[:3]:
            row["value"] = float(row["value"])
    for row in value["create"]["rows"]:
        row["first"] = float(row["first"])
        row["second"] = float(row["second"])
    assert inspect(value)["getter_calls"] == 6


def test_missing_duplicate_and_duplicate_key_records_reject():
    text = control.MARKER + json.dumps(record())
    for log in ("", text + "\n" + text, control.MARKER + '{"mods":[],"mods":[]}'):
        with pytest.raises(Fault):
            control.inspect_control(log, catalog())


def test_identical_nested_content_retains_all_candidates_but_different_bytes_reject():
    inputs = catalog()
    copy = dict(inputs[0], path="mods/parent.jar!/META-INF/jars/create.jar")
    result = inspect(record(), inputs + [copy])
    assert result["bindings"][0]["catalog_paths"] == [inputs[0]["path"], copy["path"]]
    copy["sha256"] = "b" * 64
    with pytest.raises(Fault, match="ROLE_CONTROL_CATALOG"):
        inspect(record(), inputs + [copy])


def test_empty_runtime_root_requires_only_nested_content_matches():
    value = record()
    value["mods"][0]["path"] = ""
    with pytest.raises(Fault, match="ROLE_CONTROL_RUNTIME_PATH"):
        inspect(value)
    inputs = catalog()
    inputs[0]["path"] = "mods/parent.jar!/META-INF/jars/create.jar"
    assert inspect(value, inputs)["bindings"][0]["runtime_path_available"] is False
    value["mods"][1]["path"] = ""
    with pytest.raises(Fault, match="ROLE_CONTROL_RUNTIME_PATH"):
        inspect(value, inputs)


def jar(mod_id, children=None):
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as archive:
        archive.writestr("META-INF/mods.toml", f'[[mods]]\nmodId="{mod_id}"\nversion="fixture"')
        if children:
            archive.writestr("META-INF/jarjar/metadata.json", json.dumps(
                {"jars": [{"path": path} for path in children]}))
            for path, raw in children.items():
                archive.writestr(path, raw)
    return output.getvalue()


@pytest.mark.parametrize("prefix", ["META-INF/jarjar", "META-INF/jars"])
def test_catalog_binds_top_level_and_declared_nested_bytes_without_extraction(tmp_path, prefix):
    (tmp_path / "mods").mkdir()
    child = jar("child")
    top = jar("parent", {prefix + "/child.jar": child})
    (tmp_path / "mods/parent.jar").write_bytes(top)
    result = control.mod_catalog(tmp_path)
    assert [row["mod_ids"] for row in result] == [["parent"], ["child"]]
    assert result[1]["sha256"] == hashlib.sha256(child).hexdigest()
    assert result[1]["path"] == "mods/parent.jar!/" + prefix + "/child.jar"
    assert list(tmp_path.rglob("*.jar")) == [tmp_path / "mods/parent.jar"]
    assert (tmp_path / "mods/parent.jar").read_bytes() == top


def test_unsafe_declared_nested_path_rejects(tmp_path):
    (tmp_path / "mods").mkdir()
    (tmp_path / "mods/parent.jar").write_bytes(jar("parent", {"../escape.jar": jar("child")}))
    with pytest.raises(Fault):
        control.mod_catalog(tmp_path)


def test_custom_loader_resource_requires_exact_outer_and_child_pins(tmp_path, monkeypatch):
    (tmp_path / "mods").mkdir()
    child = jar("child")
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as archive:
        archive.writestr("private/child.jar", child)
    outer = output.getvalue()
    (tmp_path / "mods/loader.jar").write_bytes(outer)
    assert len(control.mod_catalog(tmp_path)) == 1
    outer_pin = hashlib.sha256(outer).hexdigest()
    monkeypatch.setattr(control, "PINNED_EMBEDDED", {
        outer_pin: {"private/child.jar": hashlib.sha256(child).hexdigest()}})
    result = control.mod_catalog(tmp_path)
    assert result[1]["mod_ids"] == ["child"]
    control.PINNED_EMBEDDED[outer_pin]["private/child.jar"] = "b" * 64
    with pytest.raises(Fault, match="ROLE_CATALOG_EMBEDDED"):
        control.mod_catalog(tmp_path)


def test_preparation_binds_artifacts_and_requires_exact_current_values(tmp_path, monkeypatch):
    (tmp_path / "mods").mkdir()
    (tmp_path / "mods/fixture.jar").write_bytes(jar("fixture"))
    monkeypatch.setattr(control, "PINS", {"mods/fixture.jar": hashlib.sha256(
        (tmp_path / "mods/fixture.jar").read_bytes()).hexdigest()})
    config = tmp_path / "world/serverconfig/create-server.toml"
    config.parent.mkdir(parents=True)
    config.write_text('[logistics]\ndefaultExtractionTimer=8\n[schematics.schematicannon]\n'
                      'schematicannonShotsPerGunpowder=400\nschematicannonDelay=10\n')
    assert control.prepare_control(tmp_path)["catalog"][0]["mod_ids"] == ["fixture"]
    config.write_text(config.read_text().replace('Timer=8', 'Timer=9'))
    with pytest.raises(Fault, match="ROLE_CONTROL_CONFIG"):
        control.prepare_control(tmp_path)
