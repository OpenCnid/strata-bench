"""Paired capture wiring with synthetic JVM/worker/observer evidence.

Actual private source, configuration, file custody and stopped joins are used.
This is not an authentic Minecraft comparison or a native admission certificate.
"""

import gzip
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from mcbench.launch_integrity import FileLease, snapshot
from mcbench.storage import Fault
from strata_evaluator import probe_vanilla_runtime as servers
from strata_evaluator import probe_worker_runtime as workers
from strata_evaluator.player_body_custody import STORAGE_BOUND
from strata_evaluator.player_body_evidence import MODULE_SHA, sha
from test_probe_saved_bodies import PLAYER, payload, player
from test_probe_worker_runtime import (
    source,
    inputs,
    base_candidate,
    base_installed,
    sealed_installation,
    copies,
    custody,
    configs,
    base_pair_source,
    unbound_pair_source,
    pair_source,
    software_plans,
    fake_writers,
    candidate,
    installed,
    runtime,
    process_fixture,
    worker_processes,
    account,
    values,
    EVALUATOR,
)

(
    source,
    inputs,
    base_candidate,
    base_installed,
    sealed_installation,
    copies,
    custody,
    configs,
    base_pair_source,
    unbound_pair_source,
    pair_source,
    software_plans,
    fake_writers,
    candidate,
    installed,
    runtime,
    process_fixture,
    worker_processes,
) = (
    source,
    inputs,
    base_candidate,
    base_installed,
    sealed_installation,
    copies,
    custody,
    configs,
    base_pair_source,
    unbound_pair_source,
    pair_source,
    software_plans,
    fake_writers,
    candidate,
    installed,
    runtime,
    process_fixture,
    worker_processes,
)


def observed_launches(launches):
    return {
        arm: p
        | {
            "schema": "strata/PrivateProbeVanillaLaunch/3",
            "policy": servers.CAPTURE_POLICY,
            "body_observer": {
                "schema": "strata/PrivateBodyObserverLaunch/1",
                "campaign_id": p["pair_id"],
                "epoch": 1,
                "run_id": p["pair_id"] + ":" + arm,
                "roster": [PLAYER],
                "module": {
                    "path": "C:/synthetic/observer.jar",
                    "sha256": MODULE_SHA,
                    "bytes": 143995,
                },
            },
        }
        for arm, p in launches.items()
    }


def basic():
    pair = {"pair_id": "p1", "arm_order": ["initial", "experienced"], "common": {"n": 1}}
    launches = {
        arm: {
            "schema": "strata/PrivateProbeVanillaLaunch/1",
            "policy": servers.POLICY,
            "pair_id": "p1",
            "arm": arm,
            "max_wall_s": 60,
            "max_stopped_state_bytes": 1024,
            "helper_class": {
                "path": "C:/synthetic/StrataWriterLaunch.class",
                "sha256": "a" * 64,
                "bytes": 20,
            },
        }
        for arm in pair["arm_order"]
    }
    return pair, launches


def test_new_profile_reserves_both_complete_capture_bounds():
    pair, launches = basic()
    old = servers.PairedVanillaRuntime(pair, launches)
    new = servers.PairedVanillaRuntime(pair, observed_launches(launches))
    assert new.capture_bodies and new.storage_bound == old.storage_bound + 2 * STORAGE_BOUND
    assert (
        not new.record["native_probe_admission"] and not new.result["live_initial_state_verified"]
    )


@pytest.mark.parametrize("change", ["mixed", "campaign", "epoch", "run", "module", "roster"])
def test_wrong_scope_or_asymmetric_capture_refuses_before_io(change):
    pair, old = basic()
    launches = observed_launches(old)
    if change == "mixed":
        launches["initial"] = old["initial"]
    else:
        value = launches["initial"]["body_observer"]
        if change == "campaign":
            value["campaign_id"] = "foreign"
        elif change == "epoch":
            value["epoch"] = 2
        elif change == "run":
            value["run_id"] = "p1:experienced"
        elif change == "module":
            value["module"]["sha256"] = "b" * 64
        else:
            value["roster"] = ["00000000-0000-4000-8000-000000000002"]
    with pytest.raises(Fault, match="PROBE_UNMATCHED_RUNTIME|PROBE_BODY_CAPTURE_SCOPE"):
        servers.PairedVanillaRuntime(pair, launches)


@pytest.mark.parametrize(
    "roster,n",
    [([PLAYER, PLAYER], 1), ([PLAYER], 2), (["00000000-0000-4000-8000-000000000002"], 1)],
)
def test_registered_roster_refuses_before_worker_import_or_writer(roster, n):
    pair, old = basic()
    pair["common"]["n"] = n
    launches = observed_launches(old)
    for p in launches.values():
        p["body_observer"]["roster"] = roster
    inputs = SimpleNamespace(
        check=lambda: {},
        software=SimpleNamespace(
            record={"saved_bodies": {"bodies": {"a1": {"state": {"player_uuid": PLAYER}}}}}
        ),
    )
    with pytest.raises(Fault, match="PROBE_BODY_CAPTURE_ROSTER"):
        workers.PairedWorkerReference(pair, launches, inputs)


