"""Operator-owned native inference gateway; no model loop or new allowance.

One listener belongs to one native job. Admission closes before transports are
cancelled, but the port stays owned until native termination is confirmed.
Unknown usage survives shutdown. A crashed owner cannot reopen the same job.
"""

import hashlib
import socket
import threading
import time
import uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field

from .accounting import EstimateBasis, FiniteExposure
from .contracts import Digest, Id, Ref, Strict
from .inference_dispatch import InferenceAttempt, InferenceDispatches
from .inference_transport import strict_json, transport_failure_code
from .native_admission import NativeAdmission, context_metadata
from .native_ingress import NativeIngress, provider_binding
from .native_oauth import NativeOAuthRequest, NativeOAuthTransport, SyntheticOAuthTransport
from .records import BudgetLedger
from .storage import CAS, Database, Principal, canonical, digest, require

POLICY = "native-budgeted-loopback-gateway/1"
OPERATOR = Principal("operator", "operator")
TERMINAL = {"REJECTED", "SETTLED", "UNSETTLED"}


class GatewayConfig(Strict):
    schema_: Literal["strata/NativeGatewayConfig/1"] = Field(alias="schema")
    job_id: Id
    profile_digest: Digest
    pricing_ref: Ref
    exposure: FiniteExposure
    transport_qualification_ref: Ref | None
    authorization_id: Id | None
    skill_corpus_ref: Ref | None = None
    helper_calls_bound: Annotated[int, Field(ge=1, le=32)] = 1
    max_requests: Annotated[int, Field(ge=1, le=256)] = 32
    max_handlers: Annotated[int, Field(ge=1, le=16)] = 4
    read_timeout_s: Annotated[int, Field(ge=1, le=10)] = 3
    request_timeout_s: Annotated[int, Field(ge=1, le=30)] = 30

    def profile_fingerprint(self):
        # Evidence refers to the resulting profile, so refs cannot hash themselves.
        body = self.model_dump(exclude={"job_id", "profile_digest", "transport_qualification_ref"})
        if self.skill_corpus_ref is None:
            body.pop("skill_corpus_ref")
        body["exposure"].pop("enforcement_ref")
        return digest({"policy": POLICY, "config": body})


def require_gateway(db, plan, state):
    require(db.execute("SELECT 1 FROM sqlite_master WHERE name='native_gateways'").fetchone(),
            "GATEWAY_REQUIRED")
    row = db.execute("SELECT * FROM native_gateways WHERE job=?", (plan.job_id,)).fetchone()
    require(row is not None and row["state"] == state and row["profile"] == plan.profile_digest()
            and row["config_digest"] == plan.gateway_config_digest, "GATEWAY_NOT_ADMITTED")
    return row


def require_gateway_seal(database, cas, plan, proof, simulation):
    row = require_gateway(database.connection, plan, "CLOSED")
    require(proof.get("gateway_fence_ref") == row["fence_ref"] and row["fence_ref"] is not None,
            "GATEWAY_FENCE_REQUIRED")
    fence = cas.json(OPERATOR, "operator", row["fence_ref"])
    requests = list(database.connection.execute("SELECT operation,state FROM native_gateway_requests "
                                                "WHERE job=? ORDER BY operation", (plan.job_id,)))
    require(fence.get("schema") == "strata/NativeGatewayFence/1" and
            fence.get("is_example") is simulation and fence.get("owner") == row["owner"] and
            fence.get("config_digest") == plan.gateway_config_digest and
            fence.get("request_ids") == [r["operation"] for r in requests] and
            all(r["state"] in TERMINAL for r in requests), "GATEWAY_FENCE_REQUIRED")


