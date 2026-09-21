"""Operator-configured stdio adapter; no listening socket or model-selected paths.

The supplied config and all broker persistence must stay outside gameplay access.
This adapter does not claim that merely launching MCP establishes isolation.
"""

import argparse
import http.client
import json
import sys
from pathlib import Path
from urllib.parse import urlsplit

from pydantic import ValidationError

from .broker import ARGUMENTS, NativeBroker
from .contracts import RpcRequest
from .storage import CAS, Database, Fault, canonical, reject_links, require


class WorkerTransport:
    def __init__(self, descriptor):
        require(set(descriptor) == {"url", "token", "campaign_id", "agent_id", "epoch"},
                "BROKER_WORKER_DESCRIPTOR")
        endpoint = urlsplit(descriptor["url"])
        require(endpoint.scheme == "http" and endpoint.hostname == "127.0.0.1" and
                endpoint.path == "/v1/game" and not endpoint.username and not endpoint.password
                and not endpoint.query and not endpoint.fragment and endpoint.port is not None,
                "BROKER_WORKER_DESCRIPTOR")
        require(isinstance(descriptor["token"], str) and 16 <= len(descriptor["token"]) <= 256
                and all(32 < ord(c) < 127 for c in descriptor["token"]), "BROKER_WORKER_DESCRIPTOR")
        self.port, self.descriptor = endpoint.port, descriptor

    def __call__(self, request: RpcRequest):
        require(all(getattr(request, k) == self.descriptor[k] for k in (
            "campaign_id", "agent_id", "epoch")), "BROKER_SCOPE")
        payload = canonical(request.model_dump())
        require(len(payload) <= 65536, "BROKER_REQUEST_LIMIT")
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5.5)
        try:
            connection.request("POST", "/v1/game", body=payload, headers={
                "Authorization": "Bearer " + self.descriptor["token"],
                "Content-Type": "application/json"})
            response = connection.getresponse()
            require(response.status in {200, 400, 403}, "BROKER_WORKER_RESPONSE")
            data = response.read(131073)
            require(len(data) <= 131072, "BROKER_RESPONSE_LIMIT")
            result = json.loads(data)
            require(isinstance(result, dict) and result.get("schema") == "strata/GameResponse/1"
                    and result.get("status") in {"ok", "error"}, "BROKER_WORKER_RESPONSE")
            return result
        finally:
            connection.close()


def respond(broker, request, game_transport=None):
    require(isinstance(request, dict) and request.get("jsonrpc") == "2.0", "BROKER_PROTOCOL")
    method, params = request.get("method"), request.get("params", {})
    if method == "initialize":
        require(params.get("protocolVersion") in {"2024-11-05", "2025-03-26", "2025-06-18", "2026-07-28"},
                "BROKER_PROTOCOL")
        return {"protocolVersion": params["protocolVersion"],
            "serverInfo": {"name": "strata-native-broker", "version": "1"},
            "capabilities": {"tools": {}}}
    if method == "tools/list":
        descriptions = {
            "artifact_read": "Read one artifact explicitly available to this caller.",
            "artifact_write": "Write an own note/skill draft or helper result; does not activate skills.",
            "artifact_list": "List this caller's admitted artifacts and own drafts.",
            "game": "Call the existing scoped game worker. Executor only; never retries uncertain calls.",
        }
        return {"tools": [{"name": name, "description": descriptions[name],
            "inputSchema": model.model_json_schema(), "annotations": {
                "readOnlyHint": name in {"artifact_read", "artifact_list"},
                "openWorldHint": False}}
            for name, model in ARGUMENTS.items()]}
    if method == "tools/call":
        try:
            result = broker.call(params.get("name"), params.get("arguments"), params.get("_meta"),
                                 game_transport=game_transport)
            return {"content": [{"type": "text", "text": canonical(result).decode()}]}
        except (Fault, ValidationError) as error:
            # ValidationError contains rejected arguments; never echo them.
            code = error.code if isinstance(error, Fault) else "BROKER_ARGUMENTS_INVALID"
            return {"isError": True, "content": [{"type": "text", "text": code}]}
    if method == "ping":
        return {}
    raise Fault("BROKER_METHOD_FORBIDDEN")


def serve(broker, input_stream, output_stream, game_transport=None, integrity_guard=None):
    while True:
        raw = input_stream.readline(384 * 1024 + 1)
        if not raw:
            break
        # Stop rather than drain an unbounded line or parse a partial JSON request.
        if len(raw) > 384 * 1024 or not raw.endswith(b"\n"):
            break
        request_id = None
        try:
            if integrity_guard:
                integrity_guard()
            request = json.loads(raw)
            if isinstance(request, dict) and "id" not in request:
                continue
            request_id = request.get("id")
            require(type(request_id) in {str, int}, "BROKER_PROTOCOL")
            result = respond(broker, request, game_transport)
            answer = {"jsonrpc": "2.0", "id": request_id, "result": result}
        except Exception:
            answer = {"jsonrpc": "2.0", "id": request_id,
                      "error": {"code": -32600, "message": "BROKER_REQUEST_REJECTED"}}
        output_stream.write(canonical(answer) + b"\n")
        output_stream.flush()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()
    run_config(args.config)


def run_config(path, *, integrity_guard=None, bootstrap_digest=None):
    reject_links(path.absolute())
    config = json.loads(path.read_bytes())
    sealed = bootstrap_digest is not None
    require(set(config) == ({"schema", "database", "objects", "runtime_id", "worker_grant"} if sealed
                           else {"database", "objects", "runtime_id", "profile_digest", "worker_grant"}),
            "BROKER_CONFIG")
    db = Database(Path(config["database"]))
    try:
        if sealed:
            from .native import NativeLaunch
            require(config["schema"] == "strata/SealedBrokerConfig/1", "BROKER_CONFIG")
            row = db.connection.execute("SELECT plan,state FROM native_jobs WHERE id=?",
                                        (config["runtime_id"],)).fetchone()
            require(row is not None and row["state"] in {"STARTING", "RUNNING"}, "BROKER_RUNTIME_REVOKED")
            plan = NativeLaunch.model_validate_json(row["plan"])
            require(plan.bootstrap_digest == bootstrap_digest, "BROKER_BOOTSTRAP_MISMATCH")
            config["profile_digest"] = plan.profile_digest()
        broker = NativeBroker(db, CAS(db, Path(config["objects"])), config["runtime_id"],
                              config["profile_digest"])
        transport = None
        if config["worker_grant"] is not None:
            path = Path(config["worker_grant"])
            reject_links(path.absolute())
            transport = WorkerTransport(json.loads(path.read_bytes()))
        serve(broker, sys.stdin.buffer, sys.stdout.buffer, transport, integrity_guard)
    finally:
        db.close()


if __name__ == "__main__":
    main()
