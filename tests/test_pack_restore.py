"""Synthetic stopped worlds and sealed stores; actual file leases, no game/model."""

from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

import pytest

from mcbench.inventory import file_hash, scan_tree
from mcbench.launch_integrity import IntegrityError
from mcbench.pack_launch import PackLaunchBinding, parse_pack_binding, resolve_pack_launch
from mcbench.pack_restore import archive_restoration, restore_pack_instance
from mcbench.pack_worker import HeldPackWorker
from mcbench.provisioning import RoleInventoryInput
from mcbench.storage import CAS, Database, Fault, canonical, digest
from mcbench.vanilla_persistence import VanillaPersistence, verify_snapshot
import test_pack_worker as workers
import test_vanilla_persistence as persistence
from test_pack_launch import rows
from test_provisioning import prepare_fixture
from strata_evaluator.native_game_evidence import sealed_pack_evidence

inputs = workers.inputs
candidate = workers.candidate
installed = persistence.installed
sealed_installation = persistence.sealed_installation


@pytest.fixture
def source(candidate, sealed_installation, installed, tmp_path):
    _, profile, _, _, _ = candidate
    base = tmp_path / "restoration-fixture"
    base.mkdir()
    db = Database(base / "store/controller.sqlite")
    service, acquisition, _, _, evidence = prepare_fixture(db, CAS(db, base / "store/objects"), base, simulation=False)
    # Create this fixture's correct inventory on first import. An already
    # verified template cannot be repurposed by overwriting its inventory.
    db.connection.execute("UPDATE provisioning SET target='vanilla'")
    acquisition.target = "vanilla"
    for item in acquisition.distributions:
        item.file_id = None
        item.origin = "https://piston-data.mojang.com/fixture"
    receipt = service.import_acquisition_receipt(acquisition)
    root, _, _, external = sealed_installation
    properties = workers.PROPERTIES + "level-name=world\n"
    (root / "server.properties").write_text(properties)
    roles = []
    for role, path in (("client", tmp_path / "client"), ("server", root)):
        entries = [e | {"role": role, "origin": "synthetic", "project_id": None, "file_id": None,
                        "license_ref": "synthetic", "layer": "resolved"} for e in scan_tree(path)]
        roles.append(RoleInventoryInput.model_validate({"role": role, "root": str(path), "files": entries,
            "provenance_evidence": evidence, "exclusions_evidence": evidence}))
    inventory = service.verify_inventory("pack1", roles)
    profile.server.executable_path = str(external / "bin/java.exe")
    profile.server.executable.digest = file_hash(external / "bin/java.exe")
    lock = workers.seal((service, profile, evidence, receipt, inventory))
    fresh = PackLaunchBinding(store=str(base / "store"), request_id="pack1", lock=lock,
                              instance=str(tmp_path / "fresh"))
    service.materialize("pack1", Path(fresh.instance))
    played = fresh.model_copy(update={"instance": str(tmp_path / "played")})
    service.materialize("pack1", Path(played.instance))
    server = Path(played.instance) / "server"
    capture = VanillaPersistence(server, pack=played, resolved=resolve_pack_launch(played, "server"))
    try:
        persistence.write_generated_save(server, installed)
        (server / "server.properties").write_text(properties)
        receipt = capture.capture(tmp_path / "snapshot", persistence.stopped(), plan_digest="a"*64)
    finally:
        capture.close()
    reference = {"snapshot": str(tmp_path / "snapshot"), "sha256": receipt["manifest_sha256"]}
    yield fresh, reference, service
    db.close()


