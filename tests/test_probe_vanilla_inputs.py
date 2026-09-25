"""Synthetic sealed packs and paired state, real resolver and Windows file leases."""

import json
import os
from pathlib import Path

import pytest

from mcbench.storage import Fault, Principal
from strata_evaluator.probe_vanilla_inputs import POLICY, VanillaProbeInputs
from strata_evaluator.writer_preparation import parse_preparation_plan
from test_pack_restore import source, inputs, candidate, installed, sealed_installation
from test_probe_world_copies import copies, fake_writers, custody
from test_probe_pairs import pair_source as original_pair_source, EVALUATOR

pytestmark = [
    pytest.mark.skipif(os.name != "nt", reason="actual Windows deny-write leases"),
    pytest.mark.parametrize("base_pair_source", [{"probe_spend": 1000}], indirect=True),
]

# Export imported pytest fixtures without changing the underlying pack tests.
source, inputs, candidate, installed, sealed_installation, copies, fake_writers, custody = (
    source,
    inputs,
    candidate,
    installed,
    sealed_installation,
    copies,
    fake_writers,
    custody,
)


@pytest.fixture
def configs(configs, source, cas, monkeypatch):
    binding, _, service = source
    raw = service.cas.read(
        Principal("operator", "operator"), "pack:" + binding.request_id, binding.lock
    )
    cas.put(Principal("operator", "operator"), "operator", "operator", raw)
    import test_native_checkpoint

    original = test_native_checkpoint.checkpoint_fixture

    def selected(*args, **kwargs):
        config, body, namespace, stop, put = original(*args, **kwargs)
        cas.put(Principal("operator", "operator"), namespace, "operator", raw)
        # Select the real fixture's sealed pack before any checkpoint commit;
        # never rewrite a committed source or retained evidence.
        return (
            config.model_copy(update={"pack_lock": binding.lock}),
            body | {"pack_lock": binding.lock},
            namespace,
            stop,
            put,
        )

    monkeypatch.setattr(test_native_checkpoint, "checkpoint_fixture", selected)
    return configs


base_pair_source = original_pair_source


@pytest.fixture
def pair_source(base_pair_source, source, cas, request):
    pairs, make_request, put, runtime = base_pair_source
    _, reference, _ = source
    snapshot = Path(reference["snapshot"])
    body = json.loads((snapshot / "manifest.json").read_bytes())
    files = {}
    for path, entry in body["files"].items():
        if entry["disposition"] != "state":
            continue
        name = path if path.startswith("world/") else "external/" + path
        files[name] = cas.put(
            Principal("operator", "operator"),
            EVALUATOR.namespace,
            "evaluator",
            (snapshot / "state" / path).read_bytes(),
        )
    change = getattr(request.node, "callspec", None)
    change = change.params.get("fixture_change") if change else None
    if change == "missing_mutable":
        del files["external/ops.json"]
    elif change:
        path = {
            "extra_external": "external/teams.dat",
            "session_lock": "world/session.lock",
            "world_executable": "world/server.jar",
        }[change]
        files[path] = next(iter(files.values()))

    def registered(**kwargs):
        return make_request(
            **(kwargs | {"fixture_patch": {"world_files": files} | kwargs.get("fixture_patch", {})})
        )

    return pairs, registered, put, runtime


@pytest.fixture
def software_plans(copies, source, tmp_path):
    service, plans, capacity = copies
    binding, *_ = source
    with VanillaProbeInputs(service.preparation, binding.model_dump()) as inputs:
        for arm, plan in plans.items():
            plan["sources"] = inputs.sources[arm]
            plan["source_root"] = inputs.roots[arm]
            # The input common ancestor is deliberately not a writer/evidence
            # root. Native workspaces receive explicit files only.
            plan["workspace_directory"] = str(tmp_path.parent / (tmp_path.name + "-writer-" + arm))
            plan["evidence_directory"] = str(tmp_path.parent / (tmp_path.name + "-evidence-" + arm))
            java = Path(inputs.resolved["launch"]["executable_path"])
            plan["java"] = {
                "path": str(java),
                "bytes": java.stat().st_size,
                "sha256": inputs.resolved["launch"]["executable"]["digest"],
            }
    return service, plans, capacity, binding


def test_exact_sealed_software_and_registered_state_enter_both_held_copies(
    software_plans, fake_writers
):
    service, plans, _, binding = software_plans
    saved = []

    def check(held):
        saved.append(held.software)
        assert held.check()["policy"] == POLICY
        for writer in held.writers.values():
            root = writer.tree.path
            assert (root / "server.jar").read_bytes() == b"synthetic bundler"
            assert (root / "world/level.dat").read_bytes() == b"synthetic world"
            assert not (root / "external").exists()
            assert not (root / "client").exists()
            assert not (root / ".strata-instance.json").exists()
        with pytest.raises(PermissionError):
            (Path(binding.instance) / "server/server.jar").write_bytes(b"replacement")

    result = service.run(EVALUATOR, plans, continuation=check, pack_binding=binding.model_dump())
    assert result["policy"] == POLICY and not result["native_launch_authorized"]
    plan = json.loads(
        service.db.connection.execute("SELECT plan FROM probe_world_copies").fetchone()[0]
    )
    assert plan["software"]["binding"]["lock"] == binding.lock
    assert plan["software"]["state_mapping"]["server.properties"] == "external/server.properties"
    assert len(result["results"]) == 2
    with pytest.raises(Fault, match="PROBE_PACK_CUSTODY_CLOSED"):
        saved[0].check()


