"""Pinned CLI / credential-free synthetic provider accounting integration.

Run explicitly with --codex <pinned executable> --output <new private directory>.
There is no remote provider, pricing assertion, OAuth login or live mode here.
The deterministic provider executes behind the real durable dispatch boundary.
Raw native journals stay outside the source tree. The provider never sends a
command-execution tool call; its fixed JavaScript text call exercises the CLI loop.
"""

import argparse
import base64
import hashlib
import json
import os
import subprocess
import sys
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from mcbench.budgets import DIMENSIONS
from mcbench.inference_dispatch import InferenceAttempt, InferenceDispatches
from mcbench.inference_transport import ResponsesUsage, SyntheticResponsesTransport
from mcbench.inventory import file_hash
from mcbench.native import NativeExec, NativeLaunch
from mcbench.processes import ManagedProcess
from mcbench.records import BudgetLedger
from mcbench.runtime import CODEX_VERSION, DOVETAIL_COMMIT
from mcbench.storage import CAS, Database, Fault, Principal, canonical, digest, require

BINARY_SHA256 = "960c111d47afd61669954b9df9e56083e302edbfa3ef6962d81dcc14a30051dc"
OPERATOR = Principal("operator", "operator")
MODEL = "gpt-5.6-luna"
MAX_REQUEST = 1024 * 1024
MAX_REQUESTS = 8


def put(cas, value):
    return cas.put(OPERATOR, "operator", "operator", canonical(value))


def ledger(plan, operation, *, parent, calls, spend, pricing, inputs=100000, outputs=10000):
    return BudgetLedger.model_validate({"schema": "mcbench/BudgetLedger/1",
        "is_example": False, "campaign_id": plan.campaign_id, "epoch": plan.epoch,
        "seq": 1, "recorded_at": "2026-09-20T00:00:00Z", "ledger_id": operation + ":reserve",
        "campaign_account": "development", "agent_id": plan.agent_id,
        "operation_id": operation, "parent_operation_id": parent,
        "source_event_id": operation + ":reserve", "posting": "reserve",
        "kind": "helper" if plan.role == "helper" else "model",
        "usage": {"input_tokens": inputs, "cached_input_tokens": 0,
            "output_tokens": outputs, "reasoning_tokens": 0, "model_calls": calls,
            "primitive_events": 0, "avatar_ticks": 0, "wall_ms": 0, "spend_microusd": spend},
        "metering": "estimated", "pricing_ref": pricing, "model_identity": MODEL,
        "raw_usage_ref": None, "reason": "synthetic finite provider fixture; no USD expenditure"})


def sse(kind, **fields):
    return ("event: " + kind + "\ndata: " + json.dumps({"type": kind, **fields}) + "\n\n").encode()