def test_restoration_is_exact_new_instance_and_connects_held_worker_and_recapture(source, tmp_path, monkeypatch):
    fresh, reference, service = source
    before = rows(service)
    original = scan_tree(Path(fresh.instance) / "server")
    binding = restore_pack_instance(fresh, reference, tmp_path / "restored")
    assert parse_pack_binding(binding.model_dump()) == binding
    resolved = resolve_pack_launch(binding, "server")
    assert resolved["scope"] == "restored_materialization_preflight"
    assert resolved["restoration"] == reference
    assert not resolved["campaign_admission"]
    assert (tmp_path / "restored/server/world/session.lock").read_bytes() == b""
    assert not (tmp_path / "restored/server/logs").exists()
    assert (tmp_path / "restored/server/world/datapacks").is_dir()
    with pytest.raises(Fault):
        resolve_pack_launch(PackLaunchBinding.model_validate(binding.model_dump(exclude={"restoration"})), "server")
    with pytest.raises(Fault):
        restore_pack_instance(fresh, reference, tmp_path / "restored")
    output = tmp_path / "run"
    (output / "worker").mkdir(parents=True)
    invocation = {"campaign_id": "restored-fixture", "agent_id": "avatar-1", "epoch": 1, "lease_id": "fresh-lease",
                  "state_directory": str(output / "worker"), "configuration_path": str(output / "worker-config.json")}
    monkeypatch.setattr("mcbench.pack_worker.ManagedProcess", workers.fake_process_factory([]))
    with HeldPackWorker(binding, invocation) as worker:
        worker.start(preflight=True)
        worker.start()
        receipt, launch = worker.receipt(), worker.resolved
        assert receipt["held_through_owned_stop"]
    lock = service._json("pack1", binding.lock)
    inventory = service._json("pack1", lock["resolved_inventory"])
    archive_restoration(binding, inventory, output / "baseline")
    bodies = {"run/pack-lock.json": lock, "run/pack-inventory.json": inventory,
        "run/pack-launch-profile.json": service._json("pack1", lock["launch_profile"]),
        "run/pack-worker-launch.json": launch, "run/server/pack-launch.json": resolved}
    bundle = SimpleNamespace(json=lambda key: deepcopy(bodies[key]), path=lambda key: tmp_path / key)
    intent = {"plan": {"schema": "strata/M0NativeGameSmoke/5", "pack": binding.model_dump(),
        "worker_runtime": launch["worker_runtime"], "worker_invocation": invocation, "output": str(output)}}
    result = {"sealed_worker_receipt": receipt, "worker_runtime": receipt["runtime"]}
    server_plan = {"schema": "strata/DevelopmentServer/5", "pack": binding.model_dump()}
    server = {"pack_launch_digest": digest(resolved)}
    def inspect():
        return sealed_pack_evidence(bundle, intent, result, launch["worker_configuration"], server_plan, server)
    assert inspect()["both_roles_bound"]
    bodies["run/pack-worker-launch.json"]["restoration"]["sha256"] = "f"*64
    with pytest.raises(Fault, match="NATIVE_GAME_PACK_BASELINE"):
        inspect()
    bodies["run/pack-worker-launch.json"]["restoration"]["sha256"] = reference["sha256"]
    (output / "baseline/state/world/level.dat").write_bytes(b"changed archived baseline")
    with pytest.raises(Fault, match="VANILLA_CAPTURE_CHANGED"):
        inspect()
    capture = VanillaPersistence(tmp_path / "restored/server", pack=binding, resolved=resolved)
    try:
        receipt = capture.capture(tmp_path / "recaptured", persistence.stopped(), plan_digest="b"*64)
        assert verify_snapshot(Path(receipt["path"]), receipt["manifest_sha256"])["pack"]["lock"] == fresh.lock
    finally:
        capture.close()
    assert scan_tree(Path(fresh.instance) / "server") == original
    assert rows(service) == before


@pytest.mark.parametrize("change", ["state", "extra-state", "empty-dir", "immutable", "client", "marker", "lock"])
def test_changed_restoration_rejects_before_launch(source, tmp_path, change):
    fresh, reference, service = source
    target = tmp_path / "restored"
    binding = restore_pack_instance(fresh, reference, target)
    before = rows(service)
    if change == "state":
        (target / "server/world/level.dat").write_bytes(b"changed")
    elif change == "extra-state":
        (target / "server/world/level.dat_old").write_bytes(b"future state")
    elif change == "empty-dir":
        (target / "server/world/playerdata").mkdir()
    elif change == "immutable":
        (target / "server/java/release").write_bytes(b"changed")
    elif change == "client":
        (target / "client/config.txt").write_bytes(b"changed")
    elif change == "marker":
        (target / ".strata-instance.json").write_bytes(b"{}")
    else:
        (target / "server/world/session.lock").write_bytes(b"old lock")
    with pytest.raises((Fault, IntegrityError)):
        resolve_pack_launch(binding, "server")
    assert rows(service) == before


@pytest.mark.parametrize("change", ["hash", "wrong-pack", "unknown-file", "template-drift", "overlap"])
def test_bad_source_or_template_never_publishes_target(source, tmp_path, change):
    fresh, reference, service = source
    reference = deepcopy(reference)
    target = tmp_path / "restored"
    if change == "hash":
        reference["sha256"] = "e"*64
    elif change == "wrong-pack":
        path = Path(reference["snapshot"]) / "manifest.json"
        import json
        body = json.loads(path.read_bytes())
        body["pack"]["lock"] = "cas:sha256:" + "b"*64
        path.write_bytes(canonical(body))
        reference["sha256"] = file_hash(path)
    elif change == "unknown-file":
        (Path(reference["snapshot"]) / "unexpected").write_bytes(b"ignored state")
    elif change == "template-drift":
        (Path(fresh.instance) / "server/server.properties").write_bytes(b"changed")
    else:
        target = Path(reference["snapshot"]) / "nested"
    before = rows(service)
    with pytest.raises((Fault, IntegrityError)):
        restore_pack_instance(fresh, reference, target)
    assert not target.exists() and not target.with_name(target.name + ".preparing").exists()
    assert rows(service) == before


def test_copy_failure_retains_staging_and_cannot_replay_into_it(source, tmp_path, monkeypatch):
    import mcbench.pack_restore as module
    fresh, reference, _ = source
    original = module._copy
    calls = 0
    def fail(*args):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("synthetic disk failure")
        original(*args)
    monkeypatch.setattr(module, "_copy", fail)
    with pytest.raises(OSError, match="synthetic disk failure"):
        restore_pack_instance(fresh, reference, tmp_path / "restored")
    assert not (tmp_path / "restored").exists() and (tmp_path / "restored.preparing").is_dir()
    with pytest.raises(Fault, match="PACK_RESTORE_TARGET"):
        restore_pack_instance(fresh, reference, tmp_path / "restored")
