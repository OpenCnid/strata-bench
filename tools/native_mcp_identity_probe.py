"""Credential-free native identity/broker/admission fixtures, not qualification.

The default stdio server only echoes fixture metadata. Optional broker mode
uses scoped artifacts and an owned synthetic worker; admission mode exercises
durable participant/request budgets. The explicit game_probe mode binds an
operator-supplied real worker. Providers remain synthetic in every mode.
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


def close_fixture_budget(runtime, plan, provider, gateway_seal=None):
    """Retain a report on uncertainty; never fabricate a receipt or release a hold."""
    from mcbench.storage import Fault
    from native_dispatch_probe import close_budget
    try:
        return runtime.close_dispatch_budget(plan.job_id, gateway_seal) if gateway_seal else (
            close_budget(runtime, plan, provider))
    except Fault as exc:
        return {"state": runtime.status(plan.job_id)["state"], "closure_error": exc.code}


def run(binary, output, broker_mode=False, canary_mode=False, admission_mode=False,
        inherited_helper=False, bootstrap_mode=False, ingress_mode=False, oauth_mode=False,
        gateway_mode=False, skills_mode=False, *, writer_target=None, tool_projections=None,
        deferred_tools=False, no_patch_catalog=None, state_mode=False, retirement_mode=False, interrupt_mode=False,
        activation_source=None, job_id="root", activation_parent_calls=9, game_probe=None, game_retention=None,
        game_recovery=None, piloting_contract=False, model="gpt-5.6-luna", game_failure=False, pilot_timeout_s=90,
        pilot_helper=False):
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
    from native_dispatch_probe import LocalProvider, ledger, plan_for, put, sse, wait_job
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
    require(not pilot_helper or piloting_contract and pilot_timeout_s == 240 and model == "gpt-6-luna",
            "PILOT_CONTRACT_PROFILE_REQUIRED")
    require(pilot_timeout_s == 90 or piloting_contract and (pilot_timeout_s == 180 or pilot_helper and pilot_timeout_s == 240),
            "PILOT_CONTRACT_PROFILE_REQUIRED")
    require(not piloting_contract or skills_mode and bootstrap_mode and tool_projections is not None and
            no_patch_catalog is not None and not any((canary_mode, state_mode, retirement_mode, interrupt_mode,
                                                     activation_source, inherited_helper, game_probe)),
            "PILOT_CONTRACT_PROFILE_REQUIRED")
    require(activation_source is None or bootstrap_mode and ingress_mode and tool_projections is not None and
            no_patch_catalog is not None and not any((canary_mode, state_mode, retirement_mode, interrupt_mode,
                                                     gateway_mode, skills_mode, inherited_helper)),
            "ACTIVATION_PINNED_BOOTSTRAP_REQUIRED")
    require(writer_target is None or canary_mode and bootstrap_mode, "WRITER_CANARY_BOOTSTRAP_REQUIRED")
    require(tool_projections is None or bootstrap_mode, "PROJECTION_BOOTSTRAP_REQUIRED")
    require(not deferred_tools or canary_mode and bootstrap_mode and tool_projections is not None,
            "DEFERRED_CANARY_PROJECTION_REQUIRED")
    require(not state_mode or bootstrap_mode and tool_projections is not None and
            no_patch_catalog is not None and not canary_mode, "STATE_PINNED_BOOTSTRAP_REQUIRED")
    require(not retirement_mode or bootstrap_mode and tool_projections is not None and
            no_patch_catalog is not None and not any((canary_mode, state_mode, inherited_helper, gateway_mode)),
            "RETIREMENT_PINNED_BOOTSTRAP_REQUIRED")
    require(not interrupt_mode or bootstrap_mode and ingress_mode and tool_projections is not None and
            no_patch_catalog is not None and not any((canary_mode, state_mode, inherited_helper,
                                                      gateway_mode, retirement_mode)),
            "INTERRUPT_PINNED_BOOTSTRAP_REQUIRED")
    require(game_probe is None or bootstrap_mode and ingress_mode and tool_projections is not None and
            no_patch_catalog is not None and not any((canary_mode, state_mode, retirement_mode, interrupt_mode,
                                                     gateway_mode, activation_source, inherited_helper)),
            "GAME_PINNED_BOOTSTRAP_REQUIRED")
    if game_failure:
        from native_game_failure_probe import GameTransportFailureProbe
        require(isinstance(game_probe, GameTransportFailureProbe) and oauth_mode and
                game_retention is None and game_recovery is None and model == "gpt-6-luna",
                "GAME_FAILURE_PROFILE_REQUIRED")
    require(game_retention is None or game_probe is not None, "RETENTION_GAME_REQUIRED")
    require(game_recovery is None or game_probe is not None and game_retention is not None,
            "RECOVERY_GAME_REQUIRED")
    require(no_patch_catalog is None or deferred_tools or state_mode or retirement_mode or interrupt_mode or activation_source or game_probe or piloting_contract,
            "CATALOG_DEFERRED_CANARY_REQUIRED")
    from native_state_canaries import StateCanaries
    from native_retirement_probe import RetirementProbe
    from native_interrupt_probe import InterruptProbe
    state_probe = StateCanaries() if state_mode else None
    retirement_probe = RetirementProbe() if retirement_mode else None
    interrupt_probe = InterruptProbe() if interrupt_mode else None
    from native_activation_probe import ActivationProbe
    activation = ActivationProbe(activation_source, output) if activation_source else None
    require(type(activation_parent_calls) is int and 4 <= activation_parent_calls <= 9 and
            (activation is not None or activation_parent_calls == 9), "ACTIVATION_FIXTURE_BOUND")
    patch_test = no_patch_catalog is not None and activation is None and game_probe is None and not piloting_contract
    # A resumed fixture shares the original 120000-unit cap and its consumed
    # costs. Leave room for those costs instead of reinstalling the allowance.
    request_limit = 4 if game_failure else 9 if activation else 20 if retirement_mode or interrupt_mode else 10 if game_recovery else 12
    canaries = Canaries(output, writer_target=writer_target,
        deferred_tools=deferred_tools, patch_disabled=no_patch_catalog is not None) if canary_mode else None

    class Provider(LocalProvider):
        def __init__(self, *args, **kwargs):
            self.steps, self.identities, self.outputs = {}, [], []
            self.helper_deliveries = []
            self.helper_started = threading.Event()
            self.helper_release = threading.Event()
            self.helper_overlap = False
            self.outputs_by_agent = {}
            self.direct_calls = []
            self.direct_agents = set()
            self.patch_direct_calls, self.patch_agents = [], set()
            self.patch_function_calls = []
            super().__init__(*args, **kwargs)

        def respond(self, handler, body, index, operation):
            metadata = json.loads(body["client_metadata"]["x-codex-turn-metadata"])
            agent = metadata["agent_name"]
            if pilot_helper and agent == "/root/pilot_review":
                self.helper_started.set()
                require(self.helper_release.wait(20), "PILOT_HELPER_OVERLAP_TIMEOUT")
            elif pilot_helper and agent == "/root" and self.steps.get(agent, 0) == 3:
                try:
                    self.helper_overlap = self.helper_started.wait(20)
                    require(self.helper_overlap, "PILOT_HELPER_OVERLAP_TIMEOUT")
                finally:
                    self.helper_release.set()
            require(agent in ({"/root", "/root/pilot_review"} if pilot_helper else
                {"/root", "/root/identity_child", "/root/replacement"} if retirement_mode else
                {"/root", "/root/identity_child"}), "UNEXPECTED_AGENT")
            if pilot_helper and agent == "/root":
                self.helper_deliveries.extend(i for i in body.get("input", []) if i.get("type") == "agent_message"
                    and i.get("author") == "/root/pilot_review" and i.get("recipient") == "/root")
            self.identities.append({"agent": agent, "thread_id": metadata["thread_id"]})
            if state_probe:
                state_probe.observe(agent, body)
            if interrupt_probe:
                interrupt_probe.observe(agent, body)
            self.outputs.extend(i for i in body.get("input", []) if i.get("type") in {
                "custom_tool_call_output", "function_call_output"})
            self.outputs_by_agent.setdefault(agent, []).extend(i for i in body.get("input", []) if i.get("type") in {
                "custom_tool_call_output", "function_call_output"})
            step = self.steps.get(agent, 0)
            if game_failure and step > 0:
                require(agent == "/root" and step == 1, "GAME_FAILURE_PROFILE_REQUIRED")
                game_probe.truncate(handler, operation, model, self.outputs)
            extra_items = []
            self.steps[agent] = step + 1
            root_id = next(i["thread_id"] for i in self.identities if i["agent"] == "/root")
            item = {"id": "message-" + operation, "type": "message", "role": "assistant",
                "status": "completed", "content": [{"type": "output_text",
                "text": "Synthetic identity probe finished.", "annotations": []}]}
            if piloting_contract:
                from native_pilot_contract_probe import response
                item = response(agent, step, operation, helper=pilot_helper,
                                child_done=self.steps.get("/root/pilot_review", 0) == 1)
            elif step == 0:
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
                        broker = NativeBroker(connection, objects, self.plan.job_id, self.plan.profile_digest())
                        admission = put(objects, {"is_example": True, "operation_id": operation,
                            "scope": "already admitted synthetic provider request only"})
                        grant = BrokerGrant.model_validate({"schema": "strata/NativeBrokerGrant/1",
                            "runtime_id": self.plan.job_id, "session_id": root_id,
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
                        if activation is None or agent != "/root":
                            broker.project(grant.thread_id, "supplied/plan.md", "STRATA_SCOPED_PLAN")
                        if agent == "/root" and activation is None:
                            from mcbench.native_game_retention import INITIAL
                            for path, text in INITIAL.items():
                                if path != "supplied/plan.md":
                                    broker.project(grant.thread_id, path, text)
                    finally:
                        connection.close()
                    game_request = {"schema": "strata/GameRequest/1",
                        "request_id": "game-root" if agent == "/root" else "game-child",
                        "campaign_id": self.plan.campaign_id, "agent_id": self.plan.agent_id, "epoch": self.plan.epoch,
                        "deadline_at": datetime.fromtimestamp(time.time()+5, timezone.utc).isoformat(
                            timespec="milliseconds").replace("+00:00", "Z"),
                        "method": "observe", "action": None, "target_request_id": None, "after": None}
                    calls = [("artifact_read", {"path": "supplied/plan.md"}),
                        ("artifact_write", {"path": "notes/root.md" if agent == "/root" else
                            "results/advice.md", "text": "STRATA_OWN_ARTIFACT", "expected_ref": None}),
                        ("game", {"request": game_request})]
                    if activation:
                        if agent == "/root":
                            calls[0] = ("artifact_read", {"path": "notes/seed.md" if activation.reset else "notes/root.md"})
                            calls[1][1]["expected_ref"] = activation.body["workspace"].get("notes/root.md")
                            if activation.reset:
                                calls[1][1]["text"] = "STRATA_AFTER_FROZEN_BOUNDARY"
                        if activation.reset:
                            calls = activation.calls(agent) + calls
                        else:
                            calls.extend(activation.calls(agent))
                    if game_recovery:
                        if agent == "/root":
                            calls[0] = ("artifact_read", {"path": "notes/root.md"})
                            calls[1][1].update(expected_ref=game_recovery.old_note, text="STRATA_RESTORED_AND_CONTINUED")
                        else:
                            calls.append(("artifact_read", {"path": "notes/root.md"}))
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
                    elif activation is None:
                        calls.append(("artifact_write", {"path": "initial/skill.md",
                            "text": "spoof", "expected_ref": None}))
                    code = 'const calls=' + json.dumps(calls) + '; for (const [name,args] of calls) {' + (
                        ' const t=ALL_TOOLS.find(t=>t.name.endsWith("__"+name)); '
                        ' if (!t) throw new Error("MCP_TOOL_MISSING:"+name); '
                        ' text({name,result:await tools[t.name](args)}); }')
                    if canaries:
                        code += "\n" + canaries.code(agent=agent)
                    if activation and agent == "/root":
                        code += "\n" + activation.publish_code()
                    if game_probe and agent == "/root":
                        code += "\n" + game_probe.code()
                item = {"id": "tool-" + operation, "type": "custom_tool_call",
                    "call_id": "call-" + operation, "namespace": "functions", "name": "exec",
                    "input": code}
                if state_probe:
                    item = state_probe.start(agent, operation, code)
                    if agent == "/root":
                        extra_items.append(state_probe.reserve_root_handle(operation))
            elif state_probe:
                item, *extra_items = state_probe.next(agent, step, operation)
            elif retirement_probe:
                item = retirement_probe.next(self, agent, step, operation)
            elif interrupt_probe:
                item = interrupt_probe.next(self, agent, step, operation)
            elif agent == "/root" and (step in {1, 2} or bootstrap_mode and
                    not inherited_helper and self.steps.get("/root/identity_child", 0) <
                    2 + int(canary_mode) + int(patch_test)):
                call = ("spawn_agent", {"task_name": "identity_child", "fork_turns": "all" if inherited_helper else "none",
                    "message": "Exercise only the synthetic inspect_identity tool. "
                               "Do not read files or call any other tool."}) if step == 1 else (
                    "wait_agent", {"timeout_ms": 30000 if activation else 10000})
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
            elif patch_test and agent not in self.patch_agents:
                call_id = "direct-patch-" + operation
                self.patch_direct_calls.append(call_id)
                self.patch_agents.add(agent)
                item = {"id": "tool-" + operation, "type": "custom_tool_call", "call_id": call_id,
                    "namespace": "functions", "name": "apply_patch", "input":
                    "*** Begin Patch\n*** Update File: " + canaries.protected.as_posix() +
                    "\n@@\n-absent context\n+changed\n*** End Patch"}
                function_id = "function-patch-" + operation
                self.patch_function_calls.append(function_id)
                extra_items.append({"id": "function-tool-" + operation, "type": "function_call",
                    "call_id": function_id, "namespace": "functions", "name": "apply_patch",
                    "arguments": json.dumps({"input": item["input"]})})
            else:
                require(step == (3 if agent == "/root" else 1) + int(canary_mode) +
                        int(patch_test) or
                        bootstrap_mode and agent == "/root" and step >= 3, "UNEXPECTED_RETRY")
            response = {"id": "response-" + operation, "object": "response", "created_at": 1,
                "status": "completed", "model": body["model"], "output": [item, *extra_items], "usage": {
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
            for index, extra in enumerate(extra_items, 1):
                handler.wfile.write(sse("response.output_item.done", output_index=index, item=extra))
            handler.wfile.write(sse("response.completed", response=response))
            handler.wfile.flush()
            return {}, response["id"]

    db = Database(output / "synthetic.sqlite")
    cas = CAS(db, output / "objects")
    runtime = NativeExec(db, cas, simulation=True)
    native_worker = None
    if game_probe:
        from mcbench.native_worker import NativeWorker
        native_worker = NativeWorker(db, game_probe.descriptor)
        runtime.revoke_game = native_worker.revoke
    gate = InferenceDispatches(db, cas, simulation=True)
    limits = dict.fromkeys(DIMENSIONS, 2000000) | {"spend_microusd": request_limit * 10000}
    if gateway_mode:
        limits = dict.fromkeys(DIMENSIONS, 100_000_000)
    if activation is None and game_recovery is None:
        gate.budgets.create_account("project", limits, "*")
        gate.budgets.create_account("a1", limits,
            game_probe.scope["campaign_id"] if game_probe else "synthetic-campaign",
            game_probe.scope["agent_id"] if game_probe else "a1", "project",
            category="development")
    require(model in {"gpt-5.6-luna", "gpt-6-luna"}, "MODEL_POLICY")
    provider = Provider(db.path, cas.root, "identity", wire=True, max_requests=request_limit, model=model,
                        oauth_fixture=oauth_mode, gateway_fixture=gateway_mode,
                        helper_requests=8 if interrupt_mode else 5 if state_mode else 4,
                        fixture_input_reserve=10000 if activation else 100000)
    gateway = None
    if gateway_mode:
        from mcbench.accounting import EstimateBasis, FiniteExposure
        from mcbench.native_gateway import GatewayConfig, NativeGateway
        gateway = NativeGateway(db.path, cas.root, simulation=True,
            fixture_upstream=f"http://127.0.0.1:{provider.upstream.server_port}")
        basis_path = "configs/operator/live-validation.json" if model == "gpt-6-luna" else "configs/operator/legacy/live-validation-d11.json"
        basis = EstimateBasis.model_validate(json.loads((Path(__file__).resolve().parents[1] /
            basis_path).read_bytes())["accounting_basis"])
        require(basis.model == model, "PRICE_MODEL_MISMATCH")
        price = put(cas, basis.model_dump())
        exposure = FiniteExposure.model_validate({"schema": "strata/FiniteInferenceExposure/1",
            "basis_digest": basis.fingerprint(), "max_input_tokens": basis.context_window_tokens,
            "max_output_tokens": basis.max_output_tokens, "max_requests": 1,
            "input_bound_method": "provider_context_limit", "output_bound_method": "provider_model_limit",
            "enforcement_ref": "cas:sha256:" + "a" * 64})
        gateway_config = GatewayConfig.model_validate({"schema": "strata/NativeGatewayConfig/1",
            "job_id": "root", "profile_digest": "a" * 64, "pricing_ref": price, "exposure": exposure,
            "transport_qualification_ref": None, "authorization_id": None, "helper_calls_bound": 1 if pilot_helper else 4,
            "max_requests": 16 if pilot_helper else 12, "max_handlers": 2 if pilot_helper else 4,
            "request_timeout_s": 60 if piloting_contract else 30})
    worker_calls = []
    worker = None
    if broker_mode and game_probe is None:
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
                    "visible_control": "STRATA_SCOPED_GAME_CONTROL",
                    **({"state": {"next_cursor": "synthetic-public-page", "truncated": True}}
                       if piloting_contract and r["method"] == "observe" else {})}}).encode()
                self.send_response(200)
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)
        worker = ThreadingHTTPServer(("127.0.0.1", 0), Worker)
        worker_thread = threading.Thread(target=worker.serve_forever, daemon=True)
        worker_thread.start()
    try:
        plan = plan_for(binary, output, provider, job_id)
        if game_probe:
            plan = plan.model_copy(update=game_probe.scope)
        if game_recovery:
            plan = game_recovery.prepare(runtime, plan)
        if activation:
            plan = activation.prepare(runtime, plan)
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
        if activation:
            config["developer_instructions"] = activation.instructions
        bootstrap = {}
        catalog = None
        if no_patch_catalog is not None:
            from mcbench.native_catalog import install_no_patch_catalog
            from mcbench.inventory import file_hash
            catalog = install_no_patch_catalog(no_patch_catalog, output / "restricted-model-catalog.json",
                expected_sha256=file_hash(no_patch_catalog), model=plan.model)
            (output / "catalog-restriction.json").write_text(json.dumps(catalog, indent=2), encoding="utf-8")
            config.update(catalog["config_overrides"])
            bootstrap["tool_catalog_policy"] = catalog["policy"]
        if bootstrap_mode:
            from mcbench.native_bootstrap import prepare_bundle
            (output / "broker.json").write_text(json.dumps({"schema": "strata/SealedBrokerConfig/1",
                "database": str(db.path), "objects": str(cas.root), "runtime_id": plan.job_id,
                "worker_grant": str(output / "worker.json")}), encoding="utf-8")
            (output / "worker.json").write_text(json.dumps(game_probe.descriptor if game_probe else {
                "url": f"http://127.0.0.1:{worker.server_port}/v1/game",
                "token": "STRATA_SYNTHETIC_WORKER_SECRET", "campaign_id": plan.campaign_id,
                "agent_id": plan.agent_id, "epoch": plan.epoch}), encoding="utf-8")
            commands = json.loads((Path(plan.profile_directory) / "installation-commands.json").read_bytes())
            plugin_root = Path(json.loads(commands[-1]["stdout"])["installedPath"])
            sealed = prepare_bundle(output / "broker-runtime", native_executable=binary,
                plugin_root=plugin_root, broker_config=output / "broker.json", static_files=[
                    Path(plan.profile_directory) / "config.toml",
                    Path(plan.profile_directory) / "pinned-marketplace/.agents/plugins/marketplace.json",
                    *([] if catalog is None else catalog["static_files"])],
                static_trees=[Path(plan.workspace)] if activation else [])
            config["mcp_servers.strata_broker"] = sealed["server"]
            bootstrap.update({"bootstrap_manifest": sealed["path"], "bootstrap_digest": sealed["sha256"]})
        plan = NativeLaunch.model_validate(plan.model_dump() | {"config_overrides": config,
            "helper_limit": 1 if pilot_helper else 0 if piloting_contract or game_failure else 1 if retirement_mode or interrupt_mode else plan.helper_limit,
            "purpose": "development_piloting" if piloting_contract else plan.purpose,
            "broker_policy": POLICY if admission_mode else None,
            "ingress_policy": INGRESS_POLICY if ingress_mode else None,
            "auth_mode": "chatgpt_oauth" if oauth_mode else plan.auth_mode,
            "session_storage": "private_profile" if inherited_helper else plan.session_storage,
            **bootstrap, "hard_timeout_s": pilot_timeout_s if piloting_contract else 90 if bootstrap_mode else 45,
            "prompt": ("Read one scoped game observation. Model replies are scripted; no actions or helpers." if game_failure else "Read the public game contract and exercise the scripted request-format check. No helpers."
                       if piloting_contract and not pilot_helper else "Read the public game contract and exercise one clean-context helper. Synthetic provider and worker only."
                       if pilot_helper else "Exercise one bounded look action through your scoped game tool and one clean-context helper. "
                       "The game is real; model responses are scripted for integration verification."
                       if game_probe else ("$learned-crafting " if activation and not activation.reset else "") +
                       "Synthetic MCP identity test. Use only the fixed synthetic broker and one clean-context native helper.")})
        if tool_projections is not None:
            from mcbench.native_tool_projection import pin_tool_projection
            plan = plan.model_copy(update={"tool_projection_ref": pin_tool_projection(
                cas, plan, tool_projections, helper_collaboration=pilot_helper)})
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
        if game_retention:
            if game_recovery:
                game_retention.attach_existing(runtime, plan)
            else:
                game_retention.register(runtime, plan)
        if ingress_mode:
            NativeIngress(db).register(plan)
        if broker_mode:
            provider.grant_expiry = int((time.time() + 50) * 1000)
            if not bootstrap_mode:
                (output / "broker.json").write_text(json.dumps({"database": str(db.path),
                    "objects": str(cas.root), "runtime_id": plan.job_id, "profile_digest": plan.profile_digest(),
                    "worker_grant": str(output / "worker.json")}), encoding="utf-8")
                (output / "worker.json").write_text(json.dumps({
                    "url": f"http://127.0.0.1:{worker.server_port}/v1/game",
                    "token": "STRATA_SYNTHETIC_WORKER_SECRET", "campaign_id": "synthetic-campaign",
                    "agent_id": "a1", "epoch": 1}), encoding="utf-8")
        parent_calls = activation_parent_calls if activation else request_limit
        reserve = ledger(plan, plan.operation_id, parent=None, calls=parent_calls, spend=parent_calls*10000,
            pricing=put(cas, {"is_example": True, "real_usd": 0}),
            inputs=parent_calls*provider.fixture_input_reserve, outputs=parent_calls*10000)
        if activation:
            reserve = reserve.model_copy(update={"campaign_account": db.connection.execute(
                "SELECT category FROM accounts WHERE id=?", (plan.account,)).fetchone()[0]})
        if gateway_mode:
            reserve = ledger(plan, plan.operation_id, parent=None, calls=12,
                spend=exposure.amount(basis) * 12, pricing=price,
                inputs=exposure.max_input_tokens * 12, outputs=exposure.max_output_tokens * 12)
        if native_worker:
            native_worker.bind(plan)
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
        if native_worker and native_worker.job:
            native_worker.revoke(plan.campaign_id, plan.agent_id, plan.epoch)
    calls = [json.loads(line) for path in sorted(output.glob("mcp-*.jsonl"))
             for line in path.read_text(encoding="utf-8").splitlines()]
    result = {"schema": "strata/NativeMcpIdentityProbe/1", "is_example": True,
        "production_qualified": False, "real_usd": 0, "profile_digest": plan.profile_digest(),
        "identities": provider.identities, "broker_calls": calls,
        "provider_errors": provider.errors, "outputs": provider.outputs,
        "runtime": runtime.status(plan.job_id), "requests": len(provider.requests),
        "closure": close_fixture_budget(runtime, plan, provider, gateway_seal if gateway else None),
        "budget": gate.budgets.status("a1" if activation else "project")}
    if broker_mode:
        result["schema"] = "strata/NativeBrokerProbe/1"
        result["worker_calls"] = worker_calls
        result["files"] = [dict(r) for r in db.connection.execute(
            "SELECT f.namespace,f.path,f.immutable FROM broker_files f JOIN broker_grants g "
            "ON f.namespace=json_extract(g.body,'$.namespace') WHERE g.runtime=? "
            "ORDER BY f.namespace,f.path", (plan.job_id,))]
        outputs = json.dumps(provider.outputs)
        result["checks"] = {
            "budget_closure_finalized": result["closure"].get("state") == "FINALIZED" and
                "closure_error" not in result["closure"],
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
        if game_probe:
            result["game_integration"] = game_probe.report(db, plan, provider)
            result["checks"].pop("executor_worker_once")
            result["checks"].pop("positive_game_return")
            result["checks"].update(result["game_integration"]["checks"])
        if canaries:
            result["canaries"] = canaries.report(provider.direct_calls,
                patch_direct_calls=provider.patch_direct_calls, patch_function_calls=provider.patch_function_calls)
            result["checks"].update(result["canaries"]["checks"])
        if admission_mode:
            result["participants"] = [dict(r) for r in db.connection.execute(
                "SELECT thread,name,parent,depth,envelope,state FROM native_participants WHERE job=? ORDER BY depth", (plan.job_id,))]
            result["admissions"] = [dict(r) for r in db.connection.execute(
                "SELECT operation,thread,envelope FROM native_request_admissions WHERE job=? ORDER BY rowid", (plan.job_id,))]
            result["checks"].update({
                "every_request_admitted": len(result["admissions"]) == len(provider.requests),
                "distinct_root_helper_envelopes": len(result["participants"]) == 2 and len({
                    p["envelope"] for p in result["participants"]}) == 2,
                "participants_closed": all(p["state"] == "CLOSED" for p in result["participants"]),
                "all_envelopes_closed": db.connection.execute("SELECT count(*) FROM budget_envelopes e "
                    "JOIN operations o ON e.operation=o.id WHERE o.actual IS NULL OR o.uncertain=1").fetchone()[0] == 0,
                "aggregate_no_double_charge": result["budget"]["committed_and_reserved"]["spend_microusd"]
                    # Fixture: 10 input, 2 cached, 4 output; unclassified writes
                    # use the conservative write rate, rounded per request.
                    == ({"gpt-5.6-luna": 7, "gpt-6-luna": 4}[model] if gateway_mode else 14)
                    * len(provider.requests),
            })
            if plan.tool_projection_ref is not None:
                from mcbench.native_tool_projection import read_tool_projection
                from mcbench.storage import digest
                expected = {role: digest(blocks) for role, blocks in
                            read_tool_projection(cas, plan).items()}
                events = [json.loads(row[0]) for row in db.connection.execute(
                    "SELECT body FROM outbox WHERE kind='native.request_admitted' AND json_extract(body,'$.job')=?", (plan.job_id,))]
                result["tool_projection"] = {"ref": plan.tool_projection_ref,
                    "expected": expected, "admissions": events}
                result["checks"].update({
                    "every_request_projection_checked": len(events) == len(provider.requests) and
                        all(e.get("tool_projection_ref") == plan.tool_projection_ref and
                            e.get("tool_projection_digest") == expected[
                                "executor" if e["depth"] == 0 else "helper"] for e in events),
                    "both_projection_roles_checked": {e["depth"] for e in events} == {0, 1},
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
            if retirement_probe:
                result["retirement"] = retirement_probe.report(provider, db)
                result["checks"].update(result["retirement"]["checks"])
                result["checks"].update({
                    "provider_clean": provider.errors == ["NATIVE_ADMISSION_SCOPE"],
                    "every_request_admitted": len(result["admissions"]) == 15 and len(provider.requests) == 16,
                    "distinct_root_helper_envelopes": len(result["participants"]) == 3 and len({
                        p["envelope"] for p in result["participants"]}) == 3,
                    "aggregate_no_double_charge": result["budget"]["committed_and_reserved"]["spend_microusd"] == 210,
                    "every_request_projection_checked": len(events) == 15 and all(
                        e.get("tool_projection_digest") == expected["executor" if e["depth"] == 0 else "helper"]
                        and e.get("tool_projection_ref") == plan.tool_projection_ref for e in events),
                })
    if activation:
        result["activation"] = activation.report(provider, db, plan)
        result["checks"].update(result["activation"]["checks"])
        result["checks"]["aggregate_no_double_charge"] = result["activation"]["checks"]["prior_usage_preserved_once"]
    if game_retention:
        result["retention"] = game_retention.finish()
        result["checks"]["preregistered_native_retention_component"] = True
    if game_recovery:
        result["recovery"] = game_recovery.report(runtime, plan, provider)
        result["checks"].update(result["recovery"]["checks"])
        result["checks"]["aggregate_no_double_charge"] = result["recovery"]["checks"]["recovery_prior_costs_preserved"]
    db.export_journal(output / "journal.jsonl")
    if ingress_mode:
        native_raw = b"".join(base64.b64decode(json.loads(r[0])["raw_base64"])
            for r in db.connection.execute("SELECT body FROM native_events WHERE channel IN ('stdout','stderr')"))
        visible = native_raw + json.dumps(provider.outputs).encode() + (output / "journal.jsonl").read_bytes()
        requests = list(output.glob("*-request.json"))
        bindings = db.connection.execute("SELECT count(*) FROM native_ingress_requests WHERE job=?",
                                        (plan.job_id,)).fetchone()[0]
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
    if state_probe:
        result["state_canaries"] = state_probe.report()
        result["checks"].update(result["state_canaries"]["checks"])
    if interrupt_probe:
        result["interruption"] = interrupt_probe.report(provider, db)
        result["checks"].update(result["interruption"]["checks"])
        result["checks"]["provider_clean"] = not provider.errors and len(provider.requests) <= request_limit
    if piloting_contract:
        from native_pilot_contract_probe import report
        result["checks"] = report(db, cas, plan, result, provider, worker_calls, helper=pilot_helper)
        result["scope"] = "development_piloting_helper_contract" if pilot_helper else "development_piloting_public_contract"
        result["isolation_qualified"] = False
    if game_failure:
        result["failure_control"] = game_probe.failure_report(db, cas, plan, provider, result)
        result["scope"] = "scripted_transport_failure_with_authentic_game"
        result["isolation_qualified"] = False
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
        root / "src/mcbench/native_admission.py", root / "src/mcbench/native_tool_projection.py",
        root / "src/mcbench/budgets.py", root / "src/mcbench/authorization.py", root / "src/mcbench/metering_trial.py",
        root / "src/mcbench/inference_dispatch.py",
        root / "src/mcbench/native_bootstrap.py", root / "src/mcbench/launch_integrity.py",
        root / "src/mcbench/sealed_broker.py", root / "src/mcbench/processes.py",
        root / "src/mcbench/native_ingress.py", root / "src/mcbench/native_oauth.py",
        root / "src/mcbench/inference_transport.py", root / "src/mcbench/native_gateway.py",
        root / "src/mcbench/native_skills.py", root / "src/mcbench/native_conformance.py",
        root / "tools/native_oauth_conformance.py", root / "src/mcbench/native_piloting.py",
        root / "src/mcbench/pilot_budget.py",
        root / "tools/native_pilot_trial.py", root / "tools/native_pilot_report.py",
        root / "tools/native_pilot_contract_probe.py",
        root / "tools/m0_native_game.py"]
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
