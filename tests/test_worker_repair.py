"""Synthetic HTTP and controller handoff tests; no Minecraft settings qualification."""

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from mcbench.storage import Fault
from mcbench.worker_repair import POLICY, WorkerRepairClient, WorkerRepairGrant, WorkerRepairUnknown
from test_reconfiguration import repair_env as _repair_env

repair_env = _repair_env


@pytest.fixture
def worker_server(repair_env, monkeypatch):
    e = repair_env
    monkeypatch.setattr("mcbench.worker_repair.time.time", lambda: e.now[0])
    requests, modes = [], ["ok"]
    token = "b" * 64

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def do_POST(self):
            assert self.path == "/v1/repair"
            assert self.headers["Authorization"] == "Bearer " + token
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            requests.append(body)
            if modes[0] == "dropped":
                self.close_connection = True
                return
            state = {"schema": "strata/WorkerRepairState/1", "policy": POLICY, "plan": body["plan"],
                "phase": "paused", "reason": None, "inputs_released": True, "primitive_events": 3,
                "gameplay_suspended": True, "resume_authorized": False}
            if modes[0] == "wrong_plan":
                state["plan"] = state["plan"] | {"plan_digest": "c" * 64}
            elif modes[0] == "failed":
                state |= {"phase": "failed", "reason": "REPAIR_DEADLINE_EXPIRED"}
            elif modes[0] == "unreleased":
                state["inputs_released"] = False
            elif modes[0] == "slow":
                e.now[0] += 1.01
                e.mono[0] += 1.01
            elif modes[0] == "extra":
                state["secret"] = "private-canary"
            elif modes[0] == "integer_flags":
                state["gameplay_suspended"], state["resume_authorized"] = 1, 0
            payload = {"schema": "strata/WorkerRepairResponse/1", "request_id": body["request_id"],
                       "status": "ok", "result": state}
            raw = json.dumps(payload).encode()
            if modes[0] == "oversized":
                raw = b" " * 4097
            elif modes[0] == "duplicate":
                raw = raw.replace(b'"status": "ok"', b'"status": "ok", "status": "ok"')
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    e.begin()
    lease = e.controller.input_authority("c1", "owner", e.epoch, "a1")["lease_id"]
    grant = {"schema": "strata/WorkerRepairGrant/1", "policy": POLICY,
        "url": f"http://127.0.0.1:{server.server_port}/v1/repair", "token": token,
        "campaign_id": "c1", "agent_id": "a1", "epoch": e.epoch, "lease_id": lease}
    client = WorkerRepairClient(WorkerRepairGrant.model_validate(grant))
    e.request()
    try:
        yield e, client, requests, modes, grant
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()


def test_controller_enters_from_actual_http_reply_and_repeats_only_status(worker_server):
    e, client, requests, _, grant = worker_server
    result = e.repairs.quiesce_worker("tx", "owner", e.epoch, client)
    assert result["phase"] == "RECONFIGURING"
    stop_ref = result["stop_ref"]
    assert e.repairs.quiesce_worker("tx", "owner", e.epoch, client)["stop_ref"] == stop_ref
    assert [r["operation"] for r in requests] == ["pause", "status"]
    assert requests[0]["plan"] == requests[1]["plan"]
    proof = e.cas.json(e.operator, "operator", stop_ref)
    witness = e.cas.json(e.operator, "operator", proof["source_refs"][0])
    assert witness["reply"]["result"]["plan"]["plan_digest"] == result["request"]["plan_digest"]
    assert witness["is_example"] is True
    assert grant["token"] not in json.dumps(witness)
    assert not e.adapter.requests
    assert e.controller.input_authority("c1", "owner", e.epoch, "a1")["lease_id"] is None
    assert e.controller.input_authority("c1", "owner", e.epoch, "a2")["state"] == "READY"
    assert e.budgets.status("a1")["committed_and_reserved"]["primitive_events"] == 20


@pytest.mark.parametrize("mode", ["dropped", "wrong_plan", "unreleased", "extra", "oversized", "duplicate", "integer_flags"])
def test_uncertain_worker_reply_never_replays_pause_or_admits_settings(worker_server, mode):
    e, client, requests, modes, _ = worker_server
    modes[0] = mode
    with pytest.raises(WorkerRepairUnknown, match="REPAIR_OUTCOME_UNKNOWN"):
        e.repairs.quiesce_worker("tx", "owner", e.epoch, client)
    assert e.repairs.status("tx")["phase"] == "QUIESCING"
    assert not e.adapter.requests
    modes[0] = "ok"
    assert e.repairs.quiesce_worker("tx", "owner", e.epoch, client)["phase"] == "RECONFIGURING"
    assert [r["operation"] for r in requests] == ["pause", "status"]


