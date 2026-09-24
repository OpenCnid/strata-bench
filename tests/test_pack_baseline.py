"""Synthetic worlds exercise real sealed-store import and offline reconstruction."""

from copy import deepcopy
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from mcbench.pack_baseline import POLICY, LIFETIME_POLICY, profile_documents, verify_profile_baseline
from mcbench.pack_launch import PackLaunchBinding, RestoredPackLaunchBinding, parse_pack_binding, resolve_pack_launch
from mcbench.pack_restore import archive_restoration, baseline_record, restore_pack_instance
from mcbench.pack_worker import HeldPackWorker
from mcbench.provisioning import PROVISION_CHECKS, ProvisioningEvidence, RoleInventoryInput, parse_acquisition, parse_launch_profile
from mcbench.storage import Fault, canonical, digest
from mcbench.vanilla_persistence import VanillaPersistence, verify_snapshot
from native_game_recovery import GameRecovery
from strata_evaluator.native_game_evidence import sealed_pack_evidence
from test_pack_launch import rows
import test_pack_restore as restore
import test_worker_bundle as bundles

inputs = restore.inputs
candidate = restore.candidate
installed = restore.installed
sealed_installation = restore.sealed_installation
source = restore.source


@pytest.fixture
def successor(source, inputs, tmp_path, request):
    old, reference, service = source
    original = service.status(old.request_id)
    old_lock = service._json(old.request_id, old.lock)
    inventory = service._json(old.request_id, original["inventory"])
    profile = parse_launch_profile(service._json(old.request_id, old_lock["launch_profile"]))
    service.resolve_candidate("pack2", "vanilla")
    receipt = parse_acquisition(service._json(old.request_id, original["receipt"])["receipt"])
    references = {receipt.official_workflow_evidence, *(d.evidence_ref for d in receipt.distributions),
                  profile.client.reviewed_bootstrap, profile.server.reviewed_bootstrap}
    for item in inventory["role_evidence"]:
        references.update((item["provenance"], item["exclusions"]))
    for ref in references:
        assert service._put("pack2", service._json(old.request_id, ref)) == ref
    receipt.request_id = "pack2"
    acquired = service.import_acquisition_receipt(receipt)
    roles = [RoleInventoryInput.model_validate({"role": item["role"],
        "root": str(Path(old.instance) / item["role"]),
        "files": [e for e in inventory["files"] if e["role"] == item["role"]],
        "provenance_evidence": item["provenance"], "exclusions_evidence": item["exclusions"]})
        for item in inventory["role_evidence"]]
    assert service.verify_inventory("pack2", roles) == original["inventory"]
    (inputs[0] / "backends/mineflayer/dist/src/worker_control.js").write_bytes(b"synthetic operator control")
    runtime = bundles.prepare(inputs, destination=tmp_path / "controlled-runtime", operator_stop=True)
    body = json.loads(Path(runtime["manifest"]).read_bytes())
    profile.worker_runtime.path, profile.worker_runtime.sha256 = runtime["manifest"], runtime["sha256"]
    profile.client.executable_path = body["node"]
    profile.client.arguments = [body["worker"], "{strata.worker_config}", "--operator-stop"]
    policy = getattr(request, "param", POLICY)
    if policy == LIFETIME_POLICY:
        profile.worker_settings.max_wall_ms = 360000
    identity = {"is_example": False, "request_id": "pack2", "inventory_digest": digest(inventory),
                "receipt_digest": acquired[11:], "launch_profile_digest": digest(profile.model_dump())}
    proof = ProvisioningEvidence.model_validate({"schema": "strata/ProvisioningEvidence/1", **identity,
        "checks": {key: service._put("pack2", {"schema": "strata/ProvisioningCheck/1", **identity,
            "check_id": key, "result": "pass", "evidence_refs": [receipt.official_workflow_evidence]})
            for key in PROVISION_CHECKS}})
    lock = service.seal_template("pack2", profile, proof)
    fresh = PackLaunchBinding(store=old.store, request_id="pack2", lock=lock, instance=str(tmp_path / "new-template"))
    service.materialize("pack2", Path(fresh.instance))
    imported = reference | {"policy": policy, "source_lock": old.lock, "source_request_id": old.request_id}
    return old, fresh, imported, service, inventory


