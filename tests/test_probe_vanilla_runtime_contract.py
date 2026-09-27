"""Whole-pair launch limits must match before any disk/runtime work."""

import pytest

from mcbench.storage import Fault
from strata_evaluator.probe_vanilla_runtime import PairedVanillaRuntime, POLICY
from test_probe_world_copies import copies, custody, pair_source, fake_writers

copies, custody, pair_source, fake_writers = copies, custody, pair_source, fake_writers


@pytest.mark.parametrize("change", ["wall", "storage", "helper", "helper_bytes"])
def test_server_reference_cannot_allocate_asymmetric_runtime(change):
    pair = {"pair_id": "p1", "arm_order": ["initial", "experienced"]}
    values = {
        arm: {
            "schema": "strata/PrivateProbeVanillaLaunch/1",
            "policy": POLICY,
            "pair_id": "p1",
            "arm": arm,
            "max_wall_s": 60,
            "max_stopped_state_bytes": 1024,
            "helper_class": {
                "path": "C:/fixture/StrataWriterLaunch.class",
                "sha256": "a" * 64,
                "bytes": 20,
            },
        }
        for arm in pair["arm_order"]
    }
    if change == "wall":
        values["initial"]["max_wall_s"] += 1
    elif change == "storage":
        values["initial"]["max_stopped_state_bytes"] += 1
    elif change == "helper":
        values["initial"]["helper_class"]["sha256"] = "b" * 64
    else:
        values["initial"]["helper_class"]["bytes"] += 1
    with pytest.raises(Fault, match="PROBE_UNMATCHED_RUNTIME"):
        PairedVanillaRuntime(pair, values)


@pytest.mark.parametrize("pair_source", [{"probe_spend": 1000}], indirect=True)
def test_unlaunched_copies_can_release_capacity_without_releasing_costs(copies, fake_writers):
    from test_probe_pairs import EVALUATOR
    from mcbench.controller import reserved_resources

    service, plans, _ = copies
    service.run(EVALUATOR, plans, continuation=lambda _: None)
    service.preparation.release_undispatched_resources()
    assert not any(reserved_resources(service.db.connection, "probe-worker").values())
    assert (
        service.preparation.runtime.budgets.status("probe-total")["committed_and_reserved"][
            "spend_microusd"
        ]
        == 200
    )