@pytest.mark.parametrize("mode", ["failed", "slow"])
def test_failed_or_late_pause_does_not_enter_repair(worker_server, mode):
    e, client, _, modes, _ = worker_server
    modes[0] = mode
    with pytest.raises(Fault, match="INPUT_RELEASE_REQUIRED|REPAIR_EVIDENCE_INVALID"):
        e.repairs.quiesce_worker("tx", "owner", e.epoch, client)
    assert e.repairs.status("tx")["phase"] == ("RECOVERY_REQUIRED" if mode == "failed" else "QUIESCING")
    assert not e.adapter.requests


def test_changed_worker_capability_cannot_take_over_consumed_handoff(worker_server):
    e, client, requests, modes, grant = worker_server
    modes[0] = "dropped"
    with pytest.raises(WorkerRepairUnknown):
        e.repairs.quiesce_worker("tx", "owner", e.epoch, client)
    changed = WorkerRepairClient(WorkerRepairGrant.model_validate(grant | {"token": "c" * 64}))
    with pytest.raises(Fault, match="REPAIR_NOT_OWNED"):
        e.repairs.quiesce_worker("tx", "owner", e.epoch, changed)
    assert len(requests) == 1


def test_worker_scope_refusal_precedes_dispatch_and_retained_intent(worker_server):
    e, _, requests, _, grant = worker_server
    changed = WorkerRepairClient(WorkerRepairGrant.model_validate(grant | {"agent_id": "a2"}))
    with pytest.raises(Fault, match="REPAIR_NOT_OWNED"):
        e.repairs.quiesce_worker("tx", "owner", e.epoch, changed)
    assert not requests
    assert e.database.connection.execute("SELECT count(*) FROM repair_worker_handoffs").fetchone()[0] == 0


def test_failed_status_after_entry_revokes_controller_permission(worker_server):
    e, client, requests, modes, _ = worker_server
    e.repairs.quiesce_worker("tx", "owner", e.epoch, client)
    modes[0] = "failed"
    with pytest.raises(Fault, match="INPUT_RELEASE_REQUIRED"):
        e.repairs.quiesce_worker("tx", "owner", e.epoch, client)
    assert e.repairs.status("tx")["phase"] == "RECOVERY_REQUIRED"
    with pytest.raises(Fault, match="REPAIR_RECOVERY_REQUIRED"):
        e.repairs.apply("tx", "owner", e.epoch)
    assert not e.adapter.requests
    assert [r["operation"] for r in requests] == ["pause", "status"]


def test_worker_witness_storage_failure_keeps_intent_and_requires_status(worker_server, monkeypatch):
    e, client, requests, _, _ = worker_server
    original = e.cas.put

    def fail(*_args, **_kwargs):
        raise OSError("synthetic CAS failure")

    monkeypatch.setattr(e.cas, "put", fail)
    with pytest.raises(OSError, match="synthetic CAS failure"):
        e.repairs.quiesce_worker("tx", "owner", e.epoch, client)
    monkeypatch.setattr(e.cas, "put", original)
    with pytest.raises(Fault, match="REPAIR_WORKER_EVIDENCE_REQUIRED"):
        e.repairs.enter("tx", "owner", e.epoch, e.proof())
    assert e.repairs.quiesce_worker("tx", "owner", e.epoch, client)["phase"] == "RECONFIGURING"
    assert [r["operation"] for r in requests] == ["pause", "status"]


def test_private_grant_loading_rejects_external_endpoints_and_redacts_failures(worker_server, tmp_path):
    _, _, _, _, grant = worker_server
    path = tmp_path / "repair.json"
    for patch in [{"url": "http://example.com/v1/repair"}, {"url": "http://127.0.0.1:0/v1/repair"},
                  {"url": "http://127.0.0.1:65536/v1/repair"}, {"extra": grant["token"]},
                  {"token": "credential-canary"}, {"epoch": True}]:
        path.write_text(json.dumps(grant | patch))
        with pytest.raises(Fault, match="^REPAIR_GRANT_INVALID$"):
            WorkerRepairClient.from_file(path)
    path.write_text(json.dumps(grant))
    loaded = WorkerRepairClient.from_file(path)
    assert loaded.grant.token.get_secret_value() == grant["token"]
    assert grant["token"] not in repr(loaded.grant)
