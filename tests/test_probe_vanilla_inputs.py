"""Synthetic sealed packs and paired state, real resolver and Windows file leases."""

import json
import os
from pathlib import Path

import pytest

from mcbench.storage import Fault, Principal
from strata_evaluator.probe_vanilla_inputs import POLICY, DIRECTORY_POLICY, VanillaProbeInputs
from strata_evaluator.probe_pairs import DIRECTORY_POLICY as PAIR_DIRECTORY_POLICY
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
        patch = {"world_files": files}
        directory_bound = bool(
            getattr(request.node, "callspec", None)
            and request.node.callspec.params.get("directory_fixture")
        )
        if directory_bound:
            patch.update(
                schema="strata/ProbeFixture/2",
                world_directories=sorted(
                    {p for p in body["directories"] if p == "world" or p.startswith("world/")}
                    | {"external"}
                ),
            )
        value = make_request(
            **(kwargs | {"fixture_patch": patch | kwargs.get("fixture_patch", {})})
        )
        if directory_bound:
            value.update(schema="strata/ProbePairRequest/2", policy=PAIR_DIRECTORY_POLICY)
        return value

    return pairs, registered, put, runtime


@pytest.fixture
def software_plans(copies, source, tmp_path, request):
    service, plans, capacity = copies
    binding, *_ = source
    directory_bound = bool(
        getattr(request.node, "callspec", None)
        and request.node.callspec.params.get("directory_fixture")
    )
    policy = DIRECTORY_POLICY if directory_bound else POLICY
    with VanillaProbeInputs(service.preparation, binding.model_dump(), policy=policy) as inputs:
        for arm, plan in plans.items():
            if directory_bound:
                plan.update(
                    schema="strata/PrivateWriterPreparationPlan/4",
                    staging_policy="sequential-bundles512mib/1",
                    directories=inputs.directories,
                )
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


@pytest.mark.parametrize("directory_fixture", [True])
@pytest.mark.parametrize("source", [False, True], indirect=True)
def test_directory_bound_pair_preserves_world_and_software_empty_directories(
    software_plans, fake_writers, directory_fixture, source
):
    service, plans, capacity, binding = software_plans
    pair, _, target, *_ = service.preparation._source(service.preparation.pair_id)
    assert pair["schema"] == "strata/ProbePairStaging/2"
    assert "world/datapacks" in pair["world_directories"]

    def inspect(held):
        assert held.check()["policy"] == DIRECTORY_POLICY
        assert held.software.record["registered_world_directories_preserved"]
        assert not held.software.record["live_initial_state_verified"]
        for arm, writer in held.writers.items():
            expected = set(writer.plan.directories)
            assert {
                p.relative_to(writer.tree.path).as_posix()
                for p in writer.tree.path.rglob("*")
                if p.is_dir()
            } == expected
            assert (writer.tree.path / "world/datapacks").is_dir()
            assert (target / pair["arm_directories"][arm] / "server/world/datapacks").is_dir()
            assert not (writer.tree.path / "external").exists()
            if "java/empty" in expected:
                assert (writer.tree.path / "java/empty").is_dir()
                assert (writer.tree.path / "libraries/empty").is_dir()

    result = service.run(
        EVALUATOR,
        plans,
        continuation=inspect,
        pack_binding=binding.model_dump(),
        software_policy=DIRECTORY_POLICY,
    )
    assert result["policy"] == DIRECTORY_POLICY and not result["native_launch_authorized"]
    assert (
        service.db.connection.execute("SELECT state FROM probe_world_copies").fetchone()[0]
        == "DISCARDED"
    )
    from mcbench.controller import reserved_resources

    assert reserved_resources(service.db.connection, "probe-worker") == capacity


@pytest.mark.parametrize("directory_fixture", [True])
@pytest.mark.parametrize("source", [True], indirect=True)
@pytest.mark.parametrize(
    "change", ["missing", "extra", "old_writer", "old_policy", "without_software"]
)
def test_directory_bound_pair_refuses_layout_or_policy_downgrade_before_writer(
    software_plans, fake_writers, directory_fixture, change
):
    service, plans, _, binding = software_plans
    plan = plans["initial"]
    options = {"pack_binding": binding.model_dump(), "software_policy": DIRECTORY_POLICY}
    if change == "missing":
        plan["directories"] = [p for p in plan["directories"] if p != "java/empty"]
    elif change == "extra":
        plan["directories"] = sorted([*plan["directories"], "world/private-extra"])
    elif change == "old_writer":
        plan["schema"] = "strata/PrivateWriterPreparationPlan/3"
        del plan["directories"]
    elif change == "old_policy":
        options["software_policy"] = POLICY
    else:
        options = {}
    with pytest.raises(
        Fault,
        match="PROBE_PACK_DIRECTORIES|PROBE_PACK_DIRECTORY_POLICY|PROBE_WORLD_DIRECTORY_POLICY",
    ):
        service.run(EVALUATOR, plans, continuation=lambda _: None, **options)
    assert not fake_writers
    assert not service.db.connection.execute("SELECT 1 FROM probe_world_copies").fetchall()


@pytest.mark.parametrize("directory_fixture", [True])
@pytest.mark.parametrize("source", [True], indirect=True)
@pytest.mark.parametrize("change", ["add", "remove"])
def test_directory_mutation_after_copy_fences_pair_and_retains_holds(
    software_plans, fake_writers, directory_fixture, change
):
    service, plans, _, binding = software_plans

    def mutate(held):
        root = held.writers["initial"].tree.path
        if change == "add":
            (root / "world/unregistered").mkdir()
        else:
            (root / "java/empty").rmdir()

    with pytest.raises(Fault, match="PROBE_PACK_DIRECTORIES"):
        service.run(
            EVALUATOR,
            plans,
            continuation=mutate,
            pack_binding=binding.model_dump(),
            software_policy=DIRECTORY_POLICY,
        )
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


def test_legacy_pair_cannot_select_directory_policy(software_plans, fake_writers):
    service, plans, _, binding = software_plans
    with pytest.raises(Fault, match="PROBE_PACK_DIRECTORY_POLICY"):
        service.run(
            EVALUATOR,
            plans,
            continuation=lambda _: None,
            pack_binding=binding.model_dump(),
            software_policy=DIRECTORY_POLICY,
        )
    assert not fake_writers


def test_legacy_software_policy_rejects_unregistered_writer_directories(
    software_plans, fake_writers
):
    service, plans, _, binding = software_plans
    with VanillaProbeInputs(service.preparation, binding.model_dump()) as compiled:
        plan = plans["initial"]
        plan.update(
            schema="strata/PrivateWriterPreparationPlan/4",
            staging_policy="sequential-bundles512mib/1",
            directories=compiled.directories,
        )
    with pytest.raises(Fault, match="PROBE_PACK_DIRECTORY_POLICY"):
        service.run(
            EVALUATOR, plans, continuation=lambda _: None, pack_binding=binding.model_dump()
        )
    assert not fake_writers
