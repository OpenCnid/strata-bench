"""Synthetic registered pair/software; actual Windows input leases, no dispatch."""

import json
import os
from contextlib import contextmanager
from pathlib import Path

import pytest

from mcbench.launch_integrity import IntegrityError
from mcbench import pack_launch
from mcbench.storage import Fault, Principal, canonical
from strata_evaluator import probe_worker_inputs as module
from strata_evaluator.probe_vanilla_inputs import BODY_POLICY, VanillaProbeInputs
from test_probe_pairs import EVALUATOR
from test_probe_saved_bodies import PLAYER
from test_probe_saved_body_runtime import (
    source, inputs, base_candidate, base_installed, sealed_installation,
    copies, custody, configs, base_pair_source, unbound_pair_source, pair_source,
    software_plans, fake_writers, candidate, installed, runtime,
)

(source, inputs, base_candidate, base_installed, sealed_installation, copies, custody, configs, base_pair_source, unbound_pair_source, pair_source, software_plans, fake_writers, candidate, installed, runtime) = (
    source, inputs, base_candidate, base_installed, sealed_installation, copies, custody, configs, base_pair_source, unbound_pair_source, pair_source, software_plans, fake_writers, candidate, installed, runtime
)

pytestmark = [pytest.mark.skipif(os.name != "nt", reason="actual Windows deny-write leases"),
              pytest.mark.parametrize("directory_fixture", [True]),
              pytest.mark.parametrize("source", [True], indirect=True),
              pytest.mark.parametrize("base_candidate", [True], indirect=True),
              pytest.mark.parametrize("base_pair_source", [{"probe_spend": 1000}], indirect=True)]


def account(cache):
    path = Path(cache) / "account.json"
    path.write_bytes(canonical({"schema": "strata/MinecraftAccount/1", "account": "synthetic-avatar",
                               "profile_id": PLAYER.replace("-", "")}))
    return path


def values(service, tmp_path):
    result = {arm: {} for arm in ("initial", "experienced")}
    for row in service.db.connection.execute("SELECT * FROM native_probe_bindings").fetchall():
        state = tmp_path / ("worker-" + row["arm"])
        state.mkdir()
        result[row["arm"]][row["source_agent"]] = {
            "campaign_id": row["campaign"], "agent_id": row["agent"], "epoch": 1,
            "lease_id": "held-" + row["arm"], "state_directory": str(state),
            "configuration_path": str(tmp_path / ("config-" + row["arm"] + ".json"))}
    return result


def no_process(*args, **kwargs):
    raise AssertionError("input preparation attempted a process")