@pytest.mark.parametrize("successor", [POLICY, LIFETIME_POLICY], indirect=True)
def test_new_baseline_preserves_source_identity_and_durable_history(successor, tmp_path, monkeypatch):
    old, fresh, reference, service, inventory = successor
    before = rows(service)
    original = (Path(reference["snapshot"]) / "manifest.json").read_bytes()
    binding = restore_pack_instance(fresh, reference, tmp_path / "imported")
    assert parse_pack_binding(binding.model_dump()) == binding
    assert resolve_pack_launch(binding, "server")["scope"] == "imported_baseline_preflight"
    assert json.loads((Path(binding.instance) / ".strata-instance.json").read_bytes())["schema"] == "strata/Materialization/3"
    registration = baseline_record(binding)
    assert registration["schema"] == "strata/StoppedWorldBaseline/2"
    assert registration["source_lock"] == old.lock and registration["pack_lock"] == fresh.lock
    assert not registration["complete_checkpoint"] and not registration["baseline_save_qualified"]
    archive = tmp_path / "archived-source"
    world = archive_restoration(binding, inventory, archive)
    assert (archive / "manifest.json").read_bytes() == original
    assert world["pack"]["lock"] == old.lock
    documents = profile_documents(binding)
    # Offline verification uses archived bytes, even if original absolute paths
    # are inaccessible. Neither authority nor the source snapshot is rewritten.
    offline = binding.model_copy(update={"store": "unavailable", "restoration":
        binding.restoration.model_copy(update={"snapshot": "unavailable"})})
    proof = verify_profile_baseline(offline, world, inventory, documents, archive)
    assert proof["same_server_profile"] and proof["new_campaign_baseline"]
    assert not proof["dispatch_authorized"] and rows(service) == before
    assert (Path(reference["snapshot"]) / "manifest.json").read_bytes() == original
    output = tmp_path / "run"
    (output / "worker").mkdir(parents=True)
    scope = {"campaign_id": "new-campaign", "agent_id": "avatar-1", "epoch": 1, "lease_id": "new-lease",
             "state_directory": str(output / "worker"), "configuration_path": str(output / "worker-config.json")}
    monkeypatch.setattr("mcbench.pack_worker.ManagedProcess", restore.workers.fake_process_factory([]))
    with HeldPackWorker(binding, scope) as held:
        held.start(preflight=True)
        held.start()
        receipt, launch = held.receipt(), held.resolved
    archive_restoration(binding, inventory, output / "baseline")
    server = resolve_pack_launch(binding, "server")
    # Exercise the persistence constructor used before Java startup, then bind
    # recapture to the new pack without relabeling the original source snapshot.
    capture = VanillaPersistence(Path(binding.instance) / "server", pack=binding, resolved=server)
    try:
        captured = capture.capture(tmp_path / "recaptured", restore.persistence.stopped(), plan_digest="b" * 64)
        assert verify_snapshot(Path(captured["path"]), captured["manifest_sha256"])["pack"]["lock"] == fresh.lock
    finally:
        capture.close()
    bodies = {"run/pack-lock.json": documents["target_lock"], "run/pack-launch-profile.json": documents["target_profile"],
        "run/pack-inventory.json": inventory, "run/pack-worker-launch.json": launch, "run/server/pack-launch.json": server,
        "run/baseline-source-lock.json": documents["source_lock"], "run/baseline-source-profile.json": documents["source_profile"],
        "run/baseline-import.json": proof}
    bundle = SimpleNamespace(json=lambda key: deepcopy(bodies[key]), path=lambda key: tmp_path / key)
    intent = {"plan": {"schema": "strata/M0NativeGameSmoke/5", "pack": binding.model_dump(), "output": str(output),
                       "worker_runtime": launch["worker_runtime"], "worker_invocation": scope}}
    def inspect():
        return sealed_pack_evidence(bundle, intent, {"sealed_worker_receipt": receipt, "worker_runtime": receipt["runtime"]},
            launch["worker_configuration"], {"schema": "strata/DevelopmentServer/5", "pack": binding.model_dump()},
            {"pack_launch_digest": digest(server)})
    assert inspect()["both_roles_bound"]
    bodies["run/baseline-import.json"]["complete_checkpoint"] = True
    with pytest.raises(Fault, match="NATIVE_GAME_PACK_BASELINE"):
        inspect()
    bodies["run/baseline-import.json"]["complete_checkpoint"] = False
    bodies["run/baseline-source-profile.json"]["server"]["arguments"].append("changed")
    with pytest.raises(Fault, match="PACK_BASELINE_IDENTITY"):
        inspect()


def test_old_restore_cannot_silently_cross_profiles(successor, tmp_path):
    _, fresh, source, _, _ = successor
    plain = {k: source[k] for k in ("snapshot", "sha256")}
    with pytest.raises(Fault, match="PACK_RESTORE_SOURCE"):
        restore_pack_instance(fresh, plain, tmp_path / "forbidden")
    assert not (tmp_path / "forbidden.preparing").exists()


