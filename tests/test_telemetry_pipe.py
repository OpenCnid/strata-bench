"""Synthetic stream rules; actual token/pipe/JVM controls remain separate."""

import copy
import hashlib
import json
import time
import threading
from pathlib import Path
from types import SimpleNamespace

import pytest

from mcbench.storage import Fault, canonical
from strata_evaluator.craft_reference import CraftReferencePlan
from strata_evaluator.telemetry_auth import parse_authority, SpoolVerifier
from strata_evaluator.telemetry_pipe import TelemetryPipeBroker
from test_craft_reference import reference  # noqa: F401
from test_private_pipe import group, SCOPE  # noqa: F401


@pytest.fixture
def sink(reference, tmp_path):  # noqa: F811
    store, setup, events, directory, _ = reference
    store.seal(setup, directory)
    authority = parse_authority(json.loads((directory / "authority.json").read_bytes()))
    broker = object.__new__(TelemetryPipeBroker)
    broker.authority, broker.setup = authority, CraftReferencePlan.model_validate(setup)
    module = tmp_path / "module.jar"
    module.write_bytes(b"synthetic module")
    broker.plan = SimpleNamespace(executable=SimpleNamespace(path=str(tmp_path / "java.exe")),
        module_file=SimpleNamespace(path=str(module), sha256=hashlib.sha256(module.read_bytes()).hexdigest()),
        server_port=25569)
    broker.spool = tmp_path / "private-spool"
    broker.spool.mkdir()
    broker.settings = {"max_events": 10, "max_bytes": 65536}
    broker.count, broker.bytes, broker.previous = 0, 0, "0" * 64
    broker.boot, broker.last_tick, broker.stopped, broker.output = None, -1, False, None
    receipts, states = [], []
    broker.pipe = SimpleNamespace(send=receipts.append)
    broker._record = lambda state, **values: states.append((state, values))
    identity = {"pid": 1234, "process_started_unix_ms": 1000, "executable": broker.plan.executable.path}
    first = copy.deepcopy(events[0])
    first["payload_schema"] = "strata/ServerStarted/5"
    first["payload"]["module"] = "strata-forge1192-telemetry/0.3.4"
    first["payload"]["launch_identity"] = {"policy": "native-server-launch-observation/1", **identity,
        "game_directory": setup["game_directory"], "world_directory": setup["fixture_directory"],
        "module_file": str(module), "module_sha256": broker.plan.module_file.sha256,
        "online_mode": True, "server_port": 25569}
    key = Path(authority.key_file).read_bytes()
    try:
        yield broker, first, identity, key, receipts, states
    finally:
        if broker.output is not None:
            broker.output.close()


def test_operator_signs_exact_event_and_acknowledges_only_durable_sequence(sink):
    broker, first, identity, key, receipts, states = sink
    raw = canonical(first) + b"\n"
    broker._event(raw, identity, key)
    assert [state for state, _ in states] == ["CLAIMED", "DURABLE"]
    wire = next(broker.spool.glob("*.authenticated.jsonl")).read_bytes()
    with SpoolVerifier(broker.authority.model_dump(by_alias=True)) as verifier:
        assert verifier.verify(wire) == raw
    expected = canonical({"schema": "strata/TelemetryPipeReceipt/1", "sequence": 1,
                          "event_sha256": hashlib.sha256(raw).hexdigest()})
    assert receipts == [expected]
    assert key.hex().encode() not in expected and str(broker.authority.key_file).encode() not in expected
    assert broker.count == 1 and broker.bytes == len(wire)


@pytest.mark.parametrize("transport", ["windows-owned-pipe/1", "private-file/1"])
def test_history_module_preserves_pipe_identity_gate_before_claim(sink, transport):
    from strata_evaluator.setup_facts import PINS, POLICY as POINT_POLICY
    from strata_evaluator.setup_history import POLICY, ROUTES
    broker, first, identity, key, receipts, _ = sink
    first["payload_schema"] = "strata/ServerStarted/8"
    first["payload"].update(module="strata-forge1192-telemetry/0.3.7", telemetry_transport=transport,
        setup_capture_policy=POINT_POLICY, setup_capture_support={"status": "supported", "artifacts": PINS},
        setup_history_support={"policy": POLICY, "vanilla_hooks_verified": True,
            "team_hooks_verified": True, "all_mutation_routes_covered": False})
    if transport == "private-file/1":
        with pytest.raises(Fault, match="TELEMETRY_PIPE_TRANSPORT"):
            broker._event(canonical(first) + b"\n", identity, key)
        assert not receipts and not Path(broker.authority.key_file + ".claimed").exists()
    else:
        broker._event(canonical(first) + b"\n", identity, key)
        history = first | {"kind": "setup_history", "payload_schema": "strata/NativeSetupHistory/1",
            "seq": 2, "server_event_seq": 2, "server_tick": 1,
            "payload": {"policy": POLICY, "phase": "startup", "transaction_id": None,
                        "attempts": dict.fromkeys(sorted(ROUTES), 0), "off_thread_attempts": 0,
                        "overflowed": False}}
        broker._event(canonical(history) + b"\n", identity, key)
        assert broker.count == 2 and len(receipts) == 2