def test_registered_whole_pair_held_without_dispatch_or_parent_release(runtime, candidate, tmp_path,
                                                                     monkeypatch, directory_fixture):
    from mcbench import pack_worker
    from mcbench.controller import reserved_resources
    monkeypatch.setattr(pack_worker, "ManagedProcess", no_process)
    service, _, _, binding, capacity = runtime
    declaration = account(candidate[1].worker_settings.auth_cache)
    raw = declaration.read_bytes()
    supplied = values(service, tmp_path)
    with VanillaProbeInputs(service.preparation, binding.model_dump(), policy=BODY_POLICY) as software:
        holder = software.hold_worker_inputs(EVALUATOR, supplied)
        with holder:
            record = holder.check()
            workers = [w for group in holder._workers.values() for w in group.values()]
            assert all(w._materialization_lease is software.lease for w in workers)
            assert len({id(w.runtime) for w in workers}) == len(workers)
            assert len({id(w.config_lease) for w in workers}) == len(workers)
            assert record["whole_roster_held"] and not record["worker_dispatch_authorized"]
            assert not record["authenticated_identity_verified"] and not record["live_initial_state_verified"]
            assert set(record["invocations"]) == {"initial", "experienced"}
            for arm, group in record["resolved"].items():
                config = group["a1"]["worker_configuration"]
                assert config["expected_player_uuid"] == PLAYER and config["schema"].endswith("/2")
                path = Path(supplied[arm]["a1"]["configuration_path"])
                assert json.loads(path.read_bytes()) == config
                with pytest.raises(PermissionError):
                    path.write_bytes(b"foreign")
            with pytest.raises(PermissionError):
                declaration.write_bytes(b"foreign")
            # Holding the declaration must not prevent ordinary token refresh files.
            (declaration.parent / "token.fixture").write_bytes(b"synthetic refresh allowed")
            record["resolved"]["initial"]["a1"]["worker_configuration"]["expected_player_uuid"] = "foreign"
            assert holder.check()["resolved"]["initial"]["a1"]["worker_configuration"]["expected_player_uuid"] == PLAYER
            assert not service.db.connection.execute("SELECT * FROM probe_world_copies").fetchall()
        with pytest.raises(Fault, match="PROBE_WORKER_INPUTS_CLOSED"):
            holder.check()
        with pytest.raises(Fault, match="PROBE_WORKER_INPUTS_CONSUMED"):
            holder.__enter__()
        declaration.write_bytes(raw)  # Own hold closed, parent reservation retained.
        software.check()
        service.preparation.check()
        assert reserved_resources(service.db.connection, "probe-worker") == capacity
        assert service.preparation.runtime.budgets.status("probe-total")["committed_and_reserved"]["spend_microusd"] == 200


def test_late_arm_account_mismatch_refuses_before_any_configuration_commit(runtime, candidate, tmp_path,
                                                                         monkeypatch, directory_fixture):
    service, _, _, binding, _ = runtime
    account(candidate[1].worker_settings.auth_cache)
    supplied = values(service, tmp_path)
    original = pack_launch._held_pack_launch
    count = 0

    @contextmanager
    def altered(*args, **kwargs):
        nonlocal count
        with original(*args, **kwargs) as (resolved, runtime):
            if kwargs.get("worker_invocation") is not None:
                count += 1
            if count == 2 and kwargs.get("worker_invocation") is not None:
                # Substitute the resolver output to exercise the late-roster boundary.
                resolved["worker_configuration"]["expected_player_uuid"] = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
            yield resolved, runtime

    monkeypatch.setattr(pack_launch, "_held_pack_launch", altered)
    monkeypatch.setattr(module.HeldPackWorker, "commit_configuration", no_process)
    with VanillaProbeInputs(service.preparation, binding.model_dump(), policy=BODY_POLICY) as software:
        with pytest.raises(Fault, match="PROBE_WORKER_ACCOUNT_MISMATCH"):
            with software.hold_worker_inputs(EVALUATOR, supplied):
                pytest.fail("accepted mismatch")
        assert count == 2
        assert all(not Path(g["a1"]["configuration_path"]).exists() for g in supplied.values())
        service.preparation.check()


def test_partial_configuration_failure_releases_own_leases_and_retains_evidence(runtime, candidate, tmp_path,
                                                                              monkeypatch, directory_fixture):
    service, _, _, binding, _ = runtime
    declaration = account(candidate[1].worker_settings.auth_cache)
    raw = declaration.read_bytes()
    supplied = values(service, tmp_path)
    original = module.HeldPackWorker
    count = 0

    class FailingWorker(original):
        def commit_configuration(self):
            nonlocal count
            count += 1
            if count == 2:
                raise Fault("SYNTHETIC_CONFIG_FAILURE")
            return super().commit_configuration()

    monkeypatch.setattr(module, "HeldPackWorker", FailingWorker)
    with VanillaProbeInputs(service.preparation, binding.model_dump(), policy=BODY_POLICY) as software:
        holder = software.hold_worker_inputs(EVALUATOR, supplied)
        with pytest.raises(Fault, match="SYNTHETIC_CONFIG_FAILURE"):
            with holder:
                pytest.fail("accepted failure")
        present = [Path(g["a1"]["configuration_path"]) for g in supplied.values()
                   if Path(g["a1"]["configuration_path"]).exists()]
        assert len(present) == 1
        present[0].write_bytes(present[0].read_bytes())
        declaration.write_bytes(raw)
        with pytest.raises(Fault, match="PROBE_WORKER_INPUTS_CONSUMED"):
            holder.__enter__()
        service.preparation.check()