@pytest.fixture
def observers(monkeypatch):
    observed = []
    failure = {"kind": None}

    class Observer:
        def __init__(self, writer, value):
            self.writer, self.value, self.captured, self.bound = writer, value, False, False
            self.output = Path(writer.workspace.path) / "synthetic-body"
            self.output.mkdir()
            self.arguments = ["-XX:+DisableAttachMechanism", "-javaagent:synthetic-only"]
            self.inventory = {"schema": "strata/LaunchFileInventory/1", "files": [], "trees": []}
            self.binding = {"synthetic": True, "scope": value}
            observed.append(self)

        def observe(self, process, identity):
            assert process.poll() is None and identity["pid"] == 22
            self.bound = True

        def capture_ready(self, process):
            assert self.bound and process.poll() is None
            return True

        def capture(self, writer, process, destination):
            assert self.bound and writer is self.writer and process.poll() == 0
            data = player()
            if failure["kind"] == "mismatch" and self.value["run_id"].endswith(":experienced"):
                data["AbilitiesExtension"][1]["custom"] = (1, 0)
            raw = gzip.decompress(payload(data))
            (self.output / (PLAYER + ".nbt")).write_bytes(raw)
            writer.leases.append(FileLease(snapshot([], [self.output])))
            self.captured = True
            return {
                "content_verified": True,
                "owned_producer_verified": failure["kind"] != "producer",
                "launch_binding": self.binding,
                "bodies": {
                    PLAYER: {"nbt_sha256": "f" * 64 if failure["kind"] == "digest" else sha(raw)}
                },
            }

    monkeypatch.setattr(servers, "HeldBodyObserver", Observer)
    return observed, failure


@pytest.mark.parametrize("directory_fixture", [True])
@pytest.mark.parametrize("source", [True], indirect=True)
@pytest.mark.parametrize("base_candidate", [True], indirect=True)
@pytest.mark.parametrize("base_pair_source", [{"probe_spend": 1000}], indirect=True)
@pytest.mark.parametrize("per_arm_disk_bytes", [1024**3])
@pytest.mark.parametrize("case", ["equal", "mismatch", "producer", "digest"])
def test_paired_capture_custody_comparison_and_refusals(
    runtime,
    candidate,
    process_fixture,
    worker_processes,
    observers,
    tmp_path,
    directory_fixture,
    per_arm_disk_bytes,
    case,
):
    service, plans, launches, binding, capacity = runtime
    account(candidate[1].worker_settings.auth_cache)
    invocations = values(service, tmp_path)
    observers[1]["kind"] = case

    def run():
        return service.run_vanilla_worker_reference(
            EVALUATOR,
            plans,
            observed_launches(launches),
            invocations,
            pack_binding=binding.model_dump(),
        )

    if case == "equal":
        result = run()
        assert result["policy"] == workers.CAPTURE_WORKER_POLICY
        comparison = result["runtime"]["body_comparison"]
        assert comparison["save_format_state_equal"] and comparison["owned_producers_verified"]
        assert (
            not result["live_initial_state_verified"] and not comparison["native_probe_admission"]
        )
    else:
        error = {
            "mismatch": "PROBE_BODY_SAVE_STATE_MISMATCH",
            "producer": "PROBE_BODY_CAPTURE_UNPROVEN",
            "digest": "BODY_OUTPUT_CHANGED",
        }[case]
        with pytest.raises(Fault, match=error):
            run()
        assert (
            service.db.connection.execute("SELECT state FROM probe_pair_custody").fetchone()[0]
            == "FENCED"
        )
    assert process_fixture[0] == ["initial", "experienced"]
    assert len(observers[0]) == 2 and all(o.captured for o in observers[0])
    assert all(p.poll() == 0 for p in worker_processes[1])
    path = Path(plans["initial"]["evidence_directory"]) / "launch/body-comparison.json"
    assert path.exists() == (case in {"equal", "mismatch"})
    if path.exists():
        comparison = json.loads(path.read_bytes())
        assert comparison["save_format_state_equal"] == (case == "equal")
        assert comparison["members"][PLAYER]["changed_fields"] == (
            [] if case == "equal" else ["AbilitiesExtension"]
        )
    from mcbench.controller import reserved_resources

    assert reserved_resources(service.db.connection, "probe-worker") == capacity
    assert (
        service.preparation.runtime.budgets.status("probe-total")["committed_and_reserved"][
            "spend_microusd"
        ]
        == 200
    )
