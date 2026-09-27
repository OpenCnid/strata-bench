"""Synthetic wire/authority refusals for the private replacement proof consumer."""

import copy
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from mcbench.storage import digest
from mcbench.worker_restart import WorkerRestartClient, WorkerRestartGrant, WorkerRestartState, WorkerRestartUnknown
from mcbench.storage import Fault


def state():
    plan = {"schema": "strata/WorkerRepairPlan/1", "policy": "operator-owned-fixed-repair-pause/1",
        "campaign_id": "campaign", "agent_id": "avatar", "epoch": 1, "lease_id": "lease", "transaction_id": "repair",
        "plan_digest": "a" * 64, "expires_unix_ms": int(time.time() * 1000) + 30000}
    checkpoint = {"schema": "strata/NativeSettingsRestartCheckpoint/1", "source_instance": "old",
        "request": {"schema": "strata/NativeSettingsRestartRequest/1", "transaction_id": "repair", "plan_digest": "a" * 64,
            "restart_id": "restart", "expected_revision": 1, "expected_digest": "b" * 64}}
    return {"schema": "strata/WorkerRestartState/1", "plan": plan, "checkpoint": checkpoint, "phase": "attached",
        "old_connection_digest": "c" * 64, "old_terminal": {"schema": "strata/WorkerRestartOldTerminal/1",
            "checkpoint_digest": digest(checkpoint), "process_digest": "d" * 64, "connection_digest": "c" * 64,
            "termination_confirmed": True},
        "replacement": {"schema": "strata/ProcessGuardEvent/1", "kind": "ready", "process_digest": "e" * 64,
            "campaign_id": "campaign", "agent_id": "avatar", "epoch": 1, "whole_client_lifetime": True,
            "campaign_admission": False, "remaining_wall_ms": 30000, "policy": "forge-process-listener-client-thread/3",
            "connection_digest": "f" * 64, "body_fingerprint": "a" * 64, "connection_generation": 1,
            "implementation_digest": "b" * 64, "python": "3.12.14"},
        "primitive_events": 7, "gameplay_suspended": True, "input_resumed": False}


@pytest.mark.parametrize("path,value", [
    ("input_resumed", True), ("gameplay_suspended", False), ("primitive_events", -1),
    ("old_terminal", None), ("replacement", None), ("old_terminal.termination_confirmed", False),
    ("old_terminal.checkpoint_digest", "0" * 64), ("old_terminal.connection_digest", "0" * 64),
    ("replacement.campaign_id", "sibling"), ("replacement.epoch", 2),
    ("replacement.process_digest", "d" * 64), ("replacement.connection_digest", "c" * 64),
    ("replacement.policy", "forge-process-listener-client-thread/2"), ("replacement.campaign_admission", True),
    ("replacement.whole_client_lifetime", False), ("replacement.private_path", "private"),
    ("checkpoint.request.transaction_id", "foreign"), ("checkpoint.request.plan_digest", "0" * 64),
    ("replacement.epoch", True), ("input_resumed", 0),
])
def test_false_or_foreign_process_proof_cannot_authorize_adoption(path, value):
    valid = state()
    assert WorkerRestartState.model_validate(valid).phase == "attached"
    altered = copy.deepcopy(valid)
    target = altered
    pieces = path.split(".")
    for key in pieces[:-1]:
        target = target[key]
    target[pieces[-1]] = value
    with pytest.raises(ValueError):
        WorkerRestartState.model_validate(altered)


@pytest.mark.parametrize("patch", [
    {"schema": "strata/WorkerRestartGrant/1"}, {"repair_binding_digest": None},
    {"url": "http://localhost:1234/v1/restart"}, {"url": "http://127.0.0.1:0/v1/restart"},
    {"url": "http://127.0.0.1:65536/v1/restart"}, {"token": "public"},
    {"policy": "automatic-resume"}, {"private": "extra"},
])
def test_restart_grant_requires_exact_loopback_policy_and_worker_binding(patch):
    raw = {"schema": "strata/WorkerRestartGrant/2", "policy": "operator-owned-client-replacement/1",
        "repair_binding_digest": "b" * 64, "url": "http://127.0.0.1:1234/v1/restart", "token": "a" * 64,
        "campaign_id": "campaign", "agent_id": "avatar", "epoch": 1, "lease_id": "lease"}
    assert WorkerRestartGrant.model_validate(raw).port == 1234
    with pytest.raises(ValueError):
        WorkerRestartGrant.model_validate(raw | patch)


@pytest.mark.parametrize("failure", ["dropped", "duplicate", "foreign_id", "foreign_plan", "oversized", "resume"])
def test_uncertain_transport_never_reposts_or_exports_bad_reply(failure):
    valid = state()
    plan, checkpoint = WorkerRestartState.model_validate(valid).plan, WorkerRestartState.model_validate(valid).checkpoint
    requests = []

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def do_POST(self):
            assert self.path == "/v1/restart" and self.headers["Authorization"] == "Bearer " + "a" * 64
            request = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            requests.append(request)
            if failure == "dropped":
                self.close_connection = True
                return
            result = copy.deepcopy(valid)
            if failure == "foreign_plan":
                result["plan"]["lease_id"] = "foreign"
            if failure == "resume":
                result["input_resumed"] = True
            body = {"schema": "strata/WorkerRestartResponse/1", "request_id": "foreign" if failure == "foreign_id" else request["request_id"],
                "status": "ok", "result": result}
            raw = json.dumps(body).encode()
            if failure == "duplicate":
                raw = raw.replace(b'"status": "ok"', b'"status": "ok", "status": "ok"')
            if failure == "oversized":
                raw = b" " * 16385
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    client = WorkerRestartClient(WorkerRestartGrant.model_validate({"schema": "strata/WorkerRestartGrant/2",
        "policy": "operator-owned-client-replacement/1", "repair_binding_digest": "b" * 64,
        "url": f"http://127.0.0.1:{server.server_port}/v1/restart", "token": "a" * 64,
        "campaign_id": "campaign", "agent_id": "avatar", "epoch": 1, "lease_id": "lease"}))
    try:
        with pytest.raises(WorkerRestartUnknown):
            client.call("detach", plan, checkpoint)
        assert len(requests) == 1 and requests[0]["operation"] == "detach"
        with pytest.raises(Fault, match="RESTART_STATUS_UNAVAILABLE"):
            client.call("status", plan, checkpoint)
        assert [r["operation"] for r in requests] == ["detach", "status"]
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()