def test_import_cannot_be_used_as_a_recovery_or_later_epoch(successor, tmp_path):
    _, fresh, reference, _, _ = successor
    binding = restore_pack_instance(fresh, reference, tmp_path / "imported")
    invocation = {"campaign_id": "new-campaign", "agent_id": "avatar-1", "epoch": 2, "lease_id": "new-lease",
                  "state_directory": str(tmp_path / "missing"), "configuration_path": str(tmp_path / "config.json")}
    with pytest.raises(Fault, match="PACK_BASELINE_NEW_CAMPAIGN_REQUIRED"):
        resolve_pack_launch(binding, "client", worker_invocation=invocation)
    with pytest.raises(Fault, match="GAME_RECOVERY_SOURCE"):
        GameRecovery.validate_sealed_binding(SimpleNamespace(sealed=True), binding, invocation)


@pytest.mark.parametrize("change", ["server-command", "server-environment", "worker-budget", "java",
                                   "client-environment", "same-worker", "source-pin", "player", "stats", "advancements", "cache"])
def test_cross_profile_or_player_history_cannot_pass_import(successor, change):
    _, fresh, reference, _, inventory = successor
    binding = RestoredPackLaunchBinding(**fresh.model_dump(), restoration=reference)
    documents = deepcopy(profile_documents(binding))
    world = verify_snapshot(Path(reference["snapshot"]), reference["sha256"])
    if change in {"server-command", "server-environment", "worker-budget", "client-environment", "same-worker"}:
        profile = documents["target_profile"]
        if change == "server-command":
            profile["server"]["arguments"].append("--different")
        elif change == "server-environment":
            profile["server"]["environment"]["TZ"] = "different"
        elif change == "worker-budget":
            profile["worker_settings"]["primitive_limit"] += 1
        elif change == "client-environment":
            profile["client"]["environment"]["TZ"] = "different"
        else:
            profile["worker_runtime"] = documents["source_profile"]["worker_runtime"]
        documents["target_lock"]["launch_profile"] = "cas:sha256:" + digest(profile)
        binding.lock = "cas:sha256:" + digest(documents["target_lock"])
    elif change == "java":
        documents["target_lock"]["java"]["digest"] = "f" * 64
        binding.lock = "cas:sha256:" + digest(documents["target_lock"])
    elif change == "source-pin":
        documents["source_lock"]["sealed_at"] = "2026-01-01T00:00:00Z"
    elif change == "cache":
        (Path(reference["snapshot"]) / "state/usercache.json").write_bytes(canonical([{"name": "synthetic-player"}]))
    else:
        root = {"player": "playerdata", "stats": "stats", "advancements": "advancements"}[change]
        world["files"][f"world/{root}/synthetic"] = {}
    with pytest.raises(Fault):
        verify_profile_baseline(binding, world, inventory, documents, Path(reference["snapshot"]))


def test_retired_source_authority_refuses_before_copy(successor, tmp_path):
    old, fresh, reference, service, _ = successor
    service.db.connection.execute("UPDATE provisioning SET state='VERIFIED' WHERE id=?", (old.request_id,))
    with pytest.raises(Fault, match="PACK_BASELINE_AUTHORITY"):
        restore_pack_instance(fresh, reference, tmp_path / "forbidden")
    assert not (tmp_path / "forbidden.preparing").exists()


@pytest.mark.parametrize("successor", [LIFETIME_POLICY], indirect=True)
@pytest.mark.parametrize("change", ["legacy-policy", "too-long", "shorter", "primitive-limit", "server"])
def test_lifetime_baseline_only_changes_declared_worker_lifetime(successor, change):
    _, fresh, reference, _, inventory = successor
    binding = RestoredPackLaunchBinding(**fresh.model_dump(), restoration=reference)
    documents = deepcopy(profile_documents(binding))
    world = verify_snapshot(Path(reference["snapshot"]), reference["sha256"])
    target = documents["target_profile"]
    if change == "legacy-policy":
        binding.restoration.policy = POLICY
    elif change in {"too-long", "shorter"}:
        target["worker_settings"]["max_wall_ms"] = 360001 if change == "too-long" else 90000
    elif change == "primitive-limit":
        target["worker_settings"]["primitive_limit"] += 1
    else:
        target["server"]["arguments"].append("--changed")
    documents["target_lock"]["launch_profile"] = "cas:sha256:" + digest(target)
    binding.lock = "cas:sha256:" + digest(documents["target_lock"])
    with pytest.raises(Fault, match="PACK_BASELINE_PROFILE_CHANGED"):
        verify_profile_baseline(binding, world, inventory, documents, Path(reference["snapshot"]))
