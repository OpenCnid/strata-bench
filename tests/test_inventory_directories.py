"""Synthetic pack round trips; no Minecraft or inference execution."""

from pathlib import Path

import pytest

from mcbench.inventory import inventory_directories, scan_layout
from mcbench.pack_launch import PackLaunchBinding, resolve_pack_launch
from mcbench.storage import CAS, Database, Fault
from test_pack_launch import rows
from test_provisioning import prepare_fixture, seal


@pytest.fixture
def prepared(database, cas, tmp_path):
    return prepare_fixture(database, cas, tmp_path)


@pytest.fixture
def directory_pack(tmp_path):
    store = tmp_path / "store"
    db = Database(store / "controller.sqlite")
    try:
        yield prepare_fixture(db, CAS(db, store / "objects"), tmp_path, simulation=False)
    finally:
        db.close()


@pytest.mark.parametrize("change", [None, "remove-client", "remove-server", "add"])
def test_empty_directories_survive_seal_materialize_and_exact_launch(directory_pack, tmp_path, change):
    fixture = directory_pack
    service, _, roles, _, _ = fixture
    for role in roles:
        role.extra_directories = ["natives", "vendor/empty/leaf"]
        for name in role.extra_directories:
            (Path(role.root) / name).mkdir(parents=True)
    lock, _ = seal(fixture)
    inventory = service._json("pack1", service.status("pack1")["inventory"])
    assert inventory["schema"] == "strata/InstalledInventory/2"
    assert inventory["directories"] == {r: ["mods", "natives", "vendor", "vendor/empty", "vendor/empty/leaf"]
                                        for r in ("client", "server")}
    instance = tmp_path / "instance"
    service.materialize("pack1", instance)
    for role in roles:
        assert scan_layout(instance / role.role) == scan_layout(Path(role.root))
    binding = PackLaunchBinding(store=str(service.cas.root.parent), request_id="pack1", lock=lock, instance=str(instance))
    before = rows(service)
    for role in ("client", "server"):
        assert resolve_pack_launch(binding, role)["lock"] == lock
    if change:
        if change.startswith("remove-"):
            (instance / change[7:] / "natives").rmdir()
        else:
            (instance / "client/vendor/unbound").mkdir()
        with pytest.raises(Fault, match="MATERIALIZATION_CHANGED"):
            resolve_pack_launch(binding, "server")
    assert rows(service) == before


@pytest.mark.parametrize("change", ["undeclared", "absent", "world", "secret", "duplicate",
                                   "case", "file", "file-parent", "traversal"])
def test_bad_second_role_directory_plan_fails_before_any_import(prepared, change):
    service, receipt, roles, _, _ = prepared
    service.import_acquisition_receipt(receipt)
    server = roles[1]
    paths = {"undeclared": [], "absent": ["natives"], "world": ["world"], "secret": ["accounts/cache"],
             "duplicate": ["mods", "mods"], "case": ["MODS"], "file": ["config.txt"],
             "file-parent": ["config.txt/empty"], "traversal": ["../outside"]}
    server.extra_directories = paths[change]
    if change == "undeclared":
        (Path(server.root) / "natives").mkdir()
    before = rows(service)
    with pytest.raises(Fault):
        service.verify_inventory("pack1", roles)
    assert rows(service) == before
    assert service.status("pack1")["state"] == "ACQUIRED"


def test_directory_change_during_copy_cannot_freeze_inventory(prepared, monkeypatch):
    service, receipt, roles, _, _ = prepared
    service.import_acquisition_receipt(receipt)
    original = service.cas.put_file
    def changed(*args, **kwargs):
        result = original(*args, **kwargs)
        (Path(roles[0].root) / "changed").mkdir(exist_ok=True)
        return result
    monkeypatch.setattr(service.cas, "put_file", changed)
    with pytest.raises(Fault, match="SOURCE_CHANGED"):
        service.verify_inventory("pack1", roles)
    assert service.status("pack1")["inventory"] is None


def test_file_only_inventory_retains_legacy_bytes_and_idempotency(prepared):
    service, receipt, roles, _, _ = prepared
    service.import_acquisition_receipt(receipt)
    reference = service.verify_inventory("pack1", roles)
    body = service._json("pack1", reference)
    assert body["schema"] == "strata/InstalledInventory/1" and "directories" not in body
    assert inventory_directories(body) == {"client": ["mods"], "server": ["mods"]}
    # Naming an already implied directory does not issue a different inventory.
    for role in roles:
        role.extra_directories = ["mods"]
    assert service.verify_inventory("pack1", roles) == reference


@pytest.mark.parametrize("change", ["missing-parent", "wrong-role", "unordered", "legacy-field", "unknown-schema"])
def test_malformed_bound_layout_rejected(prepared, change):
    service, receipt, roles, _, _ = prepared
    service.import_acquisition_receipt(receipt)
    body = service._json("pack1", service.verify_inventory("pack1", roles))
    body.update(schema="strata/InstalledInventory/2", directories={"client": ["mods"], "server": ["mods"]})
    if change == "missing-parent":
        body["directories"]["server"] += ["natives/leaf"]
    elif change == "wrong-role":
        body["directories"]["observer"] = []
    elif change == "unordered":
        body["directories"]["server"] = ["natives", "mods"]
    else:
        body["schema"] = "strata/InstalledInventory/1" if change == "legacy-field" else "strata/InstalledInventory/3"
    with pytest.raises(Fault):
        inventory_directories(body)
