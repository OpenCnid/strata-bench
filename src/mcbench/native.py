"""Native exec process adapter; no custom model loop or synthetic upstream SDK.

Production starts require private qualification for the exact launch profile.
Process fixtures can test lifecycle without a provider. Neither process success
nor turn-level JSONL usage certifies plugin loading, isolation or all-call costs.
"""

import base64
import json
import os
import queue
import threading
import time
from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field, JsonValue

from .accounting import EstimateBasis
from .budgets import Budgets
from .authorization import Authorizations
from .contracts import Digest, Id, Positive, Ref, Strict, UInt
from .inventory import file_hash
from .processes import ManagedProcess
from .records import BudgetLedger
from .runtime import CODEX_VERSION, DOVETAIL_COMMIT, ExecUsageReader
from .storage import Fault, Principal, canonical, digest, reject_links, require

REQUIRED_PROOFS = {"plugin_load_and_invocation", "isolated_tools_and_egress",
                   "helper_boundary_and_accounting", "all_call_budget_gateway",
                   "interrupt_and_fresh_handoff", "provider_credential_boundary"}
CONFORMANCE_PREREQUISITES = {"isolated_tools_and_egress", "all_call_budget_gateway",
                            "provider_credential_boundary"}
ACTIVE = ("PREPARED", "STARTING", "RUNNING", "STOPPING", "UNSETTLED")


class NativeLaunch(Strict):
    schema_: Literal["strata/NativeLaunch/1"] = Field(alias="schema")
    job_id: Id
    campaign_id: Id
    agent_id: Id
    epoch: Positive
    role: Literal["executor", "helper"]
    purpose: Literal["campaign", "conformance"] = "campaign"
    parent_job_id: Id | None
    depth: UInt
    helper_limit: Annotated[int, Field(ge=0, le=32)] = 2
    account: Id
    operation_id: Id
    workspace: str
    profile_directory: str
    executable: str
    binary_digest: Digest
    binary_version: str
    dovetail_commit: str
    model: Annotated[str, Field(min_length=1, max_length=128)]
    provider: str = "openai"
    auth_mode: Literal["chatgpt_oauth", "api_key"] = "chatgpt_oauth"
    budget_mode: Literal["whole_job", "per_dispatch"] = "whole_job"
    session_storage: Literal["ephemeral", "private_profile"] = "ephemeral"
    accounting_basis_digest: Digest | None = None
    broker_policy: Literal["native-stdio-projected-artifacts-executor-game/1"] | None = None
    bootstrap_manifest: str | None = None
    bootstrap_digest: Digest | None = None
    ingress_policy: Literal["native-job-http-header/1"] | None = None
    gateway_config_digest: Digest | None = None
    # Operator-constructed frozen native settings, not model-provided overrides.
    config_overrides: dict[str, JsonValue]
    environment: dict[str, str]
    prompt: Annotated[str, Field(max_length=32000)]
    hard_timeout_s: Annotated[int, Field(ge=1, le=300)]
    output_limit_bytes: Annotated[int, Field(ge=1024, le=64 * 1024**2)]
    qualification_ref: Ref | None

    def profile_digest(self):
        # Episode text, identities and locations vary; execution affordances do not.
        body = {k: getattr(self, k) for k in (
            "binary_digest", "binary_version", "dovetail_commit", "model",
            "config_overrides", "hard_timeout_s", "output_limit_bytes", "helper_limit",
            "provider", "auth_mode", "purpose", "budget_mode", "session_storage")}
        # Preserve historical profile hashes; new estimate profiles bind the basis.
        if self.accounting_basis_digest is not None:
            body["accounting_basis_digest"] = self.accounting_basis_digest
        if self.broker_policy is not None:
            body["broker_policy"] = self.broker_policy
        if self.bootstrap_digest is not None:
            body["bootstrap_digest"] = self.bootstrap_digest
        if self.ingress_policy is not None:
            body["ingress_policy"] = self.ingress_policy
        if self.gateway_config_digest is not None:
            body["gateway_config_digest"] = self.gateway_config_digest
        return digest(body)


def _toml_value(value):
    require(value is not None, "CONFIG_UNSUPPORTED")
    if isinstance(value, dict):
        return "{" + ",".join(json.dumps(k, ensure_ascii=False) + "=" + _toml_value(v)
                              for k, v in sorted(value.items())) + "}"
    if isinstance(value, list):
        return "[" + ",".join(_toml_value(v) for v in value) + "]"
    return json.dumps(value, ensure_ascii=False, allow_nan=False)


