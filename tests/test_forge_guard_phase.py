"""Synthetic native-read failures; no game, process attachment, or model calls."""

import json
import os
import subprocess
import sys
import threading
import time
from types import SimpleNamespace

import pytest

from mcbench import forge_guard as module
from mcbench.storage import Fault
from test_forge_guard import forge_grant, game_jvm_factory  # noqa: F401


@pytest.mark.parametrize("phase,initialized", [
    (phase, initialized)
    for initialized in (False, True)
    for phase in ("authority", "authority_scope", "listener", "identity", "lane_status", "state")
    if not initialized or phase not in {"authority", "authority_scope"}
])
def test_failure_phase_retains_cause_and_does_not_retry_or_export_response(monkeypatch, phase, initialized):
    grant = SimpleNamespace(campaign_id="campaign", agent_id="avatar", capability_digest="c" * 64,
                            body_fingerprint="b" * 64, primitive_limit=1000, epoch=1,
                            process=SimpleNamespace(pid=123))
    calls = []
    cycles = 0

    def selected():
        return cycles >= (2 if initialized else 1)

    def listener(*_):
        nonlocal cycles
        cycles += 1
        if phase == "listener" and selected():
            raise Fault("PROCESS_LISTENER_MISMATCH")

    def call(operation, args, *, timeout_ms):
        calls.append((operation, args, timeout_ms))
        assert operation in {"authority", "identity", "lane_status"} and args == {} and timeout_ms == 500
        if operation == phase and (operation == "authority" or selected()):
            raise Fault("GAME_OBSERVATION_UNAVAILABLE")
        if operation == "authority":
            return {"campaign_id": "wrong" if phase == "authority_scope" else grant.campaign_id,
                    "agent_id": grant.agent_id, "capability_digest": grant.capability_digest,
                    "body_fingerprint": grant.body_fingerprint, "primitive_limit": grant.primitive_limit,
                    "expires_unix_ms": time.time_ns() // 1000000 + 30000, "private": "secret-response"}
        if operation == "identity":
            return {"body_fingerprint": grant.body_fingerprint, "private": "secret-response"}
        return {"journal_healthy": not (phase == "state" and selected()),
                "fenced": True, "active_request_id": None, "epoch": None}

    monkeypatch.setattr(module, "listener_owned_by", listener)
    monitor = module.NativeHealth(grant, SimpleNamespace(call=call, connection=SimpleNamespace(port=123)))
    try:
        if initialized:
            assert monitor.prepare()["body_fingerprint"] == grant.body_fingerprint
        until = time.monotonic() + 3
        while monitor.error is None and time.monotonic() < until:
            time.sleep(.005)
        assert monitor.error is not None
        with pytest.raises(Fault, match=monitor.error):
            monitor.prepare()
        diagnostic = monitor.failure_diagnostic()
        assert diagnostic == {
            "schema": "strata/ProcessGuardEvent/1", "kind": "native_health_failure",
            "policy": "forge-native-health-phase/1", "phase": phase,
            "elapsed_ms": diagnostic["elapsed_ms"],
            "read_timeout_ms": 500 if phase in {"authority", "identity", "lane_status"} else None,
            "initialized": initialized, "reason": monitor.error,
        }
        assert type(diagnostic["elapsed_ms"]) is int and 0 <= diagnostic["elapsed_ms"] < 3000
        assert "secret-response" not in json.dumps(diagnostic)
        count = len(calls)
        time.sleep(.03)
        assert len(calls) == count and monitor.failure(time.monotonic()) == monitor.error
        diagnostic["phase"] = "tampered"
        assert monitor.failure_diagnostic()["phase"] == phase
    finally:
        monitor.stop.set()


@pytest.mark.parametrize("error", [Fault("private/token/path"), RuntimeError("secret-response")])
def test_exception_contents_never_enter_phase_diagnostic(monkeypatch, error):
    def call(*_, **__):
        raise error
    monitor = module.NativeHealth(SimpleNamespace(), SimpleNamespace(call=call))
    try:
        until = time.monotonic() + 1
        while monitor.error is None and time.monotonic() < until:
            time.sleep(.005)
        diagnostic = monitor.failure_diagnostic()
        assert diagnostic["reason"] == "PROCESS_GUARD_FAILURE"
        assert diagnostic["phase"] == "authority" and diagnostic["initialized"] is False
        assert str(error) not in json.dumps(diagnostic)
    finally:
        monitor.stop.set()


def test_private_diagnostic_is_emitted_only_after_guard_cleanup(monkeypatch, capsys):
    closed = False
    emitted = []
    diagnostic = {"schema": "strata/ProcessGuardEvent/1", "kind": "native_health_failure",
                  "policy": "forge-native-health-phase/1", "phase": "identity", "elapsed_ms": 501,
                  "read_timeout_ms": 500, "initialized": True, "reason": "GAME_OBSERVATION_UNAVAILABLE"}
    monitor = SimpleNamespace(stop=threading.Event(),
        prepare=lambda: {"body_fingerprint": "b" * 64, "connection_generation": 1},
        failure=lambda _: "GAME_OBSERVATION_UNAVAILABLE", failure_diagnostic=lambda: diagnostic)
    grant = SimpleNamespace(connection_digest="c" * 64)

    def guard(*_, **__):
        nonlocal closed
        closed = True
        return {"reason": "GAME_OBSERVATION_UNAVAILABLE"}

    def emit(value):
        assert closed
        emitted.append(value)

    monkeypatch.setattr(module.sys, "argv", ["forge_guard", "--grant", "unused"])
    monkeypatch.setattr(module, "read_grant", lambda *_: grant)
    monkeypatch.setattr(module, "connection_for", lambda _: object())
    monkeypatch.setattr(module, "NativeHealth", lambda *_: monitor)
    monkeypatch.setattr(module, "GuardPipes", lambda *_: SimpleNamespace(emit=emit,
                        outgoing=SimpleNamespace(unfinished_tasks=0)))
    monkeypatch.setattr(module, "guard", guard)
    monkeypatch.setattr(module.os, "_exit", lambda code: emitted.append(code))
    assert module.main() == 1
    assert emitted == [diagnostic, 1] and monitor.stop.is_set()
    assert capsys.readouterr().out == ""


@pytest.mark.skipif(os.name != "nt", reason="Real Windows listener ownership")
@pytest.mark.parametrize("phase", ["authority", "identity", "lane_status"])
def test_actual_java_http_stall_identifies_read_without_attaching_or_arming(game_jvm_factory, tmp_path, phase):  # noqa: F811
    freeze = tmp_path / "freeze-native-thread"
    with game_jvm_factory(actions=True, freeze_file=freeze) as (client, java, root):
        grant = forge_grant(client, java, tmp_path, schema="strata/ForgeProcessGuardGrant/2",
                            shutdown_policy="java-tree1000-lease750/1")
        original = client.call
        assert original("lane_status", {})["epoch"] is None
        journal_before = (root / "game-actions.jsonl").read_bytes()
        calls = []

        def call(operation, args, *, timeout_ms=5000):
            calls.append((operation, timeout_ms))
            if operation == phase:
                freeze.touch()
            return original(operation, args, timeout_ms=timeout_ms)

        client.call = call
        monitor = module.NativeHealth(grant, client)
        try:
            with pytest.raises(Fault, match="GAME_OBSERVATION_UNAVAILABLE"):
                monitor.prepare()
            diagnostic = monitor.failure_diagnostic()
            assert diagnostic["phase"] == phase and diagnostic["read_timeout_ms"] == 500
            assert diagnostic["initialized"] is False and diagnostic["reason"] == "GAME_OBSERVATION_UNAVAILABLE"
            assert monitor.identity is None and not monitor.armed and java.poll() is None
            assert calls == [(p, 500) for p in ("authority", "identity", "lane_status")[:
                ("authority", "identity", "lane_status").index(phase) + 1]]
            assert (root / "game-actions.jsonl").read_bytes() == journal_before
        finally:
            monitor.stop.set()
            freeze.unlink(missing_ok=True)


@pytest.mark.skipif(os.name != "nt", reason="Real Windows listener ownership")
def test_actual_guard_process_emits_failed_verdict_and_private_phase(game_jvm_factory, tmp_path):  # noqa: F811
    freeze = tmp_path / "freeze-native-thread"
    with game_jvm_factory(actions=True, freeze_file=freeze) as (client, java, root):
        grant = forge_grant(client, java, tmp_path, schema="strata/ForgeProcessGuardGrant/2",
                            shutdown_policy="java-tree1000-lease750/1")
        before = (root / "game-actions.jsonl").read_bytes()
        grant_file = tmp_path / "guard-grant.json"
        grant_file.write_text(grant.model_dump_json(by_alias=True), encoding="utf-8")
        freeze.touch()
        result = subprocess.run([sys.executable, "-I", "-m", "mcbench.forge_guard", "--grant", str(grant_file)],
            capture_output=True, timeout=5, creationflags=subprocess.CREATE_NO_WINDOW)
        assert result.returncode == 1 and result.stderr == b"" and len(result.stdout) < 2048
        events = [json.loads(line) for line in result.stdout.splitlines()]
        assert [e["kind"] for e in events] == ["failed", "native_health_failure"]
        assert events[0]["reason"] == "GAME_OBSERVATION_UNAVAILABLE" and events[0]["termination_confirmed"] is False
        assert events[1]["phase"] == "authority" and events[1]["initialized"] is False
        assert events[1]["read_timeout_ms"] == 500 and events[1]["reason"] == events[0]["reason"]
        assert java.poll() is None and (root / "game-actions.jsonl").read_bytes() == before
