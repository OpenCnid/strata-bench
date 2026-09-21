"""Synthetic prelaunch authority/fixture/roster checks, never scoring qualification."""

import copy
import hashlib
import json
import os
import subprocess
from pathlib import Path

import pytest

from mcbench.storage import Database, Fault, canonical, digest
from strata_evaluator.craft_reference import CraftReferencePlan, CraftReferenceStore
from strata_evaluator.scorer import Scorer
from strata_evaluator.telemetry_auth import parse_authority
from test_craft_witness import sequence
from test_telemetry_auth import claim, signed, write

ACTOR = "11111111-1111-1111-1111-111111111111"
OTHER = "22222222-2222-2222-2222-222222222222"


def pin(path):
    return {"sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "bytes": path.stat().st_size}


@pytest.fixture
def reference(tmp_path, database, example):
    game = tmp_path / "game"
    world = game / "world"
    world.mkdir(parents=True)
    (world / "level.dat").write_bytes(b"synthetic baseline, not a Minecraft save")
    support = tmp_path / "operator-validation.json"
    support.write_bytes(b'{"synthetic":true,"qualification":false}')
    events = sequence(example)
    events[0]["payload_schema"] = "strata/ServerStarted/4"
    events[0]["payload"].update(module="strata-forge1192-telemetry/0.3.3",
        craft_capture_policy="server-result-pickup-fastbench-bound/2",
        craft_capture_support={"hook_verified": True, "fastbench_sha256": None})
    for event in events[2:5]:
        event["actor_ids"] = [ACTOR]
    for event in (events[2], events[4]):
        event["payload"]["policy"] = "server-result-pickup-fastbench-bound/2"
    plan = {"schema": "strata/PrivateCraftReferencePlan/1", "instance_id": "i",
        "campaign_id": "synthetic", "epoch": 1, "start_server_tick": 0, "cutoff_server_tick": 20,
        "evidence_kind": "synthetic", "team_id": "team",
        "roster": {"agent": ACTOR}, "predicate": {"predicate_id": "craft", "kind": "craft",
            "team_id": "team", "actors": [ACTOR], "recipes": ["fixture:furnace"],
            "item_id": "minecraft:furnace", "minimum_output": 1,
            "ingredients": {"minecraft:andesite": 5, "minecraft:polished_andesite": 3},
            "sustained_ticks": 0, "require_energy": False, "require_fluid": False, "expert_mode": True},
        "game_directory": str(game), "fixture_directory": str(world),
        "fixture_files": {"level.dat": pin(world / "level.dat")},
        "supporting_files": {"reference": {"path": str(support), **pin(support)}},
        "recipe_digests": {"fixture:furnace": digest(events[1]["payload"])}}
    return CraftReferenceStore(database), plan, events, tmp_path / "authority", tmp_path / "spool.jsonl"


def seal(reference, *, preflight=True):
    store, plan, events, directory, spool = reference
    receipt = store.seal(plan, directory)
    if preflight:
        store.preflight("i")
    authority = parse_authority(json.loads((directory / "authority.json").read_bytes()))
    key = Path(authority.key_file).read_bytes()
    claim(authority, key)
    write(spool, signed(authority, key, events))
    return receipt, authority, key


def test_authenticated_version5_stream_preserves_craft_resource_contract(reference):
    store, _, events, _, spool = reference
    events[0]["payload_schema"] = "strata/ServerStarted/5"
    events[0]["payload"].update(module="strata-forge1192-telemetry/0.3.4", launch_identity={
        "policy": "native-server-launch-observation/1", "pid": 1, "process_started_unix_ms": 1,
        "executable": "synthetic-exe", "game_directory": "synthetic-game", "world_directory": "synthetic-world",
        "module_file": "synthetic-module", "module_sha256": "a"*64, "online_mode": True, "server_port": 25569})
    seal(reference)
    result = store.inspect("i", spool)
    assert result["candidate_complete"] and result["candidate_output"] == 1
    assert not result["scoring_eligible"] and not result["launch_ownership_qualified"]


def test_seal_native_resource_join_and_replay_never_award_a_score(reference, database):
    store, plan, _, directory, spool = reference
    receipt, authority, key = seal(reference)
    assert authority.schema_ == "strata/TelemetrySpoolAuthority/2"
    assert authority.setup_digest == receipt["setup_digest"] == digest(plan)
    assert (directory / "fixture/level.dat").read_bytes() == (Path(plan["fixture_directory"]) / "level.dat").read_bytes()
    # Normal running-world changes never rewrite the preserved baseline. The
    # importer checks the archive, not a post-play state mistaken for initial.
    (Path(plan["fixture_directory"]) / "level.dat").write_bytes(b"synthetic progressed world")
    result = store.inspect("i", spool)
    assert result["candidate_complete"] and result["candidate_output"] == 1
    assert len(result["accepted_resource_witnesses"]) == 1
    assert result["team_binding"] == "registered_strata_roster"
    assert not result["scoring_eligible"] and not result["scoring_authority_qualified"]
    assert not result["launch_ownership_qualified"] and not result["setup_mechanics_qualified"]
    assert not result["rejected_resource_witnesses"]
    assert key.hex() not in json.dumps(result) and str(directory) not in json.dumps(result)
    cursor = database.connection.execute("SELECT MAX(cursor) FROM outbox").fetchone()[0]
    reopened = Database(database.path)
    try:
        assert CraftReferenceStore(reopened).inspect("i", spool) == result
        assert reopened.connection.execute("SELECT MAX(cursor) FROM outbox").fetchone()[0] == cursor
    finally:
        reopened.close()
    Scorer(database)
    assert database.connection.execute("SELECT COUNT(*) FROM predicate_state").fetchone()[0] == 0


@pytest.mark.parametrize("change,code", [("file", "CRAFT_FILE_CHANGED"),
    ("missing", "CRAFT_FIXTURE_INVENTORY_CHANGED"), ("extra", "CRAFT_FIXTURE_INVENTORY_CHANGED"),
    ("support", "CRAFT_FILE_CHANGED")])
def test_seal_verifies_actual_bytes_and_complete_fixture_inventory(reference, change, code):
    store, plan, _, directory, _ = reference
    world = Path(plan["fixture_directory"])
    if change == "file":
        (world / "level.dat").write_bytes(b"changed")
    elif change == "missing":
        (world / "level.dat").unlink()
    elif change == "extra":
        (world / "hidden-extra.dat").write_bytes(b"new")
    else:
        Path(plan["supporting_files"]["reference"]["path"]).write_bytes(b"changed")
    with pytest.raises(Fault, match=code):
        store.seal(plan, directory)
    assert not directory.exists()


def test_preflight_rechecks_files_and_never_renews_launch_reservation(reference):
    store, plan, _, directory, _ = reference
    store.seal(plan, directory)
    original = (Path(plan["fixture_directory"]) / "level.dat").read_bytes()
    (Path(plan["fixture_directory"]) / "level.dat").write_bytes(b"late mutation")
    with pytest.raises(Fault, match="CRAFT_FILE_CHANGED"):
        store.preflight("i")
    (Path(plan["fixture_directory"]) / "level.dat").write_bytes(original)
    assert store.preflight("i")["ready_for_operator_reference"]
    with pytest.raises(Fault, match="CRAFT_LAUNCH_ALREADY_RESERVED"):
        store.preflight("i")
    with pytest.raises(Fault, match="CRAFT_SEAL_EXISTS"):
        store.seal(plan, directory.with_name("replacement"))
    assert not directory.with_name("replacement").exists()


def test_used_or_unadmitted_grant_never_becomes_prelaunch_evidence(reference):
    store, _, _, _, spool = reference
    seal(reference, preflight=False)
    with pytest.raises(Fault, match="CRAFT_LAUNCH_UNREGISTERED"):
        store.inspect("i", spool)
    with pytest.raises(Fault, match="CRAFT_GRANT_ALREADY_USED"):
        store.preflight("i")


@pytest.mark.parametrize("change", ["team", "actor", "duplicate", "foreign_fixture", "path", "case"])
def test_invalid_setup_scope_and_paths_fail_before_issuing_keys(reference, change):
    store, plan, _, directory, _ = reference
    if change == "team":
        plan["team_id"] = "different"
    elif change == "actor":
        plan["predicate"]["actors"] = [OTHER]
    elif change == "duplicate":
        plan["roster"]["second"] = ACTOR
    elif change == "foreign_fixture":
        plan["fixture_directory"] = str(directory)
    elif change == "path":
        plan["fixture_files"]["../hidden"] = plan["fixture_files"].pop("level.dat")
    else:
        plan["fixture_files"]["LEVEL.DAT"] = plan["fixture_files"]["level.dat"]
    with pytest.raises((Fault, ValueError)):
        store.seal(plan, directory)
    assert not directory.exists()


@pytest.mark.parametrize("change,code", [("setup", "CRAFT_SEAL_CHANGED"),
    ("authority", "CRAFT_AUTHORITY_CHANGED"), ("legacy", "CRAFT_AUTHORITY_CHANGED")])
def test_changed_or_unbound_authority_is_not_a_registered_fixture(reference, change, code):
    store, _, _, directory, spool = reference
    seal(reference)
    path = directory / ("setup.json" if change == "setup" else "authority.json")
    body = json.loads(path.read_bytes())
    if change == "setup":
        body["team_id"] = "other"
    elif change == "authority":
        body["setup_digest"] = "a" * 64
    else:
        body["schema"] = "strata/TelemetrySpoolAuthority/1"
        del body["setup_digest"]
    path.write_bytes(canonical(body))
    with pytest.raises(Fault, match=code):
        store.inspect("i", spool)


@pytest.mark.parametrize("change,reason", [("actor", "CRAFT_WRONG_ROSTER"),
    ("recipe", "CRAFT_RECIPE_CHANGED"), ("gift", "CRAFT_GRID_UNSUPPORTED"),
    ("no_consumption", "CRAFT_CONSUMPTION_UNPROVEN"), ("late", "CRAFT_OUTSIDE_TICK_WINDOW"),
    ("early", "CRAFT_OUTSIDE_TICK_WINDOW")])
def test_authenticated_negative_trajectories_get_no_candidate_output(reference, change, reason):
    store, plan, events, directory, spool = reference
    if change == "actor":
        for event in events[2:5]:
            event["actor_ids"] = [OTHER]
    elif change == "recipe":
        plan["recipe_digests"]["fixture:furnace"] = "a" * 64
    elif change == "late":
        plan["cutoff_server_tick"] = 19
    elif change == "early":
        plan.update(start_server_tick=21, cutoff_server_tick=40)
    elif change == "gift":
        from test_craft_witness import stack, plain
        empty = [stack() for _ in range(9)]
        events[2]["payload"]["state"]["slots"][1:10] = empty
        events[4]["payload"]["callback"]["grid"] = empty
        events[3]["payload"]["matrix_at_callback"] = [plain(s) for s in empty]
    else:
        events[4]["payload"]["state"]["slots"][1] = copy.deepcopy(events[2]["payload"]["state"]["slots"][1])
    seal(reference)
    result = store.inspect("i", spool)
    assert not result["candidate_complete"] and result["candidate_output"] == 0
    assert result["rejected_resource_witnesses"][0]["reason"] == reason


def test_changed_distinct_stream_cannot_replace_imported_evidence(reference, database):
    store, _, events, _, spool = reference
    _, authority, key = seal(reference)
    original = store.inspect("i", spool)
    # An owner of the signing key can sign a different valid stream. Persisted
    # source identity still rejects changing the already imported receipt.
    events[0]["payload"]["recipe_count"] += 1
    write(spool, signed(authority, key, events))
    with pytest.raises(Fault, match="CRAFT_IMPORT_CONFLICT"):
        store.inspect("i", spool)
    row = database.connection.execute("SELECT body FROM craft_reference_imports WHERE instance='i'").fetchone()
    assert json.loads(row[0]) == original


def test_partial_publication_is_retained_and_not_automatically_reissued(reference, monkeypatch):
    import strata_evaluator.craft_reference as module
    store, plan, _, directory, _ = reference
    def fail(*args):
        raise OSError("synthetic disk failure")
    monkeypatch.setattr(module, "write_new", fail)
    with pytest.raises(OSError):
        store.seal(plan, directory)
    assert (directory / "producer.key").is_file()
    with pytest.raises(Fault, match="CRAFT_SEAL_MISSING"):
        store.preflight("i")
    with pytest.raises(Fault, match="CRAFT_SEAL_EXISTS"):
        store.seal(plan, directory)


def test_game_directory_cannot_hold_private_database(reference, tmp_path):
    _, plan, _, directory, _ = reference
    db = Database(Path(plan["game_directory"]) / "unsafe.sqlite")
    try:
        with pytest.raises(Fault, match="CRAFT_PRIVATE_PATH"):
            CraftReferenceStore(db).seal(CraftReferencePlan.model_validate(plan), directory)
    finally:
        db.close()


def test_two_distinct_crafts_count_once_each_but_duplicate_transaction_rejects(reference):
    store, plan, events, _, spool = reference
    plan["predicate"]["minimum_output"] = 2
    extra = copy.deepcopy(events[2:5])
    for event in (extra[0], extra[2]):
        event["payload"]["transaction_id"] = "second"
    events[5:5] = extra
    for index, event in enumerate(events, 1):
        event.update(seq=index, server_event_seq=index)
    _, authority, key = seal(reference)
    result = store.inspect("i", spool)
    assert result["candidate_complete"] and result["candidate_output"] == 2
    for event in (events[5], events[7]):
        event["payload"]["transaction_id"] = "transaction"
    write(spool, signed(authority, key, events))
    with pytest.raises(Fault, match="TELEMETRY_CRAFT_DUPLICATE"):
        store.inspect("i", spool)


def test_fixture_hardlink_and_private_source_paths_cannot_be_sealed(reference, tmp_path):
    store, plan, _, directory, _ = reference
    original = Path(plan["fixture_directory"]) / "level.dat"
    os.link(original, tmp_path / "linked-save")
    with pytest.raises(Fault, match="CRAFT_FILE_CHANGED"):
        store.seal(plan, directory)
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    (checkout / ".git").write_text("gitdir: private")
    with pytest.raises(Fault, match="CRAFT_PRIVATE_PATH"):
        store.seal(plan, checkout / "authority")


@pytest.mark.parametrize("target", ["fixture/level.dat", "supporting", "extra"])
def test_archived_source_corruption_or_extra_file_blocks_replay(reference, target):
    store, plan, _, directory, spool = reference
    seal(reference)
    store.inspect("i", spool)
    if target == "supporting":
        path = directory / "supporting" / digest("reference")
    elif target == "extra":
        path = directory / "fixture/extra.dat"
    else:
        path = directory / target
    path.write_bytes(b"changed")
    with pytest.raises(Fault, match="CRAFT_FILE_CHANGED|CRAFT_FIXTURE_INVENTORY_CHANGED"):
        store.inspect("i", spool)


def test_copy_capacity_is_checked_before_grant_issuance(reference, monkeypatch):
    import strata_evaluator.craft_reference as module
    store, plan, _, directory, _ = reference
    monkeypatch.setattr(module.shutil, "disk_usage", lambda _: module.shutil._ntuple_diskusage(10, 9, 1))
    with pytest.raises(Fault, match="CRAFT_STORAGE_RESERVE_LOW"):
        store.seal(plan, directory)
    assert not directory.exists()


def test_actual_java_writer_uses_the_sealed_setup_and_roster(reference, tmp_path):
    java = os.environ.get("STRATA_TELEMETRY_TEST_JAVA")
    classpath = os.environ.get("STRATA_TELEMETRY_TEST_CLASSPATH")
    if not java or not classpath:
        pytest.skip("Pinned actual Java opt-in required; this remains synthetic telemetry")
    store, plan, events, directory, _ = reference
    store.seal(plan, directory)
    store.preflight("i")
    authority = parse_authority(json.loads((directory / "authority.json").read_bytes()))
    spool = tmp_path / "java-spool"
    spool.mkdir()
    config = {"schema": "strata/ForgeTelemetryConfig/3", "campaign_id": plan["campaign_id"],
        "epoch": plan["epoch"], "spool_directory": str(spool), "max_bytes": 1048576, "max_events": 64,
        "recipe_ids": ["fixture:furnace"], "config_queries": [], "authentication": authority.producer_config()}
    config_file, events_file = directory / "producer-config.json", directory / "synthetic-events.json"
    config_file.write_bytes(canonical(config))
    events_file.write_bytes(canonical(events))
    command = [java, "-cp", Path(classpath).read_text(),
        "io.github.opencnid.strata.telemetry.AuthenticatedSpoolFixture", str(config_file),
        plan["game_directory"], str(events_file)]
    options = {"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {}
    process = subprocess.run(command, capture_output=True, timeout=20, **options)
    assert process.returncode == 0, process.stderr.decode()
    result = store.inspect("i", next(spool.glob("*.authenticated.jsonl")))
    assert result["server_boot_id"] == process.stdout.decode().strip()
    assert result["candidate_complete"] and result["candidate_output"] == 1
    assert result["recipe_bindings"] == {"fixture:furnace": True}
    assert not result["scoring_eligible"]


@pytest.mark.parametrize("destination,code", [("existing", "CRAFT_REPORT_EXISTS"),
    ("game", "CRAFT_PRIVATE_PATH"), ("archive", "CRAFT_PRIVATE_PATH")])
def test_cli_never_overwrites_or_exports_a_private_report_into_game_or_seal(reference, monkeypatch, tmp_path, destination, code):
    import sys
    from strata_evaluator.craft_reference import main
    store, plan, _, directory, spool = reference
    seal(reference)
    if destination == "existing":
        output = tmp_path / "existing.json"
        output.write_bytes(b"original private evidence")
    elif destination == "game":
        output = Path(plan["game_directory"]) / "report.json"
    else:
        output = directory / "report.json"
    monkeypatch.setattr(sys, "argv", ["craft_reference", "--database", str(store.database.path),
        "inspect", "--instance", "i", "--spool", str(spool), "--output", str(output)])
    with pytest.raises(Fault, match=code):
        main()
    if destination == "existing":
        assert output.read_bytes() == b"original private evidence"
    else:
        assert not output.exists()
