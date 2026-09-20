"""Real listener/session/process tests against the synthetic native bridge JVM."""

import json
import os
import time

import pytest

from mcbench.forge_guard import ForgeGuardGrant, NativeHealth, connection_for, listener_owned_by
from mcbench.storage import Fault, canonical, digest
import test_native_game_jvm as native_fixtures
from test_native_game_jvm import prepare
from test_process_guard import event, grant_for, guardian, reply

pytestmark = pytest.mark.skipif(os.name != "nt", reason="Windows listener ownership required")
game_jvm_factory = native_fixtures.game_jvm_factory


@pytest.mark.parametrize("reason,expected", [
    ("PROCESS_STOP_UNCONFIRMED", "PROCESS_STOP_UNCONFIRMED"),
    ("private/token-or-path", "PROCESS_GUARD_FAILURE"),
])
def test_main_failure_preserves_only_a_bounded_code(monkeypatch, capsys, reason, expected):
    import mcbench.forge_guard as module

    def fail(*_args):
        raise Fault(reason)

    monkeypatch.setattr(module.sys, "argv", ["forge_guard", "--grant", "unused.json"])
    monkeypatch.setattr(module, "read_grant", fail)
    assert module.main() == 1
    captured = capsys.readouterr()
    assert captured.err == ""
    assert json.loads(captured.out) == {
        "schema": "strata/ProcessGuardEvent/1", "kind": "failed",
        "reason": expected, "termination_confirmed": False,
    }


def forge_grant(client, process, tmp_path, **changes):
    raw = client.connection.model_dump(mode="json", by_alias=True)
    raw["bearer_token"] = client.connection.bearer_token.get_secret_value()
    path = tmp_path / "synthetic-native-connection.json"
    path.write_bytes(canonical(raw))
    base = grant_for(process).model_dump(by_alias=True)
    return ForgeGuardGrant.model_validate({**base, "schema": "strata/ForgeProcessGuardGrant/1",
        "campaign_id": "campaign", "agent_id": "avatar", "connection_file": str(path),
        "connection_digest": digest(raw), "native_fingerprint": "a" * 64,
        "body_fingerprint": "a" * 64, "capability_digest": "c" * 64, "primitive_limit": 1000,
        **changes})


def test_actual_listener_belongs_to_granted_jvm_and_rejects_sibling(game_jvm_factory, tmp_path):
    with game_jvm_factory(actions=True) as (client, java, _), game_jvm_factory() as (_, sibling, __):
        listener_owned_by(client.connection.port, java.pid)
        with pytest.raises(Fault, match="PROCESS_LISTENER_MISMATCH"):
            listener_owned_by(client.connection.port, sibling.pid)
        grant = forge_grant(client, java, tmp_path)
        assert connection_for(grant).connection == client.connection
        with pytest.raises(Fault, match="PROCESS_CONNECTION_MISMATCH"):
            connection_for(grant.model_copy(update={"connection_digest": "0" * 64}))
        assert java.poll() is None and sibling.poll() is None


@pytest.mark.parametrize("patch", [{"agent_id": "sibling"}, {"capability_digest": "f" * 64},
                                   {"body_fingerprint": "f" * 64}, {"primitive_limit": 999}])
def test_native_authority_mismatch_cannot_attach_or_arm(game_jvm_factory, tmp_path, patch):
    with game_jvm_factory(actions=True) as (client, java, _):
        grant = forge_grant(client, java, tmp_path, **patch)
        monitor = NativeHealth(grant, connection_for(grant))
        try:
            with pytest.raises(Fault, match="PROCESS_NATIVE_AUTHORITY_MISMATCH"):
                monitor.prepare()
            assert java.poll() is None
            assert client.call("lane_status", {})["epoch"] is None
        finally:
            monitor.stop.set()


def test_already_armed_native_lane_is_denied_without_terminating_existing_body(game_jvm_factory, tmp_path):
    with game_jvm_factory(actions=True) as (client, java, _):
        prepare(client)
        grant = forge_grant(client, java, tmp_path)
        monitor = NativeHealth(grant, connection_for(grant))
        try:
            with pytest.raises(Fault, match="PROCESS_NATIVE_ALREADY_ARMED"):
                monitor.prepare()
            assert java.poll() is None
            assert not client.call("lane_status", {})["fenced"]
        finally:
            monitor.stop.set()


def test_frozen_native_thread_stops_even_while_supervisor_keeps_answering(game_jvm_factory,
                                                                      tmp_path, record_property):
    freeze = tmp_path / "freeze-native-thread"
    with game_jvm_factory(actions=True, freeze_file=freeze) as (client, java, _):
        grant = forge_grant(client, java, tmp_path)
        with guardian(tmp_path, grant, "mcbench.forge_guard") as (guard, events):
            reply(guard, event(events, "challenge"))
            started = time.monotonic()
            freeze.touch()
            renewed = 0
            while True:
                item = json.loads(events.get(timeout=3))
                if item["kind"] == "challenge":
                    reply(guard, item)
                    renewed += 1
                elif item["kind"] == "termination_timing":
                    assert item["policy"] == "job-call-wait-qpc/1"
                    assert item["job_succeeded"] and item["wait_result"] == "signaled"
                    assert item["wait_bound_ms"] == 500
                    assert 0 <= item["job_returned_after_ns"] <= item["wait_started_after_ns"] <= item["wait_returned_after_ns"]
                else:
                    assert item["kind"] == "stopped"
                    assert item["reason"] != "PROCESS_LEASE_EXPIRED"
                    assert item["termination_confirmed"] and not item["release_confirmed"]
                    break
            java.wait(timeout=1)
            elapsed = time.monotonic() - started
            record_property("native_freeze_to_process_exit_ms", round(elapsed * 1000, 3))
            assert renewed > 0 and elapsed < 2.25
            assert guard.wait(timeout=5) == 1