def test_authority_and_roster_changes_close_worker_custody(runtime, candidate, tmp_path, directory_fixture):
    service, _, _, binding, _ = runtime
    account(candidate[1].worker_settings.auth_cache)
    supplied = values(service, tmp_path)
    with VanillaProbeInputs(service.preparation, binding.model_dump(), policy=BODY_POLICY) as software:
        with pytest.raises(Fault, match="FORBIDDEN"):
            with software.hold_worker_inputs(Principal("helper", "helper"), supplied):
                pytest.fail("helper admitted")
        holder = software.hold_worker_inputs(EVALUATOR, supplied)
        with holder:
            service.db.connection.execute("DELETE FROM native_probe_bindings WHERE arm=?", ("experienced",))
            with pytest.raises(Fault, match="PROBE_|NATIVE_"):
                holder.check()
            assert holder.closed
            with pytest.raises(Fault, match="PROBE_WORKER_INPUTS_CLOSED"):
                holder.check()


@pytest.mark.parametrize("failure", ["stop", "changed_account", "parent_closed", "runtime_recheck"])
def test_custody_failures_never_dispatch_or_release_parent(runtime, candidate, tmp_path,
                                                          monkeypatch, directory_fixture, failure):
    from mcbench import pack_worker
    from mcbench.controller import reserved_resources
    monkeypatch.setattr(pack_worker, "ManagedProcess", no_process)
    service, _, _, binding, capacity = runtime
    declaration = account(candidate[1].worker_settings.auth_cache)
    supplied = values(service, tmp_path)
    with VanillaProbeInputs(service.preparation, binding.model_dump(), policy=BODY_POLICY) as software:
        holder = software.hold_worker_inputs(EVALUATOR, supplied)
        if failure == "stop":
            original = pack_launch._held_pack_launch

            @contextmanager
            def no_stop(*args, **kwargs):
                with original(*args, **kwargs) as (result, runtime):
                    if kwargs.get("worker_invocation") is not None:
                        result["launch"]["arguments"].pop()
                    yield result, runtime

            monkeypatch.setattr(pack_launch, "_held_pack_launch", no_stop)
            expected = "PROBE_WORKER_STOP_REQUIRED"
        elif failure == "changed_account":
            original = module.FileLease

            def changed(inventory):
                raw = json.loads(declaration.read_bytes())
                declaration.write_bytes(canonical(raw | {"profile_id": "b" * 32}))
                return original(inventory)

            monkeypatch.setattr(module, "FileLease", changed)
            expected = "BOOTSTRAP_FILE_CHANGED"
        else:
            expected = "PROBE_PACK_CUSTODY_CLOSED" if failure == "parent_closed" else "SYNTHETIC_RUNTIME_CHANGED"
        with pytest.raises(IntegrityError if failure == "changed_account" else Fault, match=expected):
            with holder:
                if failure == "parent_closed":
                    software.close()
                elif failure == "runtime_recheck":
                    def changed():
                        raise Fault("SYNTHETIC_RUNTIME_CHANGED")
                    monkeypatch.setattr(holder._workers["experienced"]["a1"].runtime, "recheck", changed)
                else:
                    pytest.fail("invalid inputs reached config custody")
                holder.check()
        assert holder.closed
        if failure in ("stop", "changed_account"):
            assert all(not Path(g["a1"]["configuration_path"]).exists() for g in supplied.values())
        service.preparation.check()
        assert reserved_resources(service.db.connection, "probe-worker") == capacity
        assert service.preparation.runtime.budgets.status("probe-total")["committed_and_reserved"]["spend_microusd"] == 200