def native_argv(plan: NativeLaunch):
    argv = [plan.executable, "exec", "--json", "--strict-config", "--ignore-user-config",
            "--ignore-rules", "--skip-git-repo-check", "--color", "never",
            "--sandbox", "read-only" if plan.bootstrap_digest else "workspace-write",
            "--cd", plan.workspace, "--model", plan.model]
    if plan.session_storage == "ephemeral":
        argv.append("--ephemeral")
    for key, value in sorted(plan.config_overrides.items()):
        require(key and "\x00" not in key and "=" not in key and "\n" not in key,
                "CONFIG_UNSUPPORTED")
        argv.extend(["-c", key + "=" + _toml_value(value)])
    return [*argv, "-"]  # ordinary prompt via stdin, never command line or live injections


class NativeExec:
    def __init__(self, database, cas, *, simulation=False, evidence_namespace="operator",
                 revoke_game=None, authorization_id=None):
        self.db, self.cas = database, cas
        self.simulation, self.namespace = simulation, evidence_namespace
        self.budgets = Budgets(database)
        self.revoke_game = revoke_game
        self.authorization_id = authorization_id
        self.authorizations = Authorizations(database)
        self.live = {}
        self.integrity_holds = {}
        with self.db.transaction() as db:
            self.authorizations.require_store_mode(simulation)
            if db.execute("SELECT name FROM sqlite_master "
                          "WHERE name='inference_dispatch_profile'").fetchone():
                dispatch = db.execute("SELECT simulation FROM inference_dispatch_profile").fetchone()
                require(dispatch is not None and bool(dispatch[0]) == simulation,
                        "DISPATCH_PROFILE_MISMATCH")
            db.execute("CREATE TABLE IF NOT EXISTS native_profile "
                       "(singleton INTEGER PRIMARY KEY CHECK(singleton=1), simulation INTEGER)")
            row = db.execute("SELECT simulation FROM native_profile").fetchone()
            if row:
                require(bool(row[0]) == simulation, "SIMULATION_STORE")
            else:
                db.execute("INSERT INTO native_profile VALUES(1,?)", (int(simulation),))
            db.execute("CREATE TABLE IF NOT EXISTS native_jobs (id TEXT PRIMARY KEY, "
                       "campaign TEXT, agent TEXT, epoch INTEGER, role TEXT, parent TEXT, "
                       "plan_digest TEXT, plan TEXT, state TEXT, started REAL, ended REAL, "
                       "returncode INTEGER, reason TEXT)")
            db.execute("CREATE UNIQUE INDEX IF NOT EXISTS one_native_executor ON "
                       "native_jobs(campaign,agent) WHERE role='executor' AND "
                       "state IN ('PREPARED','STARTING','RUNNING','STOPPING','UNSETTLED')")
            db.execute("CREATE TABLE IF NOT EXISTS native_events (job TEXT REFERENCES native_jobs(id), "
                       "cursor INTEGER, channel TEXT, body TEXT, PRIMARY KEY(job,cursor))")

    def _proof(self, plan):
        require(plan.qualification_ref is not None, "RUNTIME_UNQUALIFIED")
        proof = self.cas.json(Principal("operator", "operator"), self.namespace,
                              plan.qualification_ref)
        require(proof.get("schema") == "strata/RuntimeQualification/1" and
                proof.get("is_example") is False and proof.get("profile_digest") ==
                plan.profile_digest() and proof.get("expires_unix", 0) > time.time() and
                proof.get("purpose", "campaign") == plan.purpose,
                "RUNTIME_UNQUALIFIED")
        required = CONFORMANCE_PREREQUISITES if plan.purpose == "conformance" else REQUIRED_PROOFS
        require(set(proof.get("checks", {})) == required, "RUNTIME_UNQUALIFIED")
        for check, ref in proof["checks"].items():
            item = self.cas.json(Principal("operator", "operator"), self.namespace, ref)
            require(item.get("result") == "pass" and item.get("is_example") is False and
                    item.get("check") == check and item.get("profile_digest") == plan.profile_digest(),
                    "RUNTIME_UNQUALIFIED")
            if check == "isolated_tools_and_egress":
                require(item.get("workspace") == plan.workspace and
                        item.get("profile_directory") == plan.profile_directory and
                        item.get("role") == plan.role and item.get("environment_digest") ==
                        digest(plan.environment), "RUNTIME_BOUNDARY_MISMATCH")
            if check == "all_call_budget_gateway":
                require(item.get("currency") == "USD" and
                        item.get("auth_mode") == plan.auth_mode and
                        item.get("pricing_semantics_verified") is True and
                        item.get("finite_dispatch_bound_verified") is True,
                        "BILLING_BOUND_UNVERIFIED")
                require(plan.accounting_basis_digest is not None and
                        item.get("accounting_basis_digest") == plan.accounting_basis_digest,
                        "ACCOUNTING_BASIS_MISMATCH")

    def _validate(self, plan, reserve, fixture_argv):
        db = self.db.connection
        if db.execute("SELECT 1 FROM sqlite_master WHERE name='inference_exposure_faults'").fetchone():
            require(db.execute("SELECT 1 FROM inference_exposure_faults LIMIT 1").fetchone() is None,
                    "INFERENCE_EXPOSURE_QUARANTINED")
        require(reserve.posting == "reserve" and reserve.campaign_id == plan.campaign_id and
                reserve.agent_id == plan.agent_id and reserve.operation_id == plan.operation_id and
                reserve.epoch == plan.epoch, "OPERATION_LINEAGE")
        require(reserve.kind == ("helper" if plan.role == "helper" else "model"), "OPERATION_LINEAGE")
        if plan.purpose == "conformance":
            require(reserve.campaign_account == "development", "CONFORMANCE_ACCOUNT_REQUIRED")
        require(reserve.usage.spend_microusd is not None and reserve.usage.spend_microusd > 0,
                "SPENDING_CEILING_REQUIRED")
        require(plan.depth <= 2 and ((plan.role == "executor" and plan.depth == 0 and
                plan.parent_job_id is None) or (plan.role == "helper" and plan.depth > 0 and
                plan.parent_job_id is not None)), "HELPER_LINEAGE")
        workspace, profile = Path(plan.workspace), Path(plan.profile_directory)
        require(workspace.is_absolute() and profile.is_absolute() and workspace != profile and
                not profile.is_relative_to(workspace) and not workspace.is_relative_to(profile),
                "UNSAFE_PATH")
        for path in (workspace, profile, Path(plan.executable)):
            reject_links(path)
        require(workspace.is_dir() and profile.is_dir(), "WORKSPACE_MISSING")
        require(Path(plan.executable).is_absolute() and file_hash(Path(plan.executable)) ==
                plan.binary_digest, "RUNTIME_PIN_MISMATCH")
        require(set(plan.environment) <= {"PATH", "LANG", "TZ", "TMP", "TEMP",
                                         "STRATA_GAME_GRANT", "STRATA_HELPER_GRANT"},
                "FORBIDDEN_ENVIRONMENT")
        if plan.broker_policy is not None:
            from .native_broker_policy import validate_broker_settings
            validate_broker_settings(plan.config_overrides)
            require(not {"STRATA_GAME_GRANT", "STRATA_HELPER_GRANT"} & set(plan.environment),
                    "BROKER_CREDENTIAL_ENVIRONMENT")
        require((plan.bootstrap_manifest is None) == (plan.bootstrap_digest is None), "BOOTSTRAP_REQUIRED")
        if plan.bootstrap_digest is not None:
            require(plan.broker_policy is not None, "BOOTSTRAP_BROKER_REQUIRED")
        if not self.simulation and plan.broker_policy is not None:
            require(plan.bootstrap_digest is not None, "BOOTSTRAP_REQUIRED")
            require(plan.ingress_policy is not None, "INGRESS_PROFILE_REQUIRED")
            require(plan.gateway_config_digest is not None, "GATEWAY_REQUIRED")
        if plan.gateway_config_digest is not None:
            from .native_gateway import require_gateway
            require_gateway(db, plan, "OPEN")
        if plan.ingress_policy is not None:
            from .native_ingress import provider_binding
            provider_binding(plan)
        if not self.simulation:
            require(fixture_argv is None, "FORBIDDEN")
            require(plan.binary_version == CODEX_VERSION and plan.dovetail_commit == DOVETAIL_COMMIT,
                    "RUNTIME_PIN_MISMATCH")
            require(callable(self.revoke_game), "REVOCATION_REQUIRED")
            self._proof(plan)
            policy = self.authorizations.check(self.authorization_id, plan.account, plan.provider,
                                              plan.auth_mode, plan.model)
            require(plan.budget_mode == "per_dispatch", "VERSIONED_ESTIMATE_REQUIRED")
            require(reserve.pricing_ref is not None, "ACCOUNTING_BASIS_MISMATCH")
            basis = EstimateBasis.model_validate(self.cas.json(
                Principal("operator", "operator"), self.namespace, reserve.pricing_ref))
            require(basis == policy.accounting_basis and
                    plan.accounting_basis_digest == basis.fingerprint(),
                    "ACCOUNTING_BASIS_MISMATCH")
            # Keep the initial live-validation stage bounded to at most $1/job.
            # Every job still consumes the original shared $10 authority.
            require(reserve.usage.spend_microusd <= policy.first_trial_max_microusd,
                    "INITIAL_TRIAL_LIMIT")
            # A different home alone is not isolation. Qualification must separately
            # prove that this workspace cannot access operator docs or provider auth.
        return workspace, profile

    def start(self, plan: NativeLaunch, reserve: BudgetLedger, *, fixture_argv=None):
        workspace, profile = self._validate(plan, reserve, fixture_argv)
        plan_body = plan.model_dump()
        if plan.accounting_basis_digest is None:
            plan_body.pop("accounting_basis_digest")
        if plan.broker_policy is None:
            plan_body.pop("broker_policy")
        for key in ("bootstrap_manifest", "bootstrap_digest", "ingress_policy", "gateway_config_digest"):
            if plan_body[key] is None:
                plan_body.pop(key)
        identity = digest({"plan": plan_body, "reserve": reserve.model_dump(),
                           "fixture_argv": fixture_argv})
        with self.db.transaction() as db:
            prior = db.execute("SELECT * FROM native_jobs WHERE id=?", (plan.job_id,)).fetchone()
            if prior:
                require(prior["plan_digest"] == identity, "IDEMPOTENCY_CONFLICT")
                return self.status(plan.job_id)  # Never re-executes a previous intent.
            if plan.role == "executor":
                occupied = db.execute("SELECT id FROM native_jobs WHERE campaign=? AND agent=? "
                    "AND role='executor' AND state IN (?,?,?,?,?)",
                    (plan.campaign_id, plan.agent_id, *ACTIVE)).fetchone()
                require(occupied is None, "EXECUTOR_BUSY")
            else:
                parent = db.execute("SELECT plan,state FROM native_jobs WHERE id=?",
                                    (plan.parent_job_id,)).fetchone()
                require(parent is not None and parent["state"] == "RUNNING", "HELPER_LINEAGE")
                parent_plan = NativeLaunch.model_validate_json(parent["plan"])
                require(parent_plan.campaign_id == plan.campaign_id and
                        parent_plan.agent_id == plan.agent_id and parent_plan.epoch == plan.epoch and
                        parent_plan.purpose == plan.purpose and
                        parent_plan.budget_mode == plan.budget_mode and
                        parent_plan.account == plan.account and parent_plan.depth + 1 == plan.depth and
                        reserve.parent_operation_id == parent_plan.operation_id, "HELPER_LINEAGE")
                count = db.execute("SELECT COUNT(*) FROM native_jobs WHERE campaign=? AND agent=? "
                    "AND role='helper' AND state IN (?,?,?,?,?)",
                    (plan.campaign_id, plan.agent_id, *ACTIVE)).fetchone()[0]
                require(plan.helper_limit == parent_plan.helper_limit and count < plan.helper_limit,
                        "HELPER_CAPACITY")
                require("STRATA_GAME_GRANT" not in plan.environment, "HELPER_CANNOT_ACT")
                for own, other in ((Path(plan.workspace), Path(parent_plan.workspace)),
                                   (Path(plan.profile_directory), Path(parent_plan.profile_directory))):
                    require(not own.is_relative_to(other) and not other.is_relative_to(own),
                            "HELPER_BOUNDARY_MISMATCH")
            db.execute("INSERT INTO native_jobs VALUES(?,?,?,?,?,?,?,?,?,NULL,NULL,NULL,NULL)",
                       (plan.job_id, plan.campaign_id, plan.agent_id, plan.epoch, plan.role,
                        plan.parent_job_id, identity, canonical(plan_body).decode(), "PREPARED"))
            self.db.event(db, "runtime.prepared", {"job_id": plan.job_id, "digest": identity})
        integrity = None
        try:
            if plan.bootstrap_digest is not None:
                from .native_bootstrap import acquire_native_bootstrap
                integrity = acquire_native_bootstrap(plan)
            self.budgets.post(plan.account, reserve, envelope=plan.budget_mode == "per_dispatch")
        except BaseException:
            if integrity:
                integrity.close()
            reason = ("bootstrap_integrity_failed" if plan.bootstrap_digest and integrity is None
                      else "budget_reservation_failed")
            self._state(plan.job_id, "REJECTED", reason)
            raise
        environment = plan.environment | {"CODEX_HOME": str(profile), "HOME": str(profile),
            "USERPROFILE": str(profile), "APPDATA": str(profile / "appdata"),
            "LOCALAPPDATA": str(profile / "localappdata")}
        for key in ("SystemRoot", "WINDIR"):
            if key in os.environ:
                environment[key] = os.environ[key]
        self._state(plan.job_id, "STARTING", None)
        process = None
        try:
            process = ManagedProcess(fixture_argv or native_argv(plan), workspace, environment,
                                     plan.prompt, **(integrity.managed_bootstrap if integrity else {}))
            events = queue.Queue(maxsize=128)
            overflow = threading.Event()
            threads = []
            for channel, stream in (("stdout", process.process.stdout),
                                     ("stderr", process.process.stderr)):
                thread = threading.Thread(target=self._read, args=(channel, stream, events, overflow),
                                          daemon=True)
                thread.start()
                threads.append(thread)
            self.live[plan.job_id] = {"plan": plan, "process": process, "queue": events,
                "overflow": overflow, "threads": threads, "reader": ExecUsageReader(),
                "source_cursor": 0, "bytes": 0, "eof": set(), "start": time.monotonic(),
                "integrity": integrity, "integrity_checked": time.monotonic()}
            self._state(plan.job_id, "RUNNING", None)
        except BaseException:
            # STARTING was durable before dispatch; even a failed start is treated as
            # possibly billable until authoritative receipts prove otherwise.
            if process:
                process.stop()
                process.close()
            if integrity:
                integrity.close()
            self.live.pop(plan.job_id, None)
            self.budgets.hold_uncertain(plan.account, plan.operation_id, "runtime_start_uncertain")
            self._state(plan.job_id, "UNSETTLED", "runtime_start_uncertain")
            raise
        return self.status(plan.job_id)

    @staticmethod
    def _read(channel, stream, events, overflow):
        try:
            while line := stream.readline(1024 * 1024 + 1):
                if len(line) > 1024 * 1024:
                    overflow.set()
                    return
                try:
                    events.put_nowait((channel, line))
                except queue.Full:
                    overflow.set()
                    return
        except (OSError, ValueError):
            overflow.set()
        finally:
            try:
                events.put_nowait((channel, None))
            except queue.Full:
                overflow.set()

    def _state(self, job, state, reason, returncode=None):
        now = time.time()
        with self.db.transaction() as db:
            db.execute("UPDATE native_jobs SET state=?,reason=?,returncode=?,"
                       "started=CASE WHEN ?='STARTING' THEN ? ELSE started END,"
                       "ended=CASE WHEN ? IN ('UNSETTLED','REJECTED','FINALIZED') THEN ? "
                       "ELSE ended END WHERE id=?", (state, reason, returncode, state, now,
                                                     state, now, job))
            self.db.event(db, "runtime.state", {"job_id": job, "state": state, "reason": reason,
                                               "returncode": returncode})

    def _event(self, job, channel, body):
        with self.db.transaction() as db:
            cursor = db.execute("SELECT COALESCE(MAX(cursor),0)+1 FROM native_events WHERE job=?",
                                (job,)).fetchone()[0]
            db.execute("INSERT INTO native_events VALUES(?,?,?,?)",
                       (job, cursor, channel, canonical(body).decode()))
        return cursor

    def pump(self, job):
        live = self.live.get(job)
        if not live:
            return self.status(job)
        plan = live["plan"]
        if live.get("integrity") and time.monotonic() - live["integrity_checked"] >= 1:
            try:
                live["integrity"].recheck()
                live["integrity_checked"] = time.monotonic()
            except Exception:
                return self.interrupt(job, "bootstrap_integrity_changed")
        if live["overflow"].is_set():
            return self.interrupt(job, "runtime_output_quota")
        if time.monotonic() - live["start"] > plan.hard_timeout_s:
            return self.interrupt(job, "runtime_hard_timeout")
        try:
            while True:
                channel, raw = live["queue"].get_nowait()
                if raw is None:
                    live["eof"].add(channel)
                    continue
                live["bytes"] += len(raw)
                if live["bytes"] > plan.output_limit_bytes:
                    return self.interrupt(job, "runtime_output_quota")
                # Preserve the exact bounded source bytes BEFORE interpreting them.
                # A malformed/truncated event remains available for fault/accounting review.
                self._event(job, channel, {"raw_base64": base64.b64encode(raw).decode("ascii")})
                line = raw.decode("utf-8", errors="strict")
                if channel == "stdout":
                    require(raw.endswith(b"\n"), "TRUNCATED_RUNTIME_EVENT")
                    live["source_cursor"] += 1
                    live["reader"].ingest(live["source_cursor"], line)
        except queue.Empty:
            pass
        except (ValueError, UnicodeError) as error:
            return self.interrupt(job, "runtime_event_invalid:" + type(error).__name__)
        except BaseException:
            self.interrupt(job, "runtime_journal_failure")
            raise
        code = live["process"].poll()
        if code is not None and live["eof"] == {"stdout", "stderr"}:
            self._finish(job, "native_exit", code)
        elif code is not None:
            # A descendant may keep the pipes alive after Codex exits. Fence it now.
            live["process"].stop()
        return self.status(job)

    def interrupt(self, job, reason):
        require(bool(reason) and len(reason) <= 200, "INVALID_REASON")
        live = self.live.get(job)
        require(live is not None, "RUNTIME_NOT_OWNED")
        plan = live["plan"]
        revoke_error = None
        try:
            self._state(job, "STOPPING", reason)
            if self.revoke_game:
                self.revoke_game(plan.campaign_id, plan.agent_id, plan.epoch)
                live["revoked"] = True
        except BaseException as error:
            revoke_error = error
        finally:
            live["process"].stop()
            self._finish(job, reason if revoke_error is None else "game_revocation_failed",
                         live["process"].poll())
        if revoke_error:
            raise Fault("GAME_REVOCATION_FAILED") from revoke_error
        return self.status(job)

    def _finish(self, job, reason, code):
        live = self.live[job]
        plan = live["plan"]
        cleanup_error = None
        for child, entry in list(self.live.items()):
            if entry["plan"].parent_job_id == job and child in self.live:
                try:
                    self.interrupt(child, "parent_runtime_stopped")
                except BaseException as error:
                    cleanup_error = error
                    reason = "child_cleanup_failed"
        try:
            if self.revoke_game and not live.get("revoked"):
                self.revoke_game(plan.campaign_id, plan.agent_id, plan.epoch)
                live["revoked"] = True
        except BaseException as error:
            cleanup_error = error
            reason = "game_revocation_failed"
        try:
            # Stop descendants before closing pipes/readers. End is not permission
            # to refund the reservation or assume only one provider call happened.
            live["process"].stop()
            for thread in live["threads"]:
                thread.join(timeout=1)
            live["process"].close()
            if live.get("integrity"):
                live["integrity"].close()
        except BaseException as error:
            if live.get("integrity"):
                self.integrity_holds[job] = live["integrity"]
            cleanup_error = error
            reason = "process_stop_failed"
        try:
            while True:
                channel, raw = live["queue"].get_nowait()
                if raw is not None and live["bytes"] + len(raw) <= plan.output_limit_bytes:
                    live["bytes"] += len(raw)
                    self._event(job, channel, {"raw_base64": base64.b64encode(raw).decode("ascii")})
        except queue.Empty:
            pass
        finally:
            # Pop even if storage is unavailable. The durable STARTING/RUNNING row
            # then requires explicit fenced recovery, while the process tree is dead.
            self.live.pop(job, None)
            self.budgets.hold_uncertain(plan.account, plan.operation_id, reason)
            self._state(job, "UNSETTLED", reason, code)
        if cleanup_error:
            raise Fault("RUNTIME_CLEANUP_FAILED") from cleanup_error

    def finalize(self, job):
        row = self._row(job)
        require(row["state"] == "UNSETTLED" and job not in self.live, "RUNTIME_NOT_QUIESCENT")
        plan = NativeLaunch.model_validate_json(row["plan"])
        op = self.db.connection.execute("SELECT * FROM operations WHERE id=?",
                                        (plan.operation_id,)).fetchone()
        require(op is not None and op["actual"] is not None and not op["uncertain"],
                "METERING_UNKNOWN")
        child = self.db.connection.execute("SELECT id FROM native_jobs WHERE parent=? "
                                           "AND state NOT IN ('FINALIZED','REJECTED')", (job,)).fetchone()
        require(child is None, "DESCENDANT_UNSETTLED")
        self._state(job, "FINALIZED", row["reason"], row["returncode"])
        return self.status(job)

    def close_dispatch_budget(self, job, seal_ref):
        """Release only unused envelope capacity after the gateway and process fence.

        A terminal CLI/turn usage summary is not this proof. The trusted gateway
        supervisor seals the exact attempt inventory only after removing its
        ingress grant and fencing all in-flight handlers. Unknown requests keep
        their reservations and prevent closing this job (and its ancestors).
        """
        row = self._row(job)
        require(row["state"] == "UNSETTLED" and job not in self.live, "RUNTIME_NOT_QUIESCENT")
        plan = NativeLaunch.model_validate_json(row["plan"])
        require(plan.budget_mode == "per_dispatch", "ENVELOPE_POSTING")
        visibility = self.db.connection.execute(
            "SELECT visibility FROM objects WHERE namespace=? AND ref=?",
            (self.namespace, seal_ref)).fetchone()
        require(visibility is not None and visibility[0] == "operator", "DISPATCH_EVIDENCE_PRIVATE")
        proof = self.cas.json(Principal("operator", "operator"), self.namespace, seal_ref)
        require(proof.get("schema") == "strata/InferenceIngressSeal/1" and
                proof.get("is_example") == self.simulation and
                proof.get("job_id") == job and proof.get("profile_digest") == plan.profile_digest()
                and proof.get("process_tree_dead") is True and
                proof.get("ingress_closed") is True and proof.get("handlers_fenced") is True,
                "DISPATCH_SEAL_UNVERIFIED")
        if plan.gateway_config_digest is not None:
            from .native_gateway import require_gateway_seal
            require_gateway_seal(self.db, self.cas, plan, proof, self.simulation)
        with self.db.transaction() as db:
            children = db.execute("SELECT id FROM native_jobs WHERE parent=? AND "
                                  "state NOT IN ('FINALIZED','REJECTED')", (job,)).fetchone()
            require(children is None, "DESCENDANT_UNSETTLED")
            attempts = list(db.execute("SELECT operation,state FROM inference_attempts WHERE "
                                      "json_extract(request,'$.runtime_job_id')=?", (job,)))
            require(sorted(r["operation"] for r in attempts) == proof.get("attempt_ids"),
                    "DISPATCH_SEAL_UNVERIFIED")
            require(all(r["state"] == "SETTLED" for r in attempts), "METERING_UNKNOWN")
            if plan.broker_policy is not None:
                from .native_admission import close_participant_envelopes
                close_participant_envelopes(self.db, self.budgets, db, plan, proof, seal_ref)
            source = db.execute("SELECT body FROM ledger WHERE "
                "json_extract(body,'$.operation_id')=? AND json_extract(body,'$.posting')='reserve'",
                (plan.operation_id,)).fetchone()
            require(source is not None, "OPERATION_LINEAGE")
            reserve = BudgetLedger.model_validate_json(source[0])
            closure_id = "envelope-close:" + digest({"job_id": job})
            receipt = BudgetLedger.model_validate(reserve.model_dump() | {
                "posting": "settle", "ledger_id": closure_id,
                "source_event_id": closure_id, "metering": "reported",
                "raw_usage_ref": seal_ref, "reason": "fenced ingress; usage belongs to descendants",
                "usage": dict.fromkeys(reserve.usage.model_dump(), 0)})
            self.budgets.post_in_transaction(db, plan.account, receipt, close_envelope=True)
            db.execute("UPDATE native_jobs SET state='FINALIZED',ended=? WHERE id=?",
                       (time.time(), job))
            self.db.event(db, "runtime.state", {"job_id": job, "state": "FINALIZED",
                "reason": row["reason"], "returncode": row["returncode"]})
        return self.status(job)

    def export_state(self, job, *, workspace_ref: str, skills_ref: str, handoff_ref: str | None,
                     artifact_namespace: str):
        """Seal admitted artifacts for fresh-handoff recovery, never a hidden session.

        Workspace and skill snapshots are created by the artifact/checkpoint
        service under its admission policy. This method binds those immutable refs
        to a settled, stopped native job and verifies their authorized existence.
        """
        row = self._row(job)
        require(row["state"] == "FINALIZED" and job not in self.live, "RUNTIME_NOT_QUIESCENT")
        plan = NativeLaunch.model_validate_json(row["plan"])
        require(artifact_namespace == f"campaign:{plan.campaign_id}:agent:{plan.agent_id}", "FORBIDDEN")
        principal = Principal(artifact_namespace, "executor")
        for ref in (workspace_ref, skills_ref):
            self.cas.read(principal, artifact_namespace, ref)
        if handoff_ref:
            text = self.cas.read(principal, artifact_namespace, handoff_ref)
            require(len(text) <= 8000, "ARTIFACT_QUOTA")
            text.decode("utf-8", errors="strict")
        # Artifacts remain in their authorized namespace. No session/profile caches,
        # provider auth, controller paths or private native logs are projected.
        state = {"schema": "strata/NativeState/1", "is_example": self.simulation,
                 "job_id": job, "campaign_id": plan.campaign_id, "agent_id": plan.agent_id,
                 "source_epoch": plan.epoch, "profile_digest": plan.profile_digest(),
                 "resume_mode": "fresh_handoff", "session": None, "runtime_cache": None,
                 "workspace": workspace_ref, "skills": skills_ref, "handoff": handoff_ref,
                 "artifact_namespace": artifact_namespace, "cost_rollback": False}
        return self.cas.put(Principal("operator", "operator"), self.namespace, "operator",
                            canonical(state))

    def resume(self, state_ref: str, plan: NativeLaunch, reserve: BudgetLedger, *, fixture_argv=None):
        """Start a fresh native process only after checkpoint artifacts are restored.

        The supervisor materializes the complete game/agent checkpoint and obtains
        a new boundary qualification. A referenced snapshot alone cannot prove its
        files are present; production qualification includes the restored workspace.
        """
        state = self.cas.json(Principal("operator", "operator"), self.namespace, state_ref)
        require(state.get("schema") == "strata/NativeState/1" and
                state.get("is_example") == self.simulation and state.get("resume_mode") ==
                "fresh_handoff" and state.get("session") is None and
                state.get("runtime_cache") is None, "RUNTIME_STATE_UNSUPPORTED")
        require(state["campaign_id"] == plan.campaign_id and state["agent_id"] == plan.agent_id and
                state["profile_digest"] == plan.profile_digest() and
                plan.epoch > state["source_epoch"] and plan.job_id != state["job_id"], "STALE_STATE")
        require(plan.parent_job_id is None and plan.role == "executor", "HELPER_LINEAGE")
        namespace = state["artifact_namespace"]
        require(namespace == f"campaign:{plan.campaign_id}:agent:{plan.agent_id}", "FORBIDDEN")
        principal = Principal(namespace, "executor")
        for key in ("workspace", "skills", "handoff"):
            if state[key]:
                self.cas.read(principal, namespace, state[key])
        if not self.simulation:
            self._proof(plan)
            proof = self.cas.json(Principal("operator", "operator"), self.namespace,
                                  plan.qualification_ref)
            require(proof.get("restored_state") == state_ref and
                    proof.get("new_epoch") == plan.epoch, "RESTORE_UNVERIFIED")
        # Handoff text is supplied by the admitted projection, never private logs.
        # Exact byte inclusion makes accidental omission a pre-dispatch failure.
        if state["handoff"]:
            handoff = self.cas.read(principal, namespace, state["handoff"]).decode("utf-8")
            require(handoff in plan.prompt, "HANDOFF_MISSING")
        return self.start(plan, reserve, fixture_argv=fixture_argv)

    def recover_fenced(self, job, fencing_ref):
        """Classify a former owner's job; never relaunch an ambiguous native turn."""
        require(job not in self.live, "RUNTIME_ALREADY_OWNED")
        row = self._row(job)
        require(row["state"] in ACTIVE, "INVALID_TRANSITION")
        plan = NativeLaunch.model_validate_json(row["plan"])
        proof = self.cas.json(Principal("operator", "operator"), self.namespace, fencing_ref)
        require(proof.get("schema") == "strata/RuntimeFenced/1" and
                proof.get("job_id") == job and proof.get("epoch") == plan.epoch and
                proof.get("process_tree_dead") is True and proof.get("game_grants_revoked") is True
                and proof.get("is_example") == self.simulation, "FENCING_UNVERIFIED")
        op = self.db.connection.execute("SELECT id FROM operations WHERE id=?",
                                        (plan.operation_id,)).fetchone()
        if op:
            self.budgets.hold_uncertain(plan.account, plan.operation_id, "supervisor_state_loss")
            self._state(job, "UNSETTLED", "supervisor_state_loss")
        else:
            require(row["state"] == "PREPARED", "OPERATION_LINEAGE")
            self._state(job, "REJECTED", "unreserved_before_dispatch")
        return self.status(job)

    def _row(self, job):
        row = self.db.connection.execute("SELECT * FROM native_jobs WHERE id=?", (job,)).fetchone()
        require(row is not None, "RUNTIME_MISSING")
        return row

    def status(self, job):
        row = self._row(job)
        return {k: row[k] for k in ("id", "campaign", "agent", "epoch", "role", "state",
                                     "started", "ended", "reason", "returncode")}

    def events(self, job, after_cursor=0):
        self._row(job)
        require(type(after_cursor) is int and after_cursor >= 0, "INVALID_CURSOR")
        return [{"cursor": r["cursor"], "channel": r["channel"], "body": json.loads(r["body"])}
                for r in self.db.connection.execute("SELECT * FROM native_events WHERE job=? "
                    "AND cursor>? ORDER BY cursor LIMIT 128", (job, after_cursor))]

    def usage_report(self, job):
        """Reconstruct observed turn summaries; provider receipts remain authoritative."""
        self._row(job)
        reader, cursor, invalid = ExecUsageReader(), 0, False
        for row in self.db.connection.execute("SELECT body FROM native_events WHERE job=? "
                                              "AND channel='stdout' ORDER BY cursor", (job,)):
            cursor += 1
            try:
                line = base64.b64decode(json.loads(row["body"])["raw_base64"]).decode("utf-8")
                reader.ingest(cursor, line)
            except (ValueError, UnicodeError):
                invalid = True
                break
        return reader.report() | {"job_id": job, "invalid_event_stream": invalid,
                                  "source_events_examined": cursor}