@pytest.mark.parametrize(
    "fault", ["software_bytes", "software_path", "state_path", "missing_state", "extra", "java"]
)
def test_changed_software_or_state_plan_cannot_enter_writer(software_plans, fake_writers, fault):
    service, plans, _, binding = software_plans
    plan = plans["initial"]
    if fault == "software_bytes":
        plan["sources"]["server.jar"]["sha256"] = "a" * 64
    elif fault == "software_path":
        plan["sources"]["server.jar"]["path"] = str(Path(binding.instance) / "client/server.jar")
    elif fault == "state_path":
        plan["sources"]["world/level.dat"]["path"] = plans["experienced"]["sources"][
            "world/level.dat"
        ]["path"]
    elif fault == "missing_state":
        del plan["sources"]["ops.json"]
    elif fault == "extra":
        plan["sources"]["private.json"] = plan["sources"]["ops.json"]
    else:
        plan["java"]["sha256"] = "b" * 64
    with pytest.raises(Fault, match="PROBE_WORLD_SOURCE|PROBE_PACK_JAVA"):
        service.run(
            EVALUATOR, plans, continuation=lambda _: None, pack_binding=binding.model_dump()
        )
    assert not fake_writers
    assert not service.db.connection.execute("SELECT 1 FROM probe_world_copies").fetchall()


def test_pack_identity_mismatch_refuses_before_any_writer(software_plans, fake_writers):
    service, plans, _, binding = software_plans
    with pytest.raises(Fault, match="PROBE_PACK_MISMATCH"):
        service.run(
            EVALUATOR,
            plans,
            continuation=lambda _: None,
            pack_binding=binding.model_dump() | {"lock": "cas:sha256:" + "a" * 64},
        )
    assert not fake_writers


def test_same_pack_cannot_smuggle_restored_or_mutated_template(software_plans, fake_writers):
    service, plans, _, binding = software_plans
    (Path(binding.instance) / "server/world").mkdir()
    with pytest.raises(Fault, match="PRIVATE_INSTALLATION_CONTENT"):
        service.run(
            EVALUATOR, plans, continuation=lambda _: None, pack_binding=binding.model_dump()
        )
    assert not fake_writers


def test_compiler_scope_is_not_native_launch_authority(software_plans):
    service, plans, _, binding = software_plans
    with VanillaProbeInputs(service.preparation, binding.model_dump()) as compiled:
        for arm, plan in plans.items():
            compiled.validate(arm, parse_preparation_plan(plan))
        assert not compiled.record["native_launch_authorized"]
        assert not compiled.record["live_initial_state_verified"]


@pytest.mark.parametrize(
    "fixture_change", ["missing_mutable", "extra_external", "session_lock", "world_executable"]
)
def test_registered_pair_with_incomplete_or_unsupported_state_cannot_become_vanilla(
    copies, source, fake_writers, fixture_change
):
    service, plans, _ = copies
    with pytest.raises(
        Fault,
        match="PROBE_PACK_STATE_INCOMPLETE|PROBE_PACK_STATE_LAYOUT|VANILLA_PERSISTENCE_LAYOUT_UNSUPPORTED",
    ):
        service.run(
            EVALUATOR, plans, continuation=lambda _: None, pack_binding=source[0].model_dump()
        )
    assert not fake_writers


@pytest.mark.parametrize("source", [True], indirect=True)
def test_sealed_empty_software_directories_are_not_silently_discarded(copies, source, fake_writers):
    service, plans, _ = copies
    with pytest.raises(Fault, match="PROBE_PACK_EMPTY_DIRECTORIES"):
        service.run(
            EVALUATOR, plans, continuation=lambda _: None, pack_binding=source[0].model_dump()
        )
    assert not fake_writers


def test_software_lease_closes_after_callback_failure_and_pair_holds_remain(
    software_plans, fake_writers
):
    service, plans, _, binding = software_plans
    borrowed = []

    def fail(held):
        borrowed.append(held.software)
        raise RuntimeError("callback failed")

    with pytest.raises(RuntimeError, match="callback failed"):
        service.run(EVALUATOR, plans, continuation=fail, pack_binding=binding.model_dump())
    assert borrowed[0].closed
    assert (
        service.db.connection.execute("SELECT state FROM probe_world_copies").fetchone()[0]
        == "FAILED"
    )
    assert (
        service.db.connection.execute("SELECT state FROM probe_pair_custody").fetchone()[0]
        == "FENCED"
    )
    assert (
        service.preparation.runtime.budgets.status("probe-total")["committed_and_reserved"][
            "spend_microusd"
        ]
        == 200
    )
