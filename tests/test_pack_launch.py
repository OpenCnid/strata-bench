"""Synthetic pack bytes/attestations and disposable Python server; never game evidence."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from mcbench.inventory import file_hash, scan_tree
from mcbench.pack_launch import PackLaunchBinding, resolve_pack_launch
from mcbench.records import FileEntry
from mcbench.storage import CAS, Database, Fault, canonical, digest
from test_provisioning import prepare_fixture, seal


@pytest.fixture
def pack(tmp_path):
    store = tmp_path / "store"
    db = Database(store / "controller.sqlite")
    fixture = prepare_fixture(db, CAS(db, store / "objects"), tmp_path, simulation=False)
    service, _, roles, launch, _ = fixture
    root = Path(roles[1].root)
    (root / "eula.txt").write_text("eula=true\n")  # Fictional fixture; no terms acceptance.
    (root / "server.properties").write_text("server-ip=127.0.0.1\nonline-mode=true\n")
    (root / "fixture.py").write_text('import sys\n'
        'print(\'Done (0.1s)! For help, type "help"\',flush=True)\n'
        'assert sys.stdin.readline()=="stop\\n"\nprint("fixture stopped")\n')
    roles[1].files = [FileEntry.model_validate(item | {"role": "server", "origin": "fixture",
        "project_id": 1, "file_id": 2, "license_ref": "fixture", "layer": "resolved"})
        for item in scan_tree(root)]
    launch.server.executable_path = sys.executable
    launch.server.executable.digest = file_hash(Path(sys.executable))
    launch.server.arguments = ["-I", "fixture.py"]
    launch.server.environment = {k: os.environ[k] for k in ("SystemRoot", "WINDIR") if k in os.environ}
    lock, _ = seal(fixture)
    instance = tmp_path / "instance"
    service.materialize("pack1", instance)
    binding = PackLaunchBinding(store=str(store), request_id="pack1", lock=lock, instance=str(instance))
    yield binding, fixture
    db.close()


def rows(service):
    db = service.db.connection
    tables = [row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")]
    return {table: [tuple(row) for row in db.execute(f'SELECT * FROM "{table}"')]
            for table in tables}


def test_exact_sealed_command_and_both_roles_are_verified_without_writes(pack, monkeypatch):
    binding, fixture = pack
    before = rows(fixture[0])
    monkeypatch.setenv("OPENAI_API_KEY", "SYNTHETIC-CANARY")
    result = resolve_pack_launch(binding, "server")
    assert result["launch"] == fixture[3].server.model_dump() | {
        "working_directory": str(Path(binding.instance) / "server")}
    assert result["lock"] == binding.lock and result["target"] == "e9e"
    assert result["scope"] == "fresh_materialization_preflight"
    assert not result["writer_custody_qualified"] and not result["campaign_admission"]
    assert "SYNTHETIC-CANARY" not in json.dumps(result)
    assert resolve_pack_launch(binding, "client")["launch"]["working_directory"] == str(
        Path(binding.instance) / "client")
    assert rows(fixture[0]) == before


@pytest.mark.parametrize("change", ["server", "client", "missing", "extra", "empty_dir", "world",
                                   "root_extra", "marker", "marker_extra", "marker_hardlink",
                                   "file_hardlink", "lock", "request", "relative", "traversal",
                                   "unsealed", "simulation", "inventory_blob", "launch_blob"])
def test_mismatch_rejects_before_start_and_preserves_store(pack, change):
    binding, fixture = pack
    service = fixture[0]
    instance = Path(binding.instance)
    if change in {"server", "client"}:
        (instance / change / "config.txt").write_text("altered")
    elif change == "missing":
        (instance / "server/config.txt").unlink()
    elif change == "extra":
        (instance / "client/unreviewed.txt").write_text("extra")
    elif change in {"empty_dir", "world"}:
        (instance / "server" / change).mkdir()
    elif change == "root_extra":
        (instance / "runtime").mkdir()
    elif change in {"marker", "marker_extra"}:
        path = instance / ".strata-instance.json"
        value = json.loads(path.read_bytes())
        value["lock" if change == "marker" else "extra"] = "cas:sha256:" + "a" * 64
        path.write_bytes(canonical(value))
    elif change in {"marker_hardlink", "file_hardlink"}:
        path = instance / (".strata-instance.json" if change == "marker_hardlink" else "server/config.txt")
        (instance.parent / "shared").hardlink_to(path)
    elif change == "lock":
        binding = binding.model_copy(update={"lock": "cas:sha256:" + "a" * 64})
    elif change == "request":
        binding = binding.model_copy(update={"request_id": "absent"})
    elif change == "relative":
        binding = binding.model_copy(update={"instance": "instance"})
    elif change == "traversal":
        binding = binding.model_copy(update={"instance": str(instance / ".." / "instance")})
    elif change == "unsealed":
        service.db.connection.execute("UPDATE provisioning SET state='VERIFIED'")
    elif change == "simulation":
        service.db.connection.execute("UPDATE provisioning_profile SET simulation=1")
    else:
        lock = service._json("pack1", binding.lock)
        ref = lock["resolved_inventory" if change == "inventory_blob" else "launch_profile"]
        (service.cas.root / ref[11:]).write_bytes(b"corrupt")
    before = rows(service)
    with pytest.raises(Fault):
        resolve_pack_launch(binding, "server")
    assert rows(service) == before


def test_changed_pinned_executable_rejects_client_even_when_server_is_valid(pack):
    binding, fixture = pack
    Path(fixture[3].client.executable_path).write_bytes(b"changed executable")
    with pytest.raises(Fault, match="HASH_MISMATCH"):
        resolve_pack_launch(binding, "client")


def test_unknown_store_is_not_created(tmp_path):
    store = tmp_path / "absent"
    with pytest.raises(Fault, match="AWAITING_ARTIFACT"):
        resolve_pack_launch(PackLaunchBinding(store=str(store), request_id="pack1",
            lock="cas:sha256:" + "a" * 64, instance=str(tmp_path / "instance")), "server")
    assert not store.exists()


@pytest.mark.parametrize("change", [None, "target", "override", "altered", "simulation",
                                   "instance_evidence", "store_evidence"])
def test_bound_development_server_uses_sealed_command_or_refuses_before_process(pack, change):
    binding, fixture = pack
    directory = Path(binding.instance).parent
    evidence = directory / "run"
    plan = {"schema": "strata/DevelopmentServer/3", "target": "e9e", "max_wall_s": 1,
            "evidence": str(evidence), "pack": binding.model_dump()}
    if change == "target":
        plan["target"] = "vanilla"
    elif change == "override":
        plan["launch"] = fixture[3].server.model_dump()
    elif change == "altered":
        (Path(binding.instance) / "server/fixture.py").write_text('raise RuntimeError("must not run")')
    elif change == "simulation":
        fixture[0].db.connection.execute("UPDATE provisioning_profile SET simulation=1")
    elif change in {"instance_evidence", "store_evidence"}:
        evidence = Path(binding.instance if change == "instance_evidence" else binding.store) / "run"
        plan["evidence"] = str(evidence)
    path = directory / "plan.json"
    path.write_text(json.dumps(plan))
    before = rows(fixture[0])
    repository = Path(__file__).resolve().parents[1]
    process = subprocess.run([sys.executable, str(repository / "tools/development_server.py"), str(path)],
                             capture_output=True, timeout=20)
    if change is None:
        assert process.returncode == 0, process.stderr
        result = json.loads((evidence / "result.json").read_bytes())
        resolved = json.loads((evidence / "pack-launch.json").read_bytes())
        assert result["status"] == "stopped_unqualified" and result["exit_code"] == 0
        assert result["ready"] and result["stop_sent"] and not result["forced_stop"]
        assert not result["campaign_admission"] and not result["clean_save_proven"]
        assert resolved["lock"] == binding.lock and resolved["launch"]["arguments"] == ["-I", "fixture.py"]
        assert result["pack_launch_digest"] == digest(resolved)
    else:
        assert process.returncode != 0
        assert not evidence.exists()  # Rejected before output creation or process construction.
    assert rows(fixture[0]) == before