class LocalProvider:
    """One fixture ingress per native runtime; only its own loopback upstream.

    Each HTTP request receives a new operation ID, regardless of body equality.
    The provider callback starts only after durable admission. All responses and
    receipts are synthetic. Errors are metered by the local provider itself;
    HTTP status alone is deliberately insufficient to infer zero-cost usage.
    """

    def __init__(self, database_path, objects, scenario, *, wire=False, max_requests=MAX_REQUESTS):
        require(type(max_requests) is int and 1 <= max_requests <= 32, "REQUEST_LIMIT")
        self.max_requests = max_requests
        self.database_path, self.objects, self.scenario = database_path, objects, scenario
        self.plan = None
        self.requests, self.errors = [], []
        self.lock = threading.Lock()
        self.release = threading.Event()
        self.entered = threading.Event()
        self.streaming = threading.Event()
        self.receipts = []
        self.wire = wire
        self.upstream_requests = []
        provider = self

        class UpstreamHandler(BaseHTTPRequestHandler):
            def log_message(self, *_):
                pass

            def do_POST(self):
                self.connection.settimeout(3)
                self.response_started = False
                observer = None
                try:
                    size = int(self.headers.get("Content-Length", "0"))
                    require(0 < size <= MAX_REQUEST and self.headers.get("Authorization") is None,
                            "UPSTREAM_REQUEST_REJECTED")
                    raw = self.rfile.read(size)
                    request_digest = hashlib.sha256(raw).hexdigest()
                    observer = Database(provider.database_path)
                    active = list(observer.connection.execute(
                        "SELECT operation,state FROM inference_attempts WHERE state='DISPATCHING' "
                        "AND json_extract(request,'$.runtime_job_id')=? AND "
                        "json_extract(request,'$.request_digest')=?",
                        (provider.plan.job_id, request_digest)))
                    require(len(active) == 1, "UPSTREAM_INTENT_NOT_DURABLE")
                    operation = active[0]["operation"]
                    with provider.lock:
                        index = len(provider.upstream_requests)
                        require(index < provider.max_requests, "REQUEST_COUNT")
                        provider.upstream_requests.append({"operation_id": operation,
                            "request_digest": request_digest, "authorization_present": False})
                        next(r for r in provider.requests if r["operation_id"] == operation)["forwarded"] = True
                    provider.entered.set()
                    provider.respond(self, json.loads(raw), index, operation)
                except Exception as error:
                    provider.errors.append("upstream:" + (error.code if isinstance(error, Fault)
                                                            else type(error).__name__))
                    self.close_connection = True
                finally:
                    if observer:
                        observer.close()

        if wire:
            self.upstream = ThreadingHTTPServer(("127.0.0.1", 0), UpstreamHandler)
            self.upstream.daemon_threads = False
            self.upstream_thread = threading.Thread(target=self.upstream.serve_forever, daemon=True)
            self.upstream_thread.start()

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_):
                pass

            def do_POST(self):
                self.connection.settimeout(3)
                self.response_started = False
                db = None
                try:
                    length = int(self.headers.get("Content-Length", "0"))
                    require(0 < length <= MAX_REQUEST, "REQUEST_SIZE")
                    require(self.path in {"/v1/responses", "/v1/responses/compact"}, "ROUTE")
                    require(self.headers.get("Authorization") is None and
                            self.headers.get("Transfer-Encoding") is None and
                            self.headers.get("Content-Encoding") is None, "CREDENTIAL_OR_ENCODING")
                    raw = self.rfile.read(length)
                    require(len(raw) == length, "TRUNCATED_REQUEST")
                    body = json.loads(raw)
                    require(body.get("model") == MODEL, "MODEL_POLICY")
                    with provider.lock:
                        index = len(provider.requests)
                        require(index < provider.max_requests, "REQUEST_COUNT")
                        operation = "dispatch-" + uuid.uuid4().hex
                        item = {"operation_id": operation, "path": self.path,
                            "request_digest": hashlib.sha256(raw).hexdigest(),
                            "bytes": length, "body_keys": sorted(body),
                            "tool_catalog": [{"type": t.get("type"), "name": t.get("name"),
                                "tools": [v.get("name") for v in t.get("tools", [])]}
                                for t in body.get("tools", [])],
                            "authorization_present": False, "state": "RECEIVED"}
                        provider.requests.append(item)
                    (provider.database_path.parent / (operation + "-request.json")).write_bytes(raw)
                    db = Database(provider.database_path)
                    cas = CAS(db, provider.objects)
                    gate = InferenceDispatches(db, cas, simulation=True)
                    plan = provider.plan
                    require(plan is not None, "RUNTIME_MISSING")
                    job = db.connection.execute("SELECT state FROM native_jobs WHERE id=?",
                                                (plan.job_id,)).fetchone()
                    require(job is not None and job[0] == "RUNNING", "RUNTIME_NOT_RUNNING")
                    price = put(cas, {"schema": "strata/SyntheticTokenPricing/1", "is_example": True,
                        "currency": "USD", "input_microusd_per_token": 1,
                        "cached_microusd_per_token": 1, "output_microusd_per_token": 1, "real_usd": 0})
                    reserve = ledger(plan, operation, parent=plan.operation_id, calls=1,
                                     spend=10000, pricing=price)
                    scope = {"runtime_job_id": plan.job_id, "profile_digest": plan.profile_digest(),
                        "provider": "strata_local_fixture", "auth_mode": "api_key",
                        "request_digest": item["request_digest"]}
                    bound = put(cas, {"schema": "strata/InferenceDispatchBound/1",
                        "is_example": True, **scope, "reservation_digest": digest(reserve.model_dump()),
                        "pricing_ref": price, "currency": "USD", "finite_dispatch_bound_verified": True,
                        "pricing_semantics_verified": True,
                        "expires_unix_ms": time.time_ns() // 1000000 + 30000})
                    attempt = InferenceAttempt.model_validate({"schema": "strata/InferenceAttempt/1",
                                                               **scope, "bound_ref": bound})

                    def forward():
                        started = time.monotonic()
                        # Independent connection observes the committed intent before
                        # the synthetic provider executes any response work.
                        observer = Database(provider.database_path)
                        try:
                            row = observer.connection.execute("SELECT state FROM inference_attempts "
                                                               "WHERE operation=?", (operation,)).fetchone()
                            require(row is not None and row[0] == "DISPATCHING", "UNDURABLE_DISPATCH")
                        finally:
                            observer.close()
                        item["forwarded"] = True
                        provider.entered.set()
                        usage, event = provider.respond(self, body, index, operation)
                        usage["wall_ms"] = int((time.monotonic() - started) * 1000)
                        raw_ref = put(cas, {"is_example": True, "event": event, "usage": usage})
                        receipt = BudgetLedger.model_validate(reserve.model_dump() | {
                            "posting": "settle", "ledger_id": operation + ":receipt",
                            "source_event_id": operation + ":settle", "metering": "reported",
                            "raw_usage_ref": raw_ref, "usage": reserve.usage.model_dump() | usage})
                        provider.receipts.append((operation, event, receipt))
                        return event, receipt

                    if provider.wire:
                        def headers(status, media):
                            self.response_started = True
                            self.send_response(status)
                            self.send_header("Content-Type", media)
                            self.end_headers()

                        def chunk(data):
                            self.wfile.write(data)
                            self.wfile.flush()

                        endpoint = f"http://127.0.0.1:{provider.upstream.server_port}" + self.path
                        transport = SyntheticResponsesTransport(gate, endpoint,
                            deadline_s=20 if provider.scenario == "helper_parent" else 3)
                        result = transport.execute(plan.account, attempt, reserve, raw,
                                                   on_headers=headers, on_chunk=chunk)
                        saved = db.connection.execute("SELECT body FROM ledger WHERE "
                            "json_extract(body,'$.operation_id')=? AND "
                            "json_extract(body,'$.posting')='settle'", (operation,)).fetchone()
                        receipt = BudgetLedger.model_validate_json(saved[0])
                        media = db.connection.execute("SELECT media_type FROM objects WHERE "
                            "namespace='operator' AND ref=?", (receipt.raw_usage_ref,)).fetchone()[0]
                        parser = ResponsesUsage(MODEL, media)
                        parser.feed(cas.read(OPERATOR, "operator", receipt.raw_usage_ref))
                        event = parser.finish()["event"]
                        provider.receipts.append((operation, event, receipt))
                    else:
                        result = gate.execute(plan.account, attempt, reserve, forward)
                    item["state"] = result["state"]
                    # Reingest the very same authoritative receipt through the public
                    # accounting method, verifying it does not charge again.
                    op, event, receipt = next(r for r in provider.receipts if r[0] == operation)
                    require(not gate.settle(op, event, receipt), "DUPLICATE_CHARGE")
                    item["receipt_deduplicated"] = True
                except (Exception, BrokenPipeError) as error:
                    code = error.code if isinstance(error, Fault) else type(error).__name__
                    with provider.lock:
                        provider.errors.append(code)
                    try:
                        if not self.response_started:
                            self.send_error(400, "synthetic fixture: " + code)
                        self.close_connection = True
                    except OSError:
                        pass
                finally:
                    if db:
                        db.close()

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.server.daemon_threads = False
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def respond(self, handler, body, index, operation):
        event = "response-" + operation
        usage = {"input_tokens": 10, "cached_input_tokens": 2, "output_tokens": 4,
                 "reasoning_tokens": 0, "spend_microusd": 14, "model_calls": 1}
        if self.scenario == "retry" and index == 0:
            data = canonical({"error": {"message": "synthetic transient failure"},
                "id": event, "model": MODEL, "status": "failed",
                "usage": {"input_tokens": 10, "output_tokens": 0, "total_tokens": 10,
                    "input_tokens_details": {"cached_tokens": 2},
                    "output_tokens_details": {"reasoning_tokens": 0}}})
            handler.response_started = True
            handler.send_response(503)
            handler.send_header("Content-Type", "application/json")
            handler.send_header("Content-Length", str(len(data)))
            handler.end_headers()
            handler.wfile.write(data)
            # Authoritative fixture-provider receipt, not an assumption about 503.
            return usage | {"output_tokens": 0, "spend_microusd": 10}, event

        item = {"id": "message-" + operation, "type": "message", "role": "assistant",
                "status": "completed", "content": [{"type": "output_text",
                "text": "Synthetic transport complete.", "annotations": []}]}
        if self.scenario == "compaction" and index == 0:
            catalogs = [i["tools"] for i in body.get("input", [])
                        if i.get("type") == "additional_tools"]
            require(any(t.get("name") == "functions" and
                        any(v.get("name") == "exec" for v in t.get("tools", []))
                        for catalog in catalogs for t in catalog), "FIXTURE_TOOL_MISSING")
            item = {"id": "tool-" + operation, "type": "custom_tool_call",
                    "call_id": "call-" + operation, "namespace": "functions", "name": "exec",
                    "input": 'text("Synthetic compaction fixture.");'}
            usage = usage | {"input_tokens": 9000, "spend_microusd": 9004}
        api_usage = {"input_tokens": usage["input_tokens"],
                     "input_tokens_details": {"cached_tokens": usage["cached_input_tokens"]},
                     "output_tokens": usage["output_tokens"],
                     "output_tokens_details": {"reasoning_tokens": 0},
                     "total_tokens": usage["input_tokens"] + usage["output_tokens"]}
        response = {"id": event, "object": "response", "created_at": 1,
                    "status": "completed", "model": MODEL, "output": [item], "usage": api_usage}
        prefix = sse("response.created", response={**response, "status": "in_progress", "output": []})
        prefix += sse("response.output_item.done", output_index=0, item=item)
        tail = sse("response.completed", response=response)
        if self.scenario == "missing_usage":
            tail = sse("response.completed", response={k: v for k, v in response.items()
                                                       if k != "usage"})
        handler.response_started = True
        handler.send_response(200)
        handler.send_header("Content-Type", "text/event-stream")
        handler.end_headers()
        handler.wfile.write(prefix)
        handler.wfile.flush()
        self.streaming.set()
        if self.scenario in {"interrupt", "restart", "crash"}:
            self.release.wait(4)
            raise Fault("SYNTHETIC_STREAM_INTERRUPTED")
        if self.scenario == "stream_loss":
            raise Fault("SYNTHETIC_STREAM_INTERRUPTED")
        if self.scenario == "helper_parent":
            require(self.release.wait(15), "HELPER_PARENT_TIMEOUT")
        handler.wfile.write(tail)
        handler.wfile.flush()
        if self.scenario == "missing_usage":
            raise Fault("AUTHORITATIVE_USAGE_REQUIRED")
        return usage, event

    def close(self):
        self.release.set()
        self.server.shutdown()
        self.server.server_close()  # Joins all handlers before issuing any seal.
        self.thread.join(3)
        require(not self.thread.is_alive(), "INGRESS_NOT_FENCED")
        if self.wire:
            self.upstream.shutdown()
            self.upstream.server_close()
            self.upstream_thread.join(3)
            require(not self.upstream_thread.is_alive(), "UPSTREAM_NOT_FENCED")


def plan_for(binary, directory, provider, job, parent=None, scenario="success"):
    for name in (job + "-workspace", job + "-profile", job + "-tmp"):
        (directory / name).mkdir()
    config = {"model_provider": "strata_local_fixture",
        "model_providers.strata_local_fixture.name": "Synthetic local provider",
        "model_providers.strata_local_fixture.base_url": f"http://127.0.0.1:{provider.server.server_port}/v1",
        "model_providers.strata_local_fixture.wire_api": "responses",
        "model_providers.strata_local_fixture.requires_openai_auth": False,
        "model_providers.strata_local_fixture.request_max_retries": 1 if scenario == "retry" else 0,
        "model_providers.strata_local_fixture.stream_max_retries": 1,
        "model_providers.strata_local_fixture.stream_idle_timeout_ms":
            20000 if scenario == "helper_parent" else 3000,
        "model_providers.strata_local_fixture.supports_websockets": False,
        "web_search": "disabled", "features.remote_models": False,
        "features.multi_agent": False}
    if scenario == "compaction":
        config["model_auto_compact_token_limit"] = 1000
    plan = NativeLaunch.model_validate({"schema": "strata/NativeLaunch/1", "job_id": job,
        "campaign_id": "synthetic-campaign", "agent_id": "a1", "epoch": 1,
        "role": "helper" if parent else "executor", "purpose": "conformance",
        "parent_job_id": parent, "depth": 1 if parent else 0, "account": "a1",
        "operation_id": job + ":envelope", "workspace": str(directory / (job + "-workspace")),
        "profile_directory": str(directory / (job + "-profile")), "executable": str(binary),
        "binary_digest": BINARY_SHA256, "binary_version": CODEX_VERSION,
        "dovetail_commit": DOVETAIL_COMMIT, "model": MODEL, "provider": "strata_local_fixture",
        "auth_mode": "api_key", "budget_mode": "per_dispatch", "config_overrides": config,
        "environment": {"PATH": str(binary.parent) + os.pathsep + str(Path(os.environ["SystemRoot"]) / "System32"),
            "TEMP": str(directory / (job + "-tmp")), "TMP": str(directory / (job + "-tmp"))},
        "prompt": "Synthetic transport fixture. Do not execute commands or access files.",
        "hard_timeout_s": 25, "output_limit_bytes": 2 * 1024**2, "qualification_ref": None})
    provider.plan = plan
    return plan


def wait_job(runtime, plan):
    until = time.monotonic() + plan.hard_timeout_s + 5
    while plan.job_id in runtime.live and time.monotonic() < until:
        runtime.pump(plan.job_id)
        time.sleep(0.01)
    require(plan.job_id not in runtime.live, "PROBE_PROCESS_TIMEOUT")


def close_budget(runtime, plan, provider):
    seal = put(runtime.cas, {"schema": "strata/InferenceIngressSeal/1", "is_example": True,
        "job_id": plan.job_id, "profile_digest": plan.profile_digest(),
        "process_tree_dead": plan.job_id not in runtime.live, "ingress_closed": True,
        "handlers_fenced": True,
        "attempt_ids": sorted(r[0] for r in runtime.db.connection.execute(
            "SELECT operation FROM inference_attempts WHERE json_extract(request,'$.runtime_job_id')=?",
            (plan.job_id,)))})
    return runtime.close_dispatch_budget(plan.job_id, seal)


def recover_only(directory):
    """Fresh supervisor process, fenced ingress/processes; never replays intent."""
    db = Database(directory / "synthetic.sqlite")
    cas = CAS(db, directory / "objects")
    runtime = NativeExec(db, cas, simulation=True)
    gate = InferenceDispatches(db, cas, simulation=True)
    native = db.connection.execute("SELECT plan,state FROM native_jobs WHERE id='root'").fetchone()
    plan = NativeLaunch.model_validate_json(native[0])
    if native["state"] != "UNSETTLED":
        evidence = json.loads((directory / "process-fence.json").read_bytes())
        require(evidence.get("job_counts", {}).get("active_processes") == 0 and
                evidence.get("child_exit_code") == 79, "CRASH_FENCE_UNVERIFIED")
        fence = put(cas, {"schema": "strata/RuntimeFenced/1", "job_id": "root",
            "epoch": plan.epoch, "process_tree_dead": True, "game_grants_revoked": True,
            "is_example": True, "source": evidence})
        runtime.recover_fenced("root", fence)
    recovered = gate.recover()
    before_replay_checks = gate.budgets.status("project")
    rows = list(db.connection.execute("SELECT * FROM inference_attempts"))
    require(rows, "MISSING_DISPATCH")

    def forbidden_forward():
        raise AssertionError("AMBIGUOUS_REQUEST_REPLAYED")

    for row in rows:
        gate.execute(row["account"], InferenceAttempt.model_validate_json(row["request"]),
                     BudgetLedger.model_validate_json(row["reservation"]), forbidden_forward)
    source = db.connection.execute("SELECT body FROM ledger WHERE "
        "json_extract(body,'$.operation_id')=? AND json_extract(body,'$.posting')='reserve'",
        (plan.operation_id,)).fetchone()
    reserve = BudgetLedger.model_validate_json(source[0])
    require(runtime.start(plan, reserve)["state"] == "UNSETTLED" and not runtime.live,
            "NATIVE_INTENT_REPLAYED")
    try:
        candidate = BudgetLedger.model_validate(reserve.model_dump() | {
            "operation_id": "new-job", "ledger_id": "new-job",
            "source_event_id": "new-job"})
        gate.budgets.post(plan.account, candidate, envelope=True)
    except Fault as error:
        require(error.code == "METERING_UNKNOWN", "WRONG_RESTART_REJECTION")
    else:
        raise AssertionError("UNKNOWN_COST_ADMITTED")
    require(gate.budgets.status("project") == before_replay_checks and
            db.connection.execute("SELECT COUNT(*) FROM inference_attempts").fetchone()[0] == len(rows),
            "RECOVERY_REPLAY_CHANGED_ACCOUNTING")
    result = {"is_example": True, "process_id": os.getpid(), "recovered": recovered,
              "ambiguous_attempts": sum(row["state"] == "UNSETTLED" for row in rows),
              "settled_attempts": sum(row["state"] == "SETTLED" for row in rows), "replayed": 0,
              "budget": gate.budgets.status("project")}
    db.close()
    (directory / "recovery.json").write_text(json.dumps(result, indent=2), encoding="utf-8")


def validate_result(result):
    scenario = result["scenario"]
    attempts, requests = result["attempts"], result["requests"]
    forwarded = [r for r in requests if r.get("forwarded")]
    require(len(attempts) == len(forwarded), "DISPATCH_COUNT_MISMATCH")
    if scenario in {"success", "retry", "compaction", "helpers"}:
        count, spend = {"success": (1, 14), "retry": (2, 24),
                        "compaction": (3, 9032), "helpers": (2, 28)}[scenario]
        require(len(attempts) == count and all(a["state"] == "SETTLED" for a in attempts)
                and all(r.get("receipt_deduplicated") for r in forwarded), "RECEIPT_COUNTS")
        require(result["closure"]["state"] == "FINALIZED" and
                result["runtime"]["returncode"] == 0, "NATIVE_COMPLETION")
        actual = result["budget"]["committed_and_reserved"]
        require(actual["model_calls"] == count and actual["spend_microusd"] == spend and
                not result["budget"]["uncertain"], "TOTALS_MISMATCH")
        if scenario == "retry":
            require(len({r["request_digest"] for r in requests}) == 1, "RETRY_BODY_CHANGED")
        if scenario == "compaction":
            require(result.get("compaction_notice") is True and
                    result.get("compaction_request") is True, "COMPACTION_NOT_OBSERVED")
    else:
        require(len(attempts) == 1 and attempts[0]["state"] == "UNSETTLED" and
                result.get("closure_blocked") == "METERING_UNKNOWN" and
                result["budget"]["uncertain"] and
                result["budget"]["committed_and_reserved"]["spend_microusd"] == 80000,
                "UNCERTAINTY_NOT_HELD")
        if scenario == "stream_loss":
            require(len(requests) > 1 and "METERING_UNKNOWN" in result["provider_errors"],
                    "STREAM_RETRY_NOT_FENCED")
        if scenario == "restart":
            require(result["recovery"]["replayed"] == 0 and
                    result["recovery"]["process_id"] != os.getpid(), "RESTART_NOT_TESTED")
    return "pass"


def run_case(binary, directory, scenario, *, wire=False):
    directory.mkdir()
    db = Database(directory / "synthetic.sqlite")
    cas = CAS(db, directory / "objects")
    runtime = NativeExec(db, cas, simulation=True)
    gate = InferenceDispatches(db, cas, simulation=True)
    limits = dict.fromkeys(DIMENSIONS, 1000000) | {"spend_microusd": 80000}
    gate.budgets.create_account("project", limits, "*")
    gate.budgets.create_account("a1", limits, "synthetic-campaign", "a1", "project",
                                category="development")
    root_scenario = "helper_parent" if scenario == "helpers" else scenario
    provider = LocalProvider(db.path, cas.root, root_scenario, wire=wire)
    plan = plan_for(binary, directory, provider, "root", scenario=root_scenario)
    price = put(cas, {"is_example": True, "real_usd": 0})
    reserve = ledger(plan, plan.operation_id, parent=None, calls=8, spend=80000,
                     pricing=price, inputs=800000, outputs=80000)
    result = {"scenario": scenario, "is_example": True, "real_usd": 0,
              "binary_sha256": BINARY_SHA256, "production_qualified": False,
              "receipt_source": "upstream_wire" if wire else "direct_synthetic_provider"}
    child_provider = None
    try:
        runtime.start(plan, reserve)
        if scenario == "crash":
            require(provider.streaming.wait(10), "STREAM_PREFIX_NOT_OBSERVED")
            runtime.pump(plan.job_id)
            ready = {"native_state": runtime.status(plan.job_id),
                     "dispatch_states": [dict(r) for r in db.connection.execute(
                         "SELECT operation,state FROM inference_attempts")],
                     "provider_requests": provider.requests,
                     "upstream_requests": provider.upstream_requests,
                     "upstream_prefix_flushed": provider.streaming.is_set()}
            with (directory / "crash-ready.json").open("xb") as output:
                output.write(canonical(ready))
                output.flush()
                os.fsync(output.fileno())
            deadline = time.monotonic() + 10
            while not (directory / "crash-now").exists():
                require(time.monotonic() < deadline, "CRASH_COORDINATION_TIMEOUT")
                time.sleep(0.01)
            os._exit(79)  # Deliberately bypass Python finally/settlement/normal cleanup.
        elif scenario == "helpers":
            require(provider.entered.wait(10), "REQUEST_NOT_OBSERVED")
            child_provider = LocalProvider(db.path, cas.root, "success", wire=wire)
            child_plan = plan_for(binary, directory, child_provider, "helper", parent="root")
            child_reserve = ledger(child_plan, child_plan.operation_id, parent=plan.operation_id,
                                   calls=2, spend=20000, pricing=price, inputs=200000, outputs=20000)
            runtime.start(child_plan, child_reserve)
            wait_job(runtime, child_plan)
            child_provider.close()
            result["helper_closure"] = close_budget(runtime, child_plan, child_provider)
            result["helper_turn_usage"] = runtime.usage_report(child_plan.job_id)
            result["while_root_active"] = gate.budgets.status("project")
            provider.release.set()
            wait_job(runtime, plan)
        elif scenario in {"interrupt", "restart"}:
            require(provider.streaming.wait(10), "STREAM_PREFIX_NOT_OBSERVED")
            runtime.interrupt(plan.job_id, "synthetic_interruption")
        else:
            wait_job(runtime, plan)
    finally:
        for job in list(runtime.live):
            runtime.interrupt(job, "probe_cleanup")
        if child_provider and child_provider.thread.is_alive():
            child_provider.close()
        provider.close()
    result["runtime"] = runtime.status(plan.job_id)
    result["requests"] = provider.requests + (child_provider.requests if child_provider else [])
    result["provider_errors"] = provider.errors + (child_provider.errors if child_provider else [])
    result["upstream_requests"] = provider.upstream_requests + (
        child_provider.upstream_requests if child_provider else [])
    result["attempts"] = [dict(r) for r in db.connection.execute(
        "SELECT operation,state,reason FROM inference_attempts")]
    try:
        result["closure"] = close_budget(runtime, plan, provider)
    except Fault as error:
        result["closure_blocked"] = error.code
    result["budget"] = gate.budgets.status("project")
    result["turn_usage"] = runtime.usage_report(plan.job_id)
    if scenario == "compaction":
        texts = [base64.b64decode(json.loads(r[0])["raw_base64"]).decode("utf-8")
                 for r in db.connection.execute("SELECT body FROM native_events WHERE channel='stdout'")]
        result["compaction_notice"] = any("multiple compactions" in t for t in texts)
        # The actual compacting request contains the pinned native summary prompt.
        request_bodies = [json.loads(p.read_bytes()) for p in directory.glob("*-request.json")]
        result["compaction_request"] = any("CONTEXT CHECKPOINT COMPACTION" in
            c.get("text", "") for b in request_bodies for i in b.get("input", [])
            for c in i.get("content", []) if i.get("role") == "user")
    db.export_journal(directory / "journal.jsonl")
    db.close()
    if scenario == "restart":
        env = {k: os.environ[k] for k in ("SystemRoot", "WINDIR") if k in os.environ}
        recovery = subprocess.run([sys.executable, str(Path(__file__).resolve()),
                                   "--recover-only", str(directory)], env=env,
                                  capture_output=True, timeout=15, check=False,
                                  creationflags=subprocess.CREATE_NO_WINDOW)
        (directory / "recovery-stderr.txt").write_bytes(recovery.stderr)
        require(recovery.returncode == 0, "RECOVERY_PROCESS_FAILED")
        result["recovery"] = json.loads((directory / "recovery.json").read_bytes())
    try:
        result["verdict"] = validate_result(result)
    except Fault as error:
        result["verdict"] = "fail"
        result["validation_error"] = error.code
    (directory / "result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def run_crash_case(binary, directory, *, wire):
    """Kill the supervisor through abrupt exit, observe the held outer job, recover."""
    argv = [sys.executable, str(Path(__file__).resolve()), "--codex", str(binary),
            "--crash-child", str(directory)] + (["--wire"] if wire else [])
    env = {k: os.environ[k] for k in ("SystemRoot", "WINDIR") if k in os.environ}
    child = ManagedProcess(argv, directory.parent, env, "")
    drains, failures = [], []

    def drain(source, name):
        # Files are outside the child-owned case so an early setup failure remains visible.
        size = 0
        with (directory.parent / name).open("xb") as output:
            while chunk := source.read(4096):
                size += len(chunk)
                if size > 2 * 1024**2:
                    failures.append("CRASH_CHILD_OUTPUT_LIMIT")
                    child.stop()
                    break
                output.write(chunk)

    for source, name in ((child.process.stdout, "crash-child-stdout.txt"),
                         (child.process.stderr, "crash-child-stderr.txt")):
        thread = threading.Thread(target=drain, args=(source, name), daemon=True)
        thread.start()
        drains.append(thread)
    evidence = {"is_example": True, "verdict": "fail",
                "method": "held job accounting and complete signaled member handles"}
    try:
        deadline = time.monotonic() + 15
        ready_path = directory / "crash-ready.json"
        while not ready_path.exists():
            require(child.poll() is None and time.monotonic() < deadline, "CRASH_CHILD_NOT_READY")
            child.job.observe_members()
            time.sleep(0.02)
        ready = json.loads(ready_path.read_bytes())
        require(ready["native_state"]["state"] == "RUNNING" and
                len(ready["dispatch_states"]) == 1 and
                ready["dispatch_states"][0]["state"] == "DISPATCHING", "CRASH_POINT_MISSED")
        child.job.observe_members()
        before = child.job.accounting()
        before_members = child.job.member_status()
        evidence.update(before_crash=before, before_members=before_members)
        require(before["active_processes"] >= 4, "CRASH_TREE_NOT_OBSERVED")
        require(before["total_processes"] == before_members["held_processes"],
                "CRASH_MEMBER_INVENTORY_INCOMPLETE")
        (directory / "crash-now").touch(exist_ok=False)
        code = child.process.wait(timeout=5)
        evidence["child_exit_code"] = code
        require(code == 79, "CRASH_CHILD_WRONG_EXIT")
        fence_started = time.monotonic()
        deadline = fence_started + 3
        counts, members = child.job.accounting(), child.job.member_status()
        while (counts["active_processes"] or members["signaled_processes"] != counts["total_processes"]) and time.monotonic() < deadline:
            time.sleep(0.01)
            counts, members = child.job.accounting(), child.job.member_status()
        observed = time.monotonic()
        evidence.update(job_counts=counts, member_counts=members,
                        wait_bound_ms=3000, observed_after_ms=(observed - fence_started) * 1000)
        require(observed <= deadline and counts["active_processes"] == 0 and
                0 < counts["total_processes"] == members["held_processes"] == members["signaled_processes"],
                "CRASH_TREE_NOT_FENCED")
        evidence["verdict"] = "pass"
    except Fault as error:
        evidence["failure"] = error.code
        raise
    finally:
        try:
            child.stop()
        finally:
            for thread in drains:
                thread.join(2)
            child.close()
            (directory / "process-fence.json" if directory.is_dir() else
             directory.parent / "process-fence.json").write_bytes(canonical(evidence))
    require(not failures and all(not t.is_alive() for t in drains), "CRASH_CHILD_OUTPUT_LIMIT")
    # A second native supervisor process must classify the persisted RUNNING /
    # DISPATCHING states, retain both holds and refuse both native/request replay.
    recovery = subprocess.run([sys.executable, str(Path(__file__).resolve()),
        "--recover-only", str(directory)], env=env, capture_output=True, timeout=15,
        creationflags=subprocess.CREATE_NO_WINDOW)
    (directory / "recovery-stderr.txt").write_bytes(recovery.stderr)
    require(recovery.returncode == 0, "RECOVERY_PROCESS_FAILED")
    restored = json.loads((directory / "recovery.json").read_bytes())
    require(len(restored["recovered"]) == 1 and restored["replayed"] == 0 and
            restored["budget"]["uncertain"] and
            restored["budget"]["committed_and_reserved"]["spend_microusd"] == 80000,
            "CRASH_RECOVERY_FAILED")
    result = {"scenario": "crash", "is_example": True, "verdict": "pass", "real_usd": 0,
              "receipt_source": "upstream_wire" if wire else "direct_synthetic_provider",
              "production_qualified": False, "before_crash": ready, "process_fence": evidence,
              "recovery": restored, "budget": restored["budget"]}
    (directory / "result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--recover-only", type=Path)
    parser.add_argument("--crash-child", type=Path)
    parser.add_argument("--codex", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--wire", action="store_true", help="Use a separate upstream HTTP fixture")
    parser.add_argument("--cases", nargs="+", default=["success", "retry", "missing_usage",
        "stream_loss", "interrupt", "compaction", "helpers", "restart"])
    args = parser.parse_args()
    if args.recover_only:
        recover_only(args.recover_only)
        return
    if args.crash_child:
        require(file_hash(args.codex) == BINARY_SHA256, "RUNTIME_PIN_MISMATCH")
        run_case(args.codex.resolve(), args.crash_child, "crash", wire=args.wire)
        raise AssertionError("CRASH_CHILD_RETURNED")
    require(args.codex is not None and args.output is not None, "PROBE_ARGUMENTS_REQUIRED")
    require(os.name == "nt", "WINDOWS_PIN_REQUIRED")
    require(file_hash(args.codex) == BINARY_SHA256, "RUNTIME_PIN_MISMATCH")
    root = Path(__file__).resolve().parents[1]
    output = args.output.resolve()
    require(not output.is_relative_to(root) and not output.exists(), "PRIVATE_FRESH_OUTPUT_REQUIRED")
    output.mkdir(parents=True)
    source_paths = [Path(__file__).resolve(), root / "src/mcbench/budgets.py",
                    root / "src/mcbench/native.py", root / "src/mcbench/inference_dispatch.py",
                    root / "src/mcbench/inference_transport.py", root / "src/mcbench/processes.py"]
    manifest = {"schema": "strata/SyntheticNativeDispatchProbe/1", "is_example": True,
                "binary_sha256": BINARY_SHA256, "binary_version": CODEX_VERSION,
                "source_sha256": {p.relative_to(root).as_posix(): file_hash(p) for p in source_paths},
                "cases": args.cases, "started_unix_ms": time.time_ns() // 1000000,
                "real_usd": 0, "production_qualified": False, "wire_transport": args.wire}
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    results = []
    for scenario in args.cases:
        require(scenario in {"success", "retry", "missing_usage", "stream_loss", "interrupt",
                             "compaction", "helpers", "restart", "crash"},
                "UNKNOWN_CASE")
        result = (run_crash_case(args.codex.resolve(), output / scenario, wire=args.wire)
                  if scenario == "crash" else
                  run_case(args.codex.resolve(), output / scenario, scenario, wire=args.wire))
        results.append(result)
        print(json.dumps({k: result.get(k) for k in (
            "scenario", "verdict", "validation_error", "runtime", "attempts",
            "closure_blocked", "budget", "provider_errors")}), flush=True)
    (output / "summary.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    require(all(r["verdict"] == "pass" for r in results), "PROBE_FAILED")


if __name__ == "__main__":
    main()