class NativeGateway:
    def __init__(self, database_path, objects, *, simulation=False, fixture_upstream=None):
        require(type(simulation) is bool and (fixture_upstream is None) != simulation,
                "GATEWAY_MODE")
        self.database_path, self.objects = Path(database_path), Path(objects)
        self.simulation, self.fixture_upstream = simulation, fixture_upstream
        self.plan = self.config = None
        self.owner = uuid.uuid4().hex
        self.stopping = threading.Event()
        self.stopping.set()  # Configure explicitly before accepting model traffic.
        self.finished = threading.Event()
        self.condition = threading.Condition()
        self.active = {}
        service = self

        class Server(ThreadingHTTPServer):
            daemon_threads = False
            block_on_close = True
            allow_reuse_address = False

            def server_bind(self):
                if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
                    self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
                super().server_bind()

            def process_request(self, request, address):
                with service.condition:
                    limit = service.config.max_handlers if service.config else 1
                    if len(service.active) >= limit:
                        self.shutdown_request(request)
                        return
                    service.active[request] = {"deadline": time.monotonic() + (
                        service.config.read_timeout_s if service.config else 1), "transport": None}
                try:
                    super().process_request(request, address)
                except BaseException:
                    with service.condition:
                        service.active.pop(request, None)
                        service.condition.notify_all()
                    raise

            def process_request_thread(self, request, address):
                try:
                    super().process_request_thread(request, address)
                finally:
                    with service.condition:
                        service.active.pop(request, None)
                        service.condition.notify_all()

            def handle_error(self, *_):
                pass  # Do not print requests, OAuth headers or exception text.

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_):
                pass

            def send_error(self, code, *_):
                self.send_response(code)
                self.send_header("Content-Length", "0")
                self.end_headers()
                self.close_connection = True

            def do_POST(self):
                service._handle(self)

        with _database(self.database_path) as db:
            self._tables(db)
        self.server = Server(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever,
                                       kwargs={"poll_interval": .05}, daemon=True)
        self.watchdog = threading.Thread(target=self._watch, daemon=True)
        self.thread.start()
        self.watchdog.start()

    @property
    def base_url(self):
        return f"http://127.0.0.1:{self.server.server_port}/v1"

    def _tables(self, database):
        with database.transaction() as db:
            db.execute("CREATE TABLE IF NOT EXISTS native_gateways (job TEXT PRIMARY KEY, profile TEXT, "
                       "config_digest TEXT, config TEXT, owner TEXT, state TEXT, fence_ref TEXT)")
            db.execute("CREATE TABLE IF NOT EXISTS native_gateway_requests (operation TEXT PRIMARY KEY, "
                       "job TEXT, ordinal INTEGER, route TEXT, request_digest TEXT, state TEXT, reason TEXT)")

    def bind(self, plan, config):
        plan, config = plan.model_copy(deep=True), config.model_copy(deep=True)
        require(self.plan is None and not self.finished.is_set(), "GATEWAY_ALREADY_BOUND")
        binding = provider_binding(plan)
        require(config.job_id == plan.job_id and config.profile_digest == plan.profile_digest() and
                plan.gateway_config_digest == config.profile_fingerprint() and binding["native_oauth"] and
                binding["authority"] == f"127.0.0.1:{self.server.server_port}", "GATEWAY_PROFILE")
        require(self.simulation or config.authorization_id is not None and
                config.transport_qualification_ref is not None, "GATEWAY_QUALIFICATION_REQUIRED")
        with _database(self.database_path) as db:
            cas = CAS(db, self.objects)
            gate = InferenceDispatches(db, cas, simulation=self.simulation,
                                      authorization_id=config.authorization_id)
            NativeAdmission(db, cas)
            if config.skill_corpus_ref:
                from .native_skills import instructions_for_corpus, validate_skill_bootstrap
                from .native_skill_activation import INSTRUCTIONS
                expected = instructions_for_corpus(cas, config.skill_corpus_ref)
                if plan.skill_activation_ref:
                    expected += INSTRUCTIONS
                require(plan.config_overrides.get("developer_instructions") == expected,
                        "SKILL_INSTRUCTIONS_MISMATCH")
                validate_skill_bootstrap(cas, config.skill_corpus_ref, plan)
            basis = EstimateBasis.model_validate_json(gate._private_ref(config.pricing_ref, 65536))
            require(plan.accounting_basis_digest == basis.fingerprint() and
                    config.exposure.input_bound_method == "provider_context_limit" and
                    config.exposure.output_bound_method == "provider_model_limit", "GATEWAY_EXPOSURE")
            config.exposure.amount(basis)
            NativeIngress(db).register(plan)
            with db.transaction() as conn:
                require(conn.execute("SELECT 1 FROM native_gateways WHERE job=?", (plan.job_id,)).fetchone()
                        is None, "GATEWAY_ALREADY_REGISTERED")
                conn.execute("INSERT INTO native_gateways VALUES(?,?,?,?,?,'OPEN',NULL)", (
                    plan.job_id, plan.profile_digest(), config.profile_fingerprint(),
                    config.model_dump_json(), self.owner))
                db.event(conn, "native.gateway_opened", {"job": plan.job_id, "owner": self.owner,
                                                       "config_digest": config.profile_fingerprint()})
        self.plan, self.config = plan, config
        self.stopping.clear()

    def _put(self, cas, body):
        return cas.put(OPERATOR, "operator", "operator", canonical(body))

    def _open(self, db):
        require(not self.stopping.is_set(), "GATEWAY_STOPPING")
        require_gateway(db.connection, self.plan, "OPEN")

    def _record(self, db, state, operation, reason=None, request_digest=None):
        with db.transaction() as conn:
            conn.execute("UPDATE native_gateway_requests SET state=?,reason=?,request_digest="
                         "COALESCE(?,request_digest) WHERE operation=?", (state, reason, request_digest, operation))
            db.event(conn, "native.gateway_request", {"operation": operation, "job": self.plan.job_id,
                                                     "state": state, "reason": reason})

    def _reservation(self, template, operation, parent, ordinal, request_bound, *, helper=False, calls=1):
        exposure = self.config.exposure
        return template.model_copy(update={"ledger_id": operation + ":reserve", "operation_id": operation,
            "parent_operation_id": parent, "source_event_id": operation + ":reserve", "seq": ordinal,
            "recorded_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
            "kind": "helper" if helper else "model", "pricing_ref": self.config.pricing_ref,
            "reason": "native gateway finite exposure; estimate is not an OAuth charge",
            "usage": template.usage.model_copy(update={"input_tokens": exposure.max_input_tokens * calls,
                "cached_input_tokens": 0, "output_tokens": exposure.max_output_tokens * calls,
                "reasoning_tokens": 0, "model_calls": calls, "primitive_events": 0, "avatar_ticks": 0,
                "wall_ms": 0, "spend_microusd": request_bound * calls})})

    def _prepare(self, db, cas, raw, operation, ordinal):
        body = strict_json(raw)
        metadata = context_metadata(body)
        admission = NativeAdmission(db, cas)
        admission.wait_for_root(self.plan.job_id)
        thread = metadata["thread_id"]
        helper = metadata["agent_name"] != "/root"
        parent = admission.child_envelope_id(self.plan.job_id, thread) if helper else self.plan.operation_id
        template = db.connection.execute("SELECT body FROM ledger WHERE "
            "json_extract(body,'$.operation_id')=? AND json_extract(body,'$.posting')='reserve'",
            (self.plan.operation_id,)).fetchone()
        require(template is not None, "OPERATION_LINEAGE")
        template = BudgetLedger.model_validate_json(template[0])
        basis = EstimateBasis.model_validate(cas.json(OPERATOR, "operator", self.config.pricing_ref))
        request_bound = self.config.exposure.amount(basis)
        reserve = self._reservation(template, operation, parent, ordinal, request_bound, helper=helper)
        child = None
        if helper and not db.connection.execute("SELECT 1 FROM native_participants WHERE job=? AND thread=?",
                                                (self.plan.job_id, thread)).fetchone():
            ancestor = db.connection.execute("SELECT envelope FROM native_participants WHERE job=? AND thread=?",
                                             (self.plan.job_id, metadata.get("parent_thread_id"))).fetchone()
            require(ancestor is not None, "NATIVE_LINEAGE")
            child = self._reservation(template, parent, ancestor[0], ordinal, request_bound, helper=True,
                                      calls=self.config.helper_calls_bound)
        fields = {"runtime_job_id": self.plan.job_id, "profile_digest": self.plan.profile_digest(),
            "provider": self.plan.provider, "auth_mode": self.plan.auth_mode,
            "request_digest": hashlib.sha256(raw).hexdigest()}
        bound = self._put(cas, {"schema": "strata/InferenceDispatchBound/2", "is_example": self.simulation,
            **fields, "reservation_digest": digest(reserve.model_dump()), "pricing_ref": self.config.pricing_ref,
            "currency": "USD", "finite_dispatch_bound_verified": True, "pricing_semantics_verified": True,
            "expires_unix_ms": time.time_ns() // 1000000 + self.config.request_timeout_s * 1000,
            "exposure": self.config.exposure.model_dump()})
        attempt = InferenceAttempt.model_validate({"schema": "strata/InferenceAttempt/1", **fields, "bound_ref": bound})
        admission.prepare(self.plan.account, attempt, reserve, raw, child_envelope=child)
        return admission, attempt, reserve

    def _handle(self, handler):
        operation = None
        credentials = None
        started = False
        db = None
        try:
            require(self.plan is not None, "GATEWAY_NOT_ADMITTED")
            db = Database(self.database_path)
            self._open(db)
            ingress = NativeIngress(db)
            ingress.authenticate(self.plan.job_id, handler.headers, handler.path)
            require(sum(len(k) + len(v) for k, v in handler.headers.items()) <= 65536, "HEADER_SIZE")
            lengths = handler.headers.get_all("Content-Length", [])
            require(len(lengths) == 1 and lengths[0].isascii() and lengths[0].isdigit() and
                    0 < int(lengths[0]) <= 1024 * 1024 and not handler.headers.get_all("Transfer-Encoding")
                    and not handler.headers.get_all("Content-Encoding"), "REQUEST_SIZE")
            with db.transaction() as conn:
                ordinal = conn.execute("SELECT count(*) FROM native_gateway_requests WHERE job=?",
                                       (self.plan.job_id,)).fetchone()[0] + 1
                require(ordinal <= self.config.max_requests, "GATEWAY_REQUEST_LIMIT")
                operation = "gateway-" + uuid.uuid4().hex
                conn.execute("INSERT INTO native_gateway_requests VALUES(?,?,?,?,NULL,'READING',NULL)",
                             (operation, self.plan.job_id, ordinal, handler.path))
            raw = bytearray()
            while len(raw) < int(lengths[0]):
                piece = handler.rfile.read1(min(65536, int(lengths[0]) - len(raw)))
                require(piece, "TRUNCATED_REQUEST")
                raw.extend(piece)
            raw = bytes(raw)
            self._open(db)
            credentials = NativeOAuthRequest(ingress, self.plan.job_id, operation,
                                             hashlib.sha256(raw).hexdigest(), handler.headers, handler.path)
            self._record(db, "PREPARING", operation, request_digest=credentials.request_digest)
            cas = CAS(db, self.objects)
            gate = InferenceDispatches(db, cas, simulation=self.simulation,
                                      authorization_id=self.config.authorization_id)
            admission, attempt, reserve = self._prepare(db, cas, raw, operation, ordinal)
            transport = (SyntheticOAuthTransport(gate, credentials, self.fixture_upstream + handler.path,
                deadline_s=self.config.request_timeout_s) if self.simulation else
                NativeOAuthTransport(gate, credentials, self.config.transport_qualification_ref,
                                     deadline_s=self.config.request_timeout_s))
            with self.condition:
                info = self.active[handler.connection]
                info.update(transport=transport, deadline=time.monotonic() + self.config.request_timeout_s)
            def headers(status, media):
                nonlocal started
                started = True
                handler.send_response(status)
                handler.send_header("Content-Type", media)
                handler.end_headers()
            def chunk(data):
                handler.wfile.write(data)
                handler.wfile.flush()
            def begin():
                self._open(db)
                grant = admission.enroll(operation)
                if self.config.skill_corpus_ref:
                    from .native_skills import project_initial_skills
                    project_initial_skills(db, cas, self.plan, grant, self.config.skill_corpus_ref)
            result = transport.execute(self.plan.account, attempt, reserve, raw,
                on_headers=headers, on_chunk=chunk, after_begin=begin)
            self._record(db, result["state"], operation)
        except Exception as error:
            reason = transport_failure_code(error)
            if db and operation:
                row = db.connection.execute("SELECT state FROM inference_attempts WHERE operation=?",
                                            (operation,)).fetchone()
                self._record(db, row[0] if row else "REJECTED", operation,
                             reason)
            elif db and reason == "GATEWAY_REQUEST_LIMIT":
                with db.transaction() as conn:
                    db.event(conn, "native.gateway_refused", {"job": self.plan.job_id, "reason": reason,
                                                             "max_requests": self.config.max_requests})
            if not started:
                try:
                    if reason in {"GATEWAY_REQUEST_LIMIT", "METERING_UNKNOWN"}:
                        message = ("The pilot request limit has been reached." if reason == "GATEWAY_REQUEST_LIMIT"
                                   else "A prior request has unresolved usage.")
                        body = canonical({"error": {"code": reason, "type": "strata_gateway_error",
                            "message": message + " Stop; do not retry."}})
                        handler.send_response(403)
                        handler.send_header("Content-Type", "application/json")
                        handler.send_header("Content-Length", str(len(body)))
                        handler.end_headers()
                        handler.wfile.write(body)
                    else:
                        handler.send_error(403)
                except OSError:
                    pass
        finally:
            if credentials:
                credentials.close()
            if db:
                db.close()
            handler.close_connection = True

    def _cancel(self, sock, info):
        if info["transport"]:
            info["transport"].cancel()
        try:
            sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass

    def _watch(self):
        while not self.finished.wait(.025):
            with self.condition:
                expired = [(s, i) for s, i in self.active.items() if time.monotonic() > i["deadline"]]
            for sock, info in expired:
                self._cancel(sock, info)

    def stop_admission(self):
        self.stopping.set()
        with self.condition:
            active = list(self.active.items())
        for sock, info in active:
            self._cancel(sock, info)
        if self.plan:
            with _database(self.database_path) as db:
                NativeIngress(db).revoke(self.plan.job_id)
                with db.transaction() as conn:
                    conn.execute("UPDATE native_gateways SET state='CLOSING' WHERE job=? AND state='OPEN'",
                                 (self.plan.job_id,))

    def close(self, runtime, *, wait_s=5):
        self.stop_admission()
        require(0 <= wait_s <= 30, "GATEWAY_CLOSE_BOUND")
        if self.plan:
            job = runtime.db.connection.execute("SELECT state FROM native_jobs WHERE id=?",
                                                (self.plan.job_id,)).fetchone()
            require(runtime.db.path == self.database_path.resolve() and self.plan.job_id not in runtime.live and
                    (job is None or job[0] in {"UNSETTLED", "FINALIZED", "REJECTED"}),
                    "RUNTIME_NOT_QUIESCENT")
        self.server.shutdown()
        deadline = time.monotonic() + wait_s
        with self.condition:
            while self.active and time.monotonic() < deadline:
                self.condition.wait(max(0, deadline - time.monotonic()))
            require(not self.active, "GATEWAY_HANDLERS_UNFENCED")
        self.server.server_close()
        self.thread.join(1)
        self.finished.set()
        self.watchdog.join(1)
        require(not self.thread.is_alive() and not self.watchdog.is_alive(), "GATEWAY_HANDLERS_UNFENCED")
        if not self.plan:
            return None
        with _database(self.database_path) as db:
            cas = CAS(db, self.objects)
            requests = list(db.connection.execute("SELECT operation,state FROM native_gateway_requests "
                                                "WHERE job=? ORDER BY operation", (self.plan.job_id,)))
            require(all(r["state"] in TERMINAL for r in requests), "GATEWAY_REQUEST_UNFINISHED")
            fence = self._put(cas, {"schema": "strata/NativeGatewayFence/1", "is_example": self.simulation,
                "owner": self.owner, "config_digest": self.config.profile_fingerprint(),
                "request_ids": [r["operation"] for r in requests]})
            with db.transaction() as conn:
                conn.execute("UPDATE native_gateways SET state='CLOSED',fence_ref=? WHERE job=?",
                             (fence, self.plan.job_id))
            attempts = [r[0] for r in db.connection.execute("SELECT operation FROM inference_attempts WHERE "
                "json_extract(request,'$.runtime_job_id')=? ORDER BY operation", (self.plan.job_id,))]
            participants = [r[0] for r in db.connection.execute("SELECT thread FROM native_participants "
                "WHERE job=? ORDER BY thread", (self.plan.job_id,))]
            return self._put(cas, {"schema": "strata/InferenceIngressSeal/1", "is_example": self.simulation,
                "job_id": self.plan.job_id, "profile_digest": self.plan.profile_digest(),
                "process_tree_dead": True, "ingress_closed": True, "handlers_fenced": True,
                "attempt_ids": attempts, "participant_threads": participants, "gateway_fence_ref": fence})


class _database:
    def __init__(self, path):
        self.path = path

    def __enter__(self):
        self.database = Database(self.path)
        return self.database

    def __exit__(self, *_):
        self.database.close()
