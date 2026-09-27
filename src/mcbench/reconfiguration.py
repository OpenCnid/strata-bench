"""Private per-avatar settings supervision; no desktop or game process control.

The worker must implement and qualify the stop/readiness receipt producers.
Controller grant fencing alone does not revoke an independently running gateway.
"""

import json
import secrets
import time
from datetime import datetime
from typing import Annotated, Literal

from pydantic import Field

from .budgets import Budgets
from .contracts import Digest, Id, Observation, Positive, Ref, Strict, UInt
from .control_lock import profile_operation
from .native_control_plan import TARGET, NativeControlTarget, native_admission
from .native_settings_effects import NativeRepairAdmission, NativeSettingsEffectsClient
from .storage import Fault, Principal, canonical, digest, require
from .worker_repair import POLICY, WorkerRepairClient, WorkerRepairPlan
from . import repair_inference


class RepairPolicy(Strict):
    schema_: Literal["strata/RepairPolicy/1"] = Field(alias="schema")
    is_example: bool
    campaign_id: Id
    system_digest: Digest
    protocol_ref: Ref
    condition: Literal["training", "cognitive_probe", "keymap_learning"]
    reconfiguration_allowed: bool
    profiles: dict[Id, Id]


class RepairProof(Strict):
    is_example: bool
    campaign_id: Id
    agent_id: Id
    transaction_id: Id
    epoch: Positive
    generation: Positive
    profile_id: Id
    fingerprint: Annotated[str, Field(min_length=1, max_length=256)]
    observed_unix: float
    source_refs: Annotated[list[Ref], Field(min_length=1, max_length=16)]


class RepairStop(RepairProof):
    schema_: Literal["strata/RepairStop/1"] = Field(alias="schema")
    old_lease_id: Id
    pending_cancelled: bool
    inputs_released: bool


class RepairReady(RepairProof):
    schema_: Literal["strata/RepairReady/1"] = Field(alias="schema")
    connected: bool
    inputs_released: bool
    control_revision: UInt
    keymap_digest: Digest
    observation_ref: Ref


