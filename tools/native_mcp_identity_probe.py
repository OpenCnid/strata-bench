"""Credential-free native root/helper MCP identity experiment, not qualification.

The stdio server only echoes fixture text/metadata. It has no path, network,
process or game operation. Its owned log path comes from operator argv only.
"""

import argparse
import json
import os
import sys
from pathlib import Path


def serve(log):
    for line in sys.stdin.buffer:
        if len(line) > 65536:
            return
        request = json.loads(line)
        if "id" not in request:
            continue
        method = request.get("method")
        if method == "initialize":
            result = {
                "protocolVersion": request["params"]["protocolVersion"],
                "serverInfo": {"name": "strata-owned-identity-probe", "version": "1"},
                "capabilities": {"tools": {}},
            }
        elif method == "tools/list":
            result = {"tools": [{
                "name": "inspect_identity", "description": "Echo synthetic caller metadata.",
                "inputSchema": {"type": "object", "properties": {
                    "note": {"type": "string"}, "threadId": {"type": "string"},
                    "_meta": {"type": "object"}}, "required": ["note"]},
                "annotations": {"readOnlyHint": True, "openWorldHint": False},
            }]}
        elif method == "tools/call":
            params = request["params"]
            observed = {"server_pid": os.getpid(), "params": params}
            # Each helper may start its own server; use one file per process.
            target = log.with_name(log.stem + "-" + str(os.getpid()) + log.suffix)
            with target.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(observed) + "\n")
            result = {"content": [{"type": "text", "text": json.dumps(observed)}]}
        elif method == "ping":
            result = {}
        else:
            print(json.dumps({"jsonrpc": "2.0", "id": request["id"],
                "error": {"code": -32601, "message": "Unsupported method"}}), flush=True)
            continue
        print(json.dumps({"jsonrpc": "2.0", "id": request["id"], "result": result}), flush=True)


