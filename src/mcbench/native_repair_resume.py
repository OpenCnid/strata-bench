"""Private controller-to-worker resume after a verified native commit.

This candidate records physical resume evidence. It does not publish campaign
readiness, synthesize a keymap observation or settle incomplete consumption.
"""

import uuid

from .control_lock import profile_operation
from .native_game import NativeGameClient
from .native_repair_flow import NativeRepairFlow
from .native_repair_restart import descriptor
from .native_restart import NativeRestartCheckpoint, NativeRestartState
from .native_resume import NativeResumeDecision
from .native_settings import strict_json
from .native_settings_effects import NativeCommitDecision, NativeRepairState
from .storage import Principal, canonical, digest, require
from .worker_repair import WorkerRepairState
from .worker_restart import WorkerRestartClient, WorkerRestartState
from .worker_resume import WorkerResumeClient
from .worker_publication import WorkerPublicationClient
from .repair_inference import RepairInference


class NativeRepairResume:
    def __init__(self, repairs):
        self.repairs, self.controls, self.database = repairs, repairs.controls, repairs.database
        self.flow = NativeRepairFlow(repairs)
        self.inference = RepairInference(repairs)
        with self.database.transaction() as db:
            db.execute("CREATE TABLE IF NOT EXISTS repair_worker_resumes (id TEXT PRIMARY KEY, "
                       "binding TEXT NOT NULL, request TEXT NOT NULL, native_instance TEXT NOT NULL, "
                       "phase TEXT NOT NULL CHECK(phase IN ('INTENT','UNKNOWN','CONFIRMED')), source_ref TEXT)")
            db.execute("CREATE TABLE IF NOT EXISTS repair_worker_measurements (id TEXT PRIMARY KEY, "
                       "binding TEXT NOT NULL, receipt TEXT NOT NULL, source_ref TEXT NOT NULL)")
            db.execute("CREATE TABLE IF NOT EXISTS repair_resume_inference (id TEXT PRIMARY KEY, "
                       "source_ref TEXT NOT NULL)")

    def _inference(self, transaction, owner, epoch, *, required=True):
        row = self.database.connection.execute("SELECT source_ref FROM repair_resume_inference WHERE id=?",
                                               (transaction,)).fetchone()
        intents = self.database.connection.execute("SELECT json_extract(body,'$.inference_ref') FROM outbox "
            "WHERE kind='repair.resume_intent' AND json_extract(body,'$.transaction_id')=?", (transaction,)).fetchall()
        if not required and row is None:
            require(not any(item[0] is not None for item in intents), "REPAIR_INFERENCE_REQUIRED")
            return None  # Historical resume status only; never a measurement prerequisite.
        require(row is not None, "REPAIR_INFERENCE_REQUIRED")
        require(len(intents) == 1 and intents[0][0] == row["source_ref"], "REPAIR_INFERENCE_CHANGED")
        proof = self._read(row["source_ref"])
        require(proof == self.inference.audit(transaction, owner, epoch)
                and proof["tracked_dispatches_settled"], "REPAIR_INFERENCE_CHANGED")
        return row["source_ref"]

    def _read(self, ref):
        return strict_json(self.repairs.controller.cas.read(Principal("operator", "operator"),
            self.repairs.controller.evidence_namespace, ref, max_bytes=1024 * 1024))

    def _evidence(self, transaction, control, admission, restart, native):
        row = self.database.connection.execute("SELECT * FROM repair_native_restarts WHERE id=?", (transaction,)).fetchone()
        require(row is not None and row["phase"] == "ADOPTED" and row["restart_binding"] == restart.binding_digest,
                "RESTART_ADOPTION_UNCONFIRMED")
        witness = self._read(row["source_ref"])
        require(isinstance(witness, dict) and set(witness) == {"schema", "is_example", "transaction_id", "old_binding", "new_binding",
            "checkpoint", "worker_state", "native_state", "native_head", "native_hold", "worker_hold"}, "RESTART_EVIDENCE_INVALID")
        require(witness["schema"] == "strata/ControllerRestartAdoptionWitness/1"
                and witness["is_example"] is self.repairs.controller.simulation
                and witness["transaction_id"] == transaction and witness["old_binding"] == row["old_binding"]
                and witness["new_binding"] == row["new_binding"], "RESTART_EVIDENCE_INVALID")
        checkpoint = NativeRestartCheckpoint.model_validate_json(row["checkpoint"])
        worker_state = WorkerRestartState.model_validate(witness["worker_state"])
        native_state = NativeRestartState.model_validate(witness["native_state"])
        native_hold = NativeRepairState.model_validate(witness["native_hold"])
        worker_hold = WorkerRepairState.model_validate(witness["worker_hold"])
        require(NativeRestartCheckpoint.model_validate(witness["checkpoint"]) == worker_state.checkpoint == native_state.checkpoint == checkpoint
                and worker_state.phase == "attached" and native_state.phase == "continued"
                and worker_state.plan == worker_hold.plan == admission.worker_plan
                and worker_state.old_connection_digest == row["old_connection"]
                and worker_state.replacement.policy == "forge-process-listener-client-thread/4"
                and worker_state.replacement.connection_digest == digest(descriptor(native))
                and native_hold.body_fingerprint == worker_state.replacement.body_fingerprint
                and native_state.expires_unix_ms == admission.worker_plan.expires_unix_ms
                and native_hold.admission == admission and native_hold.phase == "bound"
                and worker_hold.phase == "paused" and worker_hold.inputs_released, "RESTART_EVIDENCE_INVALID")
        head, _ = self.flow._head(control["plan"], witness["native_head"], applied=True, active=transaction)
        require(head.revision == checkpoint.request.expected_revision and head.digest == checkpoint.request.expected_digest
                and checkpoint.request.plan_digest == admission.worker_plan.plan_digest, "RESTART_EVIDENCE_INVALID")
        committed = self.database.connection.execute("SELECT * FROM repair_native_writes WHERE id=? AND operation='commit'",
                                                     (transaction,)).fetchone()
        require(committed is not None and committed["phase"] == "CONFIRMED", "REPAIR_NATIVE_EVIDENCE_REQUIRED")
        commit = NativeCommitDecision.model_validate_json(committed["request"])
        proof = self._read(commit.verification_ref)
        require(isinstance(proof, dict) and set(proof) == {"schema", "is_example", "transaction_id", "plan_digest",
            "verification", "native_head", "admission"}, "RESUME_VERIFICATION_INVALID")
        require(proof["schema"] == "strata/NativeControlVerification/1"
                and proof["is_example"] is self.repairs.controller.simulation
                and proof["transaction_id"] == commit.transaction_id == transaction
                and proof["plan_digest"] == commit.plan_digest == admission.worker_plan.plan_digest
                and proof["admission"] == admission.model_dump()
                and digest(proof["verification"]) == committed["verification_digest"]
                and proof["verification"] == control["receipt"]["verification"], "RESUME_VERIFICATION_INVALID")
        before, _ = self.flow._head(control["plan"], proof["native_head"], applied=True, active=transaction)
        require(before.revision == commit.expected_revision and before.digest == commit.expected_digest,
                "RESUME_VERIFICATION_INVALID")
        self.controls.validate_verification(control["plan"], proof["verification"])
        return commit, native_state.current_instance, worker_state.replacement.connection_generation, checkpoint

    def resume_committed(self, transaction, owner, epoch, worker, restart, resume, native):
        require(isinstance(restart, WorkerRestartClient) and isinstance(resume, WorkerResumeClient), "RESUME_WORKER_MISMATCH")
        profile = self.controls.status(transaction)["plan"]["profile_id"]
        with profile_operation(self.database, "repair:" + transaction), profile_operation(self.database, profile):
            old = self.database.connection.execute("SELECT * FROM repair_worker_resumes WHERE id=?", (transaction,)).fetchone()
            repair, control, admission = self.flow._context(transaction, owner, epoch, worker, native, old is not None,
                                                            observe=old is None)
            require(control["phase"] == "committed", "VERIFIED_COMMIT_REQUIRED")
            commit, native_instance, generation, checkpoint = self._evidence(transaction, control, admission, restart, native)
            if old:
                decision = NativeResumeDecision.model_validate_json(old["request"])
                require(old["binding"] == resume.binding_digest and old["native_instance"] == native_instance
                        and decision.verification_ref == commit.verification_ref, "REPAIR_NOT_OWNED")
            else:
                continued = native.call("settings_restart_status", {"restart_id": checkpoint.request.restart_id},
                    expected_restart=checkpoint, timeout_ms=self.flow._timeout(repair))
                require(continued["phase"] == "continued" and continued["current_instance"] == native_instance,
                        "RESUME_INSTANCE_MISMATCH")
                raw = native.call("settings_snapshot", {}, timeout_ms=self.flow._timeout(repair))
                head, expected = self.flow._head(control["plan"], raw, applied=True, active=None)
                require(head.revision == control["receipt"]["revision"]
                        and digest(expected) == control["receipt"]["keymap_digest"], "REPAIR_STATE_MISMATCH")
                state = native.call("settings_commit_status", {"transaction_id": transaction}, expected_commit=commit,
                                    timeout_ms=self.flow._timeout(repair))
                require(state["phase"] == "committed" and state["revision"] == head.revision, "REPAIR_STATE_MISMATCH")
                identity = NativeGameClient(native.connection).call("identity", {}, timeout_ms=self.flow._timeout(repair))
                require(identity["connection_generation"] == generation, "RESTART_CONNECTION_MISMATCH")
                now = self.repairs.clock()
                remaining = min(5.0, repair["request"]["deadline_unix"] - now,
                    repair["request"]["deadline_mono"] - self.repairs.monotonic(), admission.worker_plan.expires_unix_ms / 1000 - now)
                require(remaining >= .5, "REPAIR_DEADLINE_EXPIRED")
                decision = NativeResumeDecision.model_validate({"schema": "strata/NativeSettingsResumeDecision/1",
                    "policy": "operator-owned-settings-resume/1", "resume_id": str(uuid.uuid4()),
                    "worker_plan": admission.worker_plan.model_dump(), "expected_revision": head.revision,
                    "expected_digest": head.digest, "completion_phase": "committed", "verification_ref": commit.verification_ref,
                    "connection_generation": generation, "lease_until_unix_ms": int((now + remaining) * 1000)})
            resume.validate_worker(worker, restart, decision)
            inference_ref = self._inference(transaction, owner, epoch, required=False) if old else None
            if not old:
                audit = self.inference.freeze(transaction, owner, epoch)
                require(audit["tracked_dispatches_settled"], "REPAIR_INFERENCE_PENDING")
                inference_ref = self.flow._put(audit)
                with self.database.transaction() as db:
                    self.repairs._owned(db, self.repairs.status(transaction), owner, epoch)
                    self.repairs._budget(db, repair["request"])
                    require(self.repairs.budgets.status(repair["request"]["account"])["dispatch_allowed"], "BUDGET_EXHAUSTED")
                    require(self.inference.audit_in_transaction(db, transaction, owner, epoch) == audit,
                            "REPAIR_INFERENCE_CHANGED")
                    require(self.repairs.clock() * 1000 < decision.lease_until_unix_ms, "REPAIR_DEADLINE_EXPIRED")
                    db.execute("INSERT INTO repair_resume_inference VALUES (?,?)", (transaction, inference_ref))
                    db.execute("INSERT INTO repair_worker_resumes VALUES (?,?,?,?,'INTENT',NULL)",
                        (transaction, resume.binding_digest, canonical(decision.model_dump()).decode(), native_instance))
                    self.database.event(db, "repair.resume_intent", {"transaction_id": transaction,
                        "decision": decision.model_dump(), "inference_ref": inference_ref})
            result = None
            try:
                result = resume.call("status" if old else "resume", decision,
                    timeout_ms=1000 if old else min(2000, int(remaining * 1000))).result
                require(result.native.source_instance == result.native.current_instance == native_instance,
                        "RESUME_INSTANCE_MISMATCH")
                witness = {"schema": "strata/ControllerResumeWitness/2" if inference_ref else "strata/ControllerResumeWitness/1",
                    "is_example": self.repairs.controller.simulation, "transaction_id": transaction,
                    "worker_binding": resume.binding_digest, "worker_state": result.model_dump(),
                    "campaign_permission_published": False, "consumption_settled": False}
                if inference_ref:
                    witness["inference_ref"] = inference_ref
                source = self.flow._put(witness)
                with self.database.transaction() as db:
                    self.repairs._owned(db, self.repairs.status(transaction), owner, epoch, unexpired=False)
                    db.execute("UPDATE repair_worker_resumes SET phase='CONFIRMED',source_ref=? WHERE id=?", (source, transaction))
                    self.database.event(db, "repair.resume_observed", {"transaction_id": transaction, "source_ref": source,
                        "gameplay_resumed": result.gameplay_resumed, "campaign_permission_published": False})
                return {"source_ref": source, "worker_state": result.model_dump(), "campaign_permission_published": False}
            except BaseException:
                try:
                    with self.database.transaction() as db:
                        db.execute("UPDATE repair_worker_resumes SET phase='UNKNOWN' WHERE id=?", (transaction,))
                        self.database.event(db, "repair.resume_uncertain", {"transaction_id": transaction})
                finally:
                    if result is not None:
                        # Even a failed database write must reach physical stop.
                        try:
                            NativeGameClient(native.connection).call("stop_all", {}, timeout_ms=200)
                        finally:
                            self.repairs._fail(transaction, "RESUME_EVIDENCE_UNAVAILABLE")
                raise

    def measure_prepared(self, transaction, owner, epoch, worker, restart, resume, publisher, native):
        """Capture measured charges before publication; never a settlement certificate."""
        require(isinstance(publisher, WorkerPublicationClient), "CONTROL_PUBLICATION_GRANT_INVALID")
        publisher.validate_resume(resume)
        profile = self.controls.status(transaction)["plan"]["profile_id"]
        with profile_operation(self.database, "repair:" + transaction), profile_operation(self.database, profile):
            repair, control, admission = self.flow._context(transaction, owner, epoch, worker, native, True, observe=False)
            require(control["phase"] == "committed", "VERIFIED_COMMIT_REQUIRED")
            committed, instance, _, _ = self._evidence(transaction, control, admission, restart, native)
            row = self.database.connection.execute("SELECT * FROM repair_worker_resumes WHERE id=?", (transaction,)).fetchone()
            require(row is not None and row["phase"] == "CONFIRMED" and row["binding"] == resume.binding_digest
                    and row["native_instance"] == instance, "REPAIR_RESUME_UNCONFIRMED")
            decision = NativeResumeDecision.model_validate_json(row["request"])
            require(decision.worker_plan == admission.worker_plan and decision.verification_ref == committed.verification_ref,
                    "REPAIR_NOT_OWNED")
            self._inference(transaction, owner, epoch)
            with self.database.transaction() as db:
                self.repairs._owned(db, repair, owner, epoch)
                self.repairs._budget(db, repair["request"])
            receipt = publisher.measure(decision, timeout_ms=self.flow._timeout(repair))
            encoded = canonical(receipt.model_dump()).decode()
            # Retain known consumption before the separate CAS write. That write
            # can fail after real work; it must not hide an observed overrun or
            # make this measured dimension look unconsumed. Other dimensions
            # remain covered by the original unresolved reservation.
            with self.database.transaction() as db:
                self.repairs._owned(db, self.repairs.status(transaction), owner, epoch)
                self.repairs.budgets.retain_consumption_floor(db, repair["request"]["account"],
                    repair["request"]["operation_id"], "repair-measured:" + digest(receipt.model_dump()),
                    "primitive_events", receipt.charged_primitive_events,
                    {"schema": "strata/RepairPrimitiveConsumption/1", "transaction_id": transaction,
                     "publication_binding": publisher.binding_digest, "resume_source_ref": row["source_ref"],
                     "worker_receipt": receipt.model_dump()})
            with self.database.transaction() as db:
                # This check is deliberately after the floor transaction commits.
                # Refusing an overrun must preserve its actual observed amount.
                self.repairs._budget(db, repair["request"])
            old = self.database.connection.execute("SELECT * FROM repair_worker_measurements WHERE id=?", (transaction,)).fetchone()
            if old:
                require(old["binding"] == publisher.binding_digest and old["receipt"] == encoded, "REPAIR_ACCOUNTING_CHANGED")
                return {"source_ref": old["source_ref"], "receipt": receipt.model_dump(), "complete_repair_accounting": False}
            now, mono = self.repairs.clock(), self.repairs.monotonic()
            require(repair["request"]["clock_instance"] == self.repairs.clock_instance
                    and mono >= repair["request"]["started_mono"], "REPAIR_RECOVERY_REQUIRED")
            source = self.flow._put({"schema": "strata/ControllerRepairMeasurement/1",
                "is_example": self.repairs.controller.simulation, "transaction_id": transaction,
                "publication_binding": publisher.binding_digest, "resume_source_ref": row["source_ref"],
                "worker_receipt": receipt.model_dump(), "controller_clock_id": self.repairs.clock_instance,
                "started_unix": repair["request"]["started_unix"], "observed_unix": now,
                "elapsed_ms": int((mono - repair["request"]["started_mono"]) * 1000),
                "complete_repair_accounting": False, "consumption_settled": False,
                "campaign_permission_published": False})
            with self.database.transaction() as db:
                self.repairs._owned(db, self.repairs.status(transaction), owner, epoch)
                self.repairs._budget(db, repair["request"])
                db.execute("INSERT INTO repair_worker_measurements VALUES (?,?,?,?)",
                    (transaction, publisher.binding_digest, encoded, source))
                self.database.event(db, "repair.worker_measured", {"transaction_id": transaction, "source_ref": source,
                    "opening_primitive_events": receipt.opening.primitive_events,
                    "closing_primitive_events": receipt.closing.primitive_events,
                    "complete_repair_accounting": False})
            return {"source_ref": source, "receipt": receipt.model_dump(), "complete_repair_accounting": False}