class Reconfigurations:
    def __init__(self, controller, controls, *, monotonic=time.monotonic):
        require(controller.database is controls.database and
                controller.simulation is controls.simulation, "PROFILE_MISMATCH")
        self.controller, self.controls = controller, controls
        self.database, self.clock = controller.database, controller.clock
        self.monotonic = monotonic
        self.clock_instance = secrets.token_hex(16)
        self.budgets = Budgets(self.database)
        with self.database.transaction() as db:
            repair_inference.install(db)
            db.execute("CREATE TABLE IF NOT EXISTS repair_policies (campaign TEXT PRIMARY KEY, "
                       "ref TEXT, body TEXT)")
            db.execute("CREATE TABLE IF NOT EXISTS repairs (id TEXT PRIMARY KEY, campaign TEXT, "
                       "agent TEXT, epoch INTEGER, generation INTEGER, phase TEXT, request TEXT, "
                       "stop_ref TEXT, ready_ref TEXT, forward_started INTEGER DEFAULT 0, result TEXT, "
                       "budget_operation TEXT UNIQUE, profile TEXT)")
            db.execute("CREATE UNIQUE INDEX IF NOT EXISTS repairs_active_profile ON repairs(profile) "
                       "WHERE phase<>'COMPLETE'")
            db.execute("CREATE TABLE IF NOT EXISTS repair_worker_handoffs (id TEXT PRIMARY KEY, "
                       "binding_digest TEXT NOT NULL, plan TEXT NOT NULL, phase TEXT NOT NULL "
                       "CHECK(phase IN ('INTENT','UNKNOWN','CONFIRMED')), stop_ref TEXT)")
            db.execute("CREATE TABLE IF NOT EXISTS repair_native_handoffs (id TEXT PRIMARY KEY, "
                       "binding_digest TEXT NOT NULL, target TEXT NOT NULL, admission TEXT NOT NULL, "
                       "phase TEXT NOT NULL CHECK(phase IN ('INTENT','UNKNOWN','CONFIRMED')), source_ref TEXT)")

    def _read(self, ref, model):
        require(self.controller.cas is not None, "EVIDENCE_STORE_REQUIRED")

        def unique(pairs):
            require(len(pairs) == len(dict(pairs)), "REPAIR_EVIDENCE_INVALID")
            return dict(pairs)

        try:
            raw = self.controller.cas.read(Principal("operator", "operator"),
                self.controller.evidence_namespace, ref, max_bytes=65536)
            value = model.model_validate(json.loads(raw, object_pairs_hook=unique))
            require(value.is_example is self.controller.simulation, "PROFILE_MISMATCH")
            if isinstance(value, RepairProof):
                for source in value.source_refs:
                    self.controller.cas.verify(Principal("operator", "operator"),
                        self.controller.evidence_namespace, source)
            return value
        except Exception:
            raise Fault("REPAIR_EVIDENCE_INVALID") from None

    def configure(self, campaign, owner, epoch, policy_ref):
        policy = self._read(policy_ref, RepairPolicy)
        with self.database.transaction() as db:
            row = self.controller.owned(db, campaign, owner, epoch)
            old = db.execute("SELECT ref FROM repair_policies WHERE campaign=?", (campaign,)).fetchone()
            if old:
                require(old[0] == policy_ref, "POLICY_IMMUTABLE")
                return
            require(row["state"] in {"DRAFT", "PROVISIONING", "VALIDATING"}, "POLICY_TOO_LATE")
            config = json.loads(row["config"])
            require(policy.campaign_id == campaign and policy.system_digest == config["system_digest"]
                    and policy.protocol_ref == config["protocol_ref"]
                    and set(policy.profiles) == set(config["agent_ids"])
                    and len(set(policy.profiles.values())) == config["n"], "REPAIR_POLICY_INVALID")
            require(policy.condition != "cognitive_probe" or not policy.reconfiguration_allowed,
                    "PROBE_RECONFIGURATION_FORBIDDEN")
            db.execute("INSERT INTO repair_policies VALUES (?,?,?)",
                       (campaign, policy_ref, canonical(policy.model_dump()).decode()))
            self.database.event(db, "repair.policy", {"campaign": campaign, "ref": policy_ref})

    def status(self, transaction_id):
        row = self.database.connection.execute("SELECT * FROM repairs WHERE id=?", (transaction_id,)).fetchone()
        require(row is not None, "REPAIR_MISSING")
        return dict(row) | {"request": json.loads(row["request"]),
                            "result": json.loads(row["result"]) if row["result"] else None}

    def _owned(self, db, repair, owner, epoch, *, unexpired=True):
        campaign = self.controller.owned(db, repair["campaign"], owner, epoch)
        lane = self.controller.lane(db, repair["campaign"], repair["agent"])
        require(campaign["state"] == "RUNNING" and repair["epoch"] == epoch
                and lane["epoch"] == epoch and lane["generation"] == repair["generation"]
                and lane["repair"] == repair["id"], "REPAIR_RECOVERY_REQUIRED")
        if unexpired:
            require(self.clock() <= repair["request"]["deadline_unix"], "REPAIR_DEADLINE_EXPIRED")
            require(repair["request"]["clock_instance"] == self.clock_instance,
                    "REPAIR_RECOVERY_REQUIRED")
            require(self.monotonic() <= repair["request"]["deadline_mono"], "REPAIR_DEADLINE_EXPIRED")
        return lane

    def _budget(self, db, request, *, settled=False):
        op = db.execute("SELECT o.*,a.campaign,a.agent FROM operations o JOIN accounts a ON a.id=o.account "
                        "WHERE o.id=?", (request["operation_id"],)).fetchone()
        require(op is not None and op["account"] == request["account"]
                and op["campaign"] == request["campaign"] and op["agent"] == request["agent"]
                and op["kind"] == "tool" and not op["uncertain"], "REPAIR_BUDGET_REQUIRED")
        require((op["actual"] is not None) is settled, "REPAIR_BUDGET_UNSETTLED")
        if not settled:
            reserved = json.loads(op["reserved"])
            floors = self.budgets.consumption_floors(db).get(request["operation_id"], {})
            require(all(reserved[k] is not None and value <= reserved[k] for k, value in floors.items()),
                    "REPAIR_BUDGET_EXHAUSTED")

    def request(self, campaign, owner, epoch, transaction_id, account, operation_id, *, deadline_unix):
        intent = {"campaign": campaign, "transaction_id": transaction_id, "account": account,
                  "operation_id": operation_id, "deadline_unix": deadline_unix}
        with self.database.transaction() as db:
            row = self.controller.owned(db, campaign, owner, epoch)
            old = db.execute("SELECT * FROM repairs WHERE id=?", (transaction_id,)).fetchone()
            if old:
                saved = json.loads(old["request"])
                require(all(saved[key] == value for key, value in intent.items()), "IDEMPOTENCY_CONFLICT")
                return self.status(transaction_id)
            require(row["state"] == "RUNNING", "INVALID_TRANSITION")
            require(type(deadline_unix) in (int, float) and
                    self.clock() < deadline_unix <= self.clock() + 900, "REPAIR_DEADLINE_INVALID")
            policy_row = db.execute("SELECT body FROM repair_policies WHERE campaign=?", (campaign,)).fetchone()
            require(policy_row is not None, "REPAIR_POLICY_REQUIRED")
            policy = RepairPolicy.model_validate_json(policy_row[0])
            require(policy.reconfiguration_allowed and policy.condition != "cognitive_probe",
                    "RECONFIGURATION_FORBIDDEN")
            control = self.controls.status(transaction_id)
            plan, agent = control["plan"], control["agent"]
            require(control["phase"] == "planned" and bool(plan["changes"]), "REPAIR_PLAN_REQUIRED")
            require(policy.profiles.get(agent) == plan["profile_id"], "REPAIR_PROFILE_MISMATCH")
            require(db.execute("SELECT 1 FROM repairs WHERE profile=? AND phase<>'COMPLETE'",
                               (plan["profile_id"],)).fetchone() is None, "SETTINGS_BUSY")
            lane = self.controller.lane(db, campaign, agent)
            require(lane["state"] in {"READY", "OBSERVING"} and lane["repair"] is None
                    and lane["epoch"] == epoch and lane["lease_id"] is not None, "INPUT_SUSPENDED")
            intent |= {"agent": agent, "plan_digest": digest(plan), "profile_id": plan["profile_id"],
                       "old_lease_id": lane["lease_id"], "started_unix": self.clock(),
                       "started_mono": self.monotonic(), "clock_instance": self.clock_instance,
                       "deadline_mono": self.monotonic() + deadline_unix - self.clock()}
            self._budget(db, intent)
            require(db.execute("SELECT 1 FROM repairs WHERE budget_operation=?", (operation_id,)).fetchone()
                    is None, "REPAIR_BUDGET_REUSED")
            require(self.budgets.status(account)["dispatch_allowed"], "BUDGET_EXHAUSTED")
            generation = lane["generation"] + 1
            db.execute("INSERT INTO repairs (id,campaign,agent,epoch,generation,phase,request,budget_operation,profile) "
                       "VALUES (?,?,?,?,?,'QUIESCING',?,?,?)", (transaction_id, campaign, agent,
                       epoch, generation, canonical(intent).decode(), operation_id, plan["profile_id"]))
            db.execute("UPDATE avatar_lanes SET generation=?,state='QUIESCING',repair=?,lease_id=NULL "
                       "WHERE campaign=? AND agent=?", (generation, transaction_id, campaign, agent))
            db.execute("UPDATE grants SET revoked=1 WHERE campaign=? AND agent=? AND role='executor'",
                       (campaign, agent))
            self.database.event(db, "repair.requested", intent | {"epoch": epoch, "generation": generation})
            repair_inference.begin(db, transaction_id, campaign, agent, epoch)
        return self.status(transaction_id)

    def _proof(self, repair, proof):
        plan = self.controls.status(repair["id"])["plan"]
        require(proof.campaign_id == repair["campaign"] and proof.agent_id == repair["agent"]
                and proof.transaction_id == repair["id"] and proof.epoch == repair["epoch"]
                and proof.generation == repair["generation"]
                and proof.profile_id == plan["profile_id"] and proof.fingerprint == plan["fingerprint"]
                and repair["request"]["plan_digest"] == digest(plan)
                and max(repair["request"]["started_unix"], self.clock() - 2)
                    <= proof.observed_unix <= self.clock(), "REPAIR_EVIDENCE_INVALID")

    def enter(self, transaction_id, owner, epoch, stop_ref):
        proof = self._read(stop_ref, RepairStop)
        with self.database.transaction() as db:
            repair = self.status(transaction_id)
            self._owned(db, repair, owner, epoch)
            worker_handoff = db.execute("SELECT stop_ref FROM repair_worker_handoffs WHERE id=?",
                                        (transaction_id,)).fetchone()
            require(worker_handoff is None or worker_handoff["stop_ref"] == stop_ref,
                    "REPAIR_WORKER_EVIDENCE_REQUIRED")
            if repair["phase"] == "RECONFIGURING":
                require(repair["stop_ref"] == stop_ref, "IDEMPOTENCY_CONFLICT")
                return
            require(repair["phase"] == "QUIESCING", "INVALID_TRANSITION")
            self._proof(repair, proof)
            require(self.clock() <= repair["request"]["started_unix"] + 1
                    and self.monotonic() <= repair["request"]["started_mono"] + 1
                    and proof.old_lease_id == repair["request"]["old_lease_id"]
                    and proof.pending_cancelled and proof.inputs_released, "INPUT_RELEASE_REQUIRED")
            db.execute("UPDATE repairs SET phase='RECONFIGURING',stop_ref=? WHERE id=?", (stop_ref, transaction_id))
            db.execute("UPDATE avatar_lanes SET state='RECONFIGURING' WHERE campaign=? AND agent=?",
                       (repair["campaign"], repair["agent"]))
            self.database.event(db, "repair.entered", {"transaction_id": transaction_id, "stop_ref": stop_ref})

    def quiesce_worker(self, transaction_id, owner, epoch, worker: WorkerRepairClient):
        """Consume one private pause dispatch, then reconcile only by status.

        This supplies actual worker stop evidence to enter(); it grants neither
        native settings capability nor permission to resume a paused executor.
        """
        require(isinstance(worker, WorkerRepairClient), "REPAIR_GRANT_INVALID")
        with profile_operation(self.database, "repair:" + transaction_id):
            with self.database.transaction() as db:
                repair = self.status(transaction_id)
                self._owned(db, repair, owner, epoch)
                require(repair["phase"] in {"QUIESCING", "RECONFIGURING"}, "REPAIR_RECOVERY_REQUIRED")
                request = repair["request"]
                plan = WorkerRepairPlan.model_validate({"schema": "strata/WorkerRepairPlan/1", "policy": POLICY,
                    "campaign_id": repair["campaign"], "agent_id": repair["agent"], "epoch": repair["epoch"],
                    "lease_id": request["old_lease_id"], "transaction_id": transaction_id,
                    "plan_digest": request["plan_digest"], "expires_unix_ms": int(request["deadline_unix"] * 1000)})
                worker.validate_scope(plan)
                # The original one-second controller quiescence bound includes
                # transport, CAS storage and publication; it is never restarted.
                remaining = min(request["deadline_unix"] - self.clock(),
                                request["deadline_mono"] - self.monotonic(), 1.0)
                if repair["phase"] == "QUIESCING":
                    remaining = min(remaining, request["started_unix"] + 1 - self.clock(),
                                    request["started_mono"] + 1 - self.monotonic())
                timeout_ms = int(remaining * 1000)
                require(timeout_ms > 0, "REPAIR_DEADLINE_EXPIRED")
                old = db.execute("SELECT * FROM repair_worker_handoffs WHERE id=?", (transaction_id,)).fetchone()
                if old:
                    require(old["binding_digest"] == worker.binding_digest
                            and json.loads(old["plan"]) == plan.model_dump(), "REPAIR_NOT_OWNED")
                    operation = "status"
                else:
                    require(repair["phase"] == "QUIESCING", "REPAIR_RECOVERY_REQUIRED")
                    db.execute("INSERT INTO repair_worker_handoffs VALUES (?,?,?,'INTENT',NULL)",
                               (transaction_id, worker.binding_digest, canonical(plan.model_dump()).decode()))
                    self.database.event(db, "repair.worker_intent", {"transaction_id": transaction_id,
                        "binding_digest": worker.binding_digest, "plan": plan.model_dump()})
                    operation = "pause"
            reply = None
            try:
                reply = worker.call(operation, plan, timeout_ms=timeout_ms)
                require(reply.result.phase == "paused" and reply.result.inputs_released
                        and reply.result.plan == plan, "INPUT_RELEASE_REQUIRED")
                observed = self.clock()
                witness = {"schema": "strata/WorkerRepairWitness/1", "is_example": self.controller.simulation,
                    "binding_digest": worker.binding_digest, "operation": operation,
                    "observed_unix": observed, "reply": reply.model_dump()}
                principal = Principal("operator", "operator")
                source = self.controller.cas.put(principal, self.controller.evidence_namespace, "operator",
                                                 canonical(witness))
                control = self.controls.status(transaction_id)["plan"]
                proof = RepairStop.model_validate({"schema": "strata/RepairStop/1",
                    "is_example": self.controller.simulation, "campaign_id": repair["campaign"],
                    "agent_id": repair["agent"], "transaction_id": transaction_id, "epoch": epoch,
                    "generation": repair["generation"], "profile_id": control["profile_id"],
                    "fingerprint": control["fingerprint"], "observed_unix": observed, "source_refs": [source],
                    "old_lease_id": plan.lease_id, "pending_cancelled": True, "inputs_released": True})
                stop_ref = old["stop_ref"] if old and old["stop_ref"] else self.controller.cas.put(
                    principal, self.controller.evidence_namespace, "operator", canonical(proof.model_dump()))
                with self.database.transaction() as db:
                    self._owned(db, self.status(transaction_id), owner, epoch)
                    db.execute("UPDATE repair_worker_handoffs SET stop_ref=? WHERE id=?", (stop_ref, transaction_id))
                    self.database.event(db, "repair.worker_observed", {"transaction_id": transaction_id,
                        "operation": operation, "source_ref": source, "stop_ref": stop_ref})
                self.enter(transaction_id, owner, epoch, stop_ref)
                with self.database.transaction() as db:
                    db.execute("UPDATE repair_worker_handoffs SET phase='CONFIRMED' WHERE id=?", (transaction_id,))
                return self.status(transaction_id)
            except BaseException:
                # The input hold and budget reservation remain. Within the
                # original window, retrying this method queries status only.
                with self.database.transaction() as db:
                    db.execute("UPDATE repair_worker_handoffs SET phase='UNKNOWN' WHERE id=?", (transaction_id,))
                    self.database.event(db, "repair.worker_uncertain", {"transaction_id": transaction_id,
                        "operation": operation})
                if repair["phase"] == "RECONFIGURING" or reply is not None and reply.result.phase == "failed":
                    self._fail(transaction_id, "WORKER_REPAIR_UNAVAILABLE")
                raise

    def admit_native(self, transaction_id, owner, epoch, worker, native, target):
        """Translate the approved plan once; uncertain delivery reconciles by status.

        This private transport does not qualify an adapter or create commit/resume
        authority. The native plan remains a charged, bounded repair candidate.
        """
        require(isinstance(native, NativeSettingsEffectsClient) and isinstance(target, NativeControlTarget),
                "REPAIR_PROFILE_MISMATCH")
        target = TARGET.validate_python(target.model_dump())
        require(native.connection.fingerprint == target.game_fingerprint
                and native.settings_fingerprint == target.settings_fingerprint, "REPAIR_PROFILE_MISMATCH")
        # Digest the actual descriptor without publishing the bearer credential.
        connection = native.connection.model_dump(mode="json")
        connection["bearer_token"] = native.connection.bearer_token.get_secret_value()
        binding = digest({"connection": connection, "target": target.model_dump()})
        self.quiesce_worker(transaction_id, owner, epoch, worker)
        profile = self.controls.status(transaction_id)["plan"]["profile_id"]
        with profile_operation(self.database, "repair:" + transaction_id), profile_operation(self.database, profile):
            with self.database.transaction() as db:
                repair = self.status(transaction_id)
                self._owned(db, repair, owner, epoch)
                require(repair["phase"] == "RECONFIGURING", "REPAIR_RECOVERY_REQUIRED")
                self._budget(db, repair["request"])
                require(self.budgets.status(repair["request"]["account"])["dispatch_allowed"], "BUDGET_EXHAUSTED")
                handoff = db.execute("SELECT * FROM repair_worker_handoffs WHERE id=?", (transaction_id,)).fetchone()
                require(handoff is not None and handoff["phase"] == "CONFIRMED", "REPAIR_WORKER_EVIDENCE_REQUIRED")
                worker_plan = WorkerRepairPlan.model_validate_json(handoff["plan"])
                control = self.controls.status(transaction_id)
                plan = control["plan"]
                require(digest(plan) == worker_plan.plan_digest, "REPAIR_NOT_OWNED")
                old = db.execute("SELECT * FROM repair_native_handoffs WHERE id=?", (transaction_id,)).fetchone()
                if old:
                    require(old["binding_digest"] == binding and json.loads(old["target"]) == target.model_dump(),
                            "REPAIR_NOT_OWNED")
                    admission = NativeRepairAdmission.model_validate_json(old["admission"])
                    require(admission.worker_plan == worker_plan, "REPAIR_NOT_OWNED")
                else:
                    require(control["phase"] == "planned", "REPAIR_RECOVERY_REQUIRED")
                    self.controls._version(plan)

            def timeout():
                remaining = min(repair["request"]["deadline_unix"] - self.clock(),
                                repair["request"]["deadline_mono"] - self.monotonic(), 1.0)
                value = int(remaining * 1000)
                require(value >= 100, "REPAIR_DEADLINE_EXPIRED")
                return value

            if old is None:
                state = self.controls.adapter.snapshot()
                self.controls._qualified(state)
                require(self.controls._policy(state) == plan["policy_digest"]
                        and state["profile_id"] == plan["profile_id"]
                        and state["fingerprint"] == plan["fingerprint"] and state["revision"] == plan["revision"]
                        and {k: v["key"] for k, v in state["bindings"].items()} == plan["backup"], "REVISION_CONFLICT")
                snapshot = native.call("settings_snapshot", {}, timeout_ms=timeout())
                admission = native_admission(plan, worker_plan, target, snapshot)
                with self.database.transaction() as db:
                    self._owned(db, self.status(transaction_id), owner, epoch)
                    db.execute("INSERT INTO repair_native_handoffs VALUES (?,?,?,?,'INTENT',NULL)",
                               (transaction_id, binding, canonical(target.model_dump()).decode(),
                                canonical(admission.model_dump()).decode()))
                    self.database.event(db, "repair.native_intent", {"transaction_id": transaction_id,
                        "binding_digest": binding, "target": target.model_dump(), "admission": admission.model_dump()})
            result = None
            operation = "settings_repair_status" if old else "settings_repair_bind"
            try:
                result = native.call(operation,
                    {"transaction_id": transaction_id} if old else admission.model_dump(),
                    timeout_ms=timeout(), **({"expected_repair": admission} if old else {}))
                require(result["phase"] == "bound" and result["body_fingerprint"] == target.body_fingerprint,
                        "REPAIR_NATIVE_UNAVAILABLE")
                witness = {"schema": "strata/NativeRepairWitness/1", "is_example": self.controller.simulation,
                    "transaction_id": transaction_id, "binding_digest": binding, "target": target.model_dump(),
                    "operation": operation, "observed_unix": self.clock(), "result": result}
                source = self.controller.cas.put(Principal("operator", "operator"),
                    self.controller.evidence_namespace, "operator", canonical(witness))
                with self.database.transaction() as db:
                    self._owned(db, self.status(transaction_id), owner, epoch)
                    db.execute("UPDATE repair_native_handoffs SET phase='CONFIRMED',source_ref=? WHERE id=?",
                               (source, transaction_id))
                    self.database.event(db, "repair.native_observed", {"transaction_id": transaction_id,
                        "operation": operation, "source_ref": source})
                return {"admission": admission.model_dump(), "source_ref": source, "result": result}
            except BaseException:
                with self.database.transaction() as db:
                    db.execute("UPDATE repair_native_handoffs SET phase='UNKNOWN' WHERE id=?", (transaction_id,))
                    self.database.event(db, "repair.native_uncertain", {"transaction_id": transaction_id,
                        "operation": operation})
                if result is not None or old and old["phase"] == "CONFIRMED":
                    self._fail(transaction_id, "NATIVE_REPAIR_UNAVAILABLE")
                raise

    def apply(self, transaction_id, owner, epoch):
        return self._run(transaction_id, owner, epoch, rollback=False)

    def rollback(self, transaction_id, owner, epoch):
        return self._run(transaction_id, owner, epoch, rollback=True)

    def adopt_recovery(self, transaction_id, owner, epoch):
        """A new owner inherits the hold, never permission to repeat forward writes."""
        with profile_operation(self.database, "repair:" + transaction_id):
            with self.database.transaction() as db:
                repair = self.status(transaction_id)
                row = self.controller.owned(db, repair["campaign"], owner, epoch)
                lane = self.controller.lane(db, repair["campaign"], repair["agent"])
                require(row["state"] == "RUNNING" and repair["phase"] != "COMPLETE"
                        and lane["repair"] == transaction_id and lane["epoch"] == epoch,
                        "REPAIR_RECOVERY_REQUIRED")
                require(repair["epoch"] != epoch or repair["request"]["clock_instance"] != self.clock_instance,
                        "RECOVERY_NOT_REQUIRED")
                db.execute("UPDATE repairs SET epoch=?,generation=?,phase='RECOVERY_REQUIRED' WHERE id=?",
                           (epoch, lane["generation"], transaction_id))
                db.execute("UPDATE avatar_lanes SET state='INTERRUPTED',lease_id=NULL WHERE campaign=? AND agent=?",
                           (repair["campaign"], repair["agent"]))
                self.database.event(db, "repair.recovery_adopted", {"transaction_id": transaction_id,
                    "old_epoch": repair["epoch"], "epoch": epoch, "generation": lane["generation"]})
        return self.status(transaction_id)

    def _run(self, transaction_id, owner, epoch, *, rollback):
        with profile_operation(self.database, "repair:" + transaction_id):
            with self.database.transaction() as db:
                repair = self.status(transaction_id)
                self._owned(db, repair, owner, epoch, unexpired=not rollback)
                allowed = {"QUIESCING", "RECONFIGURING", "APPLYING", "AWAITING_OBSERVATION", "RECOVERY_REQUIRED"}
                require(repair["phase"] in (allowed if rollback else {"RECONFIGURING"}), "REPAIR_RECOVERY_REQUIRED")
                require(db.execute("SELECT 1 FROM repair_native_handoffs WHERE id=?", (transaction_id,)).fetchone()
                        is None, "NATIVE_SETTINGS_ADAPTER_REQUIRED")
                if not rollback:
                    self._budget(db, repair["request"])
                    require(self.budgets.status(repair["request"]["account"])["dispatch_allowed"], "BUDGET_EXHAUSTED")
                db.execute("UPDATE repairs SET phase='APPLYING',forward_started=MAX(forward_started,?) WHERE id=?",
                           (int(not rollback), transaction_id))
                self.database.event(db, "repair.dispatch_intent", {"transaction_id": transaction_id, "rollback": rollback})
            try:
                control = self.controls.status(transaction_id)
                if rollback and control["phase"] == "planned":
                    require(not repair["forward_started"], "REPAIR_RECOVERY_REQUIRED")
                    self.controls.adapter.stop_all()  # No forward settings write was admitted.
                else:
                    (self.controls.rollback if rollback else self.controls.apply)(transaction_id)
                with self.database.transaction() as db:
                    self._owned(db, repair, owner, epoch, unexpired=not rollback)
                    db.execute("UPDATE repairs SET phase='AWAITING_OBSERVATION',result=? WHERE id=?",
                               (canonical({"settings_finished_unix": self.clock()}).decode(), transaction_id))
                    self.database.event(db, "repair.awaiting_observation", {"transaction_id": transaction_id})
            except BaseException:
                self._fail(transaction_id, "SETTINGS_RECOVERY_REQUIRED")
                raise
        return self.status(transaction_id)

    def _fail(self, transaction_id, reason):
        with self.database.transaction() as db:
            repair = self.status(transaction_id)
            if repair["phase"] == "COMPLETE":
                return
            db.execute("UPDATE repairs SET phase='RECOVERY_REQUIRED',result=? WHERE id=?",
                       (canonical({"code": reason}).decode(), transaction_id))
            db.execute("UPDATE avatar_lanes SET state='INTERRUPTED',lease_id=NULL WHERE campaign=? "
                       "AND agent=? AND repair=?", (repair["campaign"], repair["agent"], transaction_id))
            self.database.event(db, "repair.interrupted", {"transaction_id": transaction_id, "reason": reason})

    def expire(self):
        expired = []
        for row in self.database.connection.execute("SELECT id FROM repairs WHERE phase<>'COMPLETE'").fetchall():
            repair = self.status(row[0])
            if repair["phase"] == "RECOVERY_REQUIRED":
                continue
            limit = repair["request"]["deadline_unix"]
            if repair["phase"] == "QUIESCING":
                limit = min(limit, repair["request"]["started_unix"] + 1)
            same_clock = repair["request"]["clock_instance"] == self.clock_instance
            mono_limit = repair["request"]["deadline_mono"]
            if repair["phase"] == "QUIESCING":
                mono_limit = min(mono_limit, repair["request"]["started_mono"] + 1)
            if not same_clock or self.clock() > limit or self.monotonic() > mono_limit:
                self._fail(repair["id"], "REPAIR_DEADLINE_EXPIRED")
                expired.append(repair["id"])
        return expired  # Supervisor must stop/fence the actual worker independently.

    def finish(self, transaction_id, owner, epoch, ready_ref):
        with profile_operation(self.database, "repair:" + transaction_id):
            repair = self.status(transaction_id)
            if repair["phase"] == "COMPLETE":
                with self.database.transaction() as db:
                    self.controller.owned(db, repair["campaign"], owner, epoch)
                    require(repair["ready_ref"] == ready_ref, "IDEMPOTENCY_CONFLICT")
                return repair
            require(self.database.connection.execute("SELECT 1 FROM repair_worker_handoffs WHERE id=?",
                    (transaction_id,)).fetchone() is None, "REPAIR_WORKER_RESUME_REQUIRED")
            proof = self._read(ready_ref, RepairReady)
            observation = self._read(proof.observation_ref, Observation)
            self._proof(repair, proof)
            control = self.controls.status(transaction_id)
            plan = control["plan"]
            require(control["phase"] in {"committed", "rolled_back"}
                    or control["phase"] == "planned" and not repair["forward_started"], "REPAIR_RECOVERY_REQUIRED")
            expected = dict(plan["backup"])
            if control["phase"] == "committed":
                expected.update({key: value["after"] for key, value in plan["changes"].items()})
            current = self.controls.adapter.snapshot()
            require(self.controls._policy(current) == plan["policy_digest"]
                    and {k: v["key"] for k, v in current["bindings"].items()} == expected
                    and current["revision"] == proof.control_revision, "REPAIR_STATE_MISMATCH")
            require(proof.connected and proof.inputs_released and proof.keymap_digest == digest(expected)
                    and observation.campaign_id == repair["campaign"] and observation.agent_id == repair["agent"]
                    and observation.epoch == epoch and observation.control_revision == proof.control_revision
                    and observation.keymap_digest == proof.keymap_digest and not observation.held_keys
                    and observation.age_at_send_ms <= 2000 and observation.state is not None
                    and observation.state.connected and observation.state.active_request_id is None,
                    "FRESH_OBSERVATION_REQUIRED")
            recorded = datetime.fromisoformat(observation.recorded_at.replace("Z", "+00:00")).timestamp()
            require(repair["result"] is not None and "settings_finished_unix" in repair["result"]
                    and max(repair["result"]["settings_finished_unix"], proof.observed_unix - 2)
                        <= recorded <= proof.observed_unix, "FRESH_OBSERVATION_REQUIRED")
            with self.database.transaction() as db:
                repair = self.status(transaction_id)
                self._owned(db, repair, owner, epoch, unexpired=False)
                require(repair["phase"] == "AWAITING_OBSERVATION", "REPAIR_RECOVERY_REQUIRED")
                # Adapter reads can take time; freshness is checked again at the
                # authority publication boundary, not only before contacting it.
                self._proof(repair, proof)
                self._budget(db, repair["request"], settled=True)
                usable = self.budgets.status(repair["request"]["account"])["dispatch_allowed"]
                # Expired repairs can finish rollback; they cannot resume gameplay.
                usable &= self.clock() <= repair["request"]["deadline_unix"]
                usable &= (repair["request"]["clock_instance"] == self.clock_instance
                           and self.monotonic() <= repair["request"]["deadline_mono"])
                state = "OBSERVING" if usable else "INTERRUPTED"
                result = {"control_phase": control["phase"], "keymap_digest": proof.keymap_digest,
                          "state": state, "finished_unix": self.clock(), "input_resumed": bool(usable),
                          "exposure_source": "clock_intervals; wall time is not inferred game ticks"}
                db.execute("UPDATE repairs SET phase='COMPLETE',ready_ref=?,result=? WHERE id=?",
                           (ready_ref, canonical(result).decode(), transaction_id))
                db.execute("UPDATE avatar_lanes SET state=?,repair=NULL,generation=generation+1,lease_id=? "
                           "WHERE campaign=? AND agent=?", (state, secrets.token_hex(16) if usable else None,
                           repair["campaign"], repair["agent"]))
                self.database.event(db, "repair.completed", {"transaction_id": transaction_id, **result})
        return self.status(transaction_id)