def run(binary, output, broker_mode=False, canary_mode=False):
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    import threading
    import time
    from datetime import datetime, timezone
    from mcbench.broker import BrokerGrant, NativeBroker
    from mcbench.budgets import DIMENSIONS
    from mcbench.inference_dispatch import InferenceDispatches
    from mcbench.native import NativeExec, NativeLaunch
    from mcbench.native_broker_policy import validate_broker_settings
    from mcbench.plugins import install_dovetail
    from mcbench.storage import CAS, Database, require
    from native_dispatch_probe import LocalProvider, close_budget, ledger, plan_for, put, sse, wait_job
    from native_restricted_tools_probe import RESTRICTIONS
    from native_broker_canaries import Canaries

    require(not canary_mode or broker_mode, "CANARY_BROKER_REQUIRED")
    canaries = Canaries(output) if canary_mode else None

    class Provider(LocalProvider):
        def __init__(self, *args, **kwargs):
            self.steps, self.identities, self.outputs = {}, [], []
            self.direct_calls = []
            super().__init__(*args, **kwargs)

        def respond(self, handler, body, index, operation):
            metadata = json.loads(body["client_metadata"]["x-codex-turn-metadata"])
            agent = metadata["agent_name"]
            require(agent in {"/root", "/root/identity_child"}, "UNEXPECTED_AGENT")
            self.identities.append({"agent": agent, "thread_id": metadata["thread_id"]})
            self.outputs.extend(i for i in body.get("input", []) if i.get("type") in {
                "custom_tool_call_output", "function_call_output"})
            step = self.steps.get(agent, 0)
            self.steps[agent] = step + 1
            root_id = next(i["thread_id"] for i in self.identities if i["agent"] == "/root")
            item = {"id": "message-" + operation, "type": "message", "role": "assistant",
                "status": "completed", "content": [{"type": "output_text",
                "text": "Synthetic identity probe finished.", "annotations": []}]}
            if step == 0:
                args = {"note": agent}
                if agent != "/root":
                    args.update(threadId=root_id, _meta={"threadId": root_id})
                code = ('const t = ALL_TOOLS.find(t=>t.name.endsWith("__inspect_identity")); '
                    'text({catalog:ALL_TOOLS.map(t=>t.name)}); '
                    'if (!t) throw new Error("MCP_TOOL_MISSING"); '
                    'text(await tools[t.name](' + json.dumps(args) + '));')
                if broker_mode:
                    # Test-only enrollment from the already-admitted fixed provider
                    # request. This does not implement live child-budget admission.
                    connection = Database(self.database_path)
                    try:
                        objects = CAS(connection, self.objects)
                        broker = NativeBroker(connection, objects, "root", self.plan.profile_digest())
                        admission = put(objects, {"is_example": True, "operation_id": operation,
                            "scope": "already admitted synthetic provider request only"})
                        grant = BrokerGrant.model_validate({"schema": "strata/NativeBrokerGrant/1",
                            "runtime_id": "root", "session_id": root_id,
                            "thread_id": metadata["thread_id"],
                            "parent_thread_id": None if agent == "/root" else root_id,
                            "profile_digest": self.plan.profile_digest(), "model": body["model"],
                            "role": "executor" if agent == "/root" else "helper",
                            "namespace": "root-artifacts" if agent == "/root" else "helper-results",
                            "campaign_id": "synthetic-campaign", "agent_id": "a1", "epoch": 1,
                            "depth": 0 if agent == "/root" else 1,
                            "expires_unix_ms": self.grant_expiry, "tool_calls": 20,
                            "admission_ref": admission})
                        broker.admit(grant)
                        broker.project(grant.thread_id, "supplied/plan.md", "STRATA_SCOPED_PLAN")
                        if agent == "/root":
                            broker.project(grant.thread_id, "initial/skill.md", "STRATA_IMMUTABLE_SKILL")
                            broker.project(grant.thread_id, "docs/root-only.md", "STRATA_ROOT_ONLY_CANARY")
                    finally:
                        connection.close()
                    game_request = {"schema": "strata/GameRequest/1",
                        "request_id": "game-root" if agent == "/root" else "game-child",
                        "campaign_id": "synthetic-campaign", "agent_id": "a1", "epoch": 1,
                        "deadline_at": datetime.fromtimestamp(time.time()+5, timezone.utc).isoformat(
                            timespec="milliseconds").replace("+00:00", "Z"),
                        "method": "observe", "action": None, "target_request_id": None, "after": None}
                    calls = [("artifact_read", {"path": "supplied/plan.md"}),
                        ("artifact_write", {"path": "notes/root.md" if agent == "/root" else
                            "results/advice.md", "text": "STRATA_OWN_ARTIFACT", "expected_ref": None}),
                        ("game", {"request": game_request})]
                    if agent != "/root":
                        calls.extend([("artifact_read", {"path": "docs/root-only.md"}),
                            ("artifact_write", {"path": "notes/root.md", "text": "spoof", "expected_ref": None}),
                            ("artifact_read", {"path": "docs/root-only.md", "_meta": {"threadId": root_id}})])
                    else:
                        calls.append(("artifact_write", {"path": "initial/skill.md",
                            "text": "spoof", "expected_ref": None}))
                    code = 'const calls=' + json.dumps(calls) + '; for (const [name,args] of calls) {' + (
                        ' const t=ALL_TOOLS.find(t=>t.name.endsWith("__"+name)); '
                        ' if (!t) throw new Error("MCP_TOOL_MISSING:"+name); '
                        ' text({name,result:await tools[t.name](args)}); }')
                    if canaries:
                        code += "\n" + canaries.code()
                item = {"id": "tool-" + operation, "type": "custom_tool_call",
                    "call_id": "call-" + operation, "namespace": "functions", "name": "exec",
                    "input": code}
            elif agent == "/root" and step in {1, 2}:
                call = ("spawn_agent", {"task_name": "identity_child", "fork_turns": "none",
                    "message": "Exercise only the synthetic inspect_identity tool. "
                               "Do not read files or call any other tool."}) if step == 1 else (
                    "wait_agent", {"timeout_ms": 10000})
                item = {"id": "tool-" + operation, "type": "function_call",
                    "call_id": "call-" + operation, "namespace": "collaboration",
                    "name": call[0], "arguments": json.dumps(call[1])}
            elif canaries and step == (3 if agent == "/root" else 1):
                call_id = "direct-" + operation
                self.direct_calls.append(call_id)
                item = {"id": "tool-" + operation, "type": "function_call", "call_id": call_id,
                    "namespace": "functions", "name": "exec_command",
                    "arguments": json.dumps({"cmd": canaries.command(), "login": False,
                                              "max_output_tokens": 1000})}
            else:
                require(step == (3 if agent == "/root" else 1) + int(canary_mode), "UNEXPECTED_RETRY")
            response = {"id": "response-" + operation, "object": "response", "created_at": 1,
                "status": "completed", "model": body["model"], "output": [item], "usage": {
                    "input_tokens": 10, "output_tokens": 4, "total_tokens": 14,
                    "input_tokens_details": {"cached_tokens": 2},
                    "output_tokens_details": {"reasoning_tokens": 0}}}
            handler.response_started = True
            handler.send_response(200)
            handler.send_header("Content-Type", "text/event-stream")
            handler.end_headers()
            handler.wfile.write(sse("response.created", response={
                **response, "status": "in_progress", "output": []}))
            handler.wfile.write(sse("response.output_item.done", output_index=0, item=item))
            handler.wfile.write(sse("response.completed", response=response))
            handler.wfile.flush()
            return {}, response["id"]

    db = Database(output / "synthetic.sqlite")
    cas = CAS(db, output / "objects")
    runtime = NativeExec(db, cas, simulation=True)
    gate = InferenceDispatches(db, cas, simulation=True)
    limits = dict.fromkeys(DIMENSIONS, 2000000) | {"spend_microusd": 120000}
    gate.budgets.create_account("project", limits, "*")
    gate.budgets.create_account("a1", limits, "synthetic-campaign", "a1", "project",
        category="development")
    provider = Provider(db.path, cas.root, "identity", wire=True, max_requests=12)
    worker_calls = []
    worker = None
    if broker_mode:
        class Worker(BaseHTTPRequestHandler):
            def log_message(self, *_):
                pass

            def do_POST(self):
                require(self.path == "/v1/game" and self.headers.get("Authorization") ==
                    "Bearer STRATA_SYNTHETIC_WORKER_SECRET", "WORKER_AUTH")
                r = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                worker_calls.append(r)
                raw = json.dumps({"schema": "strata/GameResponse/1", "status": "ok",
                    "request_id": r["request_id"], "result": {"is_example": True,
                    "visible_control": "STRATA_SCOPED_GAME_CONTROL"}}).encode()
                self.send_response(200)
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)
        worker = ThreadingHTTPServer(("127.0.0.1", 0), Worker)
        worker_thread = threading.Thread(target=worker.serve_forever, daemon=True)
        worker_thread.start()
    try:
        plan = plan_for(binary, output, provider, "root")
        installed = install_dovetail(binary, Path(plan.profile_directory))
        config = plan.config_overrides | installed["required_config_overrides"] | RESTRICTIONS | {
            "mcp_servers.strata_probe": {"command": sys.executable,
                "args": [str(Path(__file__).resolve()), "--serve", str(output / "mcp.jsonl")],
                "enabled_tools": ["inspect_identity"], "required": True,
                "startup_timeout_sec": 10, "tool_timeout_sec": 5},
        }
        if broker_mode:
            config.pop("mcp_servers.strata_probe")
            config["mcp_servers.strata_broker"] = {"command": sys.executable,
                "args": ["-m", "mcbench.broker_stdio", "--config", str(output / "broker.json")],
                "env": {"PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src")},
                "enabled_tools": ["artifact_read", "artifact_write", "artifact_list", "game"],
                "tools": {"artifact_write": {"approval_mode": "approve"},
                          "game": {"approval_mode": "approve"}},
                "required": True, "startup_timeout_sec": 10, "tool_timeout_sec": 6}
            validate_broker_settings(config)
        plan = NativeLaunch.model_validate(plan.model_dump() | {"config_overrides": config,
            "hard_timeout_s": 45, "prompt": "Synthetic MCP identity test. Use only the fixed "
            "synthetic broker and one clean-context native helper."})
        provider.plan = plan
        if broker_mode:
            provider.grant_expiry = int((time.time() + 50) * 1000)
            (output / "broker.json").write_text(json.dumps({"database": str(db.path),
                "objects": str(cas.root), "runtime_id": "root", "profile_digest": plan.profile_digest(),
                "worker_grant": str(output / "worker.json")}), encoding="utf-8")
            (output / "worker.json").write_text(json.dumps({
                "url": f"http://127.0.0.1:{worker.server_port}/v1/game",
                "token": "STRATA_SYNTHETIC_WORKER_SECRET", "campaign_id": "synthetic-campaign",
                "agent_id": "a1", "epoch": 1}), encoding="utf-8")
        reserve = ledger(plan, plan.operation_id, parent=None, calls=12, spend=120000,
            pricing=put(cas, {"is_example": True, "real_usd": 0}), inputs=1200000, outputs=120000)
        runtime.start(plan, reserve)
        wait_job(runtime, plan)
    finally:
        for job in list(runtime.live):
            runtime.interrupt(job, "probe_cleanup")
        provider.close()
        if worker:
            worker.shutdown()
            worker.server_close()
            worker_thread.join(3)
        if canaries:
            canaries.close()
    calls = [json.loads(line) for path in sorted(output.glob("mcp-*.jsonl"))
             for line in path.read_text(encoding="utf-8").splitlines()]
    result = {"schema": "strata/NativeMcpIdentityProbe/1", "is_example": True,
        "production_qualified": False, "real_usd": 0, "profile_digest": plan.profile_digest(),
        "identities": provider.identities, "broker_calls": calls,
        "provider_errors": provider.errors, "outputs": provider.outputs,
        "runtime": runtime.status(plan.job_id), "requests": len(provider.requests),
        "closure": close_budget(runtime, plan, provider), "budget": gate.budgets.status("project")}
    if broker_mode:
        result["schema"] = "strata/NativeBrokerProbe/1"
        result["worker_calls"] = worker_calls
        result["files"] = [dict(r) for r in db.connection.execute(
            "SELECT namespace,path,immutable FROM broker_files ORDER BY namespace,path")]
        outputs = json.dumps(provider.outputs)
        result["checks"] = {
            "executor_worker_once": len(worker_calls) == 1 and worker_calls[0]["request_id"] == "game-root",
            "positive_game_return": "STRATA_SCOPED_GAME_CONTROL" in outputs,
            "helper_result_written": any(r["namespace"] == "helper-results" and
                r["path"] == "results/advice.md" for r in result["files"]),
            "helper_game_denied": "BROKER_GAME_FORBIDDEN" in outputs,
            "root_only_projection_not_returned": "STRATA_ROOT_ONLY_CANARY" not in outputs,
            "immutable_and_parent_write_denied": "BROKER_WRITE_FORBIDDEN" in outputs,
            "spoof_arguments_denied": "BROKER_ARGUMENTS_INVALID" in outputs,
            "worker_credential_not_returned": "STRATA_SYNTHETIC_WORKER_SECRET" not in outputs,
            "provider_clean": not provider.errors and len(provider.requests) == (8 if canary_mode else 6),
        }
        if canaries:
            result["canaries"] = canaries.report(provider.direct_calls)
            result["checks"].update(result["canaries"]["checks"])
    db.export_journal(output / "journal.jsonl")
    db.close()
    (output / "result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return {k: v for k, v in result.items() if k != "outputs"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--serve", type=Path)
    parser.add_argument("--codex", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--broker", action="store_true")
    parser.add_argument("--canaries", action="store_true")
    args = parser.parse_args()
    if args.serve:
        serve(args.serve)
        return
    from mcbench.inventory import file_hash
    from mcbench.storage import require
    from native_dispatch_probe import BINARY_SHA256
    require(args.codex and args.output, "ARGUMENTS_REQUIRED")
    require(os.name == "nt" and file_hash(args.codex) == BINARY_SHA256, "RUNTIME_PIN_MISMATCH")
    root, output = Path(__file__).resolve().parents[1], args.output.resolve()
    require(not output.exists() and not output.is_relative_to(root), "PRIVATE_FRESH_OUTPUT_REQUIRED")
    output.mkdir(parents=True)
    paths = [Path(__file__), root / "tools/native_restricted_tools_probe.py",
        root / "tools/native_dispatch_probe.py", root / "src/mcbench/native.py",
        root / "src/mcbench/plugins.py", root / "src/mcbench/broker.py", root / "src/mcbench/broker_stdio.py",
        root / "src/mcbench/native_broker_policy.py", root / "tools/native_broker_canaries.py"]
    (output / "manifest.json").write_text(json.dumps({"binary_sha256": BINARY_SHA256,
        "source_sha256": {p.relative_to(root).as_posix(): file_hash(p) for p in paths},
        "production_qualified": False}, indent=2), encoding="utf-8")
    result = run(args.codex.resolve(), output, args.broker, args.canaries)
    print(json.dumps(result, indent=2))
    if args.broker:
        require(all(result["checks"].values()), "BROKER_FIXTURE_FAILED")


if __name__ == "__main__":
    main()
