"""Credential-free native identity/broker/admission fixtures, not qualification.

The default stdio server only echoes fixture metadata. Optional broker mode
uses scoped artifacts and an owned synthetic worker; admission mode exercises
durable participant/request budgets. All providers and game outcomes are fake.
"""

import argparse
import base64
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


def run(binary, output, broker_mode=False, canary_mode=False, admission_mode=False,
        inherited_helper=False, bootstrap_mode=False, ingress_mode=False, oauth_mode=False,
        gateway_mode=False, skills_mode=False):
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    import threading
    import time
    from datetime import datetime, timezone
    from mcbench.broker import BrokerGrant, NativeBroker, POLICY
    from mcbench.native_admission import NativeAdmission
    from mcbench.budgets import DIMENSIONS
    from mcbench.inference_dispatch import InferenceDispatches
    from mcbench.native import NativeExec, NativeLaunch
    from mcbench.native_broker_policy import validate_broker_settings
    from mcbench.plugins import install_dovetail
    from mcbench.storage import CAS, Database, Principal, require
    from native_dispatch_probe import LocalProvider, close_budget, ledger, plan_for, put, sse, wait_job
    from native_restricted_tools_probe import RESTRICTIONS
    from native_broker_canaries import Canaries

    require(not canary_mode or broker_mode, "CANARY_BROKER_REQUIRED")
    require(not admission_mode or broker_mode, "ADMISSION_BROKER_REQUIRED")
    require(not inherited_helper or admission_mode and not canary_mode, "INHERITED_ADMISSION_REQUIRED")
    require(not bootstrap_mode or admission_mode, "BOOTSTRAP_ADMISSION_REQUIRED")
    require(not ingress_mode or bootstrap_mode, "INGRESS_BOOTSTRAP_REQUIRED")
    require(not oauth_mode or ingress_mode, "OAUTH_INGRESS_REQUIRED")
    require(not gateway_mode or oauth_mode and not inherited_helper, "GATEWAY_OAUTH_REQUIRED")
    require(not skills_mode or gateway_mode, "SKILLS_GATEWAY_REQUIRED")
    canaries = Canaries(output) if canary_mode else None

    class Provider(LocalProvider):
        def __init__(self, *args, **kwargs):
            self.steps, self.identities, self.outputs = {}, [], []
            self.direct_calls = []
            self.direct_agents = set()
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
                        if admission_mode:
                            grant = NativeAdmission(connection, objects).enroll(operation, tool_calls=20)
                        else:
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
                    if skills_mode:
                        calls.append(("artifact_read", {"path":
                            "initial/dovetail/skills/prompt-engineering/SKILL.md"}))
                        calls.append(("artifact_write", {"path":
                            "initial/dovetail/skills/prompt-engineering/SKILL.md",
                            "text": "must remain immutable", "expected_ref": None}))
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
            elif agent == "/root" and (step in {1, 2} or bootstrap_mode and
                    not inherited_helper and self.steps.get("/root/identity_child", 0) < 2 + int(canary_mode)):
                call = ("spawn_agent", {"task_name": "identity_child", "fork_turns": "all" if inherited_helper else "none",
                    "message": "Exercise only the synthetic inspect_identity tool. "
                               "Do not read files or call any other tool."}) if step == 1 else (
                    "wait_agent", {"timeout_ms": 10000})
                item = {"id": "tool-" + operation, "type": "function_call",
                    "call_id": "call-" + operation, "namespace": "collaboration",
                    "name": call[0], "arguments": json.dumps(call[1])}
            elif canaries and (step == (3 if agent == "/root" else 1) or
                    bootstrap_mode and agent == "/root" and agent not in self.direct_agents):
                call_id = "direct-" + operation
                self.direct_calls.append(call_id)
                self.direct_agents.add(agent)
                item = {"id": "tool-" + operation, "type": "function_call", "call_id": call_id,
                    "namespace": "functions", "name": "exec_command",
                    "arguments": json.dumps({"cmd": canaries.command(), "login": False,
                                              "max_output_tokens": 1000})}
            else:
                require(step == (3 if agent == "/root" else 1) + int(canary_mode) or
                        bootstrap_mode and agent == "/root" and step >= 3, "UNEXPECTED_RETRY")
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
    if gateway_mode:
        limits = dict.fromkeys(DIMENSIONS, 100_000_000)
    gate.budgets.create_account("project", limits, "*")
    gate.budgets.create_account("a1", limits, "synthetic-campaign", "a1", "project",
        category="development")
    provider = Provider(db.path, cas.root, "identity", wire=True, max_requests=12,
                        oauth_fixture=oauth_mode, gateway_fixture=gateway_mode)
    gateway = None
    if gateway_mode:
        from mcbench.accounting import EstimateBasis, FiniteExposure
        from mcbench.native_gateway import GatewayConfig, NativeGateway
        gateway = NativeGateway(db.path, cas.root, simulation=True,
            fixture_upstream=f"http://127.0.0.1:{provider.upstream.server_port}")
        basis = EstimateBasis.model_validate(json.loads((Path(__file__).resolve().parents[1] /
            "configs/operator/live-validation.json").read_bytes())["accounting_basis"])
        price = put(cas, basis.model_dump())
        exposure = FiniteExposure.model_validate({"schema": "strata/FiniteInferenceExposure/1",
            "basis_digest": basis.fingerprint(), "max_input_tokens": basis.context_window_tokens,
            "max_output_tokens": basis.max_output_tokens, "max_requests": 1,
            "input_bound_method": "provider_context_limit", "output_bound_method": "provider_model_limit",
            "enforcement_ref": "cas:sha256:" + "a" * 64})
        gateway_config = GatewayConfig.model_validate({"schema": "strata/NativeGatewayConfig/1",
            "job_id": "root", "profile_digest": "a" * 64, "pricing_ref": price, "exposure": exposure,
            "transport_qualification_ref": None, "authorization_id": None, "helper_calls_bound": 4,
            "max_requests": 12})
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
        if skills_mode:
            from mcbench.native_skills import INSTRUCTIONS, prepare_skill_corpus, read_skill_corpus
            commands = json.loads((Path(plan.profile_directory) / "installation-commands.json").read_bytes())
            plugin_root = Path(json.loads(commands[-1]["stdout"])["installedPath"])
            gateway_config.skill_corpus_ref = prepare_skill_corpus(cas, plugin_root)
            skill_corpus = read_skill_corpus(cas, gateway_config.skill_corpus_ref)
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
        ingress_checks = []
        if ingress_mode:
            from mcbench.native_ingress import HEADER, POLICY as INGRESS_POLICY, NativeIngress, credential
            ingress_secret = credential()
            config["model_providers.strata_local_fixture.http_headers"] = {HEADER: ingress_secret}
        if oauth_mode:
            config["model_providers.strata_local_fixture.requires_openai_auth"] = True
            config["cli_auth_credentials_store"] = "file"
            def encode(value):
                return base64.urlsafe_b64encode(json.dumps(value).encode()).decode().rstrip("=")
            fake_id = encode({"alg": "none"}) + "." + encode({"exp": int(time.time()) + 3600,
                "email": "strata-fixture@example.invalid", "https://api.openai.com/auth": {
                    "chatgpt_account_id": "strata-fixture-account", "chatgpt_plan_type": "plus"}}) + ".fixture"
            (Path(plan.profile_directory) / "auth.json").write_text(json.dumps({
                "auth_mode": "chatgpt", "OPENAI_API_KEY": None,
                "tokens": {"id_token": fake_id, "access_token": "STRATA_SYNTHETIC_OAUTH_ACCESS",
                    "refresh_token": "STRATA_SYNTHETIC_OAUTH_REFRESH", "account_id": "strata-fixture-account"},
                "last_refresh": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")}), encoding="utf-8")
        if gateway_mode:
            config["model_providers.strata_local_fixture.base_url"] = gateway.base_url
            config["model_providers.strata_local_fixture.name"] = "Strata budget gateway"
            config["model_providers.strata_local_fixture.stream_idle_timeout_ms"] = 30000
        if skills_mode:
            config["developer_instructions"] = INSTRUCTIONS
        bootstrap = {}
        if bootstrap_mode:
            from mcbench.native_bootstrap import prepare_bundle
            (output / "broker.json").write_text(json.dumps({"schema": "strata/SealedBrokerConfig/1",
                "database": str(db.path), "objects": str(cas.root), "runtime_id": "root",
                "worker_grant": str(output / "worker.json")}), encoding="utf-8")
            (output / "worker.json").write_text(json.dumps({
                "url": f"http://127.0.0.1:{worker.server_port}/v1/game",
                "token": "STRATA_SYNTHETIC_WORKER_SECRET", "campaign_id": "synthetic-campaign",
                "agent_id": "a1", "epoch": 1}), encoding="utf-8")
            commands = json.loads((Path(plan.profile_directory) / "installation-commands.json").read_bytes())
            plugin_root = Path(json.loads(commands[-1]["stdout"])["installedPath"])
            sealed = prepare_bundle(output / "broker-runtime", native_executable=binary,
                plugin_root=plugin_root, broker_config=output / "broker.json", static_files=[
                    Path(plan.profile_directory) / "config.toml",
                    Path(plan.profile_directory) / "pinned-marketplace/.agents/plugins/marketplace.json"])
            config["mcp_servers.strata_broker"] = sealed["server"]
            bootstrap = {"bootstrap_manifest": sealed["path"], "bootstrap_digest": sealed["sha256"]}
        plan = NativeLaunch.model_validate(plan.model_dump() | {"config_overrides": config,
            "broker_policy": POLICY if admission_mode else None,
            "ingress_policy": INGRESS_POLICY if ingress_mode else None,
            "auth_mode": "chatgpt_oauth" if oauth_mode else plan.auth_mode,
            "session_storage": "private_profile" if inherited_helper else plan.session_storage,
            **bootstrap, "hard_timeout_s": 90 if bootstrap_mode else 45,
            "prompt": "Synthetic MCP identity test. Use only the fixed "
            "synthetic broker and one clean-context native helper."})
        if gateway_mode:
            plan = plan.model_copy(update={"accounting_basis_digest": basis.fingerprint(),
                "gateway_config_digest": gateway_config.profile_fingerprint()})
            gateway_config.profile_digest = plan.profile_digest()
            gateway_config.exposure.enforcement_ref = put(cas, {
                "schema": "strata/InferenceExposureEvidence/1", "is_example": True,
                "profile_digest": plan.profile_digest(), "result": "pass",
                "scope": "fixed fixture output, not provider limit qualification",
                **{k: getattr(exposure, k) for k in ("basis_digest", "input_bound_method",
                    "output_bound_method", "max_input_tokens", "max_output_tokens")}})
            gateway.bind(plan, gateway_config)
        provider.plan = plan
        if ingress_mode:
            NativeIngress(db).register(plan)
        if broker_mode:
            provider.grant_expiry = int((time.time() + 50) * 1000)
            if not bootstrap_mode:
                (output / "broker.json").write_text(json.dumps({"database": str(db.path),
                    "objects": str(cas.root), "runtime_id": "root", "profile_digest": plan.profile_digest(),
                    "worker_grant": str(output / "worker.json")}), encoding="utf-8")
                (output / "worker.json").write_text(json.dumps({
                    "url": f"http://127.0.0.1:{worker.server_port}/v1/game",
                    "token": "STRATA_SYNTHETIC_WORKER_SECRET", "campaign_id": "synthetic-campaign",
                    "agent_id": "a1", "epoch": 1}), encoding="utf-8")
        reserve = ledger(plan, plan.operation_id, parent=None, calls=12, spend=120000,
            pricing=put(cas, {"is_example": True, "real_usd": 0}), inputs=1200000, outputs=120000)
        if gateway_mode:
            reserve = ledger(plan, plan.operation_id, parent=None, calls=12,
                spend=exposure.amount(basis) * 12, pricing=price,
                inputs=exposure.max_input_tokens * 12, outputs=exposure.max_output_tokens * 12)
        runtime.start(plan, reserve)
        if ingress_mode:
            # Owned negative clients have no tools and send no model request. The
            # real CLI supplies the positive root/helper controls independently.
            from http.client import HTTPConnection
            port = gateway.server.server_port if gateway else provider.server.server_port
            for case in ("missing", "wrong", "duplicate", "host", "double_host", "route", "cookie"):
                client = HTTPConnection("127.0.0.1", port, timeout=3)
                path = "/v1/responses?unapproved=1" if case == "route" else "/v1/responses"
                client.putrequest("POST", path, skip_host=True)
                client.putheader("Host", "localhost" if case == "host" else
                                 f"127.0.0.1:{port}")
                if case == "double_host":
                    client.putheader("Host", f"127.0.0.1:{port}")
                if case != "missing":
                    client.putheader(HEADER, credential() if case == "wrong" else ingress_secret)
                if case == "duplicate":
                    client.putheader(HEADER, ingress_secret)
                if case == "cookie":
                    client.putheader("Cookie", "STRATA_SYNTHETIC_INGRESS_CANARY")
                client.putheader("Content-Length", "2")
                client.endheaders(b"{}")
                response = client.getresponse()
                ingress_checks.append({"case": case, "status": response.status})
                response.read()
                client.close()
        wait_job(runtime, plan)
    finally:
        if gateway:
            gateway.stop_admission()
        for job in list(runtime.live):
            runtime.interrupt(job, "probe_cleanup")
        if gateway:
            gateway_seal = gateway.close(runtime)
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
        "closure": runtime.close_dispatch_budget(plan.job_id, gateway_seal) if gateway else
            close_budget(runtime, plan, provider), "budget": gate.budgets.status("project")}
    if broker_mode:
        result["schema"] = "strata/NativeBrokerProbe/1"
        result["worker_calls"] = worker_calls
        result["files"] = [dict(r) for r in db.connection.execute(
            "SELECT namespace,path,immutable FROM broker_files ORDER BY namespace,path")]
        outputs = json.dumps(provider.outputs)
        result["checks"] = {
            "executor_worker_once": len(worker_calls) == 1 and worker_calls[0]["request_id"] == "game-root",
            "positive_game_return": "STRATA_SCOPED_GAME_CONTROL" in outputs,
            "helper_result_written": any(
                r["path"] == "results/advice.md" for r in result["files"]),
            "helper_game_denied": "BROKER_GAME_FORBIDDEN" in outputs,
            "root_only_projection_not_returned": "STRATA_ROOT_ONLY_CANARY" not in outputs,
            "immutable_and_parent_write_denied": "BROKER_WRITE_FORBIDDEN" in outputs,
            "spoof_arguments_denied": "BROKER_ARGUMENTS_INVALID" in outputs,
            "worker_credential_not_returned": "STRATA_SYNTHETIC_WORKER_SECRET" not in outputs,
            "provider_clean": not provider.errors and len(provider.requests) == (8 if canary_mode else 6),
        }
        if bootstrap_mode:
            result["checks"]["provider_clean"] = not provider.errors and 6 <= len(provider.requests) <= 12
        if canaries:
            result["canaries"] = canaries.report(provider.direct_calls)
            result["checks"].update(result["canaries"]["checks"])
        if admission_mode:
            result["participants"] = [dict(r) for r in db.connection.execute(
                "SELECT thread,name,parent,depth,envelope,state FROM native_participants ORDER BY depth")]
            result["admissions"] = [dict(r) for r in db.connection.execute(
                "SELECT operation,thread,envelope FROM native_request_admissions ORDER BY rowid")]
            result["checks"].update({
                "every_request_admitted": len(result["admissions"]) == len(provider.requests),
                "distinct_root_helper_envelopes": len(result["participants"]) == 2 and len({
                    p["envelope"] for p in result["participants"]}) == 2,
                "participants_closed": all(p["state"] == "CLOSED" for p in result["participants"]),
                "all_envelopes_closed": db.connection.execute("SELECT count(*) FROM budget_envelopes e "
                    "JOIN operations o ON e.operation=o.id WHERE o.actual IS NULL OR o.uncertain=1").fetchone()[0] == 0,
                "aggregate_no_double_charge": result["budget"]["committed_and_reserved"]["spend_microusd"]
                    == (7 if gateway_mode else 14) * len(provider.requests),
            })
            if inherited_helper:
                for key in ("helper_result_written", "helper_game_denied", "spoof_arguments_denied",
                            "distinct_root_helper_envelopes", "every_request_admitted", "provider_clean"):
                    result["checks"].pop(key)
                result["checks"].update({
                    "no_helper_artifact_written": not any(r["path"] == "results/advice.md" for r in result["files"]),
                    "no_helper_game_call": not any(r["request_id"] == "game-child" for r in worker_calls),
                    "only_root_enrolled": len(result["participants"]) == 1,
                    "inherited_context_explicitly_rejected": provider.errors == ["HELPER_CONTEXT_INHERITED"]
                        and len(provider.requests) == 5,
                    "only_root_requests_admitted": len(result["admissions"]) == 4,
                    "aggregate_no_double_charge": result["budget"]["committed_and_reserved"]["spend_microusd"] == 56,
                    "inherited_helper_not_forwarded": all(i["agent"] == "/root" for i in provider.identities),
                    "no_child_reservation_created": db.connection.execute("SELECT count(*) FROM operations "
                        "WHERE kind='helper'").fetchone()[0] == 0,
                })
    db.export_journal(output / "journal.jsonl")
    if ingress_mode:
        native_raw = b"".join(base64.b64decode(json.loads(r[0])["raw_base64"])
            for r in db.connection.execute("SELECT body FROM native_events WHERE channel IN ('stdout','stderr')"))
        visible = native_raw + json.dumps(provider.outputs).encode() + (output / "journal.jsonl").read_bytes()
        requests = list(output.glob("*-request.json"))
        bindings = db.connection.execute("SELECT count(*) FROM native_ingress_requests").fetchone()[0]
        result["ingress"] = {"negative_clients": ingress_checks, "denials": provider.ingress_denials,
                             "authenticated_bindings": bindings}
        result["checks"].update({
            "ingress_negative_clients_denied": len(ingress_checks) == 7 and
                all(c["status"] == 403 for c in ingress_checks) and
                (gateway_mode or len(provider.ingress_denials) == 7),
            "ingress_all_requests_bound": bindings == len(provider.requests) and
                all(r["ingress_authenticated"] for r in provider.requests),
            "ingress_secret_absent_from_context_and_journal": ingress_secret.encode() not in visible and
                all(ingress_secret.encode() not in p.read_bytes() for p in requests),
            "ingress_no_upstream_oauth_in_fixture": not any(r["authorization_present"] for r in provider.requests),
        })
        if oauth_mode:
            result["checks"].pop("ingress_no_upstream_oauth_in_fixture")
            result["oauth"] = {"synthetic_credentials_only": True,
                "native_header_names": sorted({h for r in provider.requests for h in r.get("header_names", [])}),
                "upstream": provider.upstream_requests}
            result["checks"].update({
                "native_oauth_headers_all_requests": all(r["authorization_present"] and
                    "chatgpt-account-id" in r.get("header_names", []) for r in provider.requests),
                "upstream_credential_all_requests": len(provider.upstream_requests) == len(provider.requests)
                    and all(r["authorization_present"] for r in provider.upstream_requests),
                "native_protocol_headers_preserved": all(r["native_headers_preserved"]
                                                          for r in provider.upstream_requests),
                "oauth_secrets_absent_from_context_and_journal": all(secret not in visible and
                    all(secret not in p.read_bytes() for p in requests) for secret in (
                        b"STRATA_SYNTHETIC_OAUTH_ACCESS", b"STRATA_SYNTHETIC_OAUTH_REFRESH", fake_id.encode())),
            })
            if gateway_mode:
                result["checks"].pop("native_protocol_headers_preserved")
                result["checks"]["native_protocol_headers_received"] = all(
                    {"session-id", "x-codex-turn-metadata", "originator"}.issubset(r["native_headers_received"])
                    for r in provider.upstream_requests)
    if gateway_mode:
        result["gateway"] = {"config_digest": plan.gateway_config_digest,
            "state": db.connection.execute("SELECT state FROM native_gateways").fetchone()[0],
            "requests": [dict(r) for r in db.connection.execute(
                "SELECT operation,state,reason FROM native_gateway_requests ORDER BY ordinal")],
            "seal": gateway_seal, "valuation": "api_equivalent_estimate", "token_evidence": "synthetic_fixture"}
        result["checks"]["gateway_all_requests_settled_and_fenced"] = (
            result["gateway"]["state"] == "CLOSED" and len(result["gateway"]["requests"]) == result["requests"]
            and all(r["state"] == "SETTLED" for r in result["gateway"]["requests"]))
    if skills_mode:
        rows = [dict(r) for r in db.connection.execute("SELECT namespace,path,ref,immutable FROM broker_files "
            "WHERE path LIKE 'initial/dovetail/%' ORDER BY namespace,path")]
        result["skills"] = {"corpus_ref": gateway_config.skill_corpus_ref, "projected": rows,
                            "supporting_files_and_learned_activation": "unavailable"}
        expected = next(x["text"] for x in skill_corpus["bodies"] if
                        x["path"].endswith("/prompt-engineering/SKILL.md"))
        # Decode actual typed native tool outputs, not provider-emitted call inputs.
        import hashlib
        def contains_skill(value, depth=0):
            if depth > 12:
                return False
            if isinstance(value, dict):
                return any(contains_skill(v, depth+1) for v in value.values())
            if isinstance(value, list):
                return any(contains_skill(v, depth+1) for v in value)
            if isinstance(value, str):
                if value == expected:
                    return True
                for line in [value, *value.splitlines()]:
                    try:
                        decoded = json.loads(line)
                    except (ValueError, TypeError):
                        continue
                    if decoded != value and contains_skill(decoded, depth+1):
                        return True
            return False
        matched = set()
        for path in output.glob("gateway-*-request.json"):
            body = json.loads(path.read_bytes())
            outputs = [x for x in body.get("input", []) if x.get("type") in {
                "custom_tool_call_output", "function_call_output"}]
            if contains_skill(outputs):
                matched.add(json.loads(body["client_metadata"]["x-codex-turn-metadata"])["agent_name"])
        result["skills"]["skill_read_agents"] = sorted(matched)
        expected_hashes = {x["path"]: x["sha256"] for x in skill_corpus["bodies"]}
        result["checks"].update({
            "eight_immutable_skill_bodies_per_participant": len(rows) == 16 and
                all(r["immutable"] == 1 and hashlib.sha256(cas.read(
                    Principal(r["namespace"], "executor"),
                    r["namespace"], r["ref"])).hexdigest() == expected_hashes[r["path"]] for r in rows),
            "root_and_helper_exact_skill_read": matched == {"/root", "/root/identity_child"},
        })
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
    parser.add_argument("--admission", action="store_true")
    parser.add_argument("--inherited-helper", action="store_true")
    parser.add_argument("--bootstrap", action="store_true")
    parser.add_argument("--ingress", action="store_true")
    parser.add_argument("--oauth", action="store_true")
    parser.add_argument("--gateway", action="store_true")
    parser.add_argument("--skills", action="store_true")
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
        root / "src/mcbench/native_broker_policy.py", root / "tools/native_broker_canaries.py",
        root / "src/mcbench/native_admission.py", root / "src/mcbench/inference_dispatch.py",
        root / "src/mcbench/native_bootstrap.py", root / "src/mcbench/launch_integrity.py",
        root / "src/mcbench/sealed_broker.py", root / "src/mcbench/processes.py",
        root / "src/mcbench/native_ingress.py", root / "src/mcbench/native_oauth.py",
        root / "src/mcbench/inference_transport.py", root / "src/mcbench/native_gateway.py",
        root / "src/mcbench/native_skills.py", root / "src/mcbench/native_conformance.py",
        root / "tools/native_oauth_conformance.py"]
    (output / "manifest.json").write_text(json.dumps({"binary_sha256": BINARY_SHA256,
        "source_sha256": {p.relative_to(root).as_posix(): file_hash(p) for p in paths},
        "production_qualified": False}, indent=2), encoding="utf-8")
    result = run(args.codex.resolve(), output, args.broker, args.canaries, args.admission,
                 args.inherited_helper, args.bootstrap, args.ingress, args.oauth, args.gateway, args.skills)
    print(json.dumps(result, indent=2))
    if args.broker:
        require(all(result["checks"].values()), "BROKER_FIXTURE_FAILED")


if __name__ == "__main__":
    main()
