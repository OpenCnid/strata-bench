"""Saved-body profile enters real custody; JVM/process results are substituted."""

import json

import pytest

from mcbench.storage import Fault, Principal
from strata_evaluator.probe_saved_bodies import saved_body
from strata_evaluator.probe_vanilla_inputs import BODY_POLICY as SOFTWARE_POLICY, VanillaProbeInputs
from strata_evaluator.probe_vanilla_runtime import BODY_POLICY, PairedVanillaRuntime
from test_probe_pairs import EVALUATOR
from test_probe_saved_bodies import PLAYER, payload, player
from test_probe_vanilla_runtime import (
    source, inputs, base_candidate, base_installed, sealed_installation,
    copies, custody, configs, base_pair_source, pair_source as unbound_pair_source,
    software_plans, fake_writers, candidate, installed, runtime, process_fixture,
)

(source, inputs, base_candidate, base_installed, sealed_installation, copies, custody,
 configs, base_pair_source, unbound_pair_source, software_plans, fake_writers,
 candidate, installed, runtime, process_fixture) = (
    source, inputs, base_candidate, base_installed, sealed_installation, copies, custody,
    configs, base_pair_source, unbound_pair_source, software_plans, fake_writers,
    candidate, installed, runtime, process_fixture)

pytestmark = [pytest.mark.parametrize("directory_fixture", [True]),
              pytest.mark.parametrize("source", [True], indirect=True),
              pytest.mark.parametrize("base_pair_source", [{"probe_spend": 1000}], indirect=True)]


@pytest.fixture
def pair_source(unbound_pair_source, cas, request):
    pairs, make, put, native = unbound_pair_source
    raw = payload(player())
    body = saved_body(raw)
    if getattr(request, "param", None) == "mismatch":
        body["health"] = 19.
    ref = cas.put(Principal("operator", "operator"), EVALUATOR.namespace, "evaluator", raw)

    def registered(**kwargs):
        original = make(**kwargs)
        fixture = pairs._private(original["fixture_ref"])
        patch = {"body_states": {"a1": put(body)},
            "world_files": fixture["world_files"] | {"world/playerdata/" + PLAYER + ".dat": ref},
            "world_directories": sorted(set(fixture["world_directories"]) | {"world/playerdata"})}
        return make(**(kwargs | {"fixture_patch": patch}))
    return pairs, registered, put, native


def launches_v2(values):
    return {arm: p | {"schema": "strata/PrivateProbeVanillaLaunch/2", "policy": BODY_POLICY}
            for arm, p in values.items()}


def test_body_profile_preserves_pair_custody_and_stopped_exports(runtime, process_fixture, directory_fixture):
    service, plans, launches, binding, _ = runtime
    result = service.run_vanilla_reference(EVALUATOR, plans, launches_v2(launches),
        continuation=lambda arm, session: {"arm": arm}, pack_binding=binding.model_dump())
    assert process_fixture[0] == ["initial", "experienced"]
    assert result["policy"] == BODY_POLICY
    bodies = result["runtime"]["saved_bodies"]
    assert bodies["saved_state_verified"] and set(bodies["bodies"]) == {"a1"}
    assert not bodies["live_initial_state_verified"] and not bodies["account_assignment_verified"]
    assert not result["runtime"]["all_bodies_ready"] and not result["native_launch_authorized"]
    plan = json.loads(service.db.connection.execute("SELECT plan FROM probe_world_copies").fetchone()[0])
    assert plan["software"]["policy"] == SOFTWARE_POLICY
    assert plan["software"]["saved_bodies"] == bodies
    for arm in ("initial", "experienced"):
        assert result["results"][arm]["custody"]["vanilla"]["policy"] == BODY_POLICY


@pytest.mark.parametrize("pair_source", ["mismatch"], indirect=True)
def test_wrong_registered_body_refuses_before_writer_or_server(runtime, process_fixture, directory_fixture):
    service, plans, launches, binding, capacity = runtime
    with pytest.raises(Fault, match="PROBE_BODY_STATE_MISMATCH"):
        service.run_vanilla_reference(EVALUATOR, plans, launches_v2(launches),
            continuation=lambda *_: None, pack_binding=binding.model_dump())
    assert not process_fixture[0]
    assert service.db.connection.execute("SELECT COUNT(*) FROM probe_world_copies").fetchone()[0] == 0
    from mcbench.controller import reserved_resources
    assert reserved_resources(service.db.connection, "probe-worker") == capacity
    assert service.preparation.runtime.budgets.status("probe-total")["committed_and_reserved"]["spend_microusd"] == 200


def test_mixed_policy_and_software_downgrade_refuse(runtime, directory_fixture):
    service, _, launches, binding, _ = runtime
    pair = service.preparation._source("p1")[0]
    mixed = launches | {"initial": launches_v2(launches)["initial"]}
    with pytest.raises(Fault, match="PROBE_UNMATCHED_RUNTIME"):
        PairedVanillaRuntime(pair, mixed)
    with VanillaProbeInputs(service.preparation, binding.model_dump(), policy=SOFTWARE_POLICY) as software:
        before = software.record["saved_bodies"]
        software.check()
        assert software.record["saved_bodies"] == before
        from types import SimpleNamespace
        runtime = PairedVanillaRuntime(pair, launches)  # Legacy runtime cannot borrow new profile.
        runtime.held = SimpleNamespace(closed=False, pair=pair, software=software, writers={})
        with pytest.raises(Fault, match="PROBE_PACK_DIRECTORY_POLICY"):
            runtime._scope()
        from strata_evaluator.probe_vanilla_inputs import DIRECTORY_POLICY
        runtime = PairedVanillaRuntime(pair, launches_v2(launches))
        runtime.held = SimpleNamespace(closed=False, pair=pair,
                                      software=SimpleNamespace(policy=DIRECTORY_POLICY), writers={})
        with pytest.raises(Fault, match="PROBE_PACK_DIRECTORY_POLICY"):
            runtime._scope()
        software.body_pair["common"]["n"] = 2
        with pytest.raises(Fault, match="PROBE_SOURCE_CHANGED"):
            software.check()