@pytest.mark.parametrize("change", ["pid", "world", "module", "port", "campaign", "sequence", "visibility",
                                   "framing", "boot_path"])
def test_mismatched_first_event_never_claims_or_signs(sink, change):
    broker, first, identity, key, receipts, _ = sink
    native = first["payload"]["launch_identity"]
    if change == "pid":
        native["pid"] += 1
    elif change == "world":
        native["world_directory"] += "-foreign"
    elif change == "module":
        native["module_sha256"] = "0" * 64
    elif change == "port":
        native["server_port"] += 1
    elif change == "campaign":
        first["campaign_id"] = "foreign"
    elif change == "sequence":
        first["seq"] = first["server_event_seq"] = 2
    elif change == "visibility":
        first["visibility"] = "public"
    elif change == "boot_path":
        first["server_boot_id"] = "alternate:stream"
    raw = canonical(first) + (b"" if change == "framing" else b"\n")
    with pytest.raises((Fault, ValueError)):
        broker._event(raw, identity, key)
    assert not receipts and not list(broker.spool.iterdir())
    assert not Path(broker.authority.key_file + ".claimed").exists()


def test_duplicate_and_quota_failure_preserve_prior_durable_cost_and_claim(sink):
    broker, first, identity, key, receipts, _ = sink
    raw = canonical(first) + b"\n"
    broker._event(raw, identity, key)
    path = next(broker.spool.iterdir())
    before = path.read_bytes()
    with pytest.raises(Fault, match="TELEMETRY_PIPE_EVENT_SCOPE"):
        broker._event(raw, identity, key)
    broker.settings["max_events"] = 1
    first["seq"] = first["server_event_seq"] = 2
    first.update(kind="server_stopped", payload_schema="strata/ServerStopped/1", payload={})
    with pytest.raises(Fault, match="TELEMETRY_PIPE_QUOTA"):
        broker._event(canonical(first) + b"\n", identity, key)
    assert broker.count == 1 and len(receipts) == 1 and path.read_bytes() == before
    assert Path(broker.authority.key_file + ".claimed").exists()


def test_unbound_connected_peer_closes_without_configuration_or_reusable_authority(reference, group, tmp_path):  # noqa: F811
    from multiprocessing.connection import Client
    store, setup, _, directory, _ = reference
    store.seal(setup, directory)
    authority = parse_authority(json.loads((directory / "authority.json").read_bytes()))
    settings = {"schema": "strata/ForgeTelemetryBrokerSettings/1", "campaign_id": authority.campaign_id,
        "epoch": authority.epoch, "max_bytes": 65536, "max_events": 10,
        "recipe_ids": list(setup["recipe_digests"]), "config_queries": []}
    options = dict(writer_sid="unbound", group_sid=group, scope_sid=SCOPE,
                   deadline=time.monotonic() + 15, settings=settings)
    broker = TelemetryPipeBroker(store.database, authority, tmp_path / "pipe-spool", SimpleNamespace(),
                                CraftReferencePlan.model_validate(setup), **options)
    with Client(broker.pipe.name, family="AF_PIPE"):
        started = time.monotonic()
        result = broker.close()
    assert time.monotonic() - started < 5 and not broker.thread.is_alive()
    assert result["status"] == "uncertain" and result["error"] == "TELEMETRY_PIPE_UNBOUND"
    assert not result["configuration_sent"] and result["records"] == 0
    assert not Path(authority.key_file + ".claimed").exists()
    before = store.database.connection.execute("SELECT count(*) FROM outbox").fetchone()[0]
    with pytest.raises(Fault, match="TELEMETRY_PIPE_ALREADY_RESERVED"):
        TelemetryPipeBroker(store.database, authority, tmp_path / "no-replay", SimpleNamespace(),
                            CraftReferencePlan.model_validate(setup), **options)
    assert not (tmp_path / "no-replay").exists()
    assert store.database.connection.execute("SELECT count(*) FROM outbox").fetchone()[0] == before


def test_unobserved_peer_cannot_trigger_a_second_job_observer_or_pid_adoption():
    broker = object.__new__(TelemetryPipeBroker)
    broker.armed, broker.closing = threading.Event(), threading.Event()
    broker.armed.set()
    broker.deadline = time.monotonic() + 0.02
    calls = []
    def identity(pid):
        calls.append(pid)
        raise Fault("PROCESS_MEMBER_UNOBSERVED")
    broker.job = SimpleNamespace(members={}, member_identity=identity)
    # No observe_members or OS PID lookup is supplied to this consumer.
    with pytest.raises(Fault, match="PROCESS_MEMBER_UNOBSERVED"):
        broker._peer(1234)
    assert calls == [1234]
